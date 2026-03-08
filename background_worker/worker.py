"""
HuntAI Background Worker
24/7 orchestrator for lead discovery, email outreach, and reply monitoring.
"""

import time
import threading
import logging
from datetime import datetime
from typing import Optional

from database.db import (
    create_campaign, save_lead, log_activity, get_db, log_email
)

logger = logging.getLogger("huntai.worker")


class BackgroundWorker:
    """Orchestrates the full HuntAI pipeline."""

    def __init__(self, config):
        self.config = config
        self._threads = []
        self._running = False

    def start_campaign(self, name: str, lead_count: int,
                       industry: str, location: str, company_size: str):
        """Start a full campaign in a background thread."""
        campaign_id = create_campaign(name, industry, location, company_size, lead_count)
        log_activity("campaign_start", f"Campaign '{name}' started (id={campaign_id})", campaign_id=campaign_id)

        t = threading.Thread(
            target=self._run_campaign,
            args=(campaign_id, name, lead_count, industry, location, company_size),
            daemon=True,
            name=f"campaign-{campaign_id}"
        )
        t.start()
        self._threads.append(t)
        return campaign_id

    def _run_campaign(self, campaign_id, name, lead_count, industry, location, company_size):
        """Full campaign pipeline."""
        try:
            log_activity("pipeline_start", "Starting scraping phase", campaign_id=campaign_id)

            # 1. Scrape leads
            leads = self._scrape_leads(campaign_id, industry, location, lead_count)
            log_activity("pipeline_scrape", f"Scraped {len(leads)} raw leads", campaign_id=campaign_id)

            # 2. Qualify with AI
            qualified = self._qualify_leads(campaign_id, leads, company_size)
            log_activity("pipeline_qualify", f"{len(qualified)} leads qualified", campaign_id=campaign_id)

            # 3. Send outreach
            self._send_outreach(campaign_id, qualified)

            # 4. Mark campaign complete
            conn = get_db()
            conn.execute("UPDATE campaigns SET status='completed', updated_at=datetime('now') WHERE id=?", (campaign_id,))
            conn.commit()
            conn.close()
            log_activity("campaign_complete", f"Campaign '{name}' completed", campaign_id=campaign_id)

        except Exception as e:
            log_activity("campaign_error", f"Campaign error: {str(e)}", campaign_id=campaign_id)
            conn = get_db()
            conn.execute("UPDATE campaigns SET status='failed', updated_at=datetime('now') WHERE id=?", (campaign_id,))
            conn.commit()
            conn.close()

    def _scrape_leads(self, campaign_id, industry, location, count):
        """Scrape leads from configured sources."""
        from scraper.scraper import get_scraper
        api_key = self.config.get('apify_api_key', '')
        use_mock = not api_key or api_key == 'mock'
        scraper = get_scraper(api_key, self.config, mock=use_mock)

        leads = []

        # Google Maps
        if self.config.get('scrape_google_maps', 'yes') == 'yes':
            try:
                results = scraper.scrape_google_maps(industry, location, max_results=count)
                leads.extend(results)
                log_activity("scrape_gmaps", f"Google Maps: {len(results)} results", campaign_id=campaign_id)
            except Exception as e:
                log_activity("scrape_error", f"Google Maps error: {e}", campaign_id=campaign_id)

        # Startup directories
        if self.config.get('scrape_startup_dirs', 'yes') == 'yes' and len(leads) < count:
            try:
                results = scraper.scrape_startup_directories(industry, location, max_results=count - len(leads))
                leads.extend(results)
                log_activity("scrape_dirs", f"Startup dirs: {len(results)} results", campaign_id=campaign_id)
            except Exception as e:
                log_activity("scrape_error", f"Directory scrape error: {e}", campaign_id=campaign_id)

        # Deduplicate by email
        seen_emails = set()
        unique = []
        for lead in leads:
            email = lead.get('email', '').lower()
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique.append(lead)
            elif not email:
                unique.append(lead)

        return unique[:count]

    def _qualify_leads(self, campaign_id, leads, company_size):
        """AI-qualify each lead and save to DB."""
        from ai_agent.engine import AIEngine
        ai = AIEngine(config=self.config)

        min_score = int(self.config.get('min_lead_score', 5))
        qualified = []

        for lead in leads:
            try:
                qual = ai.qualify_lead(lead)
                score = qual.get('score', 5)
                lead['lead_score'] = score
                lead['qualification'] = qual.get('reasoning', '')

                # Save all leads, but only send emails to qualified ones
                lead_id = save_lead(campaign_id, lead)
                lead['_id'] = lead_id
                log_activity("lead_saved", f"Lead saved: {lead.get('company_name')} (score={score})", campaign_id=campaign_id, lead_id=lead_id)

                if score >= min_score and lead.get('email'):
                    qualified.append(lead)

            except Exception as e:
                log_activity("qualify_error", f"Qualify error for {lead.get('company_name')}: {e}", campaign_id=campaign_id)

        return qualified

    def _send_outreach(self, campaign_id, leads):
        """Generate and send outreach emails."""
        from ai_agent.engine import AIEngine
        from email_engine.sender import EmailSender

        ai = AIEngine(config=self.config)
        sender = EmailSender(self.config)
        notification_email = self.config.get('notification_email', '')
        delay = int(self.config.get('email_delay_seconds', 30))

        for lead in leads:
            try:
                # Generate email
                email_data = ai.generate_outreach_email(lead)
                subject = email_data.get('subject', 'Quick question')
                body = email_data.get('body', '')

                if not body:
                    continue

                # Send outreach
                ok, result = sender.send_outreach(
                    lead_id=lead.get('_id'),
                    campaign_id=campaign_id,
                    lead=lead,
                    subject=subject,
                    body=body,
                )

                if ok:
                    log_activity("outreach_sent", f"Outreach sent to {lead.get('email')}", campaign_id=campaign_id, lead_id=lead.get('_id'))

                    # Send notification to user
                    if notification_email:
                        try:
                            sender.send_notification(notification_email, lead, subject, body)
                        except Exception as ne:
                            log_activity("notification_error", f"Notification error: {ne}", campaign_id=campaign_id)
                else:
                    log_activity("outreach_failed", f"Failed to send to {lead.get('email')}: {result}", campaign_id=campaign_id)

                # Rate limiting
                time.sleep(delay)

            except Exception as e:
                log_activity("outreach_error", f"Outreach error for {lead.get('company_name')}: {e}", campaign_id=campaign_id)

    def start_inbox_monitor(self):
        """Start background inbox monitoring for replies."""
        from email_engine.sender import InboxMonitor
        monitor = InboxMonitor(self.config)
        monitor.start(callback=self._on_reply)
        log_activity("inbox_monitor_start", "Inbox monitoring started")
        return monitor

    def _on_reply(self, reply: dict):
        """Handle an incoming reply."""
        from ai_agent.engine import AIEngine
        ai = AIEngine(config=self.config)
        classification = ai.classify_reply(reply.get('body', ''))
        log_activity("reply_classified",
                     f"Reply from {reply.get('from')}: {classification.get('classification')} | {classification.get('summary', '')}")

    def schedule_follow_ups(self, campaign_id: int, days_after: int = 3):
        """Schedule follow-up emails for non-responders."""
        t = threading.Thread(
            target=self._follow_up_loop,
            args=(campaign_id, days_after),
            daemon=True,
        )
        t.start()

    def _follow_up_loop(self, campaign_id, days_after):
        """Send follow-ups to leads that haven't responded."""
        from ai_agent.engine import AIEngine
        from email_engine.sender import EmailSender

        # Wait for follow-up window
        time.sleep(days_after * 86400)

        ai = AIEngine(config=self.config)
        sender = EmailSender(self.config)

        conn = get_db()
        # Find sent emails with no replies
        no_reply = conn.execute("""
            SELECT el.*, l.company_name, l.email, l.industry, l.location
            FROM email_log el
            JOIN leads l ON el.lead_id = l.id
            WHERE el.campaign_id = ? 
            AND el.replied_at IS NULL 
            AND el.email_type = 'outreach'
            AND el.follow_up_count < 2
        """, (campaign_id,)).fetchall()
        conn.close()

        for row in no_reply:
            lead = {
                'company_name': row['company_name'],
                'email': row['email'],
                'industry': row['industry'],
                'location': row['location'],
                '_id': row['lead_id'],
            }
            follow_up_num = (row['follow_up_count'] or 0) + 1
            try:
                fu_data = ai.generate_follow_up(lead, row['body'], follow_up_num)
                ok, _ = sender.send_email(lead['email'], fu_data['subject'], fu_data['body'])
                if ok:
                    conn = get_db()
                    conn.execute(
                        "UPDATE email_log SET follow_up_count = follow_up_count + 1 WHERE id = ?",
                        (row['id'],)
                    )
                    conn.commit()
                    conn.close()
                    log_activity("followup_sent", f"Follow-up #{follow_up_num} sent to {lead['email']}", campaign_id=campaign_id)
            except Exception as e:
                log_activity("followup_error", f"Follow-up error: {e}", campaign_id=campaign_id)

            time.sleep(60)

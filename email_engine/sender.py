"""
HuntAI Email Engine
SMTP email sending, tracking, and inbox monitoring.
"""

import smtplib
import imaplib
import email as email_lib
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from typing import Optional, Tuple
from datetime import datetime
from database.db import log_activity, log_email


def test_smtp(host: str, port: int, username: str, password: str) -> Tuple[bool, str]:
    """Test SMTP connection."""
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(username, password)
        return True, "Connection successful"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed — check email & app password"
    except smtplib.SMTPConnectError:
        return False, f"Cannot connect to {host}:{port}"
    except Exception as e:
        return False, str(e)


class EmailSender:
    """Handles email sending via SMTP."""

    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()
        self._sent_today = 0
        self._last_reset = datetime.now().date()

    @property
    def smtp_host(self):
        return self.config.get('smtp_host', 'smtp.gmail.com')

    @property
    def smtp_port(self):
        return int(self.config.get('smtp_port', 587))

    @property
    def username(self):
        return self.config.get('email_address', '')

    @property
    def password(self):
        return self.config.get('email_password', '')

    @property
    def daily_limit(self):
        return int(self.config.get('daily_email_limit', 50))

    @property
    def send_delay(self):
        return int(self.config.get('email_delay_seconds', 30))

    def _reset_daily_counter(self):
        today = datetime.now().date()
        if today != self._last_reset:
            self._sent_today = 0
            self._last_reset = today

    def can_send(self) -> Tuple[bool, str]:
        self._reset_daily_counter()
        if self._sent_today >= self.daily_limit:
            return False, f"Daily limit of {self.daily_limit} emails reached"
        if not self.username:
            return False, "Email not configured"
        return True, "OK"

    def send_email(self, to_address: str, subject: str, body: str,
                   html_body: str = None, reply_to: str = None) -> Tuple[bool, str]:
        """Send a single email."""
        with self._lock:
            can, reason = self.can_send()
            if not can:
                return False, reason

            try:
                msg = MIMEMultipart('alternative')
                msg['From'] = f"{self.config.get('company_name', 'HuntAI')} <{self.username}>"
                msg['To'] = to_address
                msg['Subject'] = subject
                if reply_to:
                    msg['Reply-To'] = reply_to

                # Add tracking pixel (base64 1x1 transparent gif)
                tracking_id = f"huntai_{int(time.time())}"
                
                msg.attach(MIMEText(body, 'plain'))
                if html_body:
                    msg.attach(MIMEText(html_body, 'html'))

                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)

                self._sent_today += 1
                log_activity("email_sent", f"Email sent to {to_address}: {subject}")
                return True, tracking_id

            except smtplib.SMTPRecipientsRefused:
                return False, f"Recipient refused: {to_address}"
            except smtplib.SMTPAuthenticationError:
                return False, "SMTP authentication failed"
            except Exception as e:
                log_activity("email_error", f"Send error to {to_address}: {str(e)}")
                return False, str(e)

    def send_outreach(self, lead_id: int, campaign_id: int,
                      lead: dict, subject: str, body: str) -> Tuple[bool, str]:
        """Send outreach email and log it."""
        ok, result = self.send_email(
            to_address=lead.get('email', ''),
            subject=subject,
            body=body,
        )
        if ok:
            log_email(lead_id, campaign_id, 'outreach', subject, body)
        return ok, result

    def send_notification(self, notification_email: str, lead: dict,
                          outreach_subject: str, outreach_body: str):
        """Send notification to the user about an outreach email sent."""
        subject = f"[HuntAI] New outreach sent to {lead.get('company_name', 'a lead')}"
        body = f"""HuntAI Outreach Notification
{'=' * 50}

LEAD DETAILS
Company:      {lead.get('company_name', 'N/A')}
Email:        {lead.get('email', 'N/A')}
Industry:     {lead.get('industry', 'N/A')}
Location:     {lead.get('location', 'N/A')}
Lead Score:   {lead.get('lead_score', 'N/A')}/10
Source:       {lead.get('source', 'N/A')}

WHY SELECTED
{lead.get('qualification', 'Matched target customer profile')}

OUTREACH EMAIL SENT
Subject: {outreach_subject}
---
{outreach_body}
---

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Dashboard: http://localhost:3000

— HuntAI Agent
"""
        self.send_email(notification_email, subject, body)


class InboxMonitor:
    """Monitors inbox for replies."""

    def __init__(self, config):
        self.config = config
        self.running = False
        self._thread = None

    @property
    def imap_host(self):
        smtp_host = self.config.get('smtp_host', 'smtp.gmail.com')
        # Derive IMAP from SMTP host
        if 'gmail' in smtp_host:
            return 'imap.gmail.com'
        if 'yahoo' in smtp_host:
            return 'imap.mail.yahoo.com'
        if 'outlook' in smtp_host or 'hotmail' in smtp_host:
            return 'imap-mail.outlook.com'
        return smtp_host.replace('smtp.', 'imap.')

    def start(self, callback=None):
        """Start background inbox monitoring."""
        self.running = True
        self.callback = callback
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _monitor_loop(self):
        while self.running:
            try:
                self._check_inbox()
            except Exception as e:
                log_activity("inbox_error", f"Inbox monitor error: {str(e)}")
            time.sleep(300)  # Check every 5 minutes

    def _check_inbox(self):
        username = self.config.get('email_address', '')
        password = self.config.get('email_password', '')
        if not username or not password:
            return

        try:
            mail = imaplib.IMAP4_SSL(self.imap_host)
            mail.login(username, password)
            mail.select('INBOX')

            # Search for unread emails
            _, message_numbers = mail.search(None, 'UNSEEN')
            for num in message_numbers[0].split():
                _, msg_data = mail.fetch(num, '(RFC822)')
                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)

                from_addr = msg.get('From', '')
                subject = msg.get('Subject', '')
                body = self._get_body(msg)

                log_activity("reply_received", f"Reply from {from_addr}: {subject}")
                if self.callback:
                    self.callback({
                        'from': from_addr,
                        'subject': subject,
                        'body': body,
                    })

            mail.logout()
        except Exception as e:
            pass  # Silent fail on IMAP errors

    def _get_body(self, msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode('utf-8', errors='replace')
        else:
            return msg.get_payload(decode=True).decode('utf-8', errors='replace')
        return ""

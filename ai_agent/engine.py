"""
HuntAI AI Decision Engine
Uses local Ollama model for lead qualification and email generation.
"""

import json
import httpx
from typing import Dict, Tuple, Optional
from database.db import log_activity

OLLAMA_BASE = "http://localhost:11434"
MODEL = "glm4:9b"  # Default model, configurable


class AIEngine:
    """Local AI engine powered by Ollama."""

    def __init__(self, model: str = MODEL, config=None):
        self.model = model
        self.config = config
        self._user_context = None

    def _get_user_context(self) -> str:
        if self.config:
            return (
                f"Company: {self.config.get('company_name', 'N/A')}\n"
                f"Service: {self.config.get('service_description', 'N/A')}\n"
                f"Target customer: {self.config.get('target_customer', 'B2B')}\n"
                f"Target industry: {self.config.get('target_industry', 'any')}\n"
                f"Target location: {self.config.get('target_location', 'any')}\n"
                f"Ideal client size: {self.config.get('ideal_client_size', 'any')}"
            )
        return "No user context available."

    def chat(self, prompt: str, system: str = "") -> str:
        """Send a prompt to the Ollama model and return the response."""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            resp = httpx.post(
                f"{OLLAMA_BASE}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False},
                timeout=120,
            )
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "")
            else:
                log_activity("ai_error", f"Ollama returned {resp.status_code}")
                return ""
        except Exception as e:
            log_activity("ai_error", f"Ollama error: {str(e)}")
            return ""

    def qualify_lead(self, lead: Dict) -> Dict:
        """
        Analyze a lead and return qualification data:
        - score (1-10)
        - reasoning
        - is_qualified (bool)
        """
        system = """You are an expert B2B sales qualifier. 
        Analyze business leads and score them on a scale of 1-10.
        Always respond with valid JSON only. No markdown, no extra text.
        """

        prompt = f"""
User's business context:
{self._get_user_context()}

Lead to evaluate:
Company: {lead.get('company_name', 'Unknown')}
Industry: {lead.get('industry', 'Unknown')}
Location: {lead.get('location', 'Unknown')}
Size: {lead.get('employee_count', 'Unknown')}
Description: {lead.get('description', '')}
Website: {lead.get('website', '')}

Score this lead 1-10 based on how well it matches the user's ideal customer profile.
Respond with JSON only:
{{
  "score": <1-10>,
  "reasoning": "<2-3 sentences explaining the score>",
  "is_qualified": <true/false>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "concerns": ["<concern 1>"]
}}
"""
        response = self.chat(prompt, system)
        try:
            # Strip any markdown code fences
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            return json.loads(clean.strip())
        except Exception:
            return {
                "score": 5,
                "reasoning": "Unable to fully qualify — proceed with caution.",
                "is_qualified": True,
                "strengths": [],
                "concerns": ["AI qualification failed"],
            }

    def generate_outreach_email(self, lead: Dict, user_context: Dict = None) -> Dict:
        """Generate a personalized outreach email for a lead."""
        ctx = user_context or (self.config.all() if self.config else {})

        system = """You are an expert B2B outreach copywriter. 
        Write personalized, concise, and compelling cold emails.
        Avoid generic openers like "I hope this email finds you well."
        Always respond with valid JSON only. No markdown, no extra text.
        """

        prompt = f"""
Write a cold outreach email from:
Sender: {ctx.get('user_name', 'Sales Rep')}
Company: {ctx.get('company_name', 'Our Company')}
Service: {ctx.get('service_description', 'Our service')}

To this prospect:
Company: {lead.get('company_name', 'Unknown Company')}
Industry: {lead.get('industry', 'Unknown')}
Location: {lead.get('location', '')}
Description: {lead.get('description', '')}

Requirements:
- 3-4 short paragraphs
- Mention a specific detail about THEIR business
- Explain how our service helps THEIR specific situation
- End with a simple, low-friction CTA
- Professional but human tone

Respond with JSON only:
{{
  "subject": "<compelling subject line>",
  "body": "<full email body>",
  "tone": "professional/friendly/direct",
  "cta": "<the specific call to action>"
}}
"""
        response = self.chat(prompt, system)
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            return json.loads(clean.strip())
        except Exception:
            # Fallback template
            company_name = ctx.get('company_name', 'us')
            user_name = ctx.get('user_name', 'The Team')
            service = ctx.get('service_description', 'our services')
            lead_company = lead.get('company_name', 'your company')

            return {
                "subject": f"Quick question about {lead_company}",
                "body": f"""Hi there,

I came across {lead_company} and was impressed by what you're building in the {lead.get('industry', '')} space.

At {company_name}, we help companies like yours with {service}. I thought there might be a good fit here.

Would you be open to a 15-minute call this week to explore?

Best,
{user_name}
{company_name}""",
                "tone": "professional",
                "cta": "15-minute discovery call",
            }

    def generate_follow_up(self, lead: Dict, previous_email: str, follow_up_number: int) -> Dict:
        """Generate a follow-up email."""
        system = "You are an expert at B2B follow-up emails. Keep them short, add value, avoid being pushy. Respond with JSON only."

        prompt = f"""
Write follow-up #{follow_up_number} for this lead who hasn't responded:
Company: {lead.get('company_name')}
Industry: {lead.get('industry')}

Previous email sent:
{previous_email[:500]}

Write a short, different angle follow-up. Respond with JSON:
{{
  "subject": "Re: <original subject or new angle>",
  "body": "<follow-up email, max 3 paragraphs>",
  "angle": "<what new angle you took>"
}}
"""
        response = self.chat(prompt, system)
        try:
            clean = response.strip().lstrip("```json").lstrip("```").rstrip("```")
            return json.loads(clean)
        except:
            return {
                "subject": f"Re: Following up",
                "body": f"Hi again,\n\nJust wanted to circle back on my previous message. Would love to connect when you have a moment.\n\nBest,\n{self.config.get('user_name', '') if self.config else ''}",
                "angle": "simple bump",
            }

    def classify_reply(self, reply_text: str) -> Dict:
        """Classify an incoming email reply."""
        system = "Classify email replies for a sales team. Respond with JSON only."

        prompt = f"""
Classify this email reply:
---
{reply_text[:1000]}
---

Respond with JSON:
{{
  "classification": "interested/not_interested/needs_more_info/wrong_person/out_of_office/unsubscribe",
  "sentiment": "positive/neutral/negative",
  "suggested_action": "<what to do next>",
  "urgency": "high/medium/low",
  "summary": "<one line summary>"
}}
"""
        response = self.chat(prompt, system)
        try:
            clean = response.strip().lstrip("```json").lstrip("```").rstrip("```")
            return json.loads(clean)
        except:
            return {
                "classification": "needs_more_info",
                "sentiment": "neutral",
                "suggested_action": "Review manually",
                "urgency": "medium",
                "summary": reply_text[:100],
            }

    def suggest_campaign_improvements(self, stats: Dict) -> str:
        """Generate campaign improvement suggestions based on stats."""
        prompt = f"""
Analyze these email campaign statistics and provide 3 specific improvement suggestions:

Emails sent: {stats.get('emails_sent', 0)}
Reply rate: {stats.get('reply_rate', '0%')}
Open rate: {stats.get('open_rate', '0%')}
Leads qualified: {stats.get('leads_qualified', 0)}
Total leads: {stats.get('total_leads', 0)}

Be specific and actionable. Format as a numbered list.
"""
        return self.chat(prompt)

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
            return r.status_code == 200
        except:
            return False

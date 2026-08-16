import json
import logging
from typing import Dict, Any, List
import httpx
from .provider import BaseAIProvider
from .fallback_provider import FallbackProvider
from ..models import SentinelSummary
from ..config import settings

logger = logging.getLogger(__name__)

class GroqProvider(BaseAIProvider):
    """Groq Free Tier (Llama 3.3 70B / Mixtral) ultra-fast inference provider."""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.fallback = FallbackProvider()

    def generate_summary(self, title: str, content: str, category: str) -> SentinelSummary:
        if not self.api_key:
            return self.fallback.generate_summary(title, content, category)

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        prompt = f"""Analyze this technology news story and return a JSON object.
Title: {title}
Category: {category}
Content: {content[:2000]}

Format:
{{
  "what": "1-sentence what happened",
  "why": "why developers should care",
  "action": "action recommendation",
  "key_points": ["point 1", "point 2", "point 3"]
}}"""
        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.post(url, headers=headers, json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                })
                if res.status_code == 200:
                    data = res.json()
                    parsed = json.loads(data["choices"][0]["message"]["content"])
                    return SentinelSummary(
                        what=parsed.get("what", title),
                        why=parsed.get("why", "Relevant technology update."),
                        action=parsed.get("action", "Learn more on official docs."),
                        key_points=parsed.get("key_points", [])
                    )
        except Exception as e:
            logger.warning(f"Groq API error, falling back: {e}")

        return self.fallback.generate_summary(title, content, category)

    def generate_daily_digest(self, news_items: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate_daily_digest(news_items, opportunities)
        # Groq implementation mirroring OpenAI chat completion format
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            news_titles = [f"- {n.get('title')}" for n in news_items[:6]]
            opp_titles = [f"- {o.get('title')} ({o.get('normal_value', 'Free')})" for o in opportunities[:6]]
            prompt = f"""Generate nightly tech intelligence digest in JSON:
News: {chr(10).join(news_titles)}
Opps: {chr(10).join(opp_titles)}

JSON: {{"headline": "...", "thirty_sec_summary": "...", "sentinel_take": "..."}}"""
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                })
                if res.status_code == 200:
                    return json.loads(res.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning(f"Groq digest error: {e}")

        return self.fallback.generate_daily_digest(news_items, opportunities)

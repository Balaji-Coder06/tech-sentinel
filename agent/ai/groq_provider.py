import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from .provider import BaseAIProvider
from .fallback_provider import FallbackProvider
from ..models import SentinelSummary
from ..config import settings

logger = logging.getLogger(__name__)

class GroqProvider(BaseAIProvider):
    """Groq Free Tier (Llama 3.3 70B Versatile) ultra-fast inference provider."""
    
    def __init__(self, fallback: Optional[BaseAIProvider] = None):
        self.api_key = settings.GROQ_API_KEY
        self.fallback = fallback or FallbackProvider()
        self.model = "llama-3.3-70b-versatile"

    def generate_summary(self, title: str, content: str, category: str) -> SentinelSummary:
        if not self.api_key:
            return self.fallback.generate_summary(title, content, category)

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
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
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                })
                if res.status_code == 200:
                    data = res.json()
                    parsed = json.loads(data["choices"][0]["message"]["content"])
                    logger.info(f"⚡ [AI Groq: {self.model}] Summarized: '{title[:45]}...'")
                    return SentinelSummary(
                        what=parsed.get("what", title),
                        why=parsed.get("why", "Relevant technology update."),
                        action=parsed.get("action", "Learn more on official docs."),
                        key_points=parsed.get("key_points", [])
                    )
                else:
                    logger.warning(f"Groq API returned HTTP {res.status_code}, cascading to fallback.")
        except Exception as e:
            logger.warning(f"Groq API error ({e}), cascading to fallback.")

        return self.fallback.generate_summary(title, content, category)

    def generate_daily_digest(self, news_items: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate_daily_digest(news_items, opportunities)

        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            news_titles = [f"- {n.get('title')}" for n in news_items[:6]]
            opp_titles = [f"- {o.get('title')} ({o.get('normal_value', 'Free')})" for o in opportunities[:6]]
            prompt = f"""Generate nightly tech intelligence digest in JSON:
News:
{chr(10).join(news_titles)}

Opportunities:
{chr(10).join(opp_titles)}

Return JSON with exact keys:
{{
  "headline": "Punchy newspaper style headline",
  "thirty_sec_summary": "Crisp 2-sentence summary of today's key developments and promotions",
  "sentinel_take": "Thoughtful editorial analysis of what today's shifts mean for developers"
}}"""
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                })
                if res.status_code == 200:
                    data = res.json()
                    parsed = json.loads(data["choices"][0]["message"]["content"])
                    logger.info(f"⚡ [AI Groq: {self.model}] Nightly digest generated successfully.")
                    return parsed
                else:
                    logger.warning(f"Groq digest returned HTTP {res.status_code}, cascading to fallback.")
        except Exception as e:
            logger.warning(f"Groq digest error ({e}), cascading to fallback.")

        return self.fallback.generate_daily_digest(news_items, opportunities)

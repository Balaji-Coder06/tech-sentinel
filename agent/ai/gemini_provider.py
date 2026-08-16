import json
import logging
from typing import Dict, Any, List
import httpx
from .provider import BaseAIProvider
from .fallback_provider import FallbackProvider
from ..models import SentinelSummary
from ..config import settings

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    """Google Gemini Free Tier integration."""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.fallback = FallbackProvider()

    def generate_summary(self, title: str, content: str, category: str) -> SentinelSummary:
        if not self.api_key:
            return self.fallback.generate_summary(title, content, category)

        prompt = f"""
You are Tech Sentinel AI. Analyze this technology news story and return a JSON object.

Title: {title}
Category: {category}
Content: {content[:2000]}

Return JSON with exact keys:
{{
  "what": "Concise 1-sentence explanation of what happened",
  "why": "Personalized explanation of why a developer or student should care",
  "action": "Direct action recommendation (e.g. Try API, Upgrade package, Read docs)",
  "key_points": ["point 1", "point 2", "point 3"]
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                })
                if res.status_code == 200:
                    data = res.json()
                    text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text_resp)
                    return SentinelSummary(
                        what=parsed.get("what", title),
                        why=parsed.get("why", "Relevant technology update."),
                        action=parsed.get("action", "Learn more on official docs."),
                        key_points=parsed.get("key_points", [])
                    )
        except Exception as e:
            logger.warning(f"Gemini API error, falling back: {e}")

        return self.fallback.generate_summary(title, content, category)

    def generate_daily_digest(self, news_items: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate_daily_digest(news_items, opportunities)

        news_titles = [f"- {n.get('title')}" for n in news_items[:6]]
        opp_titles = [f"- {o.get('title')} ({o.get('normal_value', 'Free')})" for o in opportunities[:6]]

        prompt = f"""
You are the chief intelligence editor for Tech Sentinel. Generate a nightly digest.

Top News Today:
{chr(10).join(news_titles)}

Top Free Opportunities:
{chr(10).join(opp_titles)}

Return JSON with exact keys:
{{
  "headline": "Punchy newspaper style headline",
  "thirty_sec_summary": "Crisp 2-sentence summary of today's key developments and promotions",
  "sentinel_take": "Thoughtful editorial analysis of what today's shifts mean for developers"
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(url, json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                })
                if res.status_code == 200:
                    data = res.json()
                    text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text_resp)
        except Exception as e:
            logger.warning(f"Gemini digest error, falling back: {e}")

        return self.fallback.generate_daily_digest(news_items, opportunities)

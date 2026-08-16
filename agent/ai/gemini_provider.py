import json
import time
import logging
from typing import Dict, Any, List, Optional
import httpx
from .provider import BaseAIProvider
from .fallback_provider import FallbackProvider
from .rate_limiter import parse_retry_after, apply_pacing_delay
from ..models import SentinelSummary
from ..config import settings

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    """Google Gemini Free Tier (gemini-2.5-flash) inference provider with rate-aware backoff."""
    
    def __init__(self, fallback: Optional[BaseAIProvider] = None):
        self.api_key = settings.GEMINI_API_KEY
        self.fallback = fallback or FallbackProvider()
        self.model = "gemini-2.5-flash"

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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        max_retries = max(1, settings.AI_MAX_RETRIES)
        base_delay = settings.AI_RETRY_BASE_DELAY_SECONDS

        for attempt in range(max_retries):
            try:
                apply_pacing_delay()
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(url, json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    })

                    if res.status_code == 200:
                        data = res.json()
                        text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text_resp)
                        logger.info(f"✨ [AI Gemini: {self.model}] Summarized: '{title[:45]}...'")
                        return SentinelSummary(
                            what=parsed.get("what", title),
                            why=parsed.get("why", "Relevant technology update."),
                            action=parsed.get("action", "Learn more on official docs."),
                            key_points=parsed.get("key_points", [])
                        )
                    elif res.status_code == 429:
                        wait_sec = parse_retry_after(res, default_delay=base_delay * (2 ** attempt))
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"⏳ [AI Gemini] Rate limit (429) hit for '{title[:30]}...'. "
                                f"Backing off {wait_sec:.1f}s before retry ({attempt + 2}/{max_retries})..."
                            )
                            time.sleep(wait_sec)
                            continue
                        else:
                            logger.warning(
                                f"⚠️ [AI Gemini] 429 persisted after {max_retries} attempts for '{title[:30]}...'. "
                                f"Cascading to fallback provider."
                            )
                            break
                    else:
                        logger.warning(f"Gemini API returned HTTP {res.status_code}, cascading to fallback.")
                        break
            except Exception as e:
                logger.warning(f"Gemini API error ({e}), cascading to fallback.")
                break

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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        max_retries = max(1, settings.AI_MAX_RETRIES)
        base_delay = settings.AI_RETRY_BASE_DELAY_SECONDS

        for attempt in range(max_retries):
            try:
                apply_pacing_delay()
                with httpx.Client(timeout=12.0) as client:
                    res = client.post(url, json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    })

                    if res.status_code == 200:
                        data = res.json()
                        text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
                        logger.info(f"✨ [AI Gemini: {self.model}] Nightly digest generated successfully.")
                        return json.loads(text_resp)
                    elif res.status_code == 429:
                        wait_sec = parse_retry_after(res, default_delay=base_delay * (2 ** attempt))
                        if attempt < max_retries - 1:
                            logger.warning(f"⏳ [AI Gemini] Digest rate limit (429). Waiting {wait_sec:.1f}s before retry ({attempt + 2}/{max_retries})...")
                            time.sleep(wait_sec)
                            continue
                        else:
                            logger.warning(f"⚠️ [AI Gemini] Digest 429 persisted after {max_retries} attempts. Cascading to fallback.")
                            break
                    else:
                        logger.warning(f"Gemini digest returned HTTP {res.status_code}, cascading to fallback.")
                        break
            except Exception as e:
                logger.warning(f"Gemini digest error ({e}), cascading to fallback.")
                break

        return self.fallback.generate_daily_digest(news_items, opportunities)

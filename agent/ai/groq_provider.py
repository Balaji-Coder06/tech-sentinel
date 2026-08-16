import json
import time
import logging
from typing import Dict, Any, List, Optional
import httpx
from .provider import BaseAIProvider
from .fallback_provider import FallbackProvider
from .rate_limiter import parse_retry_after, apply_global_pacing, record_request_completed
from ..models import SentinelSummary
from ..config import settings

logger = logging.getLogger(__name__)

class GroqProvider(BaseAIProvider):
    """Groq Free Tier (Llama 3.3 70B Versatile) ultra-fast inference provider with global rate-aware backoff."""
    
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

        max_retries = max(1, settings.AI_MAX_RETRIES)
        base_delay = settings.AI_RETRY_BASE_DELAY_SECONDS

        for attempt in range(max_retries):
            try:
                apply_global_pacing()
                with httpx.Client(timeout=8.0) as client:
                    res = client.post(url, headers=headers, json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    })
                    record_request_completed()

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

                    elif res.status_code == 429:
                        wait_sec = parse_retry_after(res, default_delay=base_delay * (2 ** attempt))
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"⏳ [AI Groq] Rate limit (429) hit for '{title[:30]}...'. "
                                f"Backing off {wait_sec:.1f}s before retry ({attempt + 2}/{max_retries})..."
                            )
                            time.sleep(wait_sec)
                            record_request_completed()
                            continue
                        else:
                            logger.warning(
                                f"⚠️ [AI Groq] 429 persisted after {max_retries} attempts for '{title[:30]}...'. "
                                f"Cascading to fallback provider."
                            )
                            break
                    else:
                        logger.warning(f"Groq API returned HTTP {res.status_code}, cascading to fallback.")
                        break

            except Exception as e:
                record_request_completed()
                logger.warning(f"Groq API error ({e}), cascading to fallback.")
                break

        return self.fallback.generate_summary(title, content, category)

    def generate_daily_digest(self, news_items: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate_daily_digest(news_items, opportunities)

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

        max_retries = max(1, settings.AI_MAX_RETRIES)
        base_delay = settings.AI_RETRY_BASE_DELAY_SECONDS

        for attempt in range(max_retries):
            try:
                apply_global_pacing()
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(url, headers=headers, json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    })
                    record_request_completed()

                    if res.status_code == 200:
                        data = res.json()
                        parsed = json.loads(data["choices"][0]["message"]["content"])
                        logger.info(f"⚡ [AI Groq: {self.model}] Nightly digest generated successfully.")
                        return parsed
                    elif res.status_code == 429:
                        wait_sec = parse_retry_after(res, default_delay=base_delay * (2 ** attempt))
                        if attempt < max_retries - 1:
                            logger.warning(f"⏳ [AI Groq] Digest rate limit (429). Waiting {wait_sec:.1f}s before retry ({attempt + 2}/{max_retries})...")
                            time.sleep(wait_sec)
                            record_request_completed()
                            continue
                        else:
                            logger.warning(f"⚠️ [AI Groq] Digest 429 persisted after {max_retries} attempts. Cascading to fallback.")
                            break
                    else:
                        logger.warning(f"Groq digest returned HTTP {res.status_code}, cascading to fallback.")
                        break
            except Exception as e:
                record_request_completed()
                logger.warning(f"Groq digest error ({e}), cascading to fallback.")
                break

        return self.fallback.generate_daily_digest(news_items, opportunities)

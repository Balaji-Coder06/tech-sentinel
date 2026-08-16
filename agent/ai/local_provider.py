import json
import logging
from typing import Dict, Any, List
import httpx
from .provider import BaseAIProvider
from .fallback_provider import FallbackProvider
from ..models import SentinelSummary
from ..config import settings

logger = logging.getLogger(__name__)

class LocalProvider(BaseAIProvider):
    """Local Ollama / OpenAI-compatible API provider."""

    def __init__(self):
        self.base_url = settings.LOCAL_AI_BASE_URL
        self.model = settings.LOCAL_AI_MODEL
        self.fallback = FallbackProvider()

    def generate_summary(self, title: str, content: str, category: str) -> SentinelSummary:
        try:
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            prompt = f"Analyze: {title}. Content: {content[:1500]}. Respond in JSON with what, why, action, key_points."
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "format": "json"
                })
                if res.status_code == 200:
                    parsed = json.loads(res.json()["choices"][0]["message"]["content"])
                    return SentinelSummary(
                        what=parsed.get("what", title),
                        why=parsed.get("why", "Key developer update."),
                        action=parsed.get("action", "Check official docs."),
                        key_points=parsed.get("key_points", [])
                    )
        except Exception:
            pass
        return self.fallback.generate_summary(title, content, category)

    def generate_daily_digest(self, news_items: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.fallback.generate_daily_digest(news_items, opportunities)

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..models import SentinelSummary

class BaseAIProvider(ABC):
    @abstractmethod
    def generate_summary(self, title: str, content: str, category: str) -> SentinelSummary:
        """Generates the signature Sentinel 3-part summary (What happened, Why it matters, What you can do)."""
        pass

    @abstractmethod
    def generate_daily_digest(self, news_items: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates the nightly headline, 30s summary, and Sentinel's Take."""
        pass

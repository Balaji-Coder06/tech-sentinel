from typing import Optional
from .fallback_provider import DeterministicEngine
from ..models import RawItem, SentinelSummary

class AISummarizer:
    """Produces signature Sentinel summaries using the deterministic NLP engine."""

    def __init__(self, engine: Optional[DeterministicEngine] = None):
        self.engine = engine or DeterministicEngine()

    def summarize(self, item: RawItem) -> SentinelSummary:
        return self.engine.generate_summary(
            title=item.title,
            content=item.content or item.description,
            category=item.category or "development"
        )

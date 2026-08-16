from .provider import BaseAIProvider
from ..models import RawItem, SentinelSummary

class AISummarizer:
    """Wrapper that invokes configured AI provider to produce Sentinel summaries."""

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider

    def summarize(self, item: RawItem) -> SentinelSummary:
        return self.provider.generate_summary(
            title=item.title,
            content=item.content or item.description,
            category=item.category or "development"
        )

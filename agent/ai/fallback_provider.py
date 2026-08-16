import re
from typing import Dict, Any, List
from .provider import BaseAIProvider
from ..models import SentinelSummary

class FallbackProvider(BaseAIProvider):
    """Deterministic, zero-cost NLP and heuristic AI provider.
    Ensures Tech Sentinel functions 100% reliably even without API keys or internet connection.
    """

    def generate_summary(self, title: str, content: str, category: str) -> SentinelSummary:
        # What happened: Clean primary sentence
        clean_title = re.sub(r'\[.*?\]|\(.*?\)', '', title).strip()
        what = f"{clean_title}."

        # Why it matters: Category-specific contextual reasoning
        category_reasons = {
            "ai": "Introduces new model capabilities and developer tooling to streamline pair-programming and AI integrations.",
            "cloud": "Provides scalable, cost-efficient infrastructure enhancements for deploying modern applications without vendor lock-in.",
            "development": "Streamlines engineering workflows, improves application performance, and reduces code boilerplate.",
            "open_source": "Expands open access tooling and community-driven repositories usable for commercial and personal projects.",
            "cybersecurity": "Crucial security insights to harden infrastructure against emerging vulnerabilities and zero-day threats.",
            "startups": "Key product launch updates and developer utilities to accelerate MVP delivery and market traction."
        }
        why = category_reasons.get(category.lower(), "Important technology update relevant to developers and engineering leaders.")

        # What you can do: Action recommendation
        action = "Review the official release documentation and evaluate integration into your current development roadmap."

        # Key points extraction
        sentences = [s.strip() for s in re.split(r'[\.\n]+', content) if len(s.strip()) > 20]
        key_points = sentences[:3] if sentences else [
            f"Key update regarding {category.upper()}",
            "Direct official documentation available",
            "Available immediately for developer evaluation"
        ]

        return SentinelSummary(
            what=what,
            why=why,
            action=action,
            key_points=key_points
        )

    def generate_daily_digest(self, news_items: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        top_titles = [n.get("title", "") for n in news_items[:3]]
        opp_count = len(opportunities)
        news_count = len(news_items)

        headline = f"Today's Intelligence: {top_titles[0] if top_titles else 'Major Technology Developments'}"
        thirty_sec = (
            f"Today tracked {news_count} essential technology developments across AI, cloud, and engineering. "
            f"Found {opp_count} actionable free opportunities with direct claim links before deadlines expire."
        )
        sentinel_take = (
            "Engineering velocity is accelerating with accessible AI tools and generous free tiers. "
            "Prioritize claiming expiring cloud credits and certification vouchers today."
        )

        return {
            "headline": headline,
            "thirty_sec_summary": thirty_sec,
            "sentinel_take": sentinel_take
        }

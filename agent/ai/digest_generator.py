import uuid
from datetime import datetime
from typing import List, Dict, Any
from .provider import BaseAIProvider
from ..models import DailyReport

class DailyDigestGenerator:
    """Consolidates news, opportunities, and rankings into the signature Nightly Intelligence Report."""

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider

    def generate(
        self,
        news_items: List[Dict[str, Any]],
        opportunities: List[Dict[str, Any]],
        target_date: str = None
    ) -> DailyReport:
        date_str = target_date or datetime.utcnow().strftime("%Y-%m-%d")
        
        # 1. Rank & select top items
        sorted_news = sorted(news_items, key=lambda x: x.get("importance_score", 0), reverse=True)
        sorted_opps = sorted(opportunities, key=lambda x: x.get("importance_score", 0), reverse=True)

        top_stories = [
            {
                "id": n.get("id"),
                "title": n.get("title"),
                "category": n.get("category"),
                "score": n.get("importance_score"),
                "summary": n.get("summary_what") or n.get("description", "")[:120]
            }
            for n in sorted_news[:5]
        ]

        free_opportunities = [
            {
                "id": o.get("id"),
                "title": o.get("title"),
                "provider": o.get("provider"),
                "value": o.get("normal_value") or "FREE",
                "eligibility": o.get("eligibility", "All"),
                "claim_url": o.get("claim_url")
            }
            for o in sorted_opps[:5]
        ]

        student_opportunities = [
            {
                "id": o.get("id"),
                "title": o.get("title"),
                "value": o.get("normal_value")
            }
            for o in sorted_opps if "student" in (o.get("eligibility", "") + o.get("description", "")).lower()
        ][:3]

        expiring_soon = [
            {
                "id": o.get("id"),
                "title": o.get("title"),
                "expires": o.get("expiry_date", "Soon")
            }
            for o in sorted_opps if o.get("is_expiring_soon") or o.get("status") == "EXPIRING_SOON"
        ][:3]

        open_source = [
            {"title": n.get("title"), "url": n.get("url")}
            for n in sorted_news if n.get("category") == "open_source"
        ][:3]

        # 2. AI synthesis for headline, 30s summary, and Sentinel's Take
        ai_resp = self.provider.generate_daily_digest(sorted_news, sorted_opps)

        report_id = f"rep_{date_str.replace('-', '_')}"

        return DailyReport(
            id=report_id,
            date=date_str,
            title="Tech Sentinel Daily Intelligence",
            headline=ai_resp.get("headline", "Today in Technology & Opportunities"),
            thirty_sec_summary=ai_resp.get("thirty_sec_summary", "Comprehensive digest of today's key developer updates and free promotions."),
            top_stories=top_stories,
            free_opportunities=free_opportunities,
            student_opportunities=student_opportunities,
            open_source_highlights=open_source,
            expiring_soon=expiring_soon,
            sentinel_take=ai_resp.get("sentinel_take", "Stay ahead by taking advantage of verified opportunities and AI tooling advances."),
            stats={
                "total_news_evaluated": len(news_items),
                "total_opportunities_tracked": len(opportunities),
                "expiring_count": len(expiring_soon)
            }
        )

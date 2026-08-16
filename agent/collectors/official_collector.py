import logging
from datetime import datetime
from typing import List
from .base import BaseCollector
from ..models import RawItem

logger = logging.getLogger(__name__)

class OfficialCollector(BaseCollector):
    """Monitors curated official free opportunities (Google Cloud Free, AWS Activate/Free, Azure Student, GitHub Pack, etc.)."""
    
    CURATED_PROMOTIONS = [
        {
            "title": "Google Cloud Free Program: $300 Credits + Free Tier Compute",
            "description": "Google Cloud provides new accounts with $300 in free credits to spend over 90 days, plus 20+ always-free products including e2-micro VM, Cloud Functions, and BigQuery (1TB/mo querying free).",
            "url": "https://cloud.google.com/free",
            "provider": "Google Cloud",
            "category": "cloud",
            "value": "$300",
            "eligibility": "All Developers"
        },
        {
            "title": "GitHub Student Developer Pack (JetBrains, GitHub Copilot, DigitalOcean, Azure)",
            "description": "GitHub Education bundle providing students free access to GitHub Copilot, JetBrains All Products Pack, $200 DigitalOcean credits, free Namecheap .me domains, and Canva Pro.",
            "url": "https://education.github.com/pack",
            "provider": "GitHub Education",
            "category": "education",
            "value": "$200,000+",
            "eligibility": "Students"
        },
        {
            "title": "Oracle Cloud Free Tier: 4 OCPU ARM Compute + 24GB RAM Free Forever",
            "description": "Oracle Cloud Always Free services include 4 Ampere A1 ARM compute cores, 24GB memory, 200GB block storage, and 2 Autonomous Databases at ₹0 forever.",
            "url": "https://www.oracle.com/cloud/free/",
            "provider": "Oracle",
            "category": "cloud",
            "value": "Always Free",
            "eligibility": "All Developers"
        },
        {
            "title": "Cloudflare Free Plan: Unlimited Edge CDN, Workers (100k req/day), D1 Database",
            "description": "Cloudflare offers free DNS, unlimited DDoS protection, global CDN, 100,000 daily Worker requests, Pages hosting, and D1 serverless database on their free tier.",
            "url": "https://www.cloudflare.com/plans/free/",
            "provider": "Cloudflare",
            "category": "cloud",
            "value": "Free Forever",
            "eligibility": "All Developers"
        },
        {
            "title": "Microsoft Learn Student Ambassador Program & Free Azure $100/yr",
            "description": "Students can apply for Microsoft Learn Student Ambassadors to receive free Azure $100 annual credits, Visual Studio Enterprise subscription, LinkedIn Learning, and free exam vouchers.",
            "url": "https://studentambassadors.microsoft.com/",
            "provider": "Microsoft",
            "category": "education",
            "value": "$1,000+/year",
            "eligibility": "Students"
        }
    ]

    def fetch(self) -> List[RawItem]:
        items: List[RawItem] = []
        for promo in self.CURATED_PROMOTIONS:
            items.append(RawItem(
                title=promo["title"],
                description=promo["description"],
                content=f"{promo['title']}. Provider: {promo['provider']}. Value: {promo['value']}. Eligibility: {promo['eligibility']}. URL: {promo['url']}",
                url=promo["url"],
                source_id=self.source_id,
                source_name=f"Official: {promo['provider']}",
                category=promo["category"],
                published_at=datetime.utcnow().isoformat(),
                raw_metadata=promo
            ))
        logger.info(f"OfficialCollector loaded {len(items)} official opportunity feeds.")
        return items

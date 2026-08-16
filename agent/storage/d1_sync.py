import logging
from typing import List, Dict, Any, Optional
import httpx
from ..config import settings
from ..models import NewsItem, Opportunity, DailyReport, SystemStatus

logger = logging.getLogger(__name__)

class D1SyncClient:
    """Client for synchronizing processed intelligence data and Telegram subscribers
    from Python Agent (e.g. GitHub Actions or local service) directly to/from Cloudflare D1
    via the Cloudflare Worker Ingestion & Telegram API.
    """

    def __init__(self, worker_url: Optional[str] = None, secret: Optional[str] = None):
        raw_url = worker_url or settings.WORKER_API_URL or ""
        self.worker_url = raw_url.rstrip('/')
        self.secret = secret or settings.INGESTION_SECRET or ""

    @property
    def is_configured(self) -> bool:
        return bool(self.worker_url and self.secret)

    def sync_batch(
        self,
        news: Optional[List[NewsItem]] = None,
        opportunities: Optional[List[Opportunity]] = None,
        report: Optional[DailyReport] = None,
        status: Optional[SystemStatus] = None,
        telegram_users: Optional[List[Dict[str, Any]]] = None,
        preferences: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        if not self.is_configured:
            logger.info("Cloudflare Worker ingestion URL / secret not set. Skipping remote D1 sync.")
            return False

        payload: Dict[str, Any] = {
            "news": [n.model_dump() for n in news] if news else [],
            "opportunities": [o.model_dump() for o in opportunities] if opportunities else [],
            "report": report.model_dump() if report else None,
            "status": status.model_dump() if status else None,
            "telegram_users": telegram_users or [],
            "preferences": preferences or []
        }

        endpoint = f"{self.worker_url}/api/ingest"
        headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json",
            "User-Agent": settings.USER_AGENT
        }

        try:
            logger.info(
                f"🚀 Pushing data to Cloudflare D1 ({len(payload['news'])} news, "
                f"{len(payload['opportunities'])} opps, {len(payload['telegram_users'])} users, "
                f"{len(payload['preferences'])} prefs)..."
            )
            with httpx.Client(timeout=30.0) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    logger.info(f"✅ Successfully synchronized with Cloudflare D1: {data.get('message', 'OK')}")
                    return True
                else:
                    logger.error(f"❌ D1 sync failed (HTTP {res.status_code}): {res.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Exception during D1 synchronization: {e}")
            return False

    def sync_telegram_data(
        self,
        users: List[Dict[str, Any]],
        preferences: List[Dict[str, Any]]
    ) -> bool:
        """Pushes Telegram registered users and preference profiles to Cloudflare D1."""
        return self.sync_batch(telegram_users=users, preferences=preferences)

    def get_telegram_subscribers(self, subscribed_only: bool = False) -> List[Dict[str, Any]]:
        """
        Securely fetches subscribed Telegram users and their resolved preferences
        from Cloudflare D1 via the Worker API.
        """
        if not self.is_configured:
            logger.warning("Cloudflare Worker URL / Ingestion Secret not configured. Cannot fetch D1 subscribers.")
            return []

        endpoint = f"{self.worker_url}/api/telegram/subscribers"
        if subscribed_only:
            endpoint += "?subscribed_only=true"

        headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json",
            "User-Agent": settings.USER_AGENT
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(endpoint, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    subscribers = data.get("data", [])
                    logger.info(f"✅ Retrieved {len(subscribers)} subscribed Telegram users from Cloudflare D1.")
                    return subscribers
                elif res.status_code == 401:
                    logger.error("❌ Cloudflare D1 subscribers query unauthorized: Invalid Ingestion Secret.")
                    return []
                else:
                    logger.error(f"❌ Failed to fetch subscribers from D1 (HTTP {res.status_code}): {res.text}")
                    return []
        except Exception as e:
            logger.error(f"❌ Exception fetching subscribers from Cloudflare D1: {e}")
            return []

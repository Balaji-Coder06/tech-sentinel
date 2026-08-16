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
        raw_url = settings.WORKER_API_URL if worker_url is None else worker_url
        self.worker_url = (raw_url or "").rstrip('/')
        self.secret = settings.INGESTION_SECRET if secret is None else (secret or "")

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
            logger.warning(
                f"⚠️ Cloudflare D1 sync skipped: WORKER_API_URL ({'configured' if self.worker_url else 'missing'}) "
                f"or INGESTION_SECRET ({'configured' if self.secret else 'missing'}) is not set in environment/.env."
            )
            return False

        formatted_users = []
        for u in (telegram_users or []):
            u_copy = dict(u)
            is_enabled = 1 if u_copy.get("telegram_digest_enabled") in (1, True, "1", "true") else 0
            u_copy["telegram_digest_enabled"] = is_enabled
            formatted_users.append(u_copy)

        payload: Dict[str, Any] = {
            "news": [n.model_dump() for n in news] if news else [],
            "opportunities": [o.model_dump() for o in opportunities] if opportunities else [],
            "report": report.model_dump() if report else None,
            "status": status.model_dump() if status else None,
            "telegram_users": formatted_users,
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
                f"🚀 [D1 SYNC] Initiating push to {self.worker_url}/api/ingest: "
                f"{len(payload['news'])} news, {len(payload['opportunities'])} opps, "
                f"{len(payload['telegram_users'])} users, {len(payload['preferences'])} prefs"
            )
            for u in formatted_users:
                logger.info(
                    f"   👤 [D1 SYNC USER] user_id={u.get('user_id')}, chat_id={u.get('chat_id')}, "
                    f"telegram_digest_enabled={u.get('telegram_digest_enabled')}"
                )

            with httpx.Client(timeout=30.0) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                logger.info(f"📡 [D1 SYNC RESPONSE] HTTP Status: {res.status_code}")
                if res.status_code == 200:
                    data = res.json()
                    logger.info(f"✅ [D1 SYNC SUCCESS] Worker response: {data.get('message', 'OK')}")
                    return True
                else:
                    logger.error(f"❌ [D1 SYNC ERROR] HTTP {res.status_code}: {res.text[:300]}")
                    return False
        except Exception as e:
            logger.error(f"❌ [D1 SYNC EXCEPTION] {e}")
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

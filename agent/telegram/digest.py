import logging
import os
from typing import Dict, Any, List
import httpx

from ..config import settings
from ..storage.db import Database
from ..storage.d1_sync import D1SyncClient
from .service import TelegramBotService
from ..models import NewsItem, Opportunity

logger = logging.getLogger(__name__)

def fetch_d1_news_and_opps(worker_url: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetches latest news and active opportunities from Cloudflare D1 Worker API."""
    news_items: List[Dict[str, Any]] = []
    opps_items: List[Dict[str, Any]] = []

    clean_url = worker_url.rstrip('/')
    try:
        with httpx.Client(timeout=15.0) as client:
            res_news = client.get(f"{clean_url}/api/news")
            if res_news.status_code == 200:
                data = res_news.json()
                news_items = data.get("data", [])

            res_opps = client.get(f"{clean_url}/api/opportunities?status=ACTIVE")
            if res_opps.status_code == 200:
                data = res_opps.json()
                opps_items = data.get("data", [])
    except Exception as e:
        logger.error(f"Error fetching data from Worker API: {e}")

    return news_items, opps_items

def run_telegram_digest() -> Dict[str, Any]:
    """
    Executes the scheduled Telegram digest dispatch non-interactively.
    1. Retrieves active subscribers from Cloudflare D1 (or local SQLite if D1 unconfigured).
    2. Builds personalized digests tailored to each user's category preferences.
    3. Dispatches via TelegramBotService with fault isolation per user.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.info("🚀 Starting Tech Sentinel Scheduled Telegram Digest...")

    bot = TelegramBotService()
    if not bot.is_configured:
        logger.error("❌ Telegram Bot Token is not configured. Cannot dispatch digest.")
        return {"status": "error", "error": "TELEGRAM_BOT_TOKEN missing"}

    d1_client = D1SyncClient()
    db = Database()

    # 1. Fetch subscribed users (D1 remote first, local SQLite fallback)
    subscribers: List[Dict[str, Any]] = []
    if d1_client.is_configured:
        logger.info("📡 Querying subscribed Telegram users from Cloudflare D1...")
        d1_subs = d1_client.get_telegram_subscribers(subscribed_only=True)
        subscribers = [s for s in d1_subs if s.get("telegram_digest_enabled", True)]
    else:
        logger.info("💾 Querying subscribed Telegram users from local SQLite...")
        local_subs = db.get_subscribed_telegram_users()
        for u in local_subs:
            prefs = db.get_telegram_user_preferences(u["user_id"])
            subscribers.append({
                "user_id": u["user_id"],
                "chat_id": u["chat_id"],
                "username": u.get("username"),
                "first_name": u.get("first_name"),
                "preferences": prefs
            })

    if not subscribers:
        logger.info("ℹ️ No active Telegram digest subscribers found. Skipping dispatch.")
        return {"status": "success", "dispatched": 0, "failed": 0, "message": "No active subscribers"}

    logger.info(f"📋 Found {len(subscribers)} active Telegram digest subscriber(s).")

    # 2. Check if local database has news items, else populate from Worker API
    recent_news = db.get_recent_news(limit=10)
    if not recent_news and d1_client.is_configured and d1_client.worker_url:
        logger.info("📥 Local SQLite is empty (e.g. in GitHub Actions runner). Pulling news/opps from Cloudflare D1...")
        remote_news, remote_opps = fetch_d1_news_and_opps(d1_client.worker_url)
        # Hydrate local ephemeral SQLite so existing ranking and filtering methods work 100% identically
        for item in remote_news:
            try:
                db.insert_news_item(NewsItem(
                    id=item.get("id"),
                    title=item.get("title", ""),
                    description=item.get("description"),
                    content=item.get("content"),
                    url=item.get("url", ""),
                    source_name=item.get("source_name", "Source"),
                    category=item.get("category", "development"),
                    importance_score=item.get("importance_score", 50),
                    published_at=item.get("published_at", "")
                ))
            except Exception:
                pass

        for opp in remote_opps:
            try:
                db.insert_opportunity(Opportunity(
                    id=opp.get("id"),
                    title=opp.get("title", ""),
                    provider=opp.get("provider", ""),
                    opportunity_type=opp.get("opportunity_type", "software"),
                    category=opp.get("category", "development"),
                    claim_url=opp.get("claim_url", ""),
                    status=opp.get("status", "ACTIVE"),
                    importance_score=opp.get("importance_score", 80)
                ))
            except Exception:
                pass

    # 3. Deliver digest to each subscriber with fault isolation
    success_count = 0
    fail_count = 0

    for sub in subscribers:
        chat_id = str(sub.get("chat_id") or sub.get("user_id"))
        user_name = sub.get("first_name") or sub.get("username") or "Subscriber"
        user_prefs = sub.get("preferences") or {}

        try:
            msg_text, reply_markup = bot.build_digest_message(
                user_prefs=user_prefs,
                limit_news=4,
                limit_opps=3
            )
            delivered = bot.send_message(
                chat_id=chat_id,
                text=msg_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            if delivered:
                success_count += 1
                logger.info(f"✅ Digest delivered to subscriber: {user_name} (chat_id: {chat_id})")
                try:
                    db.record_telegram_digest_sent(chat_id)
                except Exception:
                    pass
            else:
                fail_count += 1
                logger.warning(f"⚠️ Failed to deliver digest to subscriber: {user_name} (chat_id: {chat_id})")
        except Exception as err:
            fail_count += 1
            logger.error(f"❌ Exception sending digest to subscriber {user_name} (chat_id: {chat_id}): {err}")

    logger.info(f"🏁 Digest dispatch completed. Delivered: {success_count}, Failed: {fail_count}")
    return {
        "status": "success",
        "dispatched": success_count,
        "failed": fail_count,
        "total_subscribers": len(subscribers)
    }

if __name__ == "__main__":
    run_telegram_digest()

import os
import html
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
import httpx

from ..config import settings
from ..storage.db import Database
from ..storage.d1_sync import D1SyncClient
from ..utils.taxonomy import normalize_category

logger = logging.getLogger(__name__)

def is_valid_telegram_button_url(url: Optional[str]) -> bool:
    """
    Checks if a URL is valid for Telegram inline keyboard buttons.
    Telegram strictly requires public HTTP/HTTPS URLs and rejects localhost or private IPs.
    """
    if not url or not isinstance(url, str):
        return False
    clean = url.strip().lower()
    if not (clean.startswith("http://") or clean.startswith("https://")):
        return False
    # Strictly reject localhost and local network addresses in Telegram buttons
    if any(blocked in clean for blocked in ["localhost", "127.0.0.1", "0.0.0.0", "::1", "local.test"]):
        return False
    return True

def get_public_web_app_url(path: str = "") -> Optional[str]:
    """
    Returns a valid public HTTPS web app URL if configured via WEB_APP_URL.
    Returns None if unconfigured, not HTTPS, or pointing to localhost.
    """
    public_url = (settings.WEB_APP_URL or os.getenv("WEB_APP_URL") or "").strip()
    if not public_url.startswith("https://"):
        return None
    if not is_valid_telegram_button_url(public_url):
        return None
    if path:
        return f"{public_url.rstrip('/')}/{path.lstrip('/')}"
    return public_url.rstrip('/')

def format_time_ago(iso_date: Optional[str]) -> str:
    """Formats an ISO 8601 date into a short human-readable relative time."""
    if not iso_date:
        return "recently"
    try:
        clean = iso_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff_sec = max(0, int((now - dt).total_seconds()))

        if diff_sec < 60:
            return "just now"
        elif diff_sec < 3600:
            return f"{diff_sec // 60}m ago"
        elif diff_sec < 86400:
            return f"{diff_sec // 3600}h ago"
        elif diff_sec < 604800:
            return f"{diff_sec // 86400}d ago"
        else:
            return dt.strftime("%b %d")
    except Exception:
        return "recently"

class TelegramBotService:
    """
    Isolated Telegram Bot Service for Tech Sentinel.
    Uses official Telegram Bot API (https://api.telegram.org).
    Reads bot token strictly from TELEGRAM_BOT_TOKEN environment variable.
    """

    def __init__(self, bot_token: Optional[str] = None, default_chat_id: Optional[str] = None, db: Optional[Database] = None):
        if bot_token is not None:
            self._bot_token = bot_token
        else:
            self._bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or settings.TELEGRAM_BOT_TOKEN or ""

        if default_chat_id is not None:
            self.default_chat_id = default_chat_id
        else:
            self.default_chat_id = os.getenv("TELEGRAM_CHAT_ID") or settings.TELEGRAM_CHAT_ID or ""

        self._db = db

    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = Database()
        return self._db

    @property
    def is_configured(self) -> bool:
        """Returns True if a bot token is configured."""
        return bool(self._bot_token.strip())

    @property
    def api_base_url(self) -> str:
        """Constructs Telegram API base URL securely."""
        return f"https://api.telegram.org/bot{self._bot_token}"

    def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """
        Calls Telegram getMe API endpoint to verify token and retrieve bot metadata.
        Returns dict with id, is_bot, first_name, username if valid, None otherwise.
        """
        if not self.is_configured:
            logger.warning("Telegram Bot Token is not configured.")
            return None

        url = f"{self.api_base_url}/getMe"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("ok"):
                        bot_user = data.get("result", {})
                        logger.info(f"Connected to Telegram Bot: @{bot_user.get('username')} ({bot_user.get('first_name')})")
                        return bot_user
                logger.error(f"Telegram getMe failed: HTTP {res.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error connecting to Telegram Bot API: {e}")
            return None

    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Sends a text message to a specific chat ID via Telegram Bot API with defensive button URL validation."""
        if not self.is_configured:
            logger.warning("Telegram Bot Token is not configured. Cannot send message.")
            return False

        if not chat_id:
            logger.warning("No chat_id provided for Telegram message.")
            return False

        url = f"{self.api_base_url}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }

        # Defensive sanitization of inline buttons to prevent Telegram API 400 Bad Request
        if reply_markup and "inline_keyboard" in reply_markup:
            sanitized_keyboard = []
            for row in reply_markup["inline_keyboard"]:
                sanitized_row = []
                for btn in row:
                    if "url" in btn:
                        if is_valid_telegram_button_url(btn["url"]):
                            sanitized_row.append(btn)
                        else:
                            logger.debug(f"Filtered out invalid/localhost Telegram button URL: {btn.get('url')}")
                    else:
                        sanitized_row.append(btn)
                if sanitized_row:
                    sanitized_keyboard.append(sanitized_row)
            if sanitized_keyboard:
                payload["reply_markup"] = {"inline_keyboard": sanitized_keyboard}

        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    logger.info(f"Telegram message delivered successfully to chat_id: {chat_id}")
                    return True
                else:
                    logger.error(f"Telegram sendMessage failed with HTTP {res.status_code}: {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Telegram exception during sendMessage: {e}")
            return False

    def send_test_message(self, target_chat_id: Optional[str] = None) -> bool:
        """
        Sends a clean verification/health check message to the configured or provided chat ID.
        """
        chat_id = target_chat_id or self.default_chat_id
        if not chat_id:
            logger.warning("No target chat_id specified for Telegram test message.")
            return False

        public_url = get_public_web_app_url()
        web_link_html = f"\n🔗 <a href=\"{public_url}\">Open Web Dashboard</a>" if public_url else ""

        message = (
            "🛡️ <b>TECH SENTINEL BOT — STATUS VERIFIED</b>\n\n"
            "✅ <b>Connection Status:</b> Online & Operational\n"
            "⚡ <b>Intelligence Engine:</b> Active\n"
            "🎁 <b>Free Radar:</b> Monitoring cloud credits, vouchers & developer packs"
            f"{web_link_html}"
        )

        reply_markup = None
        if public_url:
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "🌐 Open Web App", "url": public_url},
                        {"text": "📰 View News", "url": f"{public_url}/news"}
                    ]
                ]
            }

        return self.send_message(chat_id=chat_id, text=message, parse_mode="HTML", reply_markup=reply_markup)

    # -------------------------------------------------------------
    # Command Formatters & Handlers
    # -------------------------------------------------------------
    def build_welcome_message(self, user_name: Optional[str] = None) -> str:
        """Constructs a clean, polished Tech Sentinel welcome message for /start command."""
        name_str = f" <b>{html.escape(user_name)}</b>" if user_name else ""
        public_url = get_public_web_app_url()
        web_line = f"\n🌐 <b>Web Dashboard:</b> <a href=\"{public_url}\">{public_url}</a>" if public_url else ""
        
        return (
            f"⚡ <b>Welcome to Tech Sentinel{name_str}!</b>\n\n"
            "Your personal technology intelligence agent and free opportunity radar.\n\n"
            "🔹 <b>Curated Intelligence:</b> Verified AI, Cloud, Dev & Open Source developments\n"
            "🔹 <b>Free Radar:</b> Cloud credits (AWS/GCP/Azure), 100% exam vouchers & student perks\n"
            "🔹 <b>Nightly Briefs:</b> Fast 30-second daily summaries\n\n"
            "<b>Quick Commands:</b>\n"
            "• /news — Personalized intelligence feed\n"
            "• /latest — Global chronological stream\n"
            "• /opportunities — Active Free Radar credits & vouchers\n"
            "• /help — Full command menu"
            f"{web_line}"
        )

    def handle_start_command(
        self,
        chat_id: str,
        user_name: Optional[str] = None,
        user_id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> bool:
        """Registers/updates Telegram user in SQLite and replies with welcome briefing."""
        resolved_user_id = str(user_id or chat_id)
        # Idempotently register/update user in SQLite
        try:
            self.db.upsert_telegram_user(
                user_id=resolved_user_id,
                chat_id=chat_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            # Synchronize updated Telegram users & preferences to Cloudflare D1 if configured
            d1_client = D1SyncClient()
            if d1_client.is_configured:
                logger.info(f"🔄 [START COMMAND] Syncing user {resolved_user_id} to Cloudflare D1...")
                users = self.db.get_all_telegram_users()
                prefs = self.db.get_all_preferences()
                d1_client.sync_telegram_data(users=users, preferences=prefs)
            else:
                logger.warning(f"⚠️ [START COMMAND] Remote D1 sync skipped: D1SyncClient is not configured in .env.")
        except Exception as e:
            logger.error(f"Error registering Telegram user {resolved_user_id}: {e}")

        welcome_text = self.build_welcome_message(user_name or first_name)
        public_url = get_public_web_app_url()
        reply_markup = None
        if public_url:
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "📰 Top News", "url": f"{public_url}/news"},
                        {"text": "🎁 Free Radar", "url": f"{public_url}/free"}
                    ],
                    [
                        {"text": "⚡ Open Web Dashboard", "url": public_url}
                    ]
                ]
            }
        return self.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML", reply_markup=reply_markup)

    def build_help_message(self) -> str:
        """Constructs the /help command menu."""
        public_url = get_public_web_app_url()
        web_line = f"\n🔗 <b>Web Dashboard:</b> <a href=\"{public_url}\">{public_url}</a>" if public_url else ""
        return (
            "🤖 <b>TECH SENTINEL — COMMAND REFERENCE</b>\n\n"
            "📡 <b>Intelligence Feeds:</b>\n"
            "• /news — Top personalized stories tailored to your tech interests\n"
            "• /latest — Global live intelligence stream in chronological order (all categories)\n\n"
            "🎁 <b>Free Opportunity Radar:</b>\n"
            "• /opportunities — High-value cloud credits, 100% free cert vouchers, and developer perks\n\n"
            "⚙️ <b>System:</b>\n"
            "• /start — Replay initial welcome briefing\n"
            "• /help — Display this command menu"
            f"{web_line}"
        )

    def handle_help_command(self, chat_id: str) -> bool:
        """Replies to a /help command."""
        text = self.build_help_message()
        public_url = get_public_web_app_url()
        reply_markup = None
        if public_url:
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "📰 News Feed", "url": f"{public_url}/news"},
                        {"text": "🎁 Free Radar", "url": f"{public_url}/free"}
                    ],
                    [
                        {"text": "⚡ Live Dashboard", "url": public_url}
                    ]
                ]
            }
        return self.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

    def build_personalized_news_message(
        self,
        limit: int = 5,
        user_id: Optional[str] = None
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Builds the /news response by resolving the requesting Telegram user's personalized
        preferences from SQLite and ranking by importance score DESC.
        """
        if user_id:
            prefs = self.db.get_telegram_user_preferences(user_id)
        else:
            prefs = self.db.get_preferences()

        active_cats = set()
        if prefs and "categories" in prefs and isinstance(prefs["categories"], list):
            for c in prefs["categories"]:
                active_cats.add(normalize_category(c))

        # Fetch recent news items from SQLite
        all_news = self.db.get_recent_news(limit=60)

        # Filter by personalized categories if preferences are configured
        if active_cats:
            filtered_news = [
                n for n in all_news
                if normalize_category(n.get("category", "")) in active_cats
            ]
        else:
            filtered_news = all_news

        # Rank by importance_score DESC, published_at DESC
        ranked_news = sorted(
            filtered_news,
            key=lambda x: (x.get("importance_score") or 50, x.get("published_at") or ""),
            reverse=True
        )[:limit]

        if not ranked_news:
            return (
                "📰 <b>PERSONALIZED NEWS FEED</b>\n\n"
                "No articles found matching your selected preferences. Adjust your interests in Preferences.",
                None
            )

        public_url = get_public_web_app_url()
        lines = [
            "📰 <b>TECH SENTINEL — PERSONALIZED INTELLIGENCE</b>",
            "<i>Top stories tailored to your interests & ranked by importance</i>\n"
        ]

        article_buttons = []
        for idx, item in enumerate(ranked_news, 1):
            title = html.escape(item.get("title", "Untitled"))
            cat = html.escape(item.get("category", "tech").upper())
            source = html.escape(item.get("source_name", "Source"))
            time_ago = format_time_ago(item.get("published_at"))
            summary = item.get("summary_what") or item.get("description") or ""
            summary_clean = html.escape(summary[:140] + ("..." if len(summary) > 140 else ""))
            raw_url = item.get("url", "")
            url = html.escape(raw_url)

            lines.append(f"<b>{idx}. [{cat}] {title}</b>")
            lines.append(f"📍 <i>{source} • {time_ago}</i>")
            if summary_clean:
                lines.append(f"{summary_clean}")
            if url:
                lines.append(f"👉 <a href=\"{url}\">Read Source Article</a>\n")
            else:
                lines.append("")

            if is_valid_telegram_button_url(raw_url):
                article_buttons.append({"text": f"👉 Story #{idx}", "url": raw_url})

        if public_url:
            lines.append(f"🌐 <a href=\"{public_url}/news\">Open Full News Feed</a>")

        button_rows = []
        for i in range(0, len(article_buttons), 2):
            button_rows.append(article_buttons[i:i+2])

        if public_url:
            button_rows.append([{"text": "🌐 Open Full Feed on Web", "url": f"{public_url}/news"}])

        reply_markup = {"inline_keyboard": button_rows} if button_rows else None
        return "\n".join(lines), reply_markup

    def handle_news_command(self, chat_id: str, user_id: Optional[str] = None) -> bool:
        """Handles /news command using the requesting Telegram user's preferences."""
        text, reply_markup = self.build_personalized_news_message(limit=5, user_id=user_id or chat_id)
        return self.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

    def build_latest_stream_message(self, limit: int = 5) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Builds the /latest response using the GLOBAL chronological stream (all categories, published_at DESC).
        """
        recent_items = self.db.get_recent_news(limit=limit)
        if not recent_items:
            return ("⚡ <b>GLOBAL INTELLIGENCE STREAM</b>\n\nNo recent articles available in stream.", None)

        public_url = get_public_web_app_url()
        lines = [
            "⚡ <b>TECH SENTINEL — LATEST INTELLIGENCE STREAM</b>",
            "<i>Live chronological dispatch across all tech domains</i>\n"
        ]

        article_buttons = []
        for idx, item in enumerate(recent_items, 1):
            title = html.escape(item.get("title", "Untitled"))
            cat = html.escape(item.get("category", "tech").upper())
            source = html.escape(item.get("source_name", "Source"))
            time_ago = format_time_ago(item.get("published_at"))
            raw_url = item.get("url", "")
            url = html.escape(raw_url)

            lines.append(f"<b>{idx}. [{cat}] {title}</b>")
            lines.append(f"⏱️ <i>{source} • {time_ago}</i>")
            if url:
                lines.append(f"👉 <a href=\"{url}\">View Story</a>\n")
            else:
                lines.append("")

            if is_valid_telegram_button_url(raw_url):
                article_buttons.append({"text": f"👉 Story #{idx}", "url": raw_url})

        if public_url:
            lines.append(f"🌐 <a href=\"{public_url}\">Open Live Stream on Web</a>")

        button_rows = []
        for i in range(0, len(article_buttons), 2):
            button_rows.append(article_buttons[i:i+2])

        if public_url:
            button_rows.append([{"text": "⚡ View Live Dashboard", "url": public_url}])

        reply_markup = {"inline_keyboard": button_rows} if button_rows else None
        return "\n".join(lines), reply_markup

    def handle_latest_command(self, chat_id: str) -> bool:
        """Handles /latest command."""
        text, reply_markup = self.build_latest_stream_message(limit=5)
        return self.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

    def build_opportunities_message(self, limit: int = 5) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Builds the /opportunities response reusing active opportunity radar ranking from SQLite.
        """
        opps = self.db.get_opportunities(limit=limit, status="ACTIVE")
        if not opps:
            return ("🎁 <b>FREE OPPORTUNITY RADAR</b>\n\nNo active opportunities currently tracked.", None)

        public_url = get_public_web_app_url()
        lines = [
            "🎁 <b>TECH SENTINEL — FREE OPPORTUNITY RADAR</b>",
            "<i>Verified cloud credits, cert vouchers & developer free tiers</i>\n"
        ]

        claim_buttons = []
        for idx, opp in enumerate(opps, 1):
            title = html.escape(opp.get("title", "Opportunity"))
            provider = html.escape(opp.get("provider", "Provider"))
            value = html.escape(str(opp.get("normal_value") or opp.get("current_value") or "FREE"))
            eligibility = html.escape(opp.get("eligibility") or "All Developers")
            why_care = opp.get("why_care") or opp.get("description") or ""
            why_clean = html.escape(why_care[:120] + ("..." if len(why_care) > 120 else ""))
            raw_claim_url = opp.get("claim_url") or opp.get("official_url") or ""
            claim_url = html.escape(raw_claim_url)

            lines.append(f"<b>{idx}. {title}</b>")
            lines.append(f"🏢 <b>Provider:</b> {provider} | 💵 <b>Value:</b> <code>{value}</code>")
            lines.append(f"🎯 <b>Eligibility:</b> {eligibility}")
            if why_clean:
                lines.append(f"💡 {why_clean}")
            if claim_url:
                lines.append(f"🔗 <a href=\"{claim_url}\">Claim Offer</a>\n")
            else:
                lines.append("")

            if is_valid_telegram_button_url(raw_claim_url):
                provider_short = provider.replace("Official: ", "")[:14]
                claim_buttons.append({"text": f"🎁 #{idx} {provider_short}", "url": raw_claim_url})

        if public_url:
            lines.append(f"🌐 <a href=\"{public_url}/free\">Open Full Free Radar Hub</a>")

        button_rows = []
        for i in range(0, len(claim_buttons), 2):
            button_rows.append(claim_buttons[i:i+2])

        if public_url:
            button_rows.append([{"text": "🎁 Open Free Radar Hub", "url": f"{public_url}/free"}])

        reply_markup = {"inline_keyboard": button_rows} if button_rows else None
        return "\n".join(lines), reply_markup

    def handle_opportunities_command(self, chat_id: str) -> bool:
        """Handles /opportunities command."""
        text, reply_markup = self.build_opportunities_message(limit=5)
        return self.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

    def build_digest_message(
        self,
        user_prefs: Optional[Dict[str, Any]] = None,
        limit_news: int = 4,
        limit_opps: int = 3
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Constructs the comprehensive evening digest tailored to a subscriber's preferences.
        Combines top personalized news items and verified free radar opportunities.
        """
        prefs = user_prefs or self.db.get_preferences()
        active_cats = set()
        if prefs and "categories" in prefs and isinstance(prefs["categories"], list):
            for c in prefs["categories"]:
                active_cats.add(normalize_category(c))

        # 1. News Section
        all_news = self.db.get_recent_news(limit=60)
        if active_cats:
            filtered_news = [
                n for n in all_news
                if normalize_category(n.get("category", "")) in active_cats
            ]
        else:
            filtered_news = all_news

        ranked_news = sorted(
            filtered_news,
            key=lambda x: (x.get("importance_score") or 50, x.get("published_at") or ""),
            reverse=True
        )[:limit_news]

        # 2. Opportunities Section
        opps = self.db.get_opportunities(limit=limit_opps, status="ACTIVE")

        public_url = get_public_web_app_url()
        lines = [
            "🛡️ <b>TECH SENTINEL — DAILY INTELLIGENCE DIGEST</b>",
            "<i>Your personalized briefing & Free Radar dispatch</i>\n",
            "📰 <b>TOP INTELLIGENCE FOR YOU:</b>"
        ]

        action_buttons = []

        if ranked_news:
            for idx, item in enumerate(ranked_news, 1):
                title = html.escape(item.get("title", "Untitled"))
                cat = html.escape(item.get("category", "tech").upper())
                source = html.escape(item.get("source_name", "Source"))
                summary = item.get("summary_what") or item.get("description") or ""
                summary_clean = html.escape(summary[:120] + ("..." if len(summary) > 120 else ""))
                raw_url = item.get("url", "")
                url = html.escape(raw_url)

                lines.append(f"<b>{idx}. [{cat}] {title}</b>")
                lines.append(f"📍 <i>{source}</i> — {summary_clean}")
                if url:
                    lines.append(f"👉 <a href=\"{url}\">Read Article</a>\n")
                else:
                    lines.append("")

                if is_valid_telegram_button_url(raw_url):
                    action_buttons.append({"text": f"👉 Story #{idx}", "url": raw_url})
        else:
            lines.append("<i>No top articles matching selected preferences today.</i>\n")

        if opps:
            lines.append("🎁 <b>FREE OPPORTUNITY RADAR:</b>")
            for idx, opp in enumerate(opps, 1):
                title = html.escape(opp.get("title", "Opportunity"))
                provider = html.escape(opp.get("provider", "Provider"))
                value = html.escape(str(opp.get("normal_value") or opp.get("current_value") or "FREE"))
                raw_claim_url = opp.get("claim_url") or opp.get("official_url") or ""
                claim_url = html.escape(raw_claim_url)

                lines.append(f"<b>{idx}. {title}</b>")
                lines.append(f"🏢 <i>{provider}</i> • Value: <code>{value}</code>")
                if claim_url:
                    lines.append(f"🔗 <a href=\"{claim_url}\">Claim Offer</a>\n")
                else:
                    lines.append("")

                if is_valid_telegram_button_url(raw_claim_url):
                    prov_short = provider.replace("Official: ", "")[:12]
                    action_buttons.append({"text": f"🎁 #{idx} {prov_short}", "url": raw_claim_url})

        if public_url:
            lines.append(f"🌐 <a href=\"{public_url}\">Open Web Dashboard</a>")

        button_rows = []
        for i in range(0, len(action_buttons), 2):
            button_rows.append(action_buttons[i:i+2])

        if public_url:
            button_rows.append([{"text": "⚡ Open Full Dashboard", "url": public_url}])

        reply_markup = {"inline_keyboard": button_rows} if button_rows else None
        return "\n".join(lines), reply_markup

    def handle_digest_command(self, chat_id: str, user_id: Optional[str] = None, arg: Optional[str] = None) -> bool:
        """Handles /digest, /digest on, /digest off subscription management."""
        resolved_user_id = str(user_id or chat_id)
        user = self.db.get_telegram_user(resolved_user_id)

        clean_arg = (arg or "").strip().lower()

        if clean_arg == "on":
            self.db.set_telegram_digest_subscription(resolved_user_id, enabled=True)
            logger.info(f"🔔 [DIGEST ON] User {resolved_user_id} enabled daily digest in SQLite.")
            # Sync to D1 if configured
            d1_client = D1SyncClient()
            if d1_client.is_configured:
                logger.info(f"🔄 [DIGEST ON] Syncing updated subscription to Cloudflare D1 for user {resolved_user_id}...")
                users = self.db.get_all_telegram_users()
                prefs = self.db.get_all_preferences()
                synced = d1_client.sync_telegram_data(users=users, preferences=prefs)
                if synced:
                    logger.info(f"✅ [DIGEST ON] Cloudflare D1 sync completed successfully.")
                else:
                    logger.warning(f"⚠️ [DIGEST ON] Cloudflare D1 sync failed.")
            else:
                logger.warning(f"⚠️ [DIGEST ON] Remote D1 sync skipped: D1SyncClient is not configured (WORKER_API_URL / INGESTION_SECRET missing in .env).")

            msg = (
                "✅ <b>Daily Digest Subscribed!</b>\n\n"
                "You will receive your personalized tech intelligence and free opportunity radar daily at <b>8:00 PM IST</b>.\n\n"
                "• To preview your digest now, send /news\n"
                "• To unsubscribe anytime, send <code>/digest off</code>"
            )
            return self.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

        elif clean_arg == "off":
            self.db.set_telegram_digest_subscription(resolved_user_id, enabled=False)
            logger.info(f"🔕 [DIGEST OFF] User {resolved_user_id} disabled daily digest in SQLite.")
            # Sync to D1 if configured
            d1_client = D1SyncClient()
            if d1_client.is_configured:
                logger.info(f"🔄 [DIGEST OFF] Syncing subscription removal to Cloudflare D1 for user {resolved_user_id}...")
                users = self.db.get_all_telegram_users()
                prefs = self.db.get_all_preferences()
                synced = d1_client.sync_telegram_data(users=users, preferences=prefs)
                if synced:
                    logger.info(f"✅ [DIGEST OFF] Cloudflare D1 sync completed successfully.")
                else:
                    logger.warning(f"⚠️ [DIGEST OFF] Cloudflare D1 sync failed.")
            else:
                logger.warning(f"⚠️ [DIGEST OFF] Remote D1 sync skipped: D1SyncClient is not configured in .env.")

            msg = (
                "🛑 <b>Daily Digest Unsubscribed.</b>\n\n"
                "You will no longer receive automated daily 8:00 PM briefings.\n\n"
                "You can re-subscribe anytime by sending <code>/digest on</code>."
            )
            return self.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

        else:
            is_enabled = bool(user.get("telegram_digest_enabled")) if user else False
            status_badge = "🟢 <b>Subscribed (Daily at 8:00 PM IST)</b>" if is_enabled else "🔴 <b>Not Subscribed</b>"
            msg = (
                "🔔 <b>TECH SENTINEL — DAILY DIGEST SETTINGS</b>\n\n"
                f"<b>Current Status:</b> {status_badge}\n\n"
                "<b>Manage Subscription:</b>\n"
                "• <code>/digest on</code> — Subscribe to daily 8:00 PM IST digest\n"
                "• <code>/digest off</code> — Unsubscribe from daily digest"
            )
            return self.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

    def process_command(
        self,
        command: str,
        chat_id: str,
        user_name: Optional[str] = None,
        user_id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> bool:
        """Routes an incoming text command to the appropriate handler."""
        parts = command.strip().split()
        cmd = parts[0].lower().split("@")[0]
        arg = parts[1].lower() if len(parts) > 1 else None

        if cmd == "/start":
            return self.handle_start_command(
                chat_id=chat_id,
                user_name=user_name,
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username
            )
        elif cmd == "/help":
            return self.handle_help_command(chat_id)
        elif cmd == "/news":
            return self.handle_news_command(chat_id, user_id=user_id)
        elif cmd in ("/opportunities", "/radar", "/free"):
            return self.handle_opportunities_command(chat_id)
        elif cmd in ("/latest", "/stream"):
            return self.handle_latest_command(chat_id)
        elif cmd == "/digest":
            return self.handle_digest_command(chat_id=chat_id, user_id=user_id, arg=arg)
        else:
            return self.handle_help_command(chat_id)

    def process_updates(self, offset: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """
        Fetches pending updates via getUpdates, registers Telegram users, and routes commands.
        Returns (processed_updates, next_offset).
        """
        if not self.is_configured:
            return [], None

        url = f"{self.api_base_url}/getUpdates"
        params: Dict[str, Any] = {"timeout": 2, "limit": 20}
        if offset is not None:
            params["offset"] = offset

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, params=params)
                if res.status_code != 200:
                    return [], offset

                data = res.json()
                if not data.get("ok"):
                    return [], offset

                updates = data.get("result", [])
                max_update_id = offset

                for upd in updates:
                    upd_id = upd.get("update_id")
                    if max_update_id is None or upd_id >= max_update_id:
                        max_update_id = upd_id + 1

                    msg = upd.get("message") or upd.get("edited_message")
                    if msg:
                        text = msg.get("text", "").strip()
                        chat = msg.get("chat", {})
                        chat_id = str(chat.get("id"))
                        from_user = msg.get("from", {})
                        user_id = str(from_user.get("id") or chat_id)
                        first_name = from_user.get("first_name")
                        last_name = from_user.get("last_name")
                        username = from_user.get("username")
                        user_name = first_name or username

                        if text.startswith("/"):
                            logger.info(f"Received command '{text}' from {user_name} (user_id: {user_id}, chat_id: {chat_id})")
                            self.process_command(
                                command=text,
                                chat_id=chat_id,
                                user_name=user_name,
                                user_id=user_id,
                                first_name=first_name,
                                last_name=last_name,
                                username=username
                            )

                return updates, max_update_id
        except Exception as e:
            logger.error(f"Error fetching Telegram updates: {e}")
            return [], offset

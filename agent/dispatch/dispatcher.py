import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..config import settings
from ..models import DailyReport
from ..storage.db import Database
from ..storage.d1_sync import D1SyncClient
from ..telegram.service import TelegramBotService
from ..notifications.email import EmailNotifier
from ..ai.digest_generator import DailyDigestGenerator

logger = logging.getLogger(__name__)

class UnifiedDispatcher:
    """Unified Multi-Channel Nightly Delivery Dispatcher for Tech Sentinel.
    Dispatches pre-generated nightly reports to opted-in Telegram users and Gmail/SMTP newsletter subscribers.
    Features cross-run idempotency tracking to prevent duplicate deliveries.
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        d1_client: Optional[D1SyncClient] = None,
        telegram_bot: Optional[TelegramBotService] = None,
        email_notifier: Optional[EmailNotifier] = None
    ):
        self.db = db or Database()
        self.d1_client = d1_client or D1SyncClient()
        self.telegram_bot = telegram_bot or TelegramBotService(db=self.db)
        self.email_notifier = email_notifier or EmailNotifier()

    def dispatch(
        self,
        report: Optional[DailyReport] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Executes unified dispatch for the given report (or latest persisted report).
        Guarantees:
        1. Report is resolved before dispatch.
        2. Idempotent across repeated workflow runs (delivered state persisted in database).
        3. Telegram delivery and Email delivery have completely independent delivery states.
        4. Failed delivery is NOT marked as delivered and can be safely retried.
        5. Only explicitly opted-in users receive messages/emails.
        """
        logger.info("🚀 [UNIFIED DISPATCH] Starting nightly intelligence delivery pipeline...")

        # 1. Resolve Report
        resolved_report = report
        if not resolved_report:
            latest_dict = self.db.get_latest_report()
            if latest_dict:
                resolved_report = DailyReport(**latest_dict)
            else:
                logger.info("ℹ️ No existing report found in database. Generating fresh Nightly Intelligence Report...")
                generator = DailyDigestGenerator()
                recent_news = self.db.get_recent_news(limit=25)
                active_opps = self.db.get_opportunities(limit=15)
                resolved_report = generator.generate(recent_news, active_opps)
                self.db.insert_report(resolved_report)

        logger.info(f"📰 [UNIFIED DISPATCH] Dispatches bound to report: '{resolved_report.headline}' (Date: {resolved_report.date})")

        stats = {
            "status": "success",
            "report_date": resolved_report.date,
            "report_headline": resolved_report.headline,
            "telegram": {"candidates": 0, "delivered": 0, "skipped": 0, "failed": 0},
            "email": {"candidates": 0, "delivered": 0, "skipped": 0, "failed": 0}
        }

        # 2. Dispatch Channel A: Telegram Opted-in Subscribers
        try:
            self._dispatch_telegram(resolved_report, stats, force=force)
        except Exception as e:
            logger.error(f"❌ [UNIFIED DISPATCH] Unhandled Telegram dispatch exception (isolated from email): {e}")

        # 3. Dispatch Channel B: Gmail / SMTP Email Newsletter Subscribers
        try:
            self._dispatch_email(resolved_report, stats, force=force)
        except Exception as e:
            logger.error(f"❌ [UNIFIED DISPATCH] Unhandled Email dispatch exception (isolated from telegram): {e}")

        logger.info(
            f"🏁 [UNIFIED DISPATCH COMPLETE] "
            f"Telegram: {stats['telegram']['delivered']} delivered, {stats['telegram']['skipped']} skipped, {stats['telegram']['failed']} failed (of {stats['telegram']['candidates']}); "
            f"Email: {stats['email']['delivered']} delivered, {stats['email']['skipped']} skipped, {stats['email']['failed']} failed (of {stats['email']['candidates']})."
        )
        return stats

    def _dispatch_telegram(self, report: DailyReport, stats: Dict[str, Any], force: bool = False):
        """Dispatches to explicitly opted-in Telegram users with idempotency checks."""
        if not self.telegram_bot.is_configured:
            logger.info("ℹ️ [TELEGRAM DISPATCH] Telegram Bot Token not configured. Skipping Telegram dispatch.")
            return

        # Fetch subscribers (D1 remote if configured, otherwise local SQLite)
        subscribers: List[Dict[str, Any]] = []
        if self.d1_client.is_configured:
            try:
                d1_subs = self.d1_client.get_telegram_subscribers(subscribed_only=True)
                subscribers = [s for s in d1_subs if s.get("telegram_digest_enabled", True)]
            except Exception as err:
                logger.warning(f"Note fetching subscribers from D1: {err}")
        else:
            local_subs = self.db.get_subscribed_telegram_users()
            for u in local_subs:
                prefs = self.db.get_telegram_user_preferences(u["user_id"])
                subscribers.append({
                    "user_id": u["user_id"],
                    "chat_id": u["chat_id"],
                    "username": u.get("username"),
                    "first_name": u.get("first_name"),
                    "preferences": prefs
                })

        # Ensure default_chat_id (from TELEGRAM_CHAT_ID secret) is included
        default_chat_id = str(self.telegram_bot.default_chat_id or "").strip()
        if default_chat_id:
            existing_chats = {str(s.get("chat_id") or s.get("user_id")).strip() for s in subscribers}
            if default_chat_id not in existing_chats:
                logger.info(f"ℹ️ [TELEGRAM DISPATCH] Including default configured TELEGRAM_CHAT_ID: {default_chat_id}")
                subscribers.append({
                    "user_id": default_chat_id,
                    "chat_id": default_chat_id,
                    "first_name": "Admin",
                    "preferences": {}
                })

        stats["telegram"]["candidates"] = len(subscribers)
        if not subscribers:
            logger.info("ℹ️ [TELEGRAM DISPATCH] No active opted-in Telegram subscribers found.")
            return

        logger.info(f"📱 [TELEGRAM DISPATCH] Dispatching to {len(subscribers)} active Telegram subscriber(s)...")

        for sub in subscribers:
            chat_id = str(sub.get("chat_id") or sub.get("user_id")).strip()
            user_name = sub.get("first_name") or sub.get("username") or "Subscriber"
            user_prefs = sub.get("preferences") or {}

            # Idempotency Check: Skip if already delivered for this date/report
            if not force and self.db.is_report_delivered(report.date, "telegram", chat_id):
                logger.info(f"⏭️ [TELEGRAM] Report {report.date} already delivered to {user_name} ({chat_id}). Skipping duplicate send.")
                stats["telegram"]["skipped"] += 1
                continue

            try:
                msg_text, reply_markup = self.telegram_bot.build_digest_message(
                    user_prefs=user_prefs,
                    limit_news=4,
                    limit_opps=3
                )
                delivered = self.telegram_bot.send_message(
                    chat_id=chat_id,
                    text=msg_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
                if delivered:
                    stats["telegram"]["delivered"] += 1
                    logger.info(f"✅ [TELEGRAM] Digest delivered to: {user_name} ({chat_id})")
                    self.db.record_delivery(
                        report_id=report.id,
                        report_date=report.date,
                        channel="telegram",
                        recipient_id=chat_id,
                        status="DELIVERED"
                    )
                    try:
                        self.db.record_telegram_digest_sent(chat_id)
                    except Exception:
                        pass
                else:
                    stats["telegram"]["failed"] += 1
                    logger.warning(f"⚠️ [TELEGRAM] Failed delivery to: {user_name} ({chat_id})")
                    self.db.record_delivery(
                        report_id=report.id,
                        report_date=report.date,
                        channel="telegram",
                        recipient_id=chat_id,
                        status="FAILED",
                        metadata={"error": "send_message returned False"}
                    )
            except Exception as err:
                stats["telegram"]["failed"] += 1
                logger.error(f"❌ [TELEGRAM] Exception sending to {user_name} ({chat_id}): {err}")
                self.db.record_delivery(
                    report_id=report.id,
                    report_date=report.date,
                    channel="telegram",
                    recipient_id=chat_id,
                    status="FAILED",
                    metadata={"error": str(err)}
                )

    def _dispatch_email(self, report: DailyReport, stats: Dict[str, Any], force: bool = False):
        """Dispatches to explicitly opted-in Email newsletter subscribers with idempotency checks."""
        if not self.email_notifier.is_configured:
            logger.info("ℹ️ [EMAIL DISPATCH] SMTP credentials (host, username, password) not configured in environment. Skipping email transmission.")
            return

        # Query opted-in email preferences from Cloudflare D1 if configured, fallback to local SQLite
        email_subscribers: List[Dict[str, Any]] = []
        if self.d1_client.is_configured:
            try:
                d1_subscribers = self.d1_client.get_email_subscribers()
                if d1_subscribers:
                    email_subscribers.extend(d1_subscribers)
            except Exception as err:
                logger.warning(f"Note fetching email subscribers from D1: {err}")

        # Also pull any local SQLite subscribers if present
        local_email_subs = self.db.get_email_subscribers()
        for ls in local_email_subs:
            ls_email = (ls.get("newsletter_email") or ls.get("email") or "").strip().lower()
            if ls_email and not any((s.get("newsletter_email") or s.get("email") or "").strip().lower() == ls_email for s in email_subscribers):
                email_subscribers.append(ls)

        # Include explicit EMAIL_TO if set in environment
        explicit_target = (getattr(settings, "EMAIL_TO", "") or os.getenv("EMAIL_TO") or os.getenv("NEWSLETTER_EMAIL") or "").strip().lower()
        if explicit_target and "@" in explicit_target:
            existing_emails = {(s.get("newsletter_email") or s.get("email") or "").strip().lower() for s in email_subscribers}
            if explicit_target not in existing_emails:
                logger.info(f"ℹ️ [EMAIL DISPATCH] Including explicit target email from environment/secrets: {explicit_target}")
                email_subscribers.append({"email": explicit_target, "newsletter_email": explicit_target})

        # If still empty, and SMTP_USER is an email address, treat as fallback recipient
        if not email_subscribers:
            admin_email = (getattr(settings, "SMTP_USER", "") or os.getenv("SMTP_USER") or os.getenv("GMAIL_USER") or "").strip().lower()
            if admin_email and "@" in admin_email:
                logger.info(f"ℹ️ [EMAIL DISPATCH] No D1 subscriber profile found; routing newsletter to configured SMTP admin user: {admin_email}")
                email_subscribers.append({"email": admin_email, "newsletter_email": admin_email})

        stats["email"]["candidates"] = len(email_subscribers)

        if not email_subscribers:
            logger.info("ℹ️ [EMAIL DISPATCH] No active opted-in email newsletter subscribers found.")
            return

        logger.info(f"📧 [EMAIL DISPATCH] Dispatching to {len(email_subscribers)} opted-in email subscriber(s)...")

        for sub in email_subscribers:
            email_addr = (sub.get("newsletter_email") or sub.get("email") or "").strip().lower()
            if not email_addr:
                continue

            # Idempotency Check: Skip if already delivered for this date/report
            if not force and self.db.is_report_delivered(report.date, "email", email_addr):
                logger.info(f"⏭️ [EMAIL] Report {report.date} already delivered to {email_addr}. Skipping duplicate send.")
                stats["email"]["skipped"] += 1
                continue

            try:
                sent = self.email_notifier.send_newsletter(
                    recipient_email=email_addr,
                    report=report
                )
                if sent:
                    stats["email"]["delivered"] += 1
                    logger.info(f"✅ [EMAIL] Newsletter delivered to: {email_addr}")
                    self.db.record_delivery(
                        report_id=report.id,
                        report_date=report.date,
                        channel="email",
                        recipient_id=email_addr,
                        status="DELIVERED"
                    )
                    try:
                        self.db.record_email_sent(email_addr)
                    except Exception:
                        pass
                else:
                    stats["email"]["failed"] += 1
                    logger.warning(f"⚠️ [EMAIL] Failed sending newsletter to: {email_addr}")
                    self.db.record_delivery(
                        report_id=report.id,
                        report_date=report.date,
                        channel="email",
                        recipient_id=email_addr,
                        status="FAILED",
                        metadata={"error": "send_newsletter returned False"}
                    )
            except Exception as err:
                stats["email"]["failed"] += 1
                logger.error(f"❌ [EMAIL] Exception sending newsletter to {email_addr}: {err}")
                self.db.record_delivery(
                    report_id=report.id,
                    report_date=report.date,
                    channel="email",
                    recipient_id=email_addr,
                    status="FAILED",
                    metadata={"error": str(err)}
                )

def run_unified_dispatch(report: Optional[DailyReport] = None, force: bool = False) -> Dict[str, Any]:
    dispatcher = UnifiedDispatcher()
    return dispatcher.dispatch(report=report, force=force)

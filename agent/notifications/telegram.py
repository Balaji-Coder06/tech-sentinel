import logging
import html
from typing import Optional
import httpx
from ..models import DailyReport
from ..config import settings

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Dispatches the nightly intelligence digest and critical opportunity alerts to Telegram safely using HTML mode."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID

    def send_daily_digest(self, report: DailyReport) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.info("Telegram credentials not configured. Skipping automated broadcast.")
            return False

        headline = html.escape(report.headline)
        summary = html.escape(report.thirty_sec_summary)
        take = html.escape(report.sentinel_take)
        report_url = html.escape(f"{settings.APP_BASE_URL.rstrip('/')}/reports/{report.date}")

        message = (
            f"🌙 <b>TECH SENTINEL DAILY INTELLIGENCE</b>\n"
            f"<i>{report.date}</i>\n\n"
            f"⚡ <b>{headline}</b>\n\n"
            f"📝 <b>30-Second Brief:</b>\n{summary}\n\n"
            f"🔥 <b>Top Stories:</b>\n"
        )
        for idx, s in enumerate(report.top_stories[:3], 1):
            title = html.escape(s.get('title', ''))
            message += f"{idx}. {title}\n"

        if report.free_opportunities:
            message += f"\n🎁 <b>Free Before It's Gone:</b>\n"
            for opp in report.free_opportunities[:3]:
                title = html.escape(opp.get('title', ''))
                val = html.escape(str(opp.get('value', 'FREE')))
                message += f"• <b>{title}</b> — <code>{val}</code>\n"

        if report.expiring_soon:
            message += f"\n⏰ <b>Expiring Soon:</b>\n"
            for exp in report.expiring_soon[:2]:
                title = html.escape(exp.get('title', ''))
                exp_time = html.escape(str(exp.get('expires_in') or exp.get('expires') or 'Soon'))
                message += f"⚠️ {title} (<b>{exp_time}</b>)\n"

        message += f"\n💡 <b>Sentinel's Take:</b>\n<i>{take}</i>\n\n"
        message += f"👉 <a href=\"{report_url}\">Open Full Daily Report</a>"

        return self._send_message(message)

    def _send_message(self, html_text: str) -> bool:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    logger.info("Telegram message dispatched successfully via HTML mode.")
                    return True
                else:
                    logger.error(f"Telegram dispatch failed: HTTP {res.status_code} - {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Telegram exception during dispatch: {e}")
            return False

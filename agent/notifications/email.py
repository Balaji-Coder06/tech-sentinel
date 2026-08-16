import logging
import smtplib
import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any
from ..models import DailyReport
from ..config import settings

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Generic SMTP / Gmail Email Notifier for Tech Sentinel Nightly Newsletters."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        sender: Optional[str] = None
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.username = username or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS if use_tls is None else use_tls
        self.sender = sender or settings.EMAIL_FROM or self.username or "Tech Sentinel <noreply@tech-sentinel.com>"

    @property
    def is_configured(self) -> bool:
        """Returns True if minimum required SMTP settings are present."""
        return bool(self.host and self.username and self.password)

    def build_newsletter_html(self, report: DailyReport, recipient_email: str = "") -> str:
        headline = html.escape(report.headline)
        summary = html.escape(report.thirty_sec_summary)
        take = html.escape(report.sentinel_take)
        app_url = settings.APP_BASE_URL.rstrip('/')
        report_url = html.escape(f"{app_url}/reports/{report.date}")

        # Top Stories HTML
        stories_html = ""
        for idx, s in enumerate(report.top_stories[:4], 1):
            title = html.escape(s.get('title', ''))
            cat = html.escape(str(s.get('category', 'development')).upper())
            sum_text = html.escape(str(s.get('summary', '')))
            stories_html += f"""
            <div style="margin-bottom: 14px; padding: 12px 16px; background: #181920; border: 1px solid #282a36; border-radius: 10px;">
                <div style="font-size: 11px; font-weight: bold; color: #00d2ff; text-transform: uppercase; margin-bottom: 4px;">{cat}</div>
                <div style="font-size: 14px; font-weight: bold; color: #ffffff; margin-bottom: 4px;">{idx}. {title}</div>
                <div style="font-size: 12px; color: #9da5b4; line-height: 1.4;">{sum_text}</div>
            </div>
            """

        # Free Opportunities HTML
        opps_html = ""
        for opp in report.free_opportunities[:3]:
            title = html.escape(opp.get('title', ''))
            val = html.escape(str(opp.get('value', 'FREE')))
            provider = html.escape(str(opp.get('provider', 'Official')))
            claim_url = html.escape(str(opp.get('claim_url') or app_url))
            opps_html += f"""
            <div style="margin-bottom: 10px; padding: 10px 14px; background: #131b24; border: 1px solid #1e3a4c; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 13px; font-weight: bold; color: #ffffff;">{title}</span>
                    <span style="font-size: 11px; color: #64b5f6; margin-left: 6px;">({provider})</span>
                </div>
                <div style="margin-top: 4px;">
                    <span style="font-size: 11px; font-weight: bold; color: #00e676; background: #00e67620; padding: 2px 8px; border-radius: 4px;">{val}</span>
                </div>
            </div>
            """

        # Expiring Soon Alerts HTML
        expiring_html = ""
        if report.expiring_soon:
            for exp in report.expiring_soon[:2]:
                title = html.escape(exp.get('title', ''))
                exp_time = html.escape(str(exp.get('expires_in') or exp.get('expires') or 'Soon'))
                expiring_html += f"""
                <div style="font-size: 12px; color: #ffb74d; margin-bottom: 4px;">
                    ⏰ <b>{title}</b> &mdash; <i>Expires {exp_time}</i>
                </div>
                """

        expiring_section = f"""
        <div style="margin: 18px 0; padding: 12px 16px; background: #2c1e11; border: 1px solid #663d14; border-radius: 8px;">
            <div style="font-size: 12px; font-weight: bold; color: #ff9800; text-transform: uppercase; margin-bottom: 6px;">Expiring Soon Alerts</div>
            {expiring_html}
        </div>
        """ if expiring_html else ""

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tech Sentinel Nightly Intelligence - {report.date}</title>
        </head>
        <body style="margin: 0; padding: 20px; background-color: #0b0c10; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e0e6ed;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #121318; border: 1px solid #1f232b; border-radius: 14px; overflow: hidden;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #111b27 0%, #0d1117 100%); padding: 24px 20px; border-bottom: 1px solid #232733; text-align: center;">
                    <div style="font-size: 11px; font-weight: 800; letter-spacing: 1.5px; color: #00d2ff; text-transform: uppercase; margin-bottom: 6px;">Autonomous Tech Radar</div>
                    <h1 style="font-size: 20px; font-weight: 900; color: #ffffff; margin: 0 0 6px 0;">TECH SENTINEL DAILY INTELLIGENCE</h1>
                    <div style="font-size: 12px; color: #788296;">Nightly Brief &bull; {report.date}</div>
                </div>

                <!-- Content -->
                <div style="padding: 24px 20px;">
                    <!-- Headline & 30s Brief -->
                    <div style="margin-bottom: 22px;">
                        <h2 style="font-size: 16px; font-weight: 800; color: #ffffff; margin: 0 0 8px 0; line-height: 1.3;">{headline}</h2>
                        <p style="font-size: 13px; color: #b0b8c4; line-height: 1.5; margin: 0; background: #161820; padding: 12px 14px; border-left: 3px solid #00d2ff; border-radius: 0 6px 6px 0;">
                            <b>30-Second Summary:</b> {summary}
                        </p>
                    </div>

                    <!-- Top Stories -->
                    <div style="margin-bottom: 22px;">
                        <h3 style="font-size: 13px; font-weight: 800; color: #00d2ff; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 10px 0;">🔥 Key Intelligence Stories</h3>
                        {stories_html}
                    </div>

                    <!-- Free Opportunities -->
                    {f'''
                    <div style="margin-bottom: 22px;">
                        <h3 style="font-size: 13px; font-weight: 800; color: #00e676; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 10px 0;">🎁 Free Radar & Credits</h3>
                        {opps_html}
                    </div>
                    ''' if opps_html else ''}

                    {expiring_section}

                    <!-- Sentinel Take -->
                    <div style="margin: 22px 0; padding: 14px 16px; background: #151d28; border: 1px solid #1d334a; border-radius: 10px;">
                        <div style="font-size: 11px; font-weight: bold; color: #00d2ff; text-transform: uppercase; margin-bottom: 4px;">💡 Sentinel's Take</div>
                        <div style="font-size: 13px; color: #d0d7de; font-style: italic; line-height: 1.4;">{take}</div>
                    </div>

                    <!-- Web CTA Button -->
                    <div style="text-align: center; margin: 26px 0 10px 0;">
                        <a href="{report_url}" style="display: inline-block; padding: 12px 28px; background-color: #0070f3; color: #ffffff; text-decoration: none; font-weight: 800; font-size: 13px; border-radius: 8px; letter-spacing: 0.3px;">Open Full Interactive Report &rarr;</a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #0c0d11; padding: 16px 20px; border-top: 1px solid #1a1d24; text-align: center; font-size: 11px; color: #586069;">
                    <p style="margin: 0 0 6px 0;">You received this automated newsletter because you opted in via your Tech Sentinel settings.</p>
                    <p style="margin: 0;"><a href="{app_url}/settings" style="color: #00d2ff; text-decoration: none;">Manage Notification Preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template

    def build_newsletter_text(self, report: DailyReport) -> str:
        app_url = settings.APP_BASE_URL.rstrip('/')
        lines = [
            f"TECH SENTINEL DAILY INTELLIGENCE - {report.date}",
            "=" * 50,
            f"\nHEADLINE: {report.headline}",
            f"\n30-SECOND SUMMARY:\n{report.thirty_sec_summary}",
            "\nTOP STORIES:"
        ]
        for idx, s in enumerate(report.top_stories[:4], 1):
            lines.append(f"{idx}. [{s.get('category', 'TECH').upper()}] {s.get('title', '')}")
            if s.get('summary'):
                lines.append(f"   {s.get('summary')}")

        if report.free_opportunities:
            lines.append("\nFREE RADAR & OPPORTUNITIES:")
            for opp in report.free_opportunities[:3]:
                lines.append(f"• {opp.get('title', '')} ({opp.get('provider', 'Official')}) - {opp.get('value', 'FREE')}")

        if report.expiring_soon:
            lines.append("\nEXPIRING SOON:")
            for exp in report.expiring_soon[:2]:
                lines.append(f"⏰ {exp.get('title', '')} (Expires: {exp.get('expires_in') or exp.get('expires') or 'Soon'})")

        lines.append(f"\nSENTINEL'S TAKE:\n{report.sentinel_take}")
        lines.append(f"\nView full report: {app_url}/reports/{report.date}")
        lines.append(f"Manage preferences: {app_url}/settings")
        return "\n".join(lines)

    def send_newsletter(
        self,
        recipient_email: str,
        report: DailyReport
    ) -> bool:
        """Sends the nightly newsletter email to a single recipient."""
        if not self.is_configured:
            logger.info("SMTP credentials not configured. Skipping email dispatch.")
            return False

        if not recipient_email or "@" not in recipient_email:
            logger.warning(f"Invalid recipient email address: '{recipient_email}'")
            return False

        subject = f"🌙 Tech Sentinel Daily Intelligence: {report.headline} ({report.date})"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = recipient_email

        text_part = MIMEText(self.build_newsletter_text(report), "plain", "utf-8")
        html_part = MIMEText(self.build_newsletter_html(report, recipient_email), "html", "utf-8")

        msg.attach(text_part)
        msg.attach(html_part)

        try:
            if self.port == 465:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=15)
                if self.use_tls:
                    server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(self.sender, [recipient_email], msg.as_string())
            server.quit()
            logger.info(f"✅ Newsletter successfully sent to email: {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send newsletter email to {recipient_email}: {e}")
            return False

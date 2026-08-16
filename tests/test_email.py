import unittest
from agent.models import DailyReport
from agent.notifications.email import EmailNotifier

class TestEmailNotifier(unittest.TestCase):

    def setUp(self):
        self.report = DailyReport(
            id="report_2026-08-16",
            date="2026-08-16",
            title="Tech Sentinel Daily Intelligence - 2026-08-16",
            headline="OpenAI Unveils Autonomous Reasoning Architecture",
            thirty_sec_summary="Major updates across AI, Cloud and Developer tooling.",
            top_stories=[
                {
                    "title": "OpenAI Unveils Architecture",
                    "category": "ai",
                    "summary": "New lightweight reasoning model released."
                }
            ],
            free_opportunities=[
                {
                    "title": "Google Cloud $300 Credits",
                    "provider": "Google Cloud",
                    "value": "$300",
                    "claim_url": "https://cloud.google.com/free"
                }
            ],
            expiring_soon=[
                {
                    "title": "AWS Builder Grant",
                    "expires_in": "12 hours"
                }
            ],
            sentinel_take="Focus on adopting lightweight reasoning models for low-latency pipelines."
        )

    def test_email_formatting_html(self):
        notifier = EmailNotifier()
        html = notifier.build_newsletter_html(self.report, "subscriber@example.com")
        self.assertIn("TECH SENTINEL DAILY INTELLIGENCE", html)
        self.assertIn("OpenAI Unveils Autonomous Reasoning Architecture", html)
        self.assertIn("Google Cloud $300 Credits", html)
        self.assertIn("AWS Builder Grant", html)
        self.assertIn("Focus on adopting lightweight", html)

    def test_email_formatting_text(self):
        notifier = EmailNotifier()
        text = notifier.build_newsletter_text(self.report)
        self.assertIn("TECH SENTINEL DAILY INTELLIGENCE - 2026-08-16", text)
        self.assertIn("HEADLINE: OpenAI Unveils Autonomous Reasoning Architecture", text)
        self.assertIn("Google Cloud $300 Credits", text)
        self.assertIn("AWS Builder Grant", text)

    def test_unconfigured_email_fails_gracefully(self):
        notifier = EmailNotifier(username="", password="")
        self.assertFalse(notifier.is_configured)
        sent = notifier.send_newsletter("test@example.com", self.report)
        self.assertFalse(sent)

if __name__ == "__main__":
    unittest.main()

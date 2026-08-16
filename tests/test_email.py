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
        self.assertIn("https://tech-sentinel-chi.vercel.app/reports/2026-08-16", html)
        self.assertIn("https://tech-sentinel-chi.vercel.app/settings", html)
        self.assertNotIn("localhost:3000", html)
        self.assertNotIn("pages.dev", html)

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

    def test_get_email_subscribers_strictly_filters_opted_in_non_empty(self):
        import tempfile
        import os
        from agent.storage.db import Database

        fd, temp_db = tempfile.mkstemp(suffix=".db")
        try:
            db = Database(temp_db)
            db.init_schema()

            # Clear any seed preferences
            with db.get_connection() as conn:
                conn.execute("DELETE FROM preferences")
                conn.commit()

            # 1. User with email enabled but empty string email -> Should NOT be returned
            db.update_preferences({
                "id": "user_empty_email",
                "email_newsletter_enabled": True,
                "newsletter_email": ""
            })

            # 2. User with email enabled but NULL email -> Should NOT be returned
            db.update_preferences({
                "id": "user_null_email",
                "email_newsletter_enabled": True,
                "newsletter_email": None
            })

            # 3. User with valid email but email disabled (opted out) -> Should NOT be returned
            db.update_preferences({
                "id": "user_opted_out",
                "email_newsletter_enabled": False,
                "newsletter_email": "opted_out@domain.com"
            })

            # 4. User genuinely opted in with valid email -> MUST be returned
            db.update_preferences({
                "id": "user_valid_opt_in",
                "email_newsletter_enabled": True,
                "newsletter_email": "valid.subscriber@domain.com"
            })

            subscribers = db.get_email_subscribers()
            self.assertEqual(len(subscribers), 1)
            self.assertEqual(subscribers[0]["id"], "user_valid_opt_in")
            self.assertEqual(subscribers[0]["newsletter_email"], "valid.subscriber@domain.com")
            self.assertTrue(subscribers[0]["email_newsletter_enabled"])
        finally:
            try:
                os.close(fd)
            except Exception:
                pass
            if os.path.exists(temp_db):
                try:
                    os.remove(temp_db)
                except Exception:
                    pass

if __name__ == "__main__":
    unittest.main()

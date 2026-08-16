import unittest
import tempfile
import os
from unittest.mock import MagicMock

from agent.storage.db import Database
from agent.storage.d1_sync import D1SyncClient
from agent.models import DailyReport
from agent.dispatch.dispatcher import UnifiedDispatcher

class TestUnifiedDispatcher(unittest.TestCase):

    def setUp(self):
        # Create a temporary SQLite database for testing
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.db = Database(self.temp_db_path)
        self.db.init_schema()
        self.d1_client = D1SyncClient(worker_url="", secret="")

        # Ensure clean isolated subscriber state in test database
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM telegram_users")
            conn.execute("DELETE FROM preferences")
            conn.execute("DELETE FROM delivery_logs")
            conn.commit()

        # Seed sample report
        self.sample_report = DailyReport(
            id="report_test_2026",
            date="2026-08-16",
            title="Tech Sentinel Daily Intelligence",
            headline="Breakthrough in Autonomous AI Engines",
            thirty_sec_summary="All key tech developments in 30 seconds.",
            top_stories=[{"title": "Breakthrough in AI", "category": "ai", "summary": "Faster inference."}],
            free_opportunities=[{"title": "$100 Credits", "provider": "DevCo", "value": "$100", "claim_url": "https://dev.co"}],
            expiring_soon=[],
            sentinel_take="Great momentum in open-source AI."
        )
        self.db.insert_report(self.sample_report)

    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass

    def test_telegram_only_opt_in(self):
        """User opted into Telegram only receives Telegram dispatch."""
        self.db.upsert_telegram_user("tg_123", "chat_123", username="alice", first_name="Alice")
        self.db.set_telegram_digest_subscription("tg_123", True)

        # Ensure no email preference opted in
        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": False,
            "newsletter_email": None
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        stats = dispatcher.dispatch(report=self.sample_report)

        self.assertEqual(stats["telegram"]["candidates"], 1)
        self.assertEqual(stats["telegram"]["delivered"], 1)
        self.assertEqual(stats["telegram"]["skipped"], 0)
        dispatcher.telegram_bot.send_message.assert_called_once()

        self.assertEqual(stats["email"]["candidates"], 0)
        self.assertEqual(stats["email"]["delivered"], 0)
        dispatcher.email_notifier.send_newsletter.assert_not_called()

    def test_email_only_opt_in(self):
        """User opted into Email only receives Email dispatch."""
        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "balaji@example.com"
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        stats = dispatcher.dispatch(report=self.sample_report)

        self.assertEqual(stats["telegram"]["candidates"], 0)
        self.assertEqual(stats["telegram"]["delivered"], 0)
        dispatcher.telegram_bot.send_message.assert_not_called()

        self.assertEqual(stats["email"]["candidates"], 1)
        self.assertEqual(stats["email"]["delivered"], 1)
        self.assertEqual(stats["email"]["skipped"], 0)
        dispatcher.email_notifier.send_newsletter.assert_called_once()

    def test_both_channels_opt_in(self):
        """User opted into both receives both dispatches."""
        self.db.upsert_telegram_user("tg_456", "chat_456", username="bob", first_name="Bob")
        self.db.set_telegram_digest_subscription("tg_456", True)

        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "bob@example.com"
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        stats = dispatcher.dispatch(report=self.sample_report)

        self.assertEqual(stats["telegram"]["delivered"], 1)
        self.assertEqual(stats["email"]["delivered"], 1)
        dispatcher.telegram_bot.send_message.assert_called_once()
        dispatcher.email_notifier.send_newsletter.assert_called_once()

    def test_neither_channel_opt_in(self):
        """User opted into neither receives nothing."""
        self.db.upsert_telegram_user("tg_789", "chat_789", username="charlie", first_name="Charlie")
        self.db.set_telegram_digest_subscription("tg_789", False)

        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": False,
            "newsletter_email": ""
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        stats = dispatcher.dispatch(report=self.sample_report)

        self.assertEqual(stats["telegram"]["candidates"], 0)
        self.assertEqual(stats["telegram"]["delivered"], 0)
        self.assertEqual(stats["email"]["candidates"], 0)
        self.assertEqual(stats["email"]["delivered"], 0)
        dispatcher.telegram_bot.send_message.assert_not_called()
        dispatcher.email_notifier.send_newsletter.assert_not_called()

    # -------------------------------------------------------------
    # Idempotency Requirement Tests (1 to 5)
    # -------------------------------------------------------------
    def test_idempotency_first_dispatch_sends_and_second_skips(self):
        """
        Requirement 1 & 2:
        - 1. First dispatch sends.
        - 2. Second dispatch for the same report/recipient/channel skips.
        """
        self.db.upsert_telegram_user("tg_user_1", "chat_user_1", username="user1", first_name="User 1")
        self.db.set_telegram_digest_subscription("tg_user_1", True)
        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "user1@example.com"
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        # First Dispatch: Must deliver to both
        stats_1 = dispatcher.dispatch(report=self.sample_report)
        self.assertEqual(stats_1["telegram"]["delivered"], 1)
        self.assertEqual(stats_1["telegram"]["skipped"], 0)
        self.assertEqual(stats_1["email"]["delivered"], 1)
        self.assertEqual(stats_1["email"]["skipped"], 0)
        self.assertEqual(dispatcher.telegram_bot.send_message.call_count, 1)
        self.assertEqual(dispatcher.email_notifier.send_newsletter.call_count, 1)

        # Verify persisted delivery states in SQLite
        self.assertTrue(self.db.is_report_delivered(self.sample_report.date, "telegram", "chat_user_1"))
        self.assertTrue(self.db.is_report_delivered(self.sample_report.date, "email", "user1@example.com"))

        # Second Dispatch (repeated workflow run): Must skip both without duplicate sending
        stats_2 = dispatcher.dispatch(report=self.sample_report)
        self.assertEqual(stats_2["telegram"]["delivered"], 0)
        self.assertEqual(stats_2["telegram"]["skipped"], 1)
        self.assertEqual(stats_2["email"]["delivered"], 0)
        self.assertEqual(stats_2["email"]["skipped"], 1)
        # Call counts must remain 1 (no new sends)
        self.assertEqual(dispatcher.telegram_bot.send_message.call_count, 1)
        self.assertEqual(dispatcher.email_notifier.send_newsletter.call_count, 1)

    def test_telegram_and_email_independent_delivery_state(self):
        """
        Requirement 3: Telegram and email have independent delivery state.
        If Telegram is already delivered, but email is not, email is sent while Telegram is skipped.
        """
        self.db.upsert_telegram_user("tg_user_2", "chat_user_2", username="user2", first_name="User 2")
        self.db.set_telegram_digest_subscription("tg_user_2", True)
        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "user2@example.com"
        })

        # Pre-mark Telegram as already delivered for today
        self.db.record_delivery(
            report_id=self.sample_report.id,
            report_date=self.sample_report.date,
            channel="telegram",
            recipient_id="chat_user_2",
            status="DELIVERED"
        )

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        stats = dispatcher.dispatch(report=self.sample_report)

        # Telegram was already delivered -> skipped
        self.assertEqual(stats["telegram"]["delivered"], 0)
        self.assertEqual(stats["telegram"]["skipped"], 1)
        dispatcher.telegram_bot.send_message.assert_not_called()

        # Email was NOT delivered yet -> sent
        self.assertEqual(stats["email"]["delivered"], 1)
        self.assertEqual(stats["email"]["skipped"], 0)
        dispatcher.email_notifier.send_newsletter.assert_called_once()

    def test_failed_delivery_can_be_retried(self):
        """
        Requirement 4: A failed delivery must NOT be marked as delivered and can be retried.
        """
        self.db.upsert_telegram_user("tg_user_3", "chat_user_3", username="user3", first_name="User 3")
        self.db.set_telegram_digest_subscription("tg_user_3", True)
        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "user3@example.com"
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        # First attempt: Both channels fail
        dispatcher.telegram_bot.send_message = MagicMock(return_value=False)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=False)

        stats_1 = dispatcher.dispatch(report=self.sample_report)
        self.assertEqual(stats_1["telegram"]["delivered"], 0)
        self.assertEqual(stats_1["telegram"]["failed"], 1)
        self.assertEqual(stats_1["email"]["delivered"], 0)
        self.assertEqual(stats_1["email"]["failed"], 1)

        # Verify not marked as delivered in DB
        self.assertFalse(self.db.is_report_delivered(self.sample_report.date, "telegram", "chat_user_3"))
        self.assertFalse(self.db.is_report_delivered(self.sample_report.date, "email", "user3@example.com"))

        # Second attempt (Retry): Channels recover and succeed
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        stats_2 = dispatcher.dispatch(report=self.sample_report)
        self.assertEqual(stats_2["telegram"]["delivered"], 1)
        self.assertEqual(stats_2["telegram"]["skipped"], 0)
        self.assertEqual(stats_2["email"]["delivered"], 1)
        self.assertEqual(stats_2["email"]["skipped"], 0)

        # Now marked as delivered
        self.assertTrue(self.db.is_report_delivered(self.sample_report.date, "telegram", "chat_user_3"))
        self.assertTrue(self.db.is_report_delivered(self.sample_report.date, "email", "user3@example.com"))

    def test_new_day_report_delivered_normally(self):
        """
        Requirement 5: A new day's report can be delivered normally even if previous days were delivered.
        """
        self.db.upsert_telegram_user("tg_user_4", "chat_user_4", username="user4", first_name="User 4")
        self.db.set_telegram_digest_subscription("tg_user_4", True)
        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "user4@example.com"
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        # Day 1 Dispatch (2026-08-16)
        stats_day1 = dispatcher.dispatch(report=self.sample_report)
        self.assertEqual(stats_day1["telegram"]["delivered"], 1)
        self.assertEqual(stats_day1["email"]["delivered"], 1)

        # Day 2 Report (2026-08-17)
        day2_report = DailyReport(
            id="report_test_2026_08_17",
            date="2026-08-17",
            title="Tech Sentinel Daily Intelligence - 2026-08-17",
            headline="New Next.js 16 Architecture Released",
            thirty_sec_summary="Performance boosts and compiler updates.",
            top_stories=[{"title": "Next.js 16", "category": "development", "summary": "Turbopack 2.0."}],
            free_opportunities=[],
            expiring_soon=[],
            sentinel_take="Great day for web engineering."
        )
        self.db.insert_report(day2_report)

        # Day 2 Dispatch: Must deliver normally
        stats_day2 = dispatcher.dispatch(report=day2_report)
        self.assertEqual(stats_day2["telegram"]["delivered"], 1)
        self.assertEqual(stats_day2["telegram"]["skipped"], 0)
        self.assertEqual(stats_day2["email"]["delivered"], 1)
        self.assertEqual(stats_day2["email"]["skipped"], 0)

        # Both dates are recorded independently
        self.assertTrue(self.db.is_report_delivered("2026-08-16", "telegram", "chat_user_4"))
        self.assertTrue(self.db.is_report_delivered("2026-08-17", "telegram", "chat_user_4"))
        self.assertTrue(self.db.is_report_delivered("2026-08-16", "email", "user4@example.com"))
        self.assertTrue(self.db.is_report_delivered("2026-08-17", "email", "user4@example.com"))

    def test_channel_error_isolation(self):
        """Failure in Telegram does NOT block Email dispatch."""
        self.db.upsert_telegram_user("tg_err", "chat_err", username="error_user")
        self.db.set_telegram_digest_subscription("tg_err", True)

        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "success@example.com"
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        # Telegram raises exception
        dispatcher.telegram_bot.send_message = MagicMock(side_effect=Exception("Telegram Network Timeout"))
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        dispatcher.email_notifier.send_newsletter = MagicMock(return_value=True)

        stats = dispatcher.dispatch(report=self.sample_report)

        self.assertEqual(stats["telegram"]["failed"], 1)
        self.assertEqual(stats["email"]["delivered"], 1)
        dispatcher.email_notifier.send_newsletter.assert_called_once()

    def test_email_error_isolation(self):
        """Failure in Email does NOT affect Telegram dispatch."""
        self.db.upsert_telegram_user("tg_ok", "chat_ok", username="ok_user")
        self.db.set_telegram_digest_subscription("tg_ok", True)

        self.db.update_preferences({
            "id": "default",
            "email_newsletter_enabled": True,
            "newsletter_email": "bad_email@example.com"
        })

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = "fake_bot_token"
        dispatcher.telegram_bot.send_message = MagicMock(return_value=True)
        dispatcher.email_notifier.username = "sender@example.com"
        dispatcher.email_notifier.password = "secret"
        # Email raises exception
        dispatcher.email_notifier.send_newsletter = MagicMock(side_effect=Exception("SMTP Connection Refused"))

        stats = dispatcher.dispatch(report=self.sample_report)

        self.assertEqual(stats["telegram"]["delivered"], 1)
        self.assertEqual(stats["email"]["failed"], 1)

    def test_auto_generate_report_if_none_exists(self):
        """Dispatcher automatically generates report if not supplied and none in db."""
        # Empty reports table
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM daily_reports")

        dispatcher = UnifiedDispatcher(db=self.db, d1_client=self.d1_client)
        dispatcher.telegram_bot.bot_token = ""
        dispatcher.email_notifier.username = ""

        stats = dispatcher.dispatch()
        self.assertEqual(stats["status"], "success")
        self.assertTrue(bool(stats["report_headline"]))

if __name__ == "__main__":
    unittest.main()

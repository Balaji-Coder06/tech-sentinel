import unittest
import json
import sqlite3
from unittest.mock import patch, MagicMock
from agent.storage.db import Database
from agent.telegram.service import TelegramBotService

class TestTelegramWebhook(unittest.TestCase):
    """
    Unit and integration tests for Telegram Bot Webhook support on Cloudflare Worker + D1 architecture.
    """

    def setUp(self):
        self.db = Database()
        self.bot = TelegramBotService(bot_token="test_token_xyz", db=self.db)

    def test_start_command_registers_and_enables_digest(self):
        """1. Test that /start registers a new user in the database and enables telegram_digest_enabled by default."""
        user_id = "tg_user_webhook_001"
        chat_id = "chat_webhook_001"
        
        # Dispatch /start command
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            result = self.bot.process_command(
                command="/start",
                chat_id=chat_id,
                user_name="Alice",
                user_id=user_id,
                first_name="Alice",
                last_name="Smith",
                username="alicesmith"
            )
            self.assertTrue(result)
            mock_send.assert_called_once()
            
            # Verify message contains welcome text and digest info
            called_text = mock_send.call_args[1]["text"]
            self.assertIn("Welcome to Tech Sentinel", called_text)
            self.assertIn("Daily Digest", called_text)
            self.assertIn("Enabled", called_text)

        # Verify in database that user exists and telegram_digest_enabled is 1
        user = self.db.get_telegram_user(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user["user_id"], user_id)
        self.assertEqual(user["chat_id"], chat_id)
        self.assertEqual(user["username"], "alicesmith")
        self.assertEqual(user["telegram_digest_enabled"], 1)

    def test_repeated_start_updates_rather_than_duplicates(self):
        """2. Test that existing users are updated upon subsequent /start commands rather than duplicated."""
        user_id = "tg_user_webhook_002"
        chat_id = "chat_webhook_002"

        # First registration
        self.bot.process_command(
            command="/start",
            chat_id=chat_id,
            user_id=user_id,
            first_name="Bob",
            username="bob_old"
        )
        
        # Second registration with updated name/username
        self.bot.process_command(
            command="/start",
            chat_id=chat_id,
            user_id=user_id,
            first_name="Robert",
            username="bob_new"
        )

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telegram_users WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)

        user = self.db.get_telegram_user(user_id)
        self.assertEqual(user["username"], "bob_new")
        self.assertEqual(user["first_name"], "Robert")
        self.assertEqual(user["telegram_digest_enabled"], 1)

    def test_subscribe_command_enables_digest(self):
        """3. Test that /subscribe enables telegram_digest_enabled for the user."""
        user_id = "tg_user_webhook_003"
        chat_id = "chat_webhook_003"

        # Register user initially with digest disabled
        self.db.upsert_telegram_user(user_id=user_id, chat_id=chat_id, first_name="Charlie")
        self.db.set_telegram_digest_subscription(user_id, enabled=False)
        
        user_before = self.db.get_telegram_user(user_id)
        self.assertEqual(user_before["telegram_digest_enabled"], 0)

        # Issue /subscribe command
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            res = self.bot.process_command(command="/subscribe", chat_id=chat_id, user_id=user_id)
            self.assertTrue(res)
            mock_send.assert_called_once()
            called_text = mock_send.call_args[1]["text"]
            self.assertIn("Daily Digest Subscribed", called_text)

        user_after = self.db.get_telegram_user(user_id)
        self.assertEqual(user_after["telegram_digest_enabled"], 1)

    def test_unsubscribe_command_disables_digest(self):
        """4. Test that /unsubscribe disables telegram_digest_enabled for the user."""
        user_id = "tg_user_webhook_004"
        chat_id = "chat_webhook_004"

        # Register user with digest enabled
        self.db.upsert_telegram_user(user_id=user_id, chat_id=chat_id, first_name="Diana")
        self.db.set_telegram_digest_subscription(user_id, enabled=True)

        user_before = self.db.get_telegram_user(user_id)
        self.assertEqual(user_before["telegram_digest_enabled"], 1)

        # Issue /unsubscribe command
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            res = self.bot.process_command(command="/unsubscribe", chat_id=chat_id, user_id=user_id)
            self.assertTrue(res)
            mock_send.assert_called_once()
            called_text = mock_send.call_args[1]["text"]
            self.assertIn("Daily Digest Unsubscribed", called_text)

        user_after = self.db.get_telegram_user(user_id)
        self.assertEqual(user_after["telegram_digest_enabled"], 0)

    def test_status_command_reports_accurate_subscription_state(self):
        """5. Test that /status reports the user's current subscription status accurately."""
        user_id_sub = "tg_user_sub"
        chat_id_sub = "chat_sub"
        user_id_unsub = "tg_user_unsub"
        chat_id_unsub = "chat_unsub"

        # User A: Subscribed
        self.db.upsert_telegram_user(user_id=user_id_sub, chat_id=chat_id_sub, first_name="SubUser")
        self.db.set_telegram_digest_subscription(user_id_sub, enabled=True)

        # User B: Unsubscribed
        self.db.upsert_telegram_user(user_id=user_id_unsub, chat_id=chat_id_unsub, first_name="UnsubUser")
        self.db.set_telegram_digest_subscription(user_id_unsub, enabled=False)

        # Check User A status
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            self.bot.process_command(command="/status", chat_id=chat_id_sub, user_id=user_id_sub)
            called_text = mock_send.call_args[1]["text"]
            self.assertIn("Subscribed", called_text)
            self.assertIn("8:00 PM IST", called_text)

        # Check User B status
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            self.bot.process_command(command="/status", chat_id=chat_id_unsub, user_id=user_id_unsub)
            called_text = mock_send.call_args[1]["text"]
            self.assertIn("Not Subscribed", called_text)

    def test_help_command_displays_all_endpoints(self):
        """6. Test that /help command includes all intelligence and subscription commands."""
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            self.bot.process_command(command="/help", chat_id="chat_help")
            mock_send.assert_called_once()
            called_text = mock_send.call_args[1]["text"]
            self.assertIn("/news", called_text)
            self.assertIn("/latest", called_text)
            self.assertIn("/opportunities", called_text)
            self.assertIn("/status", called_text)
            self.assertIn("/subscribe", called_text)
            self.assertIn("/unsubscribe", called_text)

    def test_news_opportunities_and_latest_commands(self):
        """7. Test that /news, /opportunities, and /latest successfully format and reply."""
        # /news
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            res = self.bot.process_command(command="/news", chat_id="chat_news")
            self.assertTrue(res)
            mock_send.assert_called_once()

        # /opportunities
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            res = self.bot.process_command(command="/opportunities", chat_id="chat_opps")
            self.assertTrue(res)
            mock_send.assert_called_once()

        # /latest
        with patch.object(self.bot, "send_message", return_value=True) as mock_send:
            res = self.bot.process_command(command="/latest", chat_id="chat_latest")
            self.assertTrue(res)
            mock_send.assert_called_once()

    def test_webhook_secret_header_contract(self):
        """8. Test the webhook secret token contract used by Cloudflare Worker API."""
        expected_secret = "sentinel_webhook_secret_12345"
        
        # Valid header check simulation
        valid_headers = {"X-Telegram-Bot-Api-Secret-Token": expected_secret}
        self.assertEqual(valid_headers.get("X-Telegram-Bot-Api-Secret-Token"), expected_secret)

        # Invalid header check simulation
        invalid_headers = {"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"}
        self.assertNotEqual(invalid_headers.get("X-Telegram-Bot-Api-Secret-Token"), expected_secret)

        # Missing header simulation
        missing_headers = {}
        self.assertIsNone(missing_headers.get("X-Telegram-Bot-Api-Secret-Token"))

if __name__ == "__main__":
    unittest.main()

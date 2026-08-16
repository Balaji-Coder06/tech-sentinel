import unittest
import os
from unittest.mock import patch, MagicMock
from agent.telegram.service import (
    TelegramBotService,
    format_time_ago,
    is_valid_telegram_button_url,
    get_public_web_app_url
)
from agent.storage.db import Database

class TestTelegramBotService(unittest.TestCase):
    def setUp(self):
        self.db = Database()

    def test_new_telegram_user_registration(self):
        """1. Test that a new Telegram user is registered persistently in SQLite."""
        user = self.db.upsert_telegram_user(
            user_id="tg_test_user_001",
            chat_id="chat_001",
            username="balajicoder",
            first_name="Balaji",
            last_name="Dev"
        )
        self.assertIsNotNone(user)
        self.assertEqual(user["user_id"], "tg_test_user_001")
        self.assertEqual(user["chat_id"], "chat_001")
        self.assertEqual(user["username"], "balajicoder")
        self.assertEqual(user["first_name"], "Balaji")

        # Verify from database lookup
        fetched = self.db.get_telegram_user("tg_test_user_001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["chat_id"], "chat_001")

    def test_repeated_start_does_not_duplicate_user(self):
        """2. Test that repeated /start calls are idempotent and update user data without duplication."""
        # Initial registration
        self.db.upsert_telegram_user(
            user_id="tg_test_user_002",
            chat_id="chat_002",
            username="old_handle",
            first_name="Alice"
        )
        # Repeated /start with updated username
        self.db.upsert_telegram_user(
            user_id="tg_test_user_002",
            chat_id="chat_002",
            username="new_handle",
            first_name="Alice Updated"
        )

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telegram_users WHERE user_id = 'tg_test_user_002'")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)

        user = self.db.get_telegram_user("tg_test_user_002")
        self.assertEqual(user["username"], "new_handle")
        self.assertEqual(user["first_name"], "Alice Updated")

    def test_telegram_user_preferences_resolution(self):
        """3. Test Telegram user → preferences resolution."""
        self.db.upsert_telegram_user(
            user_id="tg_test_user_003",
            chat_id="chat_003",
            first_name="Bob"
        )
        # Initial preferences should resolve to default
        prefs = self.db.get_telegram_user_preferences("tg_test_user_003")
        self.assertIsNotNone(prefs)
        self.assertIn("categories", prefs)
        self.assertIn("ai", prefs["categories"])

    def test_two_users_different_preferences(self):
        """4. Test that two different Telegram users can have distinct customized preferences in SQLite."""
        # Register User A and User B
        self.db.upsert_telegram_user(user_id="tg_user_A", chat_id="chat_A", first_name="UserA")
        self.db.upsert_telegram_user(user_id="tg_user_B", chat_id="chat_B", first_name="UserB")

        # Set User A preferences: only 'ai'
        self.db.update_telegram_user_preferences("tg_user_A", {
            "categories": ["ai"],
            "theme": "dark"
        })

        # Set User B preferences: only 'cloud' and 'cybersecurity'
        self.db.update_telegram_user_preferences("tg_user_B", {
            "categories": ["cloud", "cybersecurity"],
            "theme": "light"
        })

        prefs_a = self.db.get_telegram_user_preferences("tg_user_A")
        prefs_b = self.db.get_telegram_user_preferences("tg_user_B")

        self.assertEqual(prefs_a["categories"], ["ai"])
        self.assertEqual(prefs_b["categories"], ["cloud", "cybersecurity"])
        self.assertNotEqual(prefs_a["categories"], prefs_b["categories"])

    def test_news_uses_requesting_user_preferences(self):
        """5. Test that /news uses the requesting user's preferences to filter results."""
        bot = TelegramBotService(bot_token="fake_token", db=self.db)

        # Register User AI Only
        self.db.upsert_telegram_user(user_id="tg_user_ai", chat_id="chat_ai", first_name="AI Fan")
        self.db.update_telegram_user_preferences("tg_user_ai", {
            "categories": ["ai"]
        })

        # Register User Cloud Only
        self.db.upsert_telegram_user(user_id="tg_user_cloud", chat_id="chat_cloud", first_name="Cloud Fan")
        self.db.update_telegram_user_preferences("tg_user_cloud", {
            "categories": ["cloud"]
        })

        msg_ai, _ = bot.build_personalized_news_message(limit=5, user_id="tg_user_ai")
        msg_cloud, _ = bot.build_personalized_news_message(limit=5, user_id="tg_user_cloud")

        self.assertIn("[AI]", msg_ai)
        self.assertNotIn("[CLOUD]", msg_ai)

        self.assertIn("[CLOUD]", msg_cloud)
        self.assertNotIn("[AI]", msg_cloud)

    def test_button_url_validation(self):
        # 1. Invalid / Localhost URLs (must be rejected for Telegram inline buttons)
        self.assertFalse(is_valid_telegram_button_url(None))
        self.assertFalse(is_valid_telegram_button_url(""))
        self.assertFalse(is_valid_telegram_button_url("http://localhost:3000"))
        self.assertFalse(is_valid_telegram_button_url("http://localhost:3000/news"))
        self.assertFalse(is_valid_telegram_button_url("https://localhost:8000/free"))
        self.assertFalse(is_valid_telegram_button_url("http://127.0.0.1:3000"))
        self.assertFalse(is_valid_telegram_button_url("http://0.0.0.0:3000"))
        self.assertFalse(is_valid_telegram_button_url("/news"))
        self.assertFalse(is_valid_telegram_button_url("ftp://example.com"))

        # 2. Valid Public URLs (must be accepted)
        self.assertTrue(is_valid_telegram_button_url("https://github.com/trending"))
        self.assertTrue(is_valid_telegram_button_url("https://cloud.google.com/free"))
        self.assertTrue(is_valid_telegram_button_url("https://techcrunch.com/article-123"))
        self.assertTrue(is_valid_telegram_button_url("http://dev.to/article-456"))

    def test_public_web_app_url_handling(self):
        with patch.dict(os.environ, {"WEB_APP_URL": ""}):
            from agent.config import settings
            settings.WEB_APP_URL = ""
            self.assertIsNone(get_public_web_app_url())
            self.assertIsNone(get_public_web_app_url("news"))

        with patch.dict(os.environ, {"WEB_APP_URL": "http://localhost:3000"}):
            settings.WEB_APP_URL = "http://localhost:3000"
            self.assertIsNone(get_public_web_app_url())

        with patch.dict(os.environ, {"WEB_APP_URL": "https://tech-sentinel.app"}):
            settings.WEB_APP_URL = "https://tech-sentinel.app"
            self.assertEqual(get_public_web_app_url(), "https://tech-sentinel.app")
            self.assertEqual(get_public_web_app_url("news"), "https://tech-sentinel.app/news")
            settings.WEB_APP_URL = ""

    def test_send_message_filters_localhost_buttons(self):
        bot = TelegramBotService(bot_token="fake_token")
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            bad_markup = {
                "inline_keyboard": [
                    [
                        {"text": "Bad Localhost", "url": "http://localhost:3000/news"},
                        {"text": "Good External", "url": "https://github.com/vshulcz/deja-vu"}
                    ]
                ]
            }

            bot.send_message("12345", "Test Message", reply_markup=bad_markup)
            sent_payload = mock_client.post.call_args[1]["json"]
            self.assertIn("reply_markup", sent_payload)
            keyboard = sent_payload["reply_markup"]["inline_keyboard"]
            self.assertEqual(len(keyboard[0]), 1)
            self.assertEqual(keyboard[0][0]["text"], "Good External")
            self.assertEqual(keyboard[0][0]["url"], "https://github.com/vshulcz/deja-vu")

    def test_welcome_message_format(self):
        bot = TelegramBotService(bot_token="fake_token")
        welcome_general = bot.build_welcome_message()
        self.assertIn("Welcome to Tech Sentinel", welcome_general)
        self.assertIn("Curated Intelligence", welcome_general)
        self.assertNotIn("localhost:3000", welcome_general)

    def test_help_command_format(self):
        bot = TelegramBotService(bot_token="fake_token")
        help_msg = bot.build_help_message()
        self.assertIn("TECH SENTINEL — COMMAND REFERENCE", help_msg)
        self.assertIn("/news", help_msg)
        self.assertIn("/latest", help_msg)
        self.assertIn("/opportunities", help_msg)
        self.assertNotIn("localhost:3000", help_msg)

    def test_command_routing(self):
        bot = TelegramBotService(bot_token="fake_token", db=self.db)
        
        with patch.object(bot, "send_message", return_value=True) as mock_send:
            self.assertTrue(bot.process_command("/news", "12345", user_id="12345"))
            self.assertIn("PERSONALIZED INTELLIGENCE", mock_send.call_args[1]["text"])

            self.assertTrue(bot.process_command("/latest", "12345"))
            self.assertIn("LATEST INTELLIGENCE STREAM", mock_send.call_args[1]["text"])

            self.assertTrue(bot.process_command("/opportunities", "12345"))
            self.assertIn("FREE OPPORTUNITY RADAR", mock_send.call_args[1]["text"])

            self.assertTrue(bot.process_command("/help", "12345"))
            self.assertIn("COMMAND REFERENCE", mock_send.call_args[1]["text"])

            self.assertTrue(bot.process_command("/start", "12345", user_name="Balaji", user_id="12345"))
            self.assertIn("Welcome to Tech Sentinel", mock_send.call_args[1]["text"])

            self.assertTrue(bot.process_command("/digest on", "12345", user_id="12345"))
            self.assertIn("Daily Digest Subscribed", mock_send.call_args[1]["text"])

            self.assertTrue(bot.process_command("/digest off", "12345", user_id="12345"))
            self.assertIn("Daily Digest Unsubscribed", mock_send.call_args[1]["text"])

            self.assertTrue(bot.process_command("/digest", "12345", user_id="12345"))
            self.assertIn("DAILY DIGEST SETTINGS", mock_send.call_args[1]["text"])

    def test_format_time_ago(self):
        self.assertEqual(format_time_ago(None), "recently")
        self.assertEqual(format_time_ago("invalid-date"), "recently")

if __name__ == "__main__":
    unittest.main()

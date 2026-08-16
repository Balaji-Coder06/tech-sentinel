import unittest
import os
from unittest.mock import patch, MagicMock
from agent.telegram.service import TelegramBotService, is_valid_telegram_button_url
from agent.telegram.digest import run_telegram_digest
from agent.storage.db import Database

class TestTelegramDigest(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.bot = TelegramBotService(bot_token="test_fake_token", db=self.db)

    def test_subscription_state_default_false(self):
        """1. Test that new Telegram users are NOT automatically subscribed to the digest on registration."""
        user = self.db.upsert_telegram_user(
            user_id="tg_sub_test_01",
            chat_id="chat_sub_01",
            first_name="Sam"
        )
        self.assertEqual(user.get("telegram_digest_enabled", 0), 0)

        # Check in database
        fetched = self.db.get_telegram_user("tg_sub_test_01")
        self.assertEqual(fetched.get("telegram_digest_enabled"), 0)

    def test_subscription_toggle_commands(self):
        """2. Test that /digest on and /digest off update the subscription state persistently."""
        user_id = "tg_sub_test_02"
        self.db.upsert_telegram_user(user_id=user_id, chat_id="chat_sub_02", first_name="Dave")

        with patch.object(self.bot, "send_message", return_value=True):
            # /digest on
            self.bot.process_command("/digest on", "chat_sub_02", user_id=user_id)
            user = self.db.get_telegram_user(user_id)
            self.assertEqual(user.get("telegram_digest_enabled"), 1)

            # /digest off
            self.bot.process_command("/digest off", "chat_sub_02", user_id=user_id)
            user = self.db.get_telegram_user(user_id)
            self.assertEqual(user.get("telegram_digest_enabled"), 0)

    def test_digest_preference_filtering(self):
        """3. Test that digest respects category preferences (e.g. user with AI disabled receives 0 AI articles)."""
        # User without AI preference (only cloud and open_source)
        prefs_no_ai = {
            "categories": ["cloud", "open_source"]
        }

        # User with only AI preference
        prefs_only_ai = {
            "categories": ["ai"]
        }

        msg_no_ai, _ = self.bot.build_digest_message(user_prefs=prefs_no_ai, limit_news=4)
        msg_only_ai, _ = self.bot.build_digest_message(user_prefs=prefs_only_ai, limit_news=4)

        self.assertNotIn("[AI]", msg_no_ai)
        self.assertIn("[AI]", msg_only_ai)
        self.assertNotIn("[CLOUD]", msg_only_ai)

    def test_digest_message_buttons_and_urls(self):
        """4. Test that digest generates direct external links and zero localhost URLs in markup."""
        msg, reply_markup = self.bot.build_digest_message(limit_news=4, limit_opps=3)

        self.assertIn("DAILY INTELLIGENCE DIGEST", msg)
        self.assertNotIn("localhost:3000", msg)

        if reply_markup and "inline_keyboard" in reply_markup:
            for row in reply_markup["inline_keyboard"]:
                for btn in row:
                    url = btn.get("url", "")
                    self.assertTrue(is_valid_telegram_button_url(url))
                    self.assertNotIn("localhost", url)

    def test_failed_user_isolation(self):
        """5. Test that if delivery fails for one subscriber, subsequent subscribers still receive their digests."""
        mock_subscribers = [
            {
                "user_id": "user_bad",
                "chat_id": "chat_bad",
                "first_name": "BlockedUser",
                "preferences": {"categories": ["ai"]}
            },
            {
                "user_id": "user_good",
                "chat_id": "chat_good",
                "first_name": "ActiveUser",
                "preferences": {"categories": ["cloud"]}
            }
        ]

        def fake_send(chat_id, text, **kwargs):
            if chat_id == "chat_bad":
                return False  # Failed delivery
            return True       # Successful delivery

        with patch("agent.telegram.digest.D1SyncClient") as mock_d1_cls, \
             patch("agent.telegram.digest.TelegramBotService") as mock_bot_cls:

            mock_d1 = MagicMock()
            mock_d1.is_configured = True
            mock_d1.get_telegram_subscribers.return_value = mock_subscribers
            mock_d1_cls.return_value = mock_d1

            mock_bot = MagicMock()
            mock_bot.is_configured = True
            mock_bot.build_digest_message.return_value = ("Test Digest", None)
            mock_bot.send_message.side_effect = fake_send
            mock_bot_cls.return_value = mock_bot

            result = run_telegram_digest()
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["dispatched"], 1)
            self.assertEqual(result["failed"], 1)
            self.assertEqual(result["total_subscribers"], 2)

if __name__ == "__main__":
    unittest.main()

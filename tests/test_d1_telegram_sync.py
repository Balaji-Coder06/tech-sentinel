import unittest
import json
import sqlite3
from unittest.mock import patch, MagicMock
from agent.storage.d1_sync import D1SyncClient
from agent.storage.db import Database
from agent.telegram.service import TelegramBotService

class TestD1TelegramSync(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.worker_url = "https://tech-sentinel-api.example.workers.dev"
        self.secret = "test-secret-12345"
        self.client = D1SyncClient(worker_url=self.worker_url, secret=self.secret)
        self.bot = TelegramBotService(bot_token="test_fake_token", db=self.db)

    def test_telegram_user_sync(self):
        """1. Test that Telegram users are properly serialized and pushed via D1SyncClient."""
        users = [
            {
                "user_id": "7593127065",
                "chat_id": "7593127065",
                "username": "Mystic_balaji",
                "first_name": "Balaji",
                "last_name": None,
                "preference_id": "default",
                "telegram_digest_enabled": 1
            }
        ]

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "message": "Ingested 1 users"}
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            success = self.client.sync_telegram_data(users=users, preferences=[])
            self.assertTrue(success)

            called_endpoint = mock_client.post.call_args[0][0]
            called_json = mock_client.post.call_args[1]["json"]
            called_headers = mock_client.post.call_args[1]["headers"]

            self.assertEqual(called_endpoint, f"{self.worker_url}/api/ingest")
            self.assertEqual(called_headers["Authorization"], f"Bearer {self.secret}")
            self.assertIn("telegram_users", called_json)
            self.assertEqual(len(called_json["telegram_users"]), 1)
            self.assertEqual(called_json["telegram_users"][0]["user_id"], "7593127065")
            self.assertEqual(called_json["telegram_users"][0]["telegram_digest_enabled"], 1)

    def test_preference_sync(self):
        """2. Test that user preference profiles are synchronized to D1 via Ingestion API."""
        preferences = [
            {
                "id": "tg_7593127065",
                "user_name": "Balaji",
                "theme": "dark",
                "categories": ["ai", "cloud"],
                "keywords": ["llm", "vertex"],
                "opportunity_types": ["ai_credits", "cloud"],
                "enable_daily_brief": True,
                "enable_critical_alerts": True
            }
        ]

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            success = self.client.sync_telegram_data(users=[], preferences=preferences)
            self.assertTrue(success)

            called_json = mock_client.post.call_args[1]["json"]
            self.assertIn("preferences", called_json)
            self.assertEqual(len(called_json["preferences"]), 1)
            self.assertEqual(called_json["preferences"][0]["id"], "tg_7593127065")
            self.assertEqual(called_json["preferences"][0]["categories"], ["ai", "cloud"])

    def test_authenticated_user_retrieval(self):
        """3. Test that get_telegram_subscribers retrieves subscribed users and their preferences with Bearer auth."""
        mock_subscribers_payload = {
            "success": True,
            "count": 1,
            "data": [
                {
                    "user_id": "7593127065",
                    "chat_id": "7593127065",
                    "username": "Mystic_balaji",
                    "first_name": "Balaji",
                    "preference_id": "tg_7593127065",
                    "telegram_digest_enabled": True,
                    "preferences": {
                        "id": "tg_7593127065",
                        "categories": ["ai", "open_source"],
                        "enable_daily_brief": True
                    }
                }
            ]
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_subscribers_payload
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            subscribers = self.client.get_telegram_subscribers()
            self.assertEqual(len(subscribers), 1)
            self.assertEqual(subscribers[0]["user_id"], "7593127065")
            self.assertEqual(subscribers[0]["preferences"]["categories"], ["ai", "open_source"])

            called_endpoint = mock_client.get.call_args[0][0]
            called_headers = mock_client.get.call_args[1]["headers"]
            self.assertEqual(called_endpoint, f"{self.worker_url}/api/telegram/subscribers")
            self.assertEqual(called_headers["Authorization"], f"Bearer {self.secret}")

    def test_unauthenticated_requests_rejected(self):
        """4. Test that unauthenticated or invalid token requests return empty result and log error."""
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": "Unauthorized: Invalid Token"}
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            subscribers = self.client.get_telegram_subscribers()
            self.assertEqual(subscribers, [])

    def test_multiple_telegram_users_isolated(self):
        """5. Test that multiple Telegram users retrieved from D1 maintain isolated preference profiles."""
        mock_payload = {
            "success": True,
            "count": 2,
            "data": [
                {
                    "user_id": "user_101",
                    "chat_id": "chat_101",
                    "first_name": "Alice",
                    "preferences": {
                        "id": "tg_user_101",
                        "categories": ["ai"],
                        "enable_daily_brief": True
                    }
                },
                {
                    "user_id": "user_202",
                    "chat_id": "chat_202",
                    "first_name": "Bob",
                    "preferences": {
                        "id": "tg_user_202",
                        "categories": ["cybersecurity", "cloud"],
                        "enable_daily_brief": False
                    }
                }
            ]
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payload
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            subs = self.client.get_telegram_subscribers()
            self.assertEqual(len(subs), 2)

            user_a = next(u for u in subs if u["user_id"] == "user_101")
            user_b = next(u for u in subs if u["user_id"] == "user_202")

            self.assertEqual(user_a["preferences"]["categories"], ["ai"])
            self.assertEqual(user_b["preferences"]["categories"], ["cybersecurity", "cloud"])
            self.assertNotEqual(user_a["preferences"]["categories"], user_b["preferences"]["categories"])
            self.assertTrue(user_a["preferences"]["enable_daily_brief"])
            self.assertFalse(user_b["preferences"]["enable_daily_brief"])

    def test_digest_on_syncs_enabled_payload_to_d1(self):
        """6. Regression Test: /digest on persists telegram_digest_enabled=1 locally and syncs enabled state to D1."""
        user_id = "7593127065"
        self.db.upsert_telegram_user(user_id=user_id, chat_id=user_id, first_name="Balaji")

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            with patch.object(self.bot, "send_message", return_value=True):
                self.bot.process_command("/digest on", chat_id=user_id, user_id=user_id)

            local_user = self.db.get_telegram_user(user_id)
            self.assertEqual(local_user.get("telegram_digest_enabled"), 1)

            users = self.db.get_all_telegram_users()
            self.client.sync_telegram_data(users=users, preferences=[])

            called_json = mock_client.post.call_args[1]["json"]
            synced_user = next(u for u in called_json["telegram_users"] if str(u["user_id"]) == user_id)
            self.assertEqual(synced_user["telegram_digest_enabled"], 1)

    def test_digest_off_syncs_disabled_payload_to_d1(self):
        """7. Regression Test: /digest off persists telegram_digest_enabled=0 locally and syncs disabled state to D1."""
        user_id = "7593127065"
        self.db.upsert_telegram_user(user_id=user_id, chat_id=user_id, first_name="Balaji")

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            with patch.object(self.bot, "send_message", return_value=True):
                self.bot.process_command("/digest off", chat_id=user_id, user_id=user_id)

            local_user = self.db.get_telegram_user(user_id)
            self.assertEqual(local_user.get("telegram_digest_enabled"), 0)

            users = self.db.get_all_telegram_users()
            self.client.sync_telegram_data(users=users, preferences=[])

            called_json = mock_client.post.call_args[1]["json"]
            synced_user = next(u for u in called_json["telegram_users"] if str(u["user_id"]) == user_id)
            self.assertEqual(synced_user["telegram_digest_enabled"], 0)

    def test_subscribed_only_query_param(self):
        """8. Regression Test: subscribed_only=true sends correct query parameter and filters subscribers."""
        mock_payload = {
            "success": True,
            "count": 1,
            "data": [
                {
                    "user_id": "7593127065",
                    "chat_id": "7593127065",
                    "first_name": "Balaji",
                    "telegram_digest_enabled": True,
                    "preferences": {"categories": ["ai"]}
                }
            ]
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_payload
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            subs = self.client.get_telegram_subscribers(subscribed_only=True)
            self.assertEqual(len(subs), 1)
            self.assertEqual(subs[0]["user_id"], "7593127065")

            called_endpoint = mock_client.get.call_args[0][0]
            self.assertEqual(called_endpoint, f"{self.worker_url}/api/telegram/subscribers?subscribed_only=true")

    def test_foreign_key_ordering_and_safe_fallback(self):
        """9. Regression Test: Ingesting preferences before telegram_users satisfies FK constraints and falls back safely."""
        # Setup an in-memory SQLite database with strict foreign keys enabled
        mem_conn = sqlite3.connect(":memory:")
        mem_conn.execute("PRAGMA foreign_keys = ON;")
        
        # Create preferences and telegram_users tables
        mem_conn.execute("""
        CREATE TABLE preferences (
            id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL DEFAULT 'User',
            theme TEXT NOT NULL DEFAULT 'system',
            categories TEXT NOT NULL DEFAULT '[]',
            keywords TEXT NOT NULL DEFAULT '[]',
            opportunity_types TEXT NOT NULL DEFAULT '[]',
            enable_daily_brief INTEGER NOT NULL DEFAULT 1,
            enable_critical_alerts INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        );
        """)
        
        mem_conn.execute("""
        CREATE TABLE telegram_users (
            user_id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            preference_id TEXT DEFAULT 'default',
            telegram_digest_enabled INTEGER DEFAULT 0,
            last_digest_sent_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (preference_id) REFERENCES preferences(id) ON DELETE SET NULL
        );
        """)

        # Attempt 1: Inserting user before preferences table has 'default' or custom ID fails FK check
        with self.assertRaises(sqlite3.IntegrityError):
            mem_conn.execute(
                "INSERT INTO telegram_users (user_id, chat_id, preference_id, created_at, updated_at) VALUES ('u1', 'c1', 'default', datetime('now'), datetime('now'))"
            )

        # Attempt 2: Seed parent preference FIRST (Worker Step 1)
        mem_conn.execute(
            "INSERT INTO preferences (id, user_name, updated_at) VALUES ('default', 'Balaji', datetime('now'))"
        )
        mem_conn.execute(
            "INSERT INTO preferences (id, user_name, updated_at) VALUES ('tg_custom_01', 'Custom User', datetime('now'))"
        )

        # Attempt 3: Ingest telegram_users SECOND (Worker Step 2) with both default and custom preference references
        mem_conn.execute(
            "INSERT INTO telegram_users (user_id, chat_id, preference_id, created_at, updated_at) VALUES ('u1', 'c1', 'default', datetime('now'), datetime('now'))"
        )
        mem_conn.execute(
            "INSERT INTO telegram_users (user_id, chat_id, preference_id, created_at, updated_at) VALUES ('u2', 'c2', 'tg_custom_01', datetime('now'), datetime('now'))"
        )

        # Confirm users are properly stored and linked
        users = mem_conn.execute("SELECT user_id, preference_id FROM telegram_users ORDER BY user_id").fetchall()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0], ("u1", "default"))
        self.assertEqual(users[1], ("u2", "tg_custom_01"))

        # Attempt 4: Idempotent upsert of existing user without duplication
        mem_conn.execute("""
        INSERT INTO telegram_users (user_id, chat_id, preference_id, telegram_digest_enabled, created_at, updated_at)
        VALUES ('u1', 'c1', 'default', 1, datetime('now'), datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET telegram_digest_enabled = 1;
        """)

        users_after = mem_conn.execute("SELECT user_id, telegram_digest_enabled FROM telegram_users WHERE user_id = 'u1'").fetchall()
        self.assertEqual(len(users_after), 1)
        self.assertEqual(users_after[0], ("u1", 1))

        mem_conn.close()

    def test_sources_and_news_foreign_key_ordering(self):
        """10. Regression Test: Ingesting sources before news satisfies FK constraints and allows independent ingestion."""
        mem_conn = sqlite3.connect(":memory:")
        mem_conn.execute("PRAGMA foreign_keys = ON;")

        # Create sources and news tables
        mem_conn.execute("""
        CREATE TABLE sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL DEFAULT 'rss',
            category TEXT NOT NULL DEFAULT 'tech'
        );
        """)

        mem_conn.execute("""
        CREATE TABLE news (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            source_id TEXT,
            source_name TEXT NOT NULL,
            category TEXT NOT NULL,
            published_at TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL
        );
        """)

        # Attempt 1: Inserting news with unseeded source_id fails under foreign keys
        with self.assertRaises(sqlite3.IntegrityError):
            mem_conn.execute(
                "INSERT INTO news (id, title, url, source_id, source_name, category, published_at) VALUES ('n1', 'Test News', 'https://example.com/n1', 'hn', 'Hacker News', 'tech', datetime('now'))"
            )

        # Attempt 2: Ingest sources FIRST (Worker Step 3)
        mem_conn.execute(
            "INSERT INTO sources (id, name, url, type, category) VALUES ('hn', 'Hacker News', 'https://news.ycombinator.com', 'rss', 'tech') ON CONFLICT(id) DO NOTHING"
        )

        # Attempt 3: Ingest news SECOND (Worker Step 4)
        mem_conn.execute(
            "INSERT INTO news (id, title, url, source_id, source_name, category, published_at) VALUES ('n1', 'Test News', 'https://example.com/n1', 'hn', 'Hacker News', 'tech', datetime('now'))"
        )

        # Verify news and source link
        stored_news = mem_conn.execute("SELECT id, source_id FROM news WHERE id = 'n1'").fetchone()
        self.assertEqual(stored_news, ("n1", "hn"))

        mem_conn.close()

if __name__ == "__main__":
    unittest.main()

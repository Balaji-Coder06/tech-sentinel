import unittest
import json
from unittest.mock import patch, MagicMock
from agent.storage.d1_sync import D1SyncClient
from agent.storage.db import Database

class TestD1TelegramSync(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.worker_url = "https://tech-sentinel-api.example.workers.dev"
        self.secret = "test-secret-12345"
        self.client = D1SyncClient(worker_url=self.worker_url, secret=self.secret)

    def test_telegram_user_sync(self):
        """1. Test that Telegram users are properly serialized and pushed via D1SyncClient."""
        users = [
            {
                "user_id": "7593127065",
                "chat_id": "7593127065",
                "username": "Mystic_balaji",
                "first_name": "Balaji",
                "last_name": None,
                "preference_id": "default"
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

            # Check that the payload sent to /api/ingest contains telegram_users
            called_endpoint = mock_client.post.call_args[0][0]
            called_json = mock_client.post.call_args[1]["json"]
            called_headers = mock_client.post.call_args[1]["headers"]

            self.assertEqual(called_endpoint, f"{self.worker_url}/api/ingest")
            self.assertEqual(called_headers["Authorization"], f"Bearer {self.secret}")
            self.assertIn("telegram_users", called_json)
            self.assertEqual(len(called_json["telegram_users"]), 1)
            self.assertEqual(called_json["telegram_users"][0]["user_id"], "7593127065")

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

            # Verify endpoint and Authorization header
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

if __name__ == "__main__":
    unittest.main()

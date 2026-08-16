import unittest
from unittest.mock import patch, MagicMock
from agent.ai import get_ai_provider, AISummarizer, DailyDigestGenerator
from agent.ai.groq_provider import GroqProvider
from agent.ai.gemini_provider import GeminiProvider
from agent.ai.fallback_provider import FallbackProvider
from agent.models import RawItem, SentinelSummary

class TestAIEngine(unittest.TestCase):
    def setUp(self):
        self.sample_item = RawItem(
            title="Anthropic Releases Claude 3.7 Sonnet with Dynamic Hybrid Reasoning",
            description="Anthropic launched Claude 3.7 Sonnet with instantaneous and extended reasoning tokens.",
            content="Anthropic announced Claude 3.7 Sonnet. SWE-bench Verified score reached 70.3%. Pricing remains unchanged at $3/million tokens.",
            url="https://example.com/claude-3-7",
            source_id="src_anthropic",
            source_name="Anthropic",
            category="ai"
        )

    def test_fallback_provider_produces_valid_summary(self):
        """1. FallbackProvider produces valid SentinelSummary deterministically."""
        provider = FallbackProvider()
        summary = provider.generate_summary(
            self.sample_item.title,
            self.sample_item.content,
            self.sample_item.category
        )
        self.assertIsInstance(summary, SentinelSummary)
        self.assertTrue(len(summary.what) > 0)
        self.assertTrue(len(summary.why) > 0)
        self.assertTrue(len(summary.action) > 0)
        self.assertTrue(isinstance(summary.key_points, list))

    def test_fallback_provider_produces_valid_digest(self):
        """2. FallbackProvider produces valid Daily Digest deterministically."""
        provider = FallbackProvider()
        digest = provider.generate_daily_digest(
            [{"title": "News 1", "category": "ai"}],
            [{"title": "Free Credit", "normal_value": "$100"}]
        )
        self.assertIn("headline", digest)
        self.assertIn("thirty_sec_summary", digest)
        self.assertIn("sentinel_take", digest)

    @patch("httpx.Client")
    def test_groq_provider_successful_summary(self, mock_client_cls):
        """3. GroqProvider correctly parses valid JSON completion."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"what": "Claude 3.7 released", "why": "Top SWE-bench score", "action": "Test in console", "key_points": ["Point 1"]}'
                }
            }]
        }
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        with patch("agent.ai.groq_provider.settings.GROQ_API_KEY", "mock_groq_key"):
            provider = GroqProvider()
            summary = provider.generate_summary(self.sample_item.title, self.sample_item.content, "ai")
            self.assertEqual(summary.what, "Claude 3.7 released")
            self.assertEqual(summary.why, "Top SWE-bench score")
            self.assertEqual(summary.action, "Test in console")
            self.assertEqual(summary.key_points, ["Point 1"])

    @patch("httpx.Client")
    def test_groq_error_cascades_to_fallback(self, mock_client_cls):
        """4. GroqProvider error safely cascades to secondary provider or fallback."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        fallback_spy = MagicMock()
        fallback_spy.generate_summary.return_value = SentinelSummary(
            what="Fallback summary", why="Fallback why", action="Fallback action", key_points=[]
        )

        with patch("agent.ai.groq_provider.settings.GROQ_API_KEY", "mock_groq_key"):
            provider = GroqProvider(fallback=fallback_spy)
            summary = provider.generate_summary(self.sample_item.title, self.sample_item.content, "ai")
            self.assertEqual(summary.what, "Fallback summary")
            fallback_spy.generate_summary.assert_called_once()

    @patch("httpx.Client")
    def test_gemini_provider_successful_summary(self, mock_client_cls):
        """5. GeminiProvider correctly parses valid gemini-2.5-flash response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"what": "Gemini summary", "why": "Gemini why", "action": "Gemini action", "key_points": ["Gemini pt"]}'
                    }]
                }
            }]
        }
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        with patch("agent.ai.gemini_provider.settings.GEMINI_API_KEY", "mock_gemini_key"):
            provider = GeminiProvider()
            summary = provider.generate_summary(self.sample_item.title, self.sample_item.content, "ai")
            self.assertEqual(summary.what, "Gemini summary")
            self.assertEqual(summary.why, "Gemini why")
            self.assertEqual(summary.action, "Gemini action")

    def test_get_ai_provider_strategy_resolution(self):
        """6. get_ai_provider properly resolves Groq primary when keys are present."""
        with patch("agent.ai.settings.GROQ_API_KEY", "gsk_test"), \
             patch("agent.ai.settings.GEMINI_API_KEY", "gemini_test"), \
             patch("agent.ai.settings.AI_PROVIDER", "auto"):
            provider = get_ai_provider()
            self.assertIsInstance(provider, GroqProvider)
            self.assertIsInstance(provider.fallback, GeminiProvider)
            self.assertIsInstance(provider.fallback.fallback, FallbackProvider)

if __name__ == "__main__":
    unittest.main()

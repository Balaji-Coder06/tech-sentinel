import unittest
from unittest.mock import patch, MagicMock
import httpx
from agent.ai import get_ai_provider, AISummarizer, DailyDigestGenerator
from agent.ai.groq_provider import GroqProvider
from agent.ai.gemini_provider import GeminiProvider
from agent.ai.fallback_provider import FallbackProvider
from agent.ai.rate_limiter import parse_retry_after, apply_pacing_delay
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

    @patch("agent.ai.groq_provider.apply_pacing_delay")
    @patch("httpx.Client")
    def test_groq_provider_successful_summary(self, mock_client_cls, mock_pacing):
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

    @patch("agent.ai.groq_provider.apply_pacing_delay")
    @patch("httpx.Client")
    def test_groq_error_cascades_to_fallback(self, mock_client_cls, mock_pacing):
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

    @patch("agent.ai.gemini_provider.apply_pacing_delay")
    @patch("httpx.Client")
    def test_gemini_provider_successful_summary(self, mock_client_cls, mock_pacing):
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

    def test_parse_retry_after_header_and_body(self):
        """7. Rate limiter accurately extracts wait duration from Retry-After header and error body."""
        # Header case
        res_header = httpx.Response(429, headers={"Retry-After": "4.5"})
        self.assertEqual(parse_retry_after(res_header, default_delay=2.0), 4.5)

        # Body case (e.g. 'Please try again in 3.2s')
        res_body = httpx.Response(
            429,
            json={"error": {"message": "Rate limit reached. Please try again in 3.2s.", "type": "rate_limit_exceeded"}}
        )
        self.assertEqual(parse_retry_after(res_body, default_delay=2.0), 3.2)

        # Default fallback case
        res_plain = httpx.Response(429, text="Too Many Requests")
        self.assertEqual(parse_retry_after(res_plain, default_delay=2.0), 2.0)

    @patch("time.sleep")
    @patch("agent.ai.groq_provider.apply_pacing_delay")
    @patch("httpx.Client")
    def test_groq_429_retries_and_succeeds(self, mock_client_cls, mock_pacing, mock_sleep):
        """8. Groq retries upon receiving 429 and succeeds on subsequent attempt without disabling provider."""
        mock_client = MagicMock()
        mock_res_429 = MagicMock()
        mock_res_429.status_code = 429
        mock_res_429.headers = {"Retry-After": "1.5"}
        mock_res_429.json.return_value = {"error": {"message": "Rate limit reached"}}

        mock_res_200 = MagicMock()
        mock_res_200.status_code = 200
        mock_res_200.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"what": "Success on retry", "why": "Rate limit passed", "action": "Continue", "key_points": []}'
                }
            }]
        }

        # First request 429, second request 200
        mock_client.post.side_effect = [mock_res_429, mock_res_200]
        mock_client_cls.return_value.__enter__.return_value = mock_client

        with patch("agent.ai.groq_provider.settings.GROQ_API_KEY", "mock_key"):
            provider = GroqProvider()
            summary = provider.generate_summary(self.sample_item.title, self.sample_item.content, "ai")
            self.assertEqual(summary.what, "Success on retry")
            mock_sleep.assert_called_with(1.5)
            self.assertEqual(mock_client.post.call_count, 2)

    @patch("time.sleep")
    @patch("agent.ai.groq_provider.apply_pacing_delay")
    @patch("httpx.Client")
    def test_groq_429_persisted_falls_back_to_gemini(self, mock_client_cls, mock_pacing, mock_sleep):
        """9. Groq falls back to Gemini only after retry backoff policy is exhausted."""
        mock_client = MagicMock()
        mock_res_429 = MagicMock()
        mock_res_429.status_code = 429
        mock_res_429.headers = {}
        mock_res_429.json.return_value = {"error": {"message": "Rate limit"}}
        mock_client.post.return_value = mock_res_429
        mock_client_cls.return_value.__enter__.return_value = mock_client

        gemini_fallback = MagicMock()
        gemini_fallback.generate_summary.return_value = SentinelSummary(
            what="Gemini rescue", why="Groq rate-limited", action="Proceed", key_points=[]
        )

        with patch("agent.ai.groq_provider.settings.GROQ_API_KEY", "mock_key"), \
             patch("agent.ai.groq_provider.settings.AI_MAX_RETRIES", 2), \
             patch("agent.ai.groq_provider.settings.AI_RETRY_BASE_DELAY_SECONDS", 1.0):
            provider = GroqProvider(fallback=gemini_fallback)
            summary = provider.generate_summary(self.sample_item.title, self.sample_item.content, "ai")
            self.assertEqual(summary.what, "Gemini rescue")
            gemini_fallback.generate_summary.assert_called_once()
            self.assertEqual(mock_client.post.call_count, 2)

    @patch("time.sleep")
    @patch("agent.ai.gemini_provider.apply_pacing_delay")
    @patch("httpx.Client")
    def test_gemini_429_persisted_falls_back_to_offline_nlp(self, mock_client_cls, mock_pacing, mock_sleep):
        """10. Gemini falls back to deterministic NLP after its retry policy is exhausted."""
        mock_client = MagicMock()
        mock_res_429 = MagicMock()
        mock_res_429.status_code = 429
        mock_res_429.headers = {}
        mock_res_429.json.return_value = {"error": {"message": "Quota exceeded"}}
        mock_client.post.return_value = mock_res_429
        mock_client_cls.return_value.__enter__.return_value = mock_client

        fallback_nlp = MagicMock()
        fallback_nlp.generate_summary.return_value = SentinelSummary(
            what="Heuristic summary", why="Offline mode", action="Read link", key_points=[]
        )

        with patch("agent.ai.gemini_provider.settings.GEMINI_API_KEY", "mock_key"), \
             patch("agent.ai.gemini_provider.settings.AI_MAX_RETRIES", 2), \
             patch("agent.ai.gemini_provider.settings.AI_RETRY_BASE_DELAY_SECONDS", 1.0):
            provider = GeminiProvider(fallback=fallback_nlp)
            summary = provider.generate_summary(self.sample_item.title, self.sample_item.content, "ai")
            self.assertEqual(summary.what, "Heuristic summary")
            fallback_nlp.generate_summary.assert_called_once()

if __name__ == "__main__":
    unittest.main()

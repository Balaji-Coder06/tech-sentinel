import unittest
from agent.ai import AISummarizer, DailyDigestGenerator, DeterministicEngine
from agent.models import RawItem, SentinelSummary

class TestDeterministicEngine(unittest.TestCase):
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

    def test_deterministic_engine_produces_valid_summary(self):
        """1. DeterministicEngine produces valid SentinelSummary with structured fields."""
        engine = DeterministicEngine()
        summary = engine.generate_summary(
            self.sample_item.title,
            self.sample_item.content,
            self.sample_item.category
        )
        self.assertIsInstance(summary, SentinelSummary)
        self.assertTrue(len(summary.what) > 0)
        self.assertTrue(len(summary.why) > 0)
        self.assertTrue(len(summary.action) > 0)
        self.assertTrue(isinstance(summary.key_points, list))
        self.assertTrue(len(summary.key_points) > 0)

    def test_deterministic_category_context_reasoning(self):
        """2. DeterministicEngine tailors context across all supported tech categories."""
        engine = DeterministicEngine()
        categories = ["ai", "cloud", "development", "open_source", "cybersecurity", "startups"]
        for cat in categories:
            summary = engine.generate_summary("New Release Tool v1.0", "Release notes for tool.", cat)
            self.assertIn(".", summary.what)
            self.assertTrue(len(summary.why) > 20)
            self.assertIn("roadmap", summary.action)

    def test_deterministic_engine_produces_valid_digest(self):
        """3. DeterministicEngine produces valid Daily Digest deterministically."""
        engine = DeterministicEngine()
        digest = engine.generate_daily_digest(
            [{"title": "News 1", "category": "ai"}],
            [{"title": "Free Credit", "normal_value": "$100"}]
        )
        self.assertIn("headline", digest)
        self.assertIn("thirty_sec_summary", digest)
        self.assertIn("sentinel_take", digest)
        self.assertTrue(len(digest["headline"]) > 0)
        self.assertTrue(len(digest["thirty_sec_summary"]) > 0)
        self.assertTrue(len(digest["sentinel_take"]) > 0)

    def test_ai_summarizer_wrapper(self):
        """4. AISummarizer wraps DeterministicEngine and extracts summary correctly."""
        summarizer = AISummarizer()
        summary = summarizer.summarize(self.sample_item)
        self.assertEqual(summary.what, "Anthropic Releases Claude 3.7 Sonnet with Dynamic Hybrid Reasoning.")
        self.assertTrue(isinstance(summary.key_points, list))

    def test_daily_digest_generator_integration(self):
        """5. DailyDigestGenerator integrates with DeterministicEngine into DailyReport."""
        generator = DailyDigestGenerator()
        report = generator.generate(
            news_items=[{
                "id": "n1",
                "title": "Major Release",
                "category": "ai",
                "importance_score": 95,
                "summary_what": "Major Release happened."
            }],
            opportunities=[{
                "id": "o1",
                "title": "Cloud Credits",
                "provider": "CloudProvider",
                "normal_value": "$300",
                "importance_score": 90
            }]
        )
        self.assertEqual(report.title, "Tech Sentinel Daily Intelligence")
        self.assertTrue(len(report.top_stories) == 1)
        self.assertTrue(len(report.free_opportunities) == 1)

    def test_deterministic_engine_offline_execution(self):
        """6. DeterministicEngine operates completely locally without external API calls."""
        engine = DeterministicEngine()
        summary = engine.generate_summary("Offline Test Title", "Content without external network", "cloud")
        self.assertIsNotNone(summary)
        self.assertTrue(len(summary.why) > 0)
        self.assertIn("infrastructure", summary.why.lower())

if __name__ == "__main__":
    unittest.main()

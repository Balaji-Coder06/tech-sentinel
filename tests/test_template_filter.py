import unittest
from agent.utils.validator import is_valid_title
from agent.models import RawItem, NewsItem, SentinelSummary
from agent.storage.db import Database
from datetime import datetime, timezone

class TestTemplateExpressionFilter(unittest.TestCase):
    def test_invalid_template_expressions_rejected(self):
        corrupted_titles = [
            "{{ $('Get Ready Post').item.json.Title }}",
            "{{ title }}",
            "${item.title}",
            "$('Get Ready Post')",
            "<%= article_title %>",
            "[% title %]",
            "undefined",
            "null",
            "[object Object]",
            "   ",
            "ab"
        ]
        for title in corrupted_titles:
            self.assertFalse(is_valid_title(title), f"Title '{title}' must be rejected as invalid template/placeholder")

    def test_clean_titles_accepted(self):
        clean_titles = [
            "Meta’s ‘open’ AI, and a $250M deal gone very wrong",
            "How to Build a Production-Ready AI Agent for $0/Month",
            "Google Cloud Free Program: $300 Credits + Free Tier Compute",
            "DeepSeek-V3 Architecture: A Comprehensive Analysis",
            "GitHub Announces Copilot Free for VS Code"
        ]
        for title in clean_titles:
            self.assertTrue(is_valid_title(title), f"Title '{title}' must be accepted")

    def test_database_rejects_corrupted_raw_and_news_items(self):
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name
        try:
            db = Database(temp_db_path)
            now_iso = datetime.now(timezone.utc).isoformat()
            
            # Test raw_items rejection
            raw_item = RawItem(
                title="{{ $('Get Ready Post').item.json.Title }}",
                url="https://example.com/corrupted-post",
                source_id="src_test",
                source_name="Test Source",
                published_at=now_iso
            )
            inserted = db.insert_raw_items([raw_item])
            self.assertEqual(inserted, 0, "Corrupted raw items must not be inserted")

            # Test news rejection
            news_item = NewsItem(
                id="news_corrupted_123",
                title="{{ $('Get Ready Post').item.json.Title }}",
                description="Test description",
                category="ai",
                url="https://example.com/corrupted-news",
                source_id="src_test",
                source_name="Test Source",
                published_at=now_iso
            )
            saved = db.insert_news(news_item)
            self.assertFalse(saved, "Corrupted news item must not be inserted")
        finally:
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except Exception:
                    pass

if __name__ == "__main__":
    unittest.main()

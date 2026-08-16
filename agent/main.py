import argparse
import logging
import sys
import time
import hashlib
from datetime import datetime, timezone
from typing import List, Tuple

from .config import settings
from .models import RawItem, NewsItem, Opportunity, DailyReport, UserPreferences, SystemStatus
from .storage.db import Database
from .storage.d1_sync import D1SyncClient
from .collectors.rss_collector import RSSCollector
from .collectors.github_collector import GitHubCollector
from .collectors.official_collector import OfficialCollector
from .processors.classifier import ContentClassifier
from .processors.deduplicator import Deduplicator
from .processors.opportunity_detector import OpportunityDetector
from .processors.verifier import Verifier
from .processors.scorer import Scorer
from .ai import get_ai_provider, AISummarizer, DailyDigestGenerator
from .notifications.telegram import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tech_sentinel")

def get_default_collectors() -> List:
    return [
        RSSCollector("src_hn", "Hacker News", "https://news.ycombinator.com/rss", "development"),
        RSSCollector("src_tc", "TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/", "ai"),
        RSSCollector("src_devto", "Dev.to", "https://dev.to/feed", "development"),
        RSSCollector("src_freecodecamp", "freeCodeCamp", "https://www.freecodecamp.org/news/rss/", "education"),
        GitHubCollector("src_gh_trend", "GitHub Trending", "https://github.com/trending", "open_source"),
        OfficialCollector("src_official", "Official Provider Registry", "https://cloud.google.com/free", "cloud")
    ]

def run_collection(db: Database) -> Tuple[int, int]:
    """Stage 1: Fetch raw feeds and persist them to raw_items staging table."""
    logger.info("📡 Starting collection from all registered sources...")
    collectors = get_default_collectors()
    all_raw_items: List[RawItem] = []
    
    for collector in collectors:
        try:
            items = collector.fetch()
            all_raw_items.extend(items)
        except Exception as e:
            logger.error(f"Failed to fetch from {collector.name}: {e}")
            
    staged = db.insert_raw_items(all_raw_items)
    logger.info(f"✅ Collection complete: Fetched {len(all_raw_items)} raw items; staged {staged} into database.")
    return len(all_raw_items), staged

def run_processing(db: Database) -> Tuple[List[NewsItem], List[Opportunity]]:
    """Stage 2: Process unprocessed raw items from staging into verified news and opportunities."""
    start_time = time.time()
    logger.info("⚙️ Starting Tech Sentinel Processing Pipeline...")

    # Load unprocessed items from database staging
    raw_items = db.get_unprocessed_raw_items()
    if not raw_items:
        logger.info("ℹ️ No unprocessed raw items found in database staging. Run 'python -m agent.main collect' first.")
        return [], []

    logger.info(f"📥 Processing {len(raw_items)} unprocessed items from database staging...")

    # 1. Deduplication
    dedup = Deduplicator()
    unique_raw = dedup.filter_unique(raw_items)
    logger.info(f"🔍 Deduplication: {len(raw_items)} -> {len(unique_raw)} unique items")

    # 2. Classification & Processing
    classifier = ContentClassifier()
    detector = OpportunityDetector()
    verifier = Verifier()
    scorer = Scorer()
    ai_provider = get_ai_provider(settings.AI_PROVIDER)
    summarizer = AISummarizer(ai_provider)
    
    user_prefs_dict = db.get_preferences()
    user_prefs = UserPreferences(**user_prefs_dict) if user_prefs_dict else UserPreferences()

    saved_news: List[NewsItem] = []
    saved_opps: List[Opportunity] = []
    processed_urls: List[str] = []

    for raw in unique_raw:
        processed_urls.append(raw.url)
        category, tags = classifier.classify(raw)
        raw.category = category

        # A. Check for Free Opportunities (Signature Feature)
        opp = detector.detect(raw)
        if opp:
            opp = verifier.verify(opp)
            if db.insert_opportunity(opp):
                saved_opps.append(opp)
                logger.info(f"🎁 Opportunity Tracked: {opp.title} ({opp.normal_value}) [{opp.verification_status}]")

        # B. Process as News Item
        importance = scorer.score_news(raw, user_prefs)
        summary = summarizer.summarize(raw)
        
        # Deterministic News ID based on canonical URL hash
        url_hash = hashlib.sha256(raw.url.strip().lower().encode('utf-8')).hexdigest()[:12]
        news_id = f"news_{url_hash}"
        
        news_item = NewsItem(
            id=news_id,
            title=raw.title,
            description=raw.description,
            content=raw.content,
            url=raw.url,
            image_url=raw.image_url,
            source_id=raw.source_id,
            source_name=raw.source_name,
            category=category,
            tags=tags,
            summary=summary,
            importance_score=importance,
            relevance_score=importance,
            is_featured=importance >= 92,
            is_trending="trending" in raw.title.lower() or importance >= 88,
            published_at=raw.published_at or datetime.now(timezone.utc).isoformat()
        )
        
        if db.insert_news(news_item):
            saved_news.append(news_item)

    # Mark raw items as processed
    db.mark_raw_items_processed(processed_urls)

    duration = round(time.time() - start_time, 2)
    sources_count = len(get_default_collectors())
    
    # 3. Update System Status
    db.update_system_status(
        sources_checked=sources_count,
        new_opps_today=len(saved_opps),
        duration_sec=duration
    )
    
    # 4. Push to Cloudflare D1 if configured (e.g. during GitHub Actions run)
    sync_client = D1SyncClient()
    if sync_client.is_configured:
        status_model = SystemStatus(
            status="ACTIVE",
            sources_checked=sources_count,
            new_opportunities_today=len(saved_opps),
            last_run_duration_sec=duration
        )
        sync_client.sync_batch(saved_news, saved_opps, status=status_model)

    logger.info(f"✨ Pipeline Complete in {duration}s! Processed {len(saved_news)} news items, {len(saved_opps)} opportunities.")
    return saved_news, saved_opps

def run_nightly_report(db: Database, notify: bool = False):
    """Stage 3: Synthesize Nightly Intelligence Digest from persisted database data."""
    logger.info("🌙 Generating Nightly Daily Intelligence Digest...")
    recent_news = db.get_recent_news(limit=25)
    active_opps = db.get_opportunities(limit=15)

    ai_provider = get_ai_provider(settings.AI_PROVIDER)
    generator = DailyDigestGenerator(ai_provider)
    
    report = generator.generate(recent_news, active_opps)
    db.insert_report(report)
    logger.info(f"📰 Nightly Report Created & Persisted: {report.headline} (Date: {report.date})")

    # Push report to Cloudflare D1 if configured
    sync_client = D1SyncClient()
    if sync_client.is_configured:
        sync_client.sync_batch([], [], report=report)

    if notify:
        notifier = TelegramNotifier()
        notifier.send_daily_digest(report)

def main():
    parser = argparse.ArgumentParser(description="Tech Sentinel Agent Engine")
    parser.add_argument("command", choices=["collect", "process", "report", "notify", "run-all", "telegram"], help="Command to execute")
    parser.add_argument("action", nargs="?", default="test", help="Action for telegram command (test, info, poll)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate run without writing to database")
    args = parser.parse_args()

    db = Database()

    if args.command == "collect":
        total, staged = run_collection(db)
        print(f"Collection finished: {total} items collected, {staged} items staged.")
    elif args.command == "process":
        news, opps = run_processing(db)
        print(f"Processing finished: {len(news)} news items, {len(opps)} opportunities processed.")
    elif args.command == "report":
        run_nightly_report(db, notify=False)
        print("Nightly report generated and persisted to database.")
    elif args.command == "notify":
        latest = db.get_latest_report()
        if latest:
            notifier = TelegramNotifier()
            notifier.send_daily_digest(DailyReport(**latest))
            print("Dispatched nightly digest to Telegram.")
        else:
            print("No report found in database.")
    elif args.command == "run-all":
        run_collection(db)
        run_processing(db)
        run_nightly_report(db, notify=True)
        print("End-to-end cycle completed successfully.")
    elif args.command == "telegram":
        from .telegram.service import TelegramBotService
        bot = TelegramBotService()
        if not bot.is_configured:
            print("❌ TELEGRAM_BOT_TOKEN is not configured in environment or .env file.")
            sys.exit(1)

        if args.action == "info":
            info = bot.get_bot_info()
            if info:
                print(f"✅ Telegram Bot Connected: @{info.get('username')} ({info.get('first_name')}) [ID: {info.get('id')}]")
            else:
                print("❌ Failed to connect to Telegram Bot API. Verify your TELEGRAM_BOT_TOKEN.")
        elif args.action == "test":
            success = bot.send_test_message()
            if success:
                print("✅ Test message dispatched successfully to Telegram.")
            else:
                print("❌ Test message dispatch failed. Ensure TELEGRAM_CHAT_ID is set or pass target.")
        elif args.action == "digest":
            from .telegram.digest import run_telegram_digest
            res = run_telegram_digest()
            print(f"✅ Telegram Digest Dispatch: {res.get('dispatched', 0)} delivered, {res.get('failed', 0)} failed.")
        elif args.action == "poll":
            print("🤖 Starting Telegram Bot polling (listening for /start)... Press Ctrl+C to stop.")
            offset = None
            try:
                while True:
                    _, offset = bot.process_updates(offset)
                    time.sleep(2)
            except KeyboardInterrupt:
                print("\n🛑 Telegram Bot polling stopped.")

if __name__ == "__main__":
    main()

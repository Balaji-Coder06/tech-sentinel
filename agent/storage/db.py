import sqlite3
import json
import logging
import hashlib
import email.utils
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from ..config import settings
from ..models import RawItem, NewsItem, Opportunity, DailyReport, UserPreferences, SystemStatus
from ..utils.validator import is_valid_title
from ..utils.taxonomy import normalize_category

logger = logging.getLogger(__name__)

def normalize_iso_date(date_str: Optional[str]) -> str:
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    date_str = str(date_str).strip()
    if 'T' in date_str and (date_str.endswith('Z') or '+' in date_str):
        return date_str
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        schema_path = settings.BASE_DIR / "database" / "schema.sql"
        seed_path = settings.BASE_DIR / "database" / "seed.sql"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Clean up any pre-existing duplicates in legacy tables before enforcing unique indexes
            try:
                cursor.execute("""
                DELETE FROM opportunities WHERE rowid NOT IN (
                    SELECT MIN(rowid) FROM opportunities GROUP BY claim_url
                );
                """)
            except Exception:
                pass

            try:
                cursor.execute("""
                DELETE FROM news WHERE rowid NOT IN (
                    SELECT MIN(rowid) FROM news GROUP BY url
                );
                """)
            except Exception:
                pass

            # 2. Execute full schema if available
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

            # 3. Explicit migrations for existing SQLite databases
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                content TEXT,
                url TEXT NOT NULL UNIQUE,
                source_id TEXT NOT NULL,
                source_name TEXT NOT NULL,
                category TEXT,
                image_url TEXT,
                raw_metadata TEXT,
                published_at TEXT,
                discovered_at TEXT DEFAULT (datetime('now')),
                processed INTEGER NOT NULL DEFAULT 0
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_status (
                id TEXT PRIMARY KEY DEFAULT 'current',
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                last_scan_time TEXT DEFAULT (datetime('now')),
                sources_checked INTEGER DEFAULT 9,
                new_opportunities_today INTEGER DEFAULT 0,
                next_report_time TEXT DEFAULT '8:00 AM IST',
                last_run_duration_sec REAL DEFAULT 0.0,
                last_error TEXT,
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_users (
                user_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                preference_id TEXT NOT NULL DEFAULT 'default',
                telegram_digest_enabled INTEGER DEFAULT 0,
                last_digest_sent_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(preference_id) REFERENCES preferences(id)
            )
            """)

            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_opps_claim_url ON opportunities(claim_url);")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url ON news(url);")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_items_url ON raw_items(url);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telegram_users_chat_id ON telegram_users(chat_id);")

            try:
                cursor.execute("ALTER TABLE telegram_users ADD COLUMN telegram_digest_enabled INTEGER DEFAULT 0;")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE telegram_users ADD COLUMN last_digest_sent_at TEXT;")
            except Exception:
                pass

            # 4. Auto-migrate legacy dates to standardized ISO 8601 UTC strings
            try:
                rows = cursor.execute("SELECT id, published_at FROM news").fetchall()
                for r_id, pub in rows:
                    if pub and any(pub.startswith(prefix) for prefix in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                        try:
                            dt = email.utils.parsedate_to_datetime(pub)
                            iso = dt.astimezone(timezone.utc).isoformat()
                            cursor.execute("UPDATE news SET published_at = ? WHERE id = ?", (iso, r_id))
                        except Exception:
                            pass
            except Exception:
                pass

            # 5. Clean up any corrupted records containing unrendered template expressions
            try:
                cursor.execute("DELETE FROM news WHERE title LIKE '%{{%' OR title LIKE '%${%' OR title LIKE '%$(%';")
                cursor.execute("DELETE FROM raw_items WHERE title LIKE '%{{%' OR title LIKE '%${%' OR title LIKE '%$(%';")
            except Exception:
                pass

            # 6. Normalize legacy categories to canonical lowercase taxonomy slugs
            canonical_migrations = [
                ("ai", ["AI", "Artificial Intelligence", "artificial-intelligence", "machine_learning", "machine-learning", "ML", "deep_learning", "genai"]),
                ("cloud", ["Cloud", "Cloud Computing", "cloud-computing", "cloud_infrastructure", "DevOps", "devops", "serverless", "infrastructure"]),
                ("development", ["Development", "Software Development", "software-development", "Software Dev", "Programming", "coding", "webdev", "fullstack"]),
                ("open_source", ["Open Source", "open-source", "opensource", "OSS", "FOSS"]),
                ("cybersecurity", ["Cybersecurity", "Cyber Security", "cyber-security", "Security", "infosec"]),
                ("startups", ["Startup", "Startups", "start-up", "start_up", "venture"]),
                ("education", ["Education", "learning", "student", "students", "tutorials"])
            ]
            for canon, variants in canonical_migrations:
                try:
                    placeholders = ",".join("?" for _ in variants)
                    cursor.execute(f"UPDATE news SET category = ? WHERE category IN ({placeholders})", (canon, *variants))
                    cursor.execute(f"UPDATE raw_items SET category = ? WHERE category IN ({placeholders})", (canon, *variants))
                except Exception:
                    pass

            # 7. Idempotently migrate preferences table to remove legacy ai_provider column
            try:
                pref_table = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='preferences'").fetchone()
                if pref_table:
                    columns_info = cursor.execute("PRAGMA table_info(preferences)").fetchall()
                    column_names = [col[1] for col in columns_info]
                    if "ai_provider" in column_names:
                        sqlite_ver = sqlite3.sqlite_version_info
                        if sqlite_ver >= (3, 35, 0):
                            cursor.execute("ALTER TABLE preferences DROP COLUMN ai_provider;")
                            logger.info("Successfully dropped legacy ai_provider column from preferences table.")
                        else:
                            cursor.execute("""
                            CREATE TABLE preferences_new (
                                id TEXT PRIMARY KEY DEFAULT 'default',
                                user_name TEXT DEFAULT 'Balaji',
                                theme TEXT DEFAULT 'system',
                                categories TEXT DEFAULT '["ai", "cloud", "development", "open_source", "cybersecurity", "startups"]',
                                keywords TEXT DEFAULT '["react", "llm", "credits", "internship", "certification", "hackathon", "copilot"]',
                                opportunity_types TEXT DEFAULT '["software", "ai_credits", "cloud", "education", "certification", "competition", "career"]',
                                enable_daily_brief INTEGER DEFAULT 1,
                                enable_critical_alerts INTEGER DEFAULT 1,
                                telegram_chat_id TEXT,
                                updated_at TEXT DEFAULT (datetime('now'))
                            );
                            """)
                            cursor.execute("""
                            INSERT INTO preferences_new (id, user_name, theme, categories, keywords, opportunity_types, enable_daily_brief, enable_critical_alerts, telegram_chat_id, updated_at)
                            SELECT id, user_name, theme, categories, keywords, opportunity_types, enable_daily_brief, enable_critical_alerts, telegram_chat_id, updated_at
                            FROM preferences;
                            """)
                            cursor.execute("DROP TABLE preferences;")
                            cursor.execute("ALTER TABLE preferences_new RENAME TO preferences;")
                            logger.info("Successfully migrated preferences table without ai_provider.")
            except Exception as e:
                logger.warning(f"Note during preferences migration: {e}")

            # 8. Idempotently ensure email newsletter columns exist in preferences table
            try:
                cursor.execute("ALTER TABLE preferences ADD COLUMN email_newsletter_enabled INTEGER DEFAULT 0;")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE preferences ADD COLUMN newsletter_email TEXT;")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE preferences ADD COLUMN last_email_sent_at TEXT;")
            except Exception:
                pass

            # 9. Idempotently ensure delivery_logs table exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS delivery_logs (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                report_date TEXT NOT NULL,
                channel TEXT NOT NULL CHECK(channel IN ('telegram', 'email')),
                recipient_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('DELIVERED', 'FAILED')),
                delivered_at TEXT NOT NULL DEFAULT (datetime('now')),
                metadata TEXT,
                UNIQUE(report_date, channel, recipient_id)
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_delivery_logs_lookup ON delivery_logs(report_date, channel, recipient_id, status);")

            # Check if news table is empty -> seed
            cursor.execute("SELECT COUNT(*) FROM news")
            count = cursor.fetchone()[0]
            if count == 0 and seed_path.exists():
                with open(seed_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
                logger.info("Initialized database with seed data.")

    init_db = init_schema

    # -------------------------------------------------------------
    # Raw Items Staging Operations (Decouples Collect & Process)
    # -------------------------------------------------------------
    def insert_raw_items(self, items: List[RawItem]) -> int:
        query = """
        INSERT INTO raw_items (
            id, title, description, content, url, source_id, source_name,
            category, image_url, raw_metadata, published_at, discovered_at, processed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            description=excluded.description,
            content=excluded.content,
            image_url=COALESCE(excluded.image_url, raw_items.image_url),
            published_at=COALESCE(excluded.published_at, raw_items.published_at)
        """
        inserted_count = 0
        now_iso = datetime.now(timezone.utc).isoformat()

        with self.get_connection() as conn:
            for item in items:
                if not is_valid_title(item.title):
                    logger.warning(f"Dropping raw item with invalid/template title: '{item.title}' from {item.source_name}")
                    continue
                try:
                    url_hash = hashlib.sha256(item.url.strip().lower().encode('utf-8')).hexdigest()[:12]
                    raw_id = f"raw_{url_hash}"
                    meta_json = json.dumps(item.raw_metadata or {})
                    pub_iso = normalize_iso_date(item.published_at)
                    normalized_cat = normalize_category(item.category)
                    conn.execute(query, (
                        raw_id, item.title, item.description or "", item.content or "",
                        item.url, item.source_id, item.source_name, normalized_cat,
                        item.image_url, meta_json, pub_iso, now_iso
                    ))
                    inserted_count += 1
                except Exception as e:
                    logger.debug(f"Skipped duplicate/error raw item {item.url}: {e}")
        return inserted_count

    def get_unprocessed_raw_items(self, limit: int = 300) -> List[RawItem]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM raw_items WHERE processed = 0 ORDER BY discovered_at ASC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            items: List[RawItem] = []
            for r in rows:
                meta = {}
                if r["raw_metadata"]:
                    try:
                        meta = json.loads(r["raw_metadata"])
                    except Exception:
                        pass
                items.append(RawItem(
                    title=r["title"],
                    description=r["description"],
                    content=r["content"],
                    url=r["url"],
                    source_id=r["source_id"],
                    source_name=r["source_name"],
                    category=r["category"],
                    published_at=r["published_at"],
                    image_url=r["image_url"],
                    raw_metadata=meta
                ))
            return items

    def mark_raw_items_processed(self, urls: List[str]):
        if not urls:
            return
        with self.get_connection() as conn:
            placeholders = ",".join("?" for _ in urls)
            conn.execute(f"UPDATE raw_items SET processed = 1 WHERE url IN ({placeholders})", tuple(urls))

    def get_unprocessed_raw_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_items WHERE processed = 0")
            return cursor.fetchone()[0]

    # -------------------------------------------------------------
    # News Operations
    # -------------------------------------------------------------
    def insert_news(self, item: NewsItem) -> bool:
        if not is_valid_title(item.title):
            logger.warning(f"Refusing to insert news item {item.id} with invalid/template title: '{item.title}'")
            return False

        query = """
        INSERT INTO news (
            id, title, description, content, url, canonical_url, image_url,
            source_id, source_name, category, tags, read_time_minutes,
            summary_what, summary_why, summary_action, key_points,
            importance_score, relevance_score, is_featured, is_trending,
            published_at, discovered_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            id=excluded.id,
            title=excluded.title,
            description=excluded.description,
            content=excluded.content,
            image_url=COALESCE(excluded.image_url, news.image_url),
            summary_what=excluded.summary_what,
            summary_why=excluded.summary_why,
            summary_action=excluded.summary_action,
            key_points=excluded.key_points,
            importance_score=excluded.importance_score,
            relevance_score=excluded.relevance_score,
            is_featured=excluded.is_featured,
            is_trending=excluded.is_trending,
            published_at=excluded.published_at,
            discovered_at=excluded.discovered_at
        """
        summary_what = item.summary.what if item.summary else None
        summary_why = item.summary.why if item.summary else None
        summary_action = item.summary.action if item.summary else None
        key_points = json.dumps(item.summary.key_points) if item.summary else "[]"
        tags = json.dumps(item.tags)
        pub_iso = normalize_iso_date(item.published_at)
        disc_iso = normalize_iso_date(item.discovered_at)

        with self.get_connection() as conn:
            try:
                normalized_cat = normalize_category(item.category)
                conn.execute(query, (
                    item.id, item.title, item.description, item.content, item.url,
                    item.canonical_url, item.image_url, item.source_id, item.source_name,
                    normalized_cat, tags, item.read_time_minutes,
                    summary_what, summary_why, summary_action, key_points,
                    item.importance_score, item.relevance_score,
                    1 if item.is_featured else 0, 1 if item.is_trending else 0,
                    pub_iso, disc_iso
                ))
                return True
            except Exception as e:
                logger.error(f"Error inserting news item {item.id}: {e}")
                return False

    def get_recent_news(self, limit: int = 50, category: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if category and category.lower() != 'all':
                cursor.execute(
                    "SELECT * FROM news WHERE category = ? ORDER BY published_at DESC LIMIT ?",
                    (category.lower(), limit)
                )
            else:
                cursor.execute("SELECT * FROM news ORDER BY published_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                d = dict(row)
                if isinstance(d.get("tags"), str):
                    try:
                        d["tags"] = json.loads(d["tags"])
                    except Exception:
                        d["tags"] = []
                if isinstance(d.get("key_points"), str):
                    try:
                        d["key_points"] = json.loads(d["key_points"])
                    except Exception:
                        d["key_points"] = []
                results.append(d)
            return results

    # -------------------------------------------------------------
    # Opportunities Operations
    # -------------------------------------------------------------
    def insert_opportunity(self, opp: Opportunity) -> bool:
        query = """
        INSERT INTO opportunities (
            id, title, provider, provider_logo, description, opportunity_type, category,
            normal_value, current_value, eligibility, claim_url, official_url,
            requirements, coupon_code, start_date, expiry_date, is_expiring_soon,
            status, verification_status, last_verified_at, verification_notes,
            importance_score, relevance_score, priority, why_care, discovered_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(claim_url) DO UPDATE SET
            id=excluded.id,
            title=excluded.title,
            provider=excluded.provider,
            provider_logo=COALESCE(excluded.provider_logo, opportunities.provider_logo),
            description=excluded.description,
            opportunity_type=excluded.opportunity_type,
            category=excluded.category,
            normal_value=excluded.normal_value,
            current_value=excluded.current_value,
            eligibility=excluded.eligibility,
            official_url=excluded.official_url,
            requirements=excluded.requirements,
            coupon_code=excluded.coupon_code,
            start_date=excluded.start_date,
            expiry_date=excluded.expiry_date,
            is_expiring_soon=excluded.is_expiring_soon,
            status=excluded.status,
            verification_status=excluded.verification_status,
            last_verified_at=excluded.last_verified_at,
            verification_notes=excluded.verification_notes,
            importance_score=excluded.importance_score,
            relevance_score=excluded.relevance_score,
            priority=excluded.priority,
            why_care=excluded.why_care,
            discovered_at=excluded.discovered_at
        """
        with self.get_connection() as conn:
            try:
                conn.execute(query, (
                    opp.id, opp.title, opp.provider, opp.provider_logo, opp.description,
                    opp.opportunity_type, opp.category, opp.normal_value, opp.current_value,
                    opp.eligibility, opp.claim_url, opp.official_url, opp.requirements,
                    opp.coupon_code, opp.start_date, opp.expiry_date,
                    1 if opp.is_expiring_soon else 0, opp.status, opp.verification_status,
                    opp.last_verified_at, opp.verification_notes, opp.importance_score,
                    opp.relevance_score, opp.priority, opp.why_care, opp.discovered_at
                ))
                return True
            except Exception as e:
                logger.error(f"Error inserting opportunity {opp.id}: {e}")
                return False

    def get_opportunities(self, limit: int = 50, opp_type: Optional[str] = None, status: Optional[str] = 'ACTIVE') -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM opportunities WHERE 1=1"
            params: List[Any] = []
            
            if status and status != 'ALL':
                query += " AND status = ?"
                params.append(status)
            if opp_type and opp_type != 'all':
                query += " AND (opportunity_type = ? OR category = ?)"
                params.extend([opp_type, opp_type])
                
            query += " ORDER BY importance_score DESC, is_expiring_soon DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------
    # Reports Operations
    # -------------------------------------------------------------
    def insert_report(self, report: DailyReport) -> bool:
        query = """
        INSERT INTO daily_reports (
            id, date, title, headline, thirty_sec_summary,
            top_stories, free_opportunities, student_opportunities,
            open_source_highlights, expiring_soon, sentinel_take,
            stats_json, published_at, telegram_message_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            id=excluded.id,
            title=excluded.title,
            headline=excluded.headline,
            thirty_sec_summary=excluded.thirty_sec_summary,
            top_stories=excluded.top_stories,
            free_opportunities=excluded.free_opportunities,
            student_opportunities=excluded.student_opportunities,
            open_source_highlights=excluded.open_source_highlights,
            expiring_soon=excluded.expiring_soon,
            sentinel_take=excluded.sentinel_take,
            stats_json=excluded.stats_json,
            published_at=excluded.published_at
        """
        with self.get_connection() as conn:
            try:
                conn.execute(query, (
                    report.id, report.date, report.title, report.headline, report.thirty_sec_summary,
                    json.dumps(report.top_stories), json.dumps(report.free_opportunities),
                    json.dumps(report.student_opportunities), json.dumps(report.open_source_highlights),
                    json.dumps(report.expiring_soon), report.sentinel_take,
                    json.dumps(report.stats), report.published_at, report.telegram_message_id
                ))
                return True
            except Exception as e:
                logger.error(f"Error inserting daily report {report.id}: {e}")
                return False

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_reports ORDER BY date DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return None
            return self._parse_report_row(dict(row))

    def get_report_by_date(self, date_str: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_reports WHERE date = ? LIMIT 1", (date_str,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._parse_report_row(dict(row))

    def get_all_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_reports ORDER BY date DESC LIMIT ?", (limit,))
            return [self._parse_report_row(dict(row)) for row in cursor.fetchall()]

    def _parse_report_row(self, d: Dict[str, Any]) -> Dict[str, Any]:
        json_fields = ["top_stories", "free_opportunities", "student_opportunities", "open_source_highlights", "expiring_soon", "stats_json"]
        for field in json_fields:
            if isinstance(d.get(field), str):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    d[field] = [] if field != "stats_json" else {}
        return d

    # -------------------------------------------------------------
    # Preferences
    # -------------------------------------------------------------
    def get_preferences(self, preference_id: str = "default") -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM preferences WHERE id = ?", (preference_id,))
            row = cursor.fetchone()

            if not row and preference_id != "default":
                cursor.execute("SELECT * FROM preferences WHERE id = 'default'")
                row = cursor.fetchone()

            if not row:
                return {
                    "id": preference_id,
                    "user_name": "Balaji",
                    "theme": "system",
                    "categories": ["ai", "cloud", "development", "open_source", "cybersecurity", "startups"],
                    "keywords": ["react", "llm", "credits", "internship", "certification", "hackathon", "copilot"],
                    "opportunity_types": ["software", "ai_credits", "cloud", "education", "certification", "competition", "career"],
                    "enable_daily_brief": True,
                    "enable_critical_alerts": True,
                    "email_newsletter_enabled": False,
                    "newsletter_email": None
                }

            preferences = dict(row)
            # Remove legacy field if present in SQLite row dict
            preferences.pop("ai_provider", None)
            preferences["email_newsletter_enabled"] = bool(preferences.get("email_newsletter_enabled", 0))
            for field in ["categories", "keywords", "opportunity_types"]:
                if isinstance(preferences.get(field), str):
                    try:
                        preferences[field] = json.loads(preferences[field])
                    except Exception:
                        preferences[field] = []

            return preferences

    def update_preferences(self, prefs: Dict[str, Any], preference_id: Optional[str] = None) -> bool:
        target_id = preference_id or prefs.get("id", "default")
        query = """
        INSERT INTO preferences (
            id, user_name, theme, categories, keywords, opportunity_types,
            enable_daily_brief, enable_critical_alerts, email_newsletter_enabled, newsletter_email, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
            user_name=excluded.user_name,
            theme=excluded.theme,
            categories=excluded.categories,
            keywords=excluded.keywords,
            opportunity_types=excluded.opportunity_types,
            enable_daily_brief=excluded.enable_daily_brief,
            enable_critical_alerts=excluded.enable_critical_alerts,
            email_newsletter_enabled=excluded.email_newsletter_enabled,
            newsletter_email=excluded.newsletter_email,
            updated_at=datetime('now')
        """
        categories = json.dumps(prefs.get("categories", []))
        keywords = json.dumps(prefs.get("keywords", []))
        opportunity_types = json.dumps(prefs.get("opportunity_types", []))

        with self.get_connection() as conn:
            try:
                conn.execute(query, (
                    target_id,
                    prefs.get("user_name", "Balaji"),
                    prefs.get("theme", "system"),
                    categories, keywords, opportunity_types,
                    1 if prefs.get("enable_daily_brief", True) else 0,
                    1 if prefs.get("enable_critical_alerts", True) else 0,
                    1 if prefs.get("email_newsletter_enabled", False) else 0,
                    prefs.get("newsletter_email") or None
                ))
                return True
            except Exception as e:
                logger.error(f"Error updating preferences for {target_id}: {e}")
                return False

    def get_email_subscribers(self) -> List[Dict[str, Any]]:
        """Returns all user preference records with email newsletter explicitly opted in."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM preferences 
            WHERE email_newsletter_enabled = 1 
              AND newsletter_email IS NOT NULL 
              AND TRIM(newsletter_email) != ''
            """)
            rows = cursor.fetchall()
            subscribers = []
            for r in rows:
                p = dict(r)
                p.pop("ai_provider", None)
                p["email_newsletter_enabled"] = True
                for field in ["categories", "keywords", "opportunity_types"]:
                    if isinstance(p.get(field), str):
                        try:
                            p[field] = json.loads(p[field])
                        except Exception:
                            p[field] = []
                subscribers.append(p)
            return subscribers

    def record_email_sent(self, email: str):
        """Records last newsletter dispatch timestamp for the recipient."""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    "UPDATE preferences SET last_email_sent_at = datetime('now') WHERE newsletter_email = ?",
                    (email.strip(),)
                )
            except Exception:
                pass

    def get_all_preferences(self) -> List[Dict[str, Any]]:
        """Returns all stored preferences profiles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM preferences")
            rows = cursor.fetchall()
            prefs_list = []
            for r in rows:
                p = dict(r)
                p.pop("ai_provider", None)
                p["email_newsletter_enabled"] = bool(p.get("email_newsletter_enabled", 0))
                for field in ["categories", "keywords", "opportunity_types"]:
                    if isinstance(p.get(field), str):
                        try:
                            p[field] = json.loads(p[field])
                        except Exception:
                            p[field] = []
                prefs_list.append(p)
            return prefs_list

    # -------------------------------------------------------------
    # Telegram User Registration & Preferences
    # -------------------------------------------------------------
    def upsert_telegram_user(
        self,
        user_id: str,
        chat_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        user_id_str = str(user_id).strip()
        chat_id_str = str(chat_id).strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        query = """
        INSERT INTO telegram_users (
            user_id, chat_id, username, first_name, last_name, preference_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'default', ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            chat_id=excluded.chat_id,
            username=COALESCE(excluded.username, telegram_users.username),
            first_name=COALESCE(excluded.first_name, telegram_users.first_name),
            last_name=COALESCE(excluded.last_name, telegram_users.last_name),
            updated_at=excluded.updated_at
        """
        with self.get_connection() as conn:
            conn.execute(query, (user_id_str, chat_id_str, username, first_name, last_name, now_iso, now_iso))

        user = self.get_telegram_user(user_id_str)
        return user or {
            "user_id": user_id_str,
            "chat_id": chat_id_str,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "preference_id": "default"
        }

    def get_telegram_user(self, user_id_or_chat_id: str) -> Optional[Dict[str, Any]]:
        val = str(user_id_or_chat_id).strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telegram_users WHERE user_id = ? OR chat_id = ? LIMIT 1", (val, val))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_telegram_user_preferences(self, user_id_or_chat_id: str) -> Dict[str, Any]:
        user = self.get_telegram_user(user_id_or_chat_id)
        pref_id = user.get("preference_id", "default") if user else "default"
        return self.get_preferences(preference_id=pref_id)

    def update_telegram_user_preferences(self, user_id_or_chat_id: str, prefs: Dict[str, Any]) -> bool:
        user = self.get_telegram_user(user_id_or_chat_id)
        user_id = user.get("user_id") if user else str(user_id_or_chat_id).strip()
        user_pref_id = f"tg_{user_id}"

        # 1. Update preferences table with tg_user_id
        prefs_copy = dict(prefs)
        prefs_copy["id"] = user_pref_id
        if "user_name" not in prefs_copy and user:
            prefs_copy["user_name"] = user.get("first_name") or user.get("username") or "Telegram User"
        self.update_preferences(prefs_copy, preference_id=user_pref_id)

        # 2. Link telegram_users table to user_pref_id
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE telegram_users SET preference_id = ?, updated_at = datetime('now') WHERE user_id = ? OR chat_id = ?",
                (user_pref_id, str(user_id_or_chat_id), str(user_id_or_chat_id))
            )
        return True

    def get_all_telegram_users(self) -> List[Dict[str, Any]]:
        """Retrieves all registered Telegram users from SQLite."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telegram_users ORDER BY created_at ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_all_preferences(self) -> List[Dict[str, Any]]:
        """Retrieves all preference profiles from SQLite."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM preferences")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                p = dict(row)
                for field in ["categories", "keywords", "opportunity_types"]:
                    if isinstance(p.get(field), str):
                        try:
                            p[field] = json.loads(p[field])
                        except Exception:
                            p[field] = []
                results.append(p)
            return results

    def set_telegram_digest_subscription(self, user_id_or_chat_id: str, enabled: bool) -> bool:
        """Enables or disables scheduled Telegram digest for a user."""
        val = str(user_id_or_chat_id).strip()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE telegram_users SET telegram_digest_enabled = ?, updated_at = datetime('now') WHERE user_id = ? OR chat_id = ?",
                (1 if enabled else 0, val, val)
            )
        return True

    def get_subscribed_telegram_users(self) -> List[Dict[str, Any]]:
        """Retrieves only Telegram users who have explicitly enabled daily digests."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telegram_users WHERE telegram_digest_enabled = 1 ORDER BY created_at ASC")
            return [dict(row) for row in cursor.fetchall()]

    def record_telegram_digest_sent(self, user_id_or_chat_id: str) -> None:
        """Records the timestamp when a digest was successfully sent to a user."""
        val = str(user_id_or_chat_id).strip()
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE telegram_users SET last_digest_sent_at = ?, updated_at = datetime('now') WHERE user_id = ? OR chat_id = ?",
                (now_iso, val, val)
            )

    # -------------------------------------------------------------
    # System Status Operations
    # -------------------------------------------------------------
    def update_system_status(
        self,
        sources_checked: int,
        new_opps_today: int,
        duration_sec: float = 0.0,
        last_error: Optional[str] = None
    ) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        query = """
        INSERT INTO system_status (
            id, status, last_scan_time, sources_checked, new_opportunities_today,
            next_report_time, last_run_duration_sec, last_error, updated_at
        ) VALUES ('current', 'ACTIVE', ?, ?, ?, '8:00 AM IST', ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status='ACTIVE',
            last_scan_time=excluded.last_scan_time,
            sources_checked=excluded.sources_checked,
            new_opportunities_today=excluded.new_opportunities_today,
            last_run_duration_sec=excluded.last_run_duration_sec,
            last_error=excluded.last_error,
            updated_at=excluded.updated_at
        """
        with self.get_connection() as conn:
            try:
                conn.execute(query, (now_iso, sources_checked, new_opps_today, duration_sec, last_error, now_iso))
                return True
            except Exception as e:
                logger.error(f"Error updating system status: {e}")
                return False

    def get_system_status(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_status WHERE id = 'current'")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {
                "id": "current",
                "status": "ACTIVE",
                "last_scan_time": datetime.now(timezone.utc).isoformat(),
                "sources_checked": 9,
                "new_opportunities_today": 6,
                "next_report_time": "8:00 AM IST",
                "system_cost": "₹0.00"
            }

    # -------------------------------------------------------------
    # Multi-Channel Delivery Logs & Idempotency Tracking
    # -------------------------------------------------------------
    def is_report_delivered(self, report_date: str, channel: str, recipient_id: str) -> bool:
        """
        Checks whether a specific report/date was already successfully delivered
        to a recipient on a specific channel.
        """
        date_str = str(report_date).strip()
        chan_str = str(channel).strip().lower()
        recip_str = str(recipient_id).strip().lower()
        if not (date_str and chan_str and recip_str):
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM delivery_logs WHERE report_date = ? AND channel = ? AND recipient_id = ? AND status = 'DELIVERED' LIMIT 1",
                (date_str, chan_str, recip_str)
            )
            return cursor.fetchone() is not None

    def record_delivery(
        self,
        report_id: str,
        report_date: str,
        channel: str,
        recipient_id: str,
        status: str = "DELIVERED",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Persists an idempotent delivery attempt record (DELIVERED or FAILED).
        Only DELIVERED prevents future duplicate sends.
        """
        date_str = str(report_date).strip()
        chan_str = str(channel).strip().lower()
        recip_str = str(recipient_id).strip().lower()
        rep_id = str(report_id).strip()
        stat_str = str(status).strip().upper()
        meta_json = json.dumps(metadata or {})
        log_id = f"{date_str}:{chan_str}:{hashlib.sha256(recip_str.encode('utf-8')).hexdigest()[:12]}"

        query = """
        INSERT INTO delivery_logs (
            id, report_id, report_date, channel, recipient_id, status, delivered_at, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
        ON CONFLICT(report_date, channel, recipient_id) DO UPDATE SET
            status=excluded.status,
            delivered_at=datetime('now'),
            metadata=excluded.metadata
        """
        with self.get_connection() as conn:
            try:
                conn.execute(query, (log_id, rep_id, date_str, chan_str, recip_str, stat_str, meta_json))
                return True
            except Exception as e:
                logger.error(f"Error recording delivery log: {e}")
                return False

    def get_delivery_logs(
        self,
        report_date: Optional[str] = None,
        channel: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves delivery records filtered by date and/or channel."""
        query = "SELECT * FROM delivery_logs WHERE 1=1"
        params: List[Any] = []
        if report_date:
            query += " AND report_date = ?"
            params.append(report_date.strip())
        if channel:
            query += " AND channel = ?"
            params.append(channel.strip().lower())
        query += " ORDER BY delivered_at DESC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                d = dict(row)
                if isinstance(d.get("metadata"), str):
                    try:
                        d["metadata"] = json.loads(d["metadata"])
                    except Exception:
                        pass
                results.append(d)
            return results

-- Tech Sentinel Database Schema
-- Compatible with Cloudflare D1 and SQLite

-- 0. Staging Table for Raw Collected Items (Decouples 'collect' from 'process')
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
    raw_metadata TEXT, -- JSON
    published_at TEXT,
    discovered_at TEXT DEFAULT (datetime('now')),
    processed INTEGER NOT NULL DEFAULT 0
);

-- 1. Sources Table
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ('rss', 'api', 'github', 'official', 'scraper')),
    category TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_fetched_at TEXT,
    last_status TEXT DEFAULT 'ok',
    error_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    icon TEXT,
    description TEXT,
    is_default INTEGER DEFAULT 1
);

-- 3. News Items Table
CREATE TABLE IF NOT EXISTS news (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT NOT NULL UNIQUE,
    canonical_url TEXT,
    image_url TEXT,
    source_id TEXT,
    source_name TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT, -- JSON array of strings
    read_time_minutes INTEGER DEFAULT 3,
    
    -- AI Generated Insights
    summary_what TEXT,
    summary_why TEXT,
    summary_action TEXT,
    key_points TEXT, -- JSON array of strings
    
    importance_score INTEGER DEFAULT 50 CHECK(importance_score BETWEEN 0 AND 100),
    relevance_score INTEGER DEFAULT 50 CHECK(relevance_score BETWEEN 0 AND 100),
    is_featured INTEGER DEFAULT 0,
    is_trending INTEGER DEFAULT 0,
    
    published_at TEXT NOT NULL,
    discovered_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE SET NULL
);

-- 4. Opportunities Table (The Core Differentiator: Free Before It's Gone)
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_logo TEXT,
    description TEXT NOT NULL,
    opportunity_type TEXT NOT NULL CHECK(opportunity_type IN ('software', 'ai_credits', 'cloud', 'education', 'certification', 'competition', 'career', 'resource')),
    category TEXT NOT NULL,
    
    -- Monetary & Access Details
    normal_value TEXT, -- e.g., "$100", "₹1,500/mo"
    current_value TEXT NOT NULL DEFAULT 'FREE', -- e.g., "FREE", "100% OFF"
    eligibility TEXT DEFAULT 'All Developers', -- e.g., "Students", "Early Access", "Global"
    claim_url TEXT NOT NULL,
    official_url TEXT,
    requirements TEXT,
    coupon_code TEXT,
    
    -- Expiry & Lifecycle
    start_date TEXT,
    expiry_date TEXT, -- ISO string or null for ongoing
    is_expiring_soon INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'EXPIRING_SOON', 'EXPIRED')),
    
    -- Verification
    verification_status TEXT NOT NULL DEFAULT 'VERIFIED' CHECK(verification_status IN ('VERIFIED', 'NEEDS_VERIFICATION', 'EXPIRED')),
    last_verified_at TEXT,
    verification_notes TEXT,
    
    -- Scoring & AI
    importance_score INTEGER DEFAULT 80 CHECK(importance_score BETWEEN 0 AND 100),
    relevance_score INTEGER DEFAULT 80 CHECK(relevance_score BETWEEN 0 AND 100),
    priority TEXT DEFAULT 'High' CHECK(priority IN ('Critical', 'High', 'Medium', 'Low')),
    why_care TEXT,
    
    discovered_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now'))
);

-- 5. Daily Reports Table
CREATE TABLE IF NOT EXISTS daily_reports (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE, -- YYYY-MM-DD
    title TEXT NOT NULL,
    headline TEXT NOT NULL,
    thirty_sec_summary TEXT NOT NULL,
    top_stories TEXT NOT NULL, -- JSON array of NewsItem summaries
    free_opportunities TEXT NOT NULL, -- JSON array of Opportunity summaries
    student_opportunities TEXT, -- JSON array
    open_source_highlights TEXT, -- JSON array
    expiring_soon TEXT, -- JSON array
    sentinel_take TEXT NOT NULL,
    stats_json TEXT, -- JSON: {total_scanned, new_news, new_opps}
    published_at TEXT DEFAULT (datetime('now')),
    telegram_message_id TEXT
);

-- 6. User Preferences Table (Persistent)
CREATE TABLE IF NOT EXISTS preferences (
    id TEXT PRIMARY KEY DEFAULT 'default',
    user_name TEXT DEFAULT 'Balaji',
    theme TEXT DEFAULT 'system',
    categories TEXT DEFAULT '["ai", "cloud", "development", "open_source", "cybersecurity", "startups"]',
    keywords TEXT DEFAULT '["react", "llm", "credits", "internship", "certification", "hackathon", "copilot"]',
    opportunity_types TEXT DEFAULT '["software", "ai_credits", "cloud", "education", "certification", "competition", "career"]',
    enable_daily_brief INTEGER DEFAULT 1,
    enable_critical_alerts INTEGER DEFAULT 1,
    telegram_chat_id TEXT,
    ai_provider TEXT DEFAULT 'fallback',
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 7. Saved Items (Bookmarks Table)
CREATE TABLE IF NOT EXISTS saved_items (
    id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL CHECK(item_type IN ('news', 'opportunity')),
    item_id TEXT NOT NULL,
    notes TEXT,
    saved_at TEXT DEFAULT (datetime('now')),
    UNIQUE(item_type, item_id)
);

-- 8. Verification Logs
CREATE TABLE IF NOT EXISTS verification_logs (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    is_live INTEGER NOT NULL,
    notes TEXT,
    checked_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
);

-- 9. System Status & Agent Run Metadata (Real Live Stats)
CREATE TABLE IF NOT EXISTS system_status (
    id TEXT PRIMARY KEY DEFAULT 'current',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    last_scan_time TEXT DEFAULT (datetime('now')),
    sources_checked INTEGER DEFAULT 9,
    new_opportunities_today INTEGER DEFAULT 0,
    next_report_time TEXT DEFAULT '9:00 PM IST',
    last_run_duration_sec REAL DEFAULT 0.0,
    last_error TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 10. Telegram Registered Users & Preference Mapping
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
);

-- Unique and Performance Indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_opps_claim_url ON opportunities(claim_url);
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url ON news(url);
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_items_url ON raw_items(url);
CREATE INDEX IF NOT EXISTS idx_raw_items_processed ON raw_items(processed);
CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_importance ON news(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_opps_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opps_type ON opportunities(opportunity_type);
CREATE INDEX IF NOT EXISTS idx_opps_expiry ON opportunities(expiry_date);
CREATE INDEX IF NOT EXISTS idx_opps_score ON opportunities(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_reports_date ON daily_reports(date DESC);
CREATE INDEX IF NOT EXISTS idx_saved_items ON saved_items(item_type, item_id);
CREATE INDEX IF NOT EXISTS idx_telegram_users_chat_id ON telegram_users(chat_id);

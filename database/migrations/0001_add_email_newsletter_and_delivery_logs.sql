-- D1 Migration: Add email newsletter preference fields and delivery logs
-- Idempotent for SQLite/Cloudflare D1

ALTER TABLE preferences ADD COLUMN email_newsletter_enabled INTEGER DEFAULT 0;
ALTER TABLE preferences ADD COLUMN newsletter_email TEXT;
ALTER TABLE preferences ADD COLUMN last_email_sent_at TEXT;

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

CREATE INDEX IF NOT EXISTS idx_delivery_logs_lookup ON delivery_logs(report_date, channel, recipient_id, status);

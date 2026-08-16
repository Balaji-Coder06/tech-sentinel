# 🛡️ Tech Sentinel

> **Never miss what matters in tech.**  
> *Personal technology intelligence platform & "Free Before It's Gone" opportunity radar operating at ₹0 cost.*

---

## ⚡ Overview

**Tech Sentinel** is an autonomous technology intelligence platform designed for developers and students. It continuously monitors hundreds of sources—engineering blogs, developer communities, GitHub repositories, cloud providers, and official platforms—to extract breaking updates and, most importantly, **discover free technology opportunities before they expire**.

Every night at **9:00 PM IST**, Sentinel synthesizes everything collected into a crisp, personalized **Daily Intelligence Digest** delivered via web and Telegram.

---

## 🎁 The Signature Feature: FREE BEFORE IT'S GONE

Unlike conventional news aggregators, Tech Sentinel's core differentiator is **active opportunity detection**:

- 💳 **Free Cloud Credits**: AWS, Google Cloud, Azure vouchers & activate credits.
- 🤖 **Developer Credits & Sandbox Tiers**: Free developer tiers, cloud instances, and database clusters.
- 🎓 **Student Packs & Certifications**: Microsoft exam vouchers, GitHub Student Pack benefits.
- 💻 **Free Software & SaaS**: IDE features, database clusters, serverless tiers.
- 🏆 **Hackathons & Internships**: High-reward competitions and developer challenges.

Every offer includes **expiration tracking** (🟢 Available, 🟠 Ends Soon, 🔴 Expires Today) and **official source verification** (preventing misleading secondary claims).

---

## 🏛️ Production Architecture & Single Source of Truth

```text
                  🌐 THE INTERNET
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
    RSS Feeds     GitHub Trending   Official APIs
        │                │                │
        └────────────────┼────────────────┘
                         ↓
             🐍 PYTHON AGENT (GitHub Actions)
                         │
            ┌────────────┼────────────┐
            ↓            ↓            ↓
        Classifier  Deduplicator   Opportunity
                                    Detector
            │            │            │
            └────────────┼────────────┘
                         ↓
          ⚡ DETERMINISTIC ENGINE (₹0)
         Local Offline Heuristic NLP
                         │
                         ↓
             🔐 POST /api/ingest (Auth Token)
                         ↓
                ☁️ CLOUDFLARE D1
                         │
            ┌────────────┴────────────┐
            ↓                         ↓
    ⚡ EDGE WORKER API         ▲ NEXT.JS WEB APP ▲
       (/api/news, /api/opps)     (Editorial UI)
            │                         │
            └────────────┬────────────┘
                         ↓
                  🌙 NIGHTLY REPORT
                         ↓
                  📱 Telegram Bot
```

---

## 💻 Tech Stack & Zero-Cost Blueprint

Designed to run at **strict ₹0 infrastructure cost** utilizing free tiers and open-source tooling:

| Component | Technology | Cost |
|---|---|---:|
| **Frontend UI** | Next.js 14 + TypeScript + Tailwind CSS | ₹0 |
| **Design System** | GoRead Editorial Theme (#FF5A36 Coral) | ₹0 |
| **Agent Pipeline** | Python 3.10 (httpx, feedparser, BeautifulSoup, Pydantic) | ₹0 |
| **Intelligence Engine**| Deterministic Local Heuristic NLP | ₹0 |
| **Database** | Cloudflare D1 / Local SQLite | ₹0 |
| **Edge API** | Cloudflare Workers | ₹0 |
| **Scheduler** | GitHub Actions (Every 2 hours & Nightly 9 PM IST) | ₹0 |
| **Notifications** | Telegram Bot API | ₹0 |

---

## 📁 Repository Structure

```text
tech-sentinel/
├── agent/                    # 🐍 Python Intelligence Agent
│   ├── ai/                   # Local deterministic engine & summarizer
│   ├── collectors/           # Multi-source ingestion (RSS, GitHub, Official)
│   ├── notifications/        # Telegram Bot HTML integration
│   ├── processors/           # Classifier, Deduplicator, Opportunity Detector, Verifier, Scorer
│   ├── storage/              # SQLite repository & Cloudflare D1 Sync client
│   ├── config.py             # Agent settings & environment loader
│   ├── models.py             # Pydantic data schemas
│   └── main.py               # CLI runner with clean subcommands
│
├── apps/
│   └── web/                  # ▲ Next.js Editorial Web Application
│       ├── app/              # App Router (Home, News, Free, Reports, Saved, Settings, API)
│       ├── components/       # Editorial UI Components & Modals
│       ├── lib/              # Types, API Client, Database bridge, Utilities
│       └── styles/           # Tailwind CSS tokens & Editorial typography
│
├── database/                 # 🗄️ Database Schemas & Seeds
│   ├── schema.sql            # Cloudflare D1 / SQLite DDL schema with unique constraints
│   └── seed.sql              # Rich initial seed dataset & system status
│
├── workers/                  # ⚡ Cloudflare Workers Edge API
│   └── api/                  # Edge route handlers (/api/ingest, /api/news, /api/stats, etc.)
│
├── .github/
│   └── workflows/            # ⚙️ GitHub Actions Automation
│       ├── collect.yml       # Continuous scan every 2 hours
│       └── nightly-report.yml# Nightly digest generator at 9 PM IST
│
├── source/                   # 📄 Product specifications & design docs
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Python packaging config
├── wrangler.toml             # Cloudflare Workers/D1 deployment config
└── README.md
```

---

## 🚀 Quick Start

### 1. Web Application

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to explore the editorial dashboard.

### 2. Python Agent Pipeline

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run complete intelligence cycle (Collect -> Deduplicate -> Detect -> Score -> Report -> Sync)
python -m agent.main run-all

# Or run individual stages:
python -m agent.main collect   # Fetch latest feeds from all sources
python -m agent.main process   # Run classification & opportunity detection
python -m agent.main report    # Synthesize nightly intelligence report
python -m agent.main notify    # Dispatch Telegram brief
```

---

## ⚙️ Environment Variables

Create a `.env` file based on `.env.example`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
APP_BASE_URL=http://localhost:3000

# Cloudflare D1 Ingestion Bridge (for GitHub Actions)
WORKER_API_URL=https://tech-sentinel-api.your-subdomain.workers.dev
INGESTION_SECRET=your_super_secret_token
```

---

## 🌐 Deploying to Cloudflare at ₹0 Cost

1. **Deploy Database (D1)**:
   ```bash
   npx wrangler d1 create tech-sentinel-db
   # Copy the generated database_id into wrangler.toml
   npx wrangler d1 execute tech-sentinel-db --file=database/schema.sql
   npx wrangler d1 execute tech-sentinel-db --file=database/seed.sql
   ```

2. **Configure Worker Secrets & Deploy Edge API (Cloudflare Workers)**:
   ```bash
   npx wrangler secret put INGESTION_SECRET
   npx wrangler secret put TELEGRAM_BOT_TOKEN
   # Optional webhook secret token for header validation
   npx wrangler secret put TELEGRAM_WEBHOOK_SECRET
   npx wrangler deploy
   ```

3. **Deploy Next.js Web App (Cloudflare Pages / Vercel)**:
   ```bash
   cd apps/web
   npx @cloudflare/next-on-pages
   ```

4. **Configure GitHub Actions Secrets**:
   In your GitHub repository settings, add:
   - `WORKER_API_URL`: URL of your deployed Cloudflare Worker (`https://tech-sentinel-api.sbalaji06.workers.dev`)
   - `INGESTION_SECRET`: Same secret configured in Cloudflare Workers
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token

---

## 📱 Telegram Bot Webhook Architecture

Tech Sentinel implements a **100% serverless, zero-polling** Telegram Bot webhook handler directly inside the Cloudflare Worker Edge API (`POST /api/telegram/webhook`).

### 🤖 Supported Commands

| Command | Action | Behavior |
|---|---|---|
| `/start` | Welcome & Auto-Register | Upserts user in Cloudflare D1 and enables daily digest (`telegram_digest_enabled = 1`) |
| `/subscribe` | Enable Digest | Subscribes user to daily 8:00 PM IST personalized intelligence briefing |
| `/unsubscribe` | Disable Digest | Opts out of daily briefings (can be resumed anytime) |
| `/status` | Subscription Status | Reports current digest subscription state (`🟢 Subscribed` or `🔴 Not Subscribed`) |
| `/help` | Command Menu | Displays complete command reference and dashboard links |
| `/news` | Intelligence Feed | Returns top 5 curated stories directly from D1 with direct links & inline buttons |
| `/opportunities` | Free Radar | Returns top 5 verified cloud credits & vouchers with claim URLs |
| `/latest` | Live Stream | Chronological stream of latest intelligence across all domains |

### 🚀 Production Webhook Registration

To connect your Telegram Bot to the production Cloudflare Worker webhook:

#### 1. Register Webhook with Telegram Bot API
```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://tech-sentinel-api.sbalaji06.workers.dev/api/telegram/webhook",
    "secret_token": "<TELEGRAM_WEBHOOK_SECRET>",
    "allowed_updates": ["message", "edited_message", "callback_query"],
    "drop_pending_updates": true
  }'
```

#### 2. Verify Webhook Status & Latency
```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

Expected response:
```json
{
  "ok": true,
  "result": {
    "url": "https://tech-sentinel-api.sbalaji06.workers.dev/api/telegram/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40,
    "ip_address": "..."
  }
}
```

#### 3. Reset or Delete Webhook (if switching back to local polling)
```bash
curl -s "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/deleteWebhook"
```

---

## 🛡️ License

MIT License. Designed with precision for developers who want to stay ahead of the technology curve.

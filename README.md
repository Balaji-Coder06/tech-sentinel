# 🛡️ Tech Sentinel

> **Autonomous personal technology intelligence platform & "Free Before It's Gone" opportunity radar.**

[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://python.org/)
[![Cloudflare Workers](https://img.shields.io/badge/Cloudflare-Workers%20%26%20D1-orange?logo=cloudflare)](https://workers.cloudflare.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?logo=github-actions)](https://github.com/features/actions)

---

## ⚡ What is Tech Sentinel?

Tech Sentinel is an autonomous technology intelligence system built for developers and students. It continuously monitors engineering feeds, developer communities, trending GitHub repositories, and official cloud provider registries to:

- **Track Breaking Tech Intelligence**: Aggregates, deduplicates, classifies, and synthesizes technical developments with structured heuristic insights (*What happened*, *Why it matters*, *What you can do*).
- **Surface "Free Before It's Gone" Opportunities**: Actively detects, parses, and verifies free cloud credits, 100% discount vouchers, developer tiers, student perks, and hackathons with expiration tracking.
- **Deliver Automated Daily Briefings**: Synthesizes a daily intelligence digest delivered via an editorial web application, serverless Telegram bot, and email newsletter.

---

## 🏛️ System Architecture

```text
  🌐 Data Sources (RSS, GitHub Trending, Official Registries)
                            │
                            ▼
     🐍 Python Agent Pipeline (GitHub Actions / Scheduled)
     ┌──────────────────────────────────────────────────┐
     │  1. Ingestion & Raw Staging                      │
     │  2. Deduplication & Taxonomy Classification      │
     │  3. Opportunity Detection & Verification         │
     │  4. Deterministic NLP Summarization & Scoring    │
     │  5. Nightly Digest Synthesis                     │
     └──────────────────────┬───────────────────────────┘
                            │  POST /api/ingest (Auth Token)
                            ▼
                ☁️ Cloudflare D1 (Edge SQL)
              ┌─────────────┴─────────────┐
              ▼                           ▼
   ⚡ Cloudflare Worker API       ▲ Next.js Web App
   (REST Endpoints & Webhook)   (Editorial Dashboard)
              │                           │
              ├───────────────────────────┤
              ▼                           ▼
     📱 Telegram Bot             📧 Email Newsletter
     (Webhook & Unified Dispatch)   (SMTP / Gmail)
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Web Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons |
| **Edge API & Database** | Cloudflare Workers (TypeScript), Cloudflare D1 (Serverless SQLite) |
| **Agent Engine** | Python 3.10+, `httpx`, `feedparser`, `beautifulsoup4`, `pydantic`, `scikit-learn` |
| **NLP Engine** | Local Deterministic Heuristic Engine (zero API costs, offline capable) |
| **Automation** | GitHub Actions (`collect.yml` every 2h, `nightly-report.yml` daily at 8:00 AM IST) |
| **Delivery Channels** | Telegram Bot (Serverless Webhook + Polling), SMTP / Gmail Newsletter |

---

## 📂 Repository Structure

```text
tech-sentinel/
├── agent/                    # Python Intelligence Agent
│   ├── ai/                   # Local deterministic summarizer & digest generator
│   ├── collectors/           # Feed ingestion (RSS, GitHub Trending, Official Registries)
│   ├── dispatch/             # Unified multi-channel idempotent delivery dispatcher
│   ├── notifications/        # Telegram & SMTP email notification handlers
│   ├── processors/           # Classifier, Deduplicator, Opportunity Detector, Verifier, Scorer
│   ├── storage/              # SQLite repository & Cloudflare D1 sync client
│   ├── telegram/             # Telegram service & digest builder
│   └── main.py               # CLI entrypoint for all agent workflows
├── apps/
│   └── web/                  # Next.js Editorial Web Application
│       ├── app/              # App Router pages (Home, News, Free Radar, Reports, Saved, Settings)
│       ├── components/       # Editorial UI components and modals
│       └── lib/              # API clients, types, and utilities
├── database/
│   ├── schema.sql            # Cloudflare D1 / SQLite 11-table DDL schema
│   └── seed.sql              # Initial seed dataset & system status
├── workers/
│   └── api/                  # Cloudflare Worker REST API & Telegram webhook handler
├── .github/workflows/        # Automation workflows for ingestion and nightly dispatch
├── pyproject.toml            # Python packaging configuration
├── requirements.txt          # Python dependencies
└── wrangler.toml             # Cloudflare Workers & D1 configuration
```

---

## 🚀 Quick Start

### 1. Web Application

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the editorial interface.

### 2. Python Agent Pipeline

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run complete autonomous intelligence cycle:
python -m agent.main run-all

# Or run discrete pipeline stages:
python -m agent.main collect    # Ingest raw items from all sources to staging
python -m agent.main process    # Deduplicate, classify, detect opportunities, score, sync
python -m agent.main report     # Synthesize nightly intelligence digest
python -m agent.main dispatch   # Deliver nightly briefing to Telegram & Email
python -m agent.main telegram info  # Verify Telegram bot configuration
```

---

## ⚙️ Configuration

Create a `.env` file based on `.env.example`:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional Email Newsletter (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# Web App URLs
APP_BASE_URL=https://tech-sentinel-chi.vercel.app
WEB_APP_URL=https://tech-sentinel-chi.vercel.app

# Database & Cloudflare D1 Ingestion Bridge
DATABASE_PATH=database/tech_sentinel.db
WORKER_API_URL=https://tech-sentinel-api.your-subdomain.workers.dev
INGESTION_SECRET=your_secret_ingestion_token
```

---

## ☁️ Deployment & Edge Setup

### Cloudflare D1 & Worker API

```bash
# 1. Create and initialize D1 database
npx wrangler d1 create tech-sentinel-db
# Add database_id to wrangler.toml, then apply schemas:
npx wrangler d1 execute tech-sentinel-db --file=database/schema.sql
npx wrangler d1 execute tech-sentinel-db --file=database/seed.sql

# 2. Configure secrets and deploy Edge Worker API
npx wrangler secret put INGESTION_SECRET
npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put TELEGRAM_WEBHOOK_SECRET
npx wrangler deploy
```

### Telegram Bot Serverless Webhook

Set up the Cloudflare Worker as your live Telegram webhook:

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<your-worker-subdomain>.workers.dev/api/telegram/webhook",
    "secret_token": "<TELEGRAM_WEBHOOK_SECRET>",
    "allowed_updates": ["message", "edited_message", "callback_query"],
    "drop_pending_updates": true
  }'
```

#### Supported Telegram Commands

| Command | Action |
|---|---|
| `/start` | Auto-register in D1 and enable daily intelligence digest |
| `/news` | Top curated stories ranked by importance score |
| `/opportunities` | Active Free Radar credits, vouchers, and claim links |
| `/latest` | Real-time chronological dispatch stream |
| `/status` | View current subscription and delivery preferences |
| `/subscribe` | Opt-in to daily 8:00 PM IST briefing |
| `/unsubscribe` | Pause automated daily briefings |
| `/help` | Complete command reference and dashboard links |

---

## 📄 License

This project is licensed under the MIT License.

# Tech Sentinel — Product Requirements Document

## 1. Product Overview

**Product Name:** Tech Sentinel  
**Tagline:** Never miss what matters in tech.

Tech Sentinel is a personal AI-powered technology intelligence agent that continuously discovers important technology news, developer updates, student opportunities, hackathons, internships, certifications, AI tools, and—most importantly—free or limited-time technology promotions.

Every night, Tech Sentinel processes everything collected during the day, removes duplicates and irrelevant information, ranks the most valuable items, verifies free opportunities where possible, and delivers a concise personalized daily digest.

### Core Objective

> Make sure the user never misses another valuable technology opportunity because they did not know about it in time.

---

## 2. Problem Statement

Technology changes extremely quickly and important opportunities are distributed across company blogs, developer websites, GitHub, social media, news websites, hackathon platforms, student programs, cloud providers, AI companies, certification platforms, and promotional campaigns.

A student or developer cannot realistically monitor all of these sources every day.

### Problems

1. **Information overload** — Too much technology news makes it difficult to identify what matters.
2. **Missed opportunities** — Free trials, credits, certifications, student programs, hackathons, and limited-time promotions can disappear before users discover them.
3. **Lack of personalization** — Traditional aggregators provide information but do not answer: "Is this actually useful for me?"

Tech Sentinel solves these through automated collection, AI filtering, ranking, personalization, and verification.

---

## 3. Product Goals

### Primary Goals

- Automatically collect relevant technology information.
- Identify important developments from many sources.
- Detect free technology promotions and opportunities.
- Identify expiration dates and eligibility requirements.
- Remove duplicate information.
- Summarize information using AI.
- Rank information according to user relevance.
- Generate a daily nighttime digest.
- Provide direct official claim/source links.
- Operate at ₹0 infrastructure/API cost wherever technically possible.

### Success Criteria

The system should allow the user to know:

> What happened in tech today, and what opportunities can I claim before they disappear?

---

## 4. Target User

### Primary User

Students and early-career developers interested in:

- AI opportunities
- Developer tools
- Free resources
- Cloud credits
- Certifications
- Internships
- Hackathons
- Student programs
- Open-source opportunities
- Limited-time promotions

### Secondary Users

- Developers
- Freelancers
- Startup founders
- Researchers
- Tech enthusiasts

---

## 5. Core Features

### 5.1 Technology News Aggregation

Collect technology information from multiple sources.

Categories:

- Artificial Intelligence
- Machine Learning
- Software Development
- Web Development
- Cloud Computing
- Cybersecurity
- Developer Tools
- Open Source
- Mobile Development
- Game Development
- Databases
- Data Science
- Startups
- Major Technology Companies
- Technology Education

Users should be able to enable/disable categories.

---

## 6. Free Opportunity Detection

This is the core differentiating feature.

Detect opportunities that have monetary or practical value.

### Opportunity Types

#### Free Software

- Free developer tools
- Free IDE features
- Free SaaS plans
- Free AI tools
- Free design tools

#### AI Promotions

- Free AI subscriptions
- Free API credits
- Free model access
- Free AI courses
- Free AI tools

#### Cloud

- AWS credits
- Azure credits
- Google Cloud credits
- Free compute
- Free databases
- Free hosting

#### Education

- Free courses
- Free certifications
- Free exam vouchers
- Student programs
- Learning subscriptions

#### Competitions

- Hackathons
- Coding competitions
- AI competitions
- Developer challenges

#### Career

- Internships
- Student developer programs
- Open-source programs
- Company challenges

#### Resources

- Free books
- Free ebooks
- Free datasets
- Free development resources

---

## 7. Promotion Verification

The system must distinguish actual free opportunities from clickbait or misleading promotions.

Each opportunity should contain:

- Name
- Provider
- Description
- Normal Value
- Current Cost
- Promotion Type
- Eligibility
- Start Date
- Expiration Date
- Official URL
- Verification Status
- Last Verified

### Verification Status

- **Verified** — Official source confirms the promotion.
- **Needs Verification** — Found from secondary sources without official confirmation.
- **Expired** — No longer available.

---

## 8. AI Relevance Engine

Every collected item receives an AI-assisted relevance score.

Example:

**AI Tool Launch — Relevance: 94/100**

Why:

- AI development
- Free API credits
- Useful for developers
- Currently available

Prioritize based on:

- User interests
- Technology category
- Free value
- Deadline
- Career relevance
- Developer relevance
- Student relevance
- Popularity
- Importance
- Freshness

---

## 9. "Why Should I Care?" Feature

Every important item should have an AI-generated explanation.

Instead of simply saying:

> Google released XYZ.

The system should explain:

> **Why you should care:** This provides free access to a new AI model that could be useful for your projects and experimentation.

---

## 10. Opportunity Priority

Each opportunity receives a priority level.

- **Critical** — Highly valuable and expires soon.
- **High** — Very useful but deadline is not immediate.
- **Medium** — Potentially useful.
- **Low** — Interesting but not immediately actionable.

Example:

> 🔥 FREE $100 Cloud Credits  
> Expires in 3 days  
> Student eligible  
> Priority: 97/100

---

## 11. Daily Nightly Digest

Generate one consolidated report every night.

### Report Structure

- Tech Sentinel header
- Date
- Top stories
- Free opportunities
- Student opportunities
- AI/development updates
- Open-source highlights
- Expiring soon
- 30-second summary

The report should be concise and actionable.

---

## 12. Notification System

Initial notification channel:

- Telegram

Future options:

- Email
- Discord
- Web dashboard notification

---

## 13. Web Dashboard

Sections:

- Home
- News
- Free
- Opportunities
- Saved
- Daily Reports
- Settings

### Home

- Today's highlights
- Important opportunities
- Expiring promotions

### News

- AI
- Development
- Cloud
- Cybersecurity
- Open source
- Startups

### Free

- Free tools
- Free credits
- Free trials
- Certifications
- Courses

### Opportunities

- Hackathons
- Internships
- Student programs

### Saved

- Bookmarked opportunities

### History

- Previous daily reports

---

## 14. Search

Users can search for:

- free AI tools
- GitHub student benefits
- AWS credits
- hackathons
- free certifications
- React
- LLMs

Search results should include:

- Relevant results
- Date discovered
- Expiration date
- Category
- Verification status

---

## 15. Save / Bookmark

Users can save opportunities and articles for later.

Saved items remain accessible even after disappearing from the main feed.

---

## 16. Expiration Tracking

Promotion lifecycle:

`ACTIVE → EXPIRING SOON → EXPIRED`

The system should automatically detect and update expired opportunities and never present expired offers as active.

---

## 17. Source Management

Maintain a configurable source registry.

Each source contains:

- Source Name
- URL
- Type
- Category
- Status
- Last Successful Fetch
- Last Error

Source types can include:

- RSS feeds
- APIs
- Official company blogs
- GitHub repositories
- Developer platforms
- Opportunity platforms

---

## 18. Duplicate Detection

Detect duplicates using:

- URL matching
- Title similarity
- Semantic similarity
- Entity matching

Multiple reports about the same announcement should become one consolidated item with multiple sources.

---

## 19. AI Summarization

Each important item should provide:

### What happened
One concise explanation.

### Why it matters
Personalized explanation.

### What you can do
Action recommendation such as Claim, Apply, Register, Read More, or Try It.

---

## 20. Personalization

Maintain user preferences for:

- Categories
- Keywords
- Opportunity types
- Notification preferences

The ranking engine should use these preferences when generating the nightly digest.

---

## 21. Agent Architecture

```text
Sources
   ↓
Collector
   ↓
Normalizer
   ↓
Deduplicator
   ↓
AI Analyzer
   ↓
 ┌───────────────┬────────────────┐
 ↓               ↓                ↓
News Ranking  Opportunity      Verification
             Detection
 ↓               ↓                ↓
 └───────────────┴────────────────┘
                 ↓
           Daily Digest
                 ↓
               User
```

---

## 22. Zero-Cost Requirement

The core system must be deployable without paid infrastructure.

Avoid requiring:

- Paid API subscriptions
- Paid hosting
- Paid databases
- Paid AI APIs
- Paid email services
- Paid automation platforms

Prefer:

- GitHub Actions
- Cloudflare free services
- SQLite/D1
- Free AI tiers
- Local/open-source AI
- Telegram Bot API
- RSS/public APIs

The architecture must not depend on one provider remaining free forever.

---

## 23. Technical Requirements

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide

### Agent

- Python
- httpx
- feedparser
- BeautifulSoup
- Pydantic
- scikit-learn

### Backend

- Cloudflare Workers

### Database

- Cloudflare D1

### Scheduler

- GitHub Actions

### AI

- Provider abstraction supporting free cloud providers and local models

### Notifications

- Telegram Bot API

---

## 24. Data Model

### NewsItem

- id
- title
- description
- url
- source
- category
- published_at
- discovered_at
- summary
- importance_score
- relevance_score

### Opportunity

- id
- title
- provider
- description
- category
- normal_value
- current_value
- eligibility
- claim_url
- start_date
- expiry_date
- verification_status
- importance_score
- last_verified

### UserPreference

- categories
- keywords
- opportunity_types
- notification_preferences

---

## 25. Security Requirements

- Never store unnecessary personal information.
- Never store API keys in source code.
- Use environment variables/secrets.
- Validate external URLs.
- Sanitize scraped content.
- Rate-limit requests.
- Respect source policies.
- Never automatically claim promotions without explicit user action.

---

## 26. Reliability Requirements

If one source fails, the entire pipeline must not fail.

Failed sources should be logged while other sources continue processing.

---

## 27. Transparency

Every AI-generated result must retain its original source.

For promotions, prefer the official claim URL over affiliate or aggregator links.

Store:

- Source
- Original URL
- Discovery date
- Last verification date

---

## 28. MVP Definition

The minimum usable product must:

- Collect technology news.
- Collect free technology opportunities.
- Categorize information.
- Remove duplicates.
- Generate AI summaries.
- Rank important information.
- Detect expiration dates.
- Generate nightly digest.
- Provide source/claim links.
- Run without paid infrastructure.

The MVP must answer:

> What important happened in tech today?

and:

> What free technology opportunities can I claim right now?

---

## 29. Key Differentiator

Tech Sentinel is not another technology news aggregator.

Its core identity is:

> **An AI-powered opportunity detection system.**

The signature feature is:

### FREE BEFORE IT'S GONE

The agent actively searches for things users can obtain at ₹0, especially limited-duration or limited-eligibility offers.

---

## 30. Product Vision

```text
TECH SENTINEL

I've been watching the tech world for you.

🔥 7 things worth knowing
🎁 4 free opportunities
🎓 2 student opportunities
⚡ 1 opportunity expires tomorrow
🐙 3 interesting open-source projects

You missed nothing today.
```

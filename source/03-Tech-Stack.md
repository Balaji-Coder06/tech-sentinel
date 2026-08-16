# Tech Sentinel — Technology Stack Document

## 1. Stack Decision

For Tech Sentinel's requirements and strict ₹0 budget, the recommended stack is:

> **Next.js + TypeScript + Cloudflare Workers + Cloudflare D1 + GitHub Actions + Free/Local AI Providers + Telegram**

| Layer | Technology | Cost |
|---|---|---:|
| Frontend | Next.js + TypeScript | ₹0 |
| Styling | Tailwind CSS | ₹0 |
| UI Components | shadcn/ui | ₹0 |
| Icons | Lucide | ₹0 |
| Backend/API | Cloudflare Workers | ₹0 within free limits |
| Database | Cloudflare D1 | ₹0 within free limits |
| Scheduled Jobs | GitHub Actions | ₹0 within free limits |
| AI | Free AI API / local model fallback | ₹0 |
| News Collection | RSS + public APIs | ₹0 |
| Notifications | Telegram Bot | ₹0 |
| Hosting | Cloudflare | ₹0 within free limits |
| Source Control | GitHub | ₹0 |

The architecture must avoid making any single paid service indispensable.

---

## 2. Why This Stack?

Tech Sentinel is primarily a:

> **Data collection → processing → intelligence → presentation**

system.

A traditional stack such as React + Express + Node + PostgreSQL + Redis + Docker would introduce unnecessary infrastructure.

Recommended architecture:

```text
INTERNET
   ↓
RSS / APIs / GitHub
   ↓
GitHub Actions
   ↓
AI Processing Engine
   ↓
Cloudflare D1
   ↓
Cloudflare Workers
   ↓
Next.js UI
   ↓
Mobile / Desktop
```

---

## 3. Frontend

### Next.js

Use Next.js with TypeScript.

Benefits:

- React
- File-based routing
- Server capabilities
- SEO
- Optimized builds
- Large ecosystem
- Responsive application development

The application can start as one full-stack web project without maintaining separate frontend/backend repositories.

---

## 4. TypeScript

All application-side frontend and API code should use TypeScript.

Core entities include:

- News
- Opportunity
- Source
- User
- Category
- Promotion
- DailyReport
- Verification

Example:

```ts
type Opportunity = {
  id: string;
  title: string;
  provider: string;
  category: string;
  claimUrl: string;
  expiresAt?: string;
  verified: boolean;
  score: number;
};
```

---

## 5. UI Layer

### Tailwind CSS

Use Tailwind for the design system.

It makes responsive implementation easier across:

- Mobile
- Tablet
- Desktop

Keep design tokens centralized so the GoRead-inspired editorial style remains consistent.

---

## 6. Component Library

### shadcn/ui

Use shadcn/ui selectively for:

- Button
- Dialog
- Sheet
- Dropdown
- Tabs
- Card
- Tooltip
- Badge
- Command/Search
- Toast

Customize components heavily so the application does not look like a default shadcn project.

---

## 7. Icons

### Lucide

Use Lucide for:

- Search
- Bookmark
- Notifications
- Clock
- External links
- Filters
- Categories
- Settings

---

## 8. Backend

### Cloudflare Workers

Cloudflare Workers should expose the application's API.

Example endpoints:

```text
/api/news
/api/opportunities
/api/search
/api/reports
/api/saved
/api/preferences
```

The backend should remain lightweight and stateless where possible.

---

## 9. Database

### Cloudflare D1

Use D1 for the initial relational database.

Core tables:

```text
news
opportunities
sources
categories
reports
users
preferences
saved_items
verification_logs
```

D1 is a strong fit because it integrates directly with Cloudflare Workers.

---

## 10. Why Not Supabase?

Supabase is a valid alternative and may be useful later, especially if the application needs PostgreSQL-heavy features or more mature authentication.

However, for the initial personal version, Cloudflare provides a simpler single ecosystem:

```text
Cloudflare
├── Pages
├── Workers
├── D1
└── Deployment
```

Therefore D1 is the preferred choice.

---

## 11. Data Collection Engine

Use Python for the ingestion and AI processing pipeline.

Recommended libraries:

```text
Python
├── httpx
├── feedparser
├── BeautifulSoup
├── Pydantic
├── dateparser
└── scikit-learn
```

Python is chosen because of its strong ecosystem for:

- RSS processing
- Web extraction
- NLP
- AI SDKs
- Data cleaning
- Similarity detection

---

## 12. Why Python + TypeScript?

Use each language where it is strongest.

### TypeScript

Frontend + application API:

```text
Next.js
Cloudflare Workers
UI
```

### Python

Intelligence pipeline:

```text
Collectors
↓
Parsing
↓
Classification
↓
Deduplication
↓
Opportunity detection
↓
AI processing
```

This separation is intentional.

---

## 13. AI Provider Architecture

Do not hard-code Tech Sentinel to one AI provider.

Use an abstraction:

```text
AIProvider
    │
    ├── GeminiProvider
    ├── GroqProvider
    └── LocalProvider
```

The provider should be switchable through configuration.

This protects the project from changes in free-tier limits and provider availability.

---

## 14. AI Responsibilities

AI should perform:

### Classification

Determine whether content is relevant.

### Categorization

Examples:

- AI
- Cloud
- Open Source
- Career
- Student
- Development

### Importance Scoring

Assign a score from 0–100.

### Opportunity Detection

Determine whether content contains a genuine free opportunity.

### Information Extraction

Extract:

- Value
- Price
- Deadline
- Eligibility
- Provider
- Claim URL

### Summarization

Generate concise summaries.

### Personalization

Explain why the item matters to the user.

---

## 15. Collection Sources

Prefer RSS wherever possible.

Advantages:

- Lightweight
- Easier to maintain
- Lower resource usage
- Easier scheduling
- Cleaner data

Source structure:

```text
collectors/
    rss/
    github/
    official/
    opportunities/
```

Every collector should follow a common interface.

Example:

```python
class Collector:
    def fetch(self):
        ...
```

---

## 16. Deduplication

Use the cheapest deterministic checks first.

```text
Same URL
   ↓
Duplicate
```

Then:

- Title similarity
- Source/entity matching
- Semantic similarity where necessary

Do not waste AI calls processing the same story repeatedly.

---

## 17. Opportunity Detection Pipeline

```text
Article
   ↓
Is it technology-related?
   ↓
YES
   ↓
Does it contain an offer?
   ↓
YES
   ↓
Is the offer actually free?
   ↓
YES
   ↓
Extract:
   ├── Value
   ├── Eligibility
   ├── Deadline
   ├── Claim URL
   └── Provider
          ↓
       Verify
          ↓
    Opportunity
```

---

## 18. Verification Architecture

AI must not be the only authority.

Store:

```text
AI conclusion
+
Original source
+
Official URL
+
Last verification timestamp
```

Verification states:

```text
VERIFIED
PENDING
EXPIRED
```

For promotions, prefer official provider URLs.

---

## 19. Scheduler

### GitHub Actions

Use GitHub Actions for scheduled jobs.

Example:

```text
Every 2 hours
      ↓
Collect sources
      ↓
Process new items
      ↓
Store results

Every night
      ↓
Generate Daily Sentinel
      ↓
Send Telegram notification
```

Keep jobs lightweight to remain within free usage limits.

---

## 20. Daily Report Generator

Nightly pipeline:

```text
D1
 ↓
Today's items
 ↓
Rank
 ↓
Select top stories
 ↓
Select opportunities
 ↓
Select expiring offers
 ↓
AI generates digest
 ↓
Store DailyReport
 ↓
Telegram
```

---

## 21. Notifications

### Initial Provider

**Telegram Bot API**

Example notification:

```text
🌙 TECH SENTINEL

Your daily intelligence is ready.

🔥 5 important stories
🎁 3 free opportunities
⏰ 1 expires tomorrow

Open Daily Sentinel →
```

The notification should link to the web report.

---

## 22. Hosting

### Cloudflare

Recommended deployment:

```text
GitHub
   ↓
Cloudflare
   ↓
Tech Sentinel
```

Use Cloudflare for:

- Web deployment
- Workers
- D1
- API layer

---

## 23. Authentication

For the personal version, avoid unnecessary authentication complexity.

Initial options:

- Private/personal deployment
- Simple protected access

If Tech Sentinel becomes a public product, add proper authentication using a suitable OAuth/auth provider.

---

## 24. Repository Structure

```text
tech-sentinel/
│
├── apps/
│   └── web/
│       ├── app/
│       ├── components/
│       ├── lib/
│       └── styles/
│
├── agent/
│   ├── collectors/
│   │   ├── rss/
│   │   ├── github/
│   │   └── official/
│   │
│   ├── processors/
│   │   ├── classifier.py
│   │   ├── deduplicator.py
│   │   ├── opportunity_detector.py
│   │   ├── verifier.py
│   │   └── scorer.py
│   │
│   ├── ai/
│   │   ├── provider.py
│   │   ├── gemini.py
│   │   ├── groq.py
│   │   └── local.py
│   │
│   └── main.py
│
├── database/
│   ├── migrations/
│   └── schema.sql
│
├── workers/
│   └── api/
│
├── .github/
│   └── workflows/
│       ├── collect.yml
│       ├── process.yml
│       └── nightly-report.yml
│
├── docs/
│
├── README.md
└── package.json
```

---

## 25. Core Technology Summary

### Frontend

```text
Next.js
TypeScript
Tailwind CSS
shadcn/ui
Lucide
```

### Agent

```text
Python
httpx
feedparser
BeautifulSoup
Pydantic
scikit-learn
```

### Backend

```text
Cloudflare Workers
```

### Database

```text
Cloudflare D1
```

### Automation

```text
GitHub Actions
```

### AI

```text
Gemini / Groq
+
Local model fallback
```

### Notifications

```text
Telegram Bot API
```

### Deployment

```text
GitHub
↓
Cloudflare
```

---

## 26. Technologies Intentionally Excluded

### MongoDB

Not needed for the initial architecture.

### Firebase

Not necessary for this use case.

### Redis

Unnecessary for the expected workload.

### Docker

Avoid initially unless deployment requirements change.

### Kubernetes

Completely unnecessary for the personal MVP.

### AWS

Avoid unnecessary cloud infrastructure complexity when Cloudflare can cover the workload.

### Paid AI APIs

Not required for the core system.

### LangChain

Do not introduce an agent framework initially. Build the core pipeline directly so its behavior remains understandable and controllable.

---

## 27. Final Architecture

```text
                    🌐 INTERNET
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
         RSS           GitHub       Official APIs
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  🐍 PYTHON AGENT
                         │
             ┌───────────┼───────────┐
             ↓           ↓           ↓
        Classifier   Deduplicator  Detector
             │           │           │
             └───────────┼───────────┘
                         ↓
                    🤖 AI ENGINE
                         │
                  Ranking + Summary
                         │
                         ↓
                 ☁️ CLOUDFLARE D1
                         │
                         ↓
               ⚡ CLOUDFLARE WORKER
                         │
                         ↓
               ▲ NEXT.JS FRONTEND ▲
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
        💻 Desktop                📱 Mobile
                         │
                         ↓
                  🌙 DAILY REPORT
                         │
                         ↓
                  Telegram Bot
```

---

## 28. Cost Target

Target infrastructure cost:

> **₹0**

The design depends on free tiers, open-source software, RSS/public sources, and free/local AI options. Free-tier limits and provider policies can change, so the system should remain provider-agnostic and avoid mandatory paid dependencies.

### Final Stack

**Next.js + TypeScript** → UI  
**Python** → Agent  
**Cloudflare Workers** → API  
**Cloudflare D1** → Database  
**GitHub Actions** → Scheduler  
**Free/local AI providers** → Intelligence  
**Telegram Bot** → Nightly notification  
**Cloudflare** → Deployment

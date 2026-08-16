# Tech Sentinel — UI/UX Design Document

**Product:** Tech Sentinel  
**Platforms:** Mobile + Desktop/Web  
**Design Direction:** GoRead-inspired editorial news experience + premium AI opportunity intelligence  
**Reference:** GoRead News App by the supplied Dribbble reference  
**Core visual idea:** Clean news reader on the surface, intelligent opportunity radar underneath.

---

## 1. Design Philosophy

Tech Sentinel should not feel like a generic AI dashboard.

Avoid:

- Overly futuristic neon UI
- Huge chatbot interface
- Excessive glassmorphism
- Too many cards
- Corporate dashboard appearance
- Dense information walls

Instead, it should feel like:

> **A premium technology magazine that happens to have an AI agent working behind it.**

The GoRead reference provides the editorial inspiration. Tech Sentinel adds:

- AI prioritization
- Opportunity discovery
- Expiration awareness
- Personalization
- Saved items
- Daily intelligence reports

---

## 2. Visual Identity

### Style

**Editorial + Minimal + Premium + Intelligent**

Visual characteristics:

- Large typography
- Spacious layouts
- Rounded cards
- Soft shadows
- Strong imagery
- Minimal borders
- Clear hierarchy
- Restrained accent color
- Smooth animations

---

## 3. Color System

### Light Mode

```text
Background       #F7F7F5
Primary Text     #171717
Secondary Text   #707070
Card             #FFFFFF
Border           #E8E8E5
Accent           #FF5A36
Success          #27AE60
Warning          #F2A900
```

### Dark Mode

```text
Background       #111111
Primary Text     #F5F5F5
Secondary Text   #999999
Card             #1A1A1A
Border           #292929
Accent           #FF6845
Success          #3CCB7F
Warning          #F4B740
```

The coral/orange accent is the visual signature of Tech Sentinel.

---

## 4. Typography

Recommended:

- Inter
- Plus Jakarta Sans

Hierarchy:

```text
Hero headline       32–42px
Section heading     24–28px
Article title       18–22px
Body                14–16px
Metadata            11–13px
```

Desktop typography can scale upward.

---

## 5. Desktop Navigation

Use a persistent sidebar.

```text
┌─────────────────────────────────────────────┐
│  ◉ TECH SENTINEL                            │
│                                             │
│  Home                                       │
│  News                                       │
│  Free                                       │
│  Opportunities                              │
│  Saved                                      │
│  Daily Reports                              │
│                                             │
│  ─────────────                              │
│                                             │
│  Preferences                                │
│  Settings                                   │
│                                             │
└─────────────────────────────────────────────┘
```

Sidebar width:

**240–260px**

Keep it fixed while content scrolls.

---

## 6. Mobile Navigation

Use a bottom navigation bar.

```text
┌────────────────────────────────┐
│                                │
│          CONTENT               │
│                                │
├────────────────────────────────┤
│ Home  News  Free  Saved  You   │
└────────────────────────────────┘
```

Primary destinations:

- Home
- News
- Free
- Saved
- Profile

The **Free** section should receive special visual emphasis.

---

## 7. Mobile Home Screen

The most important screen.

### Header

```text
Good evening, Balaji 👋

Here's what you missed today.                         🔔
```

Then:

```text
Search technology, tools, opportunities...
```

Use a rounded search field.

---

## 8. Mobile Hero Story

Large editorial story.

```text
┌──────────────────────────────┐
│                              │
│       [ARTICLE IMAGE]        │
│                              │
│  ARTIFICIAL INTELLIGENCE     │
│                              │
│  Major AI development        │
│  announced today             │
│                              │
│  4 min read      2h ago      │
└──────────────────────────────┘
```

Prioritize:

- Strong image
- Large headline
- Small metadata
- Minimal controls

---

## 9. For You Section

Use horizontally scrollable editorial cards on mobile.

```text
For You                         See all →

┌─────────────────────────────┐
│ [image]                     │
│ AI model changes developer  │
│ workflows                   │
│                             │
│ AI · 2h ago                 │
└─────────────────────────────┘
```

---

## 10. Signature Section — Free Before It's Gone

This is the core differentiator.

```text
FREE BEFORE IT'S GONE       See all →

Free tech offers worth claiming before they expire.
```

Opportunity card:

```text
┌──────────────────────────────┐
│ 🎁                           │
│                              │
│ 1 MONTH FREE                 │
│                              │
│ AI Developer Pro             │
│                              │
│ Worth $20                    │
│                              │
│ Ends in 2 days               │
│                              │
│       CLAIM FREE →           │
└──────────────────────────────┘
```

Expiration must be highly visible.

States:

- 🟢 Available
- 🟠 Ends soon
- 🔴 Expires today

---

## 11. Free Opportunity Card

Every opportunity should show:

- Provider logo
- Opportunity name
- What you get
- Normal value
- Current price
- Eligibility
- Expiration
- Verification state
- Claim action

Example:

```text
Provider Logo

Opportunity Name

What you get

Normal value: $20
Current price: FREE

Eligibility: Students

Expires: Aug 20

✓ Verified

[Claim Opportunity]
```

---

## 12. Don't Miss Section

```text
⚡ Don't Miss

3 important things happened today.

→ New AI model released
→ GitHub launched developer feature
→ Free cloud credits available
```

This provides immediate scanning value.

---

## 13. AI Daily Brief

```text
━━━━━━━━━━━━━━━━━━━━

🤖 YOUR DAILY BRIEF

Today was mainly about AI,
developer tools and cloud.

3 things deserve your attention.

[Read 60-sec briefing]

━━━━━━━━━━━━━━━━━━━━
```

The report should feel like an AI-generated newspaper column.

---

## 14. News Feed

### Desktop

Use an editorial list.

```text
Technology

All   AI   Development   Cloud   Cyber   Open Source

────────────────────────────────────────────

[IMAGE]  Major AI announcement
         Short summary...
         AI · 2h ago

────────────────────────────────────────────

[IMAGE]  New developer tool
         Short summary...
         Development · 4h ago
```

### Mobile

Convert to vertically stacked cards.

---

## 15. Article Page

```text
← Back

ARTIFICIAL INTELLIGENCE

Major AI announcement
changes the developer landscape

2 hours ago · 5 min read

[ LARGE IMAGE ]

AI-generated summary

┌──────────────────────────┐
│ 🤖 Why this matters     │
│                          │
│ This could be useful...  │
└──────────────────────────┘

What happened

...

Key points

• ...
• ...
• ...

Source:
Official Website

[Read Original →]

🔖 Save
```

---

## 16. AI Summary Box

Every important article gets:

### Sentinel Summary

**What happened**

One sentence.

**Why it matters**

Personalized explanation.

**What you can do**

Action recommendation.

Example:

> **What happened:** A major company released a new AI model.
>
> **Why it matters:** It provides capabilities useful for AI-powered applications.
>
> **What you can do:** Try the API and compare it with your current tools.

---

## 17. Desktop Home

Do not simply stretch the mobile layout.

Use a three-column editorial layout.

```text
┌───────┬─────────────────────────────┬───────────────┐
│       │                             │               │
│ SIDE  │        MAIN CONTENT         │   SIDEBAR     │
│ BAR   │                             │               │
│       │  Featured Story             │ Trending      │
│       │                             │               │
│       │  For You                    │ Free          │
│       │                             │               │
│       │  News Feed                  │ Expiring      │
│       │                             │               │
└───────┴─────────────────────────────┴───────────────┘
```

Recommended proportions:

- Main content: ~60%
- Right rail: ~25%
- Navigation: ~15%

---

## 18. Desktop Right Sidebar

### Trending

```text
1  AI agents
2  Open source
3  Cloud
4  Cybersecurity
```

### Free Opportunities

```text
AI Pro
FREE · 2 days left

Cloud Credits
FREE · 5 days left
```

### Expiring Soon

```text
Certification
Tomorrow

Cloud Credits
2 days
```

---

## 19. Desktop Free Page

Header:

> **Free Tech Opportunities**

Subtext:

> Things you can claim for ₹0 right now.

Filters:

```text
All
AI
Cloud
Developer
Education
Certification
Software
Student
```

Sort:

```text
Most Valuable
Expiring Soon
Newest
```

Use a 3-column card grid on desktop.

---

## 20. Opportunity Details

```text
┌──────────────────────────────────────────┐
│                                          │
│  PROVIDER                                │
│                                          │
│  AI Developer Credits                    │
│                                          │
│  FREE                                    │
│                                          │
│  Normal value     $100                   │
│  Eligibility      Students               │
│  Expires          Aug 20                 │
│                                          │
│  ✓ Official source verified              │
│                                          │
│             [ CLAIM NOW → ]              │
│                                          │
└──────────────────────────────────────────┘
```

Below:

- What you get
- Eligibility
- How to claim
- Expiration
- Official source
- Similar opportunities

---

## 21. Search Experience

Use a modern universal search.

```text
┌──────────────────────────────────────────┐
│ 🔍 Search tech, AI, tools, opportunities │
└──────────────────────────────────────────┘
```

Suggestions:

- free AI tools
- AWS credits
- student certifications
- hackathons

Results intelligently combine:

- News
- Opportunities
- Sources

---

## 22. Saved Page

```text
Saved

Articles       Opportunities

────────────────────────────

🔖 New AI coding tool
🔖 Free cloud credits
🔖 Hackathon
🔖 AI certification
```

Mobile should support swipe-to-remove.

---

## 23. Daily Report Page

Make this feel like a digital newspaper.

```text
TECH SENTINEL

DAILY INTELLIGENCE
August 16, 2026

━━━━━━━━━━━━━━━━━━

TODAY IN TECH

A short AI-generated overview...

━━━━━━━━━━━━━━━━━━

🔥 TOP STORIES

01 ...
02 ...

━━━━━━━━━━━━━━━━━━

🎁 FREE BEFORE IT'S GONE

...

━━━━━━━━━━━━━━━━━━

🎓 OPPORTUNITIES

...

━━━━━━━━━━━━━━━━━━

🐙 OPEN SOURCE

...

━━━━━━━━━━━━━━━━━━

⏰ EXPIRING SOON

...

━━━━━━━━━━━━━━━━━━

SENTINEL'S TAKE

...
```

This can become the signature experience.

---

## 24. Profile / Preferences

Keep it simple.

### Interests

```text
☑ Artificial Intelligence
☑ Web Development
☑ Cloud
☑ Open Source
☐ Cybersecurity
☐ Gaming
```

### Opportunities

```text
☑ Free tools
☑ Free credits
☑ Hackathons
☑ Certifications
☑ Student programs
☑ Internships
```

### Notifications

```text
🌙 Daily Brief       ON
🔥 Critical Alerts   ON
```

---

## 25. AI Agent Status

A small status component can show that the agent is working.

```text
● Sentinel active

Last scan
8 minutes ago

Sources checked
127

New opportunities
6

Next report
9:00 PM
```

It should communicate:

> Your agent is working.

Do not turn it into a technical admin dashboard.

---

## 26. Micro-interactions

Keep animations subtle.

### Desktop card hover

- Slight lift
- Image zoom
- Soft shadow

### Mobile

- Swipe gestures
- Smooth transitions
- Pull-to-refresh
- Bottom sheets

### Bookmark

Animated bookmark icon.

### Claim

```text
Claim Opportunity
       ↓
Opening...
       ↓
✓ Opened
```

---

## 27. Responsive Breakpoints

### Mobile

**320–767px**

- Single column
- Bottom navigation
- Large touch targets

### Tablet

**768–1023px**

- Two-column layout
- Collapsed navigation

### Desktop

**1024–1439px**

- Sidebar
- Main content
- Right rail

### Large Desktop

**1440px+**

Maximum content width:

**1440–1600px**

Never stretch content endlessly.

---

## 28. Mobile vs Desktop Philosophy

### Mobile

**Fast consumption.**

The user should understand the important things in 30–60 seconds.

Priority:

1. Free opportunities
2. Don't Miss
3. Daily brief
4. Top stories
5. Personalized news

### Desktop

**Deep exploration.**

Priority:

1. News discovery
2. Research
3. Opportunity comparison
4. Search
5. Daily reports
6. Saved information

---

## 29. Accessibility

Support:

- WCAG-friendly contrast
- Keyboard navigation
- Screen readers
- Focus indicators
- Reduced-motion preference
- Minimum touch target sizes
- Semantic HTML
- Accessible labels

---

## 30. Core Design Rule

Every screen should answer:

> **What is worth my attention right now?**

Hierarchy:

**🔥 Important → 🎁 Valuable → ⏰ Urgent → 📖 Interesting**

---

## 31. Final Visual Direction

```text
TECH SENTINEL

TODAY'S SIGNAL

The 5 things worth
your attention today.

🔥 TOP STORIES

🎁 FREE BEFORE IT'S GONE

⚡ DON'T MISS

🤖 YOUR DAILY BRIEF

🐙 OPEN SOURCE

🎓 OPPORTUNITIES
```

The GoRead reference provides the editorial foundation; Tech Sentinel adds the intelligence layer.

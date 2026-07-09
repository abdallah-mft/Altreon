# ALTREON — Frontend Prompt

Build a single-page demo website for **ALTREON**, an AI-powered cybersecurity triage and SOAR platform. This is a showcase/portfolio project — no real backend connection needed, all data is mock/fake. The goal is to impress visitors and make the product look real and polished.

## Design Identity

- Clean **AI-driven enterprise dashboard** aesthetic — professional yet approachable
- Soft grid background, hand-drawn flow arrows, rounded containers
- Strong emphasis on clarity, process visualization, and cybersecurity workflow mapping
- Typography: elegant serif accents + bold modern sans-serif headings
- Minimalist iconography, generous spacing, muted tones
- No emojis anywhere
- Smooth scroll-triggered animations (fade-in, slide-up, etc.) as user scrolls

## Color Palette

- Sage Green: `#7E9E5D`
- Moss Green: `#6E8B4E`
- Dark Navy/Purple: `#363054`
- Soft Mint Background: `#E8ECE2`
- Light Gray Grid: `#C8CEC2`
- Charcoal Text/Lines: `#2E2E2E`
- White: `#FFFFFF` (content areas)

## Pages / Sections

The site is a **single scrollable page** with smooth section transitions.

### 1. Hero Section

- Full-viewport hero with ALTREON logo/wordmark
- Tagline: "Rapid Cyber Triage & SOAR Platform"
- Subtitle explaining it bridges the gap between employees and IT admins
- Two CTA buttons: "See How It Works" (scrolls down) and "View API Docs"
- Background: subtle animated grid or particle effect using the palette colors

### 2. Problem & Solution

Split layout:

**Left — The Problem:**
- SMEs face a critical security gap
- Employees don't report incidents due to fear and confusion
- IT teams are flooded with alerts
- Creates a "silence problem" where threats go unnoticed

**Right — The Solution:**
- AI-guided employee reporting (chat, not forms)
- Automated correlation of user reports + system alerts
- Smart escalation via SMS for critical threats
- Immutable audit trail for compliance

Use icons or small illustrations for each bullet point.

### 3. How It Works (4-Step Pipeline)

A visual workflow showing:

1. **Input & Intake** — Reports from employees (AI chat) and automated tools (EDR, firewalls, AV)
2. **AI Processing & Correlation** — Analyzes reports, checks historical data (same IP within 24h), auto-escalates correlated attacks to CRITICAL
3. **Routing & Action** — Cybersec team assigns tasks (isolate machine, reset credentials), generates final admin report
4. **Immutable Audit Logging** — Every event recorded in tamper-proof database, no PUT/PATCH/DELETE endpoints

Render this as a horizontal or vertical flow with connected nodes, hand-drawn style arrows, and icons.

### 4. Features Grid

Showcase key features in a card grid:

- **AI Employee Chat** — Interactive chat that guides employees through reporting with multiple-choice questions
- **Automated Webhook** — Direct ingestion from EDR, firewalls, antivirus, SOC tools
- **Smart Escalation** — Automatic Twilio SMS alerts for critical/high severity incidents
- **Historical Correlation** — Matches new incidents with same-IP history within 24h window
- **Rule-Based Routing** — Severity and type-based routing with human-in-the-loop fallback
- **Immutable Audit Trail** — Full Law 18-07 compliance, tamper-proof forensic artifacts

### 5. Interactive API Demo

A sandbox section where visitors can see mock API responses. Three tabs:

- **POST /report** — Submit a mock incident, show fake response with incident_id
- **POST /ai/process** — Trigger mock AI processing, show severity escalation
- **GET /incident/{id}** — Show a full mock incident JSON response

Each tab has a "Try it" button that animates a fake loading state then displays mock JSON.

### 6. Dashboard Preview

Show mock screenshots or wireframes of:

- **Monitoring Interface** — Real-time incident dashboard with severity badges, timeline
- **Reporting Interface** — Incident detail view with AI summary, routing info

Style these as browser mockups (rounded frames, shadow) with placeholder content.

### 7. Compliance Section

Highlight **Algeria's Law 18-07** compliance:

- No PUT/PATCH/DELETE endpoints exist in the backend
- All logs are permanent forensic artifacts
- Every action is timestamped and attributed (user, AI, system, admin)

Use a shield or legal icon motif.

### 8. Tech Stack

Display the technology layers in a clean table or row of cards:

- **Backend:** Python, FastAPI
- **Database:** SQLite + SQLAlchemy (immutable config)
- **AI Engine:** Open-source LLMs (DeepSeek V4, GLM-4, MiniMax)
- **Notifications:** Twilio SDK
- **Testing:** Postman MCP verified

### 9. Footer

- Simple footer with "ALTREON — Open-Source AI-Powered Cybersecurity Triage"
- Link to the GitHub repo
- Optional "Built with FastAPI" credit

## Technical Requirements

- **No framework** — pure HTML + CSS + JavaScript (or a single framework if it makes the animations smoother, but keep it lightweight)
- All data is **mock/fake** — no backend calls
- **Smooth scroll animations** — sections fade/slide in as they enter the viewport
- **Responsive** — works on desktop and tablet
- **No emojis**
- **Fast load time** — lazy-load images, minimal dependencies
- The site should feel like a **real SaaS product landing page**, not a hackathon project

## Deliverable

A single `index.html` file (with embedded CSS and JS, or linked to separate files in the same folder) that can be opened directly in a browser. Put everything inside a `frontend/` folder at the project root.

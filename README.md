
# Stylin' — AI-Powered Fashion Discovery Platform

> **See a look you love. Own it.**

[![Status](https://img.shields.io/badge/status-active-brightgreen)](https://github.com)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Overview

**Stylin'** bridges the gap between fashion inspiration and actual purchase. Drop any photo, get matched outfits across every budget — instantly.

The platform solves three core problems:
- **Fragmented search** — no more jumping between tabs and retailers
- **No personalization** — recommendations that actually reflect *your* style
- **Budget mismatch** — every look delivered at every price point, simultaneously

---

## Core Features

| Feature | Description |
|---|---|
| **Vision Scout** | AI image analysis agent — extracts style signals from any photo |
| **Style Curator** | Product + outfit recommendation agent — builds complete looks |
| **Style Persona** | Named style identity (e.g., "The Romantic Minimalist") |
| **Multi-budget Matching** | Every recommendation delivered across budget, mid-range, and splurge tiers |
| **StyleProfile** | Persistent user style data object powering personalization |

---

## Architecture

Stylin' is a **multi-agent AI system** built on the Deploy AI platform.

```
User Input (image / text)
        │
        ▼
┌──────────────────┐
│   Vision Scout   │  ← Image analysis, style signal extraction
│  (AI Agent)      │
└────────┬─────────┘
         │  Style signals
         ▼
┌──────────────────┐
│  Style Curator   │  ← Product matching, outfit building, budget tiering
│  (AI Agent)      │
└────────┬─────────┘
         │  Structured recommendations
         ▼
┌──────────────────┐
│  StyleProfile    │  ← Persistent user style data
│  (Data Layer)    │
└──────────────────┘
         │
         ▼
   User Interface
```

For full architecture documentation, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Agents | Deploy AI (multi-agent orchestration) |
| Backend | Python |
| Auth | OAuth2 Client Credentials |
| API | Deploy AI Core API (`https://core-api.dev.deploy.ai`) |
| Frontend | TBD |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Access to a Deploy AI account (org credentials required)
- `.env` file configured (see below)

### Environment Setup

Create a `.env` file at the project root:

```env
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
AUTH_URL=https://api-auth.dev.deploy.ai/oauth2/token
API_URL=https://core-api.dev.deploy.ai
ORG_ID=your_org_id
```

> **Never commit `.env` to version control.** It is included in `.gitignore`.

### Installation

```bash
git clone https://github.com/your-org/stylin.git
cd stylin
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

---

## Project Structure

```
stylin/
├── agents/
│   ├── vision_scout.py        # Image analysis agent
│   └── style_curator.py       # Product + outfit recommendation agent
├── api/
│   ├── auth.py                # OAuth2 token management
│   ├── chat.py                # Chat session management
│   └── messages.py            # Message sending/receiving
├── models/
│   └── style_profile.py       # StyleProfile data model
├── docs/
│   ├── ARCHITECTURE.md        # Full system architecture
│   ├── API.md                 # API reference
│   ├── brand-voice.md         # Brand voice & tone guidelines
│   └── product-requirements.md # PRD
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── logs/                      # Runtime logs (gitignored)
├── tests/
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── requirements.txt
└── README.md
```

---

## Target Audience

| Persona | Age | What They Need |
|---|---|---|
| Trend Chaser | 18–28 | Fast, culturally fluent recommendations |
| Conscious Stylist | 25–40 | Quality-aware, thoughtful matching |
| Gifter | Any | Guided, confidence-building experience |

---

## Brand Identity

- **Mission:** Make fashion discovery effortless and personal — for every budget, every body, every taste.
- **Vision:** A world where anyone can see a look they love and immediately know how to make it their own.
- **Tone:** Your cool friend who always knows what to wear.

Full brand guidelines: [`docs/brand-voice.md`](docs/brand-voice.md)

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch strategy, commit conventions, and PR process.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

*Stylin' — your style, decoded in seconds.*

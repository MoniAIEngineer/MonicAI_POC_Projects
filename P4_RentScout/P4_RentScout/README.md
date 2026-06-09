# 🏠 RentScout — AI Rental Listing Scout for Germany

> An AI-powered apartment-hunting assistant that scrapes live rental listings, stores and de-duplicates them, and surfaces matches — built on a FastAPI backend with an Apify scraper, Supabase storage, and a Next.js frontend.

**🌐 Live:** [rentscout-ai.de](https://rentscout-ai.de)
**🤖 Delivery:** Web app + Telegram alerts
**🏷️ Type:** AI Agent — scraping + matching pipeline
**📦 Status:** Beta-complete

---

## 📖 Overview

Finding an apartment in Germany — especially in tight markets like Stuttgart — means refreshing listing sites constantly and racing other applicants. **RentScout** automates the hunt: it scrapes real rental listings from portals, stores them in a structured database, and gives users a clean interface to browse matches, with Telegram alerts planned for instant notification of new listings.

The scraping layer uses **Apify** as a managed, maintained scraper rather than brittle hand-rolled HTML parsing, which keeps the pipeline resilient to site changes.

---

## ✨ Key Features

- **🔎 Live listing scraping** — Pulls real rental listings via an Apify actor.
- **🗂️ Structured storage** — Listings normalized and stored in Supabase.
- **🔐 User accounts** — JWT-based authentication for saved searches and preferences.
- **🖥️ Clean browse UI** — Next.js frontend to review matches.
- **📲 Telegram alerts** *(in progress)* — Push notifications for new matching listings.
- **🏷️ Owner listings** *(planned)* — A guided form for owners to post their own listings.

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│   User        │────▶│  Next.js 14  │────▶│   FastAPI       │
│ (Web/Telegram)│     │  Frontend    │     │   Backend       │
└──────────────┘     └──────────────┘     └────────┬────────┘
                                                    │
                       ┌─────────────────────────────┼──────────────────┐
                       │                              │                  │
                 ┌─────▼──────┐            ┌──────────▼──────┐  ┌────────▼────────┐
                 │ ScraperAgent│           │   JWT Auth      │  │    Supabase     │
                 │  → Apify    │           │  (sessions)     │  │   (listings,    │
                 │  (Immowelt) │           │                 │  │    users)       │
                 └────────────┘            └─────────────────┘  └─────────────────┘
```

The **ScraperAgent** calls the Apify actor directly (no multi-agent framework) and writes normalized listings into Supabase.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 |
| **Backend** | FastAPI (Python) |
| **Scraping** | Apify (managed actor) |
| **Auth** | JWT |
| **Database** | Supabase |
| **LLM** | GPT-4o-mini (OpenAI) — listing matching/enrichment |
| **Delivery** | Web + Telegram Bot API |
| **Infra** | Docker + Traefik (Let's Encrypt), Hostinger VPS (Ubuntu 24.04) |

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- A Supabase project
- An Apify account + API token
- API keys for OpenAI and (optionally) a Telegram bot token

### Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd P4_RentScout

# 2. Create your environment file from the template
cp .env.example .env
# → fill in your real keys in .env (never commit this file)

# 3. Run the database migration
#    Apply supabase/migrations.sql in your Supabase SQL editor

# 4. Build and start
docker compose up --build -d
```

---

## 📁 Project Structure

```
P4_RentScout/
├── README.md              # This file
├── .env.example           # Environment variable template (no secrets)
├── .gitignore             # Excludes secrets, build artifacts
├── LICENSE                # MIT
├── docker-compose.yml     # Service orchestration (reference)
├── supabase/
│   └── migrations.sql     # Database schema (users, listings)
├── docs/
│   ├── ARCHITECTURE.md    # Detailed technical design
│   └── SETUP.md           # Step-by-step deployment guide
└── assets/
    └── (screenshots, listing UI)
```

---

## 🔒 Security Note

This repository contains **no live credentials**. All secrets — including the Apify token, JWT secret, and any Telegram token — are referenced through `.env.example` placeholders and excluded via `.gitignore`. Configure your own keys locally.

---

## 📌 Roadmap

- [ ] Increase JWT expiry to 7 days (longer-lived sessions)
- [ ] Connect Telegram alerts for new matching listings
- [ ] Build the owner listing form (guided multi-step flow)
- [ ] Expand beyond Stuttgart to additional German cities
- [ ] AI match scoring (rank listings by user preferences)

---

## 👤 Author

**Monic** — AI/GenAI Engineer | 19+ years enterprise IT background (SAP, data migration)
Based in Sindelfingen, Germany 🇩🇪

Part of a portfolio of AI micro-SaaS products. Built with FastAPI, Next.js, Apify, Supabase, and the OpenAI API.

---

## 📄 License

MIT — see [LICENSE](./LICENSE).

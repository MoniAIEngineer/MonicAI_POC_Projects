# 🏛️ BehördenBot — AI Assistant for German Public Services

> A RAG-powered GenAI assistant that helps people in Germany understand official letters (Behördenbriefe), navigate bureaucratic processes, and get plain-language answers to public-services questions — in multiple languages.

**🌐 Live:** [behoerdenbot.sbs](https://behoerdenbot.sbs)
**🤖 Telegram:** [@BehördenBot_de_bot](https://t.me/)
**💶 Pricing:** €2.99/month (B2C subscription via Dodo Payments)

---

## 📖 Overview

German bureaucracy is notoriously hard to navigate — especially for migrants, students, and non-native speakers. Official letters use dense legal language, and a single misunderstood deadline can mean lost benefits or fines.

**BehördenBot** solves this with a Retrieval-Augmented Generation (RAG) pipeline: users upload a photo or scan of an official letter, the system extracts the text, retrieves relevant context from a curated knowledge base of German public-services information, and returns a clear, actionable explanation.

---

## ✨ Key Features

- **📷 Document OCR** — Upload a photo of any official letter; text is extracted automatically.
- **🧠 RAG-powered answers** — Responses grounded in a curated knowledge base using pgvector semantic search, reducing hallucination.
- **🌍 Multi-language support** — Get explanations in your preferred language, not just German.
- **💬 Telegram delivery** — Interact directly through a Telegram bot, no app install required.
- **💶 Subscription billing** — Integrated Dodo Payments for European B2C monetization.

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   User       │────▶│  Next.js 14  │────▶│   FastAPI       │
│ (Web/Telegram)│    │  Frontend    │     │   Backend       │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          │                         │                        │
                    ┌─────▼──────┐         ┌────────▼────────┐      ┌────────▼────────┐
                    │ pytesseract│         │   GPT-4o-mini   │      │    Supabase     │
                    │   (OCR)    │         │  (generation)   │      │  + pgvector RAG │
                    └────────────┘         └─────────────────┘      └─────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 |
| **Backend** | FastAPI (Python) |
| **OCR** | pytesseract |
| **LLM** | GPT-4o-mini (OpenAI) |
| **Vector DB / RAG** | Supabase + pgvector |
| **Payments** | Dodo Payments |
| **Delivery** | Telegram Bot API |
| **Infra** | Docker + Traefik (Let's Encrypt), Hostinger VPS (Ubuntu 24.04) |

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- A Supabase project with the `pgvector` extension enabled
- API keys for OpenAI, Resend, Dodo Payments, and a Telegram bot token

### Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd P1_BehördenBot

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
P1_BehördenBot/
├── README.md              # This file
├── .env.example           # Environment variable template (no secrets)
├── .gitignore             # Excludes secrets, build artifacts
├── LICENSE                # MIT
├── docker-compose.yml     # Service orchestration (reference)
├── docs/
│   ├── ARCHITECTURE.md    # Detailed technical design
│   └── SETUP.md           # Step-by-step deployment guide
└── assets/
    └── (screenshots, demo images)
```

---

## 🔒 Security Note

This repository contains **no live credentials**. All secrets are referenced through `.env.example` placeholders and excluded via `.gitignore`. Configure your own keys locally.

---

## 📌 Roadmap

- [ ] Expand knowledge base coverage (more Behörden, more letter types)
- [ ] Add deadline-extraction + calendar reminders
- [ ] Support direct document upload via web (in addition to Telegram)
- [ ] Multi-region public-services support

---

## 👤 Author

**Monic** — AI/GenAI Engineer | 19+ years enterprise IT background (SAP, data migration)
Based in Sindelfingen, Germany 🇩🇪

Part of a portfolio of AI micro-SaaS products. Built with FastAPI, Next.js, Supabase, and the OpenAI API.

---

## 📄 License

MIT — see [LICENSE](./LICENSE).

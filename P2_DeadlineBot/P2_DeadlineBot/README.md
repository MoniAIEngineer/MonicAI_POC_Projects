# ⏰ DeadlineBot — AI Deadline Tracker & Reminder Automation

> An AI-powered automation that captures deadlines from natural-language messages (text or voice), stores them, and sends timely reminders — built on an N8N workflow backbone with a FastAPI + Next.js layer.

**🌐 Live:** [deadlinebot.sbs](https://deadlinebot.sbs)
**🤖 Delivery:** Telegram bot
**🏷️ Type:** AI Automation (N8N) — portfolio / assignment project (no payments)

---

## 📖 Overview

Keeping track of deadlines — bills, appointments, application cut-offs, renewals — is tedious, and most reminder apps require manual structured entry. **DeadlineBot** lets users just *say* or *type* what's due and when, in plain language. The system parses the intent, extracts the deadline, stores it, and an N8N workflow fires reminders at the right time.

This project demonstrates AI-driven workflow automation: combining speech-to-text, LLM intent extraction, a database, and a scheduled N8N orchestration into one hands-off pipeline.

---

## ✨ Key Features

- **🗣️ Voice & text input** — Send a voice note or a text message; both are understood.
- **🎙️ Speech-to-text** — OpenAI Whisper transcribes voice notes before parsing.
- **🧠 Natural-language deadline extraction** — GPT-4o-mini pulls out *what* is due and *when* from free-form input.
- **🔁 Automated reminders** — An N8N workflow runs on schedule and dispatches reminders via Telegram.
- **💾 Persistent storage** — Deadlines stored in Supabase.

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│   User        │────▶│  Next.js 14  │────▶│   FastAPI       │
│  (Telegram)   │     │  Frontend    │     │   Backend       │
└──────────────┘     └──────────────┘     └────────┬────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────┐
                    │                                │                   │
              ┌─────▼──────┐              ┌──────────▼──────┐   ┌────────▼────────┐
              │  Whisper   │              │   GPT-4o-mini   │   │    Supabase     │
              │ (voice→text)│             │ (extract deadline)│  │   (deadlines)   │
              └────────────┘              └─────────────────┘   └────────┬────────┘
                                                                         │
                                                              ┌──────────▼──────────┐
                                                              │   N8N Workflow       │
                                                              │ (scheduled reminders)│
                                                              └──────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 |
| **Backend** | FastAPI (Python) |
| **Speech-to-text** | OpenAI Whisper |
| **LLM** | GPT-4o-mini (OpenAI) |
| **Automation** | N8N (self-hosted) workflows |
| **Database** | Supabase |
| **Delivery** | Telegram Bot API |
| **Infra** | Docker + Traefik (Let's Encrypt), Hostinger VPS (Ubuntu 24.04) |

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- A Supabase project
- A self-hosted N8N instance
- API keys for OpenAI and a Telegram bot token

### Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd P2_DeadlineBot

# 2. Create your environment file from the template
cp .env.example .env
# → fill in your real keys in .env (never commit this file)

# 3. Run the database migration
#    Apply supabase/migrations.sql in your Supabase SQL editor

# 4. Import the N8N workflow
#    In N8N: Import → n8n/deadline_reminders_workflow.json
#    Set the N8N_WEBHOOK_URL in .env to match

# 5. Build and start
docker compose up --build -d
```

---

## 📁 Project Structure

```
P2_DeadlineBot/
├── README.md              # This file
├── .env.example           # Environment variable template (no secrets)
├── .gitignore             # Excludes secrets, build artifacts
├── LICENSE                # MIT
├── docker-compose.yml     # Service orchestration (reference)
├── n8n/
│   └── deadline_reminders_workflow.json  # Importable N8N workflow
├── supabase/
│   └── migrations.sql     # Database schema
├── docs/
│   ├── ARCHITECTURE.md    # Detailed technical design
│   └── SETUP.md           # Step-by-step deployment guide
└── assets/
    └── (screenshots, workflow diagram)
```

---

## 🔒 Security Note

This repository contains **no live credentials**. All secrets are referenced through `.env.example` placeholders and excluded via `.gitignore`. Configure your own keys locally.

---

## 📌 Roadmap

- [ ] Recurring-deadline support (weekly/monthly)
- [ ] Snooze + reschedule via reply
- [ ] Multi-channel reminders (email via Resend, in addition to Telegram)
- [ ] Natural-language editing of existing deadlines

---

## 👤 Author

**Monic** — AI/GenAI Engineer | 19+ years enterprise IT background (SAP, data migration)
Based in Sindelfingen, Germany 🇩🇪

Part of a portfolio of AI micro-SaaS products. Built with FastAPI, Next.js, N8N, Supabase, and the OpenAI API.

---

## 📄 License

MIT — see [LICENSE](./LICENSE).

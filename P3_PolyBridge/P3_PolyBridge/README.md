# 🌐 PolyBridge — AI Universal Translation Bot

> A Telegram bot that translates **text, voice, and images** between languages in real time — built entirely on self-hosted N8N workflows, with speech-to-text, vision OCR, LLM translation, and text-to-speech wired together end to end.

**🤖 Telegram:** [@PolyBridgeAIBot](https://t.me/PolyBridgeAIBot)
**🏷️ Type:** AI Automation (N8N) — multi-modal translation pipeline
**📦 Status:** Phase 1 live · Phase 2A in planning

---

## 📖 Overview

Most translation bots handle text only. **PolyBridge** is multi-modal: send it a voice note, a photo of a sign or menu, or plain text, and it returns a translation — and can speak the result back to you. It's designed for travelers, migrants, and anyone bridging a language gap on the go.

The entire pipeline runs on **self-hosted N8N**, demonstrating that a production multi-modal AI service can be orchestrated visually without a traditional backend codebase. Each external capability (Telegram, Whisper, GPT-4o-mini, vision, TTS) is called via direct HTTP Request nodes.

---

## ✨ Key Features

- **💬 Text translation** — Send text, get it translated into the target language.
- **🎙️ Voice translation** — Send a voice note; Whisper transcribes it, then it's translated. Optional spoken reply via TTS.
- **📷 Image translation** — Send a photo (sign, menu, document); text is read and translated.
- **🗣️ Onboarding & language selection** — First-run flow sets the user's preferred language.
- **🚦 Rate limiting** — 20 translations/day per user to control cost.
- **🛡️ Centralized error handling** — A dedicated error workflow catches and reports failures.

---

## 🏗️ Architecture — Three Workflows

PolyBridge is split into three N8N workflows with clear separation of duties:

```
┌─────────────────────────────────────────────────────────────┐
│  Workflow A — Onboarding & Language                           │
│  Handles first-run setup and user language preferences.       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Workflow B — Translation Core   ◀── SOLE Telegram Trigger    │
│                                                               │
│   Telegram Trigger                                            │
│        │                                                      │
│        ├── text  ──────────────▶ GPT-4o-mini (translate)      │
│        ├── voice ── Whisper ───▶ GPT-4o-mini ──▶ TTS (opt.)   │
│        └── photo ── Vision OCR ▶ GPT-4o-mini (translate)      │
│        │                                                      │
│        └──▶ Telegram sendMessage / sendVoice                  │
│                                                               │
│   Rate limit: 20/day per user                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Workflow C — Error Handler                                   │
│  Catches failures from A & B, logs and notifies.              │
└─────────────────────────────────────────────────────────────┘
```

> **⚠️ Hard rule (Phase 1):** **One webhook per bot.** Only **Workflow B** holds the Telegram Trigger node. Workflows A and C are invoked internally — they must **not** register their own Telegram webhook, or they will collide with B and break delivery.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Orchestration** | N8N (self-hosted) — three workflows |
| **Messaging** | Telegram Bot API (HTTP Request nodes) |
| **Speech-to-text** | OpenAI Whisper |
| **Translation LLM** | GPT-4o-mini (OpenAI) |
| **Image text** | Vision OCR via OpenAI |
| **Text-to-speech** | OpenAI TTS |
| **Infra** | Docker + Traefik (Let's Encrypt), Hostinger VPS (Ubuntu 24.04) |

---

## 🚀 Getting Started

### Prerequisites
- A self-hosted N8N instance
- An OpenAI API key (Whisper + GPT-4o-mini + Vision + TTS)
- A Telegram bot token

### Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd P3_PolyBridge

# 2. Import the three workflows into N8N, in order:
#    n8n/workflow-a-onboarding.json
#    n8n/workflow-b-translation.json   ← holds the Telegram Trigger
#    n8n/workflow-c-error-handler.json

# 3. Re-create credentials inside N8N (Telegram, OpenAI).
#    Do NOT hardcode tokens in the JSON.

# 4. Activate ONLY Workflow B's Telegram Trigger.
#    Confirm the webhook registers under your bot token.
```

---

## 📁 Project Structure

```
P3_PolyBridge/
├── README.md              # This file
├── .env.example           # Reference config (no secrets)
├── .gitignore             # Excludes secrets, build artifacts
├── LICENSE                # MIT
├── n8n/
│   ├── workflow-a-onboarding.json     # Onboarding & language
│   ├── workflow-b-translation.json    # Translation core (sole trigger)
│   └── workflow-c-error-handler.json  # Error handling
├── docs/
│   ├── ARCHITECTURE.md    # Detailed three-workflow design
│   ├── SETUP.md           # Import & deployment guide
│   └── WEBHOOK_NOTES.md   # The one-webhook-per-bot rule + token rotation
└── assets/
    └── (screenshots, workflow canvas)
```

---

## 🔒 Security Note

This repository contains **no live credentials**. The workflow JSON files are skeletons with credentials stripped; the `.env.example` lists configuration references only. Configure your own keys inside N8N.

> If a bot token is ever rotated, the Telegram Trigger node on Workflow B must re-register the webhook under the new token. See [docs/WEBHOOK_NOTES.md](./docs/WEBHOOK_NOTES.md).

---

## 📌 Roadmap

- [ ] **Phase 2A** — expanded language handling, richer onboarding
- [ ] Admin chat IDs exempt from the daily rate limit
- [ ] Auto-detect source language
- [ ] Conversation mode (back-and-forth two-language sessions)
- [ ] Inline-query translation

---

## 👤 Author

**Monic** — AI/GenAI Engineer | 19+ years enterprise IT background (SAP, data migration)
Based in Sindelfingen, Germany 🇩🇪

Part of a portfolio of AI micro-SaaS products. Built on self-hosted N8N with the OpenAI API.

---

## 📄 License

MIT — see [LICENSE](./LICENSE).

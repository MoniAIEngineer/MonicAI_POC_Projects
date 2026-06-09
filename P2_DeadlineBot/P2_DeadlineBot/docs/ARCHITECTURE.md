# Architecture — DeadlineBot

## System Overview

DeadlineBot is an AI-driven automation that turns free-form messages into tracked deadlines and dispatches reminders automatically. The defining design choice is using **N8N as the scheduling and orchestration backbone** rather than building a custom cron service — the workflow is visual, editable, and decoupled from the application code.

## Two Flows

### 1. Capture flow (event-driven)
1. **Input** — A user sends a text or voice message to the Telegram bot.
2. **Transcription** — If it's a voice note, OpenAI Whisper converts it to text.
3. **Extraction** — GPT-4o-mini parses the text and extracts a structured deadline: a title and a due timestamp.
4. **Storage** — The deadline is written to the `deadlines` table in Supabase.

### 2. Reminder flow (scheduled, N8N)
1. **Schedule trigger** — An N8N schedule node fires at a fixed interval (e.g. every 15 minutes).
2. **Query** — It reads deadlines that are due soon and not yet reminded.
3. **Dispatch** — For each, it sends a Telegram reminder.
4. **Mark sent** — It updates `reminder_sent = true` to avoid duplicate reminders.

## Why N8N

- **Separation of concerns** — Reminder timing logic lives outside the app; it can be edited without redeploying.
- **Observability** — N8N's execution log shows exactly which reminders fired and why.
- **Extensibility** — Adding an email channel or a Slack reminder is a node, not a code change.

## Components

### Frontend (Next.js 14)
Lightweight web surface; the primary interface is the Telegram bot.

### Backend (FastAPI)
Receives Telegram updates, runs Whisper transcription and GPT-4o-mini extraction, persists deadlines.

### Automation (N8N, self-hosted)
Owns the scheduled reminder workflow. Imported from `n8n/deadline_reminders_workflow.json`.

### Database (Supabase)
Stores users and deadlines. Indexed on `due_at` for unsent deadlines so the workflow query stays cheap.

## Infrastructure

- **Host:** Hostinger VPS, Ubuntu 24.04
- **Containerization:** Docker Compose
- **Reverse proxy / TLS:** Traefik with Let's Encrypt (`mytlschallenge` resolver)
- **Network:** shared external `n8n_default` Docker network
- **DNS:** Cloudflare in DNS-only (grey cloud) mode

## Data Model (Supabase)

| Table | Purpose |
|-------|---------|
| `users` | User accounts + Telegram IDs |
| `deadlines` | Tracked deadlines, due times, reminder state |

## Security Considerations

- Secrets injected via environment variables, never committed.
- The N8N workflow JSON in this repo is a **skeleton** — credentials are recreated inside the N8N instance, not stored in the file.
- Supabase service-role keys use the legacy `eyJ` JWT format for compatibility.

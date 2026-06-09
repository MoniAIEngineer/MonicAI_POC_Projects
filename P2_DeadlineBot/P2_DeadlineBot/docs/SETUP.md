# Setup & Deployment — DeadlineBot

This guide walks through deploying DeadlineBot from scratch.

## 1. Prerequisites

- A Linux VPS (tested on Ubuntu 24.04)
- Docker and Docker Compose installed
- A running, self-hosted N8N instance
- A domain pointed at your server (DNS-only / grey cloud if using Cloudflare + Traefik)
- A running Traefik instance on an external Docker network
- Accounts/keys for: OpenAI, Supabase, Telegram

## 2. Supabase Setup

1. Open your Supabase project (this bot shares the portfolio project).
2. Open the SQL editor and run `supabase/migrations.sql`.
3. Copy your project URL and the legacy `eyJ` service-role key.

> **Note:** Use the legacy `eyJ` JWT key format, not the newer `sb_secret_` format, for `supabase-py` compatibility.

## 3. Environment Configuration

```bash
cp .env.example .env
```

Fill in every value in `.env`:
- OpenAI key + model (`gpt-4o-mini`) + Whisper model
- Supabase URL + service key + anon key
- `N8N_WEBHOOK_URL` (matching your N8N instance)
- Telegram bot token

## 4. Import the N8N Workflow

1. In your N8N instance: **Import from File** → `n8n/deadline_reminders_workflow.json`.
2. Re-create the Postgres (Supabase) and HTTP credentials inside N8N — the JSON ships **without** secrets.
3. Adjust the schedule interval and the reminder window to your preference.
4. Activate the workflow.

## 5. Cloudflare / DNS

If using Cloudflare, set the domain record to **DNS-only (grey cloud)** so Traefik's Let's Encrypt challenge succeeds. Set Cloudflare SSL mode to **Full**.

## 6. Build & Launch

```bash
docker compose up --build -d
```

Verify services:

```bash
docker compose ps
docker compose logs -f deadlinebot-backend
```

## 7. Telegram Webhook

Register the bot webhook against your live HTTPS domain so Telegram delivers updates to the backend.

## 8. Smoke Test

- Send a text deadline ("Pay rent on the 1st") via Telegram → confirm it's stored.
- Send a voice note → confirm Whisper transcription + extraction.
- Wait for (or manually trigger) the N8N workflow → confirm a reminder fires and `reminder_sent` flips to true.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| TLS cert won't issue | Cloudflare proxy enabled — switch to DNS-only |
| `supabase-py` auth errors | Using `sb_secret_` key instead of `eyJ` format |
| Reminders never fire | N8N workflow not activated, or wrong DB credentials |
| Duplicate reminders | `Mark Reminder Sent` step failing — check the update query |
| Telegram not responding | Webhook not registered under current bot token |

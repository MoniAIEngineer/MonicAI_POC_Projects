# Setup & Deployment — BehördenBot

This guide walks through deploying BehördenBot from scratch.

## 1. Prerequisites

- A Linux VPS (tested on Ubuntu 24.04)
- Docker and Docker Compose installed
- A domain pointed at your server (DNS-only / grey cloud if using Cloudflare + Traefik)
- A running Traefik instance on an external Docker network
- Accounts/keys for: OpenAI, Supabase, Resend, Dodo Payments, Telegram

## 2. Supabase Setup

1. Create a Supabase project.
2. Enable the `pgvector` extension (Database → Extensions).
3. Open the SQL editor and run `supabase/migrations.sql`.
4. Copy your project URL and the legacy `eyJ` service-role key.

> **Note:** Use the legacy `eyJ` JWT key format, not the newer `sb_secret_` format, for `supabase-py` compatibility.

## 3. Environment Configuration

```bash
cp .env.example .env
```

Fill in every value in `.env`:
- OpenAI key + model (`gpt-4o-mini`)
- Supabase URL + service key + anon key
- Resend key + from-address
- Telegram bot token
- Dodo API key, product ID, webhook secret

## 4. Cloudflare / DNS

If using Cloudflare, set the domain record to **DNS-only (grey cloud)**. Traefik's Let's Encrypt challenge will fail if the proxy (orange cloud) is enabled. Set Cloudflare SSL mode to **Full**.

## 5. Build & Launch

```bash
docker compose up --build -d
```

Verify both services are healthy:

```bash
docker compose ps
docker compose logs -f behoerdenbot-backend
```

## 6. Telegram Webhook

Register the bot webhook against your live HTTPS domain so Telegram delivers updates to the backend.

## 7. Smoke Test

- Send a test letter photo via Telegram → confirm OCR + RAG response.
- Trigger a test subscription via Dodo → confirm webhook updates user entitlement.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| TLS cert won't issue | Cloudflare proxy enabled — switch to DNS-only |
| `supabase-py` auth errors | Using `sb_secret_` key instead of `eyJ` format |
| Telegram not responding | Webhook not registered under current bot token |
| Service name conflict | Container name not unique on `n8n_default` |

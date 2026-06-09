# Setup & Deployment — RentScout

This guide walks through deploying RentScout from scratch.

## 1. Prerequisites

- A Linux VPS (tested on Ubuntu 24.04)
- Docker and Docker Compose installed
- A Supabase project
- An Apify account with an API token
- A domain pointed at your server (DNS-only / grey cloud if using Cloudflare + Traefik)
- A running Traefik instance on an external Docker network
- API keys for OpenAI; optionally a Telegram bot token for alerts

## 2. Supabase Setup

1. Open your Supabase project.
2. Open the SQL editor and run `supabase/migrations.sql`.
3. Copy your project URL and the legacy `eyJ` service-role key.

> **Note:** Use the legacy `eyJ` JWT key format, not the newer `sb_secret_` format, for `supabase-py` compatibility.

## 3. Apify Setup

1. Create an Apify account and copy your API token.
2. Note the actor: `azzouzana~immowelt-de-search-results-scraper-by-search-url`.
3. Build a search URL on the rental portal for your target city/filters and set it as `APIFY_SEARCH_URL`.

## 4. Environment Configuration

```bash
cp .env.example .env
```

Fill in every value in `.env`:
- OpenAI key + model (`gpt-4o-mini`)
- Supabase URL + service key + anon key
- Apify token + actor + search URL
- `JWT_SECRET` (long random string) + `JWT_EXPIRY_MINUTES`
- Telegram bot token (optional)

## 5. Cloudflare / DNS

If using Cloudflare, set the domain record to **DNS-only (grey cloud)** so Traefik's Let's Encrypt challenge succeeds. Set Cloudflare SSL mode to **Full**.

## 6. Build & Launch

```bash
docker compose up --build -d
```

Verify services:

```bash
docker compose ps
docker compose logs -f rentscout-backend
```

## 7. Seed Listings

Trigger the ScraperAgent once to populate the `listings` table from your configured search URL. Confirm rows appear in Supabase and that `external_id` de-duplication works on a second run (no duplicates).

## 8. Smoke Test

- Register / sign in → confirm a JWT is issued and accepted.
- Browse listings → confirm scraped data renders.
- (If configured) confirm Telegram alerts fire for new listings.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| TLS cert won't issue | Cloudflare proxy enabled — switch to DNS-only |
| `supabase-py` auth errors | Using `sb_secret_` key instead of `eyJ` format |
| Sessions expire too fast | `JWT_EXPIRY_MINUTES` too low — increase it |
| No listings appear | Apify token/actor/search URL misconfigured |
| Duplicate listings | `external_id` not set on upsert — check the normalize step |

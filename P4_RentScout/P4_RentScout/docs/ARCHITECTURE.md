# Architecture — RentScout

## System Overview

RentScout is an AI agent that automates apartment hunting. Unlike a pure chatbot, its core job is a **data pipeline**: scrape live rental listings, normalize and de-duplicate them, store them, and present matches to authenticated users. The design favors a managed scraper (Apify) over fragile custom HTML parsing, and a single-purpose ScraperAgent over a heavyweight multi-agent framework.

## Request & Data Flow

### Browsing flow
1. **Auth** — A user signs in; the backend issues a JWT.
2. **Query** — The frontend requests listings (optionally filtered by saved search).
3. **Serve** — FastAPI returns normalized listings from Supabase.

### Scraping flow
1. **Trigger** — The ScraperAgent runs (on demand or scheduled) against a configured search URL.
2. **Scrape** — It calls the Apify actor (`immowelt-de-search-results-scraper-by-search-url`).
3. **Normalize** — Raw results are mapped to the `listings` schema (rent, rooms, size, address, url).
4. **De-duplicate** — Listings are upserted by `external_id` so the same listing isn't stored twice.
5. **Store** — Clean records land in Supabase.
6. **Alert** *(planned)* — New matches trigger Telegram notifications.

## Why Apify

- **Resilience** — The actor is maintained against portal HTML changes, so the pipeline doesn't break every time a site tweaks its markup.
- **Speed to build** — No need to write and maintain a bespoke scraper.
- **Direct call** — The ScraperAgent calls Apify directly; there's no AutoGen or multi-agent overhead for what is fundamentally a single tool-use step.

## Components

### Frontend (Next.js 14)
Sign-in, saved searches, and the listing browse experience.

### Backend (FastAPI)
Auth (JWT), listing endpoints, and the ScraperAgent that drives Apify and writes to Supabase.

### Scraper (Apify actor)
Pulls live listings from the rental portal for a given search URL.

### Database (Supabase)
Stores `users`, `searches`, and `listings`. The `external_id` unique constraint enforces de-duplication.

## Auth Notes

JWT-based sessions. The token lifetime is configurable via `JWT_EXPIRY_MINUTES`; the roadmap moves this to 7 days for a smoother user experience (avoiding frequent re-logins during an active apartment search).

## Infrastructure

- **Host:** Hostinger VPS, Ubuntu 24.04
- **Containerization:** Docker Compose
- **Reverse proxy / TLS:** Traefik with Let's Encrypt (`mytlschallenge` resolver)
- **Network:** shared external `n8n_default` Docker network
- **DNS:** Cloudflare in DNS-only (grey cloud) mode

## Data Model (Supabase)

| Table | Purpose |
|-------|---------|
| `users` | Accounts + credentials + optional Telegram ID |
| `searches` | Saved search preferences |
| `listings` | Scraped, normalized, de-duplicated listings |

## Security Considerations

- All secrets (Apify token, JWT secret, Supabase keys) injected via environment variables, never committed.
- Passwords stored as hashes, never plaintext.
- Supabase service-role keys use the legacy `eyJ` JWT format for compatibility.

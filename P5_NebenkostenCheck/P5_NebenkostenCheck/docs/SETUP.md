# Setup & Deployment — NebenkostenCheck

This guide walks through deploying NebenkostenCheck from scratch.

## 1. Prerequisites

- A Linux VPS (tested on Ubuntu 24.04)
- Docker and Docker Compose installed
- A Supabase project
- An Anthropic API key (Claude)
- A Dodo Payments account (for paid mode; KYC required for payouts)
- A domain pointed at your server (DNS-only / grey cloud if using Cloudflare + Traefik)
- A running Traefik instance on an external Docker network

## 2. Supabase Setup

1. Open your Supabase project.
2. Open the SQL editor and run `supabase/migrations.sql`.
3. Copy your project URL and the legacy `eyJ` service-role key.

> **Note:** Use the legacy `eyJ` JWT key format, not the newer `sb_secret_` format, for `supabase-py` compatibility.

## 3. Environment Configuration

```bash
cp .env.example .env
```

Fill in every value in `.env`:
- Anthropic key + model
- Supabase URL + service key + anon key
- Dodo key, product ID, webhook secret, **and `DODO_WEBHOOK_PATH`**
- `FREE_BETA` (keep `true` for beta)
- Resend key (optional, for emailing reports)

## 4. Cloudflare / DNS

If using Cloudflare, set the domain record to **DNS-only (grey cloud)** so Traefik's Let's Encrypt challenge succeeds. Set Cloudflare SSL mode to **Full**.

## 5. Build & Launch

```bash
docker compose up --build -d
```

Verify services (note the `nkc-` names):

```bash
docker compose ps
docker compose logs -f nkc-backend
```

## 6. Smoke Test (Free Beta)

- Upload a sample *Nebenkostenabrechnung* PDF.
- Provide an email at the capture gate.
- Confirm the analysis renders charge-by-charge with any red flags.

## 7. Going Paid — Launch Checklist

Do these in order when ready to charge:

1. ✅ Confirm Dodo **KYC is approved**.
2. ✅ Verify `DODO_WEBHOOK_PATH` in `.env` **exactly matches** the backend route and the path configured in the Dodo dashboard.
3. ✅ Run a test payment in Dodo's test mode → confirm the webhook fires and the user is unlocked.
4. ✅ Set `FREE_BETA=false` **explicitly**.
5. ✅ Redeploy and do one real end-to-end paid test.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| TLS cert won't issue | Cloudflare proxy enabled — switch to DNS-only |
| `supabase-py` auth errors | Using `sb_secret_` key instead of `eyJ` format |
| Docker service name conflict | Use the `nkc-` prefixed names; they must be unique on the network |
| Paid users not unlocked | `DODO_WEBHOOK_PATH` mismatch — align dashboard ↔ backend route |
| Product gives away paid analyses | `FREE_BETA` not set to `false` |
| Analyses lost on restart | Sessions still in-memory — move to Supabase (roadmap) |

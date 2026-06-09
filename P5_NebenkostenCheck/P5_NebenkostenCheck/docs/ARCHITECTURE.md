# Architecture — NebenkostenCheck

## System Overview

NebenkostenCheck is a micro-SaaS that turns a German utility-bill PDF into a structured legal analysis. The pipeline is: extract the PDF, run a legal analysis with Claude against the relevant statutes, return a charge-by-charge report, and (in paid mode) gate the full result behind a one-time payment.

Unlike the other portfolio projects, this is a **real product with paying customers**, so the design pays particular attention to the free-beta → paid transition and to payment-webhook correctness.

## Request Flow

1. **Upload** — A tenant uploads their *Nebenkostenabrechnung* PDF through the Next.js frontend.
2. **Extract** — The FastAPI backend uses PyMuPDF to extract text and line items, handling multi-page statements.
3. **Analyze** — The extracted content is sent to the Claude API with a prompt grounded in German operating-cost law. Claude returns a structured analysis: per-charge explanations, allocability judgments, and red flags.
4. **Gate** —
   - **Free beta** (`FREE_BETA=true`): an email-capture gate; the analysis is shown after the email is provided.
   - **Paid** (`FREE_BETA=false`): the full report is unlocked after a €19 Dodo payment.
5. **Persist** — Users, analyses, and payments are recorded in Supabase.

## Why Claude for the Analysis

The task is legal reasoning over unstructured text — interpreting whether each charge is allocable under §2 BetrKV, §556 BGB, HeizkostenV, and CO2KostAufG. This benefits from a model strong at careful, grounded reasoning and at producing structured output that maps cleanly onto a per-charge report.

## The Free-Beta → Paid Transition

This is the most operationally sensitive part of the product:

- **`FREE_BETA` must be set explicitly to `false`** at launch. Leaving it unset or true means the product gives away paid analyses.
- **Dodo webhook path alignment.** The path Dodo posts to (`DODO_WEBHOOK_PATH`) must exactly match the backend route. A mismatch means payments succeed but the app never learns about them, so the user is charged without being unlocked.
- **KYC.** Dodo payouts require KYC approval before paid mode is meaningful.

## Sessions

Analysis sessions are currently held in memory. The roadmap moves them to the `analyses` table in Supabase so results survive restarts and can be revisited by the user.

## Components

### Frontend (Next.js 14)
Upload UI, email-capture gate (free beta), payment hand-off (paid), and report display.

### Backend (FastAPI)
PDF extraction, Claude analysis, payment-webhook handling, persistence.

### PDF extraction (PyMuPDF)
Robust text extraction across multi-page statements.

### Legal analysis (Claude API)
Grounded analysis against German operating-cost statutes.

### Payments (Dodo)
€19 one-time. Webhook updates payment + unlock state.

### Database (Supabase)
`users`, `analyses`, `payments`.

## Infrastructure

- **Host:** Hostinger VPS, Ubuntu 24.04
- **Containerization:** Docker Compose; services named `nkc-frontend` / `nkc-backend` to avoid Docker DNS name collisions on the shared network
- **Reverse proxy / TLS:** Traefik with Let's Encrypt (`mytlschallenge` resolver)
- **Network:** shared external `n8n_default` Docker network
- **DNS:** Cloudflare in DNS-only (grey cloud) mode

## Data Model (Supabase)

| Table | Purpose |
|-------|---------|
| `users` | Email capture + paid status |
| `analyses` | Analysis sessions + structured results |
| `payments` | Dodo payment records |

## Security Considerations

- All secrets (Anthropic, Supabase, Dodo) injected via environment variables, never committed.
- Webhook signatures verified via the Dodo webhook secret.
- Supabase service-role keys use the legacy `eyJ` JWT format for compatibility.

# Architecture — BehördenBot

## System Overview

BehördenBot is a Retrieval-Augmented Generation (RAG) application. It combines optical character recognition, semantic retrieval, and a large language model to turn confusing German official letters into clear, actionable guidance.

## Request Flow

1. **Input** — A user submits an official letter, either as a photo via the Telegram bot or through the web interface.
2. **OCR** — `pytesseract` extracts raw text from the image.
3. **Embedding & retrieval** — The extracted text is embedded and used to query a `pgvector` index in Supabase. The top relevant knowledge-base chunks (about German public-services processes, common letter types, and required actions) are retrieved.
4. **Generation** — The retrieved context plus the user's letter text are passed to GPT-4o-mini, which produces a grounded, plain-language explanation in the user's chosen language.
5. **Delivery** — The response is returned through Telegram or the web frontend.

## Why RAG

A plain LLM tends to hallucinate specifics about bureaucratic processes (deadlines, office names, required documents). Grounding generation in a curated knowledge base keeps answers accurate and reduces the risk of giving users wrong procedural advice.

## Components

### Frontend (Next.js 14)
Handles the web experience, subscription onboarding, and document upload.

### Backend (FastAPI)
Orchestrates OCR, retrieval, generation, billing webhooks, and the Telegram integration.

### Vector store (Supabase + pgvector)
Stores embedded knowledge-base content and supports cosine-similarity search for retrieval. The knowledge base is curated and versioned separately.

### Payments (Dodo Payments)
Manages the €2.99/month B2C subscription. Webhooks update user entitlement state.

## Infrastructure

- **Host:** Hostinger VPS, Ubuntu 24.04
- **Containerization:** Docker Compose
- **Reverse proxy / TLS:** Traefik with Let's Encrypt (`mytlschallenge` resolver)
- **Network:** shared external `n8n_default` Docker network
- **DNS:** Cloudflare in DNS-only (grey cloud) mode so Traefik can complete the ACME challenge

## Data Model (Supabase)

| Table | Purpose |
|-------|---------|
| `users` | User accounts, subscription status |
| `letters` | Processed letter records |
| `letter_templates` | Curated knowledge-base content (embedded) |

## Security Considerations

- All secrets are injected via environment variables, never committed.
- Supabase service-role keys use the legacy `eyJ` JWT format for `supabase-py` compatibility.
- TLS termination at Traefik; Cloudflare SSL set to Full.

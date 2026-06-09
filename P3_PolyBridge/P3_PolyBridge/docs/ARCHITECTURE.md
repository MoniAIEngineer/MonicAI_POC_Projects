# Architecture — PolyBridge

## System Overview

PolyBridge is a multi-modal translation bot built entirely on **self-hosted N8N**. There is no traditional application backend — every capability is an HTTP Request node calling an external API (Telegram, OpenAI). The system is deliberately split into three workflows with distinct responsibilities, which keeps the translation core clean and isolates onboarding and error handling.

## The Three Workflows

### Workflow A — Onboarding & Language
Handles the first-run experience: greeting new users, prompting for a preferred language, and persisting that choice. It is **invoked internally** (via an Execute Workflow trigger) rather than listening to Telegram directly.

### Workflow B — Translation Core
The heart of the system and the **only** workflow with a Telegram Trigger node.

Flow:
1. **Telegram Trigger** receives an incoming message.
2. **Rate Limit** enforces 20 translations/day per user (admin IDs exempt — Phase 2A).
3. **Route by Type** branches on the message type:
   - **text** → straight to translation
   - **voice** → Whisper transcription → translation
   - **photo** → Vision OCR → translation
4. **Translate (GPT-4o-mini)** renders the content in the user's target language.
5. **TTS (optional)** can voice the result back.
6. **Reply to User** sends the translation via Telegram.

### Workflow C — Error Handler
Registered as the Error Workflow for A and B. It catches failures, formats the error context, and notifies an admin chat. It does not listen to Telegram.

## The One-Webhook-Per-Bot Rule

A Telegram bot can have exactly **one** registered webhook. If more than one workflow registered a Telegram Trigger for the same bot token, they would fight over that single webhook and delivery would break.

**Therefore:** only Workflow B holds the Telegram Trigger. Workflows A and C are reached internally or via the error-workflow mechanism. This is a hard Phase 1 invariant — see `WEBHOOK_NOTES.md` for the token-rotation implications.

## Why N8N (no backend)

- **Visual orchestration** — the entire multi-modal pipeline is inspectable at a glance.
- **Per-node observability** — every API call's input/output is visible in the execution log, which is invaluable when debugging a transcription or translation step.
- **Fast iteration** — adding TTS or a new input type is wiring, not a redeploy.

## External Services (via HTTP Request nodes)

| Capability | Endpoint |
|-----------|----------|
| Messaging | Telegram Bot API |
| Speech-to-text | OpenAI Whisper |
| Translation | OpenAI Chat Completions (GPT-4o-mini) |
| Image text | OpenAI Vision |
| Text-to-speech | OpenAI TTS |

## Infrastructure

- **Host:** Hostinger VPS, Ubuntu 24.04
- **N8N:** self-hosted, behind Traefik
- **Reverse proxy / TLS:** Traefik with Let's Encrypt
- **Network:** shared external `n8n_default` Docker network

## Security Considerations

- All credentials live inside N8N's credential store, never in the workflow JSON.
- The workflow JSONs in this repo are **skeletons** with tokens stripped.
- Bot-token rotation requires the Workflow B trigger to re-register the webhook (see `WEBHOOK_NOTES.md`).

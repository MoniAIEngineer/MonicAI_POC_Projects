# Setup & Deployment — PolyBridge

This guide covers importing and running PolyBridge on a self-hosted N8N instance.

## 1. Prerequisites

- A running, self-hosted N8N instance (behind HTTPS)
- An OpenAI API key with access to Whisper, GPT-4o-mini, Vision, and TTS
- A Telegram bot token (from @BotFather)

## 2. Create Credentials in N8N

Before importing, create these credentials in N8N so the imported nodes can bind to them:
- **Telegram API** — your bot token
- **OpenAI / HTTP Header Auth** — your OpenAI API key

> Credentials are **never** stored in the workflow JSON. The imported files reference credentials by name; you re-create them locally.

## 3. Import the Workflows

Import all three, in this order:

1. `n8n/workflow-a-onboarding.json`
2. `n8n/workflow-b-translation.json` ← holds the Telegram Trigger
3. `n8n/workflow-c-error-handler.json`

## 4. Wire the Workflows Together

- In **Workflow B**, point the internal "Execute Workflow" calls at Workflow A where onboarding is needed.
- In **Workflow A** and **Workflow B** settings, set the **Error Workflow** to Workflow C.

## 5. Activate — Carefully

- Activate **Workflow B only** for Telegram delivery. Its Telegram Trigger registers the single webhook for the bot.
- Do **not** add a Telegram Trigger to A or C. (See `WEBHOOK_NOTES.md`.)

## 6. Verify the Webhook

After activating Workflow B, confirm Telegram has the webhook registered:

```
https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

The returned URL should point at your N8N instance.

## 7. Smoke Test

- Send `/start` → onboarding prompt appears, language can be set.
- Send text → translated reply.
- Send a voice note → transcribed, translated (and optionally spoken back).
- Send a photo with text → text read and translated.
- Exceed 20 in a day → rate-limit message.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| Bot stops responding after token change | Webhook not re-registered under new token — see `WEBHOOK_NOTES.md` |
| Two workflows both "receive" messages | A second Telegram Trigger exists — remove it (one webhook per bot) |
| Voice notes ignored | Whisper node credential or audio-fetch step failing |
| Photos ignored | Vision OCR node misconfigured |
| No error notifications | Workflow C not set as the Error Workflow for A/B |

# Webhook & Token Rotation Notes — PolyBridge

This document captures the single most important operational rule for PolyBridge and the runbook for rotating the bot token.

## The Rule: One Webhook Per Bot

A Telegram bot supports exactly **one** registered webhook URL at a time. Registering a new one silently replaces the old one.

In PolyBridge, this means:

- **Only Workflow B** holds a `Telegram Trigger` node.
- Workflows **A** and **C** must **never** hold a Telegram Trigger. A is invoked internally; C is wired in as the Error Workflow.

If a Telegram Trigger is accidentally added to A or C, the two triggers will compete for the single webhook slot, and message delivery will become unreliable or stop entirely.

## Token Rotation Runbook

When the bot token is rotated (e.g. after a suspected exposure), the old webhook registration is tied to the **old** token and will no longer deliver. Follow these steps:

1. **Update the credential** — In N8N, edit the Telegram credential and paste the new token. Do this once; all nodes referencing the credential pick it up.

2. **Re-register the webhook** — The Telegram Trigger on **Workflow B** must re-register under the new token. The reliable way:
   - Deactivate Workflow B.
   - Re-activate Workflow B. On activation, N8N re-registers the webhook using the current (new) token.

3. **Confirm registration** —
   ```
   https://api.telegram.org/bot<NEW_TOKEN>/getWebhookInfo
   ```
   The `url` field should point at your N8N instance, with no `last_error_message`.

4. **Watch for the A/B collision** — If delivery is still broken after re-activation, check that no second workflow (A or C) is also trying to register a Telegram webhook. Only B should.

5. **Smoke test** — Send a `/start` and a text message; confirm a reply.

## Security Reminder

- Never hardcode a bot token in a workflow JSON file. During a past rotation sweep, a hardcoded token was found in a workflow file — the fix is to patch the live node via the N8N UI and keep tokens only in the credential store.
- The JSON files committed to this repo are **skeletons** with no tokens.

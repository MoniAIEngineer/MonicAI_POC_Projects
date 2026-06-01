# N8N Workflows — Complete Setup Guide
## SmartHome Pro X200 AI Customer Support Agent

> ⚠️ **Never commit N8N workflow JSON to GitHub** — it contains OAuth tokens,
> API keys, and webhook URLs. Use this guide to recreate all workflows.

---

## Overview — 5 Workflows

| # | Workflow Name | Trigger | Purpose |
|---|---|---|---|
| 1 | Customer Support — Email Agent | Gmail (every minute) | Core email processing pipeline |
| 2 | Phase 2 — Smart PDF Sync | Google Drive file update | Auto-sync product manual to Pinecone |
| 3 | RAG Builder — PDF to Pinecone | Manual (Execute button) | One-time manual RAG build |
| 4 | Morning Dashboard Alert | Daily 8:00 AM | Fishbone analysis + Telegram summary |
| 5 | Dashboard Data API | Webhook (GET) | Serve data to dashboard + FAQ cache sync |

---

## Workflow 1 — Customer Support Email Agent

**Trigger:** Gmail — Every Minute — Message Received
**Search Filter:** `-from:me` (prevents email loops)
**Purpose:** Core pipeline — reads emails, calls AutoGen AI, routes responses

### Node Flow
```
[Gmail Trigger]
    → [Wait 2s]
    → [AutoGen Analyse - HTTP POST]
    → [Spam/OOO Check - IF]
        TRUE →  [Log Spam Reply - Google Sheets]
                → [Spam Auto-Reply - Gmail]
                → STOP
        FALSE → [Log Ticket to Sheets - Google Sheets]
                → [Escalate Check - IF]
                    TRUE →  [Telegram Escalation Alert]
                            → [Log Escalation to Sheets]
                            → [Holding Email to Customer - Gmail]
                            → [Log Holding Reply - Google Sheets]
                    FALSE → [Auto-Reply to Customer - Gmail]
                            → [Log Auto Reply - Google Sheets]
                            → [CVH Priority Check - IF]
                                TRUE → [Telegram CVH Alert]
                                       → [Update CVH Ticket - Google Sheets]
                                       → [Update Ticket Status - Google Sheets]
```

### AutoGen HTTP Request Node
- **Method:** POST
- **URL:** `http://YOUR_VPS_IP:8001/analyse`
- **Body (JSON):**
```json
{
  "subject": "{{ $('Email Received').item.json.subject }}",
  "body": "{{ $('Email Received').item.json.text }}",
  "sender": "{{ $('Email Received').item.json.from }}"
}
```

### Spam/OOO Check (IF Node)
- Condition: `{{ $('AutoGen Analyse').item.json.skip }}` equals `true`

### Escalate Check (IF Node)
- Condition: `{{ $('AutoGen Analyse').item.json.escalate }}` equals `true`

### CVH Priority Check (IF Node)
- Condition: `{{ $('AutoGen Analyse').item.json.priority }}` equals `Critical` OR `Very High`

### Log Ticket to Sheets — Field Mapping
| Field | Expression |
|---|---|
| ticket_id | `{{ $('Email Received').item.json.id }}` |
| received_at | `{{ $('Email Received').item.json.date }}` |
| sender_email | `{{ $('Email Received').item.json.From }}` |
| sender_name | `{{ $('Email Received').item.json.From.split('<')[0].trim() }}` |
| subject | `{{ $('AutoGen Analyse').item.json.subject \|\| $('Email Received').item.json.subject }}` |
| body_preview | `{{ $('Email Received').item.json.snippet }}` |
| priority | `{{ $('AutoGen Analyse').item.json.priority }}` |
| sentiment | `{{ $('AutoGen Analyse').item.json.sentiment }}` |
| language | `{{ $('AutoGen Analyse').item.json.language }}` |
| status | `Open` |
| rag_score | `{{ $('AutoGen Analyse').item.json.confidence_score }}` |
| rag_version | `v1.1` |
| faq_cache_hit | `{{ $('AutoGen Analyse').item.json.faq_cache_hit \|\| false }}` |
| reply_sent_at | `{{ new Date().toISOString() }}` |
| sla_breached | `FALSE` |

### Auto-Reply Email Body
```html
=<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
<p>Dear <strong>{{ $('Email Received').item.json.From.split('<')[0].trim() || 'Valued Customer' }}</strong>,</p>
<p>Thank you for contacting <strong>SmartHome Pro Support</strong>.</p>
<hr style="border: 1px solid #eeeeee; margin: 20px 0;">
{{ $('AutoGen Analyse').item.json.output.includes('ANSWER:') ?
'<p><strong>📋 Your Question:</strong><br>' + $('AutoGen Analyse').item.json.output.split("QUESTION:")[1].split("ANSWER:")[0].trim() + '</p><p><strong>✅ Solution:</strong></p><p>' + $('AutoGen Analyse').item.json.output.split("ANSWER:")[1].split("SOURCE:")[0].trim().replace(/\n/g, "<br>") + '</p><p><strong>📖 Source:</strong> ' + $('AutoGen Analyse').item.json.output.split("SOURCE:")[1].split("CONFIDENCE:")[0].trim() + '</p>'
:
'<p style="background:#fff3cd;padding:15px;border-radius:8px;border-left:4px solid #e65c00;"><strong>⚠️ Notice</strong></p><p>' + $('AutoGen Analyse').item.json.output + '</p>'
}}
<hr style="border: 1px solid #eeeeee; margin: 20px 0;">
<p>Best regards,<br><strong>SmartHome Pro Support Team</strong><br>
📧 support@smarthomepro.com<br>📞 +1-800-555-0199</p>
</div>
```

### Holding Email Body (Escalation)
```html
=<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
<p>Dear <strong>{{ $('Email Received').item.json.From.split('<')[0].trim() }}</strong>,</p>
<p>Thank you for contacting SmartHome Pro Support.</p>
<p>We have received your message and fully understand the urgency of your situation.
A senior support specialist has been personally notified and will respond to you
within <strong>2 business hours</strong>.</p>
<p>Your case reference number is: <strong>{{ $('Email Received').item.json.id }}</strong></p>
<p>We take your concern seriously and appreciate your patience.</p>
<p>Best regards,<br><strong>SmartHome Pro Support Team</strong></p>
</div>
```

### Telegram Escalation Alert Message
```
🚨 ESCALATION REQUIRED — Human Review Needed!

📌 Priority: {{ $('AutoGen Analyse').item.json.priority }}
🎯 Confidence: {{ $('AutoGen Analyse').item.json.confidence }} ({{ $('AutoGen Analyse').item.json.confidence_score }})
😤 Sentiment: {{ $('AutoGen Analyse').item.json.sentiment }}
🌐 Language: {{ $('AutoGen Analyse').item.json.language }}
📧 From: {{ $('Email Received').item.json.From }}
📋 Subject: {{ $('Email Received').item.json.subject }}
❓ Question: {{ $('AutoGen Analyse').item.json.output.split('QUESTION:')[1]?.split('ANSWER:')[0]?.trim() || 'See email' }}

Please review and reply manually.
```

---

## Workflow 2 — Phase 2: Smart PDF Sync

**Trigger:** Google Drive — File Created/Updated
**Purpose:** Auto-detects when product manual PDF is updated on Google Drive,
checks if it changed (hash comparison), and re-embeds into Pinecone automatically.

### Node Flow
```
[Google Drive Trigger - fileCreated]
    → [Download the Updated File - Google Drive]
    → [Get row(s) in sheet - Google Sheets PDF Sync Log]
    → [Hash Calculation - Code Node]
    → [IF: Hash Changed?]
        TRUE (new/changed) →
            [Pinecone Vector Store]
                ← [Embeddings OpenAI - text-embedding-3-large]
                ← [Default Data Loader]
            → [Append row in sheet - Google Sheets PDF Sync Log]
            → [Send a text message - Telegram: sync success]
        FALSE (no change) →
            [Send a text message - Telegram: no change needed]
```

### Hash Calculation Code Node
```javascript
// Calculate MD5 hash of downloaded file to detect changes
const crypto = require('crypto');
const fileData = $input.first().binary.data.data;
const hash = crypto.createHash('md5')
  .update(Buffer.from(fileData, 'base64'))
  .digest('hex');
return [{ json: { hash, filename: $input.first().binary.data.fileName } }];
```

### Pinecone Vector Store Settings
- **Index:** `product-support-rag`
- **Namespace:** `v1.1`
- **Embeddings:** OpenAI `text-embedding-3-large`
- **Data Loader:** Default (PDF chunking)

### Telegram Success Message
```
✅ RAG Knowledge Base Updated!
📄 File: {{ $('Download the updated File').item.binary.data.fileName }}
🔑 Hash: {{ $json.hash }}
⏰ Time: {{ new Date().toISOString() }}
📊 Pinecone namespace: v1.1
```

---

## Workflow 3 — RAG Builder: PDF to Pinecone

**Trigger:** Manual (Execute Workflow button)
**Purpose:** One-time manual build of RAG knowledge base from PDF on Google Drive.
Used for initial setup or full rebuild.

### Node Flow
```
[When clicking 'Execute workflow']
    → [Download file - Google Drive]
    → [Pinecone Vector Store]
        ← [Embeddings OpenAI - text-embedding-3-large]
        ← [Default Data Loader]
```

### Settings
- **Google Drive File:** SmartHome Pro X200 product manual PDF
- **Pinecone Index:** `product-support-rag`
- **Pinecone Namespace:** `v1.1`
- **Embeddings Model:** `text-embedding-3-large`

> **When to use:** Run this once during initial setup, or when you want to
> completely rebuild the knowledge base from scratch.
> For incremental updates use **Phase 2 — Smart PDF Sync** instead.

---

## Workflow 4 — Morning Dashboard Alert

**Trigger:** Schedule — Daily at 8:00 AM UTC
**Purpose:** Every morning, fetches yesterday's tickets, categorizes issues
using Fishbone analysis, logs results to Google Sheets, and sends a
summary Telegram alert to the team.

### Node Flow
```
[Daily 8am Trigger - Schedule]
    → [Get Yesterday Tickets - Google Sheets Email Log]
    → [Categorize Issues - Code Node]
    → [Log Fishbone Index - Google Sheets Fishbone Index]
    → [Morning Dashboard Alert - Telegram]
```

### Get Yesterday Tickets (Google Sheets)
- **Sheet:** Email Log
- **Filter:** received_at >= yesterday 00:00:00 AND received_at < today 00:00:00

### Categorize Issues Code Node
```javascript
// Keyword-based Fishbone categorization
const items = $input.all();
const categories = {
  Connectivity: 0, "LED/Hardware": 0, Setup: 0,
  "Device Limit": 0, "Alexa/Voice": 0, Billing: 0, Other: 0
};
const kwMap = {
  connect: "Connectivity", internet: "Connectivity", wifi: "Connectivity",
  led: "LED/Hardware", broken: "LED/Hardware", hardware: "LED/Hardware",
  setup: "Setup", install: "Setup", reset: "Setup",
  device: "Device Limit", limit: "Device Limit",
  alexa: "Alexa/Voice", voice: "Alexa/Voice",
  refund: "Billing", billing: "Billing", charge: "Billing"
};
for (const item of items) {
  const text = ((item.json.subject || '') + ' ' + (item.json.body_preview || '')).toLowerCase();
  let matched = false;
  for (const [kw, cat] of Object.entries(kwMap)) {
    if (text.includes(kw)) { categories[cat]++; matched = true; break; }
  }
  if (!matched) categories.Other++;
}
return [{ json: { date: new Date().toISOString().split('T')[0], ...categories, total: items.length } }];
```

### Telegram Morning Alert Message
```
📊 SmartHome Pro X200 — Daily Support Summary
📅 Date: {{ new Date().toLocaleDateString() }}

📈 Total Tickets: {{ $json.total }}

🐟 Fishbone Analysis:
🔌 Connectivity: {{ $json.Connectivity }}
💡 LED/Hardware: {{ $json.LED_Hardware }}
⚙️ Setup: {{ $json.Setup }}
📱 Device Limit: {{ $json.Device_Limit }}
🔊 Alexa/Voice: {{ $json.Alexa_Voice }}
💳 Billing: {{ $json.Billing }}
❓ Other: {{ $json.Other }}

🎯 Dashboard: http://YOUR_VPS_IP:8080
```

---

## Workflow 5 — Dashboard Data API

**Trigger:** Multiple Webhooks (GET)
**Purpose:** Serves ticket and escalation data to the dashboard,
and syncs FAQ cache from AutoGen to Google Sheets.

### Sub-workflows inside this workflow

#### 5a. Tickets Webhook
```
[Tickets Webhook - GET /webhook/tickets]
    → [Get Email Log - Google Sheets]
    → [Return Tickets - Respond to Webhook]
```

#### 5b. Escalations Webhook
```
[Escalations Webhook - GET /webhook/escalations]
    → [Get Escalation Queue - Google Sheets]
    → [Get Escalation Queue1 - Respond to Webhook]
```

#### 5c. FAQ Cache Sync
```
[FAQ Cache Sync Webhook - GET /webhook/faq-sync]
    → [Get FAQ Cache - HTTP GET from AutoGen VPS]
    → [Append row in sheet - Google Sheets FAQ Cache]
```

### Webhook URLs
| Webhook | URL |
|---|---|
| Tickets | `https://n8n.srv1645088.hstgr.cloud/webhook/tickets` |
| Escalations | `https://n8n.srv1645088.hstgr.cloud/webhook/escalations` |
| FAQ Cache Sync | `https://n8n.srv1645088.hstgr.cloud/webhook/faq-sync` |

### FAQ Cache HTTP GET Node
- **URL:** `http://YOUR_VPS_IP:8001/faq-cache` (or read from faq_cache.json)
- **Method:** GET

---

## Environment Variables Required

```bash
# Copy template and fill in your values
cp .env.example .env
```

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX=product-support-rag
PINECONE_NAMESPACE=v1.1
```

---

## Google Sheets Setup

Create a Google Sheet with these 6 tabs:

| Tab Name | Purpose |
|---|---|
| Email Log | All incoming tickets |
| Reply Log | All outgoing replies |
| Escalation Queue | Escalated tickets |
| PDF Sync Log | RAG sync history |
| Fishbone Index | Daily categorization |
| FAQ Cache | Cached Q&A pairs |

**Share settings:** Anyone with the link → Viewer
**Copy Sheet ID** from URL and update `SHEET_ID` in `app.py`

---

## Deployment Order

1. Set up Google Sheets (6 tabs)
2. Run **Workflow 3** (RAG Builder) — one time to build Pinecone index
3. Deploy `agent.py` on VPS (port 8001)
4. Deploy `app.py` + `index.html` on VPS (port 8080)
5. Activate **Workflow 1** (Email Agent) — main pipeline
6. Activate **Workflow 2** (Smart PDF Sync) — auto-updates
7. Activate **Workflow 4** (Morning Alert) — daily summary
8. Activate **Workflow 5** (Dashboard API) — webhook data

---

## Author
Monic Pradeep — AI Engineer — May 2026

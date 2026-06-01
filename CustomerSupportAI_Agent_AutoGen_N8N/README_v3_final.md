# 🤖 AI Customer Support Agent — SmartHome Pro X200

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![N8N](https://img.shields.io/badge/N8N-Workflow-orange)](https://n8n.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple)](https://openai.com)
[![Pinecone](https://img.shields.io/badge/Pinecone-RAG-teal)](https://pinecone.io)
[![Flask](https://img.shields.io/badge/Flask-Dashboard-black)](https://flask.palletsprojects.com)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384)](https://chartjs.org)
[![Telegram](https://img.shields.io/badge/Telegram-Alerts-blue)](https://telegram.org)

> A fully automated, production-grade AI customer support system. Processes support emails end-to-end using RAG-powered answers, multi-language detection (10+ languages), smart escalation routing, FAQ caching, question limit enforcement, auto-subject generation, email loop prevention, customer follow-up handling, and a **live Power BI-style analytics dashboard** — all orchestrated through N8N with zero manual intervention.

---

## 🚀 System Status

| Component | URL | Status |
|---|---|---|
| AutoGen API | http://72.61.178.139:8001 | ✅ Live |
| Dashboard | http://72.61.178.139:8080 | ✅ Live |
| N8N Workflows | https://n8n.srv1645088.hstgr.cloud | ✅ Live |
| Telegram Bot | SHPro_Alerts_bot (8691797452) | ✅ Live |
| Google Sheets | 6 tabs auto-populated | ✅ Live |

---

## 🤖 AutoGen AI Engine — 10-Step Pipeline

Every email passes through these steps in `/opt/autogen-support/agent.py`:

| Step | Process | Detail |
|---|---|---|
| 1 | Self-Reply Block | Detects emails from own address — prevents infinite loops |
| 2 | Auto-Subject Generation | GPT-4o generates subject if customer sends blank email |
| 3 | FAQ Cache Check | MD5 hash lookup — returns in 24ms if previously answered |
| 4 | Spam/OOO Detection | 25+ keyword patterns — blocks spam, OOO, Re:, Fwd: |
| 5 | Language Detection | GPT-4o ISO 639-1 code (hi, es, de, ja, ar, zh...) |
| 6 | Question Count Check | Max 2 questions — polite limit message for 3+ in customer language |
| 7 | RAG Query | text-embedding-3-large, top_k=8, cosine similarity |
| 8 | GPT-4o Generation | Structured prompt, temp=0.3, max_tokens=2000 |
| 9 | Escalation Logic | 3 triggers: confidence<0.4 / angry+high priority / keywords |
| 10 | FAQ Cache Save | Saves if confidence>=0.5 and not escalated |

---

## 🌍 Multi-Language Support

Auto-detects and replies in customer's language:

| Language | Code | Status |
|---|---|---|
| English | en | ✅ Tested |
| German | de | ✅ Tested |
| Hindi | hi | ✅ Tested |
| Spanish | es | ✅ Tested |
| Japanese | ja | ✅ Tested |
| French | fr | ✅ Configured |
| Arabic | ar | ✅ Configured |
| Portuguese | pt | ✅ Configured |
| Chinese | zh | ✅ Configured |
| Korean | ko | ✅ Configured |
| Mixed language | dominant | ✅ Replies in dominant language |

---

## 📊 Live Dashboard v2.0

**URL:** `http://72.61.178.139:8080` | Auto-refreshes every 30 seconds

### KPI Cards (7)
| Card | Source |
|---|---|
| Total Tickets | Email Log row count |
| Escalations | Escalation Queue row count |
| Resolution Rate | (Total-Escalations)/Total × 100 |
| SLA Compliance | Rows where sla_breached != TRUE |
| Open Tickets | Rows where status = Open |
| Avg RAG Score | Avg rag_score_at_escalation |
| Avg Resolution Time | Avg resolution_time_mi |

### Charts (13)
| Chart | Type |
|---|---|
| Fishbone Root Cause | Bar chart with value labels |
| Priority Distribution | Donut + legend (count + %) |
| Sentiment Analysis | Donut + legend (count + %) |
| Volume Trend Daily | Bar chart with value labels |
| Reply Type Breakdown | Donut + legend (count + %) |
| Status Breakdown | Donut + legend (count + %) |
| Language Distribution | Donut + legend (full names) |
| Resolution Rate Gauge | Half-doughnut |
| RAG Confidence Trend | Line chart (from rag_score_at_escalation) |
| Top 5 Subjects | Horizontal bar list |
| Recent Tickets Table | Table with badges + Resolution Time |

### Filters (6)
| Filter | Options |
|---|---|
| Priority | All / Very High / High / Normal / Low |
| Sentiment | All / Angry / Neutral / Positive |
| Status | All / Open / Replied / Closed |
| Language | **Dynamic** — auto-populated from real data |
| Period | Today / This Week / This Month / This Year / Custom Range |
| Custom Range | From + To date pickers |

### Search & Export
- **Search Bar** — searches all fields, updates ALL 13 charts + 7 KPIs simultaneously
- **Export CSV** — downloads filtered tickets as `smarthome_tickets_YYYY-MM-DD.csv`

---

## 📋 Google Sheets Structure

**Sheet ID:** `1Va5k8C4z0qeiz9zAhojWuOX084-4Rh1OiEIZpxAieaI`

| Tab | Key Columns |
|---|---|
| Email Log | ticket_id, received_at, sender_email, sender_name, subject, body_preview, priority, sentiment, **language** (ISO code), status, **rag_score**, rag_version, **faq_cache_hit**, **reply_sent_at**, resolution_time_mi, sla_breached |
| Reply Log | reply_id, ticket_id, replied_at, reply_type, reply_sent_to |
| Escalation Queue | escalation_id, ticket_id, escalated_at, reason, **rag_score_at_escalation** |
| PDF Sync Log | RAG sync tracking |
| Fishbone Index | Category-level classification |
| FAQ Cache | MD5 hash, question, answer, confidence, hit_count |

> **Note:** Dashboard RAG Confidence Trend reads `rag_score_at_escalation` from Escalation Queue tab.

---

## 🔒 Email Loop Prevention (3 Layers)

| Layer | Location | Method |
|---|---|---|
| Layer 1 | N8N Gmail Trigger | `-from:me` search filter |
| Layer 2 | AutoGen agent.py | `is_self_reply()` function |
| Layer 3 | AutoGen spam filter | Re:, Fwd:, Fw: keywords |

---

## ✅ Test Cases — 70 Total, All Passed

### Original Phase Testing (14)
| # | Test | Result |
|---|---|---|
| 1 | Spam Detection | ✅ 2.5s |
| 2 | Low Confidence Escalation | ✅ 14.5s |
| 3 | Normal Support Flow | ✅ 12s |
| 4 | German Language | ✅ 16s |
| 5 | CVH Priority Alert | ✅ 13s |
| 6 | Keyword Escalation | ✅ 13.8s |
| 7 | Reply Log — Auto | ✅ 12s |
| 8 | Reply Log — Holding | ✅ 13.8s |
| 9 | FAQ Cache Speed (24ms) | ✅ 0.024s |
| 10 | Fishbone Index | ✅ |
| 11 | Dashboard Live Data | ✅ |
| 12 | Dashboard Filters | ✅ |
| 13 | FAQ Cache Sync | ✅ |
| 14 | Alexa Integration | ✅ 14s |

### Multi-Language (7)
| # | Test | Result |
|---|---|---|
| 15 | Hindi email | ✅ hi detected |
| 16 | Spanish email | ✅ es detected |
| 17 | German email | ✅ de detected |
| 18 | Japanese email | ✅ ja detected |
| 19 | Mixed German+English | ✅ German (dominant) |
| 20 | Mixed Hindi+English | ✅ Correct language |
| 21 | Dynamic language filter | ✅ Auto-appears |

### Question Handling (7)
| # | Test | Result |
|---|---|---|
| 22 | Single question | ✅ Full answer |
| 23 | 2 questions | ✅ Both answered |
| 24 | 3 questions | ✅ Limit message |
| 25 | 4 questions | ✅ Limit message |
| 26 | Numbered format | ✅ Detected |
| 27 | ? mark detection | ✅ Detected |
| 28 | Limit message in German | ✅ German message |

### Email Edge Cases (7)
| # | Test | Result |
|---|---|---|
| 29 | No subject email | ✅ [Auto] generated |
| 30 | Email loop | ✅ Blocked |
| 31 | Self-reply block | ✅ Blocked |
| 32 | Gmail filter | ✅ Blocked |
| 33 | Re:Re:Re: chain | ✅ Stopped |
| 34 | Customer follow-up | ✅ New ticket |
| 35 | Non-support content (Zoom link) | ✅ Escalated |

### Dashboard (19) — All ✅ Passed
Filters, search, export CSV, RAG trend, language distribution, auto-refresh, donut labels

### Google Sheets Fixes (5) — All ✅ Passed
Language, RAG score, reply_sent_at, faq_cache_hit, auto-subject logging

### FAQ Cache (2)
| # | Test | Result |
|---|---|---|
| 67 | Same question speed | ✅ 24ms vs 4000ms |
| 68 | Auto-answer from cache | ✅ No RAG call |

### Document Update (1)
| # | Test | Result |
|---|---|---|
| 69 | All 3 documents updated | ✅ Complete |

### Non-Support Content (1)
| # | Test | Result |
|---|---|---|
| 70 | Zoom link only email | ✅ Escalated correctly |

### Negative Test Cases (7) — All ✅ Handled
AutoGen down, malformed email, Sheets failure, OOO loop, unknown language, empty body, question not in KB

---

## 🏢 Enterprise Readiness

| Platform | Time |
|---|---|
| Gmail | ✅ Live now |
| Jira Cloud | 2-3 hrs |
| Zendesk | 2-3 hrs |
| Freshdesk | 2-3 hrs |
| ServiceNow | 4-6 hrs |
| HubSpot | 3-4 hrs |
| Salesforce | 6-8 hrs |

---

## 📁 File Structure

```
/opt/autogen-support/
├── agent.py          ← AutoGen FastAPI (port 8001) — 10-step pipeline
├── faq_cache.json    ← Auto-created FAQ cache
├── agent.py.backup   ← Backup of last stable version
└── .env              ← API keys

/opt/dashboard/
├── app.py            ← Flask — reads Google Sheets CSV directly
└── index.html        ← Dashboard frontend (13 charts, 6 filters, search, export)
```

---

## 👤 Author

**Monic Pradeep** — AI Engineer | May 2026
VPS: 72.61.178.139 | N8N: n8n.srv1645088.hstgr.cloud

---

## 🔄 N8N Workflows (5 Total)

| # | Workflow | Trigger | Purpose |
|---|---|---|---|
| 1 | Customer Support Email Agent | Gmail every minute | Core email processing pipeline |
| 2 | Phase 2 — Smart PDF Sync | Google Drive file update | Auto-sync product manual to Pinecone |
| 3 | RAG Builder — PDF to Pinecone | Manual (Execute button) | One-time manual RAG build |
| 4 | Morning Dashboard Alert | Daily 8:00 AM | Fishbone analysis + Telegram summary |
| 5 | Dashboard Data API | Webhook GET | Serve data to dashboard + FAQ cache sync |

### Workflow 1 — Customer Support Email Agent
Main pipeline. Every incoming email goes through:
`Gmail Trigger → Wait 2s → AutoGen Analyse → Spam Check → Log to Sheets → Escalate Check → Auto-Reply OR Holding Email → Telegram Alert → CVH Check`

### Workflow 2 — Phase 2: Smart PDF Sync
Auto-triggered when product manual PDF is updated on Google Drive. Calculates MD5 hash to detect changes — only re-embeds to Pinecone if file actually changed. Sends Telegram confirmation.
`Google Drive Trigger → Download File → Get Sync Log → Hash Calculation → IF Changed → Pinecone Vector Store → Log to Sheets → Telegram`

### Workflow 3 — RAG Builder: PDF to Pinecone
One-time manual workflow to build the RAG knowledge base from scratch. Run once during initial setup or for full rebuild.
`Execute Button → Download PDF from Google Drive → Pinecone Vector Store (text-embedding-3-large)`

### Workflow 4 — Morning Dashboard Alert
Runs daily at 8AM UTC. Fetches yesterday's tickets, runs Fishbone keyword categorization, logs results to Google Sheets, sends team summary via Telegram.
`8AM Schedule → Get Yesterday Tickets → Categorize Issues (Code) → Log Fishbone Index → Telegram Morning Alert`

### Workflow 5 — Dashboard Data API
Three sub-workflows serving data via webhooks:
- **Tickets Webhook** → Reads Email Log → Returns to dashboard
- **Escalations Webhook** → Reads Escalation Queue → Returns to dashboard
- **FAQ Cache Sync** → Fetches FAQ cache from AutoGen VPS → Appends to Google Sheets

> Full workflow setup guide: see `N8N_WORKFLOW_SETUP.md`

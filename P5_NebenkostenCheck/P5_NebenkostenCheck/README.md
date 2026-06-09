# 🧾 NebenkostenCheck — AI Utility Bill Analyzer for German Tenants

> Upload your German service-charge statement (*Nebenkostenabrechnung*) and get an AI-powered legal analysis that flags questionable charges, checks compliance against German tenancy law, and explains your bill in plain language.

**🌐 Live:** [nebenkostencheck-ai.de](https://nebenkostencheck-ai.de)
**💶 Pricing:** €19 one-time analysis (Dodo Payments) · currently in **free beta**
**🏷️ Type:** Micro-SaaS — real product

---

## 📖 Overview

Every year, millions of German tenants receive a *Nebenkostenabrechnung* — an annual statement of operating and heating costs. Studies repeatedly find that a large share contain errors, and most tenants lack the legal knowledge to spot them. Professional review is expensive and slow.

**NebenkostenCheck** closes that gap. A tenant uploads their PDF statement; the system extracts the line items and runs an AI legal analysis against the relevant German statutes, returning a clear report: what each charge means, which items are legally allocable, and where something looks off and worth disputing.

This is the portfolio's flagship **real, monetized product** — built for paying customers, not just as a demonstration.

---

## ✨ Key Features

- **📄 PDF extraction** — Parses uploaded statements with PyMuPDF, including multi-page bills.
- **⚖️ Legal compliance analysis** — Checks charges against German tenancy law (see *Legal Basis* below).
- **🔍 Charge-by-charge breakdown** — Each line item explained in plain language.
- **🚩 Red-flag detection** — Highlights items that may not be lawfully allocable to tenants.
- **💶 One-time pricing** — €19 per analysis via Dodo Payments — no subscription.
- **🆓 Free beta** — Currently free with an email-capture gate while gathering real-world test bills.

---

## ⚖️ Legal Basis

The analysis is grounded in the core German statutes governing operating costs:

| Statute | Scope |
|---------|-------|
| **§2 BetrKV** | Catalogue of allocable operating costs |
| **§556 BGB** | Agreements on operating costs in tenancy |
| **HeizkostenV §7** | Distribution of heating costs |
| **CO2KostAufG** | Allocation of the CO₂ price between landlord and tenant |

> ⚠️ NebenkostenCheck provides **informational analysis, not legal advice**. For a binding assessment, consult a *Mieterverein* or a qualified lawyer.

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Tenant      │────▶│  Next.js 14  │────▶│   FastAPI       │
│  (uploads PDF)│     │  Frontend    │     │   Backend       │
└──────────────┘     └──────────────┘     └────────┬────────┘
                                                    │
                  ┌──────────────────────────────────┼──────────────────┐
                  │                                   │                  │
            ┌─────▼──────┐               ┌────────────▼────────┐ ┌───────▼────────┐
            │  PyMuPDF    │               │   Claude API        │ │     Supabase    │
            │ (extract)   │──────────────▶│ (legal analysis vs  │ │ (sessions,      │
            │             │               │  BetrKV/BGB/etc.)   │ │  email capture) │
            └────────────┘               └─────────────────────┘ └────────────────┘
                                                    │
                                          ┌─────────▼─────────┐
                                          │   Dodo Payments    │
                                          │  (€19 one-time)    │
                                          └────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 |
| **Backend** | FastAPI (Python) |
| **PDF extraction** | PyMuPDF |
| **Legal analysis LLM** | Claude API (Anthropic) |
| **Database** | Supabase |
| **Payments** | Dodo Payments (€19 one-time) |
| **Infra** | Docker + Traefik (Let's Encrypt), Hostinger VPS (Ubuntu 24.04) |

> Service containers are named `nkc-frontend` / `nkc-backend` to keep names globally unique on the shared Docker network.

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- A Supabase project
- An Anthropic API key (Claude)
- A Dodo Payments account (for paid mode)

### Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd P5_NebenkostenCheck

# 2. Create your environment file from the template
cp .env.example .env
# → fill in your real keys in .env (never commit this file)

# 3. Run the database migration
#    Apply supabase/migrations.sql in your Supabase SQL editor

# 4. Build and start
docker compose up --build -d
```

### Switching from Free Beta to Paid

The app ships in free beta. To launch paid mode:
1. Confirm Dodo KYC is approved.
2. Align the Dodo webhook path with the backend route.
3. Set `FREE_BETA=false` **explicitly** in `.env`.

---

## 📁 Project Structure

```
P5_NebenkostenCheck/
├── README.md              # This file
├── .env.example           # Environment variable template (no secrets)
├── .gitignore             # Excludes secrets, build artifacts
├── LICENSE                # MIT
├── docker-compose.yml     # Service orchestration (reference)
├── supabase/
│   └── migrations.sql     # Database schema
├── docs/
│   ├── ARCHITECTURE.md    # Detailed technical design
│   ├── SETUP.md           # Step-by-step deployment guide
│   └── LEGAL_BASIS.md     # The statutes the analysis checks against
└── assets/
    └── (screenshots, sample report)
```

---

## 🔒 Security Note

This repository contains **no live credentials**. All secrets — Anthropic key, Supabase keys, Dodo key/webhook secret — are referenced through `.env.example` placeholders and excluded via `.gitignore`. Configure your own keys locally.

---

## 📌 Roadmap

- [ ] Move sessions from in-memory to Supabase persistence
- [ ] Align Dodo webhook path before paid launch
- [ ] Gather real-world PDF test bills (free-beta goal)
- [ ] Flip `FREE_BETA=false` once KYC is approved
- [ ] Export analysis as a downloadable PDF report
- [ ] Side-by-side comparison across multiple years

---

## 👤 Author

**Monic** — AI/GenAI Engineer | 19+ years enterprise IT background (SAP, data migration)
Based in Sindelfingen, Germany 🇩🇪

The flagship real product in a portfolio of AI micro-SaaS builds. Built with FastAPI, Next.js, PyMuPDF, Supabase, and the Anthropic Claude API.

---

## 📄 License

MIT — see [LICENSE](./LICENSE).

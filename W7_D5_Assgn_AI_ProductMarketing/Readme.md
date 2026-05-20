# 🤖 AI Product Marketing Multi-Agent System

An AI-powered Product Marketing Automation System built using **Python + Streamlit + AutoGen AgentChat + OpenAI**.

This project demonstrates how multiple AI agents can collaborate together to automate modern product marketing workflows such as:

- Trend research
- Content generation
- SEO optimization
- Competitor positioning
- Campaign scoring

---

# 🚀 Features

## ✅ Multi-Agent AI Workflow

The system uses multiple specialized AI agents working together:

```text
User Input
   ↓
Trend Research Agent
   ↓
Content Writer Agent
   ↓
SEO Optimization Agent
   ↓
Competitor Positioning Agent
   ↓
Content Scoring Agent
   ↓
Final Campaign Pack
```

---

# 🧠 AI Agents

## 1. 🔍 Trend Research Agent

Responsible for:
- Fetching live web trends
- Identifying trending marketing angles
- Understanding market demand
- Product positioning opportunities

### Uses:
- DDGS (DuckDuckGo Search)
- OpenAI LLM reasoning

---

## 2. ✍️ Content Writer Agent

Generates:
- LinkedIn posts
- Blog intros
- Email campaigns
- Ad copy
- CTA variations

Supports:
- Persona-based writing
- Platform-specific generation
- Tone customization

---

## 3. 🔎 SEO Optimization Agent

Responsible for:
- SEO title generation
- Meta descriptions
- Primary & secondary keywords
- Hashtags
- Search intent analysis
- SEO recommendations

---

## 4. ⚔️ Competitor Positioning Agent

Creates:
- Differentiation strategies
- Unique value propositions
- Messaging gaps
- Competitive hooks

---

## 5. 🏆 Campaign Scoring Agent

Scores:
- Clarity
- SEO strength
- LinkedIn engagement potential
- Product marketing relevance
- CTA quality

Also provides:
- Improvement suggestions
- AI confidence score

---

# 🖥️ Streamlit Dashboard Features

## ✅ Interactive UI

Users can configure:
- Topic
- Product Name
- Target Audience
- Persona
- Platform
- Tone
- Content Type
- Post Length

---

# 📊 Dashboard Features

## ✅ Live Search Results

Displays:
- search title
- URLs
- snippets
- trend sources

---

## ✅ Campaign Score Dashboard

Visual metrics using:
- progress bars
- score cards
- AI scoring

---

## ✅ Sources Used Tab

Shows:
- all live web references
- source transparency
- credibility

---

## ✅ Download Campaign Pack

Exports generated campaign as:
- Markdown file

---

# 🎯 Supported Content Types

- LinkedIn Post
- Blog Intro
- Email Campaign
- Ad Copy
- Full Campaign Pack

---

# 🌐 Supported Platforms

- LinkedIn
- Blog
- Email
- Ad Campaign
- Full Multi-Channel Campaign

---

# 👥 Persona-Based Generation

Supports:
- Founder
- Enterprise CTO
- Product Marketer
- Sales VP
- Customer Support Head

---

# 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend |
| Streamlit | Frontend UI |
| AutoGen AgentChat | Multi-agent orchestration |
| OpenAI | LLM reasoning |
| DDGS | Live web search |
| Pandas | Data handling |

---

# 📁 Project Structure

```text
project/
│
├── app.py
├── agents.py
├── utils.py
├── requirements.txt
├── .env
├── outputs/
│
└── README.md
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone <your_repo_url>
cd project_name
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\\Scripts\\activate
```

### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
```

---

# ▶️ Run Application

```bash
streamlit run app.py
```

---

# 🧪 Example Test Inputs

## Example 1

| Field | Value |
|---|---|
| Topic | AI for customer support |
| Product Name | SupportAI Copilot |
| Audience | Customer support leaders |
| Persona | Enterprise CTO |
| Platform | LinkedIn |
| Content Type | LinkedIn Post |

---

## Example 2

| Field | Value |
|---|---|
| Topic | AI in cybersecurity |
| Product Name | SecureMind AI |
| Audience | CTOs |
| Persona | Enterprise CTO |
| Platform | Blog |
| Content Type | Blog Intro |

---

# 📸 Sample Output

The system can generate:

✅ Live trend analysis  
✅ Product marketing copy  
✅ SEO metadata  
✅ Competitor positioning  
✅ Campaign scores  
✅ Improvement recommendations  

---

# 🎥 LinkedIn Showcase Features

This project is designed as a:
- Portfolio project
- LinkedIn showcase
- AI engineering POC
- Product marketing automation demo

---

# 🚀 Future Enhancements

Planned improvements:

- PDF export
- PPT export
- Trend visualizations
- Agent memory
- Multi-session history
- Real competitor scraping
- Real-time analytics dashboard
- GIF/MP4 campaign generation

---

# 🧠 Key Learnings

This project demonstrates:
- Multi-agent AI systems
- AI orchestration
- Prompt engineering
- Product marketing automation
- AI-powered content workflows
- Streamlit dashboard development

---

# 📌 LinkedIn Post

If showcasing on LinkedIn:

Include:
- architecture screenshot
- Streamlit dashboard
- generated outputs
- workflow diagram
- GitHub repository

---

# 🙌 Author

Built using ❤️ with:
- Python
- Streamlit
- AutoGen
- OpenAI

---

# 🤖 AI Interview Platform

> **A fully working, multi-round AI voice interviewer** — conducts real job interviews in 9 languages, scores answers in real time, and moves candidates from round to round automatically.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai)](https://platform.openai.com)
[![LiveKit](https://img.shields.io/badge/LiveKit-Agents%201.5-orange)](https://livekit.io)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📋 Table of Contents

- [What Is This?](#-what-is-this)
- [Live Demo Features](#-live-demo-features)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Running the Project](#-running-the-project)
- [Interview Modes](#-interview-modes)
- [Languages Supported](#-languages-supported)
- [Extending This Project](#-extending-this-project)
- [Cost Estimation](#-cost-estimation)
- [Common Issues](#-common-issues)
- [Contributing](#-contributing)

---

## 🎯 What Is This?

This project is a **fully automated AI Interview Platform** built with Python, OpenAI, LiveKit, React, and Streamlit. It can:

- Conduct **4-round job interviews** (HR Screening → Technical → Hands-on Discussion → Final HR)
- **Speak and listen** in 9 languages with native-script TTS instructions
- **Score every answer** out of 10 with coaching feedback and behaviour analysis
- **Show live results** in a React interview room and a Streamlit dashboard simultaneously
- **Transition automatically** between rounds — farewell speech, next interviewer joining

### 🔁 Extend It For Any Use Case

| Original | You Can Build |
|---|---|
| Job interview | Python / JavaScript training tutor |
| HR screening | English communication skills coach |
| Technical round | Medical / legal knowledge assessor |
| Hands-on discussion | Sales pitch evaluator |
| Final HR | Language learning conversation partner |

---

## ✨ Live Demo Features

```
Candidate joins room → AI greets in Tamil/Hindi/English/etc.
    ↓
AI asks 4 HR questions (salary, notice period, relocation, reason for change)
    ↓
Each answer scored live: 7/10 ✅ Selected | Coach feedback | Confidence 80%
    ↓
After 4 questions: "You did well! Our Technical team will join shortly."
    ↓
Streamlit shows: HR Screening ✅ Selected 6.8/10 → [▶ Start Technical] button
    ↓
Technical interviewer joins with different name, voice, and deeper questions
    ↓
Final report with all 4 rounds, downloadable as JSON
```

---

## 🏗 How It Works

### Architecture

```
Browser (Edge/Chrome)
    ↓ WebRTC audio stream
LiveKit Cloud ←→ livekit_worker.py (Python agent)
                        ↓
                 EnergyVAD (custom VAD)
                        ↓ speech detected
                 OpenAI Whisper STT
                        ↓ transcript
                 GPT-4o-mini (score + coach + behaviour)
                        ↓ results
                 SQLite (scores.db)    +    LiveKit data channel
                        ↓                         ↓
                 Streamlit (app.py)          React (App.jsx)
                 localhost:8501               localhost:5173
```

### Key Components

| File | Role |
|---|---|
| `app.py` | Streamlit dashboard — setup form, round navigation, live scores |
| `livekit_worker.py` | AI agent — interviewer persona, question flow, scoring, farewell speeches |
| `energy_vad.py` | Custom Voice Activity Detector — pure Python RMS, no ML model, <0.1ms |
| `App.jsx` | React interview room — real-time score cards, transcript, wave animations |

---

## 📁 Project Structure

```
LiveKit_Translator_Agent/
├── app.py                        # Streamlit dashboard
├── livekit_worker.py             # LiveKit AI agent
├── energy_vad.py                 # Custom VAD (RMS-based)
├── requirements.txt              # Python dependencies
├── .env                          # API keys (never commit this)
├── .gitignore
├── README.md
│
├── storage/
│   └── scores.db                 # SQLite — all interview scores
├── resumes/                      # Uploaded resumes
├── audio/                        # TTS audio files (temp)
│
└── livekit-interview-ui/         # React frontend
    ├── src/
    │   ├── App.jsx               # Entire interview room UI
    │   └── main.jsx
    ├── index.html
    ├── package.json
    └── vite.config.ts
```

---

## ✅ Prerequisites

### Accounts Required

| Service | URL | What You Need |
|---|---|---|
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | API Key (`sk-proj-...`) + billing setup |
| **LiveKit Cloud** | [cloud.livekit.io](https://cloud.livekit.io) | WebSocket URL + API Key + API Secret |

### Software Required

| Tool | Version | Download |
|---|---|---|
| Python | **3.11.x** (NOT 3.13) | [python.org](https://python.org) |
| Node.js | 20+ or 22+ | [nodejs.org](https://nodejs.org) |
| Git | Any | [git-scm.com](https://git-scm.com) |
| Browser | Chrome or Edge | (Firefox has WebRTC limitations) |

### Hardware

- Any laptop/desktop (Windows, Mac, Linux)
- Working microphone (external recommended for best RMS levels)
- Stable internet connection

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-interview-platform.git
cd ai-interview-platform
```

### 2. Create Python Virtual Environment

```bash
# Create
python -m venv venv

# Activate — Windows:
venv\Scripts\Activate.ps1

# Activate — Mac/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install React Dependencies

```bash
cd livekit-interview-ui
npm install
cd ..
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-proj-your-key-here
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxx
LIVEKIT_AGENT_NAME=ai-interviewer-agent
LIVEKIT_FRONTEND_URL=http://localhost:5173
```

> ⚠️ **Rules:** No spaces around `=`. No quotes. `LIVEKIT_URL` must start with `wss://` not `https://`. Never commit this file.

### 6. Create Required Folders

```bash
mkdir storage resumes audio
```

---

## ▶️ Running the Project

Open **3 terminal windows** and run one command in each:

```bash
# Terminal 1 — AI Worker (start this FIRST)
python livekit_worker.py dev

# Terminal 2 — Streamlit Dashboard
streamlit run app.py

# Terminal 3 — React Interview Room
cd livekit-interview-ui && npm run dev
```

Then open **[localhost:8501](http://localhost:8501)** in your browser.

> ⚠️ **Order matters:** Start the worker (Terminal 1) before creating a room in Streamlit. The worker must be registered before it can receive jobs.

---

## 🎙 Interview Modes

| Mode | How to Use | Best For |
|---|---|---|
| **Streamlit Voice** | Click Record Answer button in the dashboard | Quick testing without React room |
| **LiveKit Audio Call** | Click Join Interview Room → audio only | Most common — voice interview |
| **LiveKit Video Call** | Select Video mode → Join Interview Room | Full video interview experience |

### Interview Rounds

| Round | Questions | Focus Area |
|---|---|---|
| HR Screening | 4 | Job change reason, salary, notice period, relocation |
| Technical | 5 | Resume-based technical depth, tools, methodologies |
| Hands-on Discussion | 2 | Code writing, SQL, API testing, automation design |
| Final HR Discussion | 4 | Career goals, company fit, salary negotiation, joining |

---

## 🌐 Languages Supported

| Language | TTS Instructions | Silence Responses |
|---|---|---|
| English | ✅ | ✅ |
| Tamil | ✅ Native script | ✅ Native script |
| Hindi | ✅ Native script | ✅ Native script |
| Telugu | ✅ Native script | ✅ Native script |
| Kannada | ✅ Native script | ✅ Native script |
| German | ✅ | ✅ |
| French | ✅ | ✅ |
| Spanish | ✅ | ✅ |
| Japanese | ✅ Native script | ✅ Native script |

---

## 🔧 Extending This Project

### Change the Rounds (Example: Python Tutor)

In `app.py` and `livekit_worker.py`:

```python
# Change these variables
ROUND_ORDER = ['Python Basics', 'Functions and OOP', 'Real Projects']
ROUND_QUESTION_LIMITS = {
    'Python Basics': 5,
    'Functions and OOP': 5,
    'Real Projects': 3,
}
ROUND_PASS_SCORE = {'Python Basics': 5, 'Functions and OOP': 5, 'Real Projects': 5}
```

### Change the Questions

In `livekit_worker.py`, update the instructions template:

```python
# Replace the QUESTIONS FOR THIS ROUND section with your topics
# Example for Python tutor:
# "Python Basics": ask about variables, loops, lists, conditions
# "Functions and OOP": ask about def, class, inheritance
# "Real Projects": ask them to describe a project they built
```

### Add a New Language

```python
# In app.py:
"Korean": {"code": "ko", "whisper": "ko", "tts_instructions": "한국어로만 말하세요."}

# In livekit_worker.py:
WHISPER_LANG["Korean"] = "ko"
TTS_INSTRUCTIONS["Korean"] = "한국어로만 말하세요."
SILENCE_MSGS["Korean"] = ["{name}씨, 거기 계세요?", "준비되면 말씀해 주세요."]
```

---

## 💰 Cost Estimation

| Service | Per Session | Per Month (100 sessions) |
|---|---|---|
| OpenAI Whisper STT | ~$0.03 | ~$3 |
| OpenAI TTS | ~$0.04 | ~$4 |
| OpenAI GPT-4o-mini | ~$0.03 | ~$3 |
| LiveKit Cloud | Free (10k min/month) | ~$0 |
| **Total** | **~$0.10** | **~$10** |

**Cost control tips:**
- Use `gpt-4o-mini` not `gpt-4o` (10x cheaper)
- Keep `max_tokens` low: 80 for scoring, 150 for coaching
- LiveKit free tier covers ~100 interviews/month

---

## 🔧 Key Configuration Variables

| Variable | File | Default | What It Controls |
|---|---|---|---|
| `ROUND_ORDER` | app.py | HR→Technical→... | Round sequence |
| `ROUND_QUESTION_LIMITS` | app.py + worker | HR:4, Tech:5 | Questions per round |
| `ROUND_PASS_SCORE` | app.py + worker | 6.0 | Min score to pass |
| `energy_threshold` | livekit_worker.py | 50.0 | Mic sensitivity |
| `min_silence_duration` | energy_vad.py | 1.0s | Speech segment end |
| `user_away_timeout` | livekit_worker.py | 35.0s | Silence check-in |
| `FEMALE_VOICES` | livekit_worker.py | nova, shimmer | Female TTS voices |
| `MALE_VOICES` | livekit_worker.py | onyx, echo | Male TTS voices |

---

## ❗ Common Issues

| Problem | Fix |
|---|---|
| AI doesn't speak on joining | Start `livekit_worker.py dev` FIRST, then create room in Streamlit |
| MIC RMS=0 always | Select External Microphone in browser mic settings, not Intel Smart Sound |
| `Audio file corrupted` error | Already fixed in `energy_vad.py` — ensure you have latest version |
| AI speaks English in Tamil mode | Check `TTS_INSTRUCTIONS` has native script Tamil in `livekit_worker.py` |
| Streamlit shows 0/4 questions | Check `time.sleep(4) + st.rerun()` loop is present in LiveKit section of `app.py` |
| Technical round shows Rejected 0.0/10 | `advance_round()` now checks for actual scores before running |
| `npm run dev` gives package.json error | You must `cd livekit-interview-ui` first before running npm commands |
| `Plugins must be registered on main thread` | All plugin imports must be at TOP of `livekit_worker.py`, outside any function |
| Female name sounds male | `livekit_worker.py` now adds `"Speak with a warm, professional female voice."` prefix |
| Interview keeps going after 4 questions | `round_complete = True` flag set — restart worker with latest `livekit_worker.py` |

---

## 🏗 Built With

- **[Python 3.11](https://python.org)** — Core language
- **[LiveKit Agents 1.5](https://docs.livekit.io/agents)** — Real-time voice AI framework
- **[OpenAI API](https://platform.openai.com)** — Whisper STT, TTS, GPT-4o-mini
- **[Streamlit](https://streamlit.io)** — Dashboard UI
- **[React 18](https://react.dev)** — Live interview room
- **[Vite](https://vitejs.dev)** — React build tool
- **[SQLite](https://sqlite.org)** — Score storage
- **[@livekit/components-react](https://github.com/livekit/components-js)** — LiveKit React hooks

---

## 📄 License

MIT License — free to use, modify, and distribute for any purpose.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Commit: `git commit -m "Add your feature"`
5. Push: `git push origin feature/your-feature`
6. Open a Pull Request

---

<div align="center">

**Built with ❤️ using Python, OpenAI, LiveKit, React, and Streamlit**

*Extend freely • Use in any language • Deploy anywhere*

</div>

"""
app.py  —  AI Interviewer with AutoGen + LiveKit
=================================================
• Streamlit Voice Mode  : full pipeline inside Streamlit (mic → STT → AutoGen → TTS)
• LiveKit Audio Call    : real-time audio in custom React room  (only candidate has video off)
• LiveKit Video Call    : candidate camera ON, AI avatar shown as static image/animated tile
Language selection drives the entire pipeline (STT language, TTS locale, AutoGen prompt).
"""

import os, json, uuid, asyncio, wave, re, random, sqlite3, time
import warnings
# audioop: built-in on Python <=3.12, deprecated warning suppressed
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    try:
        import audioop
    except ImportError:
        audioop = None
from urllib.parse import urlencode
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
from livekit import api

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ─────────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY")
LIVEKIT_URL          = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY      = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET   = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_FRONTEND_URL = os.getenv("LIVEKIT_FRONTEND_URL", "http://localhost:5173")
LIVEKIT_AGENT_NAME   = os.getenv("LIVEKIT_AGENT_NAME", "ai-interviewer-agent")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY missing in .env"); st.stop()

oai = OpenAI(api_key=OPENAI_API_KEY)

BASE_DIR    = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
RESUME_DIR  = BASE_DIR / "resumes"
AUDIO_DIR   = BASE_DIR / "audio"
DB_PATH     = STORAGE_DIR / "scores.db"

for d in [STORAGE_DIR, RESUME_DIR, AUDIO_DIR]:
    d.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# LANGUAGE CONFIG  (name → code, OpenAI TTS locale, Whisper code)
# ─────────────────────────────────────────────────────────────────
LANGUAGES = {
    "English":  {"code": "en", "whisper": "en",    "tts_instructions": "Speak in clear, professional American English."},
    "German":   {"code": "de", "whisper": "de",    "tts_instructions": "Sprich auf Deutsch, professionell und klar."},
    "French":   {"code": "fr", "whisper": "fr",    "tts_instructions": "Parle en français professionnel et clair."},
    "Spanish":  {"code": "es", "whisper": "es",    "tts_instructions": "Habla en español profesional y claro."},
    "Hindi":    {"code": "hi", "whisper": "hi", "tts_instructions": "केवल हिंदी में बोलें। अंग्रेज़ी बिल्कुल नहीं। पेशेवर और स्पष्ट।"},
    "Tamil":    {"code": "ta", "whisper": "ta", "tts_instructions": "பேசுவது தமிழிலேயே இருக்க வேண்டும். ஆங்கிலம் வேண்டாம். தொழில்முறையாக பேசுங்கள்."},
    "Telugu":   {"code": "te", "whisper": "te", "tts_instructions": "మాత్రమే తెలుగులో మాట్లాడండి. ఇంగ్లీష్ వద్దు. వృత్తిపరంగా మాట్లాడండి."},
    "Kannada":  {"code": "kn", "whisper": "kn", "tts_instructions": "ಕೇವಲ ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ. ಇಂಗ್ಲಿಷ್ ಬೇಡ. ವೃತ್ತಿಪರವಾಗಿ ಮಾತನಾಡಿ."},
    "Japanese": {"code": "ja", "whisper": "ja", "tts_instructions": "必ず日本語のみで話してください。英語は使わないでください。プロフェッショナルに話してください。"},
}

ROUND_ORDER = ["HR Screening", "Technical", "Hands-on Discussion", "Final HR Discussion"]

ROUND_QUESTION_LIMITS = {
    "HR Screening": 4, "Technical": 5,
    "Hands-on Discussion": 2, "Final HR Discussion": 4,
}
ROUND_PASS_SCORE = {
    "HR Screening": 6, "Technical": 6,
    "Hands-on Discussion": 6, "Final HR Discussion": 6,
}

# ─────────────────────────────────────────────────────────────────
# INTERVIEWER VOICES  (OpenAI TTS voices)
# ─────────────────────────────────────────────────────────────────
MALE_VOICES   = ["onyx", "echo"]
FEMALE_VOICES = ["nova", "shimmer", "alloy"]

# ─────────────────────────────────────────────────────────────────
# PANEL DEFINITIONS  (name, title, emoji-avatar, gender)
# For LiveKit video call: a real avatar image URL can be added here.
# ─────────────────────────────────────────────────────────────────
HR_NAMES = [
    ("Ananya Sharma",  "HR Screening Specialist",      "👩‍💼", "female"),
    ("Kavya Raman",    "Talent Acquisition Executive", "👩‍💼", "female"),
    ("Rohit Verma",    "HR Recruiter",                 "👨‍💼", "male"),
    ("Arjun Menon",    "Recruitment Specialist",        "👨‍💼", "male"),
    ("Preethi Nair",   "Talent Sourcing Specialist",   "👩‍💼", "female"),
    ("Karthik Rajan",  "HR Screening Manager",         "👨‍💼", "male"),
    ("Divya Pillai",   "People Operations Executive",  "👩‍💼", "female"),
    ("Suresh Iyer",    "Recruitment Coordinator",      "👨‍💼", "male"),
]
TECH_NAMES = [
    ("Rahul Mehta",    "QA Automation Lead",          "👨‍💻", "male"),
    ("Sneha Rao",      "Test Architect",               "👩‍💻", "female"),
    ("David Martin",   "Engineering Manager",          "👨‍💼", "male"),
    ("Arjun Nair",     "Senior Test Manager",          "👨‍💻", "male"),
    ("Lisa Keller",    "Quality Engineering Lead",     "👩‍💻", "female"),
    ("Vikram Bhatia",  "Principal Software Engineer",  "👨‍💻", "male"),
    ("Meera Krishnan", "Staff Test Engineer",          "👩‍💻", "female"),
    ("Jason Fernandez","DevOps Lead",                  "👨‍💻", "male"),
    ("Pooja Sharma",   "SDET Manager",                 "👩‍💻", "female"),
    ("Rishi Kapoor",   "Platform Engineering Lead",    "👨‍💻", "male"),
]
HANDS_ON_NAMES = [
    ("Vikram Shah",    "Hands-on Coding Evaluator",  "👨‍💻", "male"),
    ("Neha Krishnan",  "Database Assessment Lead",   "👩‍💻", "female"),
    ("Arun Balaji",    "Practical Skills Evaluator", "👨‍💻", "male"),
    ("Deepa Thomas",   "Technical Assessment Lead",  "👩‍💻", "female"),
    ("Sanjay Gupta",   "Coding Interview Specialist","👨‍💻", "male"),
]
FINAL_HR_NAMES = [
    ("Priya Nair",     "Senior HR Manager",           "👩‍💼", "female"),
    ("Nisha Kapoor",   "HR Business Partner",          "👩‍💼", "female"),
    ("Mark Thomas",    "People Operations Manager",    "👨‍💼", "male"),
    ("Ravi Kumar",     "Talent Manager",               "👨‍💼", "male"),
    ("Sunita Menon",   "VP of Human Resources",        "👩‍💼", "female"),
    ("George Mathew",  "Chief People Officer",         "👨‍💼", "male"),
    ("Lakshmi Devi",   "Senior Talent Partner",        "👩‍💼", "female"),
    ("Ajay Srikanth",  "Compensation & Benefits Lead", "👨‍💼", "male"),
]

# ─────────────────────────────────────────────────────────────────
# DATABASE  (shared with livekit_worker.py)
# ─────────────────────────────────────────────────────────────────
def db_init():
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS live_scores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, round_name TEXT, question_no INTEGER,
        interviewer TEXT, question TEXT, answer TEXT,
        coach TEXT, score REAL, decision TEXT, comments TEXT,
        behaviour TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS round_state(
        session_id TEXT PRIMARY KEY, round_name TEXT,
        question_count INTEGER, status TEXT, updated_at TEXT)""")
    c.commit(); c.close()

db_init()

def db_live_scores(sid):
    c = sqlite3.connect(DB_PATH)
    cur = c.execute("SELECT * FROM live_scores WHERE session_id=? ORDER BY id", (sid,))
    cols = ["id","session_id","round_name","question_no","interviewer",
            "question","answer","coach","score","decision","comments","behaviour","created_at"]
    rows = [dict(zip(cols,r)) for r in cur.fetchall()]
    c.close(); return rows

def db_round_state(sid):
    c = sqlite3.connect(DB_PATH)
    cur = c.execute("SELECT round_name,question_count,status FROM round_state WHERE session_id=?", (sid,))
    r = cur.fetchone(); c.close()
    return {"round_name":r[0],"question_count":r[1],"status":r[2]} if r else None

def db_write_round_state(sid, round_name, qcount, status="active"):
    c = sqlite3.connect(DB_PATH)
    c.execute("""INSERT OR REPLACE INTO round_state
        (session_id,round_name,question_count,status,updated_at) VALUES(?,?,?,?,?)""",
        (sid, round_name, qcount, status, str(datetime.now())))
    c.commit(); c.close()

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG + CSS  (preserve existing look, enhance with new elements)
# ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Interviewer", layout="wide")

st.markdown("""
<style>
/* ── Global ── */
.stApp{background:linear-gradient(135deg,#eef2ff 0%,#ffffff 45%,#fdf2f8 100%)}
/* ── Header ── */
.main-title{
    background:linear-gradient(90deg,#2563eb,#7c3aed);
    color:white;padding:24px;border-radius:22px;
    margin-bottom:22px;box-shadow:0 8px 22px rgba(0,0,0,.15)
}
/* ── Cards ── */
.card{border-radius:20px;padding:20px;background:white;
      margin-bottom:16px;box-shadow:0 8px 24px rgba(0,0,0,.08);
      border:1px solid #eef0f6}
.interviewer-card{border-left:8px solid #4f46e5}
.candidate-card  {border-left:8px solid #16a34a}
.livekit-card    {border-left:8px solid #06b6d4}
.score-card      {border-left:8px solid #f59e0b}
/* ── Avatar area ── */
.avatar{font-size:56px;line-height:1.1}
.name  {font-size:22px;font-weight:800;color:#111827}
.title {font-size:14px;color:#6b7280}
/* ── Speaking wave ── */
.wave{display:flex;align-items:flex-end;gap:4px;height:28px;margin-top:10px}
.wave span{width:5px;background:#4f46e5;border-radius:4px;animation:wave .9s infinite ease-in-out}
.wave span:nth-child(1){animation-delay:0s}
.wave span:nth-child(2){animation-delay:.12s}
.wave span:nth-child(3){animation-delay:.24s}
.wave span:nth-child(4){animation-delay:.36s}
.wave span:nth-child(5){animation-delay:.48s}
@keyframes wave{0%,100%{height:5px}50%{height:22px}}
/* ── Live badge ── */
.live-badge{display:inline-block;background:#ef4444;color:white;
            padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;
            animation:livepulse 1.4s infinite}
@keyframes livepulse{0%,100%{opacity:1}50%{opacity:.45}}
/* ── Language pill ── */
.lang-pill{display:inline-block;background:#ede9fe;color:#5b21b6;
           padding:3px 12px;border-radius:14px;font-size:12px;font-weight:600;margin-left:8px}
/* ── Behaviour bars ── */
.b-wrap{margin-top:10px}
.b-lbl{font-size:12px;color:#6b7280;margin-bottom:2px}
.b-bg{background:#e5e7eb;border-radius:6px;height:8px}
.b-fill{height:8px;border-radius:6px;transition:width .6s ease}
/* ── Avatar image (LiveKit) ── */
.avatar-img-wrap{position:relative;display:inline-block}
.avatar-img{width:120px;height:120px;border-radius:50%;
            object-fit:cover;border:4px solid #4f46e5}
.avatar-emoji{font-size:90px;line-height:1}
.speaking-ring{position:absolute;inset:-6px;border-radius:50%;
               border:3px solid #4f46e5;animation:ring 1.2s infinite}
@keyframes ring{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.06)}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def pick_voice(gender):
    return random.choice(MALE_VOICES if gender == "male" else FEMALE_VOICES)

def create_panel():
    """Pick a DIFFERENT random person for EVERY round.
    Gender is synced to voice — female name = female voice, male name = male voice.
    Ensures no two rounds get the same person.
    """
    def p(t):
        gender = t[3]
        # CRITICAL: voice must match gender of the name shown
        voice = pick_voice(gender)
        return {
            "name":   t[0],
            "title":  t[1],
            "avatar": t[2],
            "gender": gender,
            "voice":  voice,    # female name → nova/shimmer/alloy, male → onyx/echo
        }

    # Pick random people — shuffle to avoid same person in multiple rounds
    hr_choice  = random.choice(HR_NAMES)
    fhr_choice = random.choice(FINAL_HR_NAMES)
    ho_choice  = random.choice(HANDS_ON_NAMES)

    # For Technical: pick 3 DIFFERENT people (no repeats in the panel)
    tech_pool = list(TECH_NAMES)
    random.shuffle(tech_pool)
    tech_choices = tech_pool[:3]

    return {
        "HR Screening":       [p(hr_choice)],
        "Technical":          [p(t) for t in tech_choices],
        "Hands-on Discussion":[p(ho_choice)],
        "Final HR Discussion":[p(fhr_choice)],
    }

def wave_html():
    return '<div class="wave"><span></span><span></span><span></span><span></span><span></span></div>'

def speaking_avatar_html(person, speaking=False):
    ring = '<div class="speaking-ring"></div>' if speaking else ''
    return f"""
<div class="card interviewer-card">
  <div class="avatar-img-wrap">
    <div class="avatar-emoji">{person["avatar"]}</div>
    {ring}
  </div>
  <div class="name">{person["name"]}
    <span class="lang-pill">{st.session_state.language}</span>
  </div>
  <div class="title">{person["title"]}</div>
  {wave_html() if speaking else ""}
</div>"""

def candidate_html(name, speaking=False):
    return f"""
<div class="card candidate-card">
  <div class="avatar">🧑‍💼</div>
  <div class="name">{name}</div>
  <div class="title">Candidate</div>
  {wave_html() if speaking else ""}
</div>"""

def score_card_html(score, decision, comments, behaviour=None):
    color = "#16a34a" if decision == "Selected" else "#dc2626"
    bbars = ""
    if behaviour:
        def bar(lbl, val, col):
            return f"""<div class="b-lbl">{lbl}</div>
<div class="b-bg"><div class="b-fill" style="width:{min(100,val or 0)}%;background:{col}"></div></div>"""
        bbars = f"""<div class="b-wrap">
          {bar("Confidence",  behaviour.get("confidence",0),  "#6366f1")}
          {bar("Speech pace", behaviour.get("pace_score",0),  "#0891b2")}
          {bar("Clarity",     behaviour.get("clarity",0),     "#16a34a")}
          <div style="font-size:12px;color:#6b7280;margin-top:4px">
            Tone: {behaviour.get("tone","—")} · Hesitation: {behaviour.get("hesitation","—")}<br>
            {behaviour.get("summary","")}
          </div></div>"""
    return f"""
<div class="card score-card">
  <div style="font-size:34px;font-weight:900;color:{color}">{score}/10</div>
  <div style="font-size:18px;font-weight:700;color:{color}">{decision}</div>
  <div style="color:#374151;margin-top:6px;font-size:14px">{comments}</div>
  {bbars}
</div>"""

# ─────────────────────────────────────────────────────────────────
# LIVEKIT TOKEN  (candidate joins, agent is dispatched automatically)
# ─────────────────────────────────────────────────────────────────
def make_livekit_token(room_name, participant_name):
    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        return None
    person   = get_interviewer()
    lang_cfg = LANGUAGES[st.session_state.language]
    meta = json.dumps({
        "session_id":         st.session_state.session_id,
        "candidate_name":     st.session_state.candidate_name,
        "role":               st.session_state.role,
        "language":           st.session_state.language,
        "language_code":      lang_cfg["code"],
        "whisper_lang":       lang_cfg["whisper"],
        "tts_instructions":   lang_cfg["tts_instructions"],
        "round_name":         st.session_state.round_name,
        "question_limit":     ROUND_QUESTION_LIMITS[st.session_state.round_name],
        "pass_score":         ROUND_PASS_SCORE[st.session_state.round_name],
        "resume_text":        st.session_state.resume_text[:4000],
        "jd_text":            st.session_state.jd_text[:3000],
        "company_text":       st.session_state.company_text[:2000],
        "interviewer_name":   person["name"],
        "interviewer_title":  person["title"],
        "interviewer_gender": person["gender"],
        "interviewer_avatar": person["avatar"],
        "tts_voice":          person["voice"],
        "history_summary":    recent_history(),
    })
    tok = (api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
           .with_identity(participant_name)
           .with_name(participant_name)
           .with_grants(api.VideoGrants(
               room_join=True, room=room_name,
               can_publish=True, can_subscribe=True))
           .with_room_config(api.RoomConfiguration(agents=[
               api.RoomAgentDispatch(agent_name=LIVEKIT_AGENT_NAME, metadata=meta)
           ])))
    return tok.to_jwt()

def livekit_room_url(token, mode, person):
    call_mode = "video" if mode == "LiveKit Video Call" else "audio"
    params = urlencode({
        "serverUrl":         LIVEKIT_URL,
        "token":             token,
        "mode":              call_mode,
        "interviewerName":   person["name"],
        "interviewerTitle":  person["title"],
        "interviewerGender": person["gender"],
        "interviewerAvatar": person["avatar"],
        "language":          st.session_state.language,
        "sessionId":         st.session_state.session_id,
        "candidateName":     st.session_state.candidate_name,
    })
    return f"{LIVEKIT_FRONTEND_URL}?{params}"

# ─────────────────────────────────────────────────────────────────
# RESUME / COMPANY SCRAPING
# ─────────────────────────────────────────────────────────────────
def scrape(url):
    pages = ["", "/about", "/company", "/services", "/careers"]
    out = ""
    for p in pages:
        try:
            r = requests.get(url.rstrip("/")+p, timeout=8,
                             headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code >= 400: continue
            soup = BeautifulSoup(r.text, "html.parser")
            for t in soup(["script","style","noscript"]): t.decompose()
            text = " ".join(soup.get_text(separator=" ").split())
            if len(text) > 300: out += f"\n\n{url}{p}\n{text[:3000]}"
        except: pass
    return out[:10000]

def parse_resume(f):
    path = RESUME_DIR / f"{uuid.uuid4()}_{f.name}"
    path.write_bytes(f.getbuffer())
    if f.name.lower().endswith(".pdf"):
        return "".join(p.extract_text() or "" for p in PdfReader(path).pages)
    if f.name.lower().endswith(".docx"):
        return "\n".join(p.text for p in Document(path).paragraphs)
    return ""

def extract_name(text):
    try:
        r = oai.chat.completions.create(model="gpt-4o-mini", temperature=0,
            messages=[{"role":"user","content":
                f"Extract ONLY the candidate full name from this resume. If not found return Candidate.\n\n{text[:2500]}"}])
        return re.sub(r"[^a-zA-Z\s]","",r.choices[0].message.content.strip()).strip() or "Candidate"
    except: return "Candidate"

# ─────────────────────────────────────────────────────────────────
# TTS  (language-aware via instructions parameter)
# ─────────────────────────────────────────────────────────────────
def tts(text, voice, language):
    lang_cfg = LANGUAGES[language]
    speech = oai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        extra_body={"instructions": lang_cfg["tts_instructions"]},
    )
    path = AUDIO_DIR / f"tts_{uuid.uuid4()}.mp3"
    speech.stream_to_file(path)
    return path

# ─────────────────────────────────────────────────────────────────
# STT  (language-aware)
# ─────────────────────────────────────────────────────────────────
def analyse_voice(audio_path):
    """
    Analyse recorded audio for voice quality.
    Thresholds kept LOW (100/400) to match typical laptop microphones.
    Same sensitivity as EnergyVAD used in LiveKit modes.
    """
    if audioop is None:
        # Python 3.13+ — skip analysis, don't block the answer
        return "Voice analysis unavailable.", True
    try:
        with wave.open(str(audio_path),"rb") as wf:
            frames = wf.readframes(wf.getnframes())
            dur    = wf.getnframes() / float(wf.getframerate())
            rms    = audioop.rms(frames, wf.getsampwidth())

        # Very short clip — but still try STT, don't hard-block
        if dur < 0.5:
            return "Recording very short — please record again.", False

        # RMS thresholds lowered to 100/400 (was 350/900)
        # This matches the EnergyVAD sensitivity used in LiveKit modes
        if rms < 100:
            return "Microphone not detected. Check mic and try again.", False
        if rms < 400:
            return "Voice audible. Speak a little louder for best results.", True
        return "Voice clear.", True
    except Exception:
        # Don't block on analysis errors — let STT try anyway
        return "Voice quality unknown.", True

def stt(audio_file, language):
    path = AUDIO_DIR / f"user_{uuid.uuid4()}.wav"
    path.write_bytes(audio_file.getbuffer())
    vfb, vok = analyse_voice(path)
    lang_code = LANGUAGES[language]["whisper"]
    with open(path,"rb") as f:
        tx = oai.audio.transcriptions.create(model="whisper-1", file=f, language=lang_code)
    return tx.text, vfb, vok

def answer_quality(ans):
    words  = re.findall(r"\w+", ans.lower())
    unique = set(words)
    fillers= {"aaa","aa","umm","um","hmm","mmm","ah","uh","blah","noise","test","hello"}
    if len(words) < 8:  return False, "Answer too short."
    if len(unique) <= 4: return False, "Answer too repetitive."
    if sum(1 for w in words if w in fillers) >= max(3, len(words)//2):
        return False, "Answer seems like filler words."
    if sum(c.isalpha() for c in ans) < 20: return False, "Not enough meaningful content."
    return True, "OK"

# ─────────────────────────────────────────────────────────────────
# AUTOGEN AGENTS  (language-aware)
# ─────────────────────────────────────────────────────────────────
def make_agents(language):
    mc = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    lang = language   # alias for f-strings

    interviewer = AssistantAgent("AI_Interviewer", model_client=mc,
        system_message=f"""
You are a realistic interview panel member conducting a professional job interview.
⚠️ CRITICAL: You MUST respond ONLY in {lang}. Every single word must be in {lang}.
Do NOT use English unless {lang} IS English. No mixing of languages whatsoever.
Ask exactly one question per turn. Return only the spoken question — no labels, no metadata.

Round-specific question types:
• HR Screening     : role match, skills match, experience, notice period, current/expected salary, location, shift flexibility.
• Technical        : resume-based and JD-based technical depth questions and follow-ups.
• Hands-on Discussion: coding problems, SQL queries, API testing, test automation framework design.
• Final HR Discussion: motivation, company interest, long-term stability, salary negotiation, joining confirmation.
""")

    coach = AssistantAgent("Coach_Agent", model_client=mc,
        system_message=f"""
You are a professional interview coach.
⚠️ CRITICAL: Respond ONLY in {lang}. Every single word must be in {lang}. No English unless {lang} is English.
After reviewing the candidate's answer, give structured feedback — be strict if answer is vague or too short:
1. Good points
2. What to improve
3. A better sample answer
4. Communication / tone feedback
Keep it concise — under 100 words total.
""")

    scorer = AssistantAgent("Score_Agent", model_client=mc,
        system_message="""
Score the candidate's answer strictly. Return EXACTLY this format (no extra lines):

Score: X/10
Decision: Selected or Rejected
Interviewer Comments: one sentence

Strict rules:
• Too short / gibberish / filler / off-topic → 0 to 2
• Partially relevant, lacks depth              → 3 to 5
• Clear, relevant, complete                    → 6 to 8
• Excellent, specific, impressive              → 9 to 10
""")

    behaviour = AssistantAgent("Behaviour_Agent", model_client=mc,
        system_message="""
Analyse the candidate's answer text for behavioural signals.
Return EXACTLY one JSON object on a single line — no extra text:
{"confidence":75,"pace_score":80,"clarity":70,"hesitation":"low","tone":"professional","summary":"One sentence."}
confidence / pace_score / clarity = integer 0–100.
hesitation = "low" | "medium" | "high"
tone = "professional" | "nervous" | "confident" | "unclear"
""")

    user_proxy = UserProxyAgent("User_Proxy", description="Human candidate.")
    return interviewer, coach, scorer, behaviour, user_proxy

async def run_agent(agent, task):
    r = await agent.run(task=task)
    return r.messages[-1].content

def sync(coro):
    return asyncio.run(coro)

# ─────────────────────────────────────────────────────────────────
# STATE HELPERS
# ─────────────────────────────────────────────────────────────────
def get_interviewer():
    panel = st.session_state.panel[st.session_state.round_name]
    if st.session_state.round_name == "Technical":
        return panel[st.session_state.question_count % len(panel)]
    return panel[0]

def recent_history():
    out = ""
    for h in st.session_state.history[-4:]:
        out += f"\nQ: {h.get('question','')}\nA: {h.get('answer','')}\nScore: {h.get('numeric_score',0)}/10\n"
    return out

def round_avg(rname):
    s = [x["numeric_score"] for x in st.session_state.history if x.get("round")==rname]
    return sum(s)/len(s) if s else 0

def round_last_comment(rname):
    items = [x for x in st.session_state.history if x.get("round")==rname]
    return items[-1].get("interviewer_comments","") if items else ""

def advance_round():
    cur  = st.session_state.round_name

    # CRITICAL: Only advance if this round actually has scores in DB
    # Prevents phantom "Rejected" for rounds that never happened
    live_rows = db_live_scores(st.session_state.session_id)
    cur_scores = [r for r in live_rows if r["round_name"] == cur]
    if not cur_scores:
        logger.warning(f"advance_round called for {cur} but no scores in DB — skipping")
        return  # Don't advance if no questions were answered

    avg  = round_avg(cur)
    dec  = "Selected" if avg >= ROUND_PASS_SCORE[cur] else "Rejected"
    st.session_state.round_results[cur] = {
        "decision": dec, "average_score": avg,
        "comments": f"{round_last_comment(cur)} Avg: {avg:.2f}/10.",
    }
    st.session_state.current_question = ""
    st.session_state.question_round   = ""
    if dec == "Rejected":
        st.session_state.stage = "final"; return
    idx = ROUND_ORDER.index(cur)
    if idx < len(ROUND_ORDER)-1:
        nxt = ROUND_ORDER[idx+1]
        st.session_state.update({
            "round_name": nxt, "question_count": 0,
            "current_question": "", "question_round": "",
            "round_intro_done": False, "round_intro_text": "",
            "livekit_room": f"interview-{uuid.uuid4()}",
        })
    else:
        st.session_state.stage = "final"

def skip_round():
    cur = st.session_state.round_name
    st.session_state.round_results[cur] = {
        "decision":"Skipped","average_score":0,
        "comments":f"{cur} skipped by candidate.",
    }
    idx = ROUND_ORDER.index(cur)
    if idx < len(ROUND_ORDER)-1:
        nxt = ROUND_ORDER[idx+1]
        st.session_state.update({
            "round_name": nxt, "question_count": 0,
            "current_question": "", "question_round": "",
            "round_intro_done": False, "round_intro_text": "",
            "livekit_room": f"interview-{uuid.uuid4()}",
        })
    else:
        st.session_state.stage = "final"

def parse_score(text):
    score=0.0; decision="Rejected"; comments="No comments."
    for line in text.splitlines():
        ll = line.lower()
        if ll.startswith("score:"):
            try: score=float(line.split(":")[1].split("/")[0].strip())
            except: pass
        elif ll.startswith("decision:"):
            decision = "Selected" if "selected" in ll else "Rejected"
        elif ll.startswith("interviewer comments:"):
            comments = line.split(":",1)[1].strip()
    return score, decision, comments

def parse_behaviour(text):
    try:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m: return json.loads(m.group())
    except: pass
    return {"confidence":50,"pace_score":50,"clarity":50,
            "hesitation":"medium","tone":"neutral","summary":"Could not evaluate."}

def save_json(data):
    p = STORAGE_DIR / f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    p.write_text(json.dumps(data, indent=4, ensure_ascii=False))
    return p

# ─────────────────────────────────────────────────────────────────
# LIVE SCORE SYNC  (pulls from SQLite written by livekit_worker)
# ─────────────────────────────────────────────────────────────────
def sync_live_scores():
    rows  = db_live_scores(st.session_state.session_id)
    known = {(x.get("round"), x.get("question_no")) for x in st.session_state.history}
    added = False
    for row in rows:
        key = (row["round_name"], row["question_no"])
        if key in known: continue
        bdata = None
        try: bdata = json.loads(row.get("behaviour") or "{}")
        except: pass
        st.session_state.history.append({
            "round": row["round_name"], "interviewer_name": row["interviewer"],
            "question": row["question"], "answer": row["answer"],
            "coach_feedback": row["coach"], "numeric_score": row["score"],
            "answer_decision": row["decision"], "interviewer_comments": row["comments"],
            "behaviour": bdata, "question_no": row["question_no"],
            "interview_mode": st.session_state.interview_mode,
        })
        st.session_state.scores.append(row["score"])
        st.session_state.question_count = max(st.session_state.question_count, row["question_no"])
        added = True
    # Guard: only advance round once — check it hasn't been processed already
    rs = db_round_state(st.session_state.session_id)
    already_advanced = st.session_state.round_results.get(st.session_state.round_name)
    if (rs and rs["status"] == "completed"
            and rs["round_name"] == st.session_state.round_name
            and not already_advanced):
        advance_round()
    return added

# ─────────────────────────────────────────────────────────────────
# SESSION STATE  INIT
# ─────────────────────────────────────────────────────────────────
def init_state():
    defs = {
        "stage": "setup", "session_id": str(uuid.uuid4()),
        "resume_text": "", "jd_text": "", "company_url": "",
        "company_text": "", "role": "", "candidate_name": "Candidate",
        "language": "English", "interview_mode": "Streamlit Voice Mode",
        "round_name": "HR Screening", "question_count": 0,
        "current_question": "", "question_round": "",
        "round_intro_done": False, "round_intro_text": "",
        "history": [], "scores": [], "round_results": {},
        "panel": None, "livekit_room": "", "last_sync": 0,
    }
    for k,v in defs.items():
        if k not in st.session_state: st.session_state[k] = v
    if st.session_state.panel is None:
        st.session_state.panel = create_panel()

init_state()

# ─────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-title">
  <h1>🎙️ AI Interviewer with AutoGen + LiveKit</h1>
  <p>HR Screening → Technical → Hands-on Discussion → Final HR Discussion</p>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Interview Settings")

    # Language selector — drives STT, TTS, AutoGen
    lang_sel = st.selectbox("Interview Language", list(LANGUAGES.keys()),
                             index=list(LANGUAGES.keys()).index(st.session_state.language))
    if lang_sel != st.session_state.language:
        st.session_state.language = lang_sel
        # reset intro so it regenerates in new language
        st.session_state.round_intro_text = ""
        st.session_state.round_intro_done = False

    # Mode selector
    mode_options = ["Streamlit Voice Mode", "LiveKit Audio Call", "LiveKit Video Call"]
    mode_sel = st.selectbox("Interview Mode", mode_options,
                             index=mode_options.index(st.session_state.interview_mode))
    st.session_state.interview_mode = mode_sel

    # Info callout for LiveKit modes
    if mode_sel != "Streamlit Voice Mode":
        st.info(
            "**LiveKit mode selected.**\n\n"
            "• Start `python livekit_worker.py dev` in a terminal.\n"
            "• Start the React frontend `cd livekit-interview-ui && npm run dev`.\n"
            "• Click **Join Interview Room** to open your call."
        )

    st.metric("Current Round",  st.session_state.round_name)
    limit = ROUND_QUESTION_LIMITS.get(st.session_state.round_name, 4)
    # Get real count from DB (more accurate than session state)
    _live_rows = db_live_scores(st.session_state.session_id)
    _real_count = len([r for r in _live_rows if r["round_name"] == st.session_state.round_name])
    _display_count = max(st.session_state.question_count, _real_count)
    st.metric("Questions", f"{_display_count} / {limit}")
    st.caption(f"Session `{st.session_state.session_id[:8]}…` · Lang: **{st.session_state.language}**")

    st.markdown("### Round Status")
    for r in ROUND_ORDER:
        res = st.session_state.round_results.get(r)
        qlimit = ROUND_QUESTION_LIMITS.get(r, 4)
        if res:
            if res["decision"] == "Selected":
                st.success(f"✅ {r} — {res['average_score']:.1f}/10 ({qlimit}Q) — **Selected**")
            elif res["decision"] == "Skipped":
                st.warning(f"⏭ {r} — Skipped")
            else:
                st.error(f"❌ {r} — {res['average_score']:.1f}/10 ({qlimit}Q) — **Rejected**")
        elif r == st.session_state.round_name:
            st.info(f"🔴 {r} — In Progress ({st.session_state.question_count}/{qlimit} questions)")
        else:
            st.info(f"⏳ {r} — Pending")

    if st.button("🔄 Reset Interview"):
        st.session_state.clear(); st.rerun()

# ─────────────────────────────────────────────────────────────────
# SETUP PAGE
# ─────────────────────────────────────────────────────────────────
if st.session_state.stage == "setup":
    st.subheader("Upload Resume and Enter Job Details")

    resume  = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf","docx"])
    jd      = st.text_area("Paste Job Description", height=220)
    role    = st.text_input("Target Role", placeholder="e.g. QA Test Manager")
    co_url  = st.text_input("Company Website URL", placeholder="https://www.company.com")

    if st.button("🚀 Start Interview"):
        errors = []
        if not resume:   errors.append("Upload your resume.")
        if not jd.strip(): errors.append("Paste the job description.")
        if not role.strip(): errors.append("Enter the target role.")
        if not co_url.strip(): errors.append("Enter the company website URL.")
        for e in errors: st.error(e)
        if not errors:
            with st.spinner("Parsing resume and scraping company website…"):
                rtxt = parse_resume(resume)
                name = extract_name(rtxt)
                ctxt = scrape(co_url.strip())
            st.session_state.update({
                "resume_text": rtxt, "jd_text": jd,
                "company_url": co_url.strip(), "company_text": ctxt,
                "role": role, "candidate_name": name,
                "stage": "interview",
                "panel": create_panel(),
                "livekit_room": f"interview-{uuid.uuid4()}",
            })
            db_write_round_state(st.session_state.session_id, "HR Screening", 0, "active")
            st.rerun()

# ─────────────────────────────────────────────────────────────────
# INTERVIEW PAGE
# ─────────────────────────────────────────────────────────────────
elif st.session_state.stage == "interview":

    # Cache agents per language — avoid recreating on every Streamlit rerender
    lang_key = f"agents_{st.session_state.language}"
    if lang_key not in st.session_state:
        st.session_state[lang_key] = make_agents(st.session_state.language)
    iagent, cagent, sagent, bagent, _ = st.session_state[lang_key]
    person = get_interviewer()
    mode   = st.session_state.interview_mode

    left, right = st.columns([2, 1])

    with right:
        st.markdown(speaking_avatar_html(person, speaking=False), unsafe_allow_html=True)
        st.markdown(candidate_html(st.session_state.candidate_name), unsafe_allow_html=True)
        st.markdown("### Panel")
        for p in st.session_state.panel[st.session_state.round_name]:
            st.write(f"{p['avatar']} **{p['name']}** — {p['title']}")

    # ══════════════════════════════════════════════════════════════
    # LIVEKIT AUDIO / VIDEO MODE
    # ══════════════════════════════════════════════════════════════
    if mode in ("LiveKit Audio Call", "LiveKit Video Call"):
        with right:
            if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
                st.error("LiveKit credentials missing in .env")
            else:
                if not st.session_state.livekit_room:
                    st.session_state.livekit_room = f"interview-{uuid.uuid4()}"
                token   = make_livekit_token(st.session_state.livekit_room,
                                              st.session_state.candidate_name)
                room_url= livekit_room_url(token, mode, person)
                st.markdown(f"""
<div class="card livekit-card">
  <div class="avatar-emoji">{person["avatar"]}</div>
  <div class="name">{person["name"]}</div>
  <div class="title">{person["title"]}</div>
  <span class="live-badge">● LIVE</span>
  <div style="margin-top:8px;font-size:12px;color:#0891b2">
    Language: <b>{st.session_state.language}</b> ·
    Mode: <b>{'📹 Video' if mode=='LiveKit Video Call' else '🎧 Audio'}</b>
  </div>
</div>""", unsafe_allow_html=True)
                st.link_button("🎥 Join Interview Room", room_url, use_container_width=True)

                # Show close instruction when round is complete
                _rs = db_round_state(st.session_state.session_id)
                _cur_result = st.session_state.round_results.get(st.session_state.round_name)
                if _cur_result or (_rs and _rs["status"] == "completed"):
                    st.info("✅ Round complete! **Close the interview room tab** then click Refresh Scores here.")
                    if st.button("🔄 Check Round Result", type="primary", use_container_width=True):
                        sync_live_scores()
                        st.rerun()

                with st.expander("Connection details"):
                    st.code(f"Server : {LIVEKIT_URL}")
                    st.code(f"Room   : {st.session_state.livekit_room}")
                    st.code(f"Token  : {token[:60]}…")

        with left:
            st.subheader(f"🔴 LIVE — {st.session_state.round_name} · {st.session_state.language}")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Refresh Scores"):
                    added = sync_live_scores()
                    st.success("Updated!" if added else "No new scores.")
                    st.rerun()
            with col2:
                if st.session_state.round_name == "Hands-on Discussion":
                    if st.button("⏭ Skip Round"):
                        skip_round(); st.rerun()
            with col3:
                # Force complete if last answer was missed
                _live_count = len([r for r in db_live_scores(st.session_state.session_id)
                                   if r["round_name"] == st.session_state.round_name])
                _limit = ROUND_QUESTION_LIMITS.get(st.session_state.round_name, 4)
                if _live_count >= max(1, _limit - 1):  # at least n-1 questions done
                    if st.button("✅ Complete Round", help="Use if last answer wasn't captured"):
                        st.session_state.question_count = _live_count
                        # Sync scores first
                        sync_live_scores()
                        advance_round()
                        st.rerun()

            # Force periodic refresh using time.sleep + st.rerun()
            # This is the ONLY reliable way to auto-refresh in Streamlit
            sync_live_scores()
            if not st.session_state.round_results.get(st.session_state.round_name):
                rs = db_round_state(st.session_state.session_id)
                if rs and rs["status"] == "completed" and rs["round_name"] == st.session_state.round_name:
                    advance_round()
            time.sleep(4)
            st.rerun()

            st.info(
                f"**How the live call works:**\n\n"
                f"1. Click **Join Interview Room** (right panel).\n"
                f"2. The AI interviewer ({person['name']}) will greet you in **{st.session_state.language}**.\n"
                f"3. {'Your camera will be ON. The AI is represented as an animated avatar.' if mode=='LiveKit Video Call' else 'Audio only — no camera required.'}\n"
                f"4. Speak your answers; scores appear below automatically."
            )

            # ── Round summary ────────────────────────────────────
            cur_round = st.session_state.round_name
            cur_result = st.session_state.round_results.get(cur_round)

            if cur_result:
                # Round is complete — show result and next round button
                dec = cur_result["decision"]
                avg = cur_result["average_score"]
                qcount = st.session_state.question_count

                if dec == "Selected":
                    st.success(f"✅ **{cur_round} Complete** — Avg Score: {avg:.1f}/10 — **{dec}**")
                    idx = ROUND_ORDER.index(cur_round)
                    if idx < len(ROUND_ORDER) - 1:
                        nxt = ROUND_ORDER[idx + 1]
                        st.info(f"🎉 You passed! Next round: **{nxt}**")
                        if st.button(f"▶ Start {nxt}", type="primary", use_container_width=True):
                            st.session_state.update({{
                                "round_name": nxt, "question_count": 0,
                                "current_question": "", "question_round": "",
                                "round_intro_done": False, "round_intro_text": "",
                                "livekit_room": f"interview-{{uuid.uuid4()}}",
                            }})
                            st.rerun()
                    else:
                        st.balloons()
                        st.success("🎊 All rounds complete! Proceeding to final report.")
                        if st.button("📊 View Final Report", type="primary"):
                            st.session_state.stage = "final"; st.rerun()
                else:
                    st.error(f"❌ **{cur_round} Complete** — Avg Score: {avg:.1f}/10 — **{dec}**")
                    st.warning(f"Unfortunately you did not pass the {cur_round}. Interview ended.")
                    if st.button("📊 View Report", type="primary"):
                        st.session_state.stage = "final"; st.rerun()

            st.markdown("### Live Scores & Transcript")
            live_rows = db_live_scores(st.session_state.session_id)
            if not live_rows:
                st.info("Waiting for your first answer… (scores appear after each question)")
            for row in live_rows:
                bdata = None
                try: bdata = json.loads(row.get("behaviour") or "{}")
                except: pass
                with st.expander(
                        f"Q{row['question_no']} · {row['round_name']} · "
                        f"{row['score']}/10 · {row['decision']}"):
                    st.markdown(f"**Interviewer:** {row['interviewer']}")
                    st.info(f"**Q:** {row['question']}")
                    st.success(f"**A:** {row['answer']}")
                    st.warning(f"**Coach:** {row['coach']}")
                    st.markdown(score_card_html(row["score"], row["decision"],
                                                row["comments"], bdata),
                                unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # STREAMLIT VOICE MODE
    # ══════════════════════════════════════════════════════════════
    else:
        with left:
            st.subheader(f"{st.session_state.round_name} Round · {st.session_state.language}")

            if st.session_state.round_name == "Hands-on Discussion":
                if st.button("⏭ Skip Hands-on Discussion"):
                    skip_round(); st.rerun()

            # Round complete banner — works for ALL 3 modes
            _r = st.session_state.round_results.get(st.session_state.round_name)
            if _r:
                _d = _r["decision"]; _a = _r["average_score"]
                _i = ROUND_ORDER.index(st.session_state.round_name) if st.session_state.round_name in ROUND_ORDER else -1
                if _d == "Selected":
                    st.success(f"✅ **{st.session_state.round_name}** — {_a:.1f}/10 — **Selected!**")
                    if _i >= 0 and _i < len(ROUND_ORDER)-1:
                        _n = ROUND_ORDER[_i+1]
                        st.info(f"🎉 You passed! Next round: **{_n}**")
                        if st.button(f"▶ Start {_n}", type="primary", use_container_width=True):
                            st.session_state.update({
                                "round_name": _n, "question_count": 0,
                                "current_question": "", "question_round": "",
                                "round_intro_done": False, "round_intro_text": "",
                                "livekit_room": f"interview-{uuid.uuid4()}",
                            }); st.rerun()
                    else:
                        if st.button("📊 View Final Report", type="primary"):
                            st.session_state.stage = "final"; st.rerun()
                    st.stop()
                else:
                    st.error(f"❌ **{st.session_state.round_name}** — {_a:.1f}/10 — **Rejected**")
                    st.warning("You did not pass this round. Interview ended.")
                    if st.button("📊 View Report", type="primary"):
                        st.session_state.stage = "final"; st.rerun()
                    st.stop()

            # ── Round intro ──────────────────────────────────────
            if not st.session_state.round_intro_done:
                if not st.session_state.round_intro_text:
                    intro_prompt = f"""
You are {person['name']}, {person['title']}.
Candidate: {st.session_state.candidate_name}  |  Role: {st.session_state.role}
Round: {st.session_state.round_name}  |  Language: {st.session_state.language}
Company info: {st.session_state.company_text[:4000]}

Introduce yourself like a real interviewer ONLY in {st.session_state.language}.
If this is HR Screening, briefly mention the company.
Do NOT ask the first question yet. Keep it under 80 words.
"""
                    with st.spinner(f"Preparing introduction in {st.session_state.language}…"):
                        st.session_state.round_intro_text = sync(run_agent(iagent, intro_prompt))

                st.markdown(speaking_avatar_html(person, speaking=True), unsafe_allow_html=True)
                st.info(st.session_state.round_intro_text)
                if st.button(f"▶ Play Introduction ({st.session_state.language})"):
                    audio = tts(st.session_state.round_intro_text,
                                person["voice"], st.session_state.language)
                    st.audio(str(audio), format="audio/mp3")
                if st.button("➡ Continue to Questions"):
                    st.session_state.round_intro_done = True
                    st.session_state.current_question = ""
                    st.session_state.question_round   = ""
                    st.rerun()
                st.stop()

            # ── Sync question to current round ───────────────────
            if st.session_state.question_round != st.session_state.round_name:
                st.session_state.current_question = ""
                st.session_state.question_round   = ""

            # ── Generate question ────────────────────────────────
            if not st.session_state.current_question:
                qprompt = f"""
You are {person['name']}, {person['title']}.
Candidate: {st.session_state.candidate_name}
Resume: {st.session_state.resume_text[:5000]}
JD: {st.session_state.jd_text[:4000]}
Role: {st.session_state.role}
Current Round: {st.session_state.round_name}
Question Number: {st.session_state.question_count + 1}
Recent Q&A history: {recent_history()}

Ask the next question in {st.session_state.language}.
Return ONLY the spoken question. No metadata. Must belong to {st.session_state.round_name} only.

For HR Screening, cover these topics across the questions (one per question):
- Reason for job change
- Current and expected salary  
- Notice period
- Location / shift flexibility

For Technical, ask depth questions based on their resume and the JD.
For Hands-on Discussion, ask practical coding/SQL/automation scenarios.
For Final HR Discussion, ask about career goals, company fit, joining timeline.
"""
                with st.spinner(f"Preparing question {st.session_state.question_count+1}…"):
                    st.session_state.current_question = sync(run_agent(iagent, qprompt))
                    st.session_state.question_round   = st.session_state.round_name

            # ── Display question ─────────────────────────────────
            st.markdown(speaking_avatar_html(person, speaking=True), unsafe_allow_html=True)
            st.markdown("### Question")
            st.info(st.session_state.current_question)
            if st.button(f"▶ Play Question ({st.session_state.language})"):
                audio = tts(st.session_state.current_question,
                            person["voice"], st.session_state.language)
                st.audio(str(audio), format="audio/mp3")

            # ── Candidate answer ─────────────────────────────────
            st.markdown("### Your Answer")
            st.markdown(candidate_html(st.session_state.candidate_name, speaking=True),
                        unsafe_allow_html=True)
            audio_ans = st.audio_input("🎤 Record your answer")
            typed_ans = ""
            if st.session_state.round_name in ["Technical","Hands-on Discussion"]:
                typed_ans = st.text_area("Or type your answer (Technical/Hands-on)")

            if st.button("✅ Submit Answer"):
                # Resolve answer text
                if audio_ans:
                    ans, vfb, vok = stt(audio_ans, st.session_state.language)
                elif typed_ans.strip():
                    ans, vfb, vok = typed_ans.strip(), "Typed answer.", True
                else:
                    st.error("Please record or type your answer."); st.stop()

                cok, creason = answer_quality(ans)

                if not vok or not cok:
                    sr  = f"Score: 1/10\nDecision: Rejected\nInterviewer Comments: {creason} {vfb}"
                    cfb = "Answer too short, unclear, or not meaningful."
                    bfb = '{"confidence":10,"pace_score":10,"clarity":10,"hesitation":"high","tone":"unclear","summary":"Could not evaluate."}'
                else:
                    cprompt = f"""
Question: {st.session_state.current_question}
Answer: {ans}
Voice feedback: {vfb}
Round: {st.session_state.round_name}  Role: {st.session_state.role}
Give coaching feedback in {st.session_state.language}.
"""
                    sprompt = f"""
Question: {st.session_state.current_question}
Answer: {ans}
Voice feedback: {vfb}
Round: {st.session_state.round_name}  Role: {st.session_state.role}
Score strictly. Return exactly Score / Decision / Interviewer Comments.
"""
                    bprompt = f"""
Question: {st.session_state.current_question}
Answer: {ans}
Voice: {vfb}
Return exactly one JSON line with confidence, pace_score, clarity, hesitation, tone, summary.
"""
                    with st.spinner("Analysing answer…"):
                        cfb = sync(run_agent(cagent, cprompt))
                        sr  = sync(run_agent(sagent, sprompt))
                        bfb = sync(run_agent(bagent, bprompt))

                score, decision, comments = parse_score(sr)
                bdata = parse_behaviour(bfb)

                st.success(f"**Your Answer:** {ans}")
                st.info(f"**Voice:** {vfb}")
                st.warning(f"**Coach:** {cfb}")
                st.markdown(score_card_html(score, decision, comments, bdata),
                            unsafe_allow_html=True)

                # Persist
                st.session_state.scores.append(score)
                st.session_state.history.append({
                    "round": st.session_state.round_name,
                    "interviewer_name": person["name"],
                    "question": st.session_state.current_question,
                    "answer": ans, "voice_feedback": vfb,
                    "coach_feedback": cfb, "score_result": sr,
                    "numeric_score": score, "answer_decision": decision,
                    "interviewer_comments": comments, "behaviour": bdata,
                    "question_no": st.session_state.question_count + 1,
                    "language": st.session_state.language,
                    "interview_mode": "Streamlit Voice Mode",
                })
                st.session_state.question_count   += 1
                st.session_state.current_question  = ""
                st.session_state.question_round    = ""

                if st.session_state.question_count >= ROUND_QUESTION_LIMITS[st.session_state.round_name]:
                    advance_round()
                st.rerun()

# ─────────────────────────────────────────────────────────────────
# FINAL REPORT
# ─────────────────────────────────────────────────────────────────
elif st.session_state.stage == "final":
    st.subheader("📋 Final Interview Report")

    final_avg = (sum(st.session_state.scores)/len(st.session_state.scores)
                 if st.session_state.scores else 0)
    all_ok = (len(st.session_state.round_results) == len(ROUND_ORDER) and
              all(x["decision"] in ["Selected","Skipped"]
                  for x in st.session_state.round_results.values()))

    st.metric("Final Average Score", f"{final_avg:.2f}/10")
    if all_ok:
        st.markdown("<h2 style='color:green'>🎉 FINAL RESULT: SELECTED</h2>",
                    unsafe_allow_html=True)
        verdict = "Selected"
    else:
        st.markdown("<h2 style='color:red'>❌ FINAL RESULT: REJECTED</h2>",
                    unsafe_allow_html=True)
        verdict = "Rejected"

    for r in ROUND_ORDER:
        res = st.session_state.round_results.get(r)
        if res:
            fn = (st.success if res["decision"]=="Selected" else
                  st.warning if res["decision"]=="Skipped" else st.error)
            fn(f"{r}: {res['decision']} — {res['average_score']:.2f}/10")
            st.caption(res["comments"])

    report = {
        "candidate_name": st.session_state.candidate_name,
        "role": st.session_state.role,
        "language": st.session_state.language,
        "interview_mode": st.session_state.interview_mode,
        "company_url": st.session_state.company_url,
        "session_id": st.session_state.session_id,
        "final_score": final_avg, "verdict": verdict,
        "round_results": st.session_state.round_results,
        "history": st.session_state.history,
        "created_at": str(datetime.now()),
    }
    path = save_json(report)
    st.success(f"Report saved: {path}")

    for i, item in enumerate(st.session_state.history, 1):
        bdata = item.get("behaviour")
        with st.expander(
                f"Q{i} · {item['round']} · {item.get('interviewer_name','')} "
                f"· {item.get('numeric_score',0)}/10"):
            st.info(item.get("question",""))
            st.success(item.get("answer",""))
            st.warning(item.get("coach_feedback",""))
            st.markdown(score_card_html(item.get("numeric_score",0),
                                        item.get("answer_decision",""),
                                        item.get("interviewer_comments",""), bdata),
                        unsafe_allow_html=True)

    st.download_button("⬇ Download Report (JSON)",
        data=json.dumps(report, indent=4, ensure_ascii=False),
        file_name="interview_report.json", mime="application/json")

    if st.button("🔁 Start New Interview"):
        st.session_state.clear(); st.rerun()

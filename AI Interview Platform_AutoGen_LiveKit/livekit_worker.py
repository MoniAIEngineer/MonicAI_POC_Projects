"""
livekit_worker.py — AI Interviewer  (DEFINITIVE FINAL VERSION)
===============================================================
livekit-agents 1.5.13

Run:
    python livekit_worker.py dev
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import re
import random
import sqlite3
import struct
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from livekit import rtc
from livekit.agents import (
    Agent, AgentSession, AutoSubscribe,
    JobContext, WorkerOptions, cli, llm,
)
from livekit.agents.voice.room_io import RoomOptions
from livekit.plugins import openai as lk_openai
from energy_vad import EnergyVAD

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ai-interviewer")
logging.getLogger("livekit").setLevel(logging.WARNING)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
STORAGE_DIR = Path(__file__).parent / "storage"
DB_PATH     = STORAGE_DIR / "scores.db"
STORAGE_DIR.mkdir(exist_ok=True)

_pool = concurrent.futures.ThreadPoolExecutor(max_workers=6)
oai   = OpenAI(api_key=OPENAI_API_KEY)

# VAD at module level — required by livekit plugin system
_vad = EnergyVAD.load(energy_threshold=50.0, min_silence_duration=1.0)

# ─────────────────────────────────────────────────────────────────
# LANGUAGE CONFIG
# ─────────────────────────────────────────────────────────────────
WHISPER_LANG = {
    "English":"en","German":"de","French":"fr","Spanish":"es",
    "Hindi":"hi","Tamil":"ta","Telugu":"te","Kannada":"kn","Japanese":"ja",
}

# TTS instructions — tells OpenAI TTS voice how to speak
# Gender prefix ensures correct feminine/masculine tone
FEMALE_TTS_PREFIX = "Speak with a warm, professional female voice. "
MALE_TTS_PREFIX   = "Speak with a confident, professional male voice. "

TTS_INSTRUCTIONS = {
    "English":  "Speak in clear, professional American English only.",
    "German":   "Sprich ausschließlich auf Deutsch. Kein Englisch. Professionell.",
    "French":   "Parle exclusivement en français. Pas d'anglais. Professionnel.",
    "Spanish":  "Habla exclusivamente en español. Sin inglés. Profesional.",
    "Hindi":    "केवल हिंदी में बोलें। अंग्रेज़ी बिल्कुल नहीं। पेशेवर तरीके से।",
    "Tamil":    "தமிழில் மட்டுமே பேசுங்கள். ஆங்கிலம் வேண்டாம். தொழில்முறையாக பேசுங்கள்.",
    "Telugu":   "తెలుగులో మాత్రమే మాట్లాడండి. ఇంగ్లీష్ వద్దు. వృత్తిపరంగా మాట్లాడండి.",
    "Kannada":  "ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಮಾತನಾಡಿ. ಇಂಗ್ಲಿಷ್ ಬೇಡ. ವೃತ್ತಿಪರವಾಗಿ ಮಾತನಾಡಿ.",
    "Japanese": "日本語のみで話してください。英語は使わないでください。プロフェッショナルに。",
}

SILENCE_MSGS = {
    "English":  ["Hello {name}, are you there? Take your time.",
                 "Still connected — speak whenever you're ready.",
                 "You might be on mute — please go ahead."],
    "Tamil":    ["{name}, நீங்கள் இருக்கிறீர்களா? உங்கள் நேரத்தை எடுத்துக்கொள்ளுங்கள்.",
                 "நீங்கள் இன்னும் இணைந்திருக்கிறீர்கள் — தயாராக இருக்கும்போது பேசுங்கள்.",
                 "மைக்கில் சிக்கல் உள்ளதா? தயவுசெய்து பேசுங்கள்."],
    "Hindi":    ["{name}, क्या आप वहाँ हैं? अपना समय लीजिए।",
                 "आप अभी भी जुड़े हुए हैं — जब तैयार हों तब बोलें।",
                 "क्या माइक में कोई समस्या है? कृपया बोलें।"],
    "Telugu":   ["{name}, మీరు అక్కడ ఉన్నారా? మీ సమయం తీసుకోండి.",
                 "మీరు ఇంకా కనెక్ట్ అయి ఉన్నారు — సిద్ధంగా ఉన్నప్పుడు మాట్లాడండి.",
                 "మైక్‌లో సమస్య ఉందా? దయచేసి మాట్లాడండి."],
    "Kannada":  ["{name}, ನೀವು ಇದ್ದೀರಾ? ನಿಮ್ಮ ಸಮಯ ತೆಗೆದುಕೊಳ್ಳಿ.",
                 "ನೀವು ಇನ್ನೂ ಸಂಪರ್ಕದಲ್ಲಿದ್ದೀರಿ — ಸಿದ್ಧರಾದಾಗ ಮಾತನಾಡಿ.",
                 "ಮೈಕ್‌ನಲ್ಲಿ ಸಮಸ್ಯೆ ಇದೆಯಾ? ದಯವಿಟ್ಟು ಮಾತನಾಡಿ."],
    "German":   ["{name}, sind Sie noch da? Nehmen Sie sich Zeit.",
                 "Sie sind noch verbunden — sprechen Sie wenn bereit.",
                 "Mikrofon-Problem? Bitte sprechen Sie jetzt."],
    "French":   ["{name}, êtes-vous là? Prenez votre temps.",
                 "Vous êtes toujours connecté — parlez quand prêt.",
                 "Problème de micro? Veuillez parler maintenant."],
    "Spanish":  ["{name}, ¿está ahí? Tómese su tiempo.",
                 "Todavía conectado — hable cuando esté listo.",
                 "¿Problema con el micrófono? Por favor hable."],
    "Japanese": ["{name}さん、そこにいますか？ゆっくりどうぞ。",
                 "まだ接続されています — 準備ができたら話してください。",
                 "マイクに問題がありますか？どうぞ話してください。"],
}

FEMALE_VOICES = ["nova","shimmer","alloy"]
MALE_VOICES   = ["onyx","echo"]
ROUND_LIMITS  = {"HR Screening":4,"Technical":5,"Hands-on Discussion":2,"Final HR Discussion":4}
ROUND_PASS    = {"HR Screening":6,"Technical":6,"Hands-on Discussion":6,"Final HR Discussion":6}

def get_silence_msg(language: str, name: str) -> str:
    pool = SILENCE_MSGS.get(language, SILENCE_MSGS["English"])
    return random.choice(pool).replace("{name}", name)

# ─────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────
def db_init():
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS live_scores(
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
        round_name TEXT, question_no INTEGER, interviewer TEXT,
        question TEXT, answer TEXT, coach TEXT, score REAL,
        decision TEXT, comments TEXT, behaviour TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS round_state(
        session_id TEXT PRIMARY KEY, round_name TEXT,
        question_count INTEGER, status TEXT, updated_at TEXT)""")
    c.commit(); c.close()
db_init()

def db_save_score(sid, rnd, qno, iv, q, a, coach, score, dec, comments, beh):
    c = sqlite3.connect(DB_PATH)
    c.execute("""INSERT INTO live_scores
        (session_id,round_name,question_no,interviewer,question,answer,
         coach,score,decision,comments,behaviour,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (sid,rnd,qno,iv,q,a,coach,score,dec,comments,json.dumps(beh),str(datetime.now())))
    c.commit(); c.close()

def db_save_round(sid, rnd, qcount, status):
    c = sqlite3.connect(DB_PATH)
    c.execute("""INSERT OR REPLACE INTO round_state
        (session_id,round_name,question_count,status,updated_at) VALUES(?,?,?,?,?)""",
        (sid,rnd,qcount,status,str(datetime.now())))
    c.commit(); c.close()

# ─────────────────────────────────────────────────────────────────
# AI HELPERS
# ─────────────────────────────────────────────────────────────────
def _chat(system: str, user: str, tokens: int = 200) -> str:
    r = oai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        max_tokens=tokens, temperature=0.7)
    return r.choices[0].message.content.strip()

async def ai_call(system: str, user: str, tokens: int = 200) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_pool, _chat, system, user, tokens)

# ─────────────────────────────────────────────────────────────────
# DATA CHANNEL  — renamed to send_event to avoid name collision
# ─────────────────────────────────────────────────────────────────
async def send_event(room: rtc.Room, data: dict):
    """Send data channel event to React frontend."""
    try:
        await room.local_participant.publish_data(
            json.dumps(data).encode(), reliable=True)
    except Exception as e:
        logger.warning(f"send_event failed: {e}")

# ─────────────────────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────────────────────
def parse_score(text):
    score=0.0; decision="Rejected"; comments="No comments."
    for line in text.splitlines():
        ll = line.lower()
        if ll.startswith("score:"):
            try: score=float(line.split(":")[1].split("/")[0].strip())
            except: pass
        elif ll.startswith("decision:"):
            decision="Selected" if "selected" in ll else "Rejected"
        elif ll.startswith("interviewer comments:"):
            comments=line.split(":",1)[1].strip()
    return score, decision, comments

def parse_behaviour(text):
    try:
        m=re.search(r'\{.*\}',text,re.DOTALL)
        if m: return json.loads(m.group())
    except: pass
    return {"confidence":50,"pace_score":50,"clarity":50,
            "hesitation":"medium","tone":"neutral","summary":"N/A"}

async def score_answer(state, qno, question, answer, room):
    try:
        sys_c=(f"Interview coach. Respond ONLY in {state.language}. Under 70 words. "
               f"1.Good points 2.Improve 3.Sample answer 4.Communication.")
        sys_s=("Score strictly:\nScore: X/10\nDecision: Selected or Rejected\n"
               "Interviewer Comments: one sentence\n"
               "Too short/off-topic=0-2,partial=3-5,clear=6-8,excellent=9-10.")
        sys_b=('Return ONE JSON line: {"confidence":75,"pace_score":80,"clarity":70,'
               '"hesitation":"low","tone":"professional","summary":"one sentence"}')
        prompt=f"Q: {question}\nA: {answer}\nRound: {state.round_name}\nRole: {state.role}"

        coach_t,score_t,beh_t = await asyncio.gather(
            ai_call(sys_c,prompt,150),
            ai_call(sys_s,prompt,80),
            ai_call(sys_b,f"Q:{question}\nA:{answer}",100),
        )
        score,decision,comments = parse_score(score_t)
        bdata = parse_behaviour(beh_t)

        for h in state.history:
            if h.get("question")==question:
                h["score"]=score; h["decision"]=decision; break

        db_save_score(state.session_id,state.round_name,qno,
                      state.interviewer_name,question,answer,
                      coach_t,score,decision,comments,bdata)

        await send_event(room,{"type":"score_update","session_id":state.session_id,
                               "question_no":qno,"round":state.round_name,
                               "interviewer":state.interviewer_name,
                               "score":score,"decision":decision,"comments":comments,
                               "coach":coach_t,"behaviour":bdata,
                               "question":question,"answer":answer})
        logger.info(f"Q{qno} → {score}/10 {decision}")
    except Exception as e:
        logger.error(f"score_answer Q{qno} failed: {e}")

# ─────────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────────
class State:
    def __init__(self, meta: dict):
        self.session_id        = meta.get("session_id", str(uuid.uuid4()))
        self.candidate_name    = meta.get("candidate_name","Candidate")
        self.role              = meta.get("role","")
        self.language          = meta.get("language","English")
        self.whisper_lang      = WHISPER_LANG.get(self.language,"en")
        self.round_name        = meta.get("round_name","HR Screening")
        self.question_limit    = int(meta.get("question_limit",
                                 ROUND_LIMITS.get(self.round_name,4)))
        # Ensure minimum 4 questions for proper evaluation
        if self.question_limit < 2:
            self.question_limit = ROUND_LIMITS.get(self.round_name, 4)
        self.pass_score        = float(meta.get("pass_score",
                                 ROUND_PASS.get(self.round_name,6)))
        self.resume_text       = meta.get("resume_text","")[:3000]
        self.jd_text           = meta.get("jd_text","")[:2000]
        self.company_text      = meta.get("company_text","")[:800]
        self.interviewer_name  = meta.get("interviewer_name","AI Interviewer")
        self.interviewer_title = meta.get("interviewer_title","HR Specialist")
        self.interviewer_gender= meta.get("interviewer_gender","female")
        if self.interviewer_gender == "female":
            # nova = warmest/clearest female voice, shimmer = softer
            self.tts_voice = random.choice(["nova", "shimmer"])
        else:
            # onyx = deepest male voice, echo = lighter male
            self.tts_voice = random.choice(["onyx", "echo"])
        self.question_count    = 0
        self.history           = []
        self.last_question     = ""
        self.round_complete    = False  # locks after round ends

    def avg_score(self):
        s=[h.get("score",0) for h in self.history if "score" in h]
        return sum(s)/len(s) if s else 0.0

    def round_done(self):
        # Minimum 2 questions always, then check limit
        return self.question_count >= max(2, self.question_limit)

    def instructions(self)->str:
        hist="\n".join(f"Q{i+1}: {h['question']}\nA: {h['answer']}"
                       for i,h in enumerate(self.history[-3:])) or "None yet."
        lang=self.language
        return f"""You are {self.interviewer_name}, {self.interviewer_title}.
Conducting a live professional job interview.
Candidate: {self.candidate_name} | Role: {self.role}
Round: {self.round_name} | Questions asked: {self.question_count} of {self.question_limit}

⚠️ LANGUAGE RULE — MANDATORY:
Respond ONLY in {lang}. Every single word must be in {lang}.
Do NOT use English unless {lang} IS English.
Examples: Tamil→தமிழில் | Hindi→हिंदी में | Telugu→తెలుగులో | German→Deutsch

FLOW:
1. FIRST TURN: Greet {self.candidate_name}, introduce yourself as {self.interviewer_name}.
   {"Briefly describe the company." if self.round_name=="HR Screening" else ""}
   Then ask your FIRST interview question immediately.
2. NEXT TURNS: One short acknowledgement + ONE new question.
3. FINAL TURN: After {self.question_limit} questions, give warm closing in {lang}.

IF SILENT: Ask if they are there. Be patient.
IF SHORT ANSWER: Ask them to elaborate.
NEVER ask more than ONE question per turn.
NEVER reveal you are AI. NEVER reveal scores.
Keep each response under 60 words.

QUESTIONS FOR THIS ROUND:
- If {self.round_name} is "HR Screening": ask about job change reason, current/expected salary, notice period, relocation flexibility
- If {self.round_name} is "Technical": ask deep technical questions from resume/JD, test automation, QA methodologies, tools used
- If {self.round_name} is "Hands-on Discussion": ask to write code/SQL/test cases, design automation frameworks
- If {self.round_name} is "Final HR Discussion": ask career goals, company motivation, salary negotiation, joining date
Current round is {self.round_name} — ask ONLY {self.round_name} questions. NOT HR questions for Technical round.

CANDIDATE:
Resume: {self.resume_text[:800]}
JD: {self.jd_text[:600]}
Company: {self.company_text[:300]}

HISTORY:
{hist}"""

# ─────────────────────────────────────────────────────────────────
# ROUND CLOSING SPEECHES (interviewer farewell/handover)
# ─────────────────────────────────────────────────────────────────
CLOSING = {
    "English": {
        "Selected": {
            "HR Screening":       "Thank you {name}! You did well in HR Screening. Our Technical team will join shortly. Please hold on!",
            "Technical":          "Excellent {name}! Technical round cleared. The Hands-on team will join shortly. Please hold.",
            "Hands-on Discussion":"Well done {name}! The Senior HR team will join for the Final Discussion. Please hold on.",
            "Final HR Discussion":"Congratulations {name}! All rounds completed. We will contact you soon. Thank you so much!",
        },
        "Rejected": {
            "HR Screening":       "Thank you {name} for your time today. Unfortunately we will not be moving forward at this stage. We wish you all the best. Goodbye!",
            "Technical":          "Thank you {name} for the Technical round. Unfortunately we cannot proceed further. Best wishes for your future. Goodbye!",
            "Hands-on Discussion":"Thank you {name} for the Hands-on Discussion. We are unable to move forward. Best of luck. Goodbye!",
            "Final HR Discussion":"Thank you {name} for completing all rounds. We will review and contact you soon. Goodbye!",
        },
    },
    "Tamil": {
        "Selected": {
            "HR Screening":       "{name}, நல்லது! HR சுற்று வெற்றிகரமாக முடிந்தது. தொழில்நுட்ப குழு விரைவில் இணைவார்கள். தயவுசெய்து காத்திருங்கள்!",
            "Technical":          "{name}, அருமை! தொழில்நுட்ப சுற்று முடிந்தது. Hands-on குழு விரைவில் வருவார்கள். காத்திருங்கள்.",
            "Hands-on Discussion":"{name}, மிகவும் நன்று! இறுதி HR குழு இப்போது இணைவார்கள். சற்று காத்திருங்கள்.",
            "Final HR Discussion":"வாழ்த்துகள் {name}! அனைத்து சுற்றுகளும் வெற்றிகரமாக முடிந்தன. விரைவில் தொடர்பு கொள்கிறோம். நன்றி!",
        },
        "Rejected": {
            "HR Screening":       "{name}, நேரம் ஒதுக்கியதற்கு நன்றி. இந்த நிலையில் தொடர முடியாது என்று வருந்துகிறோம். உங்கள் எதிர்காலம் சிறப்பாக இருக்கட்டும். விடைபெறுகிறேன்.",
            "Technical":          "{name}, தொழில்நுட்ப சுற்றுக்கு நன்றி. தொடர முடியாது. வாழ்த்துக்கள். விடைபெறுகிறேன்.",
            "Hands-on Discussion":"{name}, நன்றி. இந்த கட்டத்தில் தொடர இயலாது. வாழ்த்துக்கள்!",
            "Final HR Discussion":"{name}, அனைத்திற்கும் நன்றி. விரைவில் தொடர்பு கொள்கிறோம். விடைபெறுகிறேன்.",
        },
    },
    "Hindi": {
        "Selected": {
            "HR Screening":       "{name}, बहुत अच्छा! HR राउंड पूरा हुआ। Technical टीम जल्द जुड़ेगी। कृपया प्रतीक्षा करें!",
            "Technical":          "{name}, शानदार! Hands-on टीम जल्द आएगी। प्रतीक्षा करें।",
            "Hands-on Discussion":"{name}, बढ़िया! अंतिम HR टीम अभी जुड़ेगी।",
            "Final HR Discussion":"बधाई हो {name}! सभी राउंड पूरे हुए। जल्द संपर्क करेंगे!",
        },
        "Rejected": {
            "HR Screening":       "{name}, आज समय देने के लिए धन्यवाद। दुर्भाग्यवश आगे नहीं बढ़ सकते। शुभकामनाएं। अलविदा!",
            "Technical":          "{name}, Technical राउंड के लिए धन्यवाद। आगे नहीं बढ़ सकते। शुभकामनाएं। अलविदा!",
            "Hands-on Discussion":"{name}, धन्यवाद। आगे नहीं जा सकते। शुभकामनाएं!",
            "Final HR Discussion":"{name}, सभी राउंड के लिए धन्यवाद। जल्द संपर्क करेंगे। अलविदा!",
        },
    },
}

# Fallback for languages not explicitly defined
for _l in ["German","French","Spanish","Telugu","Kannada","Japanese"]:
    if _l not in CLOSING:
        CLOSING[_l] = CLOSING["English"]


def get_closing(language, round_name, decision, name):
    sp = CLOSING.get(language, CLOSING["English"])
    dec = sp.get(decision, sp["Rejected"])
    tmpl = dec.get(round_name, dec.get("HR Screening","Thank you {name}. Goodbye!"))
    return tmpl.replace("{name}", name)


async def _say_closing(session, state, decision):
    """Speak the farewell/handover message."""
    speech = get_closing(state.language, state.round_name, decision, state.candidate_name)
    logger.info(f"Closing ({decision}): {speech[:80]}")
    try:
        await session.say(speech, allow_interruptions=False)
        # Wait for speech to finish before session ends
        await asyncio.sleep(max(6, len(speech.split()) * 0.4 + 3))
    except Exception as e:
        logger.warning(f"Closing speech failed: {e}")


# ─────────────────────────────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────────────────────────────
class Interviewer(Agent):
    def __init__(self, state: State, room: rtc.Room):
        self.state = state
        self.room  = room
        super().__init__(instructions=state.instructions())

    async def on_enter(self):
        logger.info(f"on_enter: {self.state.interviewer_name} | "
                    f"{self.state.round_name} | {self.state.language} | "
                    f"voice={self.state.tts_voice}")
        # Trigger the LLM to generate intro + first question
        self.session.generate_reply(
            instructions=(
                f"You are {self.state.interviewer_name}. "
                f"Speak ONLY in {self.state.language}. "
                f"Warmly greet {self.state.candidate_name}, introduce yourself, "
                f"then immediately ask your first {self.state.round_name} question. "
                f"Under 60 words total. LANGUAGE: {self.state.language} ONLY."
            ),
            allow_interruptions=False,
        )
        logger.info("generate_reply triggered.")

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        # Get answer text
        answer = ""
        if hasattr(new_message,"text_content") and new_message.text_content:
            answer = new_message.text_content.strip()
        if not answer:
            for c in (new_message.content or []):
                if isinstance(c,str) and c.strip():
                    answer=c.strip(); break

        logger.info(f"Candidate said: '{answer[:100]}'")
        s = self.state

        # Stop processing if round already complete
        if s.round_complete:
            logger.info("Round already complete — ignoring answer")
            return

        if answer.strip():
            await send_event(self.room,{"type":"candidate_answer","answer":answer,
                                        "question_no":s.question_count,
                                        "session_id":s.session_id})

        # Count words — Tamil/Hindi answers can be short but valid
        # Lower threshold to 2 words to avoid missing answers
        if len(answer.split()) < 2:
            logger.info(f"Too short (1 word): '{answer}' — ignoring")
            return

        s.question_count += 1
        qno = s.question_count
        s.history.append({"question":s.last_question,"answer":answer})

        asyncio.ensure_future(score_answer(s,qno,s.last_question,answer,self.room))

        if s.round_done():
            s.round_complete = True  # LOCK immediately
            await asyncio.sleep(3)   # let background scoring finish
            avg = s.avg_score()
            rd  = "Selected" if avg >= s.pass_score else "Rejected"
            db_save_round(s.session_id, s.round_name, s.question_count, "completed")
            logger.info(f"Round done: avg={avg:.2f} → {rd}")

            # 1. Notify React UI
            await send_event(self.room, {"type":"round_complete",
                                         "session_id":s.session_id,
                                         "round":s.round_name,
                                         "average_score":round(avg,2),
                                         "decision":rd})

            # 2. Speak farewell — await so it finishes before stopping
            speech = get_closing(s.language, s.round_name, rd, s.candidate_name)
            logger.info(f"Farewell ({rd}): {speech[:80]}")
            try:
                await self.session.say(speech, allow_interruptions=False)
                await asyncio.sleep(max(6, len(speech.split()) * 0.4 + 3))
            except Exception as e:
                logger.warning(f"Farewell failed: {e}")

            # 3. STOP session — prevents LLM from generating any more replies
            # Round complete — let session end naturally when participant disconnects
            # Don't force-close as it can interfere with the farewell speech
            logger.info("Round complete — waiting for participant to disconnect.")

# ─────────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────────
async def entrypoint(ctx: JobContext):
    logger.info(f"Job received: {ctx.room.name}")

    # Read metadata
    meta = {}
    for source, getter in [
        ("ctx.job.metadata",  lambda: getattr(ctx.job,"metadata","")),
        ("ctx.room.metadata", lambda: ctx.room.metadata or ""),
    ]:
        try:
            raw = getter() or ""
            if raw.strip():
                meta = json.loads(raw)
                logger.info(f"Metadata from {source} ({len(meta)} keys)")
                break
        except Exception as e:
            logger.warning(f"{source} error: {e}")

    state = State(meta)
    logger.info(f"Session={state.session_id[:8]} | {state.candidate_name} | "
                f"{state.interviewer_name} ({state.interviewer_gender}) | "
                f"{state.round_name} | {state.language} | voice={state.tts_voice}")

    # Connect with SUBSCRIBE_ALL so worker receives candidate's audio
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("Room connected.")

    agent = Interviewer(state, ctx.room)
    # Add gender prefix to TTS instructions for correct voice tone
    lang_instr = TTS_INSTRUCTIONS.get(state.language, "Speak professionally.")
    gender_prefix = FEMALE_TTS_PREFIX if state.interviewer_gender == "female" else MALE_TTS_PREFIX
    tts_instr = gender_prefix + lang_instr

    logger.info(f"TTS voice={state.tts_voice} gender={state.interviewer_gender} instr={tts_instr[:60]}")

    session = AgentSession(
        stt=lk_openai.STT(language=state.whisper_lang),
        llm=lk_openai.LLM(model="gpt-4o-mini"),
        tts=lk_openai.TTS(voice=state.tts_voice, instructions=tts_instr),
        vad=_vad,
        user_away_timeout=35.0,
    )

    # Find participant already in room
    candidate_identity = None
    for identity in ctx.room.remote_participants:
        candidate_identity = identity
        logger.info(f"Found participant: {identity}")
        break

    # Event handlers — use send_event (not pub) to avoid name collision
    @session.on("user_state_changed")
    def on_user_state(ev):
        asyncio.ensure_future(send_event(ctx.room,{
            "type":"user_state","state":ev.new_state,
            "session_id":state.session_id}))
        if ev.new_state == "away":
            # Don't send silence check-ins after round is complete
            if state.round_complete:
                logger.info("Round complete — skipping silence check-in")
                return
            msg = get_silence_msg(state.language, state.candidate_name)
            logger.info(f"User away — saying: {msg[:60]}")
            try:
                session.say(msg, allow_interruptions=True)
            except Exception as e:
                logger.warning(f"session.say failed: {e}")

    @session.on("agent_state_changed")
    def on_agent_state(ev):
        asyncio.ensure_future(send_event(ctx.room,{
            "type":"agent_state","state":ev.new_state,
            "session_id":state.session_id}))

    @session.on("conversation_item_added")
    def on_item_added(ev):
        item = ev.item
        if not (hasattr(item,"role") and item.role=="assistant"):
            return
        text=""
        if hasattr(item,"text_content") and item.text_content:
            text=item.text_content.strip()
        if not text:
            for c in (getattr(item,"content",[]) or []):
                if isinstance(c,str): text+=c
        text=text.strip()
        if not text: return
        state.last_question=text
        logger.info(f"Agent said: {text[:100]}")
        asyncio.ensure_future(send_event(ctx.room,{
            "type":"interviewer_question","question":text,
            "question_no":state.question_count+1,
            "session_id":state.session_id}))

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        logger.info(f"Track subscribed: {participant.identity} "
                    f"kind={track.kind} sid={track.sid}")

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=RoomOptions(
            audio_input=True,
            audio_output=True,
            participant_identity=candidate_identity,
        ),
    )

    logger.info("AgentSession live.")

    # Force subscribe to all existing tracks
    await asyncio.sleep(0.5)
    for identity, participant in ctx.room.remote_participants.items():
        for track_pub in participant.track_publications.values():
            if not track_pub.subscribed:
                try:
                    await track_pub.set_subscribed(True)
                    logger.info(f"Force-subscribed: {identity} track {track_pub.sid}")
                except Exception as e:
                    logger.warning(f"Force-subscribe failed: {e}")

    await asyncio.sleep(7200)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="ai-interviewer-agent",
    ))

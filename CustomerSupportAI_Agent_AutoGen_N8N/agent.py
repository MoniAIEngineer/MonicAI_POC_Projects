import os
import re
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))
namespace = os.getenv("PINECONE_NAMESPACE", "v1.1")

class EmailRequest(BaseModel):
    subject: str = ""
    sender: str
    body: str

def query_rag(question: str) -> tuple:
    embedding_response = client.embeddings.create(
        input=question,
        model="text-embedding-3-large"
    )
    query_vector = embedding_response.data[0].embedding
    results = index.query(
        vector=query_vector,
        top_k=8,
        namespace=namespace,
        include_metadata=True
    )
    if not results.matches:
        return "No relevant information found.", 0.0
    best_score = results.matches[0].score
    context = ""
    for match in results.matches:
        if match.score > 0.3:
            metadata = match.metadata or {}
            text = metadata.get("text", "")
            if text:
                context += text + "\n\n"
    return context if context else "No relevant information found.", best_score

def is_self_reply(sender: str) -> bool:
    own_addresses = ["monicaiengineer@gmail.com", "noreply", "no-reply", "mailer-daemon", "smarthomepro", "support@", "monicai"]
    sender_lower = sender.lower()
    return any(addr in sender_lower for addr in own_addresses)

def detect_spam_or_ooo(subject: str, body: str) -> bool:
    spam_keywords = [
        "re:", "fwd:", "fw:", "out of office", "auto-reply", "automatic reply",
        "on vacation", "unsubscribe", "newsletter",
        "no-reply", "noreply", "do not reply",
        "delivery failed", "mailer-daemon",
        "you won", "you have won", "claim your prize",
        "lucky winner", "bank details", "wire transfer",
        "lottery", "nigerian prince", "inheritance funds",
        "million dollar", "billion dollar", "free money",
        "click here to claim", "selected as our lucky",
        "send your bank", "congratulations you won"
    ]
    combined = (subject + " " + body).lower()
    return any(keyword in combined for keyword in spam_keywords)

def detect_language(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a language detection expert. You MUST reply with ONLY the correct 2-letter ISO 639-1 language code. No explanation, no punctuation, just the code. Examples: English=en, German=de, French=fr, Spanish=es, Hindi=hi, Arabic=ar, Portuguese=pt, Italian=it, Chinese=zh, Japanese=ja, Korean=ko, Russian=ru, Dutch=nl, Turkish=tr, Polish=pl, Swedish=sv, Danish=da, Finnish=fi, Hebrew=he, Bengali=bn, Urdu=ur, Tamil=ta, Telugu=te, Marathi=mr, Gujarati=gu"},
            {"role": "user", "content": f"What is the ISO 639-1 language code for this text? Reply with ONLY the 2-letter code:\n\n{text[:500]}"}
        ],
        temperature=0,
        max_tokens=3
    )
    code = response.choices[0].message.content.strip().lower()
    match = re.search(r'[a-z]{2}', code)
    return match.group(0) if match else 'en'

def generate_subject(body: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Generate a short 6-8 word email subject line summarizing the customer issue. Reply with ONLY the subject line, no quotes."},
            {"role": "user", "content": f"Generate a subject line for this support email:\n\n{body[:300]}"}
        ],
        temperature=0,
        max_tokens=20
    )
    return "[Auto] " + response.choices[0].message.content.strip()

def extract_questions(body: str) -> list:
    """Extract individual questions from email body."""
    # Try numbered list first: 1. ... 2. ... 3. ...
    numbered = re.split(r'\n?\s*\d+[\.\)]\s+', body)
    numbered = [q.strip() for q in numbered if q.strip() and len(q.strip()) > 10]
    if len(numbered) > 1:
        return numbered[:4]
    # Try splitting by question marks
    questions = re.split(r'\?\s*\n', body)
    questions = [q.strip() + '?' for q in questions if q.strip() and len(q.strip()) > 10]
    if len(questions) > 1:
        return questions[:4]
    return [body]

def query_rag_multi(questions: list) -> tuple:
    """Query RAG separately for each question and combine contexts."""
    all_contexts = []
    all_scores = []
    for q in questions:
        ctx, score = query_rag(q)
        if "No relevant" not in ctx:
            all_contexts.append(f"[Context for question: {q[:80]}]\n{ctx}")
            all_scores.append(score)
    if all_contexts:
        combined = "\n\n---\n\n".join(all_contexts)
        avg_score = sum(all_scores) / len(all_scores)
        return combined, avg_score
    return "No relevant information found.", 0.0

LIMIT_MESSAGES = {
    "en": "Dear Customer,\n\nThank you for contacting SmartHome Pro Support!\n\nWe noticed your email contains more than 4 questions. To ensure you receive the best possible answer for each issue, please send a maximum of 3-4 questions per email and split the rest into separate emails.\n\nWe look forward to helping you!\n\nBest regards,\nSmartHome Pro Support Team",
    "de": "Sehr geehrter Kunde,\n\nVielen Dank für Ihre Anfrage!\n\nWir haben bemerkt, dass Ihre E-Mail mehr als 4 Fragen enthält. Bitte senden Sie maximal 3-4 Fragen pro E-Mail.\n\nMit freundlichen Grüßen,\nSmartHome Pro Support",
    "es": "Estimado cliente,\n\nGracias por contactarnos!\n\nSu correo contiene más de 4 preguntas. Por favor envíe máximo 3-4 preguntas por correo.\n\nAtentamente,\nSoporte SmartHome Pro",
    "hi": "प्रिय ग्राहक,\n\nधन्यवाद!\n\nआपके ईमेल में 4 से अधिक प्रश्न हैं। कृपया एक ईमेल में अधिकतम 3-4 प्रश्न भेजें।\n\nसादर,\nSmartHome Pro सपोर्ट",
    "fr": "Cher client,\n\nMerci!\n\nVotre email contient plus de 4 questions. Veuillez envoyer maximum 3-4 questions par email.\n\nCordialement,\nSupport SmartHome Pro",
    "ja": "お客様へ,\n\nメールに4つ以上のご質問が含まれています。1通につき最大3〜4件のご質問をお送りください。\n\nSmartHome Proサポート",
}

@app.post("/analyse")
async def analyse_email(request: EmailRequest):
    import hashlib, json

    # ── Block self-replies ───────────────────────────────────────
    if is_self_reply(request.sender):
        return {"output": "SELF_REPLY", "priority": "Skip", "sentiment": "Neutral",
                "confidence": "N/A", "confidence_score": 0, "rag_context_found": False,
                "escalate": False, "skip": True, "language": "en", "subject": request.subject}

    # ── Auto-generate subject if empty ───────────────────────────
    if not request.subject or not request.subject.strip():
        request.subject = generate_subject(request.body)

    # ── FAQ Cache Check ──────────────────────────────────────────
    question_hash = hashlib.md5((request.subject + request.body).lower().encode()).hexdigest()[:12]
    cache_file = '/opt/autogen-support/faq_cache.json'
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cache = json.load(f)
        except:
            cache = {}
    if question_hash in cache:
        cached = cache[question_hash]
        cached['hit_count'] = cached.get('hit_count', 0) + 1
        with open(cache_file, 'w') as f:
            json.dump(cache, f)
        cached_response = cached['response'].copy()
        cached_response['language'] = detect_language(request.subject + " " + request.body)
        cached_response['subject'] = request.subject
        return cached_response

    # ── Spam/OOO Detection ───────────────────────────────────────
    if detect_spam_or_ooo(request.subject, request.body):
        return {
            "output": "SPAM_OR_OOO", "priority": "Skip", "sentiment": "Neutral",
            "confidence": "N/A", "rag_context_found": False, "escalate": False,
            "skip": True, "language": detect_language(request.subject + " " + request.body),
            "subject": request.subject
        }

    # ── Language Detection ───────────────────────────────────────
    language = detect_language(request.body)

    # ── Question Count Check (max 4) ─────────────────────────────
    questions = extract_questions(request.body)
    question_count = len(questions)

    if question_count > 4:
        return {
            "output": LIMIT_MESSAGES.get(language, LIMIT_MESSAGES["en"]),
            "priority": "Normal", "sentiment": "Neutral",
            "confidence": "N/A", "confidence_score": 0,
            "rag_context_found": False, "escalate": False,
            "skip": False, "language": language,
            "subject": request.subject,
            "question_limit_exceeded": True
        }

    # ── RAG Query (per question for multi-question emails) ───────
    if question_count > 1:
        rag_context, confidence_score = query_rag_multi(questions)
    else:
        rag_context, confidence_score = query_rag(request.body)

    # ── Confidence Level ─────────────────────────────────────────
    if confidence_score >= 0.7:
        confidence_level = "High"
        escalate = False
    elif confidence_score >= 0.4:
        confidence_level = "Medium"
        escalate = False
    else:
        confidence_level = "Low"
        escalate = True

    # ── Build Prompt ─────────────────────────────────────────────
    lang_instruction = f"Reply in the same language as the customer ({language})." if language != "en" else ""

    multi_instruction = ""
    if question_count > 1:
        multi_instruction = f"The customer has asked {question_count} questions. Answer ALL of them clearly labeled as Q1, Q2, Q3 etc. with separate steps for each."

    prompt = f"""You are a customer support agent for SmartHome Pro.

A customer sent this email:
Subject: {request.subject}
From: {request.sender}
Message: {request.body}

Knowledge base context:
{rag_context}

IMPORTANT RULES:
1. ONLY answer from the knowledge base context provided above
2. {multi_instruction if multi_instruction else "Answer the customer question with clear steps."}
3. If the knowledge base has no relevant information for a specific question, say so for that question only
4. Always cite the section at the end as SOURCE: Section X.X
5. {lang_instruction}
6. If customer sounds angry or frustrated bump up the priority level

Reply in this EXACT format:
PRIORITY: [Critical/Very High/High/Normal]
SENTIMENT: [Angry/Neutral/Positive]
QUESTION: [summarize ALL customer questions in one line]
ANSWER:
[Answer each question labeled Q1, Q2, Q3 etc. with steps]
SOURCE: Section X.X - Section Name
CONFIDENCE: [{confidence_level}]"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful customer support agent for SmartHome Pro."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    output = response.choices[0].message.content
    lines = output.split("\n")
    priority = "Normal"
    sentiment = "Neutral"

    for line in lines:
        if line.startswith("PRIORITY:"):
            priority = line.replace("PRIORITY:", "").strip()
        elif line.startswith("SENTIMENT:"):
            sentiment = line.replace("SENTIMENT:", "").strip()

    # ── Escalation Logic ─────────────────────────────────────────
    ESCALATION_KEYWORDS = [
        "refund", "lawyer", "legal", "sue", "unacceptable",
        "broken", "demand", "useless", "scam", "fraud",
        "rückerstattung", "anwalt", "inakzeptabel", "kaputt"
    ]
    body_lower = request.body.lower()
    subject_lower = request.subject.lower()
    keyword_hit = any(kw in body_lower or kw in subject_lower for kw in ESCALATION_KEYWORDS)

    if (confidence_score < 0.4 or
        (sentiment in ["Angry", "Negative"] and priority in ["Critical", "Very High", "High"]) or
        keyword_hit):
        escalate = True

    response_data = {
        "output": output,
        "priority": priority,
        "sentiment": sentiment,
        "confidence": confidence_level,
        "confidence_score": confidence_score,
        "rag_context_found": "No relevant information" not in rag_context,
        "escalate": escalate,
        "skip": False,
        "language": language,
        "subject": request.subject
    }

    # ── FAQ Cache Save ───────────────────────────────────────────
    if confidence_score >= 0.5 and not escalate:
        cache[question_hash] = {
            "question": request.subject,
            "answer": output,
            "hit_count": 0,
            "response": response_data
        }
        with open(cache_file, "w") as f:
            json.dump(cache, f)

    return response_data

@app.get("/health")
async def health():
    return {"status": "ok", "namespace": namespace}

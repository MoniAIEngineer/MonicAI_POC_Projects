"""
SmartHome Pro X200 — AI Customer Support Dashboard
Flask backend that reads directly from Google Sheets (public CSV)
No API key required — sheet must be set to "Anyone with link can view"

Dashboard: http://YOUR_VPS_IP:8080
"""

from flask import Flask, jsonify
from datetime import datetime
import csv, io, urllib.request

app = Flask(__name__, static_folder='.', static_url_path='')

# ── Config ───────────────────────────────────────────────────────────────────
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"  # Replace with your Sheet ID

def fetch_sheet(tab: str) -> list:
    """Fetch a Google Sheets tab as list of dicts via public CSV URL."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab.replace(' ', '+')}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            content = r.read().decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))
    except Exception as e:
        print(f"Error fetching sheet '{tab}': {e}")
        return []

def clean_status(s: str) -> str:
    if not s or s.startswith('#'):
        return 'Open'
    return s

def breakdown(rows: list, key: str) -> dict:
    d = {}
    for r in rows:
        v = r.get(key, 'Unknown') or 'Unknown'
        d[v] = d.get(v, 0) + 1
    return d

@app.route("/api/stats")
def stats():
    emails      = fetch_sheet("Email Log")
    escalations = fetch_sheet("Escalation Queue")
    replies     = fetch_sheet("Reply Log")

    for r in emails:
        r['status'] = clean_status(r.get('status', ''))

    total      = len(emails)
    esc_count  = len(escalations)
    res_rate   = round(((total - esc_count) / total * 100) if total else 0, 1)
    sla_ok     = sum(1 for r in emails if str(r.get("sla_breached", "")).upper() != "TRUE")
    sla_pct    = round(sla_ok / total * 100 if total else 100, 1)
    open_count = sum(1 for r in emails if r.get("status", "").lower() == "open")

    rag_vals = []
    for r in escalations:
        v = r.get("rag_score_at_escalation", "").strip()
        try:
            if v: rag_vals.append(float(v))
        except: pass
    avg_conf = round(sum(rag_vals) / len(rag_vals), 3) if rag_vals else 0

    volume_by_day = {}
    for r in emails:
        try:
            ts  = int(r.get("received_at", 0))
            day = datetime.utcfromtimestamp(ts / 1000).strftime("%m/%d")
            volume_by_day[day] = volume_by_day.get(day, 0) + 1
        except: pass

    rag_by_day = {}
    for r in escalations:
        try:
            day = r.get("escalated_at", "")[:10]
            if day:
                day_fmt = datetime.strptime(day, "%Y-%m-%d").strftime("%m/%d")
                v = float(r.get("rag_score_at_escalation", "0") or 0)
                if day_fmt not in rag_by_day: rag_by_day[day_fmt] = []
                rag_by_day[day_fmt].append(v)
        except: pass
    rag_trend = [{"day": d, "score": round(sum(vs)/len(vs), 3)} for d, vs in sorted(rag_by_day.items())]

    fishbone = {"Connectivity":0,"LED/Hardware":0,"Setup":0,"Device Limit":0,"Alexa/Voice":0,"Billing":0,"Other":0}
    kw_map = {
        "connect":"Connectivity","internet":"Connectivity","wifi":"Connectivity",
        "led":"LED/Hardware","broken":"LED/Hardware","hardware":"LED/Hardware",
        "setup":"Setup","install":"Setup","reset":"Setup",
        "device":"Device Limit","limit":"Device Limit",
        "alexa":"Alexa/Voice","voice":"Alexa/Voice",
        "refund":"Billing","billing":"Billing","charge":"Billing"
    }
    for r in emails:
        subj = (r.get("subject","") + " " + r.get("body_preview","")).lower()
        matched = False
        for kw, cat in kw_map.items():
            if kw in subj:
                fishbone[cat] += 1
                matched = True
                break
        if not matched: fishbone["Other"] += 1

    top_s = {}
    for r in emails:
        s = r.get("subject","Unknown")[:40]
        top_s[s] = top_s.get(s, 0) + 1
    top_subjects = sorted(top_s.items(), key=lambda x: -x[1])[:5]

    recent = sorted(emails, key=lambda x: int(x.get("ticket_id",0) or 0), reverse=True)[:8]

    res_times = [float(r.get("resolution_time_mi",0) or 0) for r in emails if r.get("resolution_time_mi","").strip()]
    avg_res = round(sum(res_times)/len(res_times), 1) if res_times else 0

    return jsonify({
        "kpis": {
            "total_tickets":   total,
            "escalations":     esc_count,
            "resolution_rate": res_rate,
            "sla_compliance":  sla_pct,
            "open_tickets":    open_count,
            "avg_rag_score":   avg_conf,
            "avg_resolution":  avg_res,
        },
        "priority":       breakdown(emails, "priority"),
        "sentiment":      breakdown(emails, "sentiment"),
        "language":       breakdown(emails, "language"),
        "reply_types":    breakdown(replies, "reply_type"),
        "statuses":       breakdown(emails, "status"),
        "volume_by_day":  volume_by_day,
        "rag_trend":      rag_trend,
        "fishbone":       fishbone,
        "top_subjects":   top_subjects,
        "recent_tickets": recent,
        "all_emails":     emails,
        "last_updated":   datetime.utcnow().isoformat(),
    })

@app.route("/")
def index():
    return app.send_static_file("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

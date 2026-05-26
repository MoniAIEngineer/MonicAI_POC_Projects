import { useState, useEffect, useRef, useCallback } from "react";
import {
  LiveKitRoom, useDataChannel, useTracks,
  VideoTrack, RoomAudioRenderer,
  useParticipants, useIsSpeaking,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { Track } from "livekit-client";

function getParams() {
  const p = new URLSearchParams(window.location.search);
  return {
    serverUrl:         p.get("serverUrl") || "",
    token:             p.get("token") || "",
    mode:              p.get("mode") || "audio",
    interviewerName:   p.get("interviewerName") || "AI Interviewer",
    interviewerTitle:  p.get("interviewerTitle") || "HR Specialist",
    interviewerGender: p.get("interviewerGender") || "female",
    language:          p.get("language") || "English",
    sessionId:         p.get("sessionId") || "",
    candidateName:     p.get("candidateName") || "Candidate",
  };
}

function Wave({ color="#6366f1", bars=5, height=24 }) {
  return (
    <div style={{ display:"flex", gap:4, alignItems:"flex-end", height }}>
      {Array.from({length:bars}).map((_,i) => (
        <div key={i} style={{
          width:5, borderRadius:3, background:color,
          animation:`wave .9s ${i*0.15}s infinite ease-in-out`,
        }}/>
      ))}
    </div>
  );
}

function BBar({ label, value, color }) {
  return (
    <div style={{ marginBottom:8 }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:3 }}>
        <span style={{ fontSize:12, color:"#cbd5e1", fontWeight:500 }}>{label}</span>
        <span style={{ fontSize:12, color:color, fontWeight:700 }}>{Math.round(value||0)}%</span>
      </div>
      <div style={{ background:"#334155", borderRadius:6, height:8 }}>
        <div style={{
          width:`${Math.min(100,value||0)}%`, height:8,
          borderRadius:6, background:color,
          transition:"width 1s ease",
          boxShadow:`0 0 8px ${color}66`,
        }}/>
      </div>
    </div>
  );
}

function ScoreCard({ e }) {
  const ok = e.decision === "Selected";
  const b  = e.behaviour || {};
  return (
    <div style={{
      background:"#1e293b",
      borderRadius:12,
      padding:"16px 18px",
      marginBottom:12,
      borderLeft:`5px solid ${ok?"#10b981":"#ef4444"}`,
      boxShadow:"0 4px 20px rgba(0,0,0,0.3)",
    }}>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:10 }}>
        <div>
          <span style={{ fontSize:13, fontWeight:700, color:"#e2e8f0" }}>
            Question {e.question_no}
          </span>
          <span style={{
            marginLeft:8, fontSize:11, background:"#334155",
            padding:"2px 10px", borderRadius:20, color:"#94a3b8",
          }}>{e.round}</span>
        </div>
        <div style={{ textAlign:"right" }}>
          <div style={{ fontSize:28, fontWeight:900, color:ok?"#10b981":"#ef4444", lineHeight:1 }}>
            {e.score}<span style={{ fontSize:14, color:"#64748b" }}>/10</span>
          </div>
          <div style={{
            fontSize:11, fontWeight:700, marginTop:2,
            padding:"2px 10px", borderRadius:20,
            background:ok?"#064e3b":"#7f1d1d",
            color:ok?"#34d399":"#f87171",
          }}>{e.decision}</div>
        </div>
      </div>

      {/* Q&A */}
      <div style={{ background:"#0f172a", borderRadius:8, padding:"10px 12px", marginBottom:10 }}>
        <div style={{ fontSize:13, color:"#94a3b8", marginBottom:4 }}>
          <span style={{ color:"#6366f1", fontWeight:700 }}>Q: </span>
          {e.question}
        </div>
        <div style={{ fontSize:13, color:"#e2e8f0" }}>
          <span style={{ color:"#10b981", fontWeight:700 }}>A: </span>
          {e.answer}
        </div>
      </div>

      {/* Coach feedback */}
      {e.coach && (
        <div style={{
          background:"#1a2744", borderRadius:8, padding:"10px 12px",
          marginBottom:10, borderLeft:"3px solid #f59e0b",
        }}>
          <div style={{ fontSize:11, color:"#f59e0b", fontWeight:700, marginBottom:4 }}>
            💬 Coach Feedback
          </div>
          <div style={{ fontSize:12, color:"#fde68a", lineHeight:1.6 }}>{e.coach}</div>
        </div>
      )}

      {/* Behaviour bars */}
      {b.confidence != null && (
        <div>
          <BBar label="Confidence"  value={b.confidence}  color="#818cf8"/>
          <BBar label="Speech Pace" value={b.pace_score}  color="#38bdf8"/>
          <BBar label="Clarity"     value={b.clarity}     color="#34d399"/>
          <div style={{ fontSize:12, color:"#64748b", marginTop:6 }}>
            Tone: <span style={{ color:"#94a3b8" }}>{b.tone}</span>
            {" · "}Hesitation: <span style={{ color:"#94a3b8" }}>{b.hesitation}</span>
            {b.summary && <span style={{ color:"#cbd5e1" }}> · {b.summary}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

function CandidateTile({ candidateName, mode, userState }) {
  const participants = useParticipants();
  const localParticipant = participants.find(p => p.isLocal);
  const isSpeaking = useIsSpeaking(localParticipant);

  const speaking = isSpeaking || userState === "speaking";
  const away     = userState === "away";

  return (
    <div style={{
      background:"#111827", borderRadius:14,
      border:`2px solid ${speaking?"#10b981":"#1e293b"}`,
      transition:"border-color .3s, box-shadow .3s",
      boxShadow:speaking?"0 0 20px #10b98133":"none",
      padding:mode==="video"?"0":"16px",
      textAlign:"center", overflow:"hidden",
    }}>
      {mode === "video"
        ? <CandidateVideo candidateName={candidateName} userSpeaking={speaking}/>
        : <>
            <div style={{ fontSize:44 }}>🧑‍💼</div>
            <div style={{ fontSize:15, fontWeight:700, color:"#f1f5f9", marginTop:6 }}>
              {candidateName}
            </div>
            <div style={{ display:"flex", alignItems:"center",
              justifyContent:"center", gap:6, marginTop:8 }}>
              {speaking && <Wave color="#10b981" bars={4} height={16}/>}
              <span style={{
                fontSize:12, fontWeight:600,
                color: speaking ? "#10b981" : away ? "#f59e0b" : "#475569",
              }}>
                {speaking ? "🎤 Speaking…" : away ? "🔇 Please speak now" : "🎤 Listening"}
              </span>
            </div>
          </>
      }
    </div>
  );
}

function Room({ params }) {
  const [agentState, setAgentState] = useState("initializing");
  const [userState,  setUserState]  = useState("listening");
  const [scores,     setScores]     = useState([]);
  const [transcript, setTranscript] = useState([]);
  const [roundInfo,  setRoundInfo]  = useState(null);
  const [codeAnswer, setCodeAnswer] = useState("");
  const [showCode,   setShowCode]   = useState(false);
  const currentRound = scores[scores.length-1]?.round || "";
  const transcriptRef = useRef(null);

  const isSpeaking = agentState === "speaking";
  const isThinking = agentState === "thinking";
  const accentColor = isSpeaking ? "#6366f1" : isThinking ? "#f59e0b" : "#10b981";
  const stateLabel  = isSpeaking ? "Speaking…" : isThinking ? "Thinking…" : "Listening";
  const av = params.interviewerGender === "male" ? "👨‍💼" : "👩‍💼";

  useDataChannel(useCallback((msg) => {
    try {
      const d = JSON.parse(new TextDecoder().decode(msg.payload));
      if (d.type === "agent_state")    setAgentState(d.state || "listening");
      if (d.type === "user_state")     setUserState(d.state || "listening");
      if (d.type === "interviewer_question")
        setTranscript(p => [...p, { role:"ai", name:params.interviewerName,
          text:d.question, ts:new Date().toLocaleTimeString() }]);
      if (d.type === "candidate_answer" && d.answer?.trim())
        setTranscript(p => [...p, { role:"user", name:params.candidateName,
          text:d.answer, ts:new Date().toLocaleTimeString() }]);
      if (d.type === "score_update")
        setScores(p => p.some(s=>s.question_no===d.question_no&&s.round===d.round) ? p : [...p, d]);
      if (d.type === "round_complete") {
        setRoundInfo(d);
        setAgentState("listening"); // reset state
      }
    } catch(e) { console.warn(e); }
  }, [params.interviewerName, params.candidateName]));

  useEffect(() => {
    if (transcriptRef.current)
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
  }, [transcript]);

  const avg = scores.length
    ? (scores.reduce((s,x)=>s+x.score,0)/scores.length).toFixed(1) : "—";

  return (
    <div style={{
      display:"flex", height:"100vh",
      background:"#0a0f1e",
      color:"#e2e8f0",
      fontFamily:"Inter,system-ui,sans-serif",
      overflow:"hidden",
    }}>

      {/* ══ LEFT PANEL ══ */}
      <div style={{
        width:300, padding:16, display:"flex",
        flexDirection:"column", gap:12,
        borderRight:"1px solid #1e293b",
        flexShrink:0,
        background:"#0d1526",
      }}>

        {/* Header */}
        <div style={{
          display:"flex", alignItems:"center", gap:8,
          background:"#1e293b", borderRadius:10, padding:"10px 14px",
          border:"1px solid #334155",
        }}>
          <div style={{
            width:10, height:10, borderRadius:"50%",
            background:"#ef4444", animation:"pulse 1.4s infinite",
            boxShadow:"0 0 8px #ef4444",
          }}/>
          <span style={{ fontSize:13, fontWeight:800, letterSpacing:1 }}>🎙 LIVE INTERVIEW</span>
          <span style={{ marginLeft:"auto", fontSize:11, color:"#64748b", fontWeight:600 }}>
            {params.language} {params.mode==="video"?"📹":"🎧"}
          </span>
        </div>

        {/* AI Interviewer tile */}
        <div style={{
          background:"#111827", borderRadius:14,
          border:`2px solid ${accentColor}`,
          transition:"border-color .4s, box-shadow .4s",
          boxShadow:`0 0 20px ${accentColor}33`,
          padding:"20px 16px", textAlign:"center", position:"relative",
        }}>
          <div style={{ fontSize:60, lineHeight:1, marginBottom:10 }}>{av}</div>

          {isSpeaking && (
            <div style={{ display:"flex", justifyContent:"center", marginBottom:10 }}>
              <Wave color="#6366f1" bars={6} height={28}/>
            </div>
          )}
          {isThinking && (
            <div style={{ fontSize:12, color:"#f59e0b", marginBottom:8,
              animation:"pulse 1s infinite", fontWeight:600 }}>
              ⚙ Generating response…
            </div>
          )}

          <div style={{ fontSize:16, fontWeight:800, color:"#f1f5f9" }}>
            {params.interviewerName}
          </div>
          <div style={{ fontSize:12, color:"#64748b", marginTop:3 }}>
            {params.interviewerTitle}
          </div>
          <div style={{
            fontSize:12, marginTop:4, fontWeight:700,
            color:params.interviewerGender==="female"?"#f9a8d4":"#93c5fd",
          }}>
            {params.interviewerGender==="female"?"♀ Female Interviewer":"♂ Male Interviewer"}
          </div>

          <div style={{
            display:"inline-flex", alignItems:"center", justifyContent:"center",
            gap:6, marginTop:10,
            background:"#1e293b", borderRadius:20, padding:"5px 14px",
          }}>
            <div style={{
              width:8, height:8, borderRadius:"50%", background:accentColor,
              animation:isSpeaking||isThinking?"pulse 1s infinite":"none",
              boxShadow:`0 0 6px ${accentColor}`,
            }}/>
            <span style={{ fontSize:13, color:accentColor, fontWeight:700 }}>
              {stateLabel}
            </span>
          </div>

          <div style={{
            position:"absolute", top:8, right:8,
            background:"#1e293b", borderRadius:6, padding:"2px 8px",
            fontSize:10, color:"#475569",
          }}>AI Interviewer</div>
        </div>

        {/* Candidate tile */}
        <div style={{
          background:"#111827", borderRadius:14,
          border:`2px solid ${userState==="speaking"?"#10b981":"#1e293b"}`,
          transition:"border-color .3s, box-shadow .3s",
          boxShadow:userState==="speaking"?"0 0 20px #10b98133":"none",
          padding:params.mode==="video"?"0":"16px",
          textAlign:"center", overflow:"hidden",
        }}>
          {params.mode === "video"
            ? <CandidateVideo candidateName={params.candidateName} userSpeaking={userState==="speaking"}/>
            : <>
                <div style={{ fontSize:44 }}>🧑‍💼</div>
                <div style={{ fontSize:15, fontWeight:700, color:"#f1f5f9", marginTop:6 }}>
                  {params.candidateName}
                </div>
                <div style={{ display:"flex", alignItems:"center", justifyContent:"center", gap:6, marginTop:8 }}>
                  {userState==="speaking" && <Wave color="#10b981" bars={4} height={16}/>}
                  <span style={{
                    fontSize:12, fontWeight:600,
                    color:userState==="speaking"?"#10b981":userState==="away"?"#f59e0b":"#475569",
                  }}>
                    {userState==="speaking" ? "🎤 Speaking…"
                     : userState==="away"   ? "🔇 Please speak now"
                     :                        "🎤 Listening"}
                  </span>
                </div>
              </>
          }
        </div>

        {/* Round complete banner */}
        {roundInfo && (
          <div style={{
            padding:"14px 16px", borderRadius:12, textAlign:"center",
            background:roundInfo.decision==="Selected"
              ? "linear-gradient(135deg,#064e3b,#065f46)"
              : "linear-gradient(135deg,#7f1d1d,#991b1b)",
            border:`1px solid ${roundInfo.decision==="Selected"?"#10b981":"#ef4444"}`,
            boxShadow:`0 0 20px ${roundInfo.decision==="Selected"?"#10b98144":"#ef444444"}`,
          }}>
            <div style={{ fontSize:12, color:"#94a3b8", marginBottom:4 }}>
              {roundInfo.round} — Complete
            </div>
            <div style={{
              fontSize:22, fontWeight:900,
              color:roundInfo.decision==="Selected"?"#34d399":"#f87171",
            }}>
              {roundInfo.decision==="Selected" ? "✅ Selected!" : "❌ Rejected"}
            </div>
            <div style={{ fontSize:13, color:"#94a3b8", marginTop:4 }}>
              Avg: <strong style={{ color:"#e2e8f0" }}>{roundInfo.average_score}/10</strong>
            </div>
            {roundInfo.decision==="Selected" && (
              <div style={{
                marginTop:8, fontSize:12, color:"#fbbf24", fontWeight:600,
                animation:"pulse 1.5s infinite",
              }}>
                ⏳ Next interviewer joining…<br/>
                <span style={{ fontSize:11, fontWeight:400, color:"#94a3b8" }}>
                  Please stay in the call
                </span>
              </div>
            )}
            {roundInfo.decision!=="Selected" && (
              <div style={{ marginTop:8, fontSize:12, color:"#94a3b8" }}>
                You may close this window.<br/>
                Check Streamlit for your report.
              </div>
            )}
          </div>
        )}
      </div>

      {/* ══ RIGHT PANEL ══ */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", minWidth:0 }}>

        {/* Stats bar */}
        <div style={{
          display:"flex", background:"#0d1526",
          borderBottom:"1px solid #1e293b", flexShrink:0,
        }}>
          {[
            ["Questions", scores.length, "#a78bfa"],
            ["Avg Score", avg,           "#34d399"],
            ["Round",     scores[scores.length-1]?.round?.split(" ")[0]||"—", "#60a5fa"],
          ].map(([lbl,val,col])=>(
            <div key={lbl} style={{
              flex:1, padding:"14px 0", textAlign:"center",
              borderRight:"1px solid #1e293b",
            }}>
              <div style={{ fontSize:26, fontWeight:800, color:col,
                textShadow:`0 0 20px ${col}66` }}>{val}</div>
              <div style={{ fontSize:11, color:"#475569", textTransform:"uppercase",
                letterSpacing:1, marginTop:2 }}>{lbl}</div>
            </div>
          ))}
        </div>

        {/* Score cards */}
        <div style={{ flex:1, overflowY:"auto", padding:16 }}>
          <div style={{
            fontSize:11, color:"#475569", textTransform:"uppercase",
            letterSpacing:1, marginBottom:12, fontWeight:600,
          }}>
            📊 Live Scores — Auto Updated
          </div>

          {scores.length === 0 && (
            <div style={{
              color:"#334155", textAlign:"center",
              marginTop:60, fontSize:14,
            }}>
              {agentState==="initializing"
                ? "🔗 Connecting to AI interviewer…"
                : "⏳ Waiting for your first answer…"}
            </div>
          )}

          {scores.map((e,i) => <ScoreCard key={i} e={e}/>)}
        </div>

        {/* Code Editor for Hands-on Discussion */}
        {(currentRound === "Hands-on Discussion" || agentState !== "initializing") && (
          <div style={{
            background:"#0d1526",
            borderTop:"1px solid #1e293b",
            flexShrink:0,
          }}>
            <div
              onClick={() => setShowCode(v=>!v)}
              style={{
                padding:"10px 16px", cursor:"pointer",
                display:"flex", alignItems:"center", gap:8,
                background:"#1e293b",
                borderTop:"1px solid #334155",
              }}>
              <span style={{ fontSize:13, fontWeight:700, color:"#e2e8f0" }}>
                💻 Code Answer Panel
              </span>
              <span style={{ fontSize:11, color:"#64748b" }}>
                (for Hands-on Discussion — type or paste your code here)
              </span>
              <span style={{ marginLeft:"auto", color:"#64748b", fontSize:12 }}>
                {showCode ? "▼" : "▶"}
              </span>
            </div>
            {showCode && (
              <div style={{ padding:"12px 16px" }}>
                <textarea
                  value={codeAnswer}
                  onChange={e => setCodeAnswer(e.target.value)}
                  placeholder={"// Type your code answer here...\n// e.g. SQL query, Python function, test case\n// Speak your explanation while typing"}
                  style={{
                    width:"100%", height:200,
                    background:"#0f172a",
                    color:"#34d399",
                    border:"1px solid #334155",
                    borderRadius:8,
                    padding:"12px",
                    fontFamily:"'Fira Code', 'Courier New', monospace",
                    fontSize:13,
                    lineHeight:1.6,
                    resize:"vertical",
                    outline:"none",
                    boxSizing:"border-box",
                  }}
                />
                <div style={{ display:"flex", gap:8, marginTop:8 }}>
                  <button
                    onClick={() => {
                      if (codeAnswer.trim()) {
                        setTranscript(p => [...p, {
                          role:"user", name:"Code Answer",
                          text:"[Code submitted]: " + codeAnswer.substring(0,100) + (codeAnswer.length>100?"...":""),
                          ts: new Date().toLocaleTimeString(),
                        }]);
                      }
                    }}
                    style={{
                      background:"#6366f1", color:"#fff",
                      border:"none", borderRadius:6,
                      padding:"8px 16px", fontSize:12,
                      fontWeight:700, cursor:"pointer",
                    }}>
                    📤 Submit Code
                  </button>
                  <button
                    onClick={() => setCodeAnswer("")}
                    style={{
                      background:"#334155", color:"#94a3b8",
                      border:"none", borderRadius:6,
                      padding:"8px 16px", fontSize:12,
                      cursor:"pointer",
                    }}>
                    🗑 Clear
                  </button>
                  <span style={{ fontSize:11, color:"#475569", alignSelf:"center" }}>
                    💡 Speak your explanation while typing the code
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Transcript */}
        <div ref={transcriptRef} style={{
          height:200,
          background:"#0d1526",
          borderTop:"1px solid #1e293b",
          padding:"12px 16px",
          overflowY:"auto",
          flexShrink:0,
        }}>
          <div style={{
            fontSize:11, color:"#475569", textTransform:"uppercase",
            letterSpacing:1, marginBottom:8, fontWeight:600,
            display:"flex", alignItems:"center", gap:8,
          }}>
            💬 Transcript
            {userState==="speaking" && (
              <span style={{ color:"#10b981", fontSize:11, fontWeight:700,
                display:"flex", alignItems:"center", gap:4 }}>
                <div style={{ width:6, height:6, borderRadius:"50%",
                  background:"#10b981", animation:"pulse 1s infinite" }}/>
                Recording
              </span>
            )}
          </div>

          {transcript.length===0 && (
            <div style={{ fontSize:13, color:"#334155", fontStyle:"italic" }}>
              Conversation will appear here…
            </div>
          )}

          {transcript.map((t,i) => (
            <div key={i} style={{ marginBottom:8 }}>
              <span style={{
                fontSize:12, fontWeight:700, marginRight:6,
                color:t.role==="user"?"#34d399":"#818cf8",
              }}>
                {t.name}
              </span>
              <span style={{ fontSize:11, color:"#475569", marginRight:6 }}>
                {t.ts}
              </span>
              <span style={{ fontSize:13, color:"#cbd5e1", lineHeight:1.5 }}>
                {t.text}
              </span>
            </div>
          ))}
        </div>
      </div>

      <RoomAudioRenderer/>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
        @keyframes wave  { 0%,100%{height:5px} 50%{height:26px} }
        ::-webkit-scrollbar { width:5px }
        ::-webkit-scrollbar-thumb { background:#1e293b; border-radius:3px }
        ::-webkit-scrollbar-track { background:transparent }
      `}</style>
    </div>
  );
}

function CandidateVideo({ candidateName, userSpeaking }) {
  const vt = useTracks([{source:Track.Source.Camera,withPlaceholder:false}])
    .filter(t=>t.participant?.isLocal);
  return vt[0] ? (
    <div style={{ position:"relative" }}>
      <VideoTrack trackRef={vt[0]}
        style={{ width:"100%", aspectRatio:"4/3", objectFit:"cover" }}/>
      <div style={{
        position:"absolute", bottom:0, left:0, right:0,
        background:"rgba(0,0,0,.75)", padding:"6px 10px",
        display:"flex", alignItems:"center", gap:8,
      }}>
        <span style={{ fontSize:13, fontWeight:700, color:"#f1f5f9" }}>
          {candidateName}
        </span>
        {userSpeaking && <Wave color="#10b981" bars={3} height={14}/>}
      </div>
    </div>
  ) : (
    <div style={{ padding:16, textAlign:"center" }}>
      <div style={{ fontSize:40 }}>🧑‍💼</div>
      <div style={{ fontSize:13, color:"#f1f5f9", marginTop:6 }}>{candidateName}</div>
      <div style={{ fontSize:11, color:"#475569", marginTop:3 }}>Camera starting…</div>
    </div>
  );
}

export default function App() {
  const params = getParams();
  if (!params.serverUrl || !params.token) return (
    <div style={{
      display:"flex", alignItems:"center", justifyContent:"center",
      height:"100vh", background:"#0a0f1e", color:"#e2e8f0", fontSize:18,
    }}>
      Missing serverUrl or token.
    </div>
  );
  return (
    <LiveKitRoom
      serverUrl={params.serverUrl}
      token={params.token}
      connect={true}
      audio={true}
      video={params.mode === "video"}
      options={{
        audioCaptureDefaults: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: true,
          deviceId: "",
        },
      }}
      style={{ height:"100vh" }}
    >
      <Room params={params}/>
    </LiveKitRoom>
  );
}

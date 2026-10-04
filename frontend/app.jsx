const {useState, useEffect, useRef} = React;

const api = {
  token: localStorage.getItem("aa_token") || "",
  async req(path, opts={}) {
    const res = await fetch(path, {
      ...opts,
      headers: {"Content-Type":"application/json",
        ...(api.token ? {Authorization:"Bearer "+api.token} : {}),
        ...(opts.headers||{})},
    });
    const data = await res.json().catch(()=>({detail:"Server error"}));
    if(!res.ok) throw new Error(data.detail || "Request failed");
    return data;
  },
  get(p){return api.req(p);},
  post(p,b){return api.req(p,{method:"POST",body:JSON.stringify(b||{})});},
  put(p,b){return api.req(p,{method:"PUT",body:JSON.stringify(b||{})});},
  del(p){return api.req(p,{method:"DELETE"});},
};

const DIFF_COLOR = {easy:"good",medium:"warn",hard:"bad",expert:"bad"};
const LETTERS = ["A","B","C","D"];
const DOTCOLORS = ["#d9501e","#2f3fe0","#1e7a4c","#e9a800","#7c3aed","#0e7c86","#c92a5b","#5a6b00"];
function dotFor(s){let h=0;const t=String(s||"?");for(const c of t)h=(h*31+c.charCodeAt(0))>>>0;return DOTCOLORS[h%DOTCOLORS.length];}
function first(u){return (u.name||"there").split(" ")[0];}

function useTheme(){
  const [t,setT] = useState(localStorage.getItem("aa_theme")||"light");
  useEffect(()=>{document.documentElement.dataset.theme=t;localStorage.setItem("aa_theme",t);},[t]);
  return [t,()=>setT(t==="light"?"dark":"light")];
}

function Logo(){
  return <div className="logo"><span className="mark">A</span><span>AdaptiveAI</span> <small>CLASS 12 · AI</small></div>;
}
function Foot(){
  return <footer className="foot"><b>AdaptiveAI</b> · a Class 12 AI capstone. Same first question for everyone, a different quiz for everyone. FastAPI · React · SQLite.</footer>;
}

/* ---------------- APP SHELL ---------------- */
function App(){
  const [theme,toggle] = useTheme();
  const [user,setUser] = useState(null);
  const [page,setPage] = useState("dashboard");
  const [streams,setStreams] = useState({});
  const [err,setErr] = useState("");

  const loadMe = async ()=>{
    if(!api.token){setUser(null);return;}
    try{ const me = await api.get("/api/me"); setUser(me); }
    catch(e){ api.token=""; localStorage.removeItem("aa_token"); setUser(null); }
  };
  useEffect(()=>{ loadMe(); api.get("/api/streams").then(setStreams).catch(()=>{}); },[]);

  const logout = ()=>{api.token="";localStorage.removeItem("aa_token");setUser(null);setPage("dashboard");};

  if(!user) return (
    <div>
      <div className="topbar"><Logo/><div className="spacer"/>
        <button className="btn small ghost" onClick={toggle}>{theme==="light"?"Dark mode":"Light mode"}</button></div>
      <div className="layout" style={{maxWidth:980}}><Auth onAuth={(u,t)=>{api.token=t;localStorage.setItem("aa_token",t);setUser(u);}} streams={streams}/><Foot/></div>
    </div>
  );

  return (
    <div>
      <div className="topbar">
        <Logo/>
        <div className="nav">
          {[["dashboard","Dashboard"],["quiz","Quiz"],["review","Review"],["leaderboard","Leaderboard"],["demo","AI demo"],["howai","How it works"],...(user.is_admin?[["admin","Staff room"]]:[])].map(([k,l])=>(
            <button key={k} className={page===k?"active":""} onClick={()=>setPage(k)}>{l}</button>
          ))}
        </div>
        <div className="spacer"/>
        <span className="badge"><span className="subdot" style={{background:"var(--gold)"}}/>{user.reward_points} pts · {user.tier_name}</span>
        <button className="btn small ghost" onClick={toggle}>{theme==="light"?"Dark":"Light"}</button>
        <button className="btn small ghost" onClick={()=>setPage("profile")}>{first(user)}</button>
        <button className="btn small ghost" onClick={logout}>Log out</button>
      </div>
      <div className="layout">
        {err && <div className="card" style={{marginBottom:12}}>Something went wrong — {err}</div>}
        {page==="dashboard" && <Dashboard user={user} refresh={loadMe} go={setPage}/>}
        {page==="quiz" && <QuizSetup user={user} streams={streams} startQuiz={(cfg)=>{quizCfg=cfg;setPage("quizrun");}}/>}
        {page==="quizrun" && <QuizRun cfg={quizCfg} user={user} refresh={loadMe} go={setPage}/>}
        {page==="review" && <Review/>}
        {page==="leaderboard" && <Leaderboard user={user}/>}
        {page==="demo" && <Demo/>}
        {page==="howai" && <HowAI/>}
        {page==="admin" && <Admin/>}
        {page==="profile" && <Profile user={user} streams={streams} refresh={loadMe}/>}
        <Foot/>
      </div>
    </div>
  );
}
let quizCfg = {subject:"Mathematics", num_questions:10};

/* ---------------- AUTH ---------------- */
function Auth({onAuth, streams}){
  const [mode,setMode] = useState("login");
  const [f,setF] = useState({name:"",email:"",password:"",stream:"Science Non-Medical",student_class:"12"});
  const [msg,setMsg] = useState("");
  const submit = async (e)=>{
    e.preventDefault(); setMsg("");
    try{
      const data = mode==="login"
        ? await api.post("/api/login",{email:f.email,password:f.password})
        : await api.post("/api/signup",f);
      onAuth(data.user,data.token);
    }catch(e){setMsg(e.message);}
  };
  const streamNames = Object.keys(streams||{});
  return (
    <div className="grid g2">
      <div className="hero fade">
        <div className="kicker" style={{color:"var(--hero-paper)",opacity:.8}}>Class 12 · Artificial Intelligence</div>
        <h1>Same first question. <span className="squiggle">Your own quiz</span> after that.</h1>
        <p>AdaptiveAI watches how accurately — and how quickly — you answer, then picks each next question to match your level. Two students can start side by side and end up in completely different places.</p>
        <p className="muted">Everyone begins on one shared baseline question. The difficulty, the tier and the recommendations all follow from what you do next.</p>
        <div><span className="creds">try it — student: ayushi@demo.school / demo1234<br/>teacher: admin@adaptiveai.school / admin123</span></div>
      </div>
      <div className="card fade">
        <div className="kicker">{mode==="login"?"Welcome back":"Join the class"}</div>
        <div className="row" style={{marginBottom:12}}>
          <button className={"btn small"+(mode==="login"?"":" ghost")} onClick={()=>setMode("login")}>Sign in</button>
          <button className={"btn small"+(mode==="signup"?"":" ghost")} onClick={()=>setMode("signup")}>Sign up</button>
        </div>
        <form onSubmit={submit} className="grid">
          {mode==="signup" && <div><label>Full name</label><input placeholder="e.g. Ayushi Sharma" value={f.name} onChange={e=>setF({...f,name:e.target.value})} required/></div>}
          <div><label>Email</label><input type="email" autoComplete="email" placeholder="you@school.in" value={f.email} onChange={e=>setF({...f,email:e.target.value})} required/></div>
          <div><label>Password</label><input type="password" autoComplete="current-password" placeholder="6 characters minimum" value={f.password} onChange={e=>setF({...f,password:e.target.value})} required/></div>
          {mode==="signup" && <div className="grid g2">
            <div><label>Stream</label><select value={f.stream} onChange={e=>setF({...f,stream:e.target.value})}>
              {streamNames.map(s=><option key={s} value={s}>{s}</option>)}
            </select></div>
            <div><label>Class</label><select value={f.student_class} onChange={e=>setF({...f,student_class:e.target.value})}>
              <option value="11">Class 11</option><option value="12">Class 12</option>
            </select></div>
          </div>}
          {msg && <div style={{color:"var(--persimmon)",fontWeight:700}}>{msg}</div>}
          <button className="btn">{mode==="login"?"Sign in →":"Create my account →"}</button>
          <div className="row">
            <button type="button" className="btn small ghost" onClick={()=>{setF({...f,email:"ayushi@demo.school",password:"demo1234"});setMode("login");}}>Use student demo</button>
            <button type="button" className="btn small ghost" onClick={()=>{setF({...f,email:"admin@adaptiveai.school",password:"admin123"});setMode("login");}}>Use teacher demo</button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ---------------- DASHBOARD ---------------- */
function Dashboard({user, refresh, go}){
  const [d,setD] = useState(null);
  useEffect(()=>{api.get("/api/dashboard").then(setD).catch(()=>{});refresh();},[]);
  if(!d) return <div className="card">Fetching your numbers…</div>;
  const s = d.stats;
  return (
    <div className="grid">
      <div className="hero fade">
        <div className="kicker" style={{color:"var(--hero-paper)",opacity:.8}}>{user.stream||"No stream yet"} · Class {user.student_class} · {user.tier_name} tier</div>
        <h1>Good to see you, {first(user)}.</h1>
        <p className="muted">Here is where your preparation stands. The engine has been paying attention.</p>
        <div className="row" style={{marginTop:12}}>
          <span className="badge">Tier {user.current_tier} · {user.tier_name}</span>
          <span className="badge">{s.total} solved</span>
          <span className="badge">{s.accuracy}% accurate</span>
          <span className="badge">avg {s.avg_time}s a question</span>
          <span className="badge">{user.reward_points} pts</span>
          <span className="badge">rank #{user.rank||"—"} in stream</span>
        </div>
        <div style={{marginTop:14}} className="bar tierbar"><i style={{width:(user.tier_progress||0)+"%"}}/></div>
        <div className="muted" style={{fontSize:13,marginTop:6}}>{user.tier_progress||0}% of the way to the next tier</div>
      </div>
      <div className="grid g2">
        <div className="card fade">
          <div className="kicker">Form</div><h3>Accuracy lately</h3>
          {s.trend.length===0 ? <p className="muted">No quizzes yet — the graph is shy. Take one and it will show up.</p> :
          <div className="row" style={{alignItems:"end",minHeight:90}}>{s.trend.map((v,i)=>(
            <div key={i} style={{flex:1,textAlign:"center"}}><div style={{height:Math.max(8,v*0.9),background:"var(--ink)",borderRadius:6,opacity:.85}}/><small className="num">{v}%</small></div>))}</div>}
          <p className="muted">Current streak: <b className="num">{s.streak} in a row</b></p>
          <div className="row"><button className="btn" onClick={()=>go("quiz")}>Start a quiz →</button>
          <button className="btn ghost" onClick={()=>go("demo")}>Watch the AI demo</button></div>
        </div>
        <div className="card fade">
          <div className="kicker">By subject</div><h3>Where you stand</h3>
          {Object.keys(s.subjects).length===0 ? <p className="muted">Nothing here yet — your bars will appear after the first quiz.</p> :
          Object.entries(s.subjects).map(([k,v])=>(<div key={k} style={{marginBottom:9}}><div className="row"><span><span className="subdot" style={{background:dotFor(k)}}/>{k}</span><div className="spacer"/><span className="num">{v}%</span></div><div className="bar"><i style={{width:v+"%"}}/></div></div>))}
          <hr className="divider"/>
          <div className="kicker">Up next</div><h3>Suggested for you</h3>
          {d.recommendations.map((r,i)=>(<div key={i} className="card" style={{marginBottom:8,background:"var(--wash)",boxShadow:"none"}}><b>{r.title}</b><p className="muted" style={{margin:"4px 0"}}>{r.reason}</p><button className="btn small" onClick={()=>go("quiz")}>{r.cta}</button></div>))}
        </div>
      </div>
      <div className="grid g2">
        <div className="card">
          <div className="kicker">Honest feedback</div><h3>Worth a second look</h3>
          {s.weak.length===0?<p className="muted">Nothing flagging right now. Enjoy it while it lasts.</p>:
          s.weak.map(([t,v])=>(<div key={t} className="row" style={{marginBottom:6}}><span>{t}</span><div className="spacer"/><b className="num">{v}%</b></div>))}
          {s.strong.length>0 && <><h3 style={{marginTop:14}}>Going well</h3>{s.strong.map(([t,v])=>(<div key={t} className="row"><span>{t}</span><div className="spacer"/><b className="num">{v}%</b></div>))}</>}
        </div>
        <div className="card">
          <div className="kicker">History</div><h3>Recent outings</h3>
          {d.recent.length===0?<p className="muted">No quizzes yet.</p>:
          <table><thead><tr><th>Subject</th><th>Score</th><th>Acc</th><th>Date</th></tr></thead><tbody>
          {d.recent.map((r,i)=><tr key={i}><td><span className="subdot" style={{background:dotFor(r.subject)}}/>{r.subject}</td><td className="num">{r.score}</td><td className="num">{r.accuracy}%</td><td>{r.date}</td></tr>)}
          </tbody></table>}
        </div>
      </div>
    </div>
  );
}

/* ---------------- QUIZ SETUP ---------------- */
function QuizSetup({user, streams, startQuiz}){
  const subs = streams[user.stream]||["Mathematics"];
  const [subject,setSubject] = useState(subs[0]||"Mathematics");
  const [n,setN] = useState(10);
  useEffect(()=>{setSubject((streams[user.stream]||["Mathematics"])[0]);},[user.stream]);
  return (
    <div className="grid" style={{maxWidth:660,margin:"0 auto"}}>
      <div className="card fade">
        <div className="kicker">New quiz</div><h3>Set it up</h3>
        <p className="muted">One rule: everyone starts on the same baseline question. After that, the quiz is yours alone.</p>
        <label>Stream</label><input value={user.stream||""} disabled/>
        <label>Subject</label><select value={subject} onChange={e=>setSubject(e.target.value)}>{subs.map(s=><option key={s}>{s}</option>)}</select>
        <label>Length</label><select value={n} onChange={e=>setN(+e.target.value)}><option value={5}>5 questions — a quick round</option><option value={10}>10 questions — the standard</option><option value={20}>20 questions — the full run</option></select>
        <div style={{height:10}}/>
        <button className="btn" onClick={()=>{quizCfg={subject,num_questions:n};startQuiz(quizCfg);}}>Begin →</button>
      </div>
      <div className="card">
        <div className="kicker">Under the hood</div><h3>How the adapting works</h3>
        <p className="muted">Every answer earns a performance score — accuracy counts for 70%, speed for 30%, judged across your last five questions. Above 85 and you are on expert material; below 50 and it eases off. Fast, correct answers climb tiers quicker; a wrong answer steps things down gently instead of punishing you.</p>
      </div>
    </div>
  );
}

/* ---------------- QUIZ RUN ---------------- */
function QuizRun({cfg, user, refresh, go}){
  const [state,setState] = useState({loading:true});
  const [sel,setSel] = useState(-1);
  const [fb,setFb] = useState(null);
  const [time,setTime] = useState(0);
  const [left,setLeft] = useState(0);
  const [qnum,setQnum] = useState(1);
  const [removed,setRemoved] = useState([]);
  const [hint,setHint] = useState("");
  const [usedPU,setUsedPU] = useState({});
  const [balance,setBalance] = useState(user.reward_points||0);
  const [secondChance,setSecondChance] = useState(false);
  const timerRef = useRef(null);
  const t0 = useRef(Date.now());

  const start = async ()=>{
    setState({loading:true});
    try{
      const r = await api.post("/api/quiz/start",{subject:cfg.subject,num_questions:cfg.num_questions});
      setState({quiz_id:r.quiz_id,total:r.total,subject:r.subject,q:r.question,tier:r.tier,loading:false});
      setBalance(r.rewards); resetQ(r.question); setQnum(1); setFb(null);
    }catch(e){setState({loading:false,error:e.message});}
  };
  const resetQ = (q)=>{
    setSel(-1);setFb(null);setRemoved([]);setHint("");setSecondChance(false);
    t0.current = Date.now(); setTime(0); setLeft(q.expected_time);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(()=>{
      const el = (Date.now()-t0.current)/1000;
      setTime(el); setLeft(Math.max(0,Math.round(q.expected_time-el)));
    },250);
  };
  useEffect(()=>{start();return ()=>clearInterval(timerRef.current);},[]);

  const submit = async ()=>{
    if(sel<0||!state.q||fb) return;
    clearInterval(timerRef.current);
    const rt = Math.max(0.5,Math.round(((Date.now()-t0.current)/1000)*10)/10);
    try{
      const r = await api.post("/api/quiz/answer",{quiz_id:state.quiz_id,question_id:state.q.id,selected:sel,response_time:rt});
      if(!r.feedback.correct && secondChance && !fb){
        setSecondChance("consumed"); setFb({...r.feedback, retry:true});
      } else { setFb(r.feedback); }
      setBalance(r.feedback.total_rewards); refresh();
      setState(s=>({...s,next:r.next_question,tier:r.feedback.tier}));
    }catch(e){alert(e.message);}
  };
  const next = ()=>{
    if(qnum>=state.total){ go("dashboard"); return; }
    if(!state.next){ go("dashboard"); return; }
    setQnum(qnum+1); setState(s=>({...s,q:s.next,next:null})); resetQ(state.next);
  };
  const powerup = async (kind)=>{
    if(usedPU[kind]){alert("Each lifeline works once per quiz.");return;}
    try{
      const r = await api.post("/api/quiz/powerup",{quiz_id:state.quiz_id,question_id:state.q.id,kind});
      setBalance(r.balance); refresh();
      if(kind==="fifty") setRemoved(r.remove);
      if(kind==="hint") setHint(r.hint);
      if(kind==="time"){ setLeft(l=>l+15); t0.current += 15000; }
      if(kind==="second_chance") setSecondChance(true);
      setUsedPU({...usedPU,[kind]:true});
    }catch(e){alert(e.message);}
  };

  if(state.loading) return <div className="card">Setting the baseline question…</div>;
  if(state.error) return <div className="card">Could not start — {state.error} <button className="btn" onClick={()=>go("quiz")}>Back</button></div>;
  const q = state.q;
  return (
    <div className="quizshell">
      <div className="card fade">
        <div className="kicker">{state.subject} · {q.topic}</div>
        <div className="row"><h2 className="serif" style={{margin:0,fontSize:22}}>Question {qnum} <span className="muted" style={{fontSize:15}}>of {state.total}</span></h2><div className="spacer"/><span className="timer num">{left}s left</span></div>
        <div style={{margin:"10px 0"}}><span className="pill sticker">Tier {state.tier.tier} — {state.tier.name}</span> <span className={"pill "+(DIFF_COLOR[q.difficulty]||"")}>{q.difficulty}</span></div>
        <div className="bar tierbar"><i style={{width:(state.tier.progress||0)+"%"}}/></div>
        <div className="row" style={{marginTop:8}}><span className="muted">Usually takes about {q.expected_time}s</span><div className="spacer"/><span className="badge">{balance} pts</span></div>
        <h2 className="serif" style={{margin:"14px 0",fontSize:24}}>{q.question}</h2>
        {q.options.map((o,i)=> removed.includes(i)?null:(
          <button key={i} disabled={!!fb} className={"opt"+(sel===i?" sel":"")+(fb&&i===fb.correct_answer?" correct":"")+(fb&&sel===i&&!fb.correct?" wrong":"")} onClick={()=>setSel(i)}><span className="optkey">{LETTERS[i]}</span><span>{o}</span></button>
        ))}
        {!fb ? <div style={{marginTop:10}}>
            <button className="btn" onClick={submit} disabled={sel<0}>Lock in {sel>=0?LETTERS[sel]:"an answer"}</button>
            <div className="kicker" style={{marginTop:14}}>Lifelines — points buy help, each once per quiz</div>
            <div className="row">
              <button className="btn small ghost" title="Drop two wrong options · 40 pts" onClick={()=>powerup("fifty")}>{usedPU.fifty?"50-50 · used":"50-50 · 40 pts"}</button>
              <button className="btn small ghost" title="A nudge in the right direction · 50 pts" onClick={()=>powerup("hint")}>{usedPU.hint?"Hint · used":"Hint · 50 pts"}</button>
              <button className="btn small ghost" title="15 more seconds · 30 pts" onClick={()=>powerup("time")}>{usedPU.time?"+15s · used":"+15s · 30 pts"}</button>
              <button className="btn small ghost" title="Answer again after a miss · 70 pts" onClick={()=>powerup("second_chance")}>{usedPU.second_chance?"Retry · used":"Retry · 70 pts"}</button>
            </div>
          </div>
        : <div className="card fade rewardpop" style={{marginTop:12,background:"var(--wash)",boxShadow:"none"}}>
            <div className="kicker">Verdict</div>
            <b className="serif" style={{fontSize:19}}>{fb.correct?"Correct. Nicely done.":"Not this time."}</b> <span className="muted">The answer is <b>{fb.correct_text}</b>.</span>
            <p>{fb.explanation}</p>
            <div className="row">
              <span className="badge rewardpop">+{fb.reward} pts <span className="muted">· base {fb.breakdown.base}, speed {fb.breakdown.speed_bonus}, streak {fb.breakdown.streak_bonus}</span></span>
              {fb.streak>=3 && <span className="badge">{fb.streak} in a row — keep going</span>}
            </div>
            <p className="muted">Engine notes — performance {fb.performance} (accuracy {fb.accuracy_score}, speed {fb.speed_score}), next up: <b>{fb.next_difficulty}</b>. {fb.ai_note} {fb.tier_note}</p>
            <ExplainBox qid={q.id} sel={sel}/>
            <div style={{marginTop:8}}><button className="btn" onClick={next}>{qnum>=state.total?"Finish up →":"Next question →"}</button></div>
          </div>}
        {hint && <div className="card" style={{marginTop:8,boxShadow:"none"}}><b>Hint — </b>{hint}</div>}
        <div style={{marginTop:12}} className="bar"><i style={{width:(qnum/state.total*100)+"%"}}/></div>
      </div>
    </div>
  );
}

function ExplainBox({qid, sel}){
  const [t,setT] = useState("");
  return <div><button className="btn small ghost" onClick={async()=>{const r=await api.post("/api/explain",{question_id:qid,selected:sel});setT(r.explanation);}}>Explain it simply</button>{t && <p className="muted">{t}</p>}</div>;
}

/* ---------------- REVIEW ---------------- */
function Review(){
  const [rows,setRows] = useState([]);
  useEffect(()=>{api.get("/api/mistakes").then(setRows).catch(()=>{});},[]);
  const pending = rows.filter(r=>!r.understood);
  return (
    <div className="grid" style={{maxWidth:820,margin:"0 auto"}}>
      <div className="card">
        <div className="kicker">Review</div><h3 className="serif">Mistakes, minus the shame.</h3>
        <p className="muted">{rows.length===0 ? "No mistakes on record. Either flawless, or no quizzes taken yet." : pending.length+" still to fix."}</p>
        {rows.map(m=>(
          <div key={m.mistake_id} className="card fade" style={{marginBottom:10,background:"var(--wash)",boxShadow:"none",opacity:m.understood?0.7:1}}>
            <span className="pill">{m.subject}</span> <span className="pill">{m.topic}</span> <span className="pill">{m.difficulty}</span> {m.understood&&<span className="pill good">understood</span>}
            <p><b>Q. {m.question}</b></p>
            <p>You picked <b>{m.your_answer}</b> — the answer is <b>{m.correct_answer}</b>.</p>
            <p className="muted">Why — {m.explanation}</p>
            <p><i>Worth knowing — {m.tip}</i></p>
            {!m.understood && <button className="btn small" onClick={async()=>{await api.post(`/api/mistakes/${m.mistake_id}/understood`);setRows(rows.map(r=>r.mistake_id===m.mistake_id?{...r,understood:true}:r));}}>Got it, mark understood</button>}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------------- LEADERBOARD ---------------- */
function Leaderboard({user}){
  const [rows,setRows] = useState([]);
  const [f,setF] = useState({stream:user.stream||"",subject:"",period:"overall"});
  const [streams,setStreams] = useState({});
  useEffect(()=>{api.get("/api/streams").then(setStreams).catch(()=>{});},[]);
  const load = ()=>{
    const p = new URLSearchParams({stream:f.stream,subject:f.subject,period:f.period});
    api.get("/api/leaderboard?"+p.toString()).then(setRows).catch(()=>{});
  };
  useEffect(load,[f.stream,f.period]);
  const subs = ["",...(streams[f.stream]||[])];
  return (
    <div className="card fade">
      <div className="kicker">Leaderboard</div><h3 className="serif">The table.</h3>
      <p className="muted">Ordered by correct answers first, then tier, then points. No personal details beyond a name.</p>
      <div className="row">
        <select className="filters" value={f.stream} onChange={e=>setF({...f,stream:e.target.value,subject:""})}><option value="">All streams</option>{Object.keys(streams).map(s=><option key={s} value={s}>{s}</option>)}</select>
        <select className="filters" value={f.subject} onChange={e=>setF({...f,subject:e.target.value})}><option value="">All subjects</option>{subs.filter(Boolean).map(s=><option key={s} value={s}>{s}</option>)}</select>
        <select className="filters" value={f.period} onChange={e=>setF({...f,period:e.target.value})}><option value="overall">All time</option><option value="weekly">This week</option><option value="monthly">This month</option></select>
        <button className="btn small" onClick={load}>Refresh</button>
      </div>
      <table style={{marginTop:10}}><thead><tr><th>#</th><th>Student</th><th>Correct</th><th>Tier</th><th>Points</th></tr></thead><tbody>
        {rows.map(r=><tr key={r.rank} style={r.name===user.name?{fontWeight:800}:{}}><td>{r.rank===1?<span className="rank1">1</span>:r.rank}</td><td>{r.name}{r.name===user.name?" · you":""}</td><td className="num">{r.correct}</td><td>{r.tier}</td><td className="num">{r.points}</td></tr>)}
      </tbody></table>
      {rows.length===0 && <p className="muted">Nobody on this board yet. Be the first name on it.</p>}
    </div>
  );
}

/* ---------------- DEMO ---------------- */
function Demo(){
  const [d,setD] = useState(null);
  const run = async ()=>{ setD(null); setD(await api.post("/api/demo/simulate")); };
  useEffect(()=>{run();},[]);
  if(!d) return <div className="card">Setting up both students…</div>;
  const cols = ["studentA","studentB"];
  return (
    <div className="grid">
      <div className="hero">
        <div className="kicker" style={{color:"var(--hero-paper)",opacity:.8}}>For the viva</div>
        <h1>Two students. <span className="squiggle">One starting question.</span></h1>
        <p>Both begin on the same baseline. One answers fast and accurately, the other slowly and unevenly. This is what the engine does with each of them, question by question.</p>
        <p className="muted">Both start here — “{d.studentA.baseline}”</p>
        <button className="btn warm" onClick={run}>Run it again</button>
      </div>
      <div className="grid g2">
        {cols.map((k)=>(
          <div key={k} className="card fade">
            <div className="kicker">{k==="studentA"?"Fast & accurate":"Slow & uneven"}</div>
            <h3 className="serif">{d[k].label}</h3>
            <p className="muted">Finishes at {d[k].accuracy}% accuracy, Tier {d[k].final_tier}.</p>
            {d[k].path.map(p=>(
              <div key={p.q} className="card" style={{marginBottom:8,boxShadow:"none",borderLeftWidth:6,borderLeftColor:p.correct?"var(--leaf)":"var(--persimmon)"}}>
                <b className="num">Q{p.q}</b> <span className="pill">{p.difficulty}</span> <span className="muted num">{p.response_time}s · Tier {p.tier}</span>
                <div className="muted" style={{fontSize:13}}>{p.question}…</div>
                <div style={{fontSize:13}}>score <b className="num">{p.performance}</b> → next: <b>{p.next_difficulty}</b></div>
                <div className="muted" style={{fontSize:12}}>{p.ai_note}</div>
              </div>))}
          </div>))}
      </div>
      <div className="card"><div className="kicker">If the examiner asks</div><h3 className="serif">What to point at</h3>
        <p className="muted">Student A climbs from medium to expert within a few questions. Student B gets easier, related questions until the footing is steady. Same start, different journey — that is the whole project.</p></div>
    </div>
  );
}

/* ---------------- HOW IT WORKS ---------------- */
function HowAI(){
  const steps = ["Student answers a question","Accuracy is weighed across the last five answers, recent ones counting more","Response time is compared against what the question should take","Performance score = accuracy × 0.7 + speed × 0.3","Level is set: above 85 expert · 70–85 hard · 50–70 medium · below 50 easy","Next question is picked: right difficulty, weak topics first, never a repeat","Tier and rewards update — fast correct answers climb quicker"];
  return (
    <div className="grid" style={{maxWidth:740,margin:"0 auto"}}>
      <div className="card">
        <div className="kicker">Transparency</div><h3 className="serif">The engine, without the mystery.</h3>
        <p className="muted">There is no black box here. Every decision the quiz makes traces back to these steps:</p>
        <div className="flow">{steps.map((s,i)=>(<React.Fragment key={i}><div className="step"><b className="num">{i+1}.</b> {s}</div>{i<steps.length-1&&<div className="arrow">↓</div>}</React.Fragment>))}</div>
        <div className="grid g2" style={{marginTop:12}}>
          <div className="card" style={{background:"var(--wash)",boxShadow:"none"}}><b>What it looks at</b><p className="muted">Right or wrong · how long you took · your recent run · the subject, topic and difficulty</p></div>
          <div className="card" style={{background:"var(--wash)",boxShadow:"none"}}><b>What it decides</b><p className="muted">Raise, hold or lower the difficulty · nudge you toward a weak topic · move your tier</p></div>
        </div>
      </div>
    </div>
  );
}

/* ---------------- ADMIN ---------------- */
function Admin(){
  const [qs,setQs] = useState([]);
  const [ov,setOv] = useState(null);
  const [f,setF] = useState({question:"",options:["","","",""],answer:0,subject:"Mathematics",stream:"Science Non-Medical",topic:"",difficulty:"medium",expected_time:20,explanation:"",hint:""});
  const [editId,setEditId] = useState(null);
  const load = async ()=>{ setQs(await api.get("/api/admin/questions")); setOv(await api.get("/api/admin/overview")); };
  useEffect(()=>{load().catch(e=>alert(e.message));},[]);
  const save = async (e)=>{
    e.preventDefault();
    if(editId) await api.put(`/api/admin/questions/${editId}`,f);
    else await api.post("/api/admin/questions",f);
    setEditId(null); setF({...f,question:"",options:["","","",""],explanation:"",topic:"",hint:""}); load();
  };
  return (
    <div className="grid">
      <div className="grid g4">
        <div className="card"><div className="kicker">Students</div><div className="kpi">{ov?.users??"… "}</div></div>
        <div className="card"><div className="kicker">Questions</div><div className="kpi">{ov?.questions??"… "}</div></div>
        <div className="card"><div className="kicker">Attempts</div><div className="kpi">{ov?.attempts??"… "}</div></div>
        <div className="card"><div className="kicker">Accuracy</div><div className="kpi">{ov?.accuracy??"… "}%</div></div>
      </div>
      {ov?.commonly_wrong?.length>0 && <div className="card"><div className="kicker">Fix list</div><h3 className="serif">Most-missed questions</h3>{ov.commonly_wrong.map(w=><div key={w.id} className="row"><span>{w.question}…</span><div className="spacer"/><b className="num">{w.wrong_rate}% wrong ({w.attempts})</b></div>)}</div>}
      <div className="card"><div className="kicker">Question bank</div><h3 className="serif">{editId?"Edit a question":"Add a question"}</h3>
        <form onSubmit={save} className="grid">
          <div><label>Question</label><input value={f.question} onChange={e=>setF({...f,question:e.target.value})} required/></div>
          <div className="grid g2">{f.options.map((o,i)=><div key={i}><label>Option {LETTERS[i]}{i===+f.answer?" · correct":""}</label><input value={o} onChange={e=>{const a=[...f.options];a[i]=e.target.value;setF({...f,options:a});}} required/></div>)}</div>
          <div className="grid g4">
            <div><label>Correct (0–3)</label><input type="number" min="0" max="3" value={f.answer} onChange={e=>setF({...f,answer:+e.target.value})}/></div>
            <div><label>Subject</label><input value={f.subject} onChange={e=>setF({...f,subject:e.target.value})}/></div>
            <div><label>Stream</label><select value={f.stream} onChange={e=>setF({...f,stream:e.target.value})}>{["Science Medical","Science Non-Medical","Commerce","Humanities"].map(s=><option key={s}>{s}</option>)}</select></div>
            <div><label>Difficulty</label><select value={f.difficulty} onChange={e=>setF({...f,difficulty:e.target.value})}><option>easy</option><option>medium</option><option>hard</option><option>expert</option></select></div>
          </div>
          <div className="grid g3">
            <div><label>Topic</label><input value={f.topic} onChange={e=>setF({...f,topic:e.target.value})}/></div>
            <div><label>Expected time (s)</label><input type="number" value={f.expected_time} onChange={e=>setF({...f,expected_time:+e.target.value})}/></div>
            <div><label>Hint</label><input value={f.hint} onChange={e=>setF({...f,hint:e.target.value})}/></div>
          </div>
          <div><label>Explanation</label><textarea value={f.explanation} onChange={e=>setF({...f,explanation:e.target.value})}/></div>
          <div className="row"><button className="btn">{editId?"Save changes":"Add question"}</button>{editId&&<button type="button" className="btn ghost" onClick={()=>setEditId(null)}>Cancel</button>}</div>
        </form>
      </div>
      <div className="card"><div className="kicker">Bank · {qs.length}</div><h3 className="serif">All questions <span className="muted" style={{fontSize:14}}>· showing first 60</span></h3>
        <table><thead><tr><th>ID</th><th>Question</th><th>Subject</th><th>Level</th><th></th></tr></thead><tbody>
        {qs.slice(0,60).map(q=><tr key={q.id}><td className="num">{q.id}</td><td>{q.question.slice(0,60)}…</td><td><span className="subdot" style={{background:dotFor(q.subject)}}/>{q.subject}</td><td>{q.difficulty}</td>
          <td><div className="row"><button className="btn small ghost" onClick={()=>{setEditId(q.id);setF({question:q.question,options:q.options,answer:q.answer,subject:q.subject,stream:q.stream,topic:q.topic,difficulty:q.difficulty,expected_time:q.expected_time,explanation:q.explanation,hint:q.hint||""});window.scrollTo(0,0);}}>Edit</button>
          <button className="btn small ghost" onClick={async()=>{if(confirm("Delete this question?")){await api.del(`/api/admin/questions/${q.id}`);load();}}}>Delete</button></div></td></tr>)}
        </tbody></table></div>
    </div>
  );
}

/* ---------------- PROFILE ---------------- */
function Profile({user, streams, refresh}){
  const [f,setF] = useState({name:user.name,stream:user.stream,student_class:user.student_class});
  const [msg,setMsg] = useState("");
  const save = async ()=>{ try{ await api.put("/api/me",f); setMsg("Saved."); refresh(); }catch(e){setMsg(e.message);} };
  return (
    <div className="grid" style={{maxWidth:640,margin:"0 auto"}}>
      <div className="card"><div className="kicker">Profile</div><h3 className="serif">About you</h3>
        <label>Name</label><input value={f.name} onChange={e=>setF({...f,name:e.target.value})}/>
        <label>Stream</label><select value={f.stream} onChange={e=>setF({...f,stream:e.target.value})}>{Object.keys(streams).map(s=><option key={s}>{s}</option>)}</select>
        <label>Class</label><select value={f.student_class} onChange={e=>setF({...f,student_class:e.target.value})}><option value="11">Class 11</option><option value="12">Class 12</option></select>
        <div style={{height:8}}/><button className="btn" onClick={save}>Save changes</button> <span className="muted">{msg}</span>
      </div>
      <div className="card"><div className="kicker">The numbers</div><h3 className="serif">Your record</h3>
        <p>{user.tier_name} (Tier {user.current_tier}) · {user.solved} solved · {user.accuracy}% accurate · {user.avg_time}s a question on average · {user.reward_points} pts · rank #{user.rank||"—"} in your stream.</p>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);

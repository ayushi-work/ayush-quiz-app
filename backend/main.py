import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import os

from .database import get_db, engine, Base
from .models import User, Question, Attempt, Mistake
from .auth import hash_password, verify_password, create_token, decode_token
from .adaptive import (decide_next_difficulty, tier_update, reward_for, TIERS,
                       accuracy_score, performance_score, level_for_performance, REWARDS)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AdaptiveAI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def ensure_seeded():
    """Create tables + seed demo content when the DB is empty.

    Needed on serverless hosts (e.g. Vercel) where the sqlite file in /tmp
    starts out empty on a fresh instance. Locally this is a no-op.
    """
    Base.metadata.create_all(bind=engine)
    try:
        from .seed import seed
        db = next(get_db())
        try:
            from .models import Question as _Q
            if db.query(_Q).count() == 0:
                seed()
        finally:
            db.close()
    except Exception:
        pass

STREAMS = {
    "Science Medical": ["Physics", "Chemistry", "Biology"],
    "Science Non-Medical": ["Physics", "Chemistry", "Mathematics", "Computer Science"],
    "Commerce": ["Accountancy", "Business Studies", "Economics", "Mathematics"],
    "Humanities": ["History", "Political Science", "Geography", "Sociology", "Psychology"],
}
TIER_NAMES = {t["id"]: t["name"] for t in TIERS}

# ---------- helpers ----------

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter_by(id=user_id).first()


def current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Login required")
    data = decode_token(authorization.split(" ", 1)[1])
    if not data:
        raise HTTPException(401, "Session expired. Please sign in again.")
    user = get_user(db, int(data["sub"]))
    if not user:
        raise HTTPException(401, "User not found")
    return user


def optional_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    try:
        return current_user(authorization, db)
    except Exception:
        return None


def q_to_dict(q: Question, hide_answer=True):
    d = {"id": q.id, "question": q.question, "options": json.loads(q.options),
         "subject": q.subject, "stream": q.stream, "topic": q.topic,
         "difficulty": q.difficulty, "expected_time": q.expected_time,
         "explanation": q.explanation, "hint": q.hint or ""}
    if not hide_answer:
        d["answer"] = q.answer
    return d


def pick_next_question(db: Session, subject: str, stream: str, difficulties: List[str],
                       exclude_ids: List[int], weak_topics: List[str] = []):
    """Select next question: prefer target difficulties, weak topics, unseen."""
    query = db.query(Question).filter(Question.subject == subject)
    # prefer stream but fall back to any stream for that subject
    stream_qs = query.filter(Question.stream == stream).all() if stream else []
    pool = stream_qs or query.all()
    pool = [q for q in pool if q.id not in set(exclude_ids or [])]
    if not pool:
        # allow repeats if exhausted
        pool = stream_qs or query.all()
    if not pool:
        return None
    # 1) filter to target difficulties
    targeted = [q for q in pool if q.difficulty in difficulties]
    candidates = targeted or pool
    # 2) prefer weak topics
    if weak_topics:
        weak = [q for q in candidates if q.topic in weak_topics]
        if weak:
            candidates = weak
    return random.choice(candidates)


def baseline_question(db: Session, subject: str, stream: str):
    """Same starting question for every user: first medium question of subject (deterministic)."""
    query = db.query(Question).filter(Question.subject == subject)
    q = query.filter(Question.difficulty == "medium").order_by(Question.id).first()
    if not q:
        q = query.order_by(Question.id).first()
    return q


def user_stats(db: Session, user: User):
    attempts = db.query(Attempt).filter_by(user_id=user.id).order_by(Attempt.timestamp).all()
    total = len(attempts)
    correct = sum(1 for a in attempts if a.correct)
    acc = round(correct / total * 100, 1) if total else 0.0
    avg_time = round(sum(a.response_time for a in attempts) / total, 1) if total else 0.0
    # per subject / topic
    subj = {}
    topic = {}
    for a in attempts:
        s = subj.setdefault(a.subject or "General", {"total": 0, "correct": 0})
        s["total"] += 1
        s["correct"] += 1 if a.correct else 0
        t = topic.setdefault(a.topic or "General", {"total": 0, "correct": 0})
        t["total"] += 1
        t["correct"] += 1 if a.correct else 0
    subj_pct = {k: round(v["correct"] / v["total"] * 100, 1) for k, v in subj.items()}
    topic_pct = {k: round(v["correct"] / v["total"] * 100, 1) for k, v in topic.items()}
    weak = sorted([(k, v) for k, v in topic_pct.items() if v < 70], key=lambda x: x[1])[:5]
    strong = sorted([(k, v) for k, v in topic_pct.items() if v >= 70], key=lambda x: -x[1])[:5]
    # accuracy over time (last 20, bucketed by 4)
    recent = attempts[-20:]
    trend = []
    for i in range(0, len(recent), 4):
        chunk = recent[i:i + 4]
        trend.append(round(sum(1 for a in chunk if a.correct) / len(chunk) * 100, 1))
    # streak
    streak = 0
    for a in reversed(attempts):
        if a.correct:
            streak += 1
        else:
            break
    return {"total": total, "correct": correct, "accuracy": acc, "avg_time": avg_time,
            "subjects": subj_pct, "topics": topic_pct, "weak": weak, "strong": strong,
            "trend": trend, "streak": streak}


def stream_rank(db: Session, user: User):
    if not user.stream:
        return None
    users = db.query(User).filter(User.stream == user.stream).all()
    scored = []
    for u in users:
        c = db.query(Attempt).filter_by(user_id=u.id, correct=True).count()
        scored.append((u.id, c, u.reward_points))
    scored.sort(key=lambda x: (-x[1], -x[2]))
    for i, (uid, _, _) in enumerate(scored, 1):
        if uid == user.id:
            return i
    return None


def recommendations(db: Session, user: User):
    st = user_stats(db, user)
    recs = []
    for topic, pct in st["weak"]:
        # find subject for topic
        q = db.query(Question).filter_by(topic=topic).first()
        subj = q.subject if q else "General"
        recs.append({"type": "practice", "title": f"{subj} — {topic}",
                     "reason": f"Your accuracy in {topic} is {pct}%, below your overall {st['accuracy']}%.",
                     "cta": "Start Practice", "subject": subj, "topic": topic})
        if len(recs) >= 3:
            break
    if st["accuracy"] >= 75 and st["total"] >= 5:
        best = max(st["subjects"].items(), key=lambda x: x[1], default=(None, 0))
        if best[0]:
            recs.append({"type": "challenge", "title": f"Advanced {best[0]} Challenge",
                         "reason": f"You're performing well in {best[0]} ({best[1]}%). Try harder questions.",
                         "cta": "Take Challenge", "subject": best[0], "topic": ""})
    if not recs:
        recs.append({"type": "practice", "title": "Take your first quiz",
                     "reason": "Answer a few questions so the AI can personalise your path.",
                     "cta": "Start Quiz", "subject": "", "topic": ""})
    return recs

# ---------- schemas ----------

class Signup(BaseModel):
    name: str
    email: str
    password: str
    stream: str = ""
    student_class: str = "12"

class Login(BaseModel):
    email: str
    password: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    stream: Optional[str] = None
    student_class: Optional[str] = None

class QuizStart(BaseModel):
    subject: str
    stream: Optional[str] = None
    num_questions: int = 10

class QuizAnswer(BaseModel):
    quiz_id: str
    question_id: int
    selected: int
    response_time: float

class PowerupUse(BaseModel):
    quiz_id: str
    question_id: int
    kind: str  # fifty, time, hint, second_chance

class QuestionIn(BaseModel):
    question: str
    options: List[str]
    answer: int
    subject: str
    stream: str
    topic: str = ""
    difficulty: str = "medium"
    expected_time: int = 20
    explanation: str = ""
    hint: str = ""

class ExplainIn(BaseModel):
    question_id: int
    selected: Optional[int] = None

# ---------- auth ----------

@app.post("/api/signup")
def signup(body: Signup, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=body.email.lower().strip()).first():
        raise HTTPException(400, "Email already registered. Please sign in.")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    u = User(name=body.name.strip(), email=body.email.lower().strip(),
             password_hash=hash_password(body.password),
             stream=body.stream, student_class=body.student_class)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"token": create_token(u.id), "user": public_user(db, u)}


@app.post("/api/login")
def login(body: Login, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=body.email.lower().strip()).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    return {"token": create_token(u.id), "user": public_user(db, u)}


def public_user(db: Session, u: User):
    st = user_stats(db, u)
    return {"id": u.id, "name": u.name, "email": u.email, "stream": u.stream,
            "student_class": u.student_class, "reward_points": u.reward_points,
            "current_tier": u.current_tier, "tier_progress": u.tier_progress,
            "tier_name": TIER_NAMES.get(u.current_tier, "Rookie"),
            "is_admin": u.is_admin, "accuracy": st["accuracy"], "avg_time": st["avg_time"],
            "solved": st["total"], "correct": st["correct"], "rank": stream_rank(db, u)}


@app.get("/api/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return public_user(db, user)


@app.put("/api/me")
def update_me(body: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.name is not None:
        user.name = body.name
    if body.stream is not None:
        user.stream = body.stream
    if body.student_class is not None:
        user.student_class = body.student_class
    db.commit()
    return public_user(db, user)


@app.get("/api/streams")
def streams():
    return STREAMS

# ---------- quiz engine ----------

@app.post("/api/quiz/start")
def quiz_start(body: QuizStart, user: User = Depends(current_user), db: Session = Depends(get_db)):
    stream = body.stream or user.stream or "Science Non-Medical"
    q = baseline_question(db, body.subject, stream)
    if not q:
        raise HTTPException(404, f"No questions found for {body.subject}.")
    quiz_id = uuid.uuid4().hex[:12]
    return {"quiz_id": quiz_id, "total": body.num_questions, "subject": body.subject,
            "stream": stream, "question": q_to_dict(q),
            "starting_note": "Everyone starts from this same baseline question. Next questions adapt to YOU.",
            "tier": {"tier": user.current_tier, "name": TIER_NAMES[user.current_tier], "progress": user.tier_progress},
            "rewards": user.reward_points}


@app.post("/api/quiz/answer")
def quiz_answer(body: QuizAnswer, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Question).filter_by(id=body.question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")
    correct = (body.selected == q.answer)
    # history before this answer (rolling window uses previous + current)
    prior = db.query(Attempt).filter_by(user_id=user.id).order_by(Attempt.timestamp).all()
    hist_flags = [a.correct for a in prior[-4:]] + [correct]  # last 5 incl current
    decision = decide_next_difficulty(hist_flags, body.response_time, q.expected_time)
    # streak (consecutive correct incl current)
    streak = 1 if correct else 0
    for a in reversed(prior):
        if correct and a.correct:
            streak += 1
        else:
            break
    reward, breakdown = reward_for(correct, q.difficulty, body.response_time, q.expected_time, streak)
    # tier
    new_tier, new_prog, tier_note = tier_update(user.current_tier, user.tier_progress or 0.0,
                                                correct, body.response_time, q.expected_time)
    user.current_tier = new_tier
    user.tier_progress = new_prog
    user.reward_points = (user.reward_points or 0) + reward
    # persist
    att = Attempt(user_id=user.id, quiz_id=body.quiz_id, question_id=q.id,
                  selected_answer=body.selected, correct=correct,
                  response_time=body.response_time, difficulty=q.difficulty,
                  subject=q.subject, topic=q.topic, reward_earned=reward)
    db.add(att)
    if not correct:
        if not db.query(Mistake).filter_by(user_id=user.id, question_id=q.id, understood=False).first():
            db.add(Mistake(user_id=user.id, question_id=q.id, selected_answer=body.selected))
    db.commit()
    # next question
    st = user_stats(db, user)
    weak_topics = [t for t, _ in st["weak"]]
    attempted_ids = [a.question_id for a in prior] + [q.id]
    # also exclude ids in this quiz
    quiz_attempted = [a.question_id for a in db.query(Attempt).filter_by(user_id=user.id, quiz_id=body.quiz_id).all()]
    exclude = list(set(attempted_ids + quiz_attempted))
    nxt = pick_next_question(db, q.subject, user.stream or q.stream, decision["allowed"], exclude, weak_topics)
    overall_acc = st["accuracy"]
    feedback = {
        "correct": correct,
        "correct_answer": q.answer,
        "correct_text": json.loads(q.options)[q.answer],
        "explanation": q.explanation,
        "reward": reward, "breakdown": breakdown, "streak": streak if correct else 0,
        "performance": decision["performance"], "accuracy_score": decision["accuracy_score"],
        "speed_score": decision["speed_score"], "next_difficulty": decision["next_difficulty"],
        "band": decision["band"], "ai_note": decision["explanation"], "tier_note": tier_note,
        "tier": {"tier": new_tier, "name": TIER_NAMES[new_tier], "progress": new_prog},
        "total_rewards": user.reward_points,
        "overall_accuracy": overall_acc,
    }
    out = {"feedback": feedback, "next_question": q_to_dict(nxt) if nxt else None}
    return out


POWERUP_COST = {"fifty": 40, "time": 30, "hint": 50, "second_chance": 70}


@app.post("/api/quiz/powerup")
def use_powerup(body: PowerupUse, user: User = Depends(current_user), db: Session = Depends(get_db)):
    cost = POWERUP_COST.get(body.kind, 0)
    if (user.reward_points or 0) < cost:
        raise HTTPException(400, f"Not enough points. {body.kind} costs {cost}.")
    q = db.query(Question).filter_by(id=body.question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")
    # limit: max 2 powerups per quiz per kind (checked via attempts? simplified: allow, client enforces per-quiz limit of 1 each for fifty/hint/second_chance)
    user.reward_points -= cost
    db.commit()
    opts = json.loads(q.options)
    if body.kind == "fifty":
        wrong = [i for i in range(len(opts)) if i != q.answer]
        remove = random.sample(wrong, min(2, len(wrong)))
        return {"ok": True, "remove": remove, "balance": user.reward_points}
    if body.kind == "hint":
        return {"ok": True, "hint": q.hint or q.explanation, "balance": user.reward_points}
    if body.kind == "time":
        return {"ok": True, "extra_seconds": 15, "balance": user.reward_points}
    if body.kind == "second_chance":
        return {"ok": True, "balance": user.reward_points, "note": "Retry allowed once."}
    raise HTTPException(400, "Unknown powerup")

# ---------- dashboard / history / review ----------

@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    st = user_stats(db, user)
    recent_rows = db.query(Attempt).filter_by(user_id=user.id).order_by(desc(Attempt.timestamp)).limit(60).all()
    # group by quiz_id
    quizzes = {}
    for a in recent_rows:
        qu = quizzes.setdefault(a.quiz_id or f"solo-{a.id}", {"quiz_id": a.quiz_id, "subject": a.subject,
                                                              "total": 0, "correct": 0, "date": str(a.timestamp), "tier": user.current_tier})
        qu["total"] += 1
        qu["correct"] += 1 if a.correct else 0
    recent = [{"quiz_id": k, "subject": v["subject"], "score": f"{v['correct']}/{v['total']}",
               "accuracy": round(v["correct"] / v["total"] * 100, 1) if v["total"] else 0,
               "date": v["date"][:16]} for k, v in list(quizzes.items())[:8]]
    return {"user": public_user(db, user), "stats": st, "recent": recent,
            "recommendations": recommendations(db, user)}


@app.get("/api/history")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Attempt).filter_by(user_id=user.id).order_by(desc(Attempt.timestamp)).limit(200).all()
    out = []
    for a in rows:
        q = db.query(Question).filter_by(id=a.question_id).first()
        out.append({"id": a.id, "quiz_id": a.quiz_id, "question": q.question if q else "",
                    "options": json.loads(q.options) if q else [], "selected": a.selected_answer,
                    "answer": q.answer if q else -1, "correct": a.correct,
                    "response_time": a.response_time, "difficulty": a.difficulty,
                    "subject": a.subject, "topic": a.topic, "reward": a.reward_earned,
                    "date": str(a.timestamp)})
    return out


@app.get("/api/mistakes")
def mistakes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Mistake).filter_by(user_id=user.id).order_by(desc(Mistake.timestamp)).all()
    out = []
    for m in rows:
        q = db.query(Question).filter_by(id=m.question_id).first()
        if not q:
            continue
        opts = json.loads(q.options)
        # improvement tip based on topic frequency
        same_topic_wrong = db.query(Attempt).filter_by(user_id=user.id, topic=q.topic, correct=False).count()
        tip = (f"You have {same_topic_wrong} mistake(s) in {q.topic}. "
               f"Revise the core rule and practice 5 similar {q.topic} problems.")
        out.append({"mistake_id": m.id, "question_id": q.id, "question": q.question,
                    "options": opts, "your_answer": opts[m.selected_answer] if 0 <= m.selected_answer < len(opts) else "—",
                    "correct_answer": opts[q.answer], "explanation": q.explanation,
                    "topic": q.topic, "subject": q.subject, "difficulty": q.difficulty,
                    "tip": tip, "understood": m.understood})
    return out


@app.post("/api/mistakes/{mid}/understood")
def mark_understood(mid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = db.query(Mistake).filter_by(id=mid, user_id=user.id).first()
    if not m:
        raise HTTPException(404, "Not found")
    m.understood = True
    db.commit()
    return {"ok": True}


@app.post("/api/explain")
def explain(body: ExplainIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Student-friendly explanation. Works offline; LLM-ready hook via EXPLAIN_API env."""
    q = db.query(Question).filter_by(id=body.question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")
    opts = json.loads(q.options)
    llm_url = os.environ.get("EXPLAIN_API", "")
    # Optional LLM passthrough could go here; default template explanation:
    text = (f"Why: {q.explanation} The correct option is '{opts[q.answer]}'. "
            f"Key idea ({q.topic}): focus on the underlying rule, then eliminate the other options one by one.")
    return {"explanation": text}


@app.get("/api/leaderboard")
def leaderboard(stream: str = "", subject: str = "", period: str = "overall",
                db: Session = Depends(get_db)):
    since = None
    if period == "weekly":
        since = datetime.utcnow() - timedelta(days=7)
    elif period == "monthly":
        since = datetime.utcnow() - timedelta(days=30)
    users = db.query(User).all()
    if stream:
        users = [u for u in users if u.stream == stream]
    rows = []
    for u in users:
        q = db.query(Attempt).filter_by(user_id=u.id)
        if since:
            q = q.filter(Attempt.timestamp >= since)
        if subject:
            q = q.filter(Attempt.subject == subject)
        atts = q.all()
        correct = sum(1 for a in atts if a.correct)
        if period == "overall" and not atts and (u.reward_points or 0) == 0:
            continue
        rows.append({"name": u.name, "stream": u.stream, "correct": correct,
                     "tier": TIER_NAMES.get(u.current_tier, "Rookie"),
                     "tier_id": u.current_tier, "points": u.reward_points or 0})
    rows.sort(key=lambda r: (-r["correct"], -r["tier_id"], -r["points"]))
    for i, r in enumerate(rows[:50], 1):
        r["rank"] = i
    return rows[:50]

# ---------- admin ----------

def require_admin(user: User):
    if not user.is_admin:
        raise HTTPException(403, "Teacher/admin access required.")


@app.get("/api/admin/questions")
def admin_list(subject: str = "", stream: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_admin(user)
    q = db.query(Question)
    if subject:
        q = q.filter_by(subject=subject)
    if stream:
        q = q.filter_by(stream=stream)
    return [q_to_dict(x, hide_answer=False) for x in q.order_by(Question.id).limit(500).all()]


@app.post("/api/admin/questions")
def admin_create(body: QuestionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_admin(user)
    qq = Question(question=body.question, options=json.dumps(body.options), answer=body.answer,
                  subject=body.subject, stream=body.stream, topic=body.topic,
                  difficulty=body.difficulty, expected_time=body.expected_time,
                  explanation=body.explanation, hint=body.hint)
    db.add(qq)
    db.commit()
    db.refresh(qq)
    return q_to_dict(qq, hide_answer=False)


@app.put("/api/admin/questions/{qid}")
def admin_update(qid: int, body: QuestionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_admin(user)
    qq = db.query(Question).filter_by(id=qid).first()
    if not qq:
        raise HTTPException(404, "Not found")
    for k in ["question", "subject", "stream", "topic", "difficulty", "explanation", "hint"]:
        setattr(qq, k, getattr(body, k))
    qq.options = json.dumps(body.options)
    qq.answer = body.answer
    qq.expected_time = body.expected_time
    db.commit()
    return q_to_dict(qq, hide_answer=False)


@app.delete("/api/admin/questions/{qid}")
def admin_delete(qid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_admin(user)
    qq = db.query(Question).filter_by(id=qid).first()
    if not qq:
        raise HTTPException(404, "Not found")
    db.delete(qq)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/overview")
def admin_overview(user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_admin(user)
    total_users = db.query(User).count()
    total_q = db.query(Question).count()
    total_att = db.query(Attempt).count()
    acc = 0.0
    if total_att:
        acc = round(db.query(Attempt).filter_by(correct=True).count() / total_att * 100, 1)
    # commonly incorrect
    rows = db.query(Attempt.question_id, func.count(Attempt.id).label("n"),
                    func.sum(func.cast(Attempt.correct, Integer) if False else 1)).group_by(Attempt.question_id).limit(200).all() if False else None
    # simpler: per-question wrong rate
    per_q = {}
    for a in db.query(Attempt).all():
        d = per_q.setdefault(a.question_id, {"total": 0, "wrong": 0})
        d["total"] += 1
        if not a.correct:
            d["wrong"] += 1
    worst = sorted(per_q.items(), key=lambda x: -(x[1]["wrong"] / x[1]["total"]) if x[1]["total"] else 0)[:5]
    worst_out = []
    for qid, d in worst:
        qq = db.query(Question).filter_by(id=qid).first()
        if qq:
            worst_out.append({"id": qid, "question": qq.question[:90], "subject": qq.subject,
                              "wrong_rate": round(d["wrong"] / d["total"] * 100, 1), "attempts": d["total"]})
    return {"users": total_users, "questions": total_q, "attempts": total_att,
            "accuracy": acc, "commonly_wrong": worst_out}

# ---------- demo simulation ----------

@app.post("/api/demo/simulate")
def demo_simulate(db: Session = Depends(get_db)):
    """Simulate two students from the SAME baseline to show divergence. No login needed."""
    subjects = ["Mathematics"]
    subj = "Mathematics"
    base = baseline_question(db, subj, "Science Non-Medical")
    if not base:
        raise HTTPException(404, "No questions seeded yet")

    def run(profile: str):
        path = []
        hist: List[bool] = []
        tier, prog = 1, 0.0
        exclude = [base.id]
        # scripted answers: A fast+accurate, B slow+inconsistent
        script = ([(True, 0.4)] * 6) if profile == "fast" else \
                 [(False, 1.8), (True, 1.6), (True, 1.4), (False, 1.9), (True, 1.2), (True, 1.5)]
        current = base
        for i, (corr, speed_mult) in enumerate(script):
            rt = round(current.expected_time * speed_mult, 1)
            hist.append(corr)
            dec = decide_next_difficulty(hist[-5:], rt, current.expected_time)
            tier, prog, tnote = tier_update(tier, prog, corr, rt, current.expected_time)
            path.append({"q": i + 1, "question": current.question[:70], "difficulty": current.difficulty,
                         "correct": corr, "response_time": rt, "performance": dec["performance"],
                         "next_difficulty": dec["next_difficulty"], "tier": tier,
                         "ai_note": dec["explanation"]})
            nxt = pick_next_question(db, subj, "Science Non-Medical", dec["allowed"], exclude)
            if not nxt:
                break
            exclude.append(nxt.id)
            current = nxt
        return {"baseline": base.question, "path": path,
                "final_tier": tier, "accuracy": round(sum(hist) / len(hist) * 100, 1)}

    return {"studentA": {"label": "Student A — Fast & Accurate", **run("fast")},
            "studentB": {"label": "Student B — Slow & Inconsistent", **run("slow")}}

# ---------- serve frontend ----------

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.isdir(FRONTEND_DIR):
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        candidate = os.path.join(FRONTEND_DIR, full_path)
        if full_path.startswith("api/"):
            raise HTTPException(404, "API route not found")
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return {"message": "AdaptiveAI API running. Frontend not built yet."}

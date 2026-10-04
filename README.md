# AdaptiveAI — AI-Powered Adaptive Quiz & Learning Platform

Class 12 AI capstone: every student starts from the **same baseline question**;
difficulty then adapts via `performance = accuracy×0.7 + speed×0.3` over a rolling 5-question window.

## Run
```bash
bash run.sh
# open http://127.0.0.1:8000
```
Or manually:
```bash
pip install -r backend/requirements.txt
python -m backend.seed
uvicorn backend.main:app --reload --port 8000
```

Demo logins (created by seed):
- Student: `ayushi@demo.school` / `demo1234`
- Teacher: `admin@adaptiveai.school` / `admin123`

## Stack
- Frontend: React 18 (CDN) + HTML/CSS/JS, dark/light mode, responsive
- Backend: Python FastAPI, explainable adaptive engine (`backend/adaptive.py`)
- DB: SQLite (`adaptiveai.db`), SQLAlchemy models — swap `DATABASE_URL` to Postgres later

## Key flows
- `POST /api/quiz/start` → deterministic baseline (first medium question of subject)
- `POST /api/quiz/answer` → scores, tier/reward update, picks next difficulty + weak-topic question
- `POST /api/demo/simulate` → Student A (fast/accurate) vs B (slow/inconsistent) divergence
- Teacher panel: CRUD questions, overview, commonly-wrong questions

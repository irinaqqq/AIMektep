
# Backend (FastAPI) — Personalized Learning

Minimal backend for a personalized learning flow: **material → summary → quiz → submit → overview → light reviews**.

PostgreSQL storage, JWT auth.

---

## Stack

- **FastAPI**, **Uvicorn**
- **PostgreSQL** (SQLAlchemy + Alembic)
- **JWT** auth
- **OpenAI API** (strict JSON validation for quiz gen)

## Requirements

- Python 3.11+
- PostgreSQL 16+ (or Docker)
- OpenAI API key

## Environment

Create `.env`:

```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/learn
OPENAI_API_KEY=sk-xxxxx
JWT_SECRET=dev-secret
JWT_EXPIRES_HOURS=24
RATE_LIMIT_PER_MIN=5
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Docs: `http://localhost:8000/docs`

## API Surface (v1)

- **Auth**: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- **Materials**: `POST /materials`, `GET /materials`, `GET /materials/{id}?include=text,summary,quiz`, `DELETE /materials/{id}`
- **Generation**:
  - `POST /generate/summary?force=` — create/refresh summary
  - `POST /generate/quiz?force=` — create/refresh quiz (strict JSON from LLM)
- **Quiz**:
  - `GET /materials/{id}/quiz` — public quiz (no answers/hints)
  - `POST /quizzes/{quiz_id}/submit` — scoring + calibration + review cards
  - `POST /quizzes/{quiz_id}/questions/{question_id}/hint` — hint level 1|2
- **Review**: `GET /review/due`, `POST /review/{id}/grade`
- **Overview**: `GET /me/overview` (materials, completed quizzes, avg best score)

## Data Model (one-liners)

- **User**: auth + `preferred_lang`.
- **Material**: user-owned text.
- **Summary**: 1:1 with material.
- **Quiz**: 1:1 with material; `question_count` kept in sync.
- **QuizQuestion**: MCQ with `difficulty`, `tags`(≥1), `bloom`, up to 2 `hints`, and `rationales` (server-only).
- **QuizSubmission**: attempt result; stores answers, confidence, time, hints used; Brier calibration.
- **UserSkillMastery**: per-tag mastery (0..1), EMA-updated on submit.
- **ReviewCard**: light spaced-repetition cards from wrong answers.

## Core Rules

- **Ownership** only; others → 403.
- **No leakage**: never return `correct_index`, raw `hints` or `rationales` in public quiz JSON. Use `/hint` and `/submit`.
- **Force**: `summary` → overwrite; `quiz` → recreate quiz+questions.
- **Attempts**: multiple; overview uses **best per quiz**.
- **Scoring**: `score` = correct count; **penalty** `+0.25` per unique hint level → `score_weighted = max(0, score - penalty_total)`.
- **Calibration**: Brier with confidence→p mapping `low=0.55`, `med=0.70`, `high=0.85`.
- **Review**: intervals — `again +8h`, `good +2d`, `easy +5d`; `ease` moves 1..3.
- **Limits**: material text ~200–20000 chars; generation rate-limit 5/min/user.

## Example (curl)

```bash
# register & login
http :8000/v1/auth/register email=a@b.c password=secret123
http :8000/v1/auth/login    email=a@b.c password=secret123

# create material
http POST :8000/v1/materials "Authorization:Bearer $JWT" title="Sorting" text="..."
# generate summary & quiz
http POST :8000/v1/generate/summary "Authorization:Bearer $JWT" material_id:=10 lang=ru
http POST :8000/v1/generate/quiz "Authorization:Bearer $JWT" material_id:=10 num_questions:=5 target=balanced lang=ru
# submit
http POST :8000/v1/quizzes/34/submit "Authorization:Bearer $JWT" answers:='[{"question_id":1001,"answer_index":2,"confidence":"high","hints_used":[1]}]'
# hint
http POST :8000/v1/quizzes/34/questions/1001/hint "Authorization:Bearer $JWT" level:=1
# review
http :8000/v1/review/due "Authorization:Bearer $JWT"
http POST :8000/v1/review/123/grade "Authorization:Bearer $JWT" grade=good
```

## Errors

Always JSON `{ "detail": "..." }`.
Notables: `404 quiz_not_found`, `413 text_too_long`, `422 llm_invalid_json` (after one retry).

## Definition of Done

- JWT-protected `/v1` endpoints operational.
- Summary & Quiz generate with validation + retry.
- Submit computes `score`, `score_weighted`, `brier`; updates mastery; creates review cards; returns explanations.
- Review due/grade uses indexed queries.
- Overview returns counts and **avg best score per quiz**.

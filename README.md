# Resume Match Advisor for Commerce Students

A **free, non-commercial, privacy-conscious** tool that helps undergraduate commerce/business
students answer one question:

> "How well does my resume match this job, what proof do I already have, what am I missing,
> and how can I improve my application?"

Students paste a resume and a job description (plus an optional company name and target
discipline) and get an explainable match report: an overall score, a category breakdown, a
requirement-by-requirement evidence map, missing skills, and specific student-relevant
improvement suggestions.

## What this project is

- A **student-support advisor** for business/commerce students: marketing, finance, accounting,
  business analytics, BTM/MIS, consulting, operations, HR, and sales/RevOps roles.
- **Deterministic and explainable**: the core scanner is pure Python logic driven by static
  JSON knowledge packs. Every point in the score is traceable to a stated reason.
- **Commerce-specific**: it recognizes that student clubs, case competitions, class projects,
  part-time jobs, and internships are real business evidence, and tells students how to make
  that evidence explicit.

## What this project is not

- ❌ Not a startup, not a SaaS, not monetized — no accounts, payments, or subscriptions.
- ❌ Not an "ATS beater" — it makes no claims about passing any screening system.
- ❌ Not an AI wrapper — no AI API is required for the base scanner (optional AI-assisted
  features could be added later, but the product must always work without them).
- ❌ Not for software engineering resumes.

## Privacy principles

- **Resumes are never stored.** Analysis happens in memory; nothing is written to disk or a
  database, and nothing is logged.
- No user accounts, no tracking, no third-party analytics.
- The only optional external call is a lookup of the **company name** (not resume content)
  against Wikipedia's free public summary API — disable it entirely with `COMPANY_LOOKUP=off`.

## Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+, Pydantic v2 |
| Knowledge | Static JSON packs in `knowledge_packs/` |
| Storage | None (by design) |

```
backend/            FastAPI app: parsers, classifier, matcher, scoring, report
knowledge_packs/    9 discipline packs + common.json (aliases, translations)
frontend/           Next.js app: landing page, scanner, results UI
examples/           Sample resumes, job descriptions, expected output
```

## Local setup

### Backend (port 8000)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Check it: `curl localhost:8000/health` → `{"status":"ok"}`.
Interactive API docs at `http://localhost:8000/docs`.

Environment variables (all optional):

- `ALLOWED_ORIGINS` — comma-separated CORS origins (default `*`).
- `COMPANY_LOOKUP=off` — disable the Wikipedia company lookup (offline fallback card is used).
- `KNOWLEDGE_PACKS_DIR` — override the knowledge packs location.

### Frontend (port 3000)

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` if the backend isn't on `http://localhost:8000`
(e.g. in `frontend/.env.local`).

## Testing

```bash
cd backend
.venv/bin/python -m pytest
```

The suite covers discipline classification, resume/JD parsing, evidence-map quality,
score breakdown integrity, missing-skill detection, student-experience translation, and
robustness on short/messy inputs. Tests never touch the network.

## Deployment (free tiers)

**Frontend → Vercel (Hobby)**: import the repo, set the root directory to `frontend/`, and add
`NEXT_PUBLIC_API_URL` pointing at your backend URL.

**Backend → Render (free web service)**:
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Env var: `ALLOWED_ORIGINS=https://your-frontend.vercel.app`
- Note: Render copies only the root directory, so either move `knowledge_packs/` into the
  service or set the root to the repo and use
  `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`.
- Free-tier services sleep when idle; the first request after a while takes ~30s to wake.

## Future improvements

- Optional AI-assisted bullet rewriting (opt-in, clearly labeled, never required).
- Resume file upload (PDF/DOCX → text) with the same no-storage guarantee.
- Richer company cards from additional open data sources.
- More disciplines (real estate, entrepreneurship, international business).
- Knowledge-pack contributions from career centres and student societies.

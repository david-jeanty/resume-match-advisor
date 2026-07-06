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
  database, and nothing is logged. The optional context fields (university, program,
  location, courses) are processed the same way — never stored.
- No user accounts, no tracking, no third-party analytics.
- The only optional external call is a lookup of the **company name** (not resume content)
  against Wikipedia's free public summary API — disable it entirely with `COMPANY_LOOKUP=off`.
- **No scraping, ever**: no LinkedIn, no job boards, and no private co-op portal content.
  University/location packs are built only from official public pages.

## Optional university / program / location context

Students can optionally provide a university, program, location, and completed courses
(e.g. `ADM 1370, ADM 2372`). The first supported university pack is **uOttawa / Telfer**
(`university_packs/uottawa_telfer.json`); the first location packs are **Ottawa/Kanata**
and **Toronto/GTA**. Everything still works with these blank, and a generic fallback keeps
the tool useful for any commerce student.

What context does — and deliberately doesn't do:

- It **improves feedback**: translates ADM courses, Telfer clubs (TCCT, BTA, TMA, TFS, …),
  case competitions (TICC, JDC), co-op, and bilingual context into evidence advice, and adds
  a location-specific application angle (e.g. Kanata B2B tech, NCR public sector).
- It **barely moves the score**: a course code or club name alone is weak evidence at most.
  Course + project/tool = moderate; course + concrete project + tool + outcome = strong.
  Club membership alone is weak; leadership is moderate; leadership with metrics/stakeholders
  is strong. Real work/internship/project evidence always outweighs course-only evidence.
- It is **never used to rank students or compare schools**.

### Source hierarchy for university packs

1. **Official uOttawa/Telfer pages** are the only source of truth for course names,
   program structure, co-op facts, and official club lists.
2. **Public Telfer/AÉTSA club pages** may inform how clubs describe their activities.
3. **Reddit/forums** may only inform qualitative wording (how students phrase things),
   never facts. Facts that couldn't be verified are marked `to_verify` in
   `research_sources/uottawa_telfer_sources.json` and `verified: false` in the pack.

## Advisor engine (optional explanation layer)

After the deterministic scan is scored, an optional **advisor engine**
(`backend/app/advisor_engine/`) adds richer, student-friendly notes: false-gap detection
("you have adjacent validation evidence, but never say UAT — name it explicitly or keep
it as a gap"), genuine-gap explanations, positioning advice, experience translation,
and course/location/company cross-references.

Design rules:

- **The default provider is rule-based**: deterministic templates driven by the
  `adjacent_evidence` table in `knowledge_packs/common.json` plus the scan results.
  No AI, no network, no cost.
- **The advisor never changes the score.** It runs after scoring and only adds notes;
  a provider failure cannot break a scan.
- **LLM providers are opt-in stubs.** `optional_llm_provider.py` reserves slots for
  future local (Ollama) or API (Anthropic/OpenAI) providers, but they are disabled by
  default, make no calls, and raise with an explanation if selected. The base product
  must always work fully without them.
- Select a provider with `ADVISOR_PROVIDER` (`rule_based` default, `off` to disable).

### Updating university and location packs

- Add a new school: copy `university_packs/uottawa_telfer.json`, fill in `aliases`,
  `courses` (skills must use canonical terms from `knowledge_packs/`), `clubs`,
  `competitions`, and `coop_context`; record your sources in `research_sources/`.
- Add a new city: copy `location_packs/ottawa_kanata.json` and adjust `aliases`,
  `common_industries`, `positioning_advice`, and `role_angles`.
- Packs are loaded automatically from those directories — no code changes needed.

## Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+, Pydantic v2 |
| Knowledge | Static JSON packs in `knowledge_packs/` |
| Storage | None (by design) |

```
backend/            FastAPI app: parsers, classifier, matcher, scoring, context, report
knowledge_packs/    9 discipline packs + common.json (aliases, translations)
university_packs/   Optional university context (uottawa_telfer + generic fallback)
location_packs/     Optional location context (ottawa_kanata, toronto_gta, generic)
research_sources/   Source manifests + verification status for university packs
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
- `KNOWLEDGE_PACKS_DIR` / `UNIVERSITY_PACKS_DIR` / `LOCATION_PACKS_DIR` — override pack locations.
- `ADVISOR_PROVIDER` — advisor engine provider: `rule_based` (default, offline) or `off`.

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

Tested setup for sharing a private test link: backend on Render (free), frontend on
Vercel (Hobby). No accounts, no database, no resume storage — deployment doesn't change
the privacy model.

### 1. Backend → Render

The repo includes a `render.yaml` blueprint. In Render: **New → Blueprint**, point it at
your fork, and set `ALLOWED_ORIGINS` when prompted (you can fill in the real Vercel URL
after step 2 and redeploy).

Manual setup instead of the blueprint:

- **Root directory**: leave as the repo root (important — the knowledge/university/
  location packs live at the repo root).
- **Build command**: `pip install -r backend/requirements.txt`
- **Start command**: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- **Environment variables**:
  - `ALLOWED_ORIGINS=https://your-app.vercel.app` (comma-separate to add more origins,
    e.g. a Vercel preview URL; no trailing slashes needed)
  - `ADVISOR_PROVIDER=rule_based` (the free offline default; never set an LLM provider)
- Verify with `https://your-api.onrender.com/health` → `{"status":"ok"}`.

### 2. Frontend → Vercel

- **Import the repo**, set **Root Directory** to `frontend/` (Framework: Next.js,
  defaults are fine).
- **Environment variables**:
  - `NEXT_PUBLIC_API_BASE_URL=https://your-api.onrender.com` (your Render URL, no
    trailing slash)
  - `NEXT_PUBLIC_FEEDBACK_URL=https://forms.gle/...` (optional — powers the beta
    banner's "Leave feedback" button; otherwise edit the placeholder in
    `frontend/components/BetaBanner.tsx`)
- Deploy, then copy the production URL into the backend's `ALLOWED_ORIGINS` and
  redeploy the backend.

### 3. Before sending the link to testers

- Run one real scan on the deployed URL (paste a resume + posting) and confirm results render.
- Expect a slow first scan: **Render's free tier sleeps when idle** and takes ~30-60s to
  wake. Tell your testers this or warm it up with a `/health` request first.
- The UI shows a beta banner reminding testers that resumes are analyzed in memory,
  never stored, and that no AI service is used.

## Future improvements

- Optional AI-assisted bullet rewriting (opt-in, clearly labeled, never required).
- Resume file upload (PDF/DOCX → text) with the same no-storage guarantee.
- Richer company cards from additional open data sources.
- More disciplines (real estate, entrepreneurship, international business).
- Knowledge-pack contributions from career centres and student societies.

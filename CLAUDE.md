# CLAUDE.md — project instructions for AI coding sessions

## What this project is

A **free, non-commercial student-support tool**: a resume-to-job-description match advisor
for **undergraduate commerce/business students** (marketing, finance, accounting, business
analytics, BTM/MIS, consulting, operations, HR, sales/RevOps). It is not a startup, not a
SaaS, and must stay cheap/free to run.

## Hard constraints — do not violate without explicit user request

1. **No auth, no accounts, no payments, no subscriptions, no admin dashboards.**
2. **No resume storage.** Resumes and job descriptions are processed in memory only — never
   written to disk, a database, logs, or external services.
3. **No paid AI dependency for the core scanner.** The base analysis must always work with
   deterministic Python logic + the static JSON knowledge packs in `knowledge_packs/`.
   AI may only ever be an optional, clearly-labeled add-on.
4. **No fake ATS claims.** Student-facing language must never promise to "beat" or "pass"
   ATS systems. The tool gives honest, educational match feedback.
5. **No scraping** (LinkedIn, job boards, or anything legally/ethically questionable).
   The only permitted external data source is free/open APIs (currently Wikipedia summaries
   for company cards, and only the company *name* is sent).
6. **Keep it simple.** A student developer must be able to maintain this. No microservices,
   no complex infra, no unnecessary dependencies.

## University/location context rules (Phase 2)

- **Official sources only for facts.** Course names, program structure, co-op facts, and
  official club lists in `university_packs/` must come from official university pages,
  recorded in `research_sources/`. Reddit/forums may only inform qualitative wording
  (how students phrase experiences), never facts. **Never fabricate course details** —
  mark unverified entries `verified: false` / `to_verify` instead.
- **Never overvalue course-only evidence.** Course code/name alone = weak at most;
  course + project/tool = moderate; course + concrete project + tool + outcome = strong.
  Club membership alone = weak; leadership title = moderate; leadership with concrete
  tasks/metrics/stakeholders = strong. Work/internship/project evidence always outweighs
  course-only evidence. These caps are enforced in `context_engine.py` and
  `SKILL_STATUS_VALUE["context"]` — keep them.
- **Never use school or location context to judge students unfairly** — no ranking
  students, no comparing schools; location changes advice wording, not the score.
- **Keep generic fallbacks working** for non-uOttawa students
  (`university_packs/generic_commerce.json`, `location_packs/generic_canada.json`);
  the tool must work perfectly with all context fields blank.
- No private co-op portal content, login-only resources, or LinkedIn — ever.

## Product principles

- The differentiator is **commerce-specific evidence translation**: clubs, case competitions,
  class projects, part-time jobs, student ambassador roles, and internships are real business
  evidence. Feedback must translate them (e.g. club leadership → project coordination) and
  tell the student what to make explicit (stakeholders, timeline, scope, outcome, numbers).
- Scoring must stay **explainable**: whole numbers, stated weights (see
  `backend/app/scoring_engine.py`), and a plain-language explanation for every category.
  Evidence strengths are strong / moderate / weak / missing.
- Suggestions must be **specific and actionable** ("add a bullet under X naming the tool and
  the result"), never generic ("improve your resume").
- Only suggest adding things that may be true for the student — always caveat "if you did
  this work".

## Architecture map

- `backend/app/` — FastAPI. Pipeline: `resume_parser` + `jd_parser` → `discipline_classifier`
  → `matching_engine` (evidence map, student translation) → `scoring_engine` →
  `report_generator` → `/analyze`. `company_card` is Wikipedia-or-fallback and must never raise.
- `knowledge_packs/*.json` — 9 discipline packs + `common.json` (skill aliases,
  student-experience translations, action verbs, section headers, stopwords). Improving
  match quality usually means editing packs, not code.
- `frontend/` — Next.js 14 App Router + Tailwind. `/` landing, `/scan` form + results.
  `types/analysis.ts` mirrors `backend/app/models.py` — keep them in sync.

## Workflow

- Backend tests: `cd backend && .venv/bin/python -m pytest` (61+ tests; keep them green,
  and tests must never hit the network — `COMPANY_LOOKUP=off` is set in `conftest.py`).
- Frontend build check: `cd frontend && npm run build`.
- Sample inputs for manual testing live in `examples/`.

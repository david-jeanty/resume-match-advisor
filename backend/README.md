# Backend — Resume Match Advisor API

FastAPI service that performs the deterministic resume-to-job-description analysis.
See the repository root `README.md` for full setup and deployment docs.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

- `GET /health` — health check
- `POST /analyze` — full match report (see `app/models.py` for the schema)
- Interactive docs: `http://localhost:8000/docs`

## Pipeline

```
resume_text ─► resume_parser ─┐
                              ├─► discipline_classifier ─► matching_engine ─► scoring_engine ─► report_generator ─► AnalyzeResponse
jd_text ────► jd_parser ──────┘                                 (evidence map,                    (6 weighted,
                                                                 student translation)              explainable categories)
```

All matching is driven by the static packs in `../knowledge_packs/`. No AI, no storage,
no network calls except the optional company-name lookup (`COMPANY_LOOKUP=off` disables it).

## Tests

```bash
.venv/bin/python -m pytest
```

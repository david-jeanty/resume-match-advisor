"""Resume Match Advisor API — free, deterministic, no resume storage."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import AnalyzeRequest, AnalyzeResponse
from .report_generator import generate_report

app = FastAPI(
    title="Resume Match Advisor for Commerce Students",
    description=(
        "Deterministic resume-to-job-description match analysis for undergraduate "
        "commerce/business students. No AI required, no resume storage."
    ),
    version="0.1.0",
)

# Comma-separated origins, e.g. "https://yourapp.vercel.app,http://localhost:3000"
_origins = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return generate_report(request)

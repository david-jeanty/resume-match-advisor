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

# Comma-separated origins, e.g. "https://yourapp.vercel.app,http://localhost:3000".
# Defaults to "*" for easy local development; set it explicitly in deployment.
# Trailing slashes are stripped — a browser Origin header never has one, so
# "https://yourapp.vercel.app/" in the env var would otherwise never match.
_origins = [
    o.strip().rstrip("/")
    for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return generate_report(request)

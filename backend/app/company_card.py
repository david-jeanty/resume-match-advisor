"""Lightweight company context card.

Tries the free Wikipedia REST summary API (open data, no key, no scraping);
falls back to a clean deterministic card if the lookup is disabled, offline,
or finds nothing. Never raises — a card is always returned.
"""

import json
import os
import urllib.parse
import urllib.request

from .models import CompanyCard

LOOKUP_TIMEOUT_SECONDS = 4

INDUSTRY_HINTS = [
    ("bank", "Banking / Financial services"),
    ("financial services", "Financial services"),
    ("insurance", "Insurance"),
    ("retail", "Retail"),
    ("e-commerce", "E-commerce"),
    ("software", "Software / Technology"),
    ("technology", "Technology"),
    ("consulting", "Consulting / Professional services"),
    ("accounting", "Accounting / Professional services"),
    ("telecommunications", "Telecommunications"),
    ("airline", "Airlines / Travel"),
    ("pharmaceutical", "Pharmaceuticals / Healthcare"),
    ("healthcare", "Healthcare"),
    ("food", "Food & Beverage"),
    ("restaurant", "Food service"),
    ("logistics", "Logistics / Supply chain"),
    ("manufacturing", "Manufacturing"),
    ("energy", "Energy"),
    ("real estate", "Real estate"),
    ("media", "Media & Entertainment"),
    ("university", "Education"),
    ("nonprofit", "Non-profit"),
    ("grocery", "Grocery / Retail"),
]

PUBLIC_HINTS = ["publicly traded", "public company", "nyse", "nasdaq", "tsx", "listed on"]
PRIVATE_HINTS = ["privately held", "private company", "subsidiary"]


def _student_angle(company_name: str, discipline: str | None) -> str:
    focus = f"your {discipline.lower()} coursework and student experience" if discipline \
        else "your coursework and student experience"
    return (
        f"Before applying, spend 15 minutes on {company_name}'s site and recent "
        f"news: what they sell, who their customers are, and what's changing for "
        f"them right now. In your application, connect {focus} to that reality "
        "instead of speaking generically."
    )


def _resume_angle(company_name: str) -> str:
    return (
        f"Mirror the posting's own vocabulary where it's honest for you, and pick "
        f"the one or two experiences most relevant to what {company_name} actually "
        "does — a targeted resume beats a complete one."
    )


def _fallback_card(company_name: str, discipline: str | None) -> CompanyCard:
    return CompanyCard(
        company_name=company_name,
        industry=None,
        ownership=None,
        business_model=None,
        products_services=[],
        student_angle=_student_angle(company_name, discipline),
        resume_angle=_resume_angle(company_name),
        source="fallback",
    )


def _wikipedia_summary(company_name: str) -> dict | None:
    slug = urllib.parse.quote(company_name.strip().replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "resume-match-advisor (student project)"}
    )
    with urllib.request.urlopen(request, timeout=LOOKUP_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            return None
        return json.loads(response.read().decode("utf-8"))


def build_company_card(
    company_name: str | None, discipline: str | None = None
) -> CompanyCard | None:
    if not company_name or not company_name.strip():
        return None
    company_name = company_name.strip()

    if os.environ.get("COMPANY_LOOKUP", "on").lower() in ("off", "0", "false"):
        return _fallback_card(company_name, discipline)

    try:
        summary = _wikipedia_summary(company_name)
    except Exception:
        summary = None
    if not summary or summary.get("type") == "disambiguation":
        return _fallback_card(company_name, discipline)

    extract = (summary.get("extract") or "").strip()
    if not extract:
        return _fallback_card(company_name, discipline)
    lowered = extract.lower()

    industry = next((label for hint, label in INDUSTRY_HINTS if hint in lowered), None)
    if any(h in lowered for h in PUBLIC_HINTS):
        ownership = "Public"
    elif any(h in lowered for h in PRIVATE_HINTS):
        ownership = "Private"
    else:
        ownership = None

    # First sentence of the summary doubles as a products/services hint.
    first_sentence = extract.split(". ")[0].strip()
    if first_sentence and not first_sentence.endswith("."):
        first_sentence += "."

    return CompanyCard(
        company_name=summary.get("title", company_name),
        industry=industry,
        ownership=ownership,
        business_model=first_sentence[:300] if first_sentence else None,
        products_services=[],
        student_angle=_student_angle(company_name, discipline),
        resume_angle=_resume_angle(company_name),
        source="wikipedia",
    )

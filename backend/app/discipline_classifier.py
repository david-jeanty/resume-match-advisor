"""Classifies a job description into commerce disciplines using knowledge packs.

Scoring is a weighted count of matched pack vocabulary — role titles weigh
most, then core skills and tools, then business keywords. Fully explainable:
each detected discipline carries the signals that matched.
"""

from . import knowledge_loader
from .jd_parser import ParsedJD
from .models import DisciplineFit

TITLE_WEIGHT = 4
SKILL_WEIGHT = 2
TOOL_WEIGHT = 2
KEYWORD_WEIGHT = 1
MAX_DISCIPLINES = 3


def _score_pack(pack: dict, jd: ParsedJD) -> tuple[float, list[str]]:
    from .text_utils import contains_term

    score = 0.0
    signals: list[str] = []

    title_text = (jd.role_title or "").lower()
    for role in pack.get("role_titles", []):
        role_l = role.lower()
        if title_text and (role_l in title_text or title_text in role_l):
            score += TITLE_WEIGHT
            signals.append(f"title matches '{role}'")
            break

    pack_skills = {s.lower() for s in pack.get("core_skills", [])}
    pack_tools = {t.lower() for t in pack.get("tools", [])}
    for skill in jd.skills:
        if skill in pack_skills:
            score += SKILL_WEIGHT
            signals.append(f"skill: {skill}")
    for tool in jd.tools:
        if tool in pack_tools:
            score += TOOL_WEIGHT
            signals.append(f"tool: {tool}")

    for kw in pack.get("business_keywords", []):
        if contains_term(jd.norm_text, kw.lower()):
            score += KEYWORD_WEIGHT
            signals.append(f"keyword: {kw}")

    return score, signals


def classify(jd: ParsedJD, target_discipline: str | None = None) -> list[DisciplineFit]:
    disciplines = knowledge_loader.get_disciplines()

    scored: list[tuple[str, float, list[str]]] = []
    for pack_id, pack in disciplines.items():
        score, signals = _score_pack(pack, jd)
        if score > 0:
            scored.append((pack_id, score, signals))
    scored.sort(key=lambda item: item[1], reverse=True)

    results: list[DisciplineFit] = []

    # A user-selected discipline is always honored and listed first.
    if target_discipline and target_discipline in disciplines:
        pack = disciplines[target_discipline]
        _, signals = _score_pack(pack, jd)
        results.append(
            DisciplineFit(
                discipline_id=target_discipline,
                discipline=pack["discipline"],
                confidence="high",
                matched_signals=["selected by you"] + signals[:6],
            )
        )

    top_score = scored[0][1] if scored else 0.0
    for pack_id, score, signals in scored:
        if any(r.discipline_id == pack_id for r in results):
            continue
        if len(results) >= MAX_DISCIPLINES:
            break
        # Keep disciplines that are at least half as strong as the leader.
        if score < max(3.0, top_score * 0.5):
            continue
        if score >= 12:
            confidence = "high"
        elif score >= 6:
            confidence = "medium"
        else:
            confidence = "low"
        results.append(
            DisciplineFit(
                discipline_id=pack_id,
                discipline=disciplines[pack_id]["discipline"],
                confidence=confidence,
                matched_signals=signals[:8],
            )
        )

    return results

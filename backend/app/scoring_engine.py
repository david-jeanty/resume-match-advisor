"""Transparent, deterministic scoring.

Six weighted categories totaling 100. Every category produces a plain-language
explanation of how its points were earned. Whole numbers only — no fake precision.
"""

from . import knowledge_loader
from .jd_parser import ParsedJD
from .matching_engine import SkillMatch
from .models import DisciplineFit, EvidenceItem, ScoreBreakdownItem
from .resume_parser import ParsedResume
from .text_utils import contains_term

WEIGHTS = {
    "required_qualifications": 25,
    "skills_tools": 20,
    "experience_evidence": 20,
    "discipline_fit": 15,
    "keyword_coverage": 10,
    "clarity_structure": 10,
}

LABELS = {
    "required_qualifications": "Required qualifications match",
    "skills_tools": "Skills & tools match",
    "experience_evidence": "Experience evidence match",
    "discipline_fit": "Commerce discipline fit",
    "keyword_coverage": "Keyword & context coverage",
    "clarity_structure": "Resume clarity & structure",
}

STRENGTH_VALUE = {"strong": 1.0, "moderate": 0.65, "weak": 0.3, "missing": 0.0}
SKILL_STATUS_VALUE = {"direct": 1.0, "alias": 0.9, "translated": 0.5, "missing": 0.0}


def _avg_strength(items: list[EvidenceItem]) -> float:
    if not items:
        return 0.0
    return sum(STRENGTH_VALUE[i.match_strength] for i in items) / len(items)


def _count(items: list[EvidenceItem], strength: str) -> int:
    return sum(1 for i in items if i.match_strength == strength)


def score_required(items: list[EvidenceItem], skill_ratio: float) -> tuple[float, str]:
    required = [i for i in items if i.requirement_type == "required"]
    if not required:
        return skill_ratio, (
            "The posting had no clearly separated required qualifications, so this "
            "is based on overall skill coverage instead."
        )
    ratio = _avg_strength(required)
    return ratio, (
        f"Of {len(required)} required qualifications: {_count(required, 'strong')} strong, "
        f"{_count(required, 'moderate')} moderate, {_count(required, 'weak')} weak, "
        f"{_count(required, 'missing')} missing."
    )


def score_skills(matches: list[SkillMatch]) -> tuple[float, str]:
    if not matches:
        return 0.5, (
            "No specific skills or tools were detected in the posting, so a neutral "
            "score was applied."
        )
    ratio = sum(SKILL_STATUS_VALUE[m.status] for m in matches) / len(matches)
    covered = sum(1 for m in matches if m.status in ("direct", "alias"))
    transferable = sum(1 for m in matches if m.status == "translated")
    missing = sum(1 for m in matches if m.status == "missing")
    return ratio, (
        f"The posting mentions {len(matches)} skills/tools: {covered} covered in your "
        f"resume, {transferable} plausibly transferable from student experience, "
        f"{missing} not found."
    )


def score_experience(
    items: list[EvidenceItem], resume: ParsedResume
) -> tuple[float, str]:
    resp = [i for i in items if i.requirement_type == "responsibility"]
    resp_ratio = _avg_strength(resp) if resp else 0.5
    quant_ratio = (
        len(resume.quantified_bullets) / len(resume.bullets) if resume.bullets else 0.0
    )
    ratio = 0.8 * resp_ratio + 0.2 * min(1.0, quant_ratio / 0.4)
    if resp:
        detail = (
            f"{_count(resp, 'strong') + _count(resp, 'moderate')} of {len(resp)} "
            "responsibilities have direct or transferable evidence"
        )
    else:
        detail = "no responsibility list was detected, so a neutral base was used"
    return ratio, (
        f"Based on how well your bullets support the day-to-day work: {detail}; "
        f"{len(resume.quantified_bullets)} of {len(resume.bullets)} bullets include numbers."
    )


def score_discipline(
    disciplines: list[DisciplineFit], resume: ParsedResume
) -> tuple[float, str]:
    if not disciplines:
        return 0.4, (
            "The posting didn't map cleanly to a commerce discipline, so a neutral "
            "score was applied."
        )
    top = disciplines[0]
    pack = knowledge_loader.get_pack(top.discipline_id) or {}
    vocab = {s.lower() for s in pack.get("core_skills", [])}
    vocab |= {t.lower() for t in pack.get("tools", [])}
    resume_terms = set(resume.skills_found) | set(resume.tools_found)
    hits = len(vocab & resume_terms)
    coverage = min(1.0, hits / max(1, len(vocab) * 0.35))
    confidence_factor = {"high": 1.0, "medium": 0.85, "low": 0.7}[top.confidence]
    return coverage * confidence_factor, (
        f"This looks like a {top.discipline} role; your resume shows {hits} of the "
        f"skills and tools common to that discipline."
    )


def score_keywords(jd: ParsedJD, resume: ParsedResume,
                   disciplines: list[DisciplineFit]) -> tuple[float, str]:
    packs = knowledge_loader.get_disciplines()
    keywords: set[str] = set()
    pack_ids = [d.discipline_id for d in disciplines] or list(packs)
    for pack_id in pack_ids:
        for kw in packs.get(pack_id, {}).get("business_keywords", []):
            if contains_term(jd.norm_text, kw.lower()):
                keywords.add(kw.lower())
    if not keywords:
        return 0.5, "The posting used few recognizable business keywords; neutral score."
    found = {kw for kw in keywords if contains_term(resume.norm_text, kw)}
    ratio = min(1.0, (len(found) / len(keywords)) / 0.6)
    return ratio, (
        f"The posting uses {len(keywords)} business keywords for this discipline; "
        f"your resume speaks the same language on {len(found)} of them"
        + (f" (e.g. {', '.join(sorted(found)[:4])})." if found else ".")
    )


def score_clarity(resume: ParsedResume) -> tuple[float, str]:
    checks: list[tuple[bool, str]] = []
    sections = set(resume.sections_found)
    checks.append(("experience" in sections, "an Experience section"))
    checks.append(("education" in sections, "an Education section"))
    checks.append(("skills" in sections, "a Skills section"))
    checks.append((len(resume.bullets) >= 5, "at least 5 substantive bullets"))
    quant_ok = (
        resume.bullets
        and len(resume.quantified_bullets) / len(resume.bullets) >= 0.25
    )
    checks.append((bool(quant_ok), "numbers in at least a quarter of bullets"))
    verb_ok = (
        resume.bullets
        and len(resume.action_verb_bullets) / len(resume.bullets) >= 0.4
    )
    checks.append((bool(verb_ok), "bullets that start with action verbs"))

    passed = [label for ok, label in checks if ok]
    failed = [label for ok, label in checks if not ok]
    ratio = len(passed) / len(checks)
    explanation = f"Structure checks passed: {len(passed)} of {len(checks)}."
    if failed:
        explanation += f" Could improve: {'; '.join(failed[:3])}."
    return ratio, explanation


def interpret(score: int) -> str:
    if score >= 80:
        return (
            "Strong match — your resume already supports most of this role, but "
            "review the remaining gaps before applying."
        )
    if score >= 65:
        return (
            "Good potential match — a few clear, fixable improvements would make "
            "your application noticeably stronger."
        )
    if score >= 50:
        return (
            "Partial match — targeted resume changes are needed to show the "
            "evidence this role asks for."
        )
    return (
        "Weak match based on current resume evidence — but if you have relevant "
        "experience that isn't on the page yet, adding it could change this "
        "picture significantly."
    )


def compute_scores(
    jd: ParsedJD,
    resume: ParsedResume,
    evidence: list[EvidenceItem],
    skill_matches: list[SkillMatch],
    disciplines: list[DisciplineFit],
) -> tuple[int, str, list[ScoreBreakdownItem]]:
    skill_ratio, skills_expl = score_skills(skill_matches)
    ratios: dict[str, tuple[float, str]] = {
        "required_qualifications": score_required(evidence, skill_ratio),
        "skills_tools": (skill_ratio, skills_expl),
        "experience_evidence": score_experience(evidence, resume),
        "discipline_fit": score_discipline(disciplines, resume),
        "keyword_coverage": score_keywords(jd, resume, disciplines),
        "clarity_structure": score_clarity(resume),
    }
    breakdown = [
        ScoreBreakdownItem(
            category=cat,
            label=LABELS[cat],
            score=round(max(0.0, min(1.0, ratio)) * WEIGHTS[cat]),
            max_score=WEIGHTS[cat],
            explanation=expl,
        )
        for cat, (ratio, expl) in ratios.items()
    ]
    overall = min(100, sum(item.score for item in breakdown))
    return overall, interpret(overall), breakdown

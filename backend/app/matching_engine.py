"""Matching engine: builds the evidence map and skill coverage.

Match strengths, in plain terms:
  strong   — the requirement's key term (or a well-known equivalent like
             Salesforce for CRM) appears in an experience bullet.
  moderate — the term appears only in a skills list, or a transferable
             student experience (club, case competition, part-time job)
             plausibly supports it.
  weak     — some words overlap but nothing clearly demonstrates it.
  missing  — no evidence found at all.
"""

import re
from dataclasses import dataclass
from typing import Literal, Optional

from . import knowledge_loader
from .jd_parser import EDUCATION_DEGREE_CUES, ParsedJD
from .models import EvidenceItem, RequirementType
from .resume_parser import ParsedResume
from .text_utils import clip, contains_term, content_tokens, normalize

STRENGTH_ORDER = {"strong": 3, "moderate": 2, "weak": 1, "missing": 0}

# Broad field-of-study aliases for "degree in Business, Finance, Economics,
# or a related field"-type requirements. Deliberately does NOT include
# "intern"/"co-op" — those describe work status, not a field of study, and
# must never satisfy an education requirement on their own.
#
# Distinctive multi-word/program names are safe to search anywhere in the
# resume. Generic single-word field names (finance, marketing, accounting...)
# are common outside an education context too (job titles, company
# descriptions) and are only trusted when found inside a detected Education
# section — otherwise "Marketing Intern" would falsely satisfy a degree
# requirement for someone with no education section at all.
DISTINCTIVE_DEGREE_TERMS = [
    "bachelor of commerce", "bcom", "b.com", "bcomm",
    "business technology management", "btm", "telfer school of management",
    "telfer", "management information systems", "business analytics",
    "operations management", "business administration", "bba",
    "business management",
]
GENERIC_FIELD_TERMS = ["commerce", "finance", "accounting", "marketing", "economics", "mis"]
BUSINESS_DEGREE_TERMS = DISTINCTIVE_DEGREE_TERMS + GENERIC_FIELD_TERMS
DEGREE_DATE_CUES = ["expected", "anticipated", "in progress", "current year"]
_YEAR_RE = re.compile(r"\b20\d{2}\b")


def _is_education_requirement(text: str) -> bool:
    lowered = normalize(text)
    return any(cue in lowered for cue in EDUCATION_DEGREE_CUES)


def _evaluate_education_requirement(resume: ParsedResume) -> "TermEvidence":
    education_lines = resume.sections.get("education", [])
    education_text = normalize(" ".join(education_lines))

    if education_lines:
        matched_term = next(
            (t for t in BUSINESS_DEGREE_TERMS if contains_term(education_text, t)), None
        )
    else:
        # No Education section at all — only trust distinctive program names,
        # never a bare word like "marketing" or "finance" that could just as
        # easily come from a job title.
        matched_term = next(
            (t for t in DISTINCTIVE_DEGREE_TERMS if contains_term(resume.norm_text, t)),
            None,
        )
    if not matched_term:
        return TermEvidence(
            "degree field", "missing", None, None,
            advice="No business/finance/economics-related degree or program was found.",
        )

    line = next(
        (l for l in (education_lines or resume.lines) if contains_term(normalize(l), matched_term)),
        None,
    )
    has_date = bool(education_lines) and (
        _YEAR_RE.search(education_text) or any(c in education_text for c in DEGREE_DATE_CUES)
    )

    if education_lines and has_date:
        strength = "strong"
        advice = (
            f"Your {matched_term} program in the Education section satisfies this "
            "field-of-study requirement, and your resume shows you're currently enrolled."
        )
    elif education_lines:
        strength = "moderate"
        advice = (
            f"Your {matched_term} program supports this requirement — add your expected "
            "graduation date to your Education section to make current enrollment obvious."
        )
    else:
        strength = "moderate"
        advice = (
            f"Found '{matched_term}' relevant to this requirement, but not in a clearly "
            "labeled Education section — make sure your degree and expected graduation "
            "date are easy to find."
        )
    return TermEvidence("degree field", strength, line, matched_term, advice=advice)


@dataclass
class SkillMatch:
    term: str
    status: Literal["direct", "alias", "translated", "context", "missing"]
    evidence_line: Optional[str] = None
    matched_via: Optional[str] = None  # alias term, student signal, or context source
    translation_advice: Optional[str] = None


@dataclass
class ContextTermEvidence:
    """Evidence contributed by optional university/club context (Phase 2).

    Consulted only when the resume itself shows nothing for a term, and
    capped: course context is weak, club context at most moderate.
    """

    strength: str  # weak | moderate
    line: Optional[str]
    source: str  # e.g. "ADM 2372 (Management Information Systems) coursework"
    advice: str


@dataclass
class TermEvidence:
    term: str
    strength: str  # strong | moderate | weak | missing
    line: Optional[str]
    via: Optional[str]  # what actually matched (alias / student signal / context)
    advice: Optional[str] = None
    origin: str = "resume"  # resume | translation | context


def _all_vocab_terms() -> set[str]:
    disciplines = knowledge_loader.get_disciplines()
    common = knowledge_loader.get_common()
    terms: set[str] = set(common.get("skill_aliases", {}).keys())
    for pack in disciplines.values():
        terms.update(s.lower() for s in pack.get("core_skills", []))
        terms.update(t.lower() for t in pack.get("tools", []))
    return terms


def _terms_in(text: str) -> list[str]:
    norm = normalize(text)
    found = [t for t in _all_vocab_terms() if contains_term(norm, t)]
    # Requirements often use an equivalent phrase instead of the canonical
    # term ("event promotion" for event planning, "Salesforce" for CRM).
    aliases = knowledge_loader.get_common().get("skill_aliases", {})
    for canonical, variants in aliases.items():
        if canonical not in found and any(contains_term(norm, v) for v in variants):
            found.append(canonical)
    # Drop terms fully contained in a longer matched term
    # ("marketing" inside "email marketing").
    return sorted(
        (t for t in found
         if not any(t != other and t in other for other in found)),
        key=len, reverse=True,
    )


def _find_line(resume: ParsedResume, term: str) -> Optional[str]:
    """Best resume line containing the term: quantified bullets win."""
    hits = [b for b in resume.bullets if contains_term(normalize(b), term)]
    if hits:
        quantified = [b for b in hits if b in resume.quantified_bullets]
        return (quantified or hits)[0]
    for line in resume.lines:
        if contains_term(normalize(line), term):
            return line
    return None


def _translations_for(term: str) -> list[dict]:
    common = knowledge_loader.get_common()
    return [
        t for t in common.get("student_experience_translations", [])
        if term in {s.lower() for s in t.get("supports", [])}
    ]


def evidence_for_term(term: str, resume: ParsedResume) -> TermEvidence:
    aliases = knowledge_loader.get_common().get("skill_aliases", {})

    # 1. Direct occurrence of the term itself.
    if contains_term(resume.norm_text, term):
        line = _find_line(resume, term)
        in_bullet = line is not None and line in resume.bullets
        return TermEvidence(term, "strong" if in_bullet else "moderate", line, None)

    # 2. A known equivalent (e.g. Salesforce for CRM).
    for alias in aliases.get(term, []):
        if contains_term(resume.norm_text, alias):
            line = _find_line(resume, alias)
            in_bullet = line is not None and line in resume.bullets
            return TermEvidence(
                term, "strong" if in_bullet else "moderate", line, alias
            )

    # 3. Transferable student experience present in the resume.
    for translation in _translations_for(term):
        for signal in translation.get("signals", []):
            if contains_term(resume.norm_text, signal):
                return TermEvidence(
                    term, "moderate", _find_line(resume, signal), signal,
                    advice=translation.get("advice"), origin="translation",
                )

    # 4. Optional university/club context (courses = weak, clubs <= moderate).
    ctx = resume.context_evidence.get(term)
    if ctx is not None:
        return TermEvidence(
            term, ctx.strength, ctx.line, ctx.source,
            advice=ctx.advice, origin="context",
        )

    return TermEvidence(term, "missing", None, None)


def _token_overlap_evidence(
    requirement: str, resume: ParsedResume
) -> tuple[str, Optional[str]]:
    """Fallback for requirements with no known vocabulary terms."""
    stopwords = set(knowledge_loader.get_common().get("stopwords", []))
    req_tokens = content_tokens(requirement, stopwords)
    if not req_tokens:
        return "missing", None
    best_line, best_hits = None, 0
    for line in resume.lines:
        hits = len(req_tokens & content_tokens(line, stopwords))
        if hits > best_hits:
            best_line, best_hits = line, hits
    ratio = best_hits / len(req_tokens)
    if best_hits >= 2 and ratio >= 0.5:
        return "moderate", best_line
    if best_hits >= 2 or ratio >= 0.4:
        return "weak", best_line
    return "missing", None


def _explain(strength: str, evidences: list[TermEvidence], line: Optional[str]) -> str:
    supported = [e for e in evidences if e.strength != "missing"]
    unsupported = [e.term for e in evidences if e.strength == "missing"]
    parts: list[str] = []
    if strength in ("strong", "moderate") and not supported:
        # Token-overlap match (no recognizable skill term in the requirement).
        parts.append(
            "Your resume covers this requirement's wording closely, though no "
            "specific skill term was involved — read the quoted line and make "
            "sure it says this as directly as possible."
        )
    elif strength == "strong":
        best = supported[0]
        via = f" (via {best.via})" if best.via else ""
        parts.append(
            f"Your resume directly shows {best.term}{via} in an experience bullet."
        )
    elif strength == "moderate":
        best = supported[0]
        if best.origin == "context":
            parts.append(
                f"No direct {best.term} evidence in the resume, but your "
                f"{best.via} may support it. {best.advice}"
            )
        elif best.advice:
            parts.append(
                f"No direct {best.term} bullet, but your '{best.via}' experience "
                f"is transferable. {best.advice}"
            )
        elif best.via:
            parts.append(
                f"Found related evidence for {best.term} through {best.via}, "
                "though it isn't framed in an experience bullet yet."
            )
        else:
            parts.append(
                f"{best.term.capitalize()} appears in your resume, but only as a "
                "listed skill — an experience bullet showing it in use would be stronger."
            )
    elif strength == "weak":
        if supported and supported[0].origin == "context":
            best = supported[0]
            parts.append(
                f"Your {best.via} may relate to {best.term}, but coursework or "
                f"membership alone is weak evidence. {best.advice}"
            )
        else:
            parts.append(
                "Some wording overlaps with this requirement, but nothing in the "
                "resume clearly demonstrates it."
            )
    else:
        parts.append("No evidence for this requirement was found in your resume.")
    if unsupported and strength in ("strong", "moderate"):
        parts.append(f"Still unaddressed: {', '.join(unsupported[:4])}.")
    return " ".join(parts)


def build_evidence_item(
    requirement: str, req_type: RequirementType, resume: ParsedResume
) -> EvidenceItem:
    if _is_education_requirement(requirement):
        ev = _evaluate_education_requirement(resume)
        return EvidenceItem(
            requirement=clip(requirement, 220),
            requirement_type=req_type,
            resume_evidence=clip(ev.line) if ev.line else None,
            match_strength=ev.strength,  # type: ignore[arg-type]
            explanation=ev.advice or "",
        )

    terms = _terms_in(requirement)
    if terms:
        evidences = sorted(
            (evidence_for_term(t, resume) for t in terms),
            key=lambda e: STRENGTH_ORDER[e.strength],
            reverse=True,
        )
        best = evidences[0]
        strength, line = best.strength, best.line
        # A requirement whose terms are mostly unaddressed shouldn't read
        # as fully covered even if one term matched.
        missing_count = sum(1 for e in evidences if e.strength == "missing")
        if strength == "strong" and missing_count > len(evidences) / 2:
            strength = "moderate"
        explanation = _explain(strength, evidences, line)
    else:
        strength, line = _token_overlap_evidence(requirement, resume)
        evidences = []
        explanation = _explain(strength, [], line)

    return EvidenceItem(
        requirement=clip(requirement, 220),
        requirement_type=req_type,
        resume_evidence=clip(line) if line else None,
        match_strength=strength,  # type: ignore[arg-type]
        explanation=explanation,
    )


def build_evidence_map(jd: ParsedJD, resume: ParsedResume) -> list[EvidenceItem]:
    items = [build_evidence_item(r, "required", resume) for r in jd.required]
    items += [build_evidence_item(r, "preferred", resume) for r in jd.preferred]
    items += [build_evidence_item(r, "responsibility", resume) for r in jd.responsibilities]
    return items


def match_skills(terms: list[str], resume: ParsedResume) -> list[SkillMatch]:
    matches: list[SkillMatch] = []
    for term in terms:
        ev = evidence_for_term(term, resume)
        if ev.strength == "missing":
            status = "missing"
        elif ev.origin == "context":
            status = "context"
        elif ev.advice:
            status = "translated"
        elif ev.via:
            status = "alias"
        else:
            status = "direct"
        matches.append(
            SkillMatch(
                term=term,
                status=status,  # type: ignore[arg-type]
                evidence_line=clip(ev.line) if ev.line else None,
                matched_via=ev.via,
                translation_advice=ev.advice,
            )
        )
    return matches

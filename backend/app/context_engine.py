"""Optional university / location context layer (Phase 2).

Detects university, course, club, co-op, and location context — either
provided by the student or found in the resume/JD text — and turns it into:

  1. structured context objects for the report,
  2. capped-strength term evidence for the matching engine, and
  3. the optional "context" report sections.

Design rule (non-negotiable): context improves feedback wording and evidence
translation. Course codes and club names alone are weak evidence at most and
must never meaningfully inflate the score.
"""

import re

from . import knowledge_loader
from .jd_parser import ParsedJD
from .matching_engine import ContextTermEvidence, evidence_for_term
from .models import (
    AnalyzeRequest,
    ContextSection,
    DetectedClub,
    DetectedCourse,
    DisciplineFit,
    LocationContext,
    UniversityContext,
)
from .resume_parser import ParsedResume
from .text_utils import clip, contains_term, normalize

STRENGTH_RANK = {"weak": 1, "moderate": 2, "strong": 3}


# ---------------------------------------------------------------- university

def resolve_university(
    request: AnalyzeRequest, resume: ParsedResume
) -> tuple[dict | None, str | None]:
    """Return (pack, detected_from) — a specific pack, the generic fallback,
    or (None, None) when there's no university context at all."""
    packs = knowledge_loader.get_universities()
    provided = normalize(request.university or "")

    if provided:
        for pack in packs.values():
            names = [pack.get("university_name", ""), pack.get("business_school") or ""]
            candidates = [normalize(n) for n in names if n] + [
                a.lower() for a in pack.get("aliases", [])
            ]
            if any(c and (c in provided or provided in c) for c in candidates):
                return pack, "provided"
        generic = packs.get("generic_commerce")
        if generic:
            generic = dict(generic)
            generic["university_name"] = request.university.strip()
            return generic, "provided"
        return None, None

    for pack in packs.values():
        if pack.get("id") == "generic_commerce":
            continue
        if any(contains_term(resume.norm_text, a) for a in pack.get("aliases", [])):
            return pack, "resume"
    return None, None


def _extract_course_codes(pack: dict, resume: ParsedResume,
                          completed_courses) -> set[str]:
    """Canonicalized codes like 'ADM 1370' from resume text and user input."""
    texts = [resume.norm_text]
    if completed_courses:
        if isinstance(completed_courses, str):
            texts.append(completed_courses.lower())
        else:
            texts.append(" ".join(completed_courses).lower())

    codes: set[str] = set()
    for pattern in pack.get("course_code_patterns", []):
        regex = re.compile(pattern, re.IGNORECASE)
        for text in texts:
            for match in regex.findall(text):
                cleaned = re.sub(r"[\s-]+", "", match).upper()  # ADM1370
                codes.add(f"{cleaned[:3]} {cleaned[3:]}")
    return codes


def detect_courses(pack: dict, resume: ParsedResume,
                   completed_courses) -> list[DetectedCourse]:
    courses = pack.get("courses", {})
    if not courses:
        return []
    # French sections use parallel codes (ADM 1770 -> ADM 1370 entry).
    code_lookup: dict[str, str] = {code: code for code in courses}
    for code, course in courses.items():
        fr = course.get("french_equivalent")
        if fr:
            code_lookup[fr] = code

    detected: list[DetectedCourse] = []
    for raw_code in sorted(_extract_course_codes(pack, resume, completed_courses)):
        canonical = code_lookup.get(raw_code)
        if not canonical or any(d.code == canonical for d in detected):
            continue
        course = courses[canonical]

        # Strength rule: code only = weak; resume shows a mapped skill/tool
        # in use = moderate; in a quantified bullet = strong.
        strength = "weak"
        applied_line: str | None = None
        for skill in course.get("skills", []):
            ev = evidence_for_term(skill, resume)
            if ev.advice or ev.strength not in ("strong", "moderate"):
                continue  # translation/context hits don't count as applied work
            if ev.line and ev.line in resume.quantified_bullets:
                strength, applied_line = "strong", ev.line
                break
            if strength != "strong":
                strength, applied_line = "moderate", ev.line or applied_line

        if strength == "weak":
            note = course.get("advice", "A course name alone is weak evidence — add the project, tool, deliverable, or outcome.")
        elif strength == "moderate":
            note = (
                f"Your resume already shows related applied work ("
                f"\"{clip(applied_line or '', 100)}\") — connect it to the "
                f"{canonical} material explicitly and add the outcome to make it stronger."
            )
        else:
            note = (
                f"Good: this coursework is backed by concrete, quantified work in your "
                f"resume (\"{clip(applied_line or '', 100)}\")."
            )
        detected.append(
            DetectedCourse(
                code=canonical,
                name=course.get("name", canonical),
                disciplines=course.get("disciplines", []),
                related_skills=course.get("skills", []),
                strength=strength,  # type: ignore[arg-type]
                note=note,
            )
        )
    return detected


def _club_strength(pack: dict, resume: ParsedResume, alias: str,
                   kind: str) -> tuple[str, str | None]:
    """Apply the evidence-strength rules to a detected club/competition."""
    leadership_terms = pack.get("leadership_title_terms", [])
    outcome_terms = pack.get("strong_outcome_terms", [])

    matched_indexes = [
        i for i, line in enumerate(resume.lines)
        if contains_term(normalize(line), alias)
    ]
    if not matched_indexes:
        return ("moderate" if kind == "competition" else "weak"), None

    first_line = resume.lines[matched_indexes[0]]
    leadership = False
    concrete = False
    for i in matched_indexes:
        window = resume.lines[max(0, i - 1): i + 4]
        for line in window:
            norm_line = normalize(line)
            if any(contains_term(norm_line, t) for t in leadership_terms):
                leadership = True
            has_numbers = any(c.isdigit() for c in line) or "$" in line or "%" in line
            if has_numbers or any(contains_term(norm_line, t) for t in outcome_terms):
                concrete = True

    if kind == "competition":
        # Participation alone is moderate; results/organizing make it strong.
        return ("strong" if (concrete and leadership) or concrete else "moderate"), first_line
    if leadership and concrete:
        return "strong", first_line
    if leadership or concrete:
        return "moderate", first_line
    return "weak", first_line


def detect_clubs(pack: dict, resume: ParsedResume) -> list[DetectedClub]:
    detected: list[DetectedClub] = []
    groups = [("club", pack.get("clubs", {})), ("competition", pack.get("competitions", {}))]
    for default_kind, group in groups:
        for entry in group.values():
            alias_hit = next(
                (a for a in entry.get("aliases", [])
                 if contains_term(resume.norm_text, a)),
                None,
            )
            if not alias_hit:
                continue
            kind = entry.get("kind", default_kind)
            strength, line = _club_strength(
                pack, resume, alias_hit, "competition" if default_kind == "competition" else kind
            )
            prefix = {
                "weak": "Right now this reads as membership only. ",
                "moderate": "",
                "strong": "Strong involvement — keep the specifics. ",
            }[strength]
            detected.append(
                DetectedClub(
                    name=entry.get("full_name", alias_hit),
                    matched_text=alias_hit,
                    kind="competition" if default_kind == "competition" else (
                        kind if kind in ("club", "association") else "club"
                    ),
                    disciplines=entry.get("disciplines", []),
                    supports=entry.get("supports", []),
                    strength=strength,  # type: ignore[arg-type]
                    note=prefix + entry.get("advice", ""),
                )
            )
    return detected


def build_university_context(
    request: AnalyzeRequest, resume: ParsedResume
) -> tuple[UniversityContext | None, dict | None]:
    pack, detected_from = resolve_university(request, resume)
    if not pack:
        return None, None

    coop_signals = pack.get("coop_context", {}).get("signals", [])
    bilingual_signals = pack.get("bilingual_context", {}).get("signals", [])

    context = UniversityContext(
        university_name=pack.get("university_name", "your university"),
        business_school=pack.get("business_school"),
        detected_from=detected_from,  # type: ignore[arg-type]
        program=(request.program or "").strip() or None,
        detected_courses=detect_courses(pack, resume, request.completed_courses),
        detected_clubs=detect_clubs(pack, resume),
        coop_detected=any(contains_term(resume.norm_text, s) for s in coop_signals),
        bilingual_detected=any(
            contains_term(resume.norm_text, s) for s in bilingual_signals
        ),
        notes=[],
    )
    return context, pack


# ------------------------------------------------------------------ location

def resolve_location(request: AnalyzeRequest, jd: ParsedJD) -> tuple[dict | None, str | None]:
    packs = knowledge_loader.get_locations()
    provided = normalize(request.location or "")
    if provided:
        for pack in packs.values():
            candidates = [normalize(pack.get("location_name", ""))] + [
                a.lower() for a in pack.get("aliases", [])
            ]
            if any(c and (c in provided or provided in c) for c in candidates):
                return pack, "provided"
        return packs.get("generic_canada"), "provided"
    # Only specific locations are auto-detected from the posting — generic
    # aliases like "remote"/"hybrid" appear in too many JDs to be a signal.
    for pack in packs.values():
        if pack.get("id") == "generic_canada":
            continue
        if any(contains_term(jd.norm_text, a) for a in pack.get("aliases", [])):
            return pack, "job_description"
    return None, None


def build_location_context(
    request: AnalyzeRequest, jd: ParsedJD
) -> tuple[LocationContext | None, dict | None]:
    pack, detected_from = resolve_location(request, jd)
    if not pack:
        return None, None
    advice = [
        angle["advice"]
        for angle in pack.get("role_angles", [])
        if any(contains_term(jd.norm_text, t) for t in angle.get("if_jd_mentions", []))
    ]
    advice += pack.get("positioning_advice", [])
    return (
        LocationContext(
            location_name=pack.get("location_name", "your location"),
            detected_from=detected_from,  # type: ignore[arg-type]
            industries=pack.get("common_industries", []),
            positioning_advice=advice[:4],
        ),
        pack,
    )


# ---------------------------------------------------- matching-engine bridge

def build_context_term_evidence(
    university_context: UniversityContext | None, pack: dict | None
) -> dict[str, ContextTermEvidence]:
    """Term evidence the matcher may use ONLY when the resume itself has
    nothing. Courses inject weak evidence; clubs are capped at moderate."""
    if not university_context or not pack:
        return {}
    evidence: dict[str, ContextTermEvidence] = {}

    def _offer(term: str, candidate: ContextTermEvidence) -> None:
        existing = evidence.get(term)
        if not existing or STRENGTH_RANK[candidate.strength] > STRENGTH_RANK[existing.strength]:
            evidence[term] = candidate

    for course in university_context.detected_courses:
        for term in course.related_skills:
            _offer(term, ContextTermEvidence(
                strength="weak",  # course context is never more than weak
                line=None,
                source=f"{course.code} ({course.name}) coursework",
                advice=course.note if course.strength == "weak" else (
                    f"You may have {course.code} coursework to draw from — add the "
                    "project, tool, deliverable, or outcome to make this real evidence."
                ),
            ))

    for club in university_context.detected_clubs:
        capped = "moderate" if STRENGTH_RANK[club.strength] >= 2 else "weak"
        for term in club.supports:
            _offer(term, ContextTermEvidence(
                strength=capped,
                line=None,
                source=f"{club.name} involvement",
                advice=club.note,
            ))
    return evidence


# ------------------------------------------------------------ report sections

def build_feedback_sections(
    university_context: UniversityContext | None,
    university_pack: dict | None,
    location_context: LocationContext | None,
    disciplines: list[DisciplineFit],
) -> list[ContextSection]:
    sections: list[ContextSection] = []
    role_discipline_ids = {d.discipline_id for d in disciplines}

    if university_context and university_pack:
        items: list[str] = []
        if university_context.program:
            items.append(
                f"You identified your program as {university_context.program} — make "
                "sure your education section names it the same way, with your expected "
                "graduation date."
            )
        if university_context.coop_detected:
            coop_advice = university_pack.get("coop_context", {}).get("advice")
            if coop_advice:
                items.append(coop_advice)
        if university_context.bilingual_detected:
            bilingual_advice = university_pack.get("bilingual_context", {}).get("advice")
            if bilingual_advice:
                items.append(bilingual_advice)
        # Course advice, most role-relevant first, capped to keep it readable.
        relevant = [
            c for c in university_context.detected_courses
            if not c.disciplines or set(c.disciplines) & role_discipline_ids
        ]
        for course in relevant[:4]:
            items.append(f"{course.code} ({course.name}): {course.note}")
        if items:
            sections.append(ContextSection(
                section_id="university_program",
                title="How your school/program context may help",
                items=items[:6],
            ))

        club_items = [
            f"{club.name}: {club.note}"
            for club in university_context.detected_clubs
        ]
        if club_items:
            school_label = university_context.business_school or "school"
            sections.append(ContextSection(
                section_id="school_involvement",
                title=f"How your {school_label} involvement may translate",
                items=club_items[:5],
            ))

    if location_context and location_context.positioning_advice:
        sections.append(ContextSection(
            section_id="location_angle",
            title="Location-specific application angle",
            items=location_context.positioning_advice,
        ))
    return sections

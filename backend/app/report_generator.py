"""Assembles the full analysis report from the deterministic pipeline."""

from . import context_engine, knowledge_loader
from .company_card import build_company_card
from .discipline_classifier import classify
from .jd_parser import ParsedJD, parse_jd
from .matching_engine import SkillMatch, build_evidence_map, match_skills
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    EvidenceItem,
    ImprovementSuggestion,
    JobRequirements,
    MissingSkills,
    ResumeSignals,
)
from .resume_parser import ParsedResume, parse_resume
from .scoring_engine import compute_scores
from .text_utils import clip, contains_term, normalize

MAX_SUGGESTIONS = 8


def _bucket_missing(jd: ParsedJD, matches: list[SkillMatch]) -> MissingSkills:
    tools = set(jd.tools)
    required_text = normalize(" ".join(jd.required + jd.responsibilities))
    preferred_text = normalize(" ".join(jd.preferred))

    required_missing: list[str] = []
    preferred_missing: list[str] = []
    tools_missing: list[str] = []
    for m in matches:
        if m.status != "missing":
            continue
        if m.term in tools:
            tools_missing.append(m.term)
        elif contains_term(preferred_text, m.term) and not contains_term(
            required_text, m.term
        ):
            preferred_missing.append(m.term)
        else:
            required_missing.append(m.term)
    return MissingSkills(
        required_missing=sorted(required_missing),
        preferred_missing=sorted(preferred_missing),
        tools_missing=sorted(tools_missing),
    )


def _weak_areas(evidence: list[EvidenceItem], matches: list[SkillMatch]) -> list[str]:
    areas: list[str] = []
    for item in evidence:
        if item.match_strength == "weak":
            areas.append(
                f"Only weak evidence for: \"{clip(item.requirement, 120)}\""
            )
        elif item.match_strength == "missing" and item.requirement_type == "required":
            areas.append(
                f"No evidence yet for required item: \"{clip(item.requirement, 120)}\""
            )
    for m in matches:
        if m.status == "translated":
            areas.append(
                f"{m.term} — your '{m.matched_via}' experience is transferable, "
                "but the resume doesn't say it explicitly yet"
            )
        elif m.status == "context":
            areas.append(
                f"{m.term} — your {m.matched_via} may cover this, but the resume "
                "doesn't show it applied yet"
            )
    return areas[:10]


def _suggestion_for_missing_term(
    term: str, pack: dict | None, is_tool: bool
) -> ImprovementSuggestion:
    common = knowledge_loader.get_common()
    # A pack improvement angle that mentions the term is the most specific advice.
    for angle in (pack or {}).get("improvement_angles", []):
        if term in angle.lower():
            return ImprovementSuggestion(
                priority="high", title=f"Show {term} explicitly",
                suggestion=angle, related_requirement=term,
            )
    translations = [
        t for t in common.get("student_experience_translations", [])
        if term in {s.lower() for s in t.get("supports", [])}
    ]
    if translations:
        return ImprovementSuggestion(
            priority="high",
            title=f"Surface hidden {term} evidence",
            suggestion=(
                f"The posting asks for {term} and your resume doesn't show it yet. "
                f"{translations[0].get('advice', '')}"
            ),
            related_requirement=term,
        )
    where = "coursework, a class project, a club role, an internship, or a part-time job"
    kind = "tool" if is_tool else "skill"
    return ImprovementSuggestion(
        priority="high" if not is_tool else "medium",
        title=f"Add {term} evidence" if not is_tool else f"Mention {term} if you've used it",
        suggestion=(
            f"The posting names {term} as a {kind} it cares about. If you have used "
            f"it in {where}, add a specific bullet naming the context and what you "
            f"did with it. If you haven't, consider a small project or course to "
            "build it before applying — don't add it without real experience."
        ),
        related_requirement=term,
    )


def _build_suggestions(
    jd: ParsedJD,
    resume: ParsedResume,
    evidence: list[EvidenceItem],
    matches: list[SkillMatch],
    missing: MissingSkills,
    pack: dict | None,
) -> list[ImprovementSuggestion]:
    suggestions: list[ImprovementSuggestion] = []

    for term in missing.required_missing[:3]:
        suggestions.append(_suggestion_for_missing_term(term, pack, is_tool=False))
    for term in missing.tools_missing[:2]:
        suggestions.append(_suggestion_for_missing_term(term, pack, is_tool=True))

    # Transferable student experience that should be made explicit.
    for m in matches:
        if len(suggestions) >= MAX_SUGGESTIONS:
            break
        if m.status == "translated":
            suggestions.append(
                ImprovementSuggestion(
                    priority="medium",
                    title=f"Reframe your {m.matched_via} experience as {m.term}",
                    suggestion=m.translation_advice
                    or f"Make the {m.term} aspect of your {m.matched_via} experience explicit.",
                    related_requirement=m.term,
                )
            )
        elif m.status == "context":
            suggestions.append(
                ImprovementSuggestion(
                    priority="medium",
                    title=f"Turn your {m.matched_via} into {m.term} evidence",
                    suggestion=m.translation_advice
                    or (
                        f"The posting asks for {m.term}, and your {m.matched_via} may "
                        "cover it — but only if the resume shows the project, tool, "
                        "deliverable, or outcome, not just the name."
                    ),
                    related_requirement=m.term,
                )
            )

    # Required requirements with no evidence and no recognizable skill terms.
    for item in evidence:
        if (
            item.requirement_type == "required"
            and item.match_strength == "missing"
            and not any(s.related_requirement and s.related_requirement in
                        item.requirement.lower() for s in suggestions)
            and len(suggestions) < MAX_SUGGESTIONS
        ):
            suggestions.append(
                ImprovementSuggestion(
                    priority="medium",
                    title="Address an unmatched requirement",
                    suggestion=(
                        f"The posting requires: \"{clip(item.requirement, 140)}\". "
                        "Nothing in your resume speaks to this — if any experience, "
                        "course, or activity relates, make it explicit; if not, be "
                        "ready to address it in a cover letter."
                    ),
                    related_requirement=clip(item.requirement, 100),
                )
            )
            break

    # Structural advice.
    if resume.bullets and len(resume.quantified_bullets) / len(resume.bullets) < 0.25:
        suggestions.append(
            ImprovementSuggestion(
                priority="medium",
                title="Add numbers to your bullets",
                suggestion=(
                    "Few of your bullets include numbers. Add scale wherever honest: "
                    "team size, attendance, dollars handled, items processed, growth "
                    "percentages, or hours per week. Numbers make student experience credible."
                ),
            )
        )
    if "skills" not in resume.sections_found and jd.tools:
        suggestions.append(
            ImprovementSuggestion(
                priority="low",
                title="Add a skills section",
                suggestion=(
                    "Add a short Skills section listing tools you can genuinely use — "
                    f"this posting names {', '.join(jd.tools[:5])}."
                ),
            )
        )

    order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: order[s.priority])
    return suggestions[:MAX_SUGGESTIONS]


def generate_report(request: AnalyzeRequest) -> AnalyzeResponse:
    resume = parse_resume(request.resume_text)
    jd = parse_jd(request.job_description_text)

    # Optional Phase-2 context (university/courses/clubs/location). Context
    # feeds evidence translation and advice; course codes and club names on
    # their own contribute weak evidence at most and can't inflate the score.
    university_context, university_pack = context_engine.build_university_context(
        request, resume
    )
    resume.context_evidence = context_engine.build_context_term_evidence(
        university_context, university_pack
    )

    disciplines = classify(jd, request.target_discipline)

    evidence = build_evidence_map(jd, resume)
    # Drop terms subsumed by a longer detected term ("testing" vs "a/b testing").
    all_terms = set(jd.skills) | set(jd.tools)
    skill_terms = sorted(
        t for t in all_terms if not any(t != other and t in other for other in all_terms)
    )
    matches = match_skills(skill_terms, resume)

    overall, interpretation, breakdown = compute_scores(
        jd, resume, evidence, matches, disciplines
    )
    missing = _bucket_missing(jd, matches)

    top_pack = (
        knowledge_loader.get_pack(disciplines[0].discipline_id) if disciplines else None
    )
    suggestions = _build_suggestions(jd, resume, evidence, matches, missing, top_pack)

    card = build_company_card(
        request.company_name,
        disciplines[0].discipline if disciplines else None,
    )

    location_context, _location_pack = context_engine.build_location_context(request, jd)
    contextual_feedback = context_engine.build_feedback_sections(
        university_context, university_pack, location_context, disciplines
    )

    return AnalyzeResponse(
        overall_score=overall,
        score_interpretation=interpretation,
        score_breakdown=breakdown,
        detected_disciplines=disciplines,
        extracted_job_requirements=JobRequirements(
            role_title=jd.role_title,
            required_qualifications=jd.required,
            preferred_qualifications=jd.preferred,
            responsibilities=jd.responsibilities,
            skills=jd.skills,
            tools=jd.tools,
        ),
        extracted_resume_signals=ResumeSignals(
            sections_found=resume.sections_found,
            skills_found=resume.skills_found,
            tools_found=resume.tools_found,
            student_signals=resume.student_signals,
            bullet_count=len(resume.bullets),
            quantified_bullet_count=len(resume.quantified_bullets),
            action_verb_bullet_count=len(resume.action_verb_bullets),
        ),
        evidence_map=evidence,
        missing_skills=missing,
        weak_areas=_weak_areas(evidence, matches),
        improvement_suggestions=suggestions,
        company_card=card,
        university_context=university_context,
        location_context=location_context,
        contextual_feedback=contextual_feedback,
    )

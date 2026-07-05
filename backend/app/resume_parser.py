"""Deterministic resume parser.

Splits pasted resume text into sections, extracts bullets, and detects
skills, tools, and student-experience signals using the knowledge packs.
No AI involved — everything here is explainable string matching.
"""

from dataclasses import dataclass, field

from . import knowledge_loader
from .text_utils import contains_term, normalize, split_lines


@dataclass
class ParsedResume:
    raw_text: str
    norm_text: str
    lines: list[str]
    sections: dict[str, list[str]]  # canonical section name -> lines
    bullets: list[str]  # experience-like lines used as evidence candidates
    skills_found: list[str]
    tools_found: list[str]
    student_signals: list[str]
    quantified_bullets: list[str] = field(default_factory=list)
    action_verb_bullets: list[str] = field(default_factory=list)
    # Optional Phase-2 context evidence (term -> ContextTermEvidence),
    # attached by the report generator after parsing.
    context_evidence: dict = field(default_factory=dict)

    @property
    def sections_found(self) -> list[str]:
        return list(self.sections.keys())


def _match_section_header(line: str, header_map: dict[str, list[str]]) -> str | None:
    """Return the canonical section name if this line looks like a header."""
    cleaned = normalize(line).rstrip(":").strip()
    if len(cleaned) > 45:
        return None
    for canonical, variants in header_map.items():
        if cleaned in variants:
            return canonical
    return None


def _is_quantified(line: str) -> bool:
    return any(c.isdigit() for c in line) or "$" in line or "%" in line


def _starts_with_action_verb(line: str, verbs: set[str]) -> bool:
    first = normalize(line).split(" ", 1)[0].rstrip(",.")
    return first in verbs or (first.endswith("ing") and first[:-3] in verbs)


def _vocab_from_packs(disciplines: dict[str, dict]) -> tuple[set[str], set[str]]:
    skills: set[str] = set()
    tools: set[str] = set()
    for pack in disciplines.values():
        skills.update(s.lower() for s in pack.get("core_skills", []))
        tools.update(t.lower() for t in pack.get("tools", []))
    return skills, tools


def _find_with_aliases(text: str, term: str, aliases: dict[str, list[str]]) -> bool:
    if contains_term(text, term):
        return True
    return any(contains_term(text, a) for a in aliases.get(term, []))


def parse_resume(text: str) -> ParsedResume:
    disciplines = knowledge_loader.get_disciplines()
    common = knowledge_loader.get_common()
    header_map = common.get("section_headers", {})
    verbs = set(common.get("action_verbs", []))
    aliases = common.get("skill_aliases", {})

    lines = split_lines(text)
    norm_text = normalize(text)

    # Section detection: walk lines, switching buckets at recognized headers.
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        header = _match_section_header(line, header_map)
        if header:
            current = header
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)

    # Evidence bullets: substantive lines from experience-like sections,
    # or (if no sections were detected) any substantive line in the resume.
    evidence_sections = ["experience", "projects", "leadership", "summary"]
    if sections:
        candidate_lines = [
            ln for name in evidence_sections for ln in sections.get(name, [])
        ]
        # Some resumes put everything under unrecognized headers; fall back.
        if not candidate_lines:
            candidate_lines = lines
    else:
        candidate_lines = lines
    bullets = [ln for ln in candidate_lines if len(ln) >= 30]

    skills_vocab, tools_vocab = _vocab_from_packs(disciplines)
    skills_found = sorted(
        s for s in skills_vocab if _find_with_aliases(norm_text, s, aliases)
    )
    tools_found = sorted(
        t for t in tools_vocab if _find_with_aliases(norm_text, t, aliases)
    )

    # Student-experience signals: union of translation triggers and pack signals.
    signals: set[str] = set()
    for translation in common.get("student_experience_translations", []):
        for sig in translation.get("signals", []):
            if contains_term(norm_text, sig):
                signals.add(sig)
    for pack in disciplines.values():
        for sig in pack.get("student_experience_signals", []):
            if contains_term(norm_text, sig.lower()):
                signals.add(sig.lower())

    return ParsedResume(
        raw_text=text,
        norm_text=norm_text,
        lines=lines,
        sections=sections,
        bullets=bullets,
        skills_found=skills_found,
        tools_found=tools_found,
        student_signals=sorted(signals),
        quantified_bullets=[b for b in bullets if _is_quantified(b)],
        action_verb_bullets=[b for b in bullets if _starts_with_action_verb(b, verbs)],
    )

"""Deterministic job description parser.

Buckets lines into required qualifications, preferred qualifications, and
responsibilities using section headers and inline cue words, then extracts
skills/tools mentioned anywhere in the posting via the knowledge packs.
"""

import re
from dataclasses import dataclass

from . import knowledge_loader
from .text_utils import contains_term, normalize, split_lines

REQUIRED_HEADERS = [
    "requirements", "required qualifications", "minimum qualifications",
    "qualifications", "what you bring", "what you'll bring",
    "must have", "must-haves", "about you", "what we're looking for",
    "what we are looking for", "your background", "you have", "skills and qualifications",
]
PREFERRED_HEADERS = [
    "preferred qualifications", "preferred", "nice to have", "nice-to-haves",
    "assets", "bonus points", "bonus", "additional assets", "it's a plus if",
    "preferred skills",
]
RESPONSIBILITY_HEADERS = [
    "responsibilities", "key responsibilities", "what you'll do", "what you will do",
    "the role", "your role", "duties", "day to day", "day-to-day", "in this role",
    "about the role", "what you'll be doing", "position summary", "job duties",
    "your responsibilities", "core responsibilities", "the opportunity",
    "how you'll succeed", "how you will succeed",
]
# "Who You Are" mixes one or two real requirements (degree, tools) into mostly
# corporate-values language. Route it to a holding bucket that gets filtered
# line-by-line instead of treating everything in it as a hard requirement.
SOFT_HEADERS = ["who you are", "our values", "what we value", "you are someone who"]
# Sections that are neither requirements nor evidence — never scored.
IGNORE_HEADERS = [
    "important information", "what cibc offers", "what we offer", "what's in it for you",
    "whats in it for you", "application instructions", "how to apply", "about us",
    "about the company", "equal opportunity employer", "accommodation",
    "legal disclaimer", "disclaimer", "additional information",
]

PREFERRED_INLINE_CUES = ["preferred", "nice to have", "an asset", "a plus", "bonus"]
REQUIRED_INLINE_CUES = [
    "must", "required", "experience with", "experience in", "proficiency",
    "proficient", "knowledge of", "ability to", "familiarity with",
    "currently enrolled", "working towards", "pursuing a",
]

# Recruitment-process/logistics text — never a requirement or evidence item,
# regardless of which section it lands in.
LOGISTICS_INLINE_CUES = [
    "recruitment timeline", "work location:", "duration of term", "duration:",
    "multiple positions available", "unofficial transcript", "upload your transcript",
    "upload an unofficial", "cover letter", "resume should be no more than",
    "resumes should be no more than", "no more than one page", "application review",
    "interview stage", "offer stage", "open for a limited time",
    "apply as soon as possible", "only those selected", "thank all applicants",
    "we thank all applicants", "competitive compensation", "hybrid work environment",
    "opportunities to build your network", "supportive, inclusive team culture",
    "rolling basis", "interviews held on a rolling basis",
]

# Corporate-values / soft-attribute phrasing that should not count as a hard
# requirement even if it slips outside a recognized SOFT_HEADERS section.
SOFT_VALUE_CUES = [
    "values matter", "you love to learn", "you give meaning to",
    "you engage with purpose", "you bring your real self", "live our values",
    "trust, teamwork", "accountability", "passionate about building relationships",
    "clients first", "building relationships with", "grow your knowledge",
    "create value for our clients", "embrace your strengths", "diverse experiences",
    "unique ambitions", "be your best self", "you enjoy investigating and analyzing",
]

# Degree/enrollment requirement language — matched against the resume's
# Education section by the matching engine, not generic skill terms.
EDUCATION_DEGREE_CUES = [
    "degree in", "currently enrolled", "post-secondary education",
    "pursuing a degree", "working towards a degree", "enrolled in a bachelor",
    "undergraduate degree", "bachelor's degree", "working towards a bachelor",
]

MAX_ITEMS_PER_BUCKET = 12

TITLE_WORDS = [
    "intern", "internship", "co-op", "coop", "analyst", "coordinator", "assistant",
    "associate", "specialist", "representative", "consultant", "student",
]


def _is_logistics_line(line: str) -> bool:
    lowered = normalize(line)
    return any(cue in lowered for cue in LOGISTICS_INLINE_CUES)


def _is_soft_value_line(line: str) -> bool:
    lowered = normalize(line)
    return any(cue in lowered for cue in SOFT_VALUE_CUES)


def _is_education_requirement(line: str) -> bool:
    lowered = normalize(line)
    return any(cue in lowered for cue in EDUCATION_DEGREE_CUES)


def _has_hard_vocab_term(line: str, skills_vocab: set[str], tools_vocab: set[str]) -> bool:
    lowered = normalize(line)
    return any(contains_term(lowered, t) for t in skills_vocab | tools_vocab)


def _drop_fully_subsumed(terms: list[str], text: str) -> list[str]:
    """Drop a shorter term only when every occurrence of it in the text is
    part of a longer detected term ("testing" inside "a/b testing"). A term
    that also occurs on its own elsewhere (e.g. "reporting" alongside a
    separate "regulatory reporting" mention) is kept — they're distinct asks.
    """
    kept: list[str] = []
    for term in terms:
        containing = [other for other in terms if other != term and term in other]
        if not containing:
            kept.append(term)
            continue
        stripped = text
        for other in containing:
            stripped = re.sub(re.escape(other), " ", stripped)
        if contains_term(stripped, term):
            kept.append(term)
    return kept


@dataclass
class ParsedJD:
    raw_text: str
    norm_text: str
    role_title: str | None
    required: list[str]
    preferred: list[str]
    responsibilities: list[str]
    skills: list[str]
    tools: list[str]


def _match_header(line: str, variants: list[str]) -> bool:
    cleaned = normalize(line).rstrip(":").strip()
    if len(cleaned) > 60:
        return False
    return any(cleaned == v or cleaned.startswith(v + " ") or cleaned.endswith(" " + v)
               for v in variants)


def _looks_like_item(line: str) -> bool:
    return 15 <= len(line) <= 350


def _extract_title(lines: list[str]) -> str | None:
    for line in lines[:6]:
        lowered = normalize(line)
        for prefix in ("job title:", "title:", "position:", "role:"):
            if lowered.startswith(prefix):
                return line.split(":", 1)[1].strip()
    for line in lines[:4]:
        lowered = normalize(line)
        if len(line) <= 80 and any(contains_term(lowered, w) for w in TITLE_WORDS):
            return line
    return None


def parse_jd(text: str) -> ParsedJD:
    disciplines = knowledge_loader.get_disciplines()
    common = knowledge_loader.get_common()
    aliases = common.get("skill_aliases", {})

    lines = split_lines(text)
    norm_text = normalize(text)

    # Skills/tools vocabulary, built up front so soft-bucket lines can be
    # checked for a genuine hard-skill mention (used for promotion below).
    skills_vocab: set[str] = set()
    tools_vocab: set[str] = set()
    for pack in disciplines.values():
        skills_vocab.update(s.lower() for s in pack.get("core_skills", []))
        tools_vocab.update(t.lower() for t in pack.get("tools", []))

    required: list[str] = []
    preferred: list[str] = []
    responsibilities: list[str] = []
    soft_lines: list[str] = []

    bucket: list[str] | None = None
    for line in lines:
        if _is_logistics_line(line):
            continue
        # Order matters: ignore first (never scored), then preferred (more
        # specific than the generic "qualifications" required header), then
        # required, then soft attributes, then responsibilities.
        if _match_header(line, IGNORE_HEADERS):
            bucket = None
            continue
        if _match_header(line, PREFERRED_HEADERS):
            bucket = preferred
            continue
        if _match_header(line, REQUIRED_HEADERS):
            bucket = required
            continue
        if _match_header(line, SOFT_HEADERS):
            bucket = soft_lines
            continue
        if _match_header(line, RESPONSIBILITY_HEADERS):
            bucket = responsibilities
            continue
        if bucket is not None and _looks_like_item(line):
            lowered = normalize(line)
            if bucket is soft_lines:
                soft_lines.append(line)
            elif bucket is required and any(c in lowered for c in PREFERRED_INLINE_CUES):
                preferred.append(line)
            elif bucket is not soft_lines and _is_soft_value_line(line) and not (
                _is_education_requirement(line)
                or _has_hard_vocab_term(line, skills_vocab, tools_vocab)
            ):
                # Soft-value phrasing that leaked outside a SOFT_HEADERS
                # section (e.g. under a "Who You Are"-style required header
                # variant we don't recognize by name).
                soft_lines.append(line)
            else:
                bucket.append(line)

    # A "Who You Are" style section usually mixes one real requirement
    # (degree/tool) into mostly values language. Promote the real ones into
    # required; drop the rest — they inform tone, not scoring.
    for line in soft_lines:
        if _is_education_requirement(line) or _has_hard_vocab_term(
            line, skills_vocab, tools_vocab
        ):
            required.append(line)

    # No recognizable headers: fall back to inline cue words so short or
    # messy postings still produce an evidence map.
    if not (required or responsibilities):
        for line in lines:
            if not _looks_like_item(line) or _is_logistics_line(line):
                continue
            lowered = normalize(line)
            if _is_soft_value_line(line) and not (
                _is_education_requirement(line)
                or _has_hard_vocab_term(line, skills_vocab, tools_vocab)
            ):
                continue
            if any(c in lowered for c in PREFERRED_INLINE_CUES):
                preferred.append(line)
            elif any(c in lowered for c in REQUIRED_INLINE_CUES):
                required.append(line)
            else:
                responsibilities.append(line)

    # Skills/tools are scored only from retained requirement/responsibility
    # text — never from logistics, section headers, or dropped soft-value
    # lines, so e.g. "Recruitment timeline" can't surface "recruitment" as a
    # missing HR skill for an unrelated role.
    scored_text = normalize(" ".join(required + preferred + responsibilities))

    def _found(term: str) -> bool:
        if contains_term(scored_text, term):
            return True
        return any(contains_term(scored_text, a) for a in aliases.get(term, []))

    skills = _drop_fully_subsumed(sorted(s for s in skills_vocab if _found(s)), scored_text)
    tools = _drop_fully_subsumed(sorted(t for t in tools_vocab if _found(t)), scored_text)

    return ParsedJD(
        raw_text=text,
        norm_text=norm_text,
        role_title=_extract_title(lines),
        required=required[:MAX_ITEMS_PER_BUCKET],
        preferred=preferred[:MAX_ITEMS_PER_BUCKET],
        responsibilities=responsibilities[:MAX_ITEMS_PER_BUCKET],
        skills=skills,
        tools=tools,
    )

"""Deterministic job description parser.

Buckets lines into required qualifications, preferred qualifications, and
responsibilities using section headers and inline cue words, then extracts
skills/tools mentioned anywhere in the posting via the knowledge packs.
"""

from dataclasses import dataclass

from . import knowledge_loader
from .text_utils import contains_term, normalize, split_lines

REQUIRED_HEADERS = [
    "requirements", "required qualifications", "minimum qualifications",
    "qualifications", "what you bring", "what you'll bring", "who you are",
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
]

PREFERRED_INLINE_CUES = ["preferred", "nice to have", "an asset", "a plus", "bonus"]
REQUIRED_INLINE_CUES = [
    "must", "required", "experience with", "experience in", "proficiency",
    "proficient", "knowledge of", "ability to", "familiarity with",
    "currently enrolled", "working towards", "pursuing a",
]

MAX_ITEMS_PER_BUCKET = 12

TITLE_WORDS = [
    "intern", "internship", "co-op", "coop", "analyst", "coordinator", "assistant",
    "associate", "specialist", "representative", "consultant", "student",
]


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

    required: list[str] = []
    preferred: list[str] = []
    responsibilities: list[str] = []

    bucket: list[str] | None = None
    for line in lines:
        # Preferred headers first: "preferred qualifications" also matches
        # the generic "qualifications" required header.
        if _match_header(line, PREFERRED_HEADERS):
            bucket = preferred
            continue
        if _match_header(line, REQUIRED_HEADERS):
            bucket = required
            continue
        if _match_header(line, RESPONSIBILITY_HEADERS):
            bucket = responsibilities
            continue
        if bucket is not None and _looks_like_item(line):
            lowered = normalize(line)
            if bucket is required and any(c in lowered for c in PREFERRED_INLINE_CUES):
                preferred.append(line)
            else:
                bucket.append(line)

    # No recognizable headers: fall back to inline cue words so short or
    # messy postings still produce an evidence map.
    if not (required or responsibilities):
        for line in lines:
            if not _looks_like_item(line):
                continue
            lowered = normalize(line)
            if any(c in lowered for c in PREFERRED_INLINE_CUES):
                preferred.append(line)
            elif any(c in lowered for c in REQUIRED_INLINE_CUES):
                required.append(line)
            else:
                responsibilities.append(line)

    # Skills/tools mentioned anywhere in the posting.
    skills_vocab: set[str] = set()
    tools_vocab: set[str] = set()
    for pack in disciplines.values():
        skills_vocab.update(s.lower() for s in pack.get("core_skills", []))
        tools_vocab.update(t.lower() for t in pack.get("tools", []))

    def _found(term: str) -> bool:
        if contains_term(norm_text, term):
            return True
        return any(contains_term(norm_text, a) for a in aliases.get(term, []))

    skills = sorted(s for s in skills_vocab if _found(s))
    tools = sorted(t for t in tools_vocab if _found(t))

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

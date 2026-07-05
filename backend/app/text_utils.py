"""Small deterministic text helpers shared by the parsers and matcher."""

import re

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9&/+.#-]*")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_term(text: str, term: str) -> bool:
    """Word-boundary match of a (possibly multi-word) term inside text.

    Both inputs are expected lowercase; `text` should be normalized.
    """
    term = term.lower().strip()
    if not term:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def content_tokens(text: str, stopwords: set[str]) -> set[str]:
    return {t for t in tokenize(text) if t not in stopwords and len(t) > 2}


def clip(text: str, max_len: int = 180) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def split_lines(text: str) -> list[str]:
    """Split raw pasted text into cleaned, non-empty lines."""
    lines = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("•·▪◦*–—-").strip()
        if line:
            lines.append(line)
    return lines

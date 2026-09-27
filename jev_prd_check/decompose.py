"""Break free-form ticket/PRD text into checkable criteria, preferring the
finest structure actually present:

    bullets (each further split by sentence, then phrase)
    > sentences (each further split by phrase)
    > phrases
    > the whole text, if none of the above is recognized

Each tier is a fallback from the one above it, not a separate mode to pick --
a bulleted ticket still gets its bullets refined by sentence/phrase where
that structure exists within a bullet.
"""

from __future__ import annotations

import re

_BULLET_START_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(\S.*)$")
_CONTINUATION_RE = re.compile(r"^\s+(\S.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_PHRASE_SPLIT_RE = re.compile(r"\s*(?:,\s*(?:and|or|but)\s+|;\s+|\s+(?:and|or|but)\s+)\s*", re.IGNORECASE)
_MIN_PHRASE_WORDS = 3


def _clean(fragments: list[str]) -> list[str]:
    return [f.strip().rstrip(",;") for f in fragments if f.strip()]


def split_bullets(text: str) -> list[str] | None:
    """One entry per markdown bullet, including bullets that wrap onto
    indented continuation lines. None if no bullets are present."""
    bullets: list[str] = []
    for line in text.splitlines():
        if m := _BULLET_START_RE.match(line):
            bullets.append(m.group(1).strip())
        elif bullets and line.strip() and (m := _CONTINUATION_RE.match(line)):
            bullets[-1] = f"{bullets[-1]} {m.group(1).strip()}"
    return bullets or None


def split_sentences(text: str) -> list[str] | None:
    """None unless the text actually contains more than one sentence."""
    parts = _clean(_SENTENCE_SPLIT_RE.split(text.strip()))
    return parts if len(parts) > 1 else None


def split_phrases(text: str) -> list[str] | None:
    """Split on coordinating conjunctions/semicolons. Discards fragments too
    short to be a standalone requirement, and returns None unless that
    leaves more than one phrase."""
    parts = _clean(_PHRASE_SPLIT_RE.split(text.strip()))
    parts = [p for p in parts if len(p.split()) >= _MIN_PHRASE_WORDS]
    return parts if len(parts) > 1 else None


def _finest(text: str) -> list[str]:
    sentences = split_sentences(text)
    if sentences:
        out: list[str] = []
        for s in sentences:
            out.extend(split_phrases(s) or [s])
        return out
    phrases = split_phrases(text)
    if phrases:
        return phrases
    stripped = text.strip()
    return [stripped] if stripped else []


def decompose(text: str) -> list[str]:
    bullets = split_bullets(text)
    if bullets:
        out: list[str] = []
        for bullet in bullets:
            out.extend(_finest(bullet))
        return out
    return _finest(text)

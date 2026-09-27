"""Parse a checkpoint-check PRD fixture (see docs/prds/*.md).

Expects a `## Checkpoint range` section with `start_sha`/`end_sha` lines, and
a `## Requirements` section whose bullets become the checkable criteria.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SHA_RE = re.compile(r"`(start|end)_sha`:\s*`([0-9a-f]{7,40})`")
_SECTION_RE = re.compile(r"^##\s+(.*)$")


@dataclass(frozen=True)
class PrdFixture:
    start_sha: str
    end_sha: str
    requirements_text: str


def _sections(markdown: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = None
    for line in markdown.splitlines():
        if m := _SECTION_RE.match(line):
            current = m.group(1).strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def load_prd_fixture(path: str | Path) -> PrdFixture:
    text = Path(path).read_text()
    sections = _sections(text)

    range_section = sections.get("Checkpoint range", "")
    shas = dict(_SHA_RE.findall(range_section))
    if "start" not in shas or "end" not in shas:
        raise ValueError(f"{path}: could not find both start_sha and end_sha in 'Checkpoint range'")

    requirements = sections.get("Requirements")
    if not requirements:
        raise ValueError(f"{path}: no 'Requirements' section found")

    return PrdFixture(start_sha=shas["start"], end_sha=shas["end"], requirements_text=requirements)

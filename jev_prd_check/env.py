"""Tiny .env loader -- no external dependency, since env vars set in the
user's own shell don't reach separate tool invocations anyway."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path) -> None:
    path = Path(path)
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

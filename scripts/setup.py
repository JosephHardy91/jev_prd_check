#!/usr/bin/env python3
"""Interactive setup for jev-prd-check: collects the keys/slugs this plugin
needs and writes them to .env, then prints how to register the plugin with
Claude Code and/or Codex CLI.

Usage:
    .venv/bin/python scripts/setup.py [--codex]

--codex additionally appends codex/config-snippet.toml to
~/.codex/config.toml (asks first; never overwrites without confirmation).
"""

from __future__ import annotations

import argparse
import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

FIELDS = [
    ("TYPESAFE_API_KEY", "TypeSafe API key (for Jev calls)", True),
    ("ADO_ORG_PROJECT", "Azure DevOps org/project (e.g. contoso/kubebot)", False),
    ("ADO_PAT", "Azure DevOps personal access token (Work Items: Read)", True),
]


def _read_existing(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def _prompt(label: str, current: str | None, secret: bool) -> str:
    suffix = " [keep current]" if current else ""
    prompt = f"{label}{suffix}: "
    value = getpass.getpass(prompt) if secret else input(prompt)
    return value.strip() or (current or "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", action="store_true", help="Also offer to register with ~/.codex/config.toml")
    args = parser.parse_args()

    existing = _read_existing(ENV_PATH)
    print(f"Writing to {ENV_PATH}\n(press Enter on any prompt to keep its current value, if set)\n")

    updated = dict(existing)
    for key, label, secret in FIELDS:
        updated[key] = _prompt(label, existing.get(key), secret)

    lines = [f"{key}={value}" for key, value in updated.items() if value]
    ENV_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {len(lines)} value(s) to {ENV_PATH}")

    print(
        "\nClaude Code: install this directory as a plugin (its "
        ".claude-plugin/plugin.json already declares the MCP server and "
        "the SubagentStop/Stop hook) -- e.g. via a local marketplace entry "
        "or `claude plugin install` pointed at this path."
    )

    codex_config = Path.home() / ".codex" / "config.toml"
    snippet_path = PROJECT_ROOT / "codex" / "config-snippet.toml"
    print(f"\nCodex CLI: append {snippet_path} to {codex_config}.")
    if args.codex:
        if not snippet_path.is_file():
            print(f"  (snippet not found at {snippet_path}, skipping)")
        else:
            answer = input(f"  Append it to {codex_config} now? [y/N] ").strip().lower()
            if answer == "y":
                codex_config.parent.mkdir(parents=True, exist_ok=True)
                with codex_config.open("a") as f:
                    f.write("\n" + snippet_path.read_text())
                print(f"  Appended to {codex_config}")
            else:
                print("  Skipped -- copy it in yourself when ready.")


if __name__ == "__main__":
    main()

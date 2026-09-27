#!/usr/bin/env python3
"""Run the checkpoint checker against one kubebot-derived PRD fixture.

Usage:
    .venv/bin/python scripts/run_kubebot_case.py docs/prds/kubebot-tui-source-pane.md
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jev_prd_check.checker import check_checkpoint
from jev_prd_check.env import load_dotenv
from jev_prd_check.prd import load_prd_fixture

KUBEBOT_REPO = Path.home() / "programming" / "kubebot"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def get_diff(start_sha: str, end_sha: str) -> str:
    result = subprocess.run(
        ["git", "diff", f"{start_sha}..{end_sha}"],
        cwd=KUBEBOT_REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prd_path", help="Path to a docs/prds/*.md fixture")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    fixture = load_prd_fixture(args.prd_path)
    diff = get_diff(fixture.start_sha, fixture.end_sha)
    print(f"Loaded fixture: {args.prd_path}")
    print(f"  start_sha={fixture.start_sha}")
    print(f"  end_sha={fixture.end_sha}")
    print(f"  diff: {len(diff.splitlines())} lines")

    if not os.environ.get("TYPESAFE_API_KEY"):
        print("\nTYPESAFE_API_KEY is not set -- stopping before the live Jev call.")
        print("Requirements parsed from the PRD (would become one Noul each):")
        from jev_prd_check.checker import split_criteria

        for i, criterion in enumerate(split_criteria(fixture.requirements_text)):
            print(f"  [{i}] {criterion}")
        return

    from typesafe_sdk import TypeSafeClient

    with TypeSafeClient() as client:
        result = check_checkpoint(fixture.requirements_text, diff, client=client, threshold=args.threshold)

    print(f"\nOverall satisfied: {result.overall_satisfied}")
    for v in result.verdicts:
        mark = "PASS" if v.satisfied else "FAIL"
        print(f"  [{mark}] p={v.probability:.2f}  {v.criterion}")


if __name__ == "__main__":
    main()

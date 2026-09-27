#!/usr/bin/env python3
"""Check the current branch's diff against its ADO ticket via Jev.

Extracts a \\d+ ticket id from the current branch name, fetches that work
item from Azure DevOps, decomposes its text into criteria (bullets, then
sentences, then phrases, falling back to the whole text), and checks the
branch's diff (against --base) for satisfaction of each one.

Usage:
    .venv/bin/python scripts/check_branch.py [--repo PATH] [--base main] [--threshold 0.5]

Config (env vars, or a .env file in this project's root):
    ADO_ORG_PROJECT   "org/project", e.g. "contoso/kubebot"
    ADO_PAT           Azure DevOps personal access token (Work Items: Read)
    TYPESAFE_API_KEY  TypeSafe API key
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jev_prd_check.ado import fetch_ticket
from jev_prd_check.checker import check_checkpoint
from jev_prd_check.decompose import decompose
from jev_prd_check.env import load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TICKET_RE = re.compile(r"\d+")


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def current_branch(repo: Path) -> str:
    return run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def extract_ticket_id(branch: str) -> int:
    m = TICKET_RE.search(branch)
    if not m:
        raise ValueError(f"no ticket id (\\d+) found in branch name {branch!r}")
    return int(m.group())


def branch_diff(repo: Path, base: str) -> str:
    try:
        merge_base = run_git(repo, "merge-base", base, "HEAD")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"could not find base branch {base!r} in {repo}") from e
    return run_git(repo, "diff", f"{merge_base}..HEAD")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="Path to the git repo (default: current directory)")
    parser.add_argument("--base", default="main", help="Base branch to diff against (default: main)")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    load_config(PROJECT_ROOT)

    repo = Path(args.repo).resolve()
    branch = current_branch(repo)
    ticket_id = extract_ticket_id(branch)
    print(f"Branch: {branch}  ->  ticket #{ticket_id}")

    diff = branch_diff(repo, args.base)
    print(f"Diff vs. {args.base}: {len(diff.splitlines())} lines")

    org_project = os.environ.get("ADO_ORG_PROJECT")
    pat = os.environ.get("ADO_PAT")
    if not org_project or not pat:
        print("\nADO_ORG_PROJECT and/or ADO_PAT not set -- stopping before the ADO lookup.")
        return

    ticket = fetch_ticket(org_project, ticket_id, pat=pat)
    print(f"Ticket: {ticket.title}")

    criteria = decompose(ticket.text)
    print(f"Decomposed into {len(criteria)} criteria:")
    for i, c in enumerate(criteria):
        print(f"  [{i}] {c}")

    if not os.environ.get("TYPESAFE_API_KEY"):
        print("\nTYPESAFE_API_KEY not set -- stopping before the live Jev call.")
        return

    from typesafe_sdk import TypeSafeClient

    with TypeSafeClient() as client:
        result = check_checkpoint(ticket.text, diff, client=client, threshold=args.threshold, criteria=criteria)

    print(f"\nOverall satisfied: {result.overall_satisfied}")
    for v in result.verdicts:
        mark = "PASS" if v.satisfied else "FAIL"
        print(f"  [{mark}] p={v.probability:.2f}  {v.criterion}")


if __name__ == "__main__":
    main()

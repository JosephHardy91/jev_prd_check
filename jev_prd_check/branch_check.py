"""Git-branch + ADO-ticket checkpoint check, importable for the MCP server
and the SubagentStop/Stop hook (scripts/check_branch.py is the CLI form of
the same idea, with its own step-by-step console output)."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from jev_prd_check.ado import fetch_ticket
from jev_prd_check.checker import CheckpointResult, check_checkpoint
from jev_prd_check.decompose import decompose

TICKET_RE = re.compile(r"\d+")


class BranchCheckSkipped(Exception):
    """No ticket-numbered branch, or required config missing -- distinct
    from a real error so callers (esp. the hook) can treat it as a no-op
    rather than a failure."""


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def current_branch(repo: Path) -> str:
    return _run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def extract_ticket_id(branch: str) -> int | None:
    m = TICKET_RE.search(branch)
    return int(m.group()) if m else None


def branch_diff(repo: Path, base: str) -> str:
    try:
        merge_base = _run_git(repo, "merge-base", base, "HEAD")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"could not find base branch {base!r} in {repo}") from e
    return _run_git(repo, "diff", f"{merge_base}..HEAD")


@dataclass(frozen=True)
class BranchCheckOutcome:
    branch: str
    ticket_id: int
    ticket_title: str
    diff_lines: int
    result: CheckpointResult


def run_branch_check(repo: str | Path, *, base: str = "main", threshold: float = 0.5) -> BranchCheckOutcome:
    """Raises BranchCheckSkipped when there's no ticket-numbered branch
    checked out, or ADO_ORG_PROJECT/ADO_PAT/TYPESAFE_API_KEY aren't set."""
    repo = Path(repo).resolve()

    try:
        branch = current_branch(repo)
    except subprocess.CalledProcessError as e:
        raise BranchCheckSkipped(f"{repo} is not a git repository") from e

    ticket_id = extract_ticket_id(branch)
    if ticket_id is None:
        raise BranchCheckSkipped(f"no ticket id (\\d+) found in branch name {branch!r}")

    org_project = os.environ.get("ADO_ORG_PROJECT")
    pat = os.environ.get("ADO_PAT")
    if not org_project or not pat:
        raise BranchCheckSkipped("ADO_ORG_PROJECT and/or ADO_PAT not set")
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise BranchCheckSkipped("TYPESAFE_API_KEY not set")

    diff = branch_diff(repo, base)
    ticket = fetch_ticket(org_project, ticket_id, pat=pat)
    criteria = decompose(ticket.text)

    from typesafe_sdk import TypeSafeClient

    with TypeSafeClient() as client:
        result = check_checkpoint(ticket.text, diff, client=client, threshold=threshold, criteria=criteria)

    return BranchCheckOutcome(
        branch=branch,
        ticket_id=ticket_id,
        ticket_title=ticket.title,
        diff_lines=len(diff.splitlines()),
        result=result,
    )

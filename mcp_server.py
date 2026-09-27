#!/usr/bin/env python3
"""jev-prd-check MCP server -- the callable surface shared across agent
harnesses (Claude Code, Codex CLI, anything else that speaks MCP).

This exposes the checker as tools an agent CAN call. It is deliberately
NOT the enforcement mechanism -- see hooks/on_stop.py for the part that
runs whether or not the checked agent chooses to. Use this tool surface
for ad hoc checks (e.g. "am I done yet?"), and the hook for automatic,
non-skippable gating.
"""

from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PLUGIN_ROOT))

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    sys.exit("jev-prd-check: missing dependency (mcp) -- run `pip install -r requirements.txt`")

from jev_prd_check.branch_check import BranchCheckSkipped, run_branch_check  # noqa: E402
from jev_prd_check.env import load_config  # noqa: E402

load_config(PLUGIN_ROOT)

server = MCPServer(
    name="jev-prd-check",
    description="Check whether a git branch's diff satisfies its ADO ticket, via Jev.",
)


@server.tool()
def check_branch(repo: str = ".", base: str = "main", threshold: float = 0.5) -> dict:
    """Check the current branch's diff against its ADO ticket.

    Extracts a ticket id (\\d+) from the branch name, fetches that work item
    from Azure DevOps (config via ADO_ORG_PROJECT/ADO_PAT env vars), and
    checks the diff against `base` for satisfaction of each requirement.

    Args:
        repo: Path to the git repo (default: current directory).
        base: Base branch to diff against (default: "main").
        threshold: Noul probability above which a criterion counts as satisfied.
    """
    try:
        outcome = run_branch_check(repo, base=base, threshold=threshold)
    except BranchCheckSkipped as e:
        return {"skipped": True, "reason": str(e)}

    return {
        "skipped": False,
        "branch": outcome.branch,
        "ticket_id": outcome.ticket_id,
        "ticket_title": outcome.ticket_title,
        "diff_lines": outcome.diff_lines,
        "overall_satisfied": outcome.result.overall_satisfied,
        "verdicts": [
            {"criterion": v.criterion, "probability": v.probability, "satisfied": v.satisfied}
            for v in outcome.result.verdicts
        ],
    }


if __name__ == "__main__":
    server.run(transport="stdio")

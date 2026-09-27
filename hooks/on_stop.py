#!/usr/bin/env python3
"""Shared SubagentStop/Stop hook for Claude Code and Codex CLI.

Both harnesses invoke command hooks the same way: JSON on stdin, JSON on
stdout. This is deliberately NOT a skill the checked agent can choose to
call -- it's registered as a hook, so it runs whether or not the agent
wants it to.

Reads the harness's cwd from stdin (falling back to os.getcwd()), runs the
ADO-ticket branch check there, and:
  - if there's no ticket-numbered branch or required config is missing,
    does nothing (this is a normal, silent no-op, not a failure)
  - if the diff satisfies the ticket, does nothing
  - if it doesn't, returns decision:"block" with the failing criteria as
    the reason, so the harness keeps the agent working instead of
    stopping. Both Claude Code and Codex honor this field the same way.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from jev_prd_check.branch_check import BranchCheckSkipped, run_branch_check  # noqa: E402
from jev_prd_check.env import load_config  # noqa: E402


def _emit(payload: dict) -> None:
    print(json.dumps(payload))


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()
    load_config(PLUGIN_ROOT)
    base = os.environ.get("JEV_BASE_BRANCH", "main")
    threshold = float(os.environ.get("JEV_THRESHOLD", "0.5"))

    try:
        outcome = run_branch_check(cwd, base=base, threshold=threshold)
    except BranchCheckSkipped:
        _emit({"suppressOutput": True})
        return
    except ImportError as e:
        _emit(
            {
                "suppressOutput": True,
                "systemMessage": f"jev-prd-check: missing dependency ({e}) -- run "
                "`pip install -r requirements.txt` from a checkout of the repo.",
            }
        )
        return
    except Exception as e:  # never block the agent because OUR check errored
        _emit({"suppressOutput": True, "systemMessage": f"jev-prd-check error (ignored): {e}"})
        return

    if outcome.result.overall_satisfied:
        _emit({"suppressOutput": True})
        return

    failing = "\n".join(f"- {v.criterion} (p={v.probability:.2f})" for v in outcome.result.failing)
    reason = (
        f"jev checked this branch's diff against ticket #{outcome.ticket_id} "
        f'("{outcome.ticket_title}") and found unmet requirements:\n{failing}\n'
        "Keep working until these are satisfied before stopping."
    )
    _emit(
        {
            "decision": "block",
            "reason": reason,
            "continue": True,
            "hookSpecificOutput": {"hookEventName": "SubagentStop", "additionalContext": reason},
        }
    )


if __name__ == "__main__":
    main()

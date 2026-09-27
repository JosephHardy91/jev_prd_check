# jev-prd-check

Uses Jev to check whether a branch's diff satisfies its ticket, enforced via a SubagentStop/Stop hook so the checked agent can't skip it.

## Setup

1. Install [uv](https://docs.astral.sh/uv/) — dependencies resolve automatically via `uv run`, no pip install or venv needed.
2. Claude Code: `claude plugin marketplace add JosephHardy91/jev_prd_check && claude plugin install jev-prd-check@jev-prd-check`, then `/plugin configure jev-prd-check` in a session to enter your TypeSafe/ADO credentials (or non-interactively: `--config typesafe_api_key=... --config ado_org_project=... --config ado_pat=...` on the install command — leaves secrets in shell history, so prefer `/plugin configure` when that matters).
3. Codex CLI: `python3 scripts/setup.py --codex`

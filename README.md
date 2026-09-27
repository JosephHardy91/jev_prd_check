# jev-prd-check

Uses Jev to check whether a branch's diff satisfies its ticket, enforced via a SubagentStop/Stop hook so the checked agent can't skip it.

## Setup

1. `python3 scripts/setup.py` — writes your TypeSafe/ADO credentials to `~/.config/jev-prd-check/.env`.
2. Install [uv](https://docs.astral.sh/uv/) — dependencies resolve automatically via `uv run`, no pip install or venv needed.
3. Claude Code: `claude plugin marketplace add JosephHardy91/jev_prd_check && claude plugin install jev-prd-check@jev-prd-check`
4. Codex CLI: `python3 scripts/setup.py --codex`

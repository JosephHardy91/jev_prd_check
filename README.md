# jev-prd-check

Checks whether a diff satisfies the PRD/ticket that asked for it, using
[Jev](https://docs.typesafe.ai) (TypeSafe's System One model) to judge each
requirement independently. Scoped to one clean checkpoint at a time: a
single task/ticket and the single diff produced for it.

## Design principle

A check on an agent's own work is only meaningful if that agent can't skip
or bias it. So the core checker is a plain function — never a skill the
checked agent chooses to invoke — and this repo exposes it two different
ways on purpose:

- **An MCP tool** (`mcp_server.py`) — callable on demand, by anything that
  speaks MCP. This is the surface an agent (or a person) can ask "does this
  satisfy the ticket?"
- **A harness hook** (`hooks/on_stop.py`) — runs automatically at
  `SubagentStop`/`Stop`, whether or not the checked agent wants it to. When
  the diff doesn't satisfy the ticket, it tells the harness to keep the
  agent working instead of letting it stop.

Everything else — how requirements get decomposed into checkable criteria,
how the diff is fetched, how a ticket gets looked up — is a supporting
detail behind that split. See `docs/ideas/` for the fuller design rationale
and open questions, and the docstrings in `jev_prd_check/` for how each
piece works today.

## Setup

Run the interactive setup once to collect the credentials this needs:

```
.venv/bin/python scripts/setup.py        # writes .env
.venv/bin/python scripts/setup.py --codex  # also offers to register with Codex
```

Then register the plugin with whichever harness you use.

### Claude Code

The plugin manifest (`.claude-plugin/plugin.json`), `.mcp.json`, and
`hooks/hooks.json` are already set up — no extra files to write. Pick
based on how permanent you want this:

- **Try it for one session**, no install:
  ```
  claude --plugin-dir /path/to/jev_prd_check
  ```
- **Load it every session**, no marketplace: symlink (don't copy — the
  plugin needs to keep seeing this checkout's `.venv` and `.env`) this
  directory into your personal skills directory:
  ```
  ln -s /path/to/jev_prd_check ~/.claude/skills/jev-prd-check
  ```
  Claude Code auto-loads any folder there with a `.claude-plugin/plugin.json`.
- **Share it with a team**, so everyone gets your updates: list it in a
  [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
  — a `marketplace.json` with a `plugins` entry whose `source` points at
  this directory, then `claude plugin marketplace add` + `claude plugin install`.

Verify any of these with `claude plugin validate /path/to/jev_prd_check`,
and check what actually loaded with
`claude --plugin-dir /path/to/jev_prd_check plugin details jev-prd-check`
(should show 2 hooks and 1 MCP server).

### Codex CLI

Append `codex/config-snippet.toml` to `~/.codex/config.toml`
(or let `setup.py --codex` do it).

## Using it directly

```
.venv/bin/python scripts/check_branch.py --repo <path> --base main
```

Run from (or pointed at) a repo checked out on a ticket-numbered branch; it
extracts the ticket id, fetches it from Azure DevOps, and checks the
branch's diff against it. `scripts/run_kubebot_case.py` runs the same
checker against a fixture file instead of a live branch — see
`docs/prds/` for what a fixture looks like and why each one is grounded in
a real issue rather than an invented one. It clones the kubebot repo into
a temp directory and cleans up afterward; pass `--kubebot-repo <path>` to
reuse an existing local checkout instead.

## Layout

| Path | What's there |
|---|---|
| `jev_prd_check/` | The library: checker, criteria decomposition, ADO lookup, branch check, env loading |
| `scripts/` | CLI entry points |
| `hooks/` | Harness hook scripts |
| `mcp_server.py` | The MCP tool surface |
| `.claude-plugin/`, `.mcp.json`, `hooks/hooks.json`, `codex/` | Per-harness registration |
| `docs/ideas/` | Design rationale, assumptions, and deferred future work |
| `docs/prds/` | Ground-truthed test fixtures |

Current scope is one checkpoint at a time (one task, one diff); extending
to multi-checkpoint sessions and a live "implement → check → iterate" loop
are recorded as future work in `docs/ideas/` rather than built yet.

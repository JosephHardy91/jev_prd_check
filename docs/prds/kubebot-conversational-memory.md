# PRD: Conversational memory support

## Provenance

- Source issue: `JosephHardy91/kubebot#2` — "Add conversational memory
  support" (closed, merged via PR #3).
- Requirements below are derived **only** from the original issue text, not
  the merged PR's own description (same rationale as the TUI-source-pane
  fixture: using a diff's own description as its requirement would make
  satisfaction checks trivially pass).
- Retrospective PRD written for checker test data, not a live requirement.

## Checkpoint range

- `start_sha`: `0234fe55c011abcba318ceae541f42f2de672254`
  (merge-base of `main` and the feature branch)
- `end_sha`: `19a4ddf7c88ca560b0af2079ba2071acb48328bf`
  (tip of the feature branch, immediately before merge as PR #3)
- The diff to check is `git diff start_sha..end_sha` in the kubebot repo.

## Objective

Let a user carry on a multi-turn conversation with KubeBot from the
terminal, with the bot remembering earlier context, and invoke it easily.

## Original issue text (verbatim)

> Support long-running user queries with conversational memory within the
> terminal.
>
> Ensure 'kubebot' alias support.

## Requirements

- Within a single terminal session, the assistant retains conversational
  memory across multiple user queries -- a follow-up question can rely on
  context from earlier in that same session.
- Conversation memory persists across long-running use rather than living
  only in transient in-process state that disappears between invocations
  (i.e. some form of session persistence/checkpointing, not just an
  in-memory variable for the life of one process).
- A `kubebot` shell alias is ensured/available so the user can invoke the
  tool directly by that name.

## Open Questions

- The issue doesn't say how long "long-running" should mean in practice
  (minutes vs. days), or where the alias should be installed from -- left
  to the implementer's judgment at the time, and not used as a checkable
  criterion here.

## Ground-Truth Assessment (2026-09-27)

Jev verdict: all 3 criteria PASS (0.87-0.92) -- overall satisfied. Verified
against actual code: `services/memory.py` adds a real `PostgresSaver`
checkpointer (Postgres-backed, survives across invocations, not just
in-process state), and `dev.sh` adds a real `kubebot` bash alias. No flip
needed; all 3 verdicts confirmed correct.

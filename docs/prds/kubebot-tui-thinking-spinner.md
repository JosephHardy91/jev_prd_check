# PRD: Show the bot "thinking" in the TUI

## Provenance

- Source issue: `JosephHardy91/kubebot#5` — 'In the TUI, show the bot
  "thinking"' (closed, merged via PR #17).
- Requirements below are derived **only** from the original issue text, not
  the merged PR's own description.
- Retrospective PRD written for checker test data, not a live requirement.

## Checkpoint range

- `start_sha`: `262468e924a53e454cb20a2db14d402dc341d102`
  (merge-base of `main` and the feature branch)
- `end_sha`: `bde28b7213f5c03687b1baf26c25b31a31acb275`
  (tip of the feature branch, immediately before merge as PR #17)
- The diff to check is `git diff start_sha..end_sha` in the kubebot repo.

## Objective

Give the TUI user visible feedback that KubeBot is actively working on
their question, instead of an unexplained pause.

## Original issue text (verbatim)

> Show each intermediate step (AI Message/Tool Message) in the TUI as a way
> to communicate that the bot is thinking, as a quasi-loading message (with
> a square dot spinner).

## Requirements

- Each intermediate step produced while answering a query (an AI Message or
  a Tool Message) is shown in the TUI, not only the final answer.
- These intermediate steps function as a way of communicating that the bot
  is "thinking" -- i.e. they read as in-progress/loading feedback, not just
  incidental log output.
- The loading indication specifically uses a square dot spinner.

## Open Questions

- The issue doesn't specify how long an intermediate step should remain
  visible before being replaced by the next one, or the final answer --
  left to the implementer's judgment at the time, and not used as a
  checkable criterion here.

## Ground-Truth Assessment (2026-09-27)

Jev verdict: criterion 0 FAIL (p=0.05), criteria 1-2 weak PASS (0.57, 0.60)
-- overall not satisfied. Verified against actual code: the diff only adds
a generic `WheelSpinner` (a `rich.spinner.Spinner("dots12")`) shown/hidden
around one blocking request/response call -- no individual AI/Tool message
is ever rendered as a distinct step. Jev's fail on criterion 0 is correct.

Criteria 1-2's weak passes are defensible standalone (a generic spinner does
read as "thinking" feedback, and "dots12" is a dot-style spinner close to
"square dot"), but this fixture coupled "intermediate steps are shown" and
"those steps communicate thinking" across two separate bullets when the
second depends on the first being true. Not a jev error -- a lesson for
future fixtures: don't split a compound claim across bullets when one
clause presupposes the other. No flip; overall verdict (unsatisfied) is
correct regardless.

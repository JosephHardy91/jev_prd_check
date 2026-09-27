# PRD: TUI with a source pane for the selected answer

## Provenance

- Source issue: `JosephHardy91/kubebot#4` — "Add a TUI with a source pane for
  the selected answer" (closed, merged via PR #6).
- Requirements below are derived **only** from the original issue text.
  The merged PR's own description was deliberately not used as a
  requirements source — copying a diff's own description back as its
  "requirement" would make any satisfaction check trivially pass. This PRD
  exists as a test fixture for a Jev-based checkpoint checker, so it needs
  to reflect what was asked *before* the work, not what was built.
- This is a retrospective PRD written after the fact, for the purpose of
  generating realistic checker test data — not a live product requirement.

## Checkpoint range

- `start_sha`: `4572c6c4889f3999d8687da0bee62cfa3e638883`
  (merge-base of `main` and the feature branch — state before this feature's
  work began)
- `end_sha`: `98440408f1e935aefb3674c0eacf2ca4f965f738`
  (tip of the feature branch, immediately before it was merged into `main`
  as PR #6)
- The diff to check is `git diff start_sha..end_sha` in the kubebot repo.

## Objective

Let a user run KubeBot from a terminal and interactively browse a Q&A
session, seeing the sources behind any answer without leaving the terminal.

## Original issue text (verbatim)

> Typing "kubebot" into terminal or 'kubebot "question here"' should open
> an interactive terminal session that displays the messages in a session
> and allows the user to arrow through system messages. Upon arrival at a
> system message, the sources should be displayed in a right-hand pane (if
> they exist and are retrievable) so the user can deep dive.

## Requirements

- Running `kubebot` with no arguments, or `kubebot "question here"`, opens
  an interactive terminal (TUI) session rather than printing and exiting.
- The TUI displays the messages that make up the session (the running
  history of questions and answers), not just the latest exchange.
- The user can navigate ("arrow through") the system's messages within
  that session.
- When the user arrives at a system message that has retrievable sources,
  those sources are displayed in a right-hand pane.
- The right-hand source pane lets the user view a source's own content in
  more depth ("deep dive"), not merely list its name or a citation label.

## Open Questions

- The issue doesn't specify behavior when a system message has no sources,
  or when sources exist but aren't retrievable — left to the implementer's
  judgment at the time, and not used as a checkable criterion here.

## Ground-Truth Assessment (2026-09-27)

Jev verdict: criteria 1-4 PASS (0.73-0.93), criterion 0 FAIL (p=0.38) --
overall not satisfied. Verified against actual code: at `end_sha`,
`make_local_alias.sh`'s `kubebot` alias is a plain `curl` to `/ask` piped
through `jq`/`glow` -- it never launches the TUI. Jev's fail on criterion 0
is correct. No flip needed; all 5 verdicts confirmed correct.

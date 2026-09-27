# Jev PRD Checkpoint Check

## Problem Statement
How might we, at the close of a single clean agent-work checkpoint (a
start/stop pair — a task in an agent session, or a subagent's begin/end),
use Jev to judge whether the resulting diff actually satisfies the
PRD/task item that opened that checkpoint — without relying on the agent
under test to self-report honestly?

## Recommended Direction
A three-layer design, in order of build priority:

1. **Core checker (pure function, source-agnostic).** Takes `{task_text, diff}`
   for one checkpoint. Never a skill the tested agent invokes on itself — the
   whole point is that it can't be gamed, so it must be called by something
   outside that agent's tool surface (a hook, a harness, CI, a human script).
   Code splits `task_text` into criteria: one per sub-bullet if present,
   otherwise the whole task is one criterion. Jev then asks one **Noul**
   per criterion in a single parallel batch — "does this diff satisfy this
   requirement?" — with `task_text` (for context) and `diff` as shared state.
   Code combines the per-criterion Nouls into an overall verdict (no
   hidden LLM-side aggregation).

2. **Criticality judgment (separate, independent).** A second, decoupled
   Jev judgment (Score or Choice) reads the PRD context and rates the task's
   criticality (e.g. critical-path vs. add-on vs. nice-to-have). This is
   *not* entangled with the satisfaction Nouls — it's askable independently
   and cacheable per task regardless of which diff is being checked against it.

3. **Policy wrapper (the actual "skill").** Maps `(criticality, verdict)` →
   enforcement action — e.g. critical-path failure blocks/gates, add-on
   failure just opens an unmerged PR or logs. This is where org-specific
   usage assumptions live (not Linear-specific — you don't use Linear).
   Kept separate so the core checker stays reusable across whatever
   checkpoint sources show up later (subagent sessions, other trackers).

Test/dev data comes from a clone of the kubebot repo: rewind its commit
history to a point-in-time, take a following range of commits as the
"diff produced for a task," and derive the corresponding PRD task text from
`stories-autogen.md` (synthesizing a task from it where no clean 1:1 mapping
exists). No live agent run needed during development.

## Key Assumptions to Validate
- [ ] Text-only judgment (task + diff, no test execution) is a legitimate,
      independent signal for "did they address the requirement" — not a
      weaker stand-in for behavioral proof. Behavioral tests aren't
      objective ground truth either: someone still chose what to test and
      how, which is its own judgment call. Treat this checker and any
      future "behavioral-jev" (real env, real test run) as two independent
      signals to combine, not a cheap-vs-authoritative pair.
- [ ] Code-level bullet-splitting of `task_text` reliably yields independent,
      checkable criteria — spot-check `stories-autogen.md`'s actual bullet
      style; some bullets may be non-criteria guidance, not requirements.
- [ ] A single small diff fits directly in Jev state with no retrieval step —
      fine at this scope, will break for large diffs later.
- [ ] Noul pass/fail threshold (e.g. p > 0.5 vs. a stricter bar) needs
      empirical tuning against the kubebot-derived examples, not a guess.

## MVP Scope
**In:** core checker as a pure function/library; criteria = sub-bullets-or-one;
one Noul per criterion via a single batched Jev call; code-side combination
into overall verdict; separate criticality judgment; kubebot-based test
harness (checkout two commits, pull/derive task text, run checker, inspect
output) for a handful of manually chosen commit ranges.

**Out (this pass):** the policy wrapper's actual enforcement rules; any live
capture pipeline (hooks into real agent-session boundaries); Linear or any
specific tracker integration; multi-task/multi-checkpoint sessions; running
tests/executing the diff as part of the judgment.

## Not Doing (and Why)
- **Linear integration** — you don't use Linear; building around it would be
  wasted, tracker-specific work the core checker doesn't need.
- **Multi-checkpoint sessions** — explicitly deferred; get one clean
  checkpoint right first, extend later.
- **Executing the diff / running tests** — a distinct future layer
  ("behavioral-jev": real env, real test run) rather than a superior
  replacement for this one. Its own tests carry the same subjectivity
  problem this checker has, just moved to test-authorship time — not
  in scope here, but worth designing as a peer signal later, not a
  ground-truth override.
- **Building the policy/consumption skill now** — premature before the core
  checker is validated against real(ish) data; the criticality→action mapping
  needs a working checker underneath it first.

## Open Questions
- Where does the kubebot repo live (local path or URL to clone)?
- What does `stories-autogen.md` actually look like — one story per task,
  or does it need reshaping into individual PRD task text blocks?
- What Noul confidence threshold counts as "satisfied" — pick a default,
  then tune against the sim data?
- Should criteria decomposition ever use Jev (to judge "is this bullet a
  real criterion?") instead of pure code bullet-splitting, or is that
  overkill for v1?

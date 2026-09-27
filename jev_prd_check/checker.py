"""Core checkpoint checker.

Judges whether a diff satisfies a PRD task, for one clean checkpoint (a
single task_text + a single diff). Deliberately not a Claude Code skill: it
must be callable only by something outside the tested agent's own tool
surface, so the agent under test can't skip or bias the check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient

DEFAULT_THRESHOLD = 0.5

_BULLET_START_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(\S.*)$")
_CONTINUATION_RE = re.compile(r"^\s+(\S.*)$")


def split_criteria(task_text: str) -> list[str]:
    """Split task_text into checkable criteria.

    One criterion per markdown bullet if any are present -- including bullets
    that wrap onto indented continuation lines -- otherwise the whole
    task_text is a single criterion.
    """
    bullets: list[str] = []
    for line in task_text.splitlines():
        if m := _BULLET_START_RE.match(line):
            bullets.append(m.group(1).strip())
        elif bullets and line.strip() and (m := _CONTINUATION_RE.match(line)):
            bullets[-1] = f"{bullets[-1]} {m.group(1).strip()}"
    if bullets:
        return bullets
    stripped = task_text.strip()
    return [stripped] if stripped else []


def build_questions(criteria: list[str]) -> dict[str, Noul]:
    """Each question's instructions quotes the extracted criterion verbatim
    (never a paraphrase or an LLM-rewritten question) and explicitly anchors
    it to `diff`; `task_text` is passed as full, unmodified shared state so
    Jev has the surrounding context an isolated fragment may need.

    Tried moving the "check this against diff" framing out of instructions
    and into criteria's true/false definitions instead (keeping instructions
    as the bare criterion). That regressed a ground-truthed kubebot fixture:
    a criterion that should fail (the diff never wires up launching the TUI)
    went from a confident, correct fail (~0.38) to a stable, wrong pass
    (~0.66-0.71) across repeated calls. Without the explicit anchor in
    instructions, Jev reads it as "is this generally true of the code" rather
    than "does this diff specifically implement it" -- keep the anchor here.
    """
    return {
        f"criterion_{i}": Noul(
            instructions=(
                f'Does the code change in `diff` satisfy this specific requirement: "{criterion}"? '
                "Use `task_text` only for surrounding context -- judge satisfaction of this "
                "requirement alone, not the task as a whole."
            ),
            criteria=NoulCriteria(
                true=(
                    "The diff contains changes that directly implement or fulfill this "
                    "requirement."
                ),
                false=(
                    "The diff does not address this requirement, addresses it only partially "
                    "or superficially, or is unrelated to it."
                ),
            ),
        )
        for i, criterion in enumerate(criteria)
    }


@dataclass(frozen=True)
class CriterionVerdict:
    criterion: str
    probability: float
    satisfied: bool


@dataclass(frozen=True)
class CheckpointResult:
    task_text: str
    diff: str
    verdicts: list[CriterionVerdict]

    @property
    def overall_satisfied(self) -> bool:
        return all(v.satisfied for v in self.verdicts)

    @property
    def failing(self) -> list[CriterionVerdict]:
        return [v for v in self.verdicts if not v.satisfied]


def check_checkpoint(
    task_text: str,
    diff: str,
    *,
    client: TypeSafeClient,
    threshold: float = DEFAULT_THRESHOLD,
    criteria: list[str] | None = None,
) -> CheckpointResult:
    """criteria, if given, overrides the default bullets-or-whole split (see
    jev_prd_check.decompose for a finer bullet/sentence/phrase cascade)."""
    if criteria is None:
        criteria = split_criteria(task_text)
    if not criteria:
        raise ValueError("task_text yielded no checkable criteria")

    questions = build_questions(criteria)
    response = client.system_one(state={"task_text": task_text, "diff": diff}, questions=questions)

    verdicts = [
        CriterionVerdict(
            criterion=criterion,
            probability=(p := response.nouls[f"criterion_{i}"].noul),
            satisfied=p >= threshold,
        )
        for i, criterion in enumerate(criteria)
    ]
    return CheckpointResult(task_text=task_text, diff=diff, verdicts=verdicts)

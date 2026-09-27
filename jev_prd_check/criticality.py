"""Criticality judgment: separate from, and independent of, satisfaction.

Feeds a policy layer (block vs. advisory vs. log-only) that lives outside
this core module -- this only produces the judgment, not the enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import Score, TypeSafeClient

CRITICALITY_LEVELS = [
    "add-on / nice-to-have",
    "important, non-blocking",
    "critical-path / blocker",
]


@dataclass(frozen=True)
class CriticalityResult:
    level: str
    confidence: float


def judge_criticality(
    task_text: str,
    prd_context: str,
    *,
    client: TypeSafeClient,
) -> CriticalityResult:
    response = client.system_one(
        state={"task_text": task_text, "prd_context": prd_context},
        questions={
            "criticality": Score(
                instructions=(
                    "Given `prd_context`, how critical is the specific task described in "
                    "`task_text` to the product's core purpose?"
                ),
                criteria=CRITICALITY_LEVELS,
            )
        },
    )
    result = response.scores["criticality"]
    return CriticalityResult(level=result.score, confidence=result.confidence)

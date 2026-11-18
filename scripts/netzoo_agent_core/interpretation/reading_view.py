"""The reading of a request that routing accepted, as the window shows it ("Understood: ...").

This is the model's own output, and routing uses it, so showing it is showing what the agent worked
from. Only typed fields and quotes are carried: the outcome's closed-vocabulary values, the user's
own words each stated value rests on (only quotes that occur in the request), and which values were
inferred rather than stated. The model's free-text rationale is never carried, because a reason the
code did not act on would read as one it did.
"""

from __future__ import annotations

from .outcome_validation import explicit_evidence_grounded

__all__ = ["reading_view"]

_MAX_HYPOTHESES = 3


def reading_view(hypotheses, user_task: str = "") -> list[dict]:
    """One entry per accepted hypothesis: what was understood, and the words it rests on."""
    view = []
    for hypothesis in list(hypotheses or [])[:_MAX_HYPOTHESES]:
        outcome = hypothesis.outcome
        stated, inferred = [], []
        for item in hypothesis.evidence:
            if item.source == "explicit" and item.text_span:
                if user_task and not explicit_evidence_grounded(user_task, item):
                    continue
                stated.append({"dimension": item.dimension, "value": item.value, "quote": item.text_span})
            elif item.source == "inferred":
                inferred.append({"dimension": item.dimension, "value": item.value})
        view.append({
            "operation": outcome.operation,
            "artifact_type": outcome.artifact_type,
            "granularity": outcome.granularity,
            "regulator_types": list(outcome.regulator_types),
            "input_artifacts": list(outcome.input_artifacts),
            "unresolved": list(outcome.unresolved_dimensions),
            "stated": stated[:8],
            "inferred": inferred[:6],
        })
    return view

"""Fold a step toward the stated patient grouping into the grouping reading (Log 323).

TEST_PROMPTS Test 5 asks to summarize sparse mutations into pathway scores
"and then subtype patients on those scores". The model sometimes writes two
readings: the pathway score matrix, with the mutation input and its quote,
and the patient grouping, without inputs. The grouping goal rule
(`terminal_goal_conflict`) rejects the score reading; dropping it then left
the grouping reading without the input the request states, and the request
fell back (2 of 10 local runs). Its successful runs are one grouping reading
with the mutation input.

When the request states patient grouping and one reading is that grouping, a
reading whose result the grouping workflow also produces on the way (by the
registry: SAMBAR's pathway and gene mutation scores and sample distances) is
folded into it: the step reading goes, and its inputs and the model's own
input evidence join the grouping reading. Nothing is taken from wording
alone; the inputs are the ones the model wrote, as G1(a) already counts a
sibling reading's inputs (Log 242).
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES

from ..routing.capability_compatibility import _supported_artifacts
from .request_integrity import patient_clustering_goal

__all__ = ["fold_intermediate_readings"]

_GROUPING = "sample_cluster_assignment"
_STEPS = frozenset().union(*(
    _supported_artifacts(capability) for capability in OUTPUT_CAPABILITIES.values()
    if _GROUPING in _supported_artifacts(capability)
)) - {_GROUPING}


def fold_intermediate_readings(user_task, interpretation):
    """Return (interpretation, notes); notes is empty when nothing was folded."""
    hypotheses = list(interpretation.outcome_hypotheses)
    goals = [index for index, item in enumerate(hypotheses) if item.outcome.artifact_type == _GROUPING]
    steps = [index for index, item in enumerate(hypotheses) if item.outcome.artifact_type in _STEPS]
    if not goals or not steps or not patient_clustering_goal(user_task):
        return interpretation, []
    target = hypotheses[goals[0]]
    inputs = list(target.outcome.input_artifacts)
    evidence = list(target.evidence)
    notes = []
    for index in steps:
        step = hypotheses[index]
        moved = [value for value in step.outcome.input_artifacts if value not in inputs and value != "unknown"]
        inputs.extend(moved)
        evidence.extend(
            item for item in step.evidence
            if item.dimension == "input_artifact" and item.value in moved
            and not any(own.dimension == item.dimension and own.value == item.value for own in evidence)
        )
        notes.append({"hypothesis": index, "into": goals[0], "artifact": step.outcome.artifact_type,
                      "inputs_moved": moved})
    if "unknown" in inputs and len(inputs) > 1:
        inputs.remove("unknown")
        evidence = [item for item in evidence if not (item.dimension == "input_artifact" and item.value == "unknown")]
    folded = target.model_copy(update={
        "outcome": target.outcome.model_copy(update={"input_artifacts": inputs}),
        "evidence": evidence,
    })
    kept = [folded if index == goals[0] else item for index, item in enumerate(hypotheses) if index not in steps]
    return interpretation.model_copy(update={"outcome_hypotheses": kept}), notes

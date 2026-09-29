"""A reading whose result is only ever a workflow input is not a result (Log 285).

A reading is the model's account of what the request asks for. One whose
result only enters workflows as an input (for example the expression matrix a
survival analysis will be related to) names nothing the registry can produce,
yet it kept a one-candidate tie open. When another reading names a produced
result and still validates on its own, that reading is dropped. The input-only
set is derived from the registry, never listed by hand.
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES

from ..interpretation.outcome_validation import validate_outcome_hypotheses
from .capability_compatibility import _supported_artifacts

_PRODUCED = frozenset().union(*(_supported_artifacts(cap) for cap in OUTPUT_CAPABILITIES.values()))
INPUT_ONLY = frozenset().union(*(cap.input_artifacts for cap in OUTPUT_CAPABILITIES.values())) - _PRODUCED


def drop_input_only_readings(task, interpretation):
    """Rule B. Return (interpretation, dropped artifact types)."""
    readings = interpretation.outcome_hypotheses
    kept = [r for r in readings if r.outcome.artifact_type not in INPUT_ONLY]
    if (len(readings) < 2 or len(kept) == len(readings)
            or not any(r.outcome.artifact_type in _PRODUCED for r in kept)
            or not validate_outcome_hypotheses(task, kept, interpretation.request_mode).valid):
        return interpretation, []
    dropped = [r.outcome.artifact_type for r in readings if r not in kept]
    return interpretation.model_copy(update={"outcome_hypotheses": kept}), dropped

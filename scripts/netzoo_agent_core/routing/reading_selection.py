"""A reading whose result is only ever a workflow input is not a result (Log 285).

A reading is the model's account of what the request asks for. One whose
result only enters workflows as an input (for example the expression matrix a
survival analysis will be related to) names nothing the registry can produce,
yet it kept a one-candidate tie open. When another reading names a produced
result and still validates on its own, that reading is dropped. The input-only
set is derived from the registry, never listed by hand.

Log 313: a reading can also need a fact the request must state. A
multi-omic network needs two omics layers by definition; "microarray
expression profiles ... a separate regulatory network for each patient" (Test
2) got such a reading with no quote, beside the quoted regulatory one, and
LIONESS-DRAGON joined the tie. When the request names no second layer, that
reading is dropped under rule B's guard. Whether a reading lacks a quote is no
guide: the model leaves legitimate readings (TF activity in blind cases 1 and
4) unquoted too.
"""

from __future__ import annotations

import re

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


# A reading's artifact and the words the request must contain for it (Log 313).
# Deliberately loose: a word that might name a second omics layer keeps the
# reading. "protein interaction" is a PPI prior, not a layer.
READING_WITNESSES = {
    "multi_omic_network": re.compile(
        r"omic|methylat|proteom|protein (?:abundance|level|expression)|metabolo|metabolite|lipid|phospho|"
        r"ATAC|chromatin|accessib|histone|ChIP|copy[- ]?number|\bCNVs?\b|genotyp|\bSNPs?\b|microbio|"
        r"small[- ]RNA|mi(?:cro)?[- ]?RNA (?:expression|levels?|profiles?|data)|layers?\b|two (?:data|measurement|assay)|"
        r"多體學|多组学|多組學|甲基化|蛋白質體|蛋白质组|代謝|代谢|染色質|染色质|層|层",
        re.I,
    ),
}


def drop_unwitnessed_readings(task, interpretation):
    """Return (interpretation, dropped artifact types) under rule B's guard."""
    readings = interpretation.outcome_hypotheses
    kept = [r for r in readings
            if (witness := READING_WITNESSES.get(r.outcome.artifact_type)) is None or witness.search(task)]
    if (len(readings) < 2 or not kept or len(kept) == len(readings)
            or not validate_outcome_hypotheses(task, kept, interpretation.request_mode).valid):
        return interpretation, []
    dropped = [r.outcome.artifact_type for r in readings if r not in kept]
    return interpretation.model_copy(update={"outcome_hypotheses": kept}), dropped


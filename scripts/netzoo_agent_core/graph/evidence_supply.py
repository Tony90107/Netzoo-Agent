"""Ask for the missing evidence itself, in a strict schema (Log 196, Log 198).

The T2 failure (Log 183, Log 187): a first pass names an artifact type and a
granularity with no evidence at all, validation reports
``missing_evidence:artifact_type=multi_omic_network``, and the patch that
follows -- asked in its repair feedback to supply evidence for exactly that
pair -- adds evidence for other fields and never for the named one.

Log 196 added required fields to the patch schema; Log 197 found them inert:
in non-strict function calling the model left every required field out, in
12 of 12 calls. So when every first-pass issue is missing evidence for one
hypothesis, the second call keeps the same messages but is answered in a
*strict* schema whose only fields are the named pairs, each one a `Support`
(the strict-compatible quote-or-rationale shape the claims contract uses).

The reply becomes a patch whose only content is those evidence additions, and
takes the ordinary patch path. Nothing else could have been in that patch: a
missing-evidence issue licenses no outcome field (`NO_OUTCOME_FIELDS`), so the
entry justifies the value the first pass wrote and cannot change it.
Validation afterwards is the same as for any interpretation: a quote the
request does not contain still fails, and a granularity against the request's
own witness is rejected however it is justified (Log 196 (b)).
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..contracts.outcomes import SemanticInterpretation
from ..contracts.repair_scope import FIELD_BY_DIMENSION
from ..contracts.semantic_claims import Support

__all__ = ["evidence_supply_schema", "supplied_pairs", "supply_as_patch"]

_MISSING = re.compile(r"^hypothesis\[(\d+)\]\.missing_evidence:([a-z_]+)=(.+)$")
_MAX_PAIRS = 8

Pair = tuple[int, str, str]


def _written(proposal: SemanticInterpretation, pair: Pair) -> bool:
    index, dimension, value = pair
    if index >= len(proposal.outcome_hypotheses) or dimension not in FIELD_BY_DIMENSION:
        return False
    current = getattr(proposal.outcome_hypotheses[index].outcome, FIELD_BY_DIMENSION[dimension])
    return value in current if isinstance(current, list) else current == value


def supplied_pairs(issues, proposal) -> list[Pair] | None:
    """The pairs to ask for, when every issue is evidence the proposal's one hypothesis omitted."""
    pairs: list[Pair] = []
    for issue in issues:
        found = _MISSING.match(str(issue))
        if found is None:
            return None
        pairs.append((int(found.group(1)), found.group(2), found.group(3)))
    pairs = list(dict.fromkeys(pairs))
    if (
        not 0 < len(pairs) <= _MAX_PAIRS
        or len({index for index, _, _ in pairs}) != 1
        or not isinstance(proposal, SemanticInterpretation)
    ):
        return None
    return pairs if all(_written(proposal, pair) for pair in pairs) else None


def evidence_supply_schema(pairs: list[Pair]) -> type[BaseModel]:
    """One required `Support` per pair, named by position and described by the pair."""
    fields = {
        f"evidence_{number}": (Support, Field(description=f"hypothesis[{index}] {dimension}={value}"))
        for number, (index, dimension, value) in enumerate(pairs)
    }
    return create_model("SemanticEvidenceSupply", __config__=ConfigDict(extra="forbid"), **fields)


def supply_as_patch(payload, pairs: list[Pair]) -> dict:
    """The patch this reply amounts to: the supplied entries as evidence additions."""
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(exclude_none=True)
    additions = []
    for number, (_, dimension, value) in enumerate(pairs):
        entry = payload.get(f"evidence_{number}") if isinstance(payload, Mapping) else None
        if isinstance(entry, Mapping):
            additions.append({"dimension": dimension, "value": value, **entry})
    return {"hypothesis_index": pairs[0][0], "evidence_additions": additions}

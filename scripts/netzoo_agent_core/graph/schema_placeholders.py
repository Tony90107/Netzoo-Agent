"""Patch a first pass that failed the schema on two fields, instead of rewriting it (Log 325).

A first pass that does not parse leaves nothing to patch, so the second call
was a whole review -- the worse path (`first_pass_salvage`: 71 of 83 recorded
whole reviews introduced a fresh issue). After Logs 213, 215 and 323, the
recorded first passes that still fail the schema fail on two fields only:

- a hypothesis without `confidence` (40 of 45, every hypothesis at once);
- `outcome.artifact_type` set to a value outside the vocabulary (17; always
  "sample_specific", a granularity).

For these alone a draft is built and handed to the patch, which must write
what is missing. A missing confidence is a placeholder the draft cannot keep:
it is shown to the patch as null, cleared only when a patch writes that
hypothesis's confidence, and a hypothesis still waiting after the last
attempt is dropped -- or, when none has one, the interpretation fails as the
schema error did. The system never keeps a confidence no model wrote, as
`SemanticPatch` promises. An invalid artifact becomes `unknown`, which claims
nothing; its value is named in the issue the patch answers.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field

from pydantic import ValidationError

from ..contracts.repair_scope import Issue
from ..interpretation.outcome_validation import OutcomeValidation, validate_outcome_hypotheses

__all__ = ["PLACEHOLDER_CONFIDENCE", "SchemaPlaceholders", "placeholder_draft"]

#: Only ever inside a draft; see `SchemaPlaceholders.resolve`.
PLACEHOLDER_CONFIDENCE = 0.5


@dataclass
class SchemaPlaceholders:
    confidence: set[int] = field(default_factory=set)
    artifact: dict[int, str] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.confidence or self.artifact)

    def record(self) -> dict:
        return {"confidence": sorted(self.confidence),
                "artifact_type": {str(index): value for index, value in sorted(self.artifact.items())}}

    @classmethod
    def from_record(cls, record) -> "SchemaPlaceholders":
        if not isinstance(record, Mapping):
            return cls()
        return cls(confidence={int(index) for index in record.get("confidence", ())},
                   artifact={int(index): str(value) for index, value in (record.get("artifact_type") or {}).items()})

    def issues(self) -> tuple[Issue, ...]:
        confidence = [Issue(f"hypothesis[{index}].schema_missing:confidence") for index in sorted(self.confidence)]
        artifact = [Issue(f"hypothesis[{index}].schema_invalid_value:artifact_type={value}", {"artifact_type"})
                    for index, value in sorted(self.artifact.items())]
        return (*confidence, *artifact)

    def require(self, validation: OutcomeValidation) -> OutcomeValidation:
        """The validation, rejected while anything is still waiting to be written."""
        if not self:
            return validation
        known = set(validation.issues)
        return OutcomeValidation(
            valid=False,
            issues=(*validation.issues, *(issue for issue in self.issues() if issue not in known)),
            recoverable=False,
            evidence_shapes=validation.evidence_shapes,
        )

    def written(self, index: int | None, patch) -> None:
        """A patch for hypothesis `index` came back; clear what it wrote."""
        if index is None or patch is None:
            return
        if getattr(patch, "confidence", None) is not None:
            self.confidence.discard(index)
        self.artifact.pop(index, None)

    def view(self, proposal):
        """The draft as the patch sees it: a confidence still to write is null."""
        if not self.confidence or not hasattr(proposal, "model_dump"):
            return proposal
        data = proposal.model_dump()
        for index in self.confidence:
            if index < len(data.get("outcome_hypotheses", [])):
                data["outcome_hypotheses"][index]["confidence"] = None
        return data

    def resolve(self, user_task: str, interpretation, validation: OutcomeValidation):
        """After the last attempt: (interpretation, validation, dropped hypothesis indexes)."""
        if not self.confidence:
            return interpretation, validation, []
        hypotheses = interpretation.outcome_hypotheses
        kept = [item for index, item in enumerate(hypotheses) if index not in self.confidence]
        dropped = sorted(index for index in self.confidence if index < len(hypotheses))
        if not kept:
            return interpretation, self.require(validation), []
        reduced = interpretation.model_copy(update={"outcome_hypotheses": kept})
        self.confidence.clear()
        return reduced, validate_outcome_hypotheses(user_task, reduced.outcome_hypotheses, reduced.request_mode), dropped


def _placeholder_fault(error: Mapping) -> tuple[str, int] | None:
    loc = tuple(error.get("loc", ()))
    if (error.get("type") == "missing" and len(loc) == 3 and loc[0] == "outcome_hypotheses"
            and isinstance(loc[1], int) and loc[2] == "confidence"):
        return "confidence", loc[1]
    if (error.get("type") == "literal_error" and len(loc) == 4 and loc[0] == "outcome_hypotheses"
            and isinstance(loc[1], int) and loc[2:] == ("outcome", "artifact_type")
            and isinstance(error.get("input"), str)):
        return "artifact_type", loc[1]
    return None


def placeholder_draft(payload: Mapping, error: ValidationError) -> tuple[dict, SchemaPlaceholders] | None:
    """The payload with placeholders for these two faults, or None when it has neither.

    Other errors are left in place for the next repair (Log 213's evidence
    entries) or for the original located failure.
    """
    hypotheses = payload.get("outcome_hypotheses")
    if not isinstance(hypotheses, list):
        return None
    placeholders = SchemaPlaceholders()
    for item in error.errors():
        fault = _placeholder_fault(item)
        if fault is None:
            continue
        name, index = fault
        if index >= len(hypotheses) or not isinstance(hypotheses[index], Mapping):
            continue
        if name == "confidence":
            placeholders.confidence.add(index)
        else:
            placeholders.artifact[index] = item["input"]
    if not placeholders:
        return None
    draft = deepcopy(dict(payload))
    for index in placeholders.confidence:
        draft["outcome_hypotheses"][index]["confidence"] = PLACEHOLDER_CONFIDENCE
    for index, value in placeholders.artifact.items():
        hypothesis = draft["outcome_hypotheses"][index]
        if isinstance(hypothesis.get("outcome"), dict):
            hypothesis["outcome"]["artifact_type"] = "unknown"
        if isinstance(hypothesis.get("evidence"), list):
            hypothesis["evidence"] = [
                entry for entry in hypothesis["evidence"]
                if not (isinstance(entry, Mapping) and entry.get("dimension") == "artifact_type"
                        and entry.get("value") == value)
            ]
    return draft, placeholders

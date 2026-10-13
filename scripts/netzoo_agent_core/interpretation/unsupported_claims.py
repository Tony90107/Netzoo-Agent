"""What to do with a reading whose only faults are claims it gave no evidence for.

Across 6,275 traced runs, 668 semantic interpretations were discarded after both attempts, and routing fell back
with nothing read. The two largest causes were whole readings thrown away for one unsupported part:

- `missing_evidence` (171 runs, alone): a value the reading set without a quote -- entity_type=gene, a
  granularity of sample_specific, regulator_type=tf -- while everything else it read was grounded;
- `inconsistent_not_applicable_outcome` (94 runs, 14 more beside missing evidence): a vague request ("analyze these
  data and see if anything is biologically meaningful", feasibility eval F36) read as an unknown result of
  not_applicable scale, which the review is then told to reconstruct into a result the request never names.

Here, after the last attempt, only those parts are taken out: each unsupported value becomes unknown (or leaves its
list), a not_applicable scale of an unknown result becomes unknown. The reading is kept only when the same validator
then finds nothing wrong -- every claim left is quoted from the request -- so this never keeps a claim without
evidence; it keeps the claims that have it. A reading with any other fault is discarded as before.
"""

from __future__ import annotations

import re

from ..contracts.outcomes import SemanticInterpretation

__all__ = ["without_unsupported_claims"]

_ISSUE = re.compile(r"^hypothesis\[(\d+)\]\.(missing_evidence:(\w+)=(.+)|inconsistent_not_applicable_outcome)$")
_LISTS = {"entity_type": "entity_types", "regulator_type": "regulator_types", "target_type": "target_types",
          "input_artifact": "input_artifacts", "selection_tag": "selection_tags"}
_SINGLE = {"granularity", "artifact_type", "operation"}


_ROUNDS = 4


def without_unsupported_claims(user_task: str, interpretation: SemanticInterpretation,
                               issues) -> SemanticInterpretation | None:
    """The reading with its unsupported claims taken out, when nothing else was wrong and the rest validates.

    Taking a claim out can leave another one unsupported -- without regulator_type=tf, an entity_type of tf is no
    longer entailed by a role and needs a quote of its own -- so the step repeats, a few rounds at most, while every
    remaining fault is still an unsupported claim.
    """
    from .outcome_validation import validate_outcome_hypotheses

    for _ in range(_ROUNDS):
        reading = _taken_out(interpretation, issues)
        if reading is None:
            return None
        validation = validate_outcome_hypotheses(user_task, reading.outcome_hypotheses, reading.request_mode)
        if validation.valid:
            return reading
        interpretation, issues = reading, validation.issues
    return None


def _taken_out(interpretation: SemanticInterpretation, issues) -> SemanticInterpretation | None:

    drops: dict[int, list[tuple[str, str]]] = {}
    for issue in issues:
        found = _ISSUE.match(str(issue))
        if found is None:
            return None
        index = int(found.group(1))
        if found.group(2) == "inconsistent_not_applicable_outcome":
            drops.setdefault(index, []).append(("granularity", "not_applicable"))
        elif found.group(3) in _LISTS or found.group(3) in _SINGLE:
            drops.setdefault(index, []).append((found.group(3), found.group(4)))
        else:
            return None
    if not drops:
        return None
    hypotheses = list(interpretation.outcome_hypotheses)
    for index, items in drops.items():
        if index >= len(hypotheses):
            return None
        outcome = hypotheses[index].outcome
        update: dict = {}
        for dimension, value in items:
            if dimension in _SINGLE:
                update[dimension] = "unknown"
            else:
                field = _LISTS[dimension]
                current = update.get(field, list(getattr(outcome, field)))
                update[field] = [item for item in current if str(item).casefold() != value.casefold()]
        # The evidence given for a claim taken out (an inferred not_applicable scale) goes with it.
        dropped = {(dimension, value.casefold()) for dimension, value in items}
        evidence = [item for item in hypotheses[index].evidence
                    if (item.dimension, str(item.value).casefold()) not in dropped]
        hypotheses[index] = hypotheses[index].model_copy(update={
            "outcome": outcome.model_copy(update=update), "evidence": evidence})
    return interpretation.model_copy(update={"outcome_hypotheses": hypotheses})

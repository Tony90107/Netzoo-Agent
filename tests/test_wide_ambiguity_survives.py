"""A wholly unresolved outcome must ask, not abort the run.

A live full-corpus round died with `hypothesis_actions:too_long` and produced no
report at all, losing every paid call in it. The cause was a code-owned bound,
not model data: an outcome that resolves nothing is partially compatible with
every registered capability, and the field that carries those candidates was
capped at six while twelve are registered.

Widening it admits no model output -- `CapabilityMatch` is built by the matcher
from the registry -- and it restores the intended behaviour rather than inventing
any, because the caller only ever promotes a lone candidate and a wide tie stays
a clarification question.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    CapabilityMatch, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    _partially_compatible, match_outcome_hypotheses, match_semantic_request,
)
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402


def unresolved() -> RequestedOutcome:
    return RequestedOutcome(operation="unknown", artifact_type="unknown", granularity="unknown")


def test_an_unresolved_outcome_really_is_compatible_with_every_capability():
    """Pins the premise, so the bound below is not tested against a fiction."""
    compatible = [
        action for action, capability in OUTPUT_CAPABILITIES.items()
        if _partially_compatible(unresolved(), capability)
    ]

    assert len(compatible) == len(OUTPUT_CAPABILITIES)


def test_the_candidate_bound_covers_the_whole_registry():
    field = CapabilityMatch.model_fields["hypothesis_actions"]
    bound = next(item.max_length for item in field.metadata if hasattr(item, "max_length"))

    assert bound >= len(OUTPUT_CAPABILITIES)


def test_a_registry_wide_tie_returns_a_question_instead_of_raising():
    hypothesis = OutcomeHypothesis(outcome=unresolved(), confidence=0.5, evidence=[])

    match = match_outcome_hypotheses([hypothesis])

    assert match.status == "ambiguous"
    assert match.matched_actions == []
    assert len(match.hypothesis_actions) == len(OUTPUT_CAPABILITIES)
    assert match.clarification_question


def test_the_production_entry_point_survives_the_same_outcome():
    hypothesis = OutcomeHypothesis(outcome=unresolved(), confidence=0.5, evidence=[])

    match = match_semantic_request("Which workflow should I use?", [hypothesis], request_mode="guidance")

    assert match.status == "ambiguous"
    assert match.matched_actions == []


def _bound(field) -> int | None:
    return next(
        (item.max_length for item in field.metadata if hasattr(item, "max_length")),
        None,
    )


def test_every_contract_the_candidates_are_copied_into_has_the_same_bound():
    """Widening only the producer is what cost the second full-corpus round.

    `assembly` copies `CapabilityMatch.hypothesis_actions` straight into
    `TaskDecision`, whose own cap stayed at six. The run aborted with the same
    `hypothesis_actions:too_long` this file was written for, in a contract this
    file did not look at. Scanning every model that carries the field stops the
    next copy from drifting too.
    """
    import inspect

    from pydantic import BaseModel

    from netzoo_agent_core import contracts

    carriers = {
        f"{module.__name__}.{name}": model
        for module in vars(contracts).values()
        if inspect.ismodule(module)
        for name, model in vars(module).items()
        if inspect.isclass(model)
        and issubclass(model, BaseModel)
        and "hypothesis_actions" in model.model_fields
    }
    # The scan is worthless if it finds nothing; name the models it must cover.
    assert {name.rsplit(".", 1)[-1] for name in carriers} >= {
        "CapabilityMatch", "TaskDecision",
    }

    narrow = {
        name: _bound(model.model_fields["hypothesis_actions"])
        for name, model in carriers.items()
        if (_bound(model.model_fields["hypothesis_actions"]) or 0) < len(OUTPUT_CAPABILITIES)
    }

    assert not narrow, f"bounds behind the registry ({len(OUTPUT_CAPABILITIES)}): {narrow}"

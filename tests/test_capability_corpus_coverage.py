"""Every registered capability must be reachable, and the corpus must reach it.

Two defects this file exists to stop recurring.

A capability can be unreachable by construction: an earlier round found CONDOR
selectable only through a value the prompt reserves for something else, and the
corpus had no case for it, so nothing failed and nobody noticed. PANDA is the
same shape today -- its selection tags are a proper subset of OTTER's and
GIRAFFE's, so no outcome can single it out -- and it is listed below rather than
hidden.

And an expectation can be impossible: adding a corpus case for an unreachable
capability would depress the score forever for a reason that has nothing to do
with the model. So the corpus is checked against reachability, not just parsed.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402

# Reachability is a registry property, not a model one. PANDA, OTTER and GIRAFFE
# now carry distinct algorithmic tags, as do LIONESS-coexpression and BONOBO, so
# a generic output request stays ambiguous while a stated method remains reachable.
# BONOBO's *conditional* unreachability is a different defect and is pinned by
# its own test below rather than listed here. Anything added back needs its
# reason written beside it.
KNOWN_UNREACHABLE: set[str] = set()

TASK = "Which registered workflow should I use? Advice only."


def _best_outcome(action):
    """The outcome that capability's own definition implies, at its own values."""
    capability = OUTPUT_CAPABILITIES[action]
    granularities = capability.granularities or {"aggregate"}
    granularity = "aggregate" if "aggregate" in granularities else sorted(granularities)[0]
    return {
        "operation": capability.operation,
        "input_artifacts": sorted(capability.input_artifacts)[:1],
        "artifact_type": capability.artifact_type,
        "entity_types": [],
        "regulator_types": sorted(capability.regulator_types),
        "target_types": sorted(capability.target_types),
        "selection_tags": sorted(capability.selection_tags),
        "granularity": granularity,
    }


def _match(action):
    hypothesis = OutcomeHypothesis.model_validate(
        {"outcome": _best_outcome(action), "confidence": 0.9, "evidence": []}
    )
    return match_semantic_request(TASK, [hypothesis], request_mode="guidance")


@pytest.mark.parametrize("action", sorted(OUTPUT_CAPABILITIES))
def test_each_capability_is_reachable_or_listed_as_not(action):
    result = _match(action)
    reachable = result.status == "exact" and result.matched_actions == [action]

    if action in KNOWN_UNREACHABLE:
        assert not reachable, (
            f"{action} is now reachable; remove it from KNOWN_UNREACHABLE and "
            "add a corpus case for it."
        )
        return
    assert reachable, (
        f"{action} cannot be singled out by its own definition "
        f"(got {result.status} {result.matched_actions or result.hypothesis_actions}). "
        "Give it a distinguishing selection tag or add it to KNOWN_UNREACHABLE "
        "with the reason."
    )


def test_the_corpus_never_expects_an_unreachable_capability():
    expected = {
        action for case in load_scenarios(DEFAULT_SCENARIOS)
        for action in (case.expected.actions or [])
    }

    assert not expected & KNOWN_UNREACHABLE


def test_the_corpus_covers_every_reachable_capability():
    """Half the registry had no case at all when this was written."""
    expected = {
        action for case in load_scenarios(DEFAULT_SCENARIOS)
        for action in (case.expected.actions or [])
    }
    uncovered = set(OUTPUT_CAPABILITIES) - expected - KNOWN_UNREACHABLE

    assert not uncovered, f"reachable capabilities with no corpus case: {sorted(uncovered)}"


# --- the defect the corpus expansion exposed ---------------------------------

COEXPRESSION_TASK = (
    "Given only a gene expression matrix, I want a separate gene-by-gene "
    "coexpression network for each sample. Advice only."
)


def _coexpression_match(entity_types, selection_tags=()):
    hypothesis = OutcomeHypothesis.model_validate({
        "outcome": {
            "operation": "infer",
            "input_artifacts": ["expression_matrix"],
            "artifact_type": "coexpression_network",
            "entity_types": list(entity_types),
            "regulator_types": [],
            "target_types": [],
            "selection_tags": list(selection_tags),
            "granularity": "sample_specific",
        },
        "confidence": 0.9,
        "evidence": [],
    })
    return match_semantic_request(COEXPRESSION_TASK, [hypothesis], request_mode="guidance")


def test_declaring_sample_an_entity_no_longer_switches_the_recommended_tool():
    """Fourth and final revision; the defect it pinned is fixed.

    It pinned this study's only wrong-tool recommendations -- 3 of 57 trials,
    deterministic, `status = exact` and a semantic basis. The prompt states the
    rule the model broke: a sample-specific result does not by itself make
    `sample` an entity in the result. BONOBO declared `sample` and
    LIONESS-coexpression did not, so breaking that one rule changed the answer.

    Two earlier fixes were withdrawn because removing `sample` made the two tie
    and `_specificity_score` then preferred BONOBO on granularity breadth alone.
    That term is gone: the request names one granularity, both candidates
    support it, and supporting another elsewhere is not evidence. Role and
    entity excess still count, so a `tf`-only request still prefers
    LIONESS-PANDA over LIONESS-PUMA.
    """
    correct = _coexpression_match(["gene"])
    with_sample = _coexpression_match(["gene", "sample"])

    assert with_sample.matched_actions != ["run_bonobo"]
    assert with_sample.matched_actions == correct.matched_actions
    # Neither is preferred on nothing: without a distinguishing tag it asks.
    assert correct.status == "ambiguous"


def test_each_coexpression_capability_is_reached_by_its_own_tag():
    """Algorithmic tags, rather than a subset-order default, decide."""
    assert _coexpression_match(["gene"], ["bayesian"]).matched_actions == ["run_bonobo"]
    assert _coexpression_match(
        ["gene"], ["leave_one_out_network_inference"]
    ).matched_actions == [
        "run_lioness_coexpression",
    ]
    assert _coexpression_match(["gene"], ["coexpression"]).status == "ambiguous"

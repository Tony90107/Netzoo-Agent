"""An exact match has to be the request's doing, not this system's preference.

When several capabilities remain compatible, `_specificity_score` prefers the
one carrying least beyond what was asked. That preference is often right, and it
was also being reported as an *exact* match -- so a trial where the model named
the dimension that actually separates the capabilities scored identically to one
where the harness broke the tie for it. Twenty-four of twenty-seven trials in
one round were the second kind and every one was recorded as fully correct.

The blunt rule -- never exact while more than one candidate remains -- was tried
in an earlier round and rejected, correctly: a `tf`-only request preferring
LIONESS-PANDA over LIONESS-PUMA is a real difference, because PUMA needs miRNA
priors the user does not have. The request did state `regulator_types` there.

So the line drawn here is narrower: the winner must beat the others on the
dimensions the request actually states. Preferences over dimensions it left
empty -- and over `guidance_predecessors`, which an outcome cannot speak to at
all -- may still order candidates, but can no longer certify the answer.

Both halves are pinned below. Losing the first makes the score meaningless
again; losing the second rebuilds the rule that was already rejected once.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.routing.candidate_ranking import (  # noqa: E402
    stated_dimension_score,
)
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_requested_outcome, match_semantic_request,
)
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402


def outcome(**fields) -> RequestedOutcome:
    return RequestedOutcome(**{
        "operation": "infer", "artifact_type": "regulatory_network",
        "granularity": "aggregate", **fields,
    })


def semantic(task="", evidence=(), **fields):
    return match_semantic_request(
        task, [OutcomeHypothesis.model_validate({
            "outcome": outcome(**fields).model_dump(), "confidence": 0.9,
            "evidence": list(evidence),
        })],
        request_mode="guidance",
    )


def test_a_winner_separated_only_by_an_unstated_dimension_is_not_exact():
    """The shape this rule exists for, taken from a live round.

    PUMA and LIONESS-PUMA both carry exactly the regulators and targets this
    request names. With granularity unstated, what separates them is only that
    LIONESS-PUMA has a predecessor step -- nothing the request said anything
    about. Before this rule the answer came back as an exact match for PUMA.

    Until 2026-09-23 this was pinned with `granularity="aggregate"`, on the
    reading that LIONESS-PUMA's declared aggregate output made granularity
    non-separating too. The traced A/B showed that reading cost every explicit
    aggregate miRNA request its answer; the cohort network LIONESS-PUMA reports
    is its PUMA stage's, so a *stated* aggregate now selects PUMA (see
    `test_a_stated_aggregate_selects_the_first_stage_not_the_pipeline`). The
    principle pinned here is unchanged: an unstated dimension certifies nothing.
    """
    match = match_requested_outcome(
        outcome(
            regulator_types=["mirna", "tf"], target_types=["gene"],
            granularity="unknown",
        ),
    )

    assert match.status == "ambiguous"
    assert match.matched_actions == []


def test_a_stated_aggregate_selects_the_first_stage_not_the_pipeline():
    match = match_requested_outcome(
        outcome(regulator_types=["mirna", "tf"], target_types=["gene"]),
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_puma"]


def test_the_request_stating_the_separating_dimension_still_gives_an_exact_match():
    """The case an earlier round used to reject the blunt version of this rule.

    LIONESS-PANDA handles `{tf}`, LIONESS-PUMA `{tf, mirna}`. The request named
    `tf`, so the preference for the narrower one is reading the request, not
    guessing -- and PUMA would need miRNA priors the user never mentioned.
    If this ever flips, the rule has widened back into the one already rejected.
    """
    match = match_requested_outcome(outcome(
        regulator_types=["tf"], target_types=["gene"], granularity="sample_specific",
    ))

    assert match.status == "exact"
    assert match.matched_actions == ["run_lioness_panda"]


def test_a_grounded_tag_the_model_declared_still_discriminates():
    """A model tag discriminates only when it quotes the user's request."""
    match = semantic(
        task="Use iterative message passing to infer the TF regulatory network.",
        evidence=[OutcomeEvidence(
            dimension="selection_tag",
            value="message_passing",
            source="explicit",
            text_span="message passing",
            rationale="The request explicitly names the algorithmic philosophy.",
        )],
        regulator_types=["tf"], target_types=["gene"],
        selection_tags=["message_passing"],
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_panda"]
    assert match.match_basis == "registry_features"


def test_a_sole_compatible_capability_is_still_exact():
    """Nothing was tied, so nothing had to be broken."""
    match = match_requested_outcome(RequestedOutcome(
        operation="analyze", artifact_type="sample_cluster_assignment",
        input_artifacts=["mutation_matrix"], granularity="aggregate",
    ))

    assert match.status == "exact"
    assert match.matched_actions == ["run_sambar"]


def test_the_restricted_score_ignores_every_dimension_the_request_left_empty():
    """The mechanism, stated on its own so its reason cannot drift.

    An empty dimension contributes nothing, which is what makes two capabilities
    differing only there indistinguishable to this score -- and therefore not an
    exact match. `guidance_predecessors` never contributes at all: an outcome
    has no field that could speak to it.
    """
    puma, lioness_puma = OUTPUT_CAPABILITIES["run_puma"], OUTPUT_CAPABILITIES["run_lioness_puma"]
    unstated = outcome(regulator_types=["mirna", "tf"], target_types=["gene"])

    assert stated_dimension_score(unstated, puma) == stated_dimension_score(
        unstated, lioness_puma,
    )

    # And with the separating dimension stated, the score does distinguish them.
    panda = OUTPUT_CAPABILITIES["run_lioness_panda"]
    stated = outcome(regulator_types=["tf"], target_types=["gene"])
    assert stated_dimension_score(stated, panda) < stated_dimension_score(
        stated, lioness_puma,
    )

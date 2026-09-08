"""An accepted `unknown` must say which of two opposite things produced it.

`unknown` needs no evidence, so dropping a value is always a way to dissolve an
`ungrounded_evidence` issue about it, and supplying a quote the request really
contains may be impossible. Nothing recorded so far could tell a dimension the
first pass never committed to from one it committed to and then lost -- and on
that gap a rate measured over three archived rounds was attributed to a citation
failure that none of the trials in it actually had.

These tests pin the three distinctions that make the instrument falsifiable:
a drop is reported, a non-drop is not, "not comparable" is never reported as
"nothing was lost", and every drop carries the first pass's own grounding result
for that exact value.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticInterpretation,
)
from netzoo_agent_core.interpretation.outcome_downgrade import (  # noqa: E402
    interpretation_downgrades,
)
from test_routing_evaluation import FixtureProvider, hypothesis  # noqa: E402


TASK = "Which tool groups patients from somatic mutations using gene length normalization?"


def interpretation(**outcome) -> SemanticInterpretation:
    item = hypothesis()
    item["outcome"].update(outcome)
    return SemanticInterpretation.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Cohort grouping",
        "outcome_hypotheses": [item],
    })


def test_a_value_the_accepted_outcome_no_longer_carries_is_reported():
    report = interpretation_downgrades(
        interpretation(operation="analyze"),
        interpretation(operation="unknown"),
    )

    assert report.comparable
    assert [
        (item["dimension"], item["from_value"], item["to_value"])
        for item in report.downgrades
    ] == [("operation", "analyze", "unknown")]


def test_a_dimension_neither_pass_committed_to_is_not_a_downgrade():
    """The other route to the same `unknown`, and the reason the rate is ambiguous."""
    report = interpretation_downgrades(
        interpretation(operation="unknown"),
        interpretation(operation="unknown"),
    )

    assert report.comparable
    assert report.downgrades == ()


def test_a_drop_carries_the_first_passs_own_grounding_result_for_that_value():
    """Without this the instrument cannot separate the citation contract's

    effect from every other reason a value disappears, which is precisely the
    inference the archived rounds were read as supporting.
    """
    report = interpretation_downgrades(
        interpretation(artifact_type="sample_cluster_assignment", operation="analyze"),
        interpretation(artifact_type="unknown", operation="unknown"),
        [
            {
                "hypothesis": 0,
                "dimension": "artifact_type",
                "value": "sample_cluster_assignment",
                "span": "unmatched",
            },
        ],
    )

    assert {
        item["dimension"]: item["first_pass_span"] for item in report.downgrades
    } == {"artifact_type": "unmatched", "operation": None}


def test_a_grounding_failure_on_a_different_value_is_not_borrowed():
    """The index is keyed on the value too: one dimension can cite two values."""
    report = interpretation_downgrades(
        interpretation(operation="analyze"),
        interpretation(operation="unknown"),
        [{"hypothesis": 0, "dimension": "operation", "value": "infer", "span": "absent"}],
    )

    assert [item["first_pass_span"] for item in report.downgrades] == [None]


def test_an_uncomparable_pair_says_so_instead_of_reporting_no_loss():
    """A whole review returns one hypothesis and no index.

    Against a first pass offering two, nothing says which one it replaced.
    Reporting the empty list alone would be the same conflation this module
    exists to expose, so the flag is what a caller must read first.
    """
    both = interpretation()
    both.outcome_hypotheses.append(hypothesis_model())

    report = interpretation_downgrades(both, interpretation(operation="unknown"))

    assert not report.comparable
    assert report.reason == "hypothesis_correspondence_unknown"
    assert report.downgrades == ()


def test_a_first_pass_that_never_parsed_is_not_compared_against():
    """A schema failure leaves the raw payload, not a typed outcome."""
    report = interpretation_downgrades(
        {"request_mode": "guidance"}, interpretation(operation="unknown"),
    )

    assert not report.comparable
    assert report.reason == "no_parsed_first_pass"


def test_a_patch_is_compared_against_the_hypothesis_it_was_merged_onto():
    both = interpretation(operation="infer")
    both.outcome_hypotheses.append(hypothesis_model(operation="analyze"))

    report = interpretation_downgrades(
        both, interpretation(operation="unknown"), hypothesis_index=1,
    )

    assert report.comparable and report.hypothesis_index == 1
    assert [item["from_value"] for item in report.downgrades] == ["analyze"]


def test_a_list_narrowed_to_another_concrete_value_is_kept_apart_from_abandoned():
    """Only abandoning a dimension loses the commitment; narrowing keeps one."""
    narrowed = interpretation_downgrades(
        interpretation(regulator_types=["tf", "mirna"]),
        interpretation(regulator_types=["mirna"]),
    )
    abandoned = interpretation_downgrades(
        interpretation(regulator_types=["tf"]),
        interpretation(regulator_types=[]),
    )

    assert [item["to_value"] for item in narrowed.downgrades] == ["narrowed"]
    assert [item["to_value"] for item in abandoned.downgrades] == ["empty"]


def hypothesis_model(**outcome):
    item = hypothesis()
    item["outcome"].update(outcome)
    from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis

    return OutcomeHypothesis.model_validate(item)


# --- the same distinctions, as the evaluation report states them --------------


def case() -> RoutingScenario:
    return RoutingScenario.model_validate({
        "id": "downgrade-case", "language": "en", "category": "positive",
        "prompt": TASK,
        "expected": {
            "status": "exact", "actions": ["run_sambar"],
            "input_artifacts": ["mutation_matrix"],
            "artifact_type": "sample_cluster_assignment", "granularity": "aggregate",
        },
    })


def report_for(first, review):
    return evaluate(
        [case()],
        provider=FixtureProvider(
            first={"request_mode": "guidance", "semantic_goal": "Cohort grouping",
                   "outcome_hypotheses": [first]},
            review={"request_mode": "guidance", "semantic_goal": "Cohort grouping",
                    "outcome_hypothesis": review},
        ),
        model_name="fixture",
    )


def test_the_report_separates_a_downgraded_unknown_from_a_never_stated_one():
    stated = hypothesis()
    dropped = hypothesis()
    dropped["outcome"]["operation"] = "unknown"
    dropped["evidence"] = [
        item for item in dropped["evidence"] if item["dimension"] != "operation"
    ]

    downgraded = report_for(stated, dropped)["results"][0]
    never = report_for(dropped, dropped)["results"][0]

    assert downgraded["outcome"]["operation"] == "unknown"
    assert never["outcome"]["operation"] == "unknown"
    assert [entry["origin"] for entry in downgraded["unknown_core"]] == ["downgraded"]
    assert [entry["origin"] for entry in never["unknown_core"]] == ["never_stated"]


def test_the_summary_counts_downgrades_by_dimension_and_grounding_result():
    stated = hypothesis()
    dropped = hypothesis()
    dropped["outcome"]["operation"] = "unknown"
    dropped["evidence"] = [
        item for item in dropped["evidence"] if item["dimension"] != "operation"
    ]

    summary = report_for(stated, dropped)["summary"]

    assert summary["outcome_downgrades"] == {"operation:unknown:grounded": 1}
    assert summary["trials_with_outcome_downgrade"] == 1
    assert summary["trials_with_unknown_core"] == 1
    assert summary["unknown_core_origin"] == {"operation:downgraded:grounded": 1}


def test_a_run_with_nothing_dropped_reports_zero_rather_than_omitting_the_metric():
    """A metric that only appears when it fires cannot show an unchanged rate."""
    summary = report_for(hypothesis(), hypothesis())["summary"]

    assert summary["outcome_downgrades"] == {}
    assert summary["trials_with_outcome_downgrade"] == 0
    assert summary["trials_with_unknown_core"] == 0
    assert summary["downgrade_not_comparable"] == {}


def test_a_value_dropped_after_its_quote_failed_is_recorded_as_such_end_to_end():
    """The mechanism the handoff attributed the 8-12% rate to, exercised whole.

    The first pass cites `artifact_type` with a quote the request does not
    contain, is rejected for it, and the review resolves the rejection by
    setting the field to `unknown` -- which needs no evidence and therefore
    always validates. Every link in that chain has to survive the plumbing for
    the instrument to be able to confirm or refute the attribution on a live
    round; `grounded` here would mean the grounding result never arrived.
    """
    first = hypothesis()
    for item in first["evidence"]:
        if item["dimension"] == "operation":
            item.update(source="explicit", text_span="cluster the patients")

    dropped = hypothesis()
    dropped["outcome"]["operation"] = "unknown"
    dropped["evidence"] = [
        item for item in dropped["evidence"] if item["dimension"] != "operation"
    ]

    report = report_for(first, dropped)
    row = report["results"][0]

    assert any(
        entry.get("attempt") == 1
        and any("ungrounded_evidence:operation" in issue for issue in entry["issues"])
        for entry in row["diagnostic_details"]
    ), "the first pass must have been rejected for the quote, or nothing is being measured"
    assert report["summary"]["outcome_downgrades"] == {
        "operation:unknown:unmatched": 1,
    }
    assert [entry["first_pass_span"] for entry in row["unknown_core"]] == ["unmatched"]

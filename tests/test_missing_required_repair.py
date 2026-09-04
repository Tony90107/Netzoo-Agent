"""Latest observed missing-field failures, distinct from missing evidence."""
import pytest

from test_routing_evaluation import FixtureProvider, hypothesis, run
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation.semantic_repair import repair_feedback


@pytest.mark.parametrize("index,field", [(0, "operation"), (0, "granularity"), (1, "operation")])
def test_missing_field_diagnostic_targets_correct_hypothesis_and_review_path(index, field):
    items = [hypothesis() for _ in range(index + 1)]
    if index:
        items[0]["outcome"]["artifact_type"] = "sample_distance_matrix"
    del items[index]["outcome"][field]
    proposal = {"semantic_goal": "Group patients", "outcome_hypotheses": items}
    issue = f"schema_validation:outcome_hypotheses.{index}.outcome.{field}:missing"
    detail = repair_feedback(proposal, (issue,))[0]
    assert detail["actual"]["artifact_type"] == "sample_cluster_assignment"
    assert detail["location"] == ["outcome_hypotheses", str(index), "outcome", field]
    expected = detail["expected"]
    assert expected["review_path"] == f"outcome_hypothesis.outcome.{field}"
    assert expected["action"] == "add_required_field"
    assert expected["required_fields"] == ["operation", "artifact_type", "granularity"]
    assert expected["field_schema"]["type"] == "string"
    assert "unknown" in expected["field_schema"]["enum"]
    assert "original request" in expected["instruction"]
    assert "evidence" in expected["instruction"]
    assert "default" not in expected["field_schema"]
    with pytest.raises(ValueError):
        SemanticInterpretation.model_validate(proposal)


def test_missing_operation_repair_is_still_rejected_if_reviewer_omits_it():
    item = hypothesis()
    del item["outcome"]["operation"]
    provider = FixtureProvider(first={"semantic_goal": "Grouping", "outcome_hypotheses": [item]},
                               review={"semantic_goal": "Grouping", "outcome_hypothesis": item})
    report = run(provider)
    assert report["summary"]["review_repair_rate"] == 0
    assert report["summary"]["review_repair_validation_rate"] == 0
    assert report["results"][0]["status"] == "fallback"
    assert not report["results"][0]["next_step"]["allow_workflow_continuation"]


def test_latest_replay_reconstructs_exact_observed_schema_issue_locations():
    from pydantic import ValidationError
    from routing_repair_replay import MISSING_REQUIRED_ISSUES, reconstructed_proposal
    for case, expected in MISSING_REQUIRED_ISSUES.items():
        with pytest.raises(ValidationError) as error:
            SemanticInterpretation.model_validate(reconstructed_proposal(case, "missing-required"))
        actual = ["schema_validation:" + ".".join(str(part) for part in item["loc"]) + ":" + item["type"]
                  for item in error.value.errors()]
        assert actual == expected


def test_latest_replay_selection_requires_opt_in_and_has_distinct_metadata(monkeypatch, capsys):
    import json
    from evaluate_routing import main
    monkeypatch.setattr("evaluate_routing.build_llm", lambda *_a, **_kw: pytest.fail("Unexpected provider call"))
    assert main(["--repair-replay-suite", "missing-required"]) == 2
    assert main(["--repair-replay", "--repair-replay-suite", "missing-required", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "corpus_validation_only" and report["cases"] == 3
    assert report["repair_replay_suite"] == "missing-required"

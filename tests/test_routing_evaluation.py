"""Offline evaluation-harness contracts, not measurements of model accuracy."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import (  # noqa: E402
    DEFAULT_SCENARIOS, RoutingScenario, evaluate, load_scenarios, main,
)
from netzoo_agent_core.contracts import IntentDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticInterpretation, SemanticReview,
)


TASK = "Which tool groups patients from somatic mutations using gene length normalization?"


def scenario(**expected):
    return RoutingScenario.model_validate({
        "id": "synthetic-case", "language": "en", "category": "positive",
        "prompt": TASK,
        "expected": {
            "status": "exact", "actions": ["run_sambar"],
            "input_artifacts": ["mutation_matrix"],
            "artifact_type": "sample_cluster_assignment", "granularity": "aggregate",
            **expected,
        },
    })


def hypothesis():
    return {
        "outcome": {
            "operation": "analyze", "input_artifacts": ["mutation_matrix"],
            "artifact_type": "sample_cluster_assignment", "entity_types": ["sample"],
            "granularity": "aggregate",
        },
        "confidence": 0.95,
        "evidence": [
            {"dimension": dimension, "value": value, "source": "explicit" if span else "inferred",
             "text_span": span, "rationale": "The user requests one cohort grouping."}
            for dimension, value, span in (
                ("operation", "analyze", None),
                ("input_artifact", "mutation_matrix", "somatic mutations"),
                ("artifact_type", "sample_cluster_assignment", "groups patients"),
                ("entity_type", "sample", "patients"),
                ("granularity", "aggregate", None),
            )
        ],
    }


class FixtureProvider:
    """Independent scripted transport responses; never consult case expectations."""

    def __init__(self, *, first=None, review=None, intent=None):
        item = hypothesis()
        self.responses = {
            SemanticInterpretation: first if first is not None else {
                "request_mode": "guidance", "semantic_goal": "Cohort grouping",
                "outcome_hypotheses": [item],
            },
            SemanticReview: review if review is not None else {
                "request_mode": "guidance", "semantic_goal": "Cohort grouping",
                "outcome_hypothesis": item,
            },
            IntentDecision: intent if intent is not None else {
                "mode": "answer", "confidence": 0.95, "reason": "Guidance only.",
            },
        }
        self.calls = []

    def with_structured_output(self, schema, **kwargs):
        assert kwargs == {"method": "function_calling", "include_raw": schema is not IntentDecision}
        provider = self

        class Adapter:
            def invoke(self, messages):
                provider.calls.append((schema, messages))
                result = provider.responses[schema]
                if isinstance(result, BaseException):
                    raise result
                return result

        return Adapter()


def run(provider, case=None, **kwargs):
    return evaluate([case or scenario()], provider=provider, model_name="fixture", **kwargs)


def test_production_routing_boundary_receives_only_prompt_not_answer_key():
    provider = FixtureProvider()
    report = run(provider)
    result = report["results"][0]

    assert result["passed"]
    assert result["semantic_passed"]
    assert result["route_passed"]
    assert result["path"] == "semantic_registry_intent"
    assert result["call_roles"] == ["semantic_interpreter", "semantic_reviewer", "intent_router"]
    assert report["summary"]["unsafe_execution_count"] == 0
    assert report["summary"]["semantic_pass_rate"] == 1
    assert report["metadata"]["source"] == "fixture"
    assert report["metadata"]["prompt_schema_sha256"]
    first_messages = provider.calls[0][1]
    assert any(message.content == TASK for message in first_messages)
    assert "run_sambar" not in "\n".join(str(m.content) for m in first_messages)
    assert "synthetic-case" not in "\n".join(str(m.content) for m in first_messages)


def test_provider_value_error_recovery_is_not_counted_as_semantic_success():
    provider = FixtureProvider(first=ValueError("sensitive provider detail"))
    report = run(provider)
    result = report["results"][0]

    assert not result["route_passed"]  # A fallback is not the expected exact match.
    assert result["status"] == "fallback"
    assert result["matched_actions"] == ["run_sambar"]
    assert result["answer_passed"]
    assert "Fallback recommendation" in result["answer"]
    assert not result["semantic_passed"]
    assert not result["passed"]
    assert result["path"] == "registry_recovery"
    assert report["summary"]["registry_recovery_count"] == 1
    assert report["summary"]["semantic_pass_rate"] == 0
    assert len(provider.calls) == 1
    assert "provider" in result["diagnostics"]
    assert "sensitive provider detail" not in json.dumps(report)


def test_transport_outage_fails_closed_without_review_or_intent_calls():
    provider = FixtureProvider(first=TimeoutError("sensitive provider detail"))
    result = run(provider)["results"][0]

    assert not result["passed"]
    assert not result["route_passed"]
    assert result["path"] == "semantic_fallback"
    assert result["diagnostics"] == ["provider"]
    assert len(provider.calls) == 1
    assert not result["should_execute"]


def test_schema_failure_gets_one_review_repair_and_is_reported():
    provider = FixtureProvider(first={"outcome_hypotheses": []})
    result = run(provider)["results"][0]

    assert result["passed"]
    assert "schema_validation" in result["diagnostics"]
    assert len(provider.calls) == 3
    assert "schema_validation" in str(provider.calls[1][1][-1].content)


def test_unrepaired_quotes_fail_semantic_metric_even_when_fallback_selects_tool():
    item = hypothesis()
    item["evidence"][1]["text_span"] = "This text is absent from the request"
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypothesis": item},
    )
    result = run(provider)["results"][0]

    assert not result["passed"]
    assert not result["semantic_passed"]
    assert not result["route_passed"]
    assert result["status"] == "fallback"
    assert "evidence_validation" in result["diagnostics"]
    assert len(provider.calls) == 2
    assert result["should_execute"] is False


def test_cross_field_semantic_failure_reaches_safe_final_guidance():
    item = hypothesis()
    item["outcome"].update(entity_types=["gene"], granularity="sample_specific")
    for evidence in item["evidence"]:
        if evidence["dimension"] in {"entity_type", "granularity"}:
            evidence.update(value="gene" if evidence["dimension"] == "entity_type" else "sample_specific",
                            source="inferred", text_span=None)
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypothesis": item},
    )
    result = run(provider)["results"][0]
    assert not result["semantic_passed"]
    assert result["status"] == "fallback"
    assert result["answer_evaluated"] and result["answer_passed"]
    assert "not an exact semantic match" in result["answer"]
    assert "`sample_cluster_assignment`: Sample-to-cluster labels" in result["answer"]
    assert len(provider.calls) == 2


@pytest.mark.parametrize("bad_answer", [
    "Using LIONESS with mutation data is a valid approach. However, do not use it.",
    "The pathway_mutation_matrix contains cluster labels.",
    "You can indeed use PANDA, but it does not accept mutations.",
])
def test_final_answer_failure_cannot_hide_behind_correct_routing(monkeypatch, bad_answer):
    from netzoo_agent_core.contracts import AIMessage
    monkeypatch.setattr("evaluate_routing.respond", lambda *_: {"messages": [AIMessage(content=bad_answer)]})
    report = evaluate([scenario(
        answer_required=["`sample_cluster_assignment`: Sample-to-cluster labels"],
        answer_forbidden=["is a valid approach", "you can indeed use"],
    )], provider=FixtureProvider(), model_name="fixture")
    row = report["results"][0]
    assert row["route_passed"] and row["semantic_passed"]
    assert not row["answer_passed"] and not row["passed"]
    assert report["summary"]["answer_failure_count"] == 1


def test_valid_but_wrong_semantics_do_not_pass_on_action_name_alone():
    provider = FixtureProvider()
    result = run(provider, scenario(artifact_type="sample_distance_matrix"))["results"][0]

    assert result["route_passed"]
    assert not result["semantic_passed"]
    assert not result["passed"]
    assert "artifact_type" in " ".join(result["errors"])


def test_guidance_blocks_misclassified_execute_intent():
    provider = FixtureProvider(intent={"mode": "execute", "confidence": 1, "reason": "Wrong intent."})
    result = run(provider)["results"][0]

    assert result["passed"]
    assert result["should_execute"] is False
    assert result["action"] == "no_tool"


def test_joint_semantic_and_intent_misclassification_does_not_pass_semantics():
    provider = FixtureProvider(intent={"mode": "execute", "confidence": 1, "reason": "Wrong intent."})
    provider.responses[SemanticInterpretation]["request_mode"] = "execute"
    provider.responses[SemanticReview]["request_mode"] = "execute"
    report = run(provider)

    # The existing task-text execution guard also rejects this question.
    assert report["summary"]["unsafe_execution_count"] == 0
    assert not report["results"][0]["passed"]
    assert "request_mode:" in " ".join(report["results"][0]["errors"])
    assert len(provider.calls) == 3


def test_scorer_catches_an_unsafe_decision_even_if_other_dimensions_pass(monkeypatch):
    from dataclasses import replace
    from evaluate_routing import invoke_router

    def unsafe_route(*args, **kwargs):
        result = invoke_router(*args, **kwargs)
        return replace(result, decision=result.decision.model_copy(update={
            "should_execute": True, "action": "run_sambar",
        }))

    # A deliberately corrupted boundary result tests the evaluator's safety oracle.
    monkeypatch.setattr("evaluate_routing.invoke_router", unsafe_route)
    report = run(FixtureProvider())

    assert report["summary"]["unsafe_execution_count"] == 1
    assert report["results"][0]["route_passed"]
    assert report["results"][0]["semantic_passed"]
    assert not report["results"][0]["passed"]
    assert "execution:" in " ".join(report["results"][0]["errors"])


def test_intent_failure_remains_distinct_from_successful_semantics():
    result = run(FixtureProvider(intent=TimeoutError("private")))["results"][0]

    assert result["semantic_passed"]
    assert not result["passed"]
    assert "intent" in result["diagnostics"]
    assert not result["should_execute"]


def test_budget_exhaustion_fails_without_any_provider_call():
    provider = FixtureProvider()
    result = run(provider, task_token_budget=1)["results"][0]

    assert not result["passed"]
    assert provider.calls == []
    assert "budget" in result["diagnostics"]


def test_repeated_trials_use_fresh_usage_and_report_denominator():
    provider = FixtureProvider()
    report = run(provider, repeat=3)

    assert report["summary"]["cases"] == 1
    assert report["summary"]["trials"] == report["summary"]["passed"] == 3
    assert report["summary"]["provider_calls"] == 9
    assert len(provider.calls) == 9
    assert report["summary"]["unstable_cases"] == []
    assert report["summary"]["by_language"]["en"] == {"trials": 3, "passed": 3, "pass_rate": 1}
    assert [item["trial"] for item in report["results"]] == [1, 2, 3]


def test_repeated_semantic_drift_is_visible_even_when_the_action_stays_correct():
    import copy

    class AlternatingProvider(FixtureProvider):
        reviews = 0

        def with_structured_output(self, schema, **kwargs):
            base = super().with_structured_output(schema, **kwargs)
            provider = self

            class Adapter:
                def invoke(self, messages):
                    result = copy.deepcopy(base.invoke(messages))
                    if schema is SemanticReview:
                        provider.reviews += 1
                        if provider.reviews % 2 == 0:
                            item = result["outcome_hypothesis"]
                            item["outcome"]["artifact_type"] = "sample_distance_matrix"
                            for evidence in item["evidence"]:
                                if evidence["dimension"] == "artifact_type":
                                    evidence.update(value="sample_distance_matrix", source="inferred", text_span=None)
                    return result

            return Adapter()

    report = run(AlternatingProvider(), repeat=2)

    assert report["summary"]["route_pass_rate"] == 1
    assert report["summary"]["semantic_pass_rate"] == 0.5
    assert report["summary"]["unstable_cases"] == ["synthetic-case"]


def test_empty_duplicate_and_unknown_action_corpora_are_rejected(tmp_path):
    path = tmp_path / "cases.json"
    for payload in ([], [scenario().model_dump()] * 2, [{
        **scenario().model_dump(), "expected": {"status": "exact", "actions": ["run_invented"]},
    }]):
        path.write_text(json.dumps(payload))
        with pytest.raises(ValueError):
            load_scenarios(path)


def test_default_cli_validates_corpus_without_building_a_provider(monkeypatch, capsys):
    monkeypatch.setattr("evaluate_routing.build_llm", lambda *_a, **_kw: pytest.fail("live call without opt-in"))
    assert main(["--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "corpus_validation_only"
    assert "pass_rate" not in report
    assert report["cases"] >= 12


def test_live_call_cap_and_unknown_case_fail_before_provider_construction(monkeypatch):
    monkeypatch.setattr("evaluate_routing.build_llm", lambda *_a, **_kw: pytest.fail("must validate first"))
    for args in (["--live", "--max-calls", "1"], ["--case", "does-not-exist"]):
        assert main(args) == 2


@pytest.mark.parametrize("failed,exit_code", [(False, 0), (True, 1)])
def test_live_cli_exit_status_uses_all_trials_not_just_recommended_action(
    monkeypatch, tmp_path, capsys, failed, exit_code,
):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([scenario().model_dump()]))
    provider = FixtureProvider(first=ValueError("private")) if failed else FixtureProvider()
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture-not-a-real-key")
    monkeypatch.setattr("evaluate_routing.build_llm", lambda *_a, **_kw: provider)

    assert main(["--scenarios", str(path), "--live", "--json"]) == exit_code
    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["route_pass_rate"] == (0 if failed else 1)
    assert report["summary"]["passed"] == (0 if failed else 1)


def test_provider_setup_errors_are_redacted(monkeypatch, tmp_path, capsys):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([scenario().model_dump()]))
    monkeypatch.setenv("OPENROUTER_API_KEY", "fixture-not-a-real-key")

    def broken_setup(*_args, **_kwargs):
        raise ValueError("sensitive provider setup payload")

    monkeypatch.setattr("evaluate_routing.build_llm", broken_setup)
    assert main(["--scenarios", str(path), "--live"]) == 2
    assert "sensitive provider" not in capsys.readouterr().err


def test_public_corpus_covers_original_prompts_and_negative_controls():
    cases = load_scenarios(DEFAULT_SCENARIOS)
    assert {"original-q1", "original-q2", "original-q3"}.issubset({case.id for case in cases})
    assert {"en", "zh", "mixed"}.issubset({case.language for case in cases})
    assert {"positive", "negative", "history", "paraphrase"}.issubset({case.category for case in cases})
    assert len({action for case in cases for action in case.expected.actions}) >= 5

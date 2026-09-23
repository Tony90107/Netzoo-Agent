"""Offline evaluation-harness contracts, not measurements of model accuracy."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import (  # noqa: E402
    DEFAULT_SCENARIOS, RoutingScenario, _review_patch_payload, evaluate, load_scenarios, main,
)
from netzoo_agent_core.contracts import IntentDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticDiscriminator, SemanticInterpretation, SemanticPatch, SemanticReview,
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
        # 2026-09-06: the second semantic call now asks for a SemanticPatch. These
        # scripted transports keep answering with the complete review shape, which
        # production still accepts, so every existing assertion keeps testing what
        # it named. tests/test_semantic_patch_repair.py scripts the patch shape.
        self.responses[SemanticPatch] = self.responses[SemanticReview]
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


def test_claims_evaluation_uses_the_same_strict_binding_as_production():
    bindings = []

    class InvalidProvider:
        def with_structured_output(self, schema, **kwargs):
            bindings.append((schema.__name__, kwargs))

            class Adapter:
                def invoke(self, messages):
                    return {}

            return Adapter()

    report = run(InvalidProvider(), semantic_contract="claims")

    claim_bindings = [
        kwargs
        for name, kwargs in bindings
        if name in {"SemanticClaims", "SemanticClaimRepair"}
    ]
    assert report["metadata"]["semantic_contract"] == "claims"
    assert claim_bindings and all(kwargs.get("strict") is True for kwargs in claim_bindings)


def test_claim_patch_event_is_scored_without_legacy_only_fields():
    event = {
        "payload": {
            "attempt": 2,
            "repairs": [
                {"hypothesis_index": 0, "changed_fields": ["granularity"]}
            ],
        }
    }

    assert _review_patch_payload(event) == {
        "repairs": [{"hypothesis_index": 0, "changed_fields": ["granularity"]}]
    }


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


def test_discriminator_contract_can_select_otter_from_a_validated_panda_tie():
    task = (
        "I have an expression matrix, motif priors and PPI data. Infer one aggregate "
        "TF-gene regulatory network with continuous relaxed graph matching rather than "
        "message passing. Which tool fits?"
    )
    item = {
        "outcome": {
            "operation": "infer",
            "input_artifacts": ["expression_matrix"],
            "artifact_type": "regulatory_network",
            "entity_types": ["tf", "gene"],
            "regulator_types": ["tf"],
            "target_types": ["gene"],
            "selection_tags": [],
            "granularity": "aggregate",
        },
        "confidence": 0.95,
        "evidence": [
            {"dimension": "operation", "value": "infer", "source": "inferred", "rationale": "The request asks to infer a network."},
            {"dimension": "input_artifact", "value": "expression_matrix", "source": "explicit", "text_span": "expression matrix", "rationale": "The request supplies an expression matrix."},
            {"dimension": "artifact_type", "value": "regulatory_network", "source": "explicit", "text_span": "regulatory network", "rationale": "The request asks for a regulatory network."},
            {"dimension": "regulator_type", "value": "tf", "source": "inferred", "rationale": "TF-gene identifies TF regulators."},
            {"dimension": "target_type", "value": "gene", "source": "inferred", "rationale": "TF-gene identifies gene targets."},
            {"dimension": "granularity", "value": "aggregate", "source": "inferred", "rationale": "The request asks for one aggregate network."},
        ],
    }
    provider = FixtureProvider(first={
        "request_mode": "guidance", "semantic_goal": "Infer an aggregate TF-gene network",
        "outcome_hypotheses": [item],
    })
    provider.responses[SemanticPatch] = {"outcome": {}}
    provider.responses[SemanticDiscriminator] = {
        "selection_tags": ["relaxed_graph_matching"],
        "evidence": [{
            "dimension": "selection_tag", "value": "relaxed_graph_matching",
            "source": "explicit", "text_span": "continuous relaxed graph matching",
            "rationale": "The request explicitly contrasts relaxed graph matching with message passing.",
        }],
    }
    case = RoutingScenario.model_validate({
        "id": "discriminator-otter", "language": "en", "category": "positive",
        "prompt": task,
        "expected": {
            "status": "exact", "actions": ["run_otter"],
            "input_artifacts": ["expression_matrix"],
            "artifact_type": "regulatory_network", "granularity": "aggregate",
            "required_discriminators": {"selection_tags": ["relaxed_graph_matching"]},
        },
    })

    report = evaluate([case], provider=provider, model_name="fixture")
    result = report["results"][0]

    assert result["route_passed"], result
    assert result["semantic_passed"]
    assert result["matched_actions"] == ["run_otter"]
    assert [schema.__name__ for schema, _ in provider.calls] == [
        "SemanticInterpretation", "SemanticPatch", "SemanticDiscriminator", "IntentDecision",
    ]


def test_not_applicable_recovery_preserves_chinese_otter_constraints():
    """A malformed first reading must not erase the stated scientific goal."""
    task = (
        "我想要建構一個基因調控網路，希望模型在求解時有明確的損失函數、正則化項，"
        "並以目標函數鬆弛化的推論架構完成。請問哪個演算法適合？"
    )
    empty = {
        "outcome": {
            "operation": "explain", "input_artifacts": [], "artifact_type": "unknown",
            "entity_types": [], "regulator_types": [], "target_types": [],
            "selection_tags": [], "granularity": "not_applicable",
        },
        "confidence": 0.8,
        "evidence": [{
            "dimension": "operation", "value": "explain", "source": "explicit",
            "text_span": "請問哪個演算法適合？", "rationale": "The user asks for guidance.",
        }],
    }
    recovered = {
        "outcome": {
            "operation": "infer", "input_artifacts": [], "artifact_type": "regulatory_network",
            "entity_types": ["tf", "gene"], "regulator_types": ["tf"], "target_types": ["gene"],
            "selection_tags": [], "granularity": "aggregate",
        },
        "confidence": 0.9,
        "evidence": [
            {"dimension": "operation", "value": "infer", "source": "inferred", "rationale": "The requested model constructs a network."},
            {"dimension": "artifact_type", "value": "regulatory_network", "source": "explicit", "text_span": "基因調控網路", "rationale": "The terminal result is a regulatory network."},
            {"dimension": "regulator_type", "value": "tf", "source": "inferred", "rationale": "Regulatory-network roles are TF to gene."},
            {"dimension": "target_type", "value": "gene", "source": "inferred", "rationale": "Regulatory-network roles are TF to gene."},
            {"dimension": "granularity", "value": "aggregate", "source": "inferred", "rationale": "一個 network requests one aggregate result."},
        ],
    }
    provider = FixtureProvider(first={
        "request_mode": "guidance", "semantic_goal": "Identify a suitable algorithm",
        "outcome_hypotheses": [empty],
    }, review={
        "request_mode": "guidance", "semantic_goal": "Infer an aggregate regulatory network",
        "outcome_hypothesis": recovered,
    })
    provider.responses[SemanticDiscriminator] = {
        "selection_tags": ["relaxed_graph_matching"],
        "evidence": [{
            "dimension": "selection_tag", "value": "relaxed_graph_matching", "source": "explicit",
            "text_span": "目標函數鬆弛化", "rationale": "The request explicitly asks for a relaxation-based objective.",
        }],
    }
    case = RoutingScenario.model_validate({
        "id": "not-applicable-recovery-otter", "language": "zh", "category": "positive",
        "prompt": task,
        "expected": {
            "status": "exact", "actions": ["run_otter"], "artifact_type": "regulatory_network",
            "granularity": "aggregate", "required_discriminators": {"selection_tags": ["relaxed_graph_matching"]},
        },
    })

    result = evaluate([case], provider=provider, model_name="fixture", task_token_budget=30000)["results"][0]
    assert result["route_passed"], result
    assert result["semantic_passed"], result
    assert result["matched_actions"] == ["run_otter"]


def test_provider_value_error_recovery_is_not_counted_as_semantic_success():
    provider = FixtureProvider(first=ValueError("sensitive provider detail"))
    report = run(provider)
    result = report["results"][0]

    assert not result["route_passed"]  # A fallback is not the expected exact match.
    assert result["status"] is None
    assert result["matched_actions"] == []
    assert result["answer_passed"]
    assert "Fallback recommendation" not in result["answer"]
    assert not result["semantic_passed"]
    assert not result["passed"]
    assert result["path"] == "semantic_fallback"
    assert report["summary"]["registry_recovery_count"] == 0
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
    # Not discarded any more -- kept as a candidate, and still not a pass. The
    # semantic metric is what must not soften: a reading whose quote the request
    # lacks has not been verified, whatever guidance was salvaged from it.
    assert result["status"] == "fallback"
    assert "evidence_validation" in result["diagnostics"]
    # Three, not two: the reading survives to intent classification instead of
    # being dropped before it. The extra call is what keeping it costs.
    assert len(provider.calls) == 3
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
    assert result["status"] is None
    assert result["answer_evaluated"] and result["answer_passed"]
    assert "Fallback recommendation" not in result["answer"]
    assert "SAMBAR" not in result["answer"]
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


def test_repeated_semantic_drift_invalidates_exact_even_when_candidate_stays_correct():
    import copy

    class AlternatingProvider(FixtureProvider):
        """Drift through every review of the second trial, not just its first.

        Written when a third semantic attempt existed, so that one drifting
        review could not be read as a correctable slip. That attempt was
        reverted, and the fixture is kept because tying drift to the trial
        states this test's subject directly: a drifting review never becomes
        the answer, whatever the pipeline does with the attempt that produced it.
        """

        trials = 0

        def with_structured_output(self, schema, **kwargs):
            base = super().with_structured_output(schema, **kwargs)
            provider = self

            class Adapter:
                def invoke(self, messages):
                    result = copy.deepcopy(base.invoke(messages))
                    if schema is SemanticInterpretation:
                        provider.trials += 1
                    # 2026-09-06: the second call's adapter is bound to
                    # SemanticPatch, while this transport still answers with the
                    # review shape production also accepts. Drift is injected on
                    # whichever schema that second call asks for.
                    if schema in {SemanticReview, SemanticPatch}:
                        if provider.trials % 2 == 0:
                            item = result["outcome_hypothesis"]
                            item["outcome"]["artifact_type"] = "sample_distance_matrix"
                            for evidence in item["evidence"]:
                                if evidence["dimension"] == "artifact_type":
                                    evidence.update(value="sample_distance_matrix", source="inferred", text_span=None)
                    return result

            return Adapter()

    report = run(AlternatingProvider(), repeat=2)

    # A drifting review is now discarded in favour of the first pass that had
    # already validated, so the drift never becomes the stored answer. That is
    # what this test is about; it no longer costs the run its workflow.
    drifted = report["results"][1]
    assert drifted["outcome"]["artifact_type"] == "sample_cluster_assignment"
    assert drifted["status"] == "exact"
    assert any(
        "artifact_type" in issue or "terminal_goal_conflict" in issue
        for entry in drifted["diagnostic_details"] for issue in entry["issues"]
    )


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


def test_a_missing_dependency_names_the_module_without_echoing_payloads(monkeypatch, capsys):
    """A wrong interpreter is a setup mistake; the module name is not a secret."""
    from evaluate_routing import main
    import evaluate_routing

    def missing(*_args, **_kwargs):
        raise ModuleNotFoundError("No module named 'langchain_openai'", name="langchain_openai")

    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-placeholder")
    monkeypatch.setattr(evaluate_routing, "build_llm", missing)

    status = main(["--live", "--case", "original-q1", "--max-calls", "3", "--json"])

    error = capsys.readouterr().err
    assert status == 2
    assert "ModuleNotFoundError" in error and "langchain_openai" in error
    assert "offline-placeholder" not in error


def test_other_failures_still_report_only_their_type(monkeypatch, capsys):
    from evaluate_routing import main
    import evaluate_routing

    def broken(*_args, **_kwargs):
        raise ValueError("provider rejected key sk-secret-value")

    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-placeholder")
    monkeypatch.setattr(evaluate_routing, "build_llm", broken)

    status = main(["--live", "--case", "original-q1", "--max-calls", "3", "--json"])

    error = capsys.readouterr().err
    assert status == 2
    assert "ValueError" in error
    assert "sk-secret-value" not in error


def test_report_exposes_structured_validation_issues_not_only_categories():
    """A coarse category cannot say which field a live model got wrong."""
    item = hypothesis()
    item["outcome"]["input_artifacts"] = []
    item["evidence"] = [e for e in item["evidence"] if e["dimension"] != "input_artifact"]
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Subtype patients",
               "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "Subtype patients",
                "outcome_hypothesis": item},
    )

    row = run(provider, next(c for c in load_scenarios(DEFAULT_SCENARIOS) if c.id == 'original-q1'))["results"][0]

    attempts = {entry["attempt"]: entry for entry in row["diagnostic_details"]}
    assert "hypothesis[0].missing_current_input:mutation_matrix" in attempts[1]["issues"]
    assert attempts[2]["issues"] == attempts[1]["issues"]
    assert attempts[2]["error_type"] == "ValueError"


def test_diagnostic_details_carry_the_rejected_shape_and_identifier():
    item = hypothesis()
    item["outcome"]["input_artifacts"] = ["somatic_mutation"]
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Subtype patients",
               "outcome_hypotheses": [item]},
    )

    row = run(provider, next(c for c in load_scenarios(DEFAULT_SCENARIOS) if c.id == 'original-q1'))["results"][0]

    issues = [issue for entry in row["diagnostic_details"] for issue in entry["issues"]]
    assert "schema_validation:outcome_hypotheses.0.outcome.input_artifacts.0:literal_error" in issues
    shapes = [shape for entry in row["diagnostic_details"] for shape in entry.get("shapes", [])]
    assert {"location": ["outcome_hypotheses", "0", "outcome", "input_artifacts", "0"],
            "type": "literal_error", "input_type": "str",
            "input_value": "somatic_mutation"} in shapes


def test_report_separates_a_missing_quote_from_a_quote_the_request_lacks():
    """Both shapes are reported as `ungrounded_evidence` and call for opposite fixes.

    Across four live rounds this is the largest issue family, and no stored
    artifact said which shape occurred. The classification carries only the
    closed-vocabulary dimension and value, never the provider's own words.
    """
    item = hypothesis()
    # A quote made of characters that are not words. Since the contract began
    # requiring `explicit` entries to carry a quote, an entry supplying none no
    # longer parses, and this is the remaining way to reach `absent`.
    item["evidence"][3]["source"] = "explicit"
    item["evidence"][3]["text_span"] = "--"
    # Supplies one the request does not contain.
    item["evidence"][2]["text_span"] = "This text is absent from the request"
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypothesis": item},
    )

    report = run(provider)
    shapes = [
        shape for entry in report["results"][0]["diagnostic_details"]
        for shape in entry["evidence_shapes"]
    ]

    assert {"hypothesis": 0, "dimension": "entity_type", "value": "sample",
            "span": "absent"} in shapes
    assert {"hypothesis": 0, "dimension": "artifact_type",
            "value": "sample_cluster_assignment", "span": "unmatched"} in shapes
    # One rejection reported through two events must not count twice.
    assert report["summary"]["ungrounded_evidence_shapes"] == {"unmatched": 2, "absent": 2}
    assert report["summary"]["ungrounded_evidence_clusters"] == {"mixed": 2}
    # The quotes themselves never enter the report.
    assert "absent from the request" not in json.dumps(report)


@pytest.mark.parametrize(
    ("shapes", "expected"),
    [
        ([("absent", 0), ("absent", 0)], {"all_absent": 1}),
        ([("unmatched", 0), ("unmatched", 0)], {"all_unmatched": 1}),
        ([("absent", 0), ("unmatched", 0)], {"mixed": 1}),
        # Separate hypotheses are separate units even in one attempt.
        ([("absent", 0), ("unmatched", 1)], {"all_absent": 1, "all_unmatched": 1}),
    ],
)
def test_ungrounded_clusters_group_by_hypothesis_before_any_criterion(shapes, expected):
    """Pin the unit a criterion is allowed to count, against known rows.

    Entries inside one hypothesis are not independent, so a criterion stated
    per entry would overstate its own sample size.
    """
    from collections import Counter

    from evaluate_routing import _ungrounded_clusters

    row = {"diagnostic_details": [{
        "attempt": 1,
        "evidence_shapes": [
            {"hypothesis": index, "dimension": "operation", "value": "infer", "span": span}
            for span, index in shapes
        ],
    }]}

    assert dict(Counter(_ungrounded_clusters(row))) == expected


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([(2, 0)], {"all_spanned": 1}),
        ([(0, 2)], {"none_spanned": 1}),
        ([(1, 1)], {"mixed": 1}),
        # A hypothesis that wrote no explicit evidence is not a unit at all.
        ([(0, 0), (1, 0)], {"all_spanned": 1}),
    ],
)
def test_span_hypotheses_count_only_hypotheses_that_claimed_an_explicit_source(rows, expected):
    from collections import Counter

    from evaluate_routing import _span_hypotheses

    result = {"evidence_census": [
        {"hypothesis": index, "explicit_with_span": with_span,
         "explicit_without_span": without_span, "inferred": 0}
        for index, (with_span, without_span) in enumerate(rows)
    ]}

    assert dict(Counter(_span_hypotheses(result))) == expected


def test_report_carries_one_evidence_census_row_per_attempt_and_hypothesis():
    item = hypothesis()
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypothesis": item},
    )

    report = run(provider)
    census = report["results"][0]["evidence_census"]

    # The fixture writes three quoted entries and two inferred ones. The review
    # is a second writer, not a precondition, so it reports its own row: the
    # contract under consideration would bind both passes.
    row = {"hypothesis": 0, "explicit_with_span": 3, "explicit_without_span": 0, "inferred": 2}
    assert census == [dict(row, attempt=1), dict(row, attempt=2)]
    assert report["summary"]["evidence_span_hypotheses"] == {"all_spanned": 2}
    assert report["summary"]["evidence_span_entries"] == {
        "with_span": 6, "without_span": 0, "inferred": 4}


def test_the_report_says_when_the_harness_wrote_a_field_itself():
    """The only authorized field write must never be invisible in the report.

    It was declared with the change and left unwired for a round, so the
    criterion it served had to be checked indirectly. Without this the pass rate
    cannot be separated from the harness's own repairs.
    """
    item = hypothesis()
    item["outcome"]["input_artifacts"] = []
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Subtype patients",
               "outcome_hypotheses": [item]},
    )

    row = run(provider, next(c for c in load_scenarios(DEFAULT_SCENARIOS) if c.id == "original-q1"))["results"][0]

    restored = [entry for entry in row["restored_fields"]]
    assert [(entry["field"], entry["value"]) for entry in restored] == [
        ("input_artifacts", "mutation_matrix"),
    ]
    assert restored[0]["attempt"] == 1


def test_a_report_with_no_repair_says_so_rather_than_omitting_the_field():
    item = hypothesis()
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Grouping",
               "outcome_hypotheses": [item]},
    )

    report = run(provider)

    assert report["results"][0]["restored_fields"] == []
    assert report["summary"]["trials_with_restored_fields"] == 0


def test_a_validation_error_reports_where_it_failed(monkeypatch, capsys):
    """Third time the sanitiser hid a real fault; locations are not payloads."""
    from evaluate_routing import main
    import evaluate_routing
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation

    def broken(*_args, **_kwargs):
        SemanticInterpretation.model_validate(
            {"semantic_goal": "g", "outcome_hypotheses": [{"outcome": {
                "operation": "analyze", "artifact_type": "sample_cluster_assignment",
                "granularity": "aggregate"}}]}
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-placeholder")
    monkeypatch.setattr(evaluate_routing, "build_llm", broken)

    status = main(["--live", "--case", "original-q1", "--max-calls", "3", "--json"])

    error = capsys.readouterr().err
    assert status == 2
    assert "ValidationError" in error
    assert "outcome_hypotheses.0.confidence" in error
    assert "missing" in error
    assert "offline-placeholder" not in error


def test_naming_the_right_tool_without_the_discriminator_is_reported():
    """Credit for the right tool must not cover for a missing discriminator.

    Several corpus prompts fit more than one capability on their coarse fields;
    what separates them is a role or a registry tag. One prompt scored 3/3 while
    two of its three trials named no distinguishing tag at all -- the harness
    resolved the tie, not the model. The corpus now records the discriminator
    and the scorer reports its absence.
    """
    item = hypothesis()
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypotheses": [item]},
    )
    case = scenario(required_discriminators={"selection_tags": ["cancer_subtyping"]})

    row = run(provider, case)["results"][0]

    assert row["matched_actions"] == ["run_sambar"]
    assert any(
        error.startswith("discriminator: selection_tags must include")
        for error in row["errors"]
    )
    assert not row["passed"]

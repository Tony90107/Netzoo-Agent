from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    CapabilityMatch,
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
)
from netzoo_agent_core.graph.discriminator import (  # noqa: E402
    invoke_semantic_discriminator,
)
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    explicit_input_artifacts,
    match_semantic_request,
)
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402


Q1 = (
    "I have an expression matrix, motif and PPI priors. I need an explicit "
    "objective function, continuous convex optimization and convergence "
    "guarantees, not heuristic updates."
)
Q2 = (
    "I have an expression matrix, motif and PPI priors for 100 patients. "
    "First build one aggregate network, then apply LIONESS to derive each "
    "patient network."
)
Q1_ZH = (
    "我手邊有完整的 Expression、Motif 和 PPI 矩陣。在推論基因調控網路時，"
    "我需要演算法具備嚴謹的數學目標函數（Objective Function），能明確量化並平衡先驗資訊與共表現約束之間的損失，"
    "同時保有連續凸最佳化的理論收斂保證，而不是仰賴啟發式的迭代更新。"
)
Q2_ZH = (
    "我擁有 100 個病患的 Expression 矩陣、Motif 和 PPI 先驗資料。我的最終目標是先建立一個整體的群體調控網路，"
    "接著立刻使用 LIONESS 演算法拆解並反推每一位病患個人的專屬調控網路。"
)


def tf_aggregate(*, tags: list[str] | None = None) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            input_artifacts=["expression_matrix"],
            artifact_type="regulatory_network",
            entity_types=["tf", "gene"],
            regulator_types=["tf"],
            target_types=["gene"],
            selection_tags=tags or [],
            granularity="aggregate",
        ),
        confidence=0.95,
        evidence=[
            OutcomeEvidence(
                dimension="operation",
                value="infer",
                source="inferred",
                rationale="Fixture supplies the validated operation.",
            ),
            OutcomeEvidence(
                dimension="artifact_type",
                value="regulatory_network",
                source="inferred",
                rationale="Fixture supplies the validated output artifact.",
            ),
            OutcomeEvidence(
                dimension="input_artifact",
                value="expression_matrix",
                source="inferred",
                rationale="Fixture supplies the validated input artifact.",
            ),
            OutcomeEvidence(
                dimension="granularity",
                value="aggregate",
                source="inferred",
                rationale="Fixture supplies the validated granularity.",
            ),
            OutcomeEvidence(
                dimension="regulator_type",
                value="tf",
                source="inferred",
                rationale="Fixture supplies the validated regulator role.",
            ),
            OutcomeEvidence(
                dimension="target_type",
                value="gene",
                source="inferred",
                rationale="Fixture supplies the validated target role.",
            ),
        ],
    )


def test_q1_objective_and_continuous_optimization_selects_otter():
    result = match_semantic_request(
        Q1,
        [tf_aggregate(tags=["relaxed_graph_matching"])],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_otter"]


def test_q2_lioness_first_stage_selects_panda_and_excludes_puma_without_mirna():
    assert explicit_input_artifacts(Q2) == {"expression_matrix"}
    result = match_semantic_request(
        Q2,
        [tf_aggregate(tags=["lioness_base_compatibility"])],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_panda"]


def test_empty_provider_tags_recover_chinese_q1_to_otter(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="q1-zh-recovery", profile_id="default")
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            "parsed": {"selection_tags": [], "evidence": []},
            "raw": object(),
        }),
        semantic_claims=False,
        semantic_model_name="fixture",
        router_max_tokens=200,
        task_token_budget=10_000,
        recorder=recorder,
        price_catalog=PriceCatalog(),
    )
    interpretation = SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="Choose a regulatory-network method",
        outcome_hypotheses=[tf_aggregate()],
    )
    capability_match = CapabilityMatch(
        status="ambiguous",
        hypothesis_actions=["run_panda", "run_otter"],
    )

    updated, match, _, _ = invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        Q1_ZH,
        interpretation,
        capability_match,
        LLMUsage(),
        [],
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_otter"]
    assert updated.outcome_hypotheses[0].outcome.selection_tags == [
        "relaxed_graph_matching"
    ]
    recovery = next(
        event for event in store.read_events(run_id)
        if event.event_type == "routing.semantic_discriminator_recovered"
    )
    assert recovery.payload["selection_tags"] == ["relaxed_graph_matching"]
    assert recovery.payload["evidence"]["text_span"] == "連續凸最佳化"


def test_empty_provider_tags_recover_chinese_q2_to_panda(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="q2-zh-recovery", profile_id="default")
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            "parsed": {"selection_tags": [], "evidence": []},
            "raw": object(),
        }),
        semantic_claims=False,
        semantic_model_name="fixture",
        router_max_tokens=200,
        task_token_budget=10_000,
        recorder=recorder,
        price_catalog=PriceCatalog(),
    )
    interpretation = SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="Choose a regulatory-network method",
        outcome_hypotheses=[tf_aggregate()],
    )
    capability_match = CapabilityMatch(
        status="ambiguous",
        hypothesis_actions=["run_panda", "run_otter"],
    )

    _, match, _, _ = invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        Q2_ZH,
        interpretation,
        capability_match,
        LLMUsage(),
        [],
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_panda"]


def test_discriminator_normalizes_glossary_aliases_to_otter(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="q1-alias-recovery", profile_id="default")
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            "parsed": {
                "selection_tags": [
                    "explicit objective/loss",
                    "convergence guarantees",
                    "aggregate_network",
                ],
                "evidence": [
                    {
                        "dimension": "selection_tag",
                        "value": "explicit objective/loss",
                        "source": "explicit",
                        "text_span": "嚴謹的數學目標函數（Objective Function）",
                        "rationale": "The request states an explicit objective.",
                    },
                    {
                        "dimension": "selection_tag",
                        "value": "convergence guarantees",
                        "source": "explicit",
                        "text_span": "連續凸最佳化的理論收斂保證",
                        "rationale": "The request states convergence guarantees.",
                    },
                    {
                        "dimension": "selection_tag",
                        "value": "aggregate_network",
                        "source": "explicit",
                        "text_span": "推論基因調控網路",
                        "rationale": "The request asks for a network inference result.",
                    },
                ],
            },
            "raw": object(),
        }),
        semantic_claims=False,
        semantic_model_name="fixture",
        router_max_tokens=200,
        task_token_budget=10_000,
        recorder=recorder,
        price_catalog=PriceCatalog(),
    )
    interpretation = SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="Choose a regulatory-network method",
        outcome_hypotheses=[tf_aggregate()],
    )
    capability_match = CapabilityMatch(
        status="ambiguous",
        hypothesis_actions=[
            "run_panda",
            "run_puma",
            "run_lioness_panda",
            "run_lioness_puma",
            "run_otter",
            "run_giraffe",
        ],
    )

    _, match, _, _ = invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        Q1_ZH,
        interpretation,
        capability_match,
        LLMUsage(),
        [],
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_otter"]


def test_aggregate_tf_tie_does_not_ask_a_non_discriminating_granularity_question():
    result = match_semantic_request(Q1, [tf_aggregate()], request_mode="guidance")

    assert result.status == "ambiguous"
    assert result.clarification_question != (
        "Should the result be aggregate or sample-specific?"
    )
    assert "run_puma" not in result.hypothesis_actions
    assert "run_lioness_puma" not in result.hypothesis_actions


def test_discriminator_failure_records_payload_and_validation_diagnostics(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="discriminator-observability", profile_id="default")
    interpretation = SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="Choose a regulatory-network method",
        outcome_hypotheses=[tf_aggregate()],
    )
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            "parsed": {
                "selection_tags": ["relaxed_graph_matching"],
                "evidence": [],
            },
            "raw": object(),
        }),
        semantic_claims=False,
        semantic_model_name="fixture",
        router_max_tokens=200,
        task_token_budget=10_000,
        recorder=recorder,
        price_catalog=PriceCatalog(),
    )
    capability_match = CapabilityMatch(
        status="ambiguous",
        hypothesis_actions=["run_panda", "run_otter"],
    )

    invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        Q1,
        interpretation,
        capability_match,
        LLMUsage(),
        [],
    )

    failed = next(
        event for event in store.read_events(run_id)
        if event.event_type == "routing.semantic_discriminator_failed"
    )
    assert failed.payload["error_type"] == "ValidationError"
    assert failed.payload["candidate_actions"] == ["run_panda", "run_otter"]
    assert failed.payload["provider_payload"]["selection_tags"] == [
        "relaxed_graph_matching"
    ]
    assert failed.payload["validation_issues"]
    assert "Every selected discriminator tag requires evidence" in failed.payload[
        "error_message"
    ]


def test_user_visible_output_policy_is_english_for_multilingual_requests():
    from netzoo_agent_core.presentation import output_language_policy

    policy = output_language_policy()
    assert "Always reply in English" in policy
    assert not any("\u3400" <= character <= "\u9fff" for character in policy)

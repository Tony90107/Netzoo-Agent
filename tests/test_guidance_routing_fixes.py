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
from netzoo_agent_core.graph.claim_invocation import invoke_claim_interpreter  # noqa: E402
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
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402


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
BONOBO_PVALUE_TASK = (
    "我想從一份包含 20 個樣本的 expression matrix 中，只分析 S01 和 S07，"
    "產生兩張 sample-specific gene-gene co-expression matrix，並且在 sparsify 後輸出 p-value matrix"
)
BONOBO_BAYESIAN_TASK = (
    "My expression data are noisy; use background covariance and prior information "
    "with adaptive shrinkage to balance data and prior automatically for each sample."
)


def tf_aggregate(
    *, tags: list[str] | None = None, tag_span: str | None = None,
) -> OutcomeHypothesis:
    evidence = [
        OutcomeEvidence(
            dimension=dimension,
            value=value,
            source="inferred",
            rationale=f"Fixture supplies the validated {dimension}.",
        )
        for dimension, value in (
            ("operation", "infer"),
            ("artifact_type", "regulatory_network"),
            ("input_artifact", "expression_matrix"),
            ("granularity", "aggregate"),
            ("regulator_type", "tf"),
            ("target_type", "gene"),
        )
    ]
    if tags and tag_span is not None:
        evidence.append(OutcomeEvidence(
            dimension="selection_tag",
            value=tags[0],
            source="explicit",
            text_span=tag_span,
            rationale="The request explicitly states the method discriminator.",
        ))
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
        evidence=evidence,
    )


def bonobo_coexpression() -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", input_artifacts=["expression_matrix"],
            artifact_type="coexpression_network", entity_types=["gene"],
            selection_tags=[], granularity="sample_specific",
        ),
        confidence=0.95,
        evidence=[
            OutcomeEvidence(
                dimension=dimension, value=value, source="inferred",
                rationale="Fixture supplies the validated outcome dimension.",
            )
            for dimension, value in (
                ("operation", "infer"),
                ("input_artifact", "expression_matrix"),
                ("artifact_type", "coexpression_network"),
                ("entity_type", "gene"),
                ("granularity", "sample_specific"),
            )
        ],
    )


def test_q1_objective_and_continuous_optimization_selects_otter():
    result = match_semantic_request(
        Q1,
        [tf_aggregate(
            tags=["relaxed_graph_matching"],
            tag_span="continuous convex optimization",
        )],
        request_mode="guidance",
    )

    assert result.status == "exact"
    assert result.matched_actions == ["run_otter"]


def test_q2_lioness_first_stage_selects_panda_and_excludes_puma_without_mirna():
    assert explicit_input_artifacts(Q2) == {
        "expression_matrix", "motif_prior", "ppi_prior",
    }
    result = match_semantic_request(
        Q2,
        [tf_aggregate(
            tags=["lioness_base_compatibility"],
            tag_span="First build one aggregate network, then apply LIONESS",
        )],
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


def test_generic_provider_tags_recover_bonobo_pvalue_discriminator(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="bonobo-pvalue-recovery", profile_id="default")
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            "parsed": {
                "selection_tags": [
                    "sample_specific", "coexpression", "sparse_pvalue_coexpression",
                ],
                "evidence": [
                    {
                        "dimension": "artifact_type", "value": "coexpression_network",
                        "source": "explicit", "text_span": "co-expression",
                        "rationale": "The provider repeated the prior outcome evidence.",
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

    _, match, _, _ = invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        BONOBO_PVALUE_TASK,
        SemanticInterpretation(
            request_mode="guidance",
            semantic_goal="sample-specific co-expression with p-values",
            outcome_hypotheses=[bonobo_coexpression()],
        ),
        CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=[
                "run_lioness_coexpression", "run_cobra", "run_bonobo",
            ],
        ),
        LLMUsage(),
        [],
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_bonobo"]


def test_empty_provider_tags_recover_bonobo_bayesian_discriminator(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="bonobo-bayesian-recovery", profile_id="default")
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            "parsed": {"selection_tags": [], "evidence": []}, "raw": object(),
        }),
        semantic_claims=False,
        semantic_model_name="fixture",
        router_max_tokens=200,
        task_token_budget=10_000,
        recorder=recorder,
        price_catalog=PriceCatalog(),
    )

    _, match, _, _ = invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        BONOBO_BAYESIAN_TASK,
        SemanticInterpretation(
            request_mode="guidance",
            semantic_goal="adaptive Bayesian sample-specific co-expression",
            outcome_hypotheses=[bonobo_coexpression()],
        ),
        CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=["run_lioness_coexpression", "run_bonobo"],
        ),
        LLMUsage(),
        [],
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_bonobo"]


def test_invalid_discriminator_payload_still_recovers_bonobo_pvalue(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="bonobo-pvalue-invalid-discriminator", profile_id="default")
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            # The provider selected a shared tag but omitted its required evidence.
            # This is the live failure mode: the payload is invalid, so the old
            # code returned the original LIONESS/BONOBO tie unchanged.
            "parsed": {"selection_tags": ["sample_specific"], "evidence": []},
            "raw": object(),
        }),
        semantic_claims=False,
        semantic_model_name="fixture",
        router_max_tokens=200,
        task_token_budget=10_000,
        recorder=recorder,
        price_catalog=PriceCatalog(),
    )

    _, match, _, _ = invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        BONOBO_PVALUE_TASK,
        SemanticInterpretation(
            request_mode="guidance",
            semantic_goal="sample-specific co-expression with p-values",
            outcome_hypotheses=[bonobo_coexpression()],
        ),
        CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=["run_lioness_coexpression", "run_bonobo"],
        ),
        LLMUsage(),
        [],
    )

    assert match.status == "exact"
    assert match.matched_actions == ["run_bonobo"]


def test_grounded_discriminator_tag_can_narrow_unverified_base_evidence(tmp_path):
    """A valid tie-break must not inherit unrelated first-pass quote failures."""
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(
        session_id="bonobo-pvalue-unverified-base", profile_id="default"
    )
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {
            "parsed": {
                "selection_tags": [
                    "sample_specific", "sparse_pvalue_coexpression",
                ],
                "evidence": [
                    {
                        "dimension": "selection_tag",
                        "value": "sample_specific",
                        "source": "explicit",
                        "text_span": "sample-specific gene-gene co-expression matrix",
                        "rationale": "The request explicitly asks for sample-specific matrices.",
                    },
                    {
                        "dimension": "selection_tag",
                        "value": "sparse_pvalue_coexpression",
                        "source": "explicit",
                        "text_span": "sparsify 後輸出 p-value matrix",
                        "rationale": "The request explicitly asks for p-values after sparsification.",
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
    base = bonobo_coexpression().model_copy(update={
        "evidence": [OutcomeEvidence(
            dimension="operation",
            value="infer",
            source="explicit",
            text_span="words absent from the request",
            rationale="Simulates an unrelated first-pass grounding failure.",
        )],
    })

    interpretation, match, _, _ = invoke_semantic_discriminator(
        context,
        {"run_id": str(run_id)},
        BONOBO_PVALUE_TASK,
        SemanticInterpretation(
            request_mode="guidance",
            semantic_goal="sample-specific co-expression with p-values",
            outcome_hypotheses=[base],
        ),
        CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=["run_lioness_coexpression", "run_bonobo"],
            match_basis="unverified_evidence",
        ),
        LLMUsage(),
        [],
    )

    assert interpretation.outcome_hypotheses[0] == base
    assert match.status == "exact"
    assert match.match_basis == "registry_features"
    assert match.matched_actions == ["run_bonobo"]


def test_glasso_bayesian_method_constraint_blocks_generic_panda_match():
    result = match_semantic_request(
        "Use Graphical Lasso to estimate the precision matrix and Bayesian "
        "optimization to tune the regularization strength.",
        [tf_aggregate()],
        request_mode="guidance",
    )

    assert result.status == "unsupported"
    assert result.matched_actions == []
    assert "unsupported_algorithm" in result.mismatch_dimensions


def test_active_learning_gaussian_process_method_constraint_blocks_network_match():
    result = match_semantic_request(
        "Use motif priors and active learning with a Gaussian process over "
        "parameter bounds to produce a sparse regulatory network.",
        [tf_aggregate()],
        request_mode="guidance",
    )

    assert result.status == "unsupported"
    assert result.matched_actions == []


def test_claim_contract_recovers_bonobo_pvalue_tag_and_normalizes_entities(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="bonobo-claims-recovery", profile_id="default")
    support = {"source": "inferred", "rationale": "Fixture supplies this outcome dimension."}
    payload = {
        "request_mode": "guidance",
        "semantic_goal": "sample-specific co-expression with p-values",
        "outcome_hypotheses": [{
            "outcome": {
                "operation": {"value": "infer", "support": support},
                "input_artifacts": [{"value": "expression_matrix", "support": support}],
                "artifact_type": {"value": "coexpression_network", "support": support},
                "entity_types": [
                    {"value": "gene", "support": support},
                    {"value": "sample", "support": support},
                ],
                "selection_tags": [],
                "granularity": {"value": "sample_specific", "support": support},
            },
            "confidence": 0.95,
        }],
    }
    context = SimpleNamespace(
        semantic_interpreter=SimpleNamespace(invoke=lambda _messages: {
            "parsed": payload, "raw": object(),
        }),
        semantic_reviewer=None,
        semantic_patcher=None,
        semantic_claims=True,
        semantic_model_name="fixture",
        router_max_tokens=200,
        task_token_budget=10_000,
        recorder=recorder,
        price_catalog=PriceCatalog(),
        project_policy=SimpleNamespace(workflows={
            action: SimpleNamespace(output_capability=capability)
            for action, capability in OUTPUT_CAPABILITIES.items()
        }),
        review_policy="when_needed",
    )
    interpretation, _, _, _, _ = invoke_claim_interpreter(
        context,
        {"run_id": str(run_id)},
        BONOBO_PVALUE_TASK,
        LLMUsage(),
        serialize=lambda _messages, _schema: "fixture",
        schema_errors=lambda _error: [],
    )

    assert interpretation is not None
    assert interpretation.outcome_hypotheses[0].outcome.entity_types == ["gene"]
    assert interpretation.outcome_hypotheses[0].outcome.selection_tags == [
        "sparse_pvalue_coexpression"
    ]


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

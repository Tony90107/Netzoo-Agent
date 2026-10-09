import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import session  # noqa: E402
import netzoo_agent_core.graph.factory as graph_module  # noqa: E402
import netzoo_agent_core.graph.router_invocation as router_invocation  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    Episode,
    HumanMessage,
    IntentDecision,
    LLMUsage,
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticDiscriminator,
    SemanticInterpretation,
    SemanticPatch,
    SemanticReview,
)

# 2026-09-06: the second semantic call is bound to SemanticPatch when the
# first pass parsed. These scripted transports answer it with the same
# complete review payload, which production still accepts, so each test
# keeps asserting what it named. The patch shape itself is covered by
# tests/test_semantic_patch_repair.py.
_REVIEW_SCHEMAS = {SemanticReview, SemanticPatch}
from netzoo_agent_core.graph import build_graph  # noqa: E402
from netzoo_agent_core.graph.policy_memory import retrieve_memory  # noqa: E402
from netzoo_agent_core.cli import export_local_trace, local_trace_status  # noqa: E402
from netzoo_agent_core.memory import (  # noqa: E402
    EpisodeStore,
    UserProfileStore,
    _write_json_atomic,
)
from netzoo_agent_core.session import (  # noqa: E402
    load_session,
    load_session_payload,
    save_session,
)
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.trace_contracts import LLMCallUsage  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402
import netzoo_agent as legacy_agent  # noqa: E402


def semantic_review(interpretation: SemanticInterpretation) -> SemanticReview:
    primary = max(
        interpretation.outcome_hypotheses,
        key=lambda hypothesis: hypothesis.confidence,
    )
    return SemanticReview(
        request_mode=interpretation.request_mode,
        semantic_goal=interpretation.semantic_goal,
        outcome_hypothesis=primary,
    )


class DeterministicRouterLLM:
    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        return SimpleNamespace(
            invoke=lambda messages: self.invoke(schema, messages)
        )

    def invoke(self, schema, _messages):
        self.calls += 1
        if schema is IntentDecision:
            return IntentDecision(
                mode="execute",
                confidence=0.99,
                reason="Deterministic execution fixture.",
            )
        interpretation = SemanticInterpretation(
            request_mode="execute",
            semantic_goal="aggregate TF regulatory network",
            outcome_hypotheses=[
                OutcomeHypothesis(
                    outcome=RequestedOutcome(
                        operation="infer",
                        artifact_type="regulatory_network",
                        entity_types=["tf", "gene"],
                        display_entities=["TF", "gene"],
                        regulator_types=["tf"],
                        target_types=["gene"],
                        granularity="aggregate",
                        unresolved_dimensions=[],
                    ),
                    confidence=0.99,
                    evidence=[
                        OutcomeEvidence(
                            dimension=dimension,
                            value=value,
                            source="inferred",
                            rationale="The named PANDA request entails this dimension.",
                        )
                        for dimension, value in (
                            ("operation", "infer"),
                            ("artifact_type", "regulatory_network"),
                            ("regulator_type", "tf"),
                            ("target_type", "gene"),
                            ("granularity", "aggregate"),
                        )
                    ],
                    assumptions=[],
                )
            ],
        )
        return (
            semantic_review(interpretation)
            if schema in _REVIEW_SCHEMAS
            else interpretation
        )


class SequencedHypothesisRouter:
    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        return SimpleNamespace(
            invoke=lambda messages: self.invoke(schema, messages)
        )

    def invoke(self, schema, _messages):
        self.calls += 1
        if schema is not IntentDecision:
            interpretation = SemanticInterpretation(
                request_mode="guidance",
                semantic_goal="sample-specific miRNA network",
                outcome_hypotheses=[
                    OutcomeHypothesis(
                        outcome=RequestedOutcome(
                            operation="infer",
                            artifact_type="regulatory_network",
                            entity_types=["mirna", "gene"],
                            regulator_types=["mirna"],
                            target_types=["gene"],
                            granularity="sample_specific",
                            unresolved_dimensions=["confirm network interpretation"],
                        ),
                        confidence=0.9,
                        evidence=[
                            OutcomeEvidence(
                                dimension=dimension,
                                value=value,
                                source="inferred",
                                rationale="The request entails this dimension.",
                            )
                            for dimension, value in (
                                ("operation", "infer"),
                                ("artifact_type", "regulatory_network"),
                                ("regulator_type", "mirna"),
                                ("target_type", "gene"),
                                ("granularity", "sample_specific"),
                            )
                        ],
                        assumptions=["network means regulatory network"],
                    )
                ],
            )
            return (
                semantic_review(interpretation)
                if schema in _REVIEW_SCHEMAS
                else interpretation
            )
        return IntentDecision(
            mode="answer",
            confidence=0.99,
            reason="The user asks which tools are needed.",
        )


class EmptyOutcomeRouter:
    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        return SimpleNamespace(
            invoke=lambda messages: self.invoke(schema, messages)
        )

    def invoke(self, schema, _messages):
        self.calls += 1
        if schema is not IntentDecision:
            interpretation = SemanticInterpretation(
                request_mode="guidance",
                semantic_goal="sample-specific miRNA regulatory network",
                outcome_hypotheses=[
                    OutcomeHypothesis(
                        outcome=RequestedOutcome(
                            operation="infer",
                            artifact_type="regulatory_network",
                            entity_types=["mirna"],
                            display_entities=["miRNA"],
                            regulator_types=["mirna"],
                            target_types=[],
                            granularity="sample_specific",
                            unresolved_dimensions=[],
                        ),
                        confidence=0.95,
                        evidence=[
                            OutcomeEvidence(
                                dimension="operation",
                                value="infer",
                                source="inferred",
                                rationale="A tool-selection question for a network implies inference.",
                            ),
                            # This shared fixture serves two differently worded
                            # prompts, so its evidence is inferred with a stated
                            # entailment. Explicit evidence must quote the exact
                            # request text, which no single span can satisfy for
                            # both; that rule keeps its own tests elsewhere.
                            OutcomeEvidence(
                                dimension="artifact_type",
                                value="regulatory_network",
                                source="inferred",
                                rationale="A miRNA regulator network is a regulatory network.",
                            ),
                            OutcomeEvidence(
                                dimension="regulator_type",
                                value="mirna",
                                source="inferred",
                                rationale="The request names miRNA as the regulator.",
                            ),
                            OutcomeEvidence(
                                dimension="granularity",
                                value="sample_specific",
                                source="inferred",
                                rationale="The request asks for one result per sample.",
                            ),
                        ],
                    )
                ],
            )
            return (
                semantic_review(interpretation)
                if schema in _REVIEW_SCHEMAS
                else interpretation
            )
        return IntentDecision(
            mode="answer",
            confidence=0.99,
            reason="The user asks which tools are needed.",
        )


class EmptyRouterAndInterpreter:
    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        return SimpleNamespace(
            invoke=lambda messages: self.invoke(schema, messages)
        )

    def invoke(self, _schema, _messages):
        self.calls += 1
        if self.calls <= 2:
            return {
                "semantic_goal": "No outcome",
                "outcome_hypotheses": [],
            }
        raise AssertionError("intent router must not run after invalid semantics")


class InvalidPandaEvidenceRouter:
    """The two structured replies recorded in the failing interactive run."""

    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        return SimpleNamespace(
            invoke=lambda messages: self.invoke(schema, messages)
        )

    def invoke(self, schema, _messages):
        self.calls += 1
        if schema is SemanticInterpretation:
            return {
                "request_mode": "execute",
                "semantic_goal": "Infer a PANDA regulatory network",
                "outcome_hypotheses": [{
                    "outcome": {
                        "operation": "infer",
                        "input_artifacts": ["expression_matrix"],
                        "artifact_type": "regulatory_network",
                        "entity_types": ["tf", "gene"],
                        "regulator_types": ["tf"],
                        "target_types": ["gene"],
                        "granularity": "not_applicable",
                    },
                    "confidence": 0.9,
                    "evidence": [
                        {
                            "dimension": "operation",
                            "value": "infer",
                            "source": "inferred",
                            "rationale": "Running PANDA infers a network.",
                        },
                        {
                            "dimension": "artifact_type",
                            "value": "regulatory_network",
                            "source": "inferred",
                            "rationale": "PANDA returns a regulatory network.",
                        },
                        {
                            "dimension": "input_artifact",
                            "value": "expression_file, motif_file, ppi_file",
                            "source": "explicit",
                            "text_span": "expression_file, motif_file, ppi_file",
                            "rationale": "The request names all three inputs.",
                        },
                    ],
                }],
            }
        if schema is SemanticPatch:
            return {
                "outcome": {
                    "granularity": "aggregate",
                    "input_artifacts": [
                        "expression_file", "motif_file", "ppi_file",
                    ],
                },
            }
        raise AssertionError("intent router must not run after failed semantics")


class EvidenceGuidedSemanticRetryRouter:
    """Reproduce the real gpt-4o-mini output, then correct it when rejected."""

    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        return SimpleNamespace(
            invoke=lambda messages: self.invoke(schema, messages)
        )

    def invoke(self, schema, messages):
        self.calls += 1
        if self.calls == 1:
            return SemanticInterpretation(
                request_mode="guidance",
                semantic_goal="tools for a sample-specific miRNA regulator network",
                outcome_hypotheses=[
                    OutcomeHypothesis(
                        outcome=RequestedOutcome(
                            operation="unknown",
                            artifact_type="unknown",
                            entity_types=["mirna"],
                            regulator_types=["mirna"],
                            target_types=["unknown"],
                            granularity="not_applicable",
                            unresolved_dimensions=["artifact_type", "operation"],
                        ),
                        confidence=0.8,
                        evidence=[
                            OutcomeEvidence(
                                dimension="granularity",
                                value="not_applicable",
                                source="explicit",
                                text_span="sample specific",
                                rationale="The request specifies a sample context.",
                            ),
                            OutcomeEvidence(
                                dimension="regulator_type",
                                value="mirna",
                                source="explicit",
                                text_span="mi-RNA regulator",
                                rationale="The regulator is explicit.",
                            ),
                        ],
                    )
                ],
            )
        if self.calls == 2:
            rendered = "\n".join(str(message.content) for message in messages)
            assert "inconsistent_not_applicable_outcome" in rendered
            corrected = EmptyOutcomeRouter()
            return corrected.invoke(schema, messages)
        if self.calls == 3:
            return IntentDecision(
                mode="answer",
                confidence=0.99,
                reason="The user asks which tools are needed.",
            )
        raise AssertionError("semantic retry pipeline made too many calls")


class AmbiguousRoleSemanticReviewRouter:
    """First pass is valid but omits the explicit miRNA regulator role."""

    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        return SimpleNamespace(
            invoke=lambda messages: self.invoke(schema, messages)
        )

    def invoke(self, schema, messages):
        self.calls += 1
        if self.calls == 1:
            return SemanticInterpretation(
                request_mode="guidance",
                semantic_goal="tools for a sample-specific regulator network",
                outcome_hypotheses=[
                    OutcomeHypothesis(
                        outcome=RequestedOutcome(
                            operation="unknown",
                            artifact_type="regulatory_network",
                            entity_types=[],
                            regulator_types=[],
                            target_types=["gene"],
                            granularity="sample_specific",
                            unresolved_dimensions=[],
                        ),
                        confidence=0.9,
                        evidence=[
                            OutcomeEvidence(
                                dimension="artifact_type",
                                value="regulatory_network",
                                source="explicit",
                                text_span="regulator network",
                                rationale="The requested artifact is explicit.",
                            ),
                            OutcomeEvidence(
                                dimension="granularity",
                                value="sample_specific",
                                source="explicit",
                                text_span="sample specific",
                                rationale="The requested granularity is explicit.",
                            ),
                            OutcomeEvidence(
                                dimension="target_type",
                                value="gene",
                                source="inferred",
                                rationale="The target role was not specified.",
                            ),
                        ],
                    )
                ],
            )
        if self.calls == 2:
            rendered = "\n".join(str(message.content) for message in messages)
            assert "registry_ambiguity" in rendered
            corrected = StrictRoutingPipelineLLM()
            review = semantic_review(corrected._interpret(messages, record_call=False))
            original_spans = {
                "artifact_type": "regulator network",
                "regulator_type": "mi-RNA regulator",
                "granularity": "sample specific",
            }
            review.outcome_hypothesis.evidence = [
                item.model_copy(update={"text_span": original_spans[item.dimension]})
                if item.dimension in original_spans else item
                for item in review.outcome_hypothesis.evidence
            ]
            return review
        if self.calls == 3:
            return IntentDecision(
                mode="answer",
                confidence=0.99,
                reason="The user asks which tools are needed.",
            )
        raise AssertionError("semantic role review made too many calls")


class GuidanceResponseLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return legacy_agent.AIMessage(
            content=(
                "Use PUMA followed by LIONESS-PUMA for sample-specific miRNA "
                "regulatory networks.\n\n"
                "No files were inspected and no analysis ran."
            )
        )


def test_a_reading_whose_quotes_are_absent_is_kept_but_held_below_an_exact_match(tmp_path):
    """The relaxation authorized in Log 94, and the exact extent of it.

    This test used to assert the opposite -- that such a reading reached no
    workflow at all. Discarding it entirely is what cost 148 of 188 such entries
    their whole run, and every one of a round's twelve misspelled trials, while
    the reading was usually right: a transposed letter makes a matching quote
    impossible, not the meaning unclear.

    The cost is stated here rather than hidden: this fixture's quotes are not a
    typo, they are fabricated, and the relaxation cannot tell the two apart. So
    a fabricated quote now does reach a named candidate. What it can never reach
    is an exact match, an authorized action, or a claim that it was verified --
    and the issue itself is still raised. Those bounds are the whole of what
    keeps this safe, so each is asserted below; if any stops holding, the
    relaxation has escaped its authorization.
    """
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", artifact_type="regulatory_network",
            entity_types=["mirna"], regulator_types=["mirna"],
            granularity="sample_specific",
        ),
        confidence=0.99,
        evidence=[OutcomeEvidence(
            dimension=dimension, value=value, source="explicit",
            text_span="fabricated quote absent from the user request",
            rationale="Provider incorrectly claimed an exact quote.",
        ) for dimension, value in (
            ("operation", "infer"), ("artifact_type", "regulatory_network"),
            ("regulator_type", "mirna"), ("granularity", "sample_specific"),
        )],
    )

    class InvalidEvidenceProvider:
        def with_structured_output(self, schema, **_kwargs):
            def invoke(_messages):
                assert schema in {SemanticInterpretation, *_REVIEW_SCHEMAS}
                if schema in _REVIEW_SCHEMAS:
                    return SemanticReview(
                        request_mode="guidance", semantic_goal="Network guidance",
                        outcome_hypothesis=hypothesis,
                    )
                return SemanticInterpretation(
                    request_mode="guidance", semantic_goal="Network guidance",
                    outcome_hypotheses=[hypothesis],
                )
            return SimpleNamespace(invoke=invoke)

    provider = InvalidEvidenceProvider()
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="unquoted-evidence", profile_id="default")
    context = SimpleNamespace(
        semantic_interpreter=provider.with_structured_output(SemanticInterpretation),
        semantic_reviewer=provider.with_structured_output(SemanticReview),
        intent_router=provider.with_structured_output(IntentDecision),
        semantic_prompt="Interpret scientific outcomes.", intent_prompt="Classify intent.",
        semantic_model_name="fake", router_model_name="fake", router_max_tokens=800,
        task_token_budget=20_000, recorder=recorder,
        project_policy=legacy_agent.ProjectPolicyLoader().load(),
        price_catalog=legacy_agent.PriceCatalog.from_environment(),
    )

    result = router_invocation.invoke_router(
        context, {"run_id": str(run_id)}, "Explain sample-specific miRNA networks.",
    )

    events = {event.event_type for event in store.read_events(run_id)}

    # Kept, and named, so the user has something to judge.
    assert result.decision.matched_actions == ["run_lioness_puma"]
    # The bounds. Never exact, never executable, never labelled verified.
    assert result.decision.capability_match_status == "fallback"
    assert result.decision.match_basis == "unverified_evidence"
    assert result.decision.should_execute is False
    assert result.decision.action == "no_tool"
    assert "routing.semantic_interpretation_accepted" not in events
    # Still detected, still recorded: relaxing the response is not the same as
    # ceasing to notice, and this is where those two would be confused.
    assert "routing.semantic_evidence_unverified" in events
    # The intent router now runs, where a discarded reading never reached it.
    # That is a third paid call on a path that used to stop at two -- the price
    # of keeping the reading, recorded rather than left to be discovered later.
    assert [call.role for call in result.usage.calls] == [
        "semantic_interpreter", "semantic_reviewer", "intent_router",
    ]


def test_routing_repairs_multilingual_review_and_selects_typed_goal_without_fallback(tmp_path):
    task = "我之前做過 PANDA；現在以 WES 資料對病人做分組。"
    requested = RequestedOutcome(
        operation="analyze", input_artifacts=["mutation_matrix"],
        artifact_type="sample_cluster_assignment", entity_types=["sample"],
        granularity="aggregate",
    )
    items = [OutcomeEvidence(
        dimension=dimension, value=value,
        source="explicit" if span else "inferred", text_span=span,
        rationale="The current request is one cohort grouping from the stated data.",
    ) for dimension, value, span in (
        ("operation", "analyze", None), ("input_artifact", "mutation_matrix", "WES"),
        ("artifact_type", "sample_cluster_assignment", "分組"),
        ("entity_type", "sample", "病人"), ("granularity", "aggregate", None),
    )]
    first_items = [
        item.model_copy(update={"text_span": "whole exome sequencing"})
        if item.dimension == "input_artifact" else item for item in items
    ]
    proposal = SemanticInterpretation(
        request_mode="guidance", semantic_goal="Cohort grouping",
        outcome_hypotheses=[OutcomeHypothesis(
            outcome=requested, confidence=0.9, evidence=first_items,
        )],
    )

    def review(messages):
        assert "ungrounded_evidence:input_artifact" in str(messages[-1].content)
        return {
            "request_mode": "guidance", "semantic_goal": "Cohort grouping",
            "outcome_hypothesis": requested.model_dump(),
            "confidence": 0.95, "evidence": [item.model_dump() for item in items],
            "assumptions": [],
        }

    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="repaired-review", profile_id="default")
    context = SimpleNamespace(
        semantic_interpreter=SimpleNamespace(invoke=lambda _m: proposal),
        semantic_reviewer=SimpleNamespace(invoke=review),
        intent_router=SimpleNamespace(invoke=lambda _m: IntentDecision(
            mode="answer", confidence=0.95, reason="Workflow guidance only.",
        )),
        semantic_prompt="Interpret scientific outcomes.", intent_prompt="Classify intent.",
        semantic_model_name="fake", router_model_name="fake", router_max_tokens=800,
        task_token_budget=20_000, recorder=recorder,
        project_policy=legacy_agent.ProjectPolicyLoader().load(),
        price_catalog=legacy_agent.PriceCatalog.from_environment(),
    )

    result = router_invocation.invoke_router(context, {"run_id": str(run_id)}, task)

    assert result.decision.matched_actions == ["run_sambar"]
    assert result.decision.requested_outcome.input_artifacts == ["mutation_matrix"]
    assert result.decision.requested_outcome.artifact_type == "sample_cluster_assignment"
    assert result.decision.should_execute is False
    assert [call.role for call in result.usage.calls] == [
        "semantic_interpreter", "semantic_reviewer", "intent_router",
    ]
    events = {event.event_type for event in store.read_events(run_id)}
    assert "routing.semantic_interpretation_accepted" in events
    assert "routing.semantic_guidance_recovered" not in events


def test_semantic_review_receives_registry_ambiguity_without_textual_matching(
    tmp_path: Path,
):
    router = AmbiguousRoleSemanticReviewRouter()
    context = SimpleNamespace(
        semantic_interpreter=SimpleNamespace(
            invoke=lambda messages: router.invoke(SemanticInterpretation, messages)
        ),
        semantic_reviewer=SimpleNamespace(
            invoke=lambda messages: router.invoke(SemanticReview, messages)
        ),
        semantic_prompt="Interpret scientific outcomes.",
        semantic_model_name="fake",
        router_max_tokens=800,
        task_token_budget=20_000,
        price_catalog=legacy_agent.PriceCatalog.from_environment(),
        recorder=legacy_agent.NullTraceRecorder(),
    )
    task = "if i want to get sample specific mi-RNA regulator network,what tools do i need?"

    # The call also reports which selection tags the harness moved into the
    # outcome, so a repair cannot pick a tool. Unused here: this test is about
    # what the review is told, not about matching.
    interpretation, _, _, error, _ = router_invocation._invoke_semantic_interpreter(
        context,
        {"budget_warnings": []},
        task,
        LLMUsage(budget_tokens=20_000),
    )

    assert error is None
    assert router.calls == 2
    assert interpretation is not None
    assert interpretation.outcome_hypotheses[0].outcome.regulator_types == ["mirna"]


class StrictRoutingPipelineLLM:
    """Expose only the three LLM seams allowed by the routing pipeline."""

    def __init__(self):
        self.call_order: list[str] = []

    def with_structured_output(self, schema, **_kwargs):
        if schema is SemanticInterpretation:
            return SimpleNamespace(invoke=self._interpret)
        if schema in _REVIEW_SCHEMAS:
            return SimpleNamespace(invoke=self._review)
        if schema is SemanticDiscriminator:
            return SimpleNamespace(invoke=lambda _messages: SemanticDiscriminator())
        if schema is IntentDecision:
            return SimpleNamespace(invoke=self._route_intent)
        raise AssertionError(f"unexpected routing schema: {schema.__name__}")

    def _interpret(self, _messages, *, record_call=True):
        if record_call:
            self.call_order.append("semantic_interpreter")
        return SemanticInterpretation(
            request_mode="guidance",
            semantic_goal="sample-specific miRNA regulatory network",
            outcome_hypotheses=[
                OutcomeHypothesis(
                    outcome=RequestedOutcome(
                        operation="infer",
                        artifact_type="regulatory_network",
                        entity_types=["mirna"],
                        display_entities=["miRNA"],
                        regulator_types=["mirna"],
                        target_types=[],
                        granularity="sample_specific",
                        unresolved_dimensions=[],
                    ),
                    confidence=0.98,
                    evidence=[
                        OutcomeEvidence(
                            dimension="operation",
                            value="infer",
                            source="inferred",
                            rationale="Producing a regulatory network requires inference.",
                        ),
                        OutcomeEvidence(
                            dimension="artifact_type",
                            value="regulatory_network",
                            source="explicit",
                            text_span="regulatory network",
                            rationale="The requested artifact is explicit.",
                        ),
                        OutcomeEvidence(
                            dimension="regulator_type",
                            value="mirna",
                            source="explicit",
                            text_span="miRNA",
                            rationale="The regulator type is explicit.",
                        ),
                        OutcomeEvidence(
                            dimension="granularity",
                            value="sample_specific",
                            source="explicit",
                            text_span="sample-specific",
                            rationale="The granularity is explicit.",
                        ),
                    ],
                )
            ],
        )

    def _route_intent(self, messages):
        self.call_order.append("intent_router")
        context = "\n".join(str(message.content) for message in messages)
        assert '"matched_actions":["run_lioness_puma"]' in context
        return IntentDecision(
            mode="answer",
            confidence=0.99,
            reason="The user asks which tools are needed.",
        )

    def _review(self, messages):
        self.call_order.append("semantic_reviewer")
        return semantic_review(self._interpret(messages, record_call=False))


def test_explicit_execution_phrase_reconciles_model_guidance_for_any_workflow():
    """Imperative run/test language wins over a model's advisory-mode drift."""
    router = StrictRoutingPipelineLLM()
    context = SimpleNamespace(
        semantic_interpreter=router.with_structured_output(SemanticInterpretation),
        semantic_reviewer=router.with_structured_output(SemanticReview),
        intent_router=router.with_structured_output(IntentDecision),
        semantic_prompt="Interpret scientific outcomes.",
        semantic_model_name="fake",
        intent_prompt="Classify intent.",
        router_model_name="fake",
        router_max_tokens=800,
        task_token_budget=20_000,
        recorder=legacy_agent.NullTraceRecorder(),
        project_policy=legacy_agent.ProjectPolicyLoader().load(),
        price_catalog=legacy_agent.PriceCatalog.from_environment(),
    )

    result = router_invocation.invoke_router(
        context,
        {},
        "請試跑 LIONESS PUMA sample-specific miRNA regulatory network.",
    )

    assert result.decision.should_execute is True
    assert result.decision.action == "run_lioness_puma"
    assert result.decision.capability_match_status == "exact"


def test_session_retains_the_trace_run_id_without_changing_legacy_load_shape(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(session, "SESSION_ROOT", tmp_path / "sessions")
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="named-session", profile_id="default")

    save_session(
        "named-session",
        [],
        {"run_id": str(run_id), "plan": None, "tool_results": []},
    )

    payload = load_session_payload("named-session")
    legacy = load_session("named-session", include_usage=True)
    assert payload["run_id"] == str(run_id)
    assert len(legacy) == 3


def test_session_serializes_llm_call_uuid_as_json_string(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(session, "SESSION_ROOT", tmp_path / "sessions")
    call = LLMCallUsage(
        role="router",
        model="test-model",
        input_tokens=3,
        output_tokens=2,
        total_tokens=5,
        usage_provenance="actual",
        status="success",
    )
    usage = LLMUsage(
        input_tokens=3,
        output_tokens=2,
        total_tokens=5,
        calls=[call],
    )

    save_session(
        "uuid-usage-session",
        [],
        {
            "plan": None,
            "tool_results": [],
            "token_usage": usage.model_dump(),
        },
    )

    payload = load_session_payload("uuid-usage-session")
    stored_call = payload["token_usage"]["calls"][0]
    assert stored_call["call_id"] == str(call.call_id)
    assert LLMUsage.model_validate(payload["token_usage"]).calls[0].call_id == call.call_id


def test_instrumented_node_records_boundaries_without_serializing_state(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="demo", profile_id="default")

    def classify(state):
        assert state["secret_state"] == "do-not-copy"
        return {"decision": {"action": "run_panda"}}

    result = recorder.instrument_node("classify", classify)(
        {"run_id": str(run_id), "current_step": 0, "secret_state": "do-not-copy"}
    )
    events = store.read_events(run_id)

    assert result == {"decision": {"action": "run_panda"}}
    assert [event.event_type for event in events] == [
        "run.started",
        "node.started",
        "node.finished",
    ]
    assert events[-1].payload["update_keys"] == ["decision"]
    assert "do-not-copy" not in (store.run_path(run_id) / "events.jsonl").read_text()


def test_instrumented_node_records_error_and_reraises(tmp_path: Path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="demo", profile_id="default")

    def fail(_state):
        raise ValueError("invalid bearer-secret")

    with pytest.raises(ValueError, match="invalid bearer-secret"):
        recorder.instrument_node("evaluate", fail)({"run_id": str(run_id)})

    events = store.read_events(run_id)
    assert events[-1].event_type == "error.recorded"
    assert events[-1].payload["error_type"] == "ValueError"


def test_memory_retrieval_trace_explains_each_selected_episode_score(tmp_path: Path):
    episode_store = EpisodeStore(tmp_path / "episodes")
    episode = Episode(
        episode_id="mirna-success",
        profile_id="default",
        task_summary="sample-specific miRNA regulatory network",
        workflow="LIONESS-PUMA",
        action="run_lioness_puma",
        status="completed",
    )
    _write_json_atomic(
        episode_store.path_for("default", episode.episode_id),
        episode.model_dump(),
    )
    trace_store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(trace_store)
    run_id = recorder.start_run(session_id="memory-score", profile_id="default")
    context = SimpleNamespace(
        profile_id="default",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=episode_store,
        recorder=recorder,
    )

    update = retrieve_memory(
        context,
        {
            "messages": [
                HumanMessage(content="run puma sample-specific miRNA")
            ],
            "run_id": str(run_id),
        },
    )

    event = next(
        item
        for item in trace_store.read_events(run_id)
        if item.event_type == "memory.retrieved"
    )
    assert update["retrieved_episodes"][0]["episode_id"] == "mirna-success"
    assert event.payload["episodes"] == [
        {
            "episode_id": "mirna-success",
            "workflow": "LIONESS-PUMA",
            "final_score": 4,
            "overlap_tokens": ["mirna", "sample-specific"],
            "workflow_bonus": 0,
            "status_bonus": 2,
            "typed_score": 0,
            "typed_matches": [],
        }
    ]


def test_trace_interfaces_are_available_from_stable_and_legacy_facades():
    from netzoo_agent_core import LocalTraceStore as StableStore
    from netzoo_agent_core import TraceRecorder as StableRecorder

    assert StableStore is LocalTraceStore
    assert StableRecorder is TraceRecorder
    assert legacy_agent.LocalTraceStore is LocalTraceStore
    assert legacy_agent.TraceRecorder is TraceRecorder


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_records_ordered_plan_tool_and_evaluation_events(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: DeterministicRouterLLM(),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="trace-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="always",
    )

    result = app.invoke(
        {
            "messages": [HumanMessage(content="Run a PANDA demo")],
            "run_id": str(run_id),
        }
    )
    events = store.read_events(run_id)
    event_types = [event.event_type for event in events]

    # Rewritten with the planner's confirmation gate. A demo request's inputs
    # are discovered locally, and the planner now refuses to treat discovery as
    # execution authority -- its own comment: "Every discovered or demo-selected
    # local input must be deliberately confirmed." So this run stops at the
    # question and emits no approval, tool or evaluation event, which is what
    # the ordering assertions below now check: the plan is recorded, and nothing
    # downstream of approval happens without it.
    #
    # The approved-and-executed ordering is still covered end to end by
    # `test_workflow_continuation.py`, which supplies the confirmation reply.
    assert "policy.loaded" in event_types
    assert "decision.recorded" in event_types
    assert "plan.created" in event_types
    assert "plan.approved" not in event_types
    assert "tool.started" not in event_types
    assert "evaluation.recorded" not in event_types
    assert result["plan"]["status"] == "needs_confirmation"
    assert result["run_id"] == str(run_id)
    # The trace stays verifiable whether or not the run reached execution.
    assert store.verify_run(run_id).valid is True


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_routes_semantics_before_intent_and_registry_owns_workflow(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    pipeline_llm = StrictRoutingPipelineLLM()
    response_llm = GuidanceResponseLLM()
    models = iter([pipeline_llm, response_llm])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="pipeline-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="always",
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What tools infer a sample-specific miRNA regulatory network?"
                    )
                )
            ],
            "run_id": str(run_id),
        }
    )

    assert pipeline_llm.call_order == [
        "semantic_interpreter",
        "semantic_reviewer",
        "intent_router",
    ]
    assert result["decision"]["action"] == "no_tool"
    assert result["decision"]["should_execute"] is False
    assert result["decision"]["capability_match_status"] == "exact"
    assert result["decision"]["matched_actions"] == ["run_lioness_puma"]
    assert result["decision"]["recommended_actions"] == [
        "run_puma",
        "run_lioness_puma",
    ]
    # Verified capability guidance is code-owned: the response model is never
    # asked to rewrite a validated recommendation.
    # Log 265 (user decision A): PANDA-family guidance offers the unreliable_prior concern.
    assert [call["role"] for call in result["token_usage"]["calls"]] == [
        "semantic_interpreter",
        "semantic_reviewer",
        "intent_router",
        "request_concerns",
        "capability_check",  # Log 387: asked right after routing
        "study_purpose",  # Log 355
        "data_facts",  # Log 380: a listed workflow needs TF priors the request does not bind
    ]
    assert "LIONESS-PUMA" in str(result["messages"][-1].content)
    event_types = [event.event_type for event in store.read_events(run_id)]
    assert event_types.index("routing.semantic_interpretation_accepted") < (
        event_types.index("routing.registry_match_completed")
    )
    assert event_types.index("routing.registry_match_completed") < event_types.index(
        "routing.intent_classified"
    )


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_matches_one_valid_partial_semantic_interpretation(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = SequencedHypothesisRouter()
    response_llm = GuidanceResponseLLM()
    models = iter([router, response_llm])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="repair-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="always",
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="What tools can produce a sample-specific miRNA network?"
                )
            ],
            "run_id": str(run_id),
        }
    )
    events = store.read_events(run_id)

    assert router.calls == 7  # Log 355: + the study-purpose call; Log 380: + data facts; Log 387: + capability check; Log 394: + its one retry
    assert result["decision"]["action"] == "no_tool"
    assert result["decision"]["matched_actions"] == []
    assert result["decision"]["hypothesis_actions"] == ["run_lioness_puma"]
    # 2026-09-27 (Log 194): one surviving candidate with no routing question
    # used to be the response-model-owned ambiguity branch. The registry now
    # supplies the question (`single_candidate_question`), so the reply is
    # deterministic and the response model is not called.
    assert response_llm.calls == 0
    assert [call["role"] for call in result["token_usage"]["calls"]] == [
        "semantic_interpreter",
        "semantic_reviewer",
        "intent_router",
        "capability_check",  # Log 387: asked right after routing
        "capability_check",  # Log 394: retried once after an undecodable reply
        "study_purpose",  # Log 355
        "data_facts",  # Log 380: a listed workflow needs TF priors the request does not bind
    ]
    assert "The only registered workflow compatible with this request is **LIONESS-PUMA**" in str(
        result["messages"][-1].content
    )
    assert any(
        event.event_type == "routing.semantic_interpretation_accepted"
        for event in events
    )


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_recovers_explicit_typed_outcome_with_semantic_interpreter(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = EmptyOutcomeRouter()
    response_llm = GuidanceResponseLLM()
    models = iter([router, response_llm])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="double-empty-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="always",
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "If I want to get a sample-specific miRNA regulatory network, "
                        "what tools do I need?"
                    )
                )
            ],
            "run_id": str(run_id),
        }
    )
    events = store.read_events(run_id)

    # Log 265 (user decision A): PANDA-family guidance offers the unreliable_prior concern.
    assert router.calls == 8  # Log 355: + the study-purpose call; Log 380: + data facts; Log 387: + capability check; Log 394: + its one retry
    assert result["decision"]["action"] == "no_tool"
    assert result["decision"]["capability_match_status"] == "exact"
    assert result["decision"]["matched_actions"] == ["run_lioness_puma"]
    assert result["decision"]["recommended_actions"] == [
        "run_puma",
        "run_lioness_puma",
    ]
    assert result["decision"]["clarification_question"] is None
    assert result["tool_results"] == []
    assert response_llm.calls == 0
    # Verified capability guidance is code-owned: the response model is never
    # asked to rewrite a validated recommendation.
    assert [call["role"] for call in result["token_usage"]["calls"]] == [
        "semantic_interpreter",
        "semantic_reviewer",
        "intent_router",
        "request_concerns",
        "capability_check",  # Log 387: asked right after routing
        "capability_check",  # Log 394: retried once after an undecodable reply
        "study_purpose",  # Log 355
        "data_facts",  # Log 380: a listed workflow needs TF priors the request does not bind
    ]
    assert "LIONESS-PUMA" in str(result["messages"][-1].content)
    assert any(
        event.event_type == "routing.semantic_interpretation_accepted"
        for event in events
    )


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_retries_a_schema_valid_but_inconsistent_semantic_outcome(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = EvidenceGuidedSemanticRetryRouter()
    models = iter([router, GuidanceResponseLLM()])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="semantic-retry-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="always",
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "if i want to get sample specific mi-RNA regulator network,"
                        "what tools do i need?"
                    )
                )
            ],
            "run_id": str(run_id),
        }
    )

    # Log 265 (user decision A): PANDA-family guidance offers the unreliable_prior concern.
    assert router.calls == 7  # Log 355: + the study-purpose call; Log 380: + data facts; Log 387: + capability check
    assert result["decision"]["action"] == "no_tool"
    assert result["decision"]["capability_match_status"] == "exact"
    assert result["decision"]["matched_actions"] == ["run_lioness_puma"]
    assert result["decision"]["recommended_actions"] == [
        "run_puma",
        "run_lioness_puma",
    ]
    assert result["decision"]["clarification_question"] is None
    event_types = [event.event_type for event in store.read_events(run_id)]
    assert "routing.semantic_interpretation_rejected" in event_types
    assert "routing.semantic_interpretation_retried" in event_types


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_reviews_registry_ambiguous_biological_roles(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = AmbiguousRoleSemanticReviewRouter()
    models = iter([router, GuidanceResponseLLM()])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="ambiguous-role-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="always",
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "if i want to get sample specific mi-RNA regulator network,"
                        "what tools do i need?"
                    )
                )
            ],
            "run_id": str(run_id),
        }
    )

    # Log 265 (user decision A): PANDA-family guidance offers the unreliable_prior concern.
    assert router.calls == 7  # Log 355: + the study-purpose call; Log 380: + data facts; Log 387: + capability check
    assert result["decision"]["capability_match_status"] == "exact"
    assert result["decision"]["matched_actions"] == ["run_lioness_puma"]
    proposed = next(
        event for event in store.read_events(run_id)
        if event.event_type == "routing.semantic_interpretation_proposed"
    )
    assert proposed.payload["registry_match_status"] == "ambiguous"


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_graph_rejects_an_empty_semantic_interpretation_without_calling_intent(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = EmptyRouterAndInterpreter()
    models = iter([router, GuidanceResponseLLM()])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="empty-semantic-test", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="always",
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Build a sample-specific miRNA regulatory network."
                    )
                )
            ],
            "run_id": str(run_id),
        }
    )

    assert router.calls == 4  # Log 355: + the study-purpose call; Log 387: + capability check
    assert result["decision"]["action"] == "no_tool"
    assert result["decision"]["matched_actions"] == []
    assert result["decision"]["recommended_actions"] == []
    # A validation failure is the system's own failure: it must not be reported
    # as an unclear question, and it must not ask the user to restate the goal.
    assert result["decision"]["clarification_question"] is None
    answer = str(result["messages"][-1].content)
    assert "restate" not in answer.casefold()
    assert "not evidence that your question is unclear" in answer.casefold()
    assert result["tool_results"] == []
    calls = result["token_usage"]["calls"]
    assert [call["role"] for call in calls] == [
        "semantic_interpreter",
        "semantic_reviewer",
        "capability_check",  # Log 387: asked right after routing
        "study_purpose",  # Log 355
    ]
    assert calls[0]["status"] == "failed"
    assert calls[1]["status"] == "failed"
    assert any(
        event.event_type == "routing.semantic_interpreter_failed"
        for event in store.read_events(run_id)
    )


@pytest.mark.skipif(
    graph_module.StateGraph is None,
    reason="LangGraph integration runs in the project container",
)
def test_explicit_panda_run_survives_semantic_validation_failure(
    tmp_path: Path,
    monkeypatch,
):
    """A broken semantic reply must not erase an unambiguous run command."""
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    router = InvalidPandaEvidenceRouter()
    models = iter([router, GuidanceResponseLLM()])
    monkeypatch.setattr(
        graph_module,
        "build_llm",
        lambda *_args, **_kwargs: next(models),
    )
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="panda-validation-fallback", profile_id="default")
    app = build_graph(
        "fake",
        0.0,
        router_model_name="fake",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
        trace_recorder=recorder,
        semantic_contract="legacy",
        review_policy="when_needed",
    )
    task = """Run PANDA using these local files:
expression_file=/work/manual_tests/input_identification/correct_names_invalid_content/expression.tsv
motif_file=/work/manual_tests/input_identification/correct_names_invalid_content/motif.tsv
ppi_file=/work/manual_tests/input_identification/correct_names_invalid_content/ppi.tsv"""

    result = app.invoke({"messages": [HumanMessage(content=task)], "run_id": str(run_id)})

    assert router.calls == 3  # Log 355: + the study-purpose call
    assert result["decision"]["action"] == "run_panda"
    assert result["decision"]["match_basis"] == "workflow_name"
    assert result["decision"]["expression_file"].endswith("/expression.tsv")
    assert result["decision"]["motif_file"].endswith("/motif.tsv")
    assert result["decision"]["ppi_file"].endswith("/ppi.tsv")
    assert result["plan"]["workflow"] == "PANDA"
    assert result["plan"]["status"] == "needs_input"
    assert "preflight failed" in result["plan"]["question"].casefold()
    assert result["tool_results"] == []


def test_local_trace_status_and_export_need_no_model_provider(tmp_path: Path):
    root = tmp_path / "traces"
    recorder = TraceRecorder(LocalTraceStore(root))
    run_id = recorder.start_run(session_id="status", profile_id="default")
    recorder.finish_run(run_id, "completed", {"result": "ok"})
    archive = tmp_path / "trace.tar.gz"

    status = local_trace_status(str(run_id), trace_root=root)
    exported = export_local_trace(str(run_id), archive, trace_root=root)

    assert status["valid"] is True
    assert status["status"] == "completed"
    assert status["event_count"] == 2
    assert exported == archive

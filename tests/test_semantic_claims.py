"""Offline semantic contract and production routing checks; no model-quality claims."""

from copy import deepcopy
from pathlib import Path
import json
import sys
from types import SimpleNamespace
from typing import get_type_hints

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from pydantic import ValidationError
from workflow_registry import OUTPUT_CAPABILITIES
from netzoo_agent_core.contracts import LLMUsage
from netzoo_agent_core.contracts.semantic_claims import (
    Support,
    SemanticClaims,
    SemanticClaimRepair,
)
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.graph.router_invocation import _invoke_semantic_interpreter
from netzoo_agent_core.interpretation.outcome_consistency import (
    select_primary_hypothesis,
)
from netzoo_agent_core.interpretation.outcome_validation import (
    validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.provider_fallback import recover_registry_guidance
from netzoo_agent_core.interpretation.registry_guidance import (
    decision_with_registry_signals,
)
from netzoo_agent_core.routing.outcome_matching import (
    match_semantic_request,
    match_registry_guidance_features,
)

TASK = (
    "if i want to get sample specific mi-rna regulator network ,what tools do i need?"
)


def claim(value, quote=None):
    return {
        "value": value,
        "support": {
            "source": "explicit" if quote else "inferred",
            "text_span": quote,
            "rationale": "The requested network requires inference.",
        },
    }


def payload():
    return {
        "request_mode": "guidance",
        "semantic_goal": "Individual miRNA regulatory networks",
        "outcome_hypotheses": [
            {
                "confidence": 0.9,
                "outcome": {
                    "operation": claim("infer"),
                    "artifact_type": claim("regulatory_network", "regulator network"),
                    "granularity": claim("sample_specific", "sample specific"),
                    "entity_types": [],
                    "regulator_types": [claim("mirna", "mi-RNA")],
                },
            }
        ],
    }


class Adapter:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def invoke(self, messages):
        self.calls.append(messages)
        if isinstance(self.reply, Exception):
            raise self.reply
        return deepcopy(self.reply)


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event, node, data):
        self.events.append((event, data))


def context(first, second):
    return SimpleNamespace(
        semantic_claims=True,
        semantic_interpreter=Adapter(first),
        semantic_reviewer=Adapter(second),
        semantic_patcher=Adapter(second),
        recorder=Recorder(),
        project_policy=SimpleNamespace(
            workflows={
                k: SimpleNamespace(output_capability=v)
                for k, v in OUTPUT_CAPABILITIES.items()
            }
        ),
        semantic_model_name="offline",
        task_token_budget=100000,
        router_max_tokens=2000,
        price_catalog=None,
    )


def run(ctx, task=TASK):
    return _invoke_semantic_interpreter(ctx, {}, task, LLMUsage(budget_tokens=100000))


@pytest.mark.parametrize(
    "task", [TASK, TASK.replace("mi-rna", "mi-RNA"), TASK.replace(" ,", ",").upper()]
)
def test_same_claims_have_same_validation_and_route_across_typography(task):
    decoded = SemanticClaims.model_validate(payload()).to_internal()
    assert validate_outcome_hypotheses(task, decoded.outcome_hypotheses).valid
    assert match_semantic_request(
        task, decoded.outcome_hypotheses, request_mode="guidance"
    ).matched_actions == ["run_lioness_puma"]


def test_provider_cannot_write_a_second_evidence_value():
    data = payload()
    data["outcome_hypotheses"][0]["outcome"]["granularity"]["support"]["value"] = (
        "aggregate"
    )
    with pytest.raises(ValidationError):
        SemanticClaims.model_validate(data)


def test_explicit_quote_is_required_at_schema_boundary():
    data = payload()
    data["outcome_hypotheses"][0]["outcome"]["granularity"]["support"]["text_span"] = (
        None
    )
    with pytest.raises(ValidationError):
        SemanticClaims.model_validate(data)


@pytest.mark.parametrize("missing", [True, False])
def test_every_claim_requires_support_at_provider_boundary(missing):
    data = payload()
    operation = data["outcome_hypotheses"][0]["outcome"]["operation"]
    if missing:
        operation.pop("support")
    else:
        operation["support"] = None

    with pytest.raises(ValidationError):
        SemanticClaims.model_validate(data)


def test_explicit_quote_requirement_is_visible_in_provider_json_schema():
    schema = Support.model_json_schema()
    variants = {
        branch["properties"]["source"]["enum"][0]: branch
        for branch in schema["anyOf"]
    }

    assert "text_span" in variants["explicit"]["required"]
    assert variants["explicit"]["properties"]["text_span"]["type"] == "string"
    assert "text_span" not in variants["inferred"]["required"]


def test_strict_provider_schema_keeps_inferred_support_satisfiable():
    from jsonschema import Draft202012Validator
    from langchain_core.utils.function_calling import convert_to_openai_tool

    schema = convert_to_openai_tool(SemanticClaims, strict=True)["function"][
        "parameters"
    ]
    support = schema["properties"]["outcome_hypotheses"]["items"]["properties"][
        "outcome"
    ]["properties"]["operation"]["properties"]["support"]

    validator = Draft202012Validator(support)
    validator.validate(
        {
            "source": "inferred",
            "rationale": "Network inference is entailed by the requested artifact.",
        }
    )
    validator.validate(
        {
            "source": "explicit",
            "text_span": "sample specific",
            "rationale": "The request states this granularity.",
        }
    )


def test_claim_prompt_requires_support_even_for_an_unknown_value():
    from netzoo_agent_core.interpretation.claim_prompt import claim_messages

    prompt = claim_messages(TASK)[0].content

    assert "Every claim requires support" in prompt
    assert "null support" not in prompt


def test_claim_prompt_forbids_empty_inferred_text_spans():
    from netzoo_agent_core.interpretation.claim_prompt import claim_messages

    prompt = claim_messages(TASK)[0].content

    assert "omit text_span or set it to null; never use an empty string" in prompt


def test_claim_prompt_stays_within_small_model_instruction_budget():
    from netzoo_agent_core.interpretation.claim_prompt import claim_messages

    tags = {
        tag
        for capability in OUTPUT_CAPABILITIES.values()
        for tag in capability.selection_tags
    }
    prompt = claim_messages(TASK, selection_tags=tags)[0].content

    assert len(prompt) <= 4200


def test_unknown_and_not_applicable_support_do_not_become_scientific_evidence():
    data = payload()
    outcome = data["outcome_hypotheses"][0]["outcome"]
    outcome.update(
        operation=claim("unknown"),
        artifact_type=claim("unknown"),
        granularity=claim("not_applicable"),
        input_artifacts=[],
        entity_types=[],
        regulator_types=[],
        target_types=[],
        unresolved_dimensions=[],
    )

    hypothesis = SemanticClaims.model_validate(data).to_internal().outcome_hypotheses[0]

    assert hypothesis.evidence == []


def test_semantic_interpreter_return_annotation_matches_runtime_contract():
    assert get_type_hints(_invoke_semantic_interpreter)["return"] == tuple[
        SemanticInterpretation | None,
        LLMUsage,
        list[str],
        BaseException | None,
        frozenset[str],
    ]


def test_complete_unique_result_does_not_call_reviewer():
    ctx = context(payload(), AssertionError("Reviewer must not run"))
    result, usage, _, error, _ = run(ctx)
    assert result and error is None
    assert len(ctx.semantic_interpreter.calls) == 1
    assert not ctx.semantic_reviewer.calls and not ctx.semantic_patcher.calls


def test_atomic_repair_preserves_other_fields_and_hypotheses():
    original = payload()
    original["outcome_hypotheses"].append(deepcopy(original["outcome_hypotheses"][0]))
    base = SemanticClaims.model_validate(original)
    repair = SemanticClaimRepair.model_validate(
        {
            "hypothesis_index": 1,
            "outcome": {"granularity": claim("aggregate", "network")},
        }
    )
    updated = repair.apply(base)
    assert updated.outcome_hypotheses[0] == base.outcome_hypotheses[0]
    assert base.model_dump() == SemanticClaims.model_validate(original).model_dump()
    internal = updated.to_internal().outcome_hypotheses[1]
    assert internal.outcome.granularity == "aggregate"
    assert [e.value for e in internal.evidence if e.dimension == "granularity"] == [
        "aggregate"
    ]


def test_repair_rejects_unknown_index():
    repair = SemanticClaimRepair.model_validate(
        {"hypothesis_index": 1, "outcome": {}}
    )
    with pytest.raises(ValueError):
        repair.apply(SemanticClaims.model_validate(payload()))


def test_repair_cannot_express_a_repeated_hypothesis_index():
    """The live failure: one outcome restated under index 0 two or three times."""
    repeated = {"repairs": [
        {"hypothesis_index": 0, "outcome": {}},
        {"hypothesis_index": 0, "outcome": {}},
    ]}
    with pytest.raises(ValidationError):
        SemanticClaimRepair.model_validate(repeated)
    schema = json.dumps(SemanticClaimRepair.model_json_schema())
    assert '"repairs"' not in schema
    assert SemanticClaimRepair.model_json_schema()["properties"]["hypothesis_index"]["type"] == "integer"


def test_bad_quote_is_repaired_without_retyping_outcome():
    # artifact_type has no deterministic witness, so only the review can fix it.
    bad = payload()
    bad["outcome_hypotheses"][0]["outcome"]["artifact_type"] = claim(
        "regulatory_network", "not in original request"
    )
    ctx = context(
        bad,
        {
            "hypothesis_index": 0,
            "outcome": {
                "artifact_type": claim("regulatory_network", "regulator network")
            },
        },
    )
    result, _, _, error, _ = run(ctx)
    assert result and error is None
    assert len(ctx.semantic_patcher.calls) == 1
    assert validate_outcome_hypotheses(TASK, result.outcome_hypotheses).valid
    assert result.outcome_hypotheses[0].outcome.regulator_types == ["mirna"]


def test_claim_repair_cannot_rewrite_fields_outside_rejected_scope():
    task = (
        "I have an expression matrix and want a sample specific mi-RNA "
        "regulator network, what tools do I need?"
    )
    patch = {
        "hypothesis_index": 0,
        "request_mode": "unknown",
        "semantic_goal": "Only explain how to begin.",
        "outcome": {
            "input_artifacts": [claim("expression_matrix", "expression matrix")],
            "operation": claim("explain", "what tools do I need?"),
            "artifact_type": claim("unknown"),
            "granularity": claim("not_applicable"),
        },
    }
    ctx = context(payload(), patch)

    result, _, _, error, _ = run(ctx, task)

    assert result is not None and error is None
    hypothesis = result.outcome_hypotheses[0]
    assert hypothesis.outcome.input_artifacts == ["expression_matrix"]
    assert hypothesis.outcome.operation == "infer"
    assert hypothesis.outcome.artifact_type == "regulatory_network"
    assert hypothesis.outcome.granularity == "sample_specific"
    assert result.request_mode == "guidance"
    assert result.semantic_goal == "Individual miRNA regulatory networks"

    rejected = next(data for event, data in ctx.recorder.events
                    if event == "routing.semantic_interpretation_rejected")
    assert rejected["issues"] == [
        "hypothesis[0].missing_current_input:expression_matrix"
    ]
    applied = next(data for event, data in ctx.recorder.events
                   if event == "routing.semantic_patch_applied")
    repair = applied["repairs"][0]
    assert repair["permitted_fields"] == ["input_artifacts"]
    assert repair["changed_fields"] == ["input_artifacts"]
    assert {
        "operation", "artifact_type", "granularity", "request_mode", "semantic_goal"
    }.issubset(repair["ignored_fields"])


def test_translated_chinese_quote_is_repaired_as_inferred_support():
    task = "請推薦能為每位病患各自建立 miRNA 對基因調控網路的方法。"
    bad = payload()
    outcome = bad["outcome_hypotheses"][0]["outcome"]
    outcome["artifact_type"] = claim(
        "regulatory_network", "a regulatory network"
    )
    outcome["granularity"] = claim("sample_specific", "每位病患各自")
    outcome["regulator_types"] = [claim("mirna", "miRNA")]
    outcome["entity_types"] = []
    patch = {
        "hypothesis_index": 0,
        "outcome": {"artifact_type": claim("regulatory_network")},
    }
    ctx = context(bad, patch)

    result, _, _, error, _ = _invoke_semantic_interpreter(
        ctx, {}, task, LLMUsage(budget_tokens=100000)
    )

    assert result is not None and error is None
    hypothesis = result.outcome_hypotheses[0]
    assert validate_outcome_hypotheses(task, [hypothesis]).valid
    assert hypothesis.outcome.granularity == "sample_specific"
    assert hypothesis.outcome.regulator_types == ["mirna"]
    assert hypothesis.outcome.target_types == ["gene"]
    assert set(hypothesis.outcome.entity_types) == {"mirna", "gene"}
    assert ctx.semantic_patcher.calls
    system_prompt = ctx.semantic_patcher.calls[0][0].content
    assert "Do not translate or paraphrase a quote" in system_prompt


def test_unknown_request_mode_for_workflow_selection_becomes_guidance():
    first = payload()
    first["request_mode"] = "unknown"
    ctx = context(first, {"hypothesis_index": 0, "outcome": {}})

    result, _, _, error, _ = run(ctx)

    assert result is not None and error is None
    # A workflow-selection question is deterministically guidance even when
    # the claims model left its request mode unknown.
    assert result.request_mode == "guidance"


def test_undecided_granularity_claims_gain_both_grounded_candidate_hypotheses():
    task = (
        "Which workflow infers a miRNA-to-gene regulatory network? "
        "I have not decided between one cohort network and separate "
        "per-patient networks, so please ask me."
    )
    first = payload()
    first["request_mode"] = "guidance"
    first["semantic_goal"] = "Identify a miRNA-to-gene network workflow"
    outcome = first["outcome_hypotheses"][0]["outcome"]
    quote = "miRNA-to-gene regulatory network"
    outcome["operation"] = claim(
        "infer", "infers a miRNA-to-gene regulatory network"
    )
    outcome["artifact_type"] = claim("regulatory_network", quote)
    outcome["granularity"] = claim("unknown")
    outcome["entity_types"] = [
        claim("mirna", quote),
        claim("gene", quote),
    ]
    outcome["regulator_types"] = [claim("mirna", quote)]
    outcome["target_types"] = [claim("gene", quote)]
    first_hypothesis = first["outcome_hypotheses"][0]
    first_hypothesis["assumptions"] = [
        "The workflow is capable of inferring regulatory relationships "
        "between miRNAs and genes."
    ]
    sample_hypothesis = deepcopy(first_hypothesis)
    sample_hypothesis["outcome"]["granularity"] = claim("sample_specific")
    sample_hypothesis["assumptions"] = [
        "The workflow can infer separate regulatory networks for each patient."
    ]
    first["outcome_hypotheses"].append(sample_hypothesis)
    ctx = context(
        first,
        AssertionError("A complete granularity clarification needs no review."),
    )

    result, usage, _, error, _ = _invoke_semantic_interpreter(
        ctx, {}, task, LLMUsage(budget_tokens=100000)
    )

    assert result is not None and error is None
    assert [call.role for call in usage.calls] == ["semantic_interpreter"]
    assert ctx.semantic_reviewer.calls == []
    assert "routing.semantic_interpretation_accepted" in {
        event for event, _ in ctx.recorder.events
    }
    hypotheses = result.outcome_hypotheses
    assert [item.outcome.granularity for item in hypotheses] == [
        "aggregate",
        "sample_specific",
    ]
    assert all(
        any(
            evidence.dimension == "granularity"
            and evidence.source == "explicit"
            for evidence in item.evidence
        )
        for item in hypotheses
    )
    assert validate_outcome_hypotheses(task, hypotheses).valid
    match = match_semantic_request(task, hypotheses, request_mode="guidance")
    assert match.status == "ambiguous"
    assert match.clarification_question == (
        "Should the result be aggregate or sample-specific?"
    )
    primary = select_primary_hypothesis(hypotheses, user_task=task)
    assert primary is not None
    assert primary.outcome.granularity == "unknown"


def test_schema_failure_uses_full_claim_repair_not_legacy_contract():
    ctx = context({"semantic_goal": "incomplete"}, payload())
    result, _, _, error, _ = run(ctx)
    assert result and error is None
    assert len(ctx.semantic_reviewer.calls) == 1 and not ctx.semantic_patcher.calls


def test_two_failed_attempts_never_become_keyword_recommendation():
    ctx = context({}, {})
    result, _, _, error, _ = run(ctx)
    assert result is None and error is not None
    assert recover_registry_guidance(TASK, ctx.project_policy.workflows, error) is None
    assert (
        match_registry_guidance_features("PUMA sample specific miRNA network") is None
    )
    assert len(ctx.semantic_interpreter.calls) + len(ctx.semantic_reviewer.calls) == 2


def test_wire_contract_through_real_sdk_and_production_interpreter():
    import httpx
    ChatOpenAI = pytest.importorskip(
        "langchain_openai",
        reason="The real-SDK wire contract runs in the acceptance dependency set.",
    ).ChatOpenAI

    bodies = []

    def handle(request):
        body = json.loads(request.content)
        bodies.append(body)
        name = body["tools"][0]["function"]["name"]
        return httpx.Response(
            200,
            json={
                "id": "offline",
                "object": "chat.completion",
                "created": 0,
                "model": "offline",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "one",
                                    "type": "function",
                                    "function": {
                                        "name": name,
                                        "arguments": json.dumps(payload()),
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        llm = ChatOpenAI(
            model="offline",
            api_key="offline-test",
            base_url="https://provider.invalid/v1",
            http_client=client,
            max_retries=0,
        )
        ctx = context(None, AssertionError("No review"))
        ctx.semantic_interpreter = llm.with_structured_output(
            SemanticClaims, method="function_calling", include_raw=True
        )
        result, _, _, error, _ = run(ctx)
    assert result and error is None and len(bodies) == 1
    schema = bodies[0]["tools"][0]["function"]["parameters"]
    props = schema["properties"]["outcome_hypotheses"]["items"]["properties"]
    assert "evidence" not in props
    support = props["outcome"]["properties"]["granularity"]["properties"]["support"][
        "anyOf"
    ][0]
    assert "value" not in support["properties"]


def legacy_context(first, second, *, policy="when_needed"):
    from netzoo_agent_core.llm import build_semantic_interpreter_prompt

    ctx = context(first, second)
    ctx.semantic_claims = False
    ctx.review_policy = policy
    ctx.semantic_prompt = build_semantic_interpreter_prompt()
    return ctx


def legacy_payload():
    return SemanticClaims.model_validate(payload()).to_internal().model_dump()


def test_default_contract_skips_review_without_changing_its_schema():
    ctx = legacy_context(legacy_payload(), AssertionError("No unnecessary review"))
    result, usage, _, error, _ = run(ctx)
    assert result is not None and error is None
    assert [call.role for call in usage.calls] == ["semantic_interpreter"]
    assert any(
        data.get("review_skipped") == "validated_complete_match"
        for _, data in ctx.recorder.events
    )


@pytest.mark.parametrize(
    "defect", ["ambiguous", "invalid_quote", "unknown_intent", "unknown_operation"]
)
def test_default_gate_preserves_needed_review(defect):
    first = legacy_payload()
    h = first["outcome_hypotheses"][0]
    if defect == "ambiguous":
        h["outcome"]["unresolved_dimensions"] = ["regulator_type"]
    elif defect == "invalid_quote":
        h["evidence"][0].update(source="explicit", text_span="absent phrase")
    elif defect == "unknown_operation":
        h["outcome"]["operation"] = "unknown"
        h["evidence"] = [e for e in h["evidence"] if e["dimension"] != "operation"]
    else:
        first["request_mode"] = "unknown"
    fixed = legacy_payload()
    second = {
        "request_mode": "guidance",
        "semantic_goal": fixed["semantic_goal"],
        "outcome_hypothesis": fixed["outcome_hypotheses"][0],
    }
    ctx = legacy_context(first, second)
    result, _, _, error, _ = run(ctx)
    assert result is not None and error is None
    assert len(ctx.semantic_patcher.calls) == 1
    assert validate_outcome_hypotheses(TASK, result.outcome_hypotheses).valid


def test_default_schema_and_experimental_schema_remain_separate_in_factory(monkeypatch):
    import netzoo_agent_core.graph.factory as factory
    from netzoo_agent_core.contracts.outcomes import (
        SemanticInterpretation,
        SemanticPatch,
        SemanticReview,
    )

    bindings = []

    class Provider:
        def with_structured_output(self, schema, **kwargs):
            bindings.append((schema, kwargs))
            return schema

    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "offline")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "offline")
    monkeypatch.setattr(factory, "build_llm", lambda *a, **kw: Provider())
    monkeypatch.setattr(factory, "compile_graph", lambda ctx, **kwargs: ctx)
    ctx = factory.build_graph("offline", 0, router_model_name="offline")
    assert not ctx.semantic_claims and ctx.review_policy == "when_needed"
    assert (ctx.semantic_interpreter, ctx.semantic_reviewer, ctx.semantic_patcher) == (
        SemanticInterpretation,
        SemanticReview,
        SemanticPatch,
    )
    experimental = factory.build_graph(
        "offline", 0, router_model_name="offline", semantic_contract="claims"
    )
    assert (
        experimental.semantic_claims
        and experimental.semantic_interpreter is SemanticClaims
    )
    claims_bindings = [kwargs for schema, kwargs in bindings if schema is SemanticClaims]
    assert claims_bindings and all(kwargs.get("strict") is True for kwargs in claims_bindings)


def test_no_text_can_add_missing_semantic_selection_tags():
    from netzoo_agent_core.contracts import TaskDecision

    interpretation = SemanticClaims.model_validate(payload()).to_internal()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=0.9,
        reason="Guidance",
        requested_outcome=interpretation.outcome_hypotheses[0].outcome,
    )
    result = decision_with_registry_signals(
        decision,
        "high order correlation batch correction",
        context(None, None).project_policy.workflows,
    )
    assert result is decision and result.requested_outcome.selection_tags == []


def test_paid_evaluation_contract_is_not_exercised_by_offline_fixture():
    from evaluate_routing import evaluate, RoutingScenario
    from netzoo_agent_core.contracts import IntentDecision
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation

    class Provider:
        def with_structured_output(self, schema, **kwargs):
            if schema is IntentDecision:
                return Adapter(
                    {"mode": "answer", "confidence": 0.9, "reason": "Guidance"}
                )
            if schema is SemanticInterpretation:
                return Adapter(legacy_payload())
            return Adapter(AssertionError("Unexpected review"))

    case = RoutingScenario(
        id="mirna-offline",
        language="en",
        category="positive",
        prompt=TASK,
        expected={
            "status": "exact",
            "actions": ["run_lioness_puma"],
            "artifact_type": "regulatory_network",
            "granularity": "sample_specific",
        },
    )
    report = evaluate(
        [case], provider=Provider(), model_name="offline", review_policy="when_needed"
    )
    assert report["results"][0]["status"] == "exact"
    # Log 265 (user decision A): PANDA-family guidance offers the unreliable_prior concern.
    assert report["results"][0]["call_roles"] == [
        "semantic_interpreter",
        "intent_router",
        "request_concerns",
    ]
    assert report["metadata"]["review_policy"] == "when_needed"
    assert report["metadata"]["semantic_contract"] == "legacy"


def test_default_graph_skips_review_but_keeps_guidance_out_of_executor(
    monkeypatch, tmp_path
):
    import netzoo_agent_core.graph.factory as factory
    from netzoo_agent_core.contracts import HumanMessage, IntentDecision
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
    from netzoo_agent_core.memory import UserProfileStore, EpisodeStore

    called = []

    class Provider:
        def with_structured_output(self, schema, **kwargs):
            class Bound:
                def invoke(self, messages):
                    called.append(schema.__name__)
                    if schema is SemanticInterpretation:
                        return legacy_payload()
                    if schema is IntentDecision:
                        # Even a mistaken intent cannot override guidance semantics.
                        return {"mode": "execute", "confidence": 1, "reason": "Execute"}
                    raise AssertionError("A complete match must not request review")

            return Bound()

        def invoke(self, messages):
            raise AssertionError(
                "Verified guidance does not need free-form response generation"
            )

    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "offline")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "offline")
    monkeypatch.setattr(factory, "build_llm", lambda *a, **kw: Provider())
    app = factory.build_graph(
        "offline",
        0,
        router_model_name="offline",
        profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"),
    )
    result = app.invoke({"messages": [HumanMessage(content=TASK)]})
    # Log 265 (user decision A): PANDA-family guidance offers the unreliable_prior concern.
    # Log 355: the study-purpose call comes after routing.
    # Log 379: the study purpose is read before routing.
    assert called == ["StudyPurposeProposal", "SemanticInterpretation", "IntentDecision", "StatedConcernClaims"]
    assert result["decision"]["should_execute"] is False
    assert result["decision"]["action"] == "no_tool"
    assert result["plan"]["status"] == "respond_only"
    assert result["tool_results"] == []
    assert "LIONESS-PUMA" in result["messages"][-1].content


def test_granularity_witness_replaces_an_unmatched_quote_without_a_review():
    """A verbatim granularity phrase outranks the model's own paraphrased quote."""
    bad = payload()
    bad["outcome_hypotheses"][0]["outcome"]["granularity"] = claim(
        "sample_specific", "not in original request"
    )
    ctx = context(bad, AssertionError("Reviewer must not run"))
    result, _, _, error, _ = run(ctx)
    assert result and error is None
    assert not ctx.semantic_patcher.calls and not ctx.semantic_reviewer.calls
    evidence = [
        item for item in result.outcome_hypotheses[0].evidence
        if item.dimension == "granularity"
    ]
    assert [(e.source, e.text_span) for e in evidence] == [(
        "explicit", "sample specific mi-rna regulator network",
    )]


# --- structured repair feedback for ontology rejections -------------------

SUBTYPE_TASK = (
    "Previously I ran PANDA on an expression matrix. This time I want to cluster "
    "patients into subtypes from somatic mutation data. Which workflow? Advice only."
)


def _mutation_as_result():
    """The traced claims shape: the input artifact written as the result."""
    return {
        "request_mode": "guidance",
        "semantic_goal": "Subtype patients from mutations",
        "outcome_hypotheses": [{
            "confidence": 0.9,
            "outcome": {
                "operation": claim("analyze", "cluster patients"),
                "artifact_type": claim("mutation_matrix", "somatic mutation data"),
                "granularity": claim("sample_specific", "cluster patients into subtypes"),
                "input_artifacts": [claim("mutation_matrix", "somatic mutation data")],
                "entity_types": [claim("sample", "patients")],
            },
        }],
    }


def _diagnostics(messages):
    return json.loads(messages[-1].content.split("\n", 1)[1])


def test_quote_only_rejection_keeps_issues_and_adds_failure_category():
    from netzoo_agent_core.interpretation.claim_prompt import claim_messages

    proposal = SemanticClaims.model_validate(payload())
    issues = ("hypothesis[0].ungrounded_evidence:regulator_type=mirna",)
    data = _diagnostics(claim_messages(TASK, proposal, issues, patching=True))
    assert set(data) == {"proposal", "issues", "issue_categories"}
    assert data["issue_categories"] == [{
        "issue": issues[0], "category": "invalid_reference", "action": "repair_citation",
    }]


def test_terminal_goal_conflict_names_the_required_artifact_and_request_facts():
    from netzoo_agent_core.interpretation.claim_prompt import claim_repair_feedback

    proposal = SemanticClaims.model_validate(_mutation_as_result())
    issues = validate_outcome_hypotheses(
        SUBTYPE_TASK, proposal.to_internal().outcome_hypotheses,
    ).issues
    feedback = claim_repair_feedback(SUBTYPE_TASK, proposal, issues)
    goal = next(i for i in feedback["repair_feedback"] if "terminal_goal_conflict" in i["issue"])
    assert goal["required_value"] == {"field": "artifact_type", "value": "sample_cluster_assignment"}
    assert goal["repairable_fields"] == ["artifact_type"]
    fields = goal["artifact_constraints"]["fields"]
    assert fields["granularity"] == {"enum": ["aggregate", "unknown"]}
    assert {(f["artifact"], f["status"]) for f in feedback["request_facts"]["inputs"]} == {
        ("expression_matrix", "historical"), ("mutation_matrix", "current"),
    }


def test_role_restoration_resolves_a_multiomic_reading_before_claim_repair():
    """Closed role witnesses correct this proposal without another model repair."""
    from netzoo_agent_core.interpretation.claim_prompt import claim_repair_feedback
    from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields

    task = "cohort-wide miRNA-gene network, which tool?"
    data = payload()
    # The recorded gran-mirna-agg-terse first pass: every support inferred.
    data["outcome_hypotheses"][0]["outcome"] = {
        "operation": claim("infer"),
        "artifact_type": claim("multi_omic_network"),
        "granularity": claim("aggregate"),
        "entity_types": [claim("mirna"), claim("gene")],
        "regulator_types": [claim("mirna")],
        "target_types": [claim("gene")],
    }
    proposal = SemanticClaims.model_validate(data)
    restored, restorations = restore_stated_fields(
        task, proposal.to_internal(), restore_explicit_scalar_evidence=True,
    )
    outcome = restored.outcome_hypotheses[0].outcome
    issues = validate_outcome_hypotheses(task, restored.outcome_hypotheses).issues
    assert outcome.artifact_type == "regulatory_network"
    assert outcome.regulator_types == ["mirna"]
    assert outcome.target_types == ["gene"]
    assert any(item["source"] == "unique_role_ontology_correction" for item in restorations)
    assert not issues
    assert claim_repair_feedback(task, proposal, issues) == {}


def test_stated_multi_regulator_conflict_requires_the_supporting_artifact():
    from netzoo_agent_core.interpretation.claim_prompt import claim_repair_feedback

    task = (
        "I want a single cohort-wide network of both miRNA and TF regulation "
        "of genes. Which workflow? Advice only."
    )
    data = payload()
    data["outcome_hypotheses"][0]["outcome"].update(
        artifact_type=claim("multi_omic_network", "network"),
        granularity=claim("aggregate", "cohort-wide"),
        regulator_types=[claim("mirna", "miRNA"), claim("tf", "TF")],
        target_types=[claim("gene", "genes")],
    )
    proposal = SemanticClaims.model_validate(data)
    issues = validate_outcome_hypotheses(
        task, proposal.to_internal().outcome_hypotheses,
    ).issues
    assert any("stated_roles_conflict:multi_omic_network" in item for item in issues)

    feedback = claim_repair_feedback(task, proposal, issues)
    conflict = next(
        item for item in feedback["repair_feedback"]
        if "stated_roles_conflict" in item["issue"]
    )

    assert conflict["required_value"] == {
        "field": "artifact_type", "value": "regulatory_network",
    }
    assert conflict["artifact_constraints"]["fields"]["artifact_type"] == {
        "const": "regulatory_network",
    }
    assert {item["regulator_type"] for item in feedback["request_facts"]["roles"]} == {
        "mirna", "tf",
    }


def test_repair_feedback_carries_no_prose_instructions():
    from netzoo_agent_core.interpretation.claim_prompt import claim_repair_feedback

    proposal = SemanticClaims.model_validate(_mutation_as_result())
    issues = validate_outcome_hypotheses(
        SUBTYPE_TASK, proposal.to_internal().outcome_hypotheses,
    ).issues
    text = json.dumps(claim_repair_feedback(SUBTYPE_TASK, proposal, issues))
    for key in ('"instruction"', '"field_constraints_note"', '"shape"', '"roles":"'):
        assert key not in text


def test_patcher_receives_structured_feedback_for_an_ontology_rejection():
    ctx = context(_mutation_as_result(), {"hypothesis_index": 0, "outcome": {}})
    _invoke_semantic_interpreter(ctx, {}, SUBTYPE_TASK, LLMUsage(budget_tokens=100000))
    assert ctx.semantic_patcher.calls
    data = _diagnostics(ctx.semantic_patcher.calls[0])
    assert any(
        item.get("required_value", {}).get("value") == "sample_cluster_assignment"
        for item in data["repair_feedback"]
    )


def test_undecided_granularity_feedback_names_unknown_as_the_required_value():
    from netzoo_agent_core.interpretation.claim_prompt import claim_repair_feedback

    task = (
        "Which workflow infers a miRNA-to-gene regulatory network? I have not decided "
        "between one cohort network and separate per-patient networks."
    )
    data = payload()
    data["outcome_hypotheses"][0]["outcome"]["granularity"] = claim("aggregate")
    proposal = SemanticClaims.model_validate(data)
    issues = validate_outcome_hypotheses(task, proposal.to_internal().outcome_hypotheses).issues
    items = claim_repair_feedback(task, proposal, issues)["repair_feedback"]
    open_item = next(i for i in items if "undecided_granularity" in i["issue"])
    assert open_item["required_value"] == {"field": "granularity", "value": "unknown"}
    assert open_item["repairable_fields"] == ["granularity"]

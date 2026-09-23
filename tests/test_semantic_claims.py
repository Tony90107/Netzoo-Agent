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


def run(ctx):
    return _invoke_semantic_interpreter(ctx, {}, TASK, LLMUsage(budget_tokens=100000))


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
            "repairs": [
                {
                    "hypothesis_index": 1,
                    "outcome": {"granularity": claim("aggregate", "network")},
                }
            ]
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


def test_repair_rejects_unknown_or_duplicate_indices():
    for indices in ([1], [0, 0]):
        repair = SemanticClaimRepair.model_validate(
            {"repairs": [{"hypothesis_index": i, "outcome": {}} for i in indices]}
        )
        with pytest.raises(ValueError):
            repair.apply(SemanticClaims.model_validate(payload()))


def test_bad_quote_is_repaired_without_retyping_outcome():
    bad = payload()
    bad["outcome_hypotheses"][0]["outcome"]["granularity"] = claim(
        "sample_specific", "not in original request"
    )
    ctx = context(
        bad,
        {
            "repairs": [
                {
                    "hypothesis_index": 0,
                    "outcome": {
                        "granularity": claim("sample_specific", "sample specific")
                    },
                }
            ]
        },
    )
    result, _, _, error, _ = run(ctx)
    assert result and error is None
    assert len(ctx.semantic_patcher.calls) == 1
    assert validate_outcome_hypotheses(TASK, result.outcome_hypotheses).valid
    assert result.outcome_hypotheses[0].outcome.regulator_types == ["mirna"]


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
    from langchain_openai import ChatOpenAI

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
    assert report["results"][0]["call_roles"] == [
        "semantic_interpreter",
        "intent_router",
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
    assert called == ["SemanticInterpretation", "IntentDecision"]
    assert result["decision"]["should_execute"] is False
    assert result["decision"]["action"] == "no_tool"
    assert result["plan"]["status"] == "respond_only"
    assert result["tool_results"] == []
    assert "LIONESS-PUMA" in result["messages"][-1].content

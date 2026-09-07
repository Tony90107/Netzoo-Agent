"""Real SDK -> intercepted HTTP body; no network or model accuracy claims."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticReview  # noqa: E402


@pytest.fixture(autouse=True)
def _disable_external_tracing(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")


@pytest.mark.parametrize("model", [SemanticInterpretation, SemanticReview])
def test_provider_wire_preserves_required_fields_in_every_artifact_branch(model):
    ChatOpenAI = pytest.importorskip("langchain_openai").ChatOpenAI
    import httpx
    from jsonschema import Draft202012Validator

    captured = []

    def handle(request):
        body = json.loads(request.content)
        captured.append(body)
        return httpx.Response(200, json={
            "id": "offline", "object": "chat.completion", "created": 0, "model": "offline",
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None, "tool_calls": [{
                    "id": "one", "type": "function", "function": {
                        "name": model.__name__, "arguments": "{}",
                    },
                }],
            }}],
        })

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        llm = ChatOpenAI(model="openai/gpt-4o-mini", api_key="offline-test",
                         base_url="https://provider.invalid/v1", http_client=client, max_retries=0)
        result = llm.with_structured_output(model, method="function_calling", include_raw=True).invoke("Offline test")
    assert len(captured) == 1
    assert result["parsed"] is None and result["parsing_error"] is not None
    properties = captured[0]["tools"][0]["function"]["parameters"]["properties"]
    hypothesis = (properties["outcome_hypotheses"]["items"] if model is SemanticInterpretation
                  else properties["outcome_hypothesis"])
    outcome = hypothesis["properties"]["outcome"]
    assert set(outcome["required"]) == {"operation", "artifact_type", "granularity"}
    assert outcome["additionalProperties"] is False
    validator = Draft202012Validator(outcome)
    for branch in outcome["anyOf"]:
        # A model reading an artifact branch must still see all required fields.
        assert branch["type"] == "object"
        assert set(branch["required"]) == set(outcome["required"])
        assert set(branch["required"]) <= branch["properties"].keys()
        assert branch["properties"]["operation"]["enum"] == outcome["properties"]["operation"]["enum"]
        artifact = branch["properties"]["artifact_type"]["const"]
        valid = {"operation": "analyze", "artifact_type": artifact, "granularity": "aggregate"}
        validator.validate(valid)
        for field in outcome["required"]:
            assert not validator.is_valid({k: v for k, v in valid.items() if k != field})
    assert not validator.is_valid({"operation": "analyze", "artifact_type": "sample_cluster_assignment",
                                   "granularity": "sample_specific"})
    assert not validator.is_valid({"operation": "analyze", "artifact_type": "sample_cluster_assignment",
                                   "granularity": "aggregate", "entity_types": ["gene"]})


@pytest.mark.parametrize("case_id", ["original-q1", "original-q2", "original-q3"])
@pytest.mark.parametrize("repair_succeeds", [True, False], ids=["complete-repair", "still-missing"])
@pytest.mark.parametrize("defect", ["missing-required", "missing-input"])
def test_latest_failures_through_real_sdk_and_production_routing(case_id, repair_succeeds, defect):
    """Scripted replies test transport and validation, never reviewer intelligence."""
    ChatOpenAI = pytest.importorskip("langchain_openai").ChatOpenAI
    import httpx
    from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios
    from routing_repair_replay import reconstructed_proposal
    from test_routing_evaluation import hypothesis

    first = reconstructed_proposal(case_id, "missing-required")
    reviewed = hypothesis()
    for evidence in reviewed["evidence"]:
        evidence.update(source="inferred", text_span=None)
    if defect == "missing-input":
        from copy import deepcopy
        first_item = deepcopy(reviewed)
        first_item["outcome"]["input_artifacts"] = []
        first_item["evidence"] = [e for e in first_item["evidence"] if e["dimension"] != "input_artifact"]
        first = {"request_mode": "guidance", "semantic_goal": "Subtype patients", "outcome_hypotheses": [first_item]}
    if not repair_succeeds:
        if defect == "missing-required":
            del reviewed["outcome"]["operation"]
        else:
            reviewed = deepcopy(first_item)
    replies = {
        "SemanticInterpretation": first,
        "SemanticReview": {"request_mode": "guidance", "semantic_goal": "Subtype patients",
                           "outcome_hypothesis": reviewed},
        "IntentDecision": {"mode": "answer", "confidence": .95, "reason": "Guidance only"},
    }
    # 2026-09-06: a first pass that parsed is repaired field by field, so the
    # second call's tool is SemanticPatch. `missing-required` still parses badly
    # and keeps the whole-review tool above; both wire shapes stay covered here.
    replies["SemanticPatch"] = {
        "outcome": {"input_artifacts": reviewed["outcome"]["input_artifacts"]},
        "evidence_additions": [
            evidence for evidence in reviewed["evidence"]
            if evidence["dimension"] == "input_artifact"
        ],
    }
    captured = []

    def handle(request):
        body = json.loads(request.content)
        captured.append(body)
        name = body["tools"][0]["function"]["name"]
        return httpx.Response(200, json={
            "id": "offline", "object": "chat.completion", "created": 0, "model": "offline",
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None, "tool_calls": [{
                    "id": "one", "type": "function", "function": {
                        "name": name, "arguments": json.dumps(replies[name]),
                    },
                }],
            }}],
        })

    case = next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == case_id)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        llm = ChatOpenAI(model="openai/gpt-4o-mini", api_key="offline-test",
                         base_url="https://provider.invalid/v1", http_client=client, max_retries=0)
        report = evaluate([case], provider=llm, model_name="fixture")
    assert len(captured) == (3 if repair_succeeds else 2)
    review_text = json.dumps(captured[1]["messages"])
    if defect == "missing-required":
        assert "add_required_field" in review_text
        assert "outcome_hypothesis.outcome.operation" in review_text
        if case_id == "original-q2":
            assert "outcome_hypothesis.outcome.granularity" in review_text
        if case_id == "original-q3":
            assert "schema_validation:outcome_hypotheses.1.outcome.operation:missing" in review_text
    else:
        assert "restore_current_input" in review_text
        assert "outcome_hypothesis.outcome.input_artifacts" in review_text
    row = report["results"][0]
    assert row["interaction_passed"]
    assert row["review_repair_correct"] is repair_succeeds
    assert report["summary"]["review_repair_rate"] == int(repair_succeeds)
    assert row["status"] == ("exact" if repair_succeeds else None)
    assert row["passed"] is repair_succeeds
    if repair_succeeds:
        assert row["outcome"]["input_artifacts"] == ["mutation_matrix"]
        assert row["outcome"]["artifact_type"] == "sample_cluster_assignment"
    else:
        assert row["outcome"] == {}
        assert not row["next_step"]["allow_workflow_continuation"]
    assert report["metadata"]["source"] == "fixture"

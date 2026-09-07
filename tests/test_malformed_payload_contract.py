"""P0: malformed provider payloads stay located schema failures, never TypeError.

A provider may return any JSON shape for a declared field. When local
normalization touches such a value before strict validation, a schema failure
becomes a `TypeError`, routing loses its reviewer attempt, and the fallback
claims the provider was unavailable instead of naming the bad field. These
regressions pin the raw-value contract only; they measure no model accuracy.
"""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticReview  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402

from test_routing_evaluation import FixtureProvider, hypothesis, run  # noqa: E402


def _outcome(value):
    def apply(item):
        item["outcome"]["input_artifacts"] = value
    return apply


def _selection_tags(value):
    def apply(item):
        item["outcome"]["selection_tags"] = value
    return apply


def _dimension(value):
    def apply(item):
        item["evidence"][1]["dimension"] = value
    return apply


def _evidence(value):
    def apply(item):
        item["evidence"] = value
    return apply


# (mutation, located path inside one hypothesis). Each raw value is a shape a
# provider can legally emit as JSON; none of them may reach a lookup untyped.
MALFORMED = {
    "input-artifact-unknown-enum": (_outcome(["somatic_mutation"]), "outcome.input_artifacts.0"),
    # Objects that mirror this contract's own field names are normalized; see
    # tests/test_transport_shape_normalization.py. An object carrying a key that
    # is not an outcome field leaves its meaning undecided and stays malformed.
    "input-artifact-dict-item": (_outcome([{"artifact_type": "mutation_matrix", "source": "explicit"}]), "outcome.input_artifacts.0"),
    "input-artifact-list-item": (_outcome([["mutation_matrix"]]), "outcome.input_artifacts.0"),
    "input-artifact-null-item": (_outcome([None]), "outcome.input_artifacts.0"),
    "input-artifacts-string": (_outcome("mutation_matrix"), "outcome.input_artifacts"),
    "input-artifacts-mapping": (_outcome({"0": "mutation_matrix"}), "outcome.input_artifacts"),
    "input-artifacts-number": (_outcome(5), "outcome.input_artifacts"),
    "selection-tags-dict-item": (_selection_tags([{"tag": "sparse"}]), "outcome.selection_tags.0"),
    "selection-tags-list-item": (_selection_tags([["sparse"]]), "outcome.selection_tags.0"),
    "selection-tags-number": (_selection_tags(5), "outcome.selection_tags"),
    "evidence-dimension-dict": (_dimension({"dimension": "input_artifact"}), "evidence.1.dimension"),
    "evidence-dimension-list": (_dimension(["input_artifact"]), "evidence.1.dimension"),
    "evidence-dimension-null": (_dimension(None), "evidence.1.dimension"),
    "evidence-mapping": (_evidence({"dimension": "input_artifact"}), "evidence"),
    "evidence-number": (_evidence(7), "evidence"),
    "outcome-not-a-mapping": (lambda item: item.update(outcome="mutation_matrix"), "outcome"),
    "outcome-null": (lambda item: item.update(outcome=None), "outcome"),
}


def malformed_item(case_id):
    item = hypothesis()
    MALFORMED[case_id][0](item)
    return item


def payload_for(model, item):
    body = {"request_mode": "guidance", "semantic_goal": "Subtype patients"}
    if model is SemanticInterpretation:
        return {**body, "outcome_hypotheses": [deepcopy(item)]}
    return {**body, "outcome_hypothesis": deepcopy(item)}


def located(model, path):
    prefix = "outcome_hypotheses.0" if model is SemanticInterpretation else "outcome_hypothesis"
    return f"{prefix}.{path}" if path else prefix


@pytest.mark.parametrize("model", [SemanticInterpretation, SemanticReview], ids=["interpretation", "review"])
@pytest.mark.parametrize("case_id", sorted(MALFORMED), ids=sorted(MALFORMED))
def test_malformed_raw_value_is_a_located_schema_failure(model, case_id):
    """A TypeError here fails the test: strict validation must name the field."""
    payload = payload_for(model, malformed_item(case_id))

    with pytest.raises(ValidationError) as raised:
        model.model_validate(payload)

    locations = [".".join(str(part) for part in issue["loc"]) for issue in raised.value.errors()]
    assert located(model, MALFORMED[case_id][1]) in locations


@pytest.mark.parametrize("model", [SemanticInterpretation, SemanticReview], ids=["interpretation", "review"])
def test_a_non_mapping_hypothesis_is_also_located(model):
    payload = payload_for(model, "mutation_matrix")

    with pytest.raises(ValidationError) as raised:
        model.model_validate(payload)

    locations = [".".join(str(part) for part in issue["loc"]) for issue in raised.value.errors()]
    assert located(model, "") in locations


@pytest.mark.parametrize("case_id", sorted(MALFORMED), ids=sorted(MALFORMED))
def test_structured_output_seam_hands_raw_arguments_to_strict_validation(case_id):
    """`semantic_payload` must not normalize, alias or index raw provider values."""
    arguments = payload_for(SemanticInterpretation, malformed_item(case_id))
    raw = SimpleNamespace(tool_calls=[{"name": "SemanticInterpretation", "args": arguments}])

    payload, returned_raw = semantic_payload(
        {"parsed": None, "raw": raw, "parsing_error": ValueError("invalid arguments")}
    )

    assert payload is arguments
    assert returned_raw is raw
    with pytest.raises(ValidationError):
        SemanticInterpretation.model_validate(payload)


def test_structured_output_seam_rejects_a_malformed_tool_call_entry():
    raw = SimpleNamespace(tool_calls=["SemanticInterpretation"])

    with pytest.raises(ValueError) as raised:
        semantic_payload({"parsed": None, "raw": raw, "parsing_error": None})

    assert not isinstance(raised.value, (TypeError, AttributeError))


@pytest.mark.parametrize("case_id", sorted(MALFORMED), ids=sorted(MALFORMED))
def test_malformed_first_pass_still_reaches_the_reviewer(case_id):
    """The reviewer attempt is the repair path; a local crash would remove it."""
    provider = FixtureProvider(
        first=payload_for(SemanticInterpretation, malformed_item(case_id)),
    )

    row = run(provider)["results"][0]

    assert row["call_roles"] == ["semantic_interpreter", "semantic_reviewer", "intent_router"]
    assert row["diagnostics"] == ["schema_validation"]
    assert row["review_repair_attempted"] and row["review_repair_validated"]
    assert row["status"] == "exact"


@pytest.mark.parametrize("case_id", sorted(MALFORMED), ids=sorted(MALFORMED))
def test_malformed_on_both_attempts_is_a_schema_failure_not_a_provider_outage(case_id):
    item = malformed_item(case_id)
    provider = FixtureProvider(
        first=payload_for(SemanticInterpretation, item),
        review=payload_for(SemanticReview, item),
    )

    row = run(provider)["results"][0]

    assert row["status"] is None
    assert row["match_basis"] != "provider_unavailable"
    assert row["diagnostics"] == ["schema_validation"]
    assert row["outcome"] == {}
    assert not row["review_repair_validated"]
    assert not row["should_execute"] and row["action"] == "no_tool"
    assert not row["next_step"]["allow_workflow_continuation"]


def test_recorded_validation_issues_keep_the_shape_without_the_value():
    """Traces need the offending path, code and shape, never the raw content."""
    from netzoo_agent_core.graph.router_invocation import _validation_issue_types

    payload = payload_for(SemanticInterpretation, malformed_item("input-artifact-dict-item"))
    payload["outcome_hypotheses"][0]["outcome"]["input_artifacts"] = [{"patient_id": "PT-0001", "n": 12}]
    with pytest.raises(ValidationError) as raised:
        SemanticInterpretation.model_validate(payload)

    issues = _validation_issue_types(raised.value)

    issue = next(item for item in issues if item["location"][-2:] == ["input_artifacts", "0"])
    assert issue["type"] == "literal_error"
    assert issue["input_type"] == "dict"
    assert "PT-0001" not in str(issues)


def test_non_validation_errors_still_report_no_shape():
    from netzoo_agent_core.graph.router_invocation import _validation_issue_types

    assert _validation_issue_types(TypeError("unhashable type: 'dict'")) == []


WIRE_CASES = ["input-artifact-dict-item", "selection-tags-dict-item", "evidence-dimension-dict"]


@pytest.mark.parametrize("case_id", WIRE_CASES, ids=WIRE_CASES)
def test_real_sdk_arguments_reach_strict_validation_and_the_reviewer(case_id):
    """The true parsed=None path: raw function arguments, no scripted adapter."""
    ChatOpenAI = pytest.importorskip("langchain_openai").ChatOpenAI
    import httpx
    import json
    from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios

    repaired = hypothesis()
    for evidence in repaired["evidence"]:
        evidence.update(source="inferred", text_span=None)
    replies = {
        "SemanticInterpretation": payload_for(SemanticInterpretation, malformed_item(case_id)),
        "SemanticReview": payload_for(SemanticReview, repaired),
        "IntentDecision": {"mode": "answer", "confidence": 0.95, "reason": "Guidance only"},
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

    case = next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q2")
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        llm = ChatOpenAI(model="openai/gpt-4o-mini", api_key="offline-test",
                         base_url="https://provider.invalid/v1", http_client=client, max_retries=0)
        row = evaluate([case], provider=llm, model_name="fixture")["results"][0]

    assert len(captured) == 3
    assert row["diagnostics"] == ["schema_validation"]
    assert row["review_repair_attempted"] and row["review_repair_validated"]
    assert row["outcome"]["input_artifacts"] == ["mutation_matrix"]
    review_text = json.dumps(captured[1]["messages"])
    assert "schema_validation:outcome_hypotheses.0." in review_text


def issue_for(payload, tail):
    from netzoo_agent_core.graph.router_invocation import _validation_issue_types

    with pytest.raises(ValidationError) as raised:
        SemanticInterpretation.model_validate(payload)
    issues = _validation_issue_types(raised.value)
    return next(item for item in issues if item["location"][-len(tail):] == tail)


def payload_with_input(value):
    payload = payload_for(SemanticInterpretation, hypothesis())
    payload["outcome_hypotheses"][0]["outcome"]["input_artifacts"] = [value]
    return payload


def test_a_canonical_looking_invalid_literal_is_recorded_verbatim():
    """One live run then answers which name the model actually invented."""
    issue = issue_for(payload_with_input("somatic_mutation"), ["input_artifacts", "0"])

    assert issue["input_type"] == "str"
    assert issue["input_value"] == "somatic_mutation"


@pytest.mark.parametrize("value, expected_type", [
    ("我手邊有一份體細胞突變矩陣", "str"),
    ("x" * 65, "str"),
    ({"type": "mutation_matrix", "source": "explicit"}, "dict"),
    (["mutation_matrix"], "list"),
    (None, "NoneType"),
    ("patient PT-0001 had 12 mutations, contact ward@example.org", "str"),
])
def test_only_identifier_shaped_values_are_recorded(value, expected_type):
    """Free text may quote the request, so only canonical-looking names are kept."""
    issue = issue_for(payload_with_input(value), ["input_artifacts", "0"])

    assert issue["input_type"] == expected_type
    assert "input_value" not in issue


# Systematically derived shapes: every contract field is covered, so a new field
# joins this matrix without a new hand-written case.
def contract_fields():
    from netzoo_agent_core.contracts.outcomes import (
        OutcomeEvidence,
        OutcomeHypothesis,
        RequestedOutcome,
    )

    for model, prefix in (
        (OutcomeHypothesis, ()),
        (RequestedOutcome, ("outcome",)),
        (OutcomeEvidence, ("evidence", 0)),
    ):
        for name in model.model_fields:
            if name == "outcome" or (prefix == ("evidence", 0) and name == "evidence"):
                continue
            yield model, prefix, name


BAD_VALUES = {
    "dict": {"unexpected": "shape"},
    "list": ["unexpected", "shape"],
    "number": 7,
    "nested-null": [None],
    "unknown-enum": "not_a_registered_ontology_value",
}


def valid_hypothesis_payload():
    item = hypothesis()
    item["evidence"] = [item["evidence"][1]]
    return payload_for(SemanticInterpretation, item)


@pytest.mark.parametrize("shape", sorted(BAD_VALUES), ids=sorted(BAD_VALUES))
@pytest.mark.parametrize(
    "field", list(contract_fields()),
    ids=[f"{'.'.join(str(part) for part in prefix)}.{name}".lstrip(".")
         for _, prefix, name in contract_fields()],
)
def test_every_contract_field_rejects_every_malformed_shape_without_a_typeerror(field, shape):
    _, prefix, name = field
    payload = valid_hypothesis_payload()
    target = payload["outcome_hypotheses"][0]
    for part in prefix:
        target = target[part]
    target[name] = BAD_VALUES[shape]

    try:
        SemanticInterpretation.model_validate(payload)
    except ValidationError as error:
        located = ["outcome_hypotheses", "0", *(str(part) for part in prefix), name]
        assert any(
            [str(part) for part in issue["loc"]][:len(located)] == located
            for issue in error.errors()
        ), f"{name}={shape} produced {[issue['loc'] for issue in error.errors()]}"


def test_a_rejected_object_records_its_field_names():
    """Live runs show objects where a literal belongs; the keys say which shape."""
    issue = issue_for(
        payload_with_input({"artifact_type": "mutation_matrix", "role": "current"}),
        ["input_artifacts", "0"],
    )

    assert issue["input_type"] == "dict"
    assert issue["input_keys"] == ["artifact_type", "role"]


def test_object_field_names_are_bounded_and_identifier_shaped():
    value = {"突變矩陣": 1, "a" * 65: 2, "ok_key": 3, "with space": 4}

    issue = issue_for(payload_with_input(value), ["input_artifacts", "0"])

    assert issue["input_keys"] == ["ok_key"]


def test_non_object_values_record_no_field_names():
    for value in ("somatic_mutation", ["mutation_matrix"], None):
        issue = issue_for(payload_with_input(value), ["input_artifacts", "0"])
        assert "input_keys" not in issue

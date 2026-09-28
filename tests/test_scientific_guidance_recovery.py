"""Scientific questions retain their subject without authorizing execution."""

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome
from netzoo_agent_core.contracts.outcomes import OutcomeEvidence
from netzoo_agent_core.graph.response_context import validated_workflow_context
from netzoo_agent_core.interpretation.registry_guidance import should_expand_guidance_catalog
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
from test_semantic_claims import claim, context, legacy_context, run

ROOT = Path(__file__).parents[1]
CASES = [
    ("借用近緣物種的結合位點先驗建立調控網路，如何透過機率量化先驗的不可靠程度？",
     "regulatory_network", "aggregate", ["tf", "gene"]),
    ("每一位病患都只抽一次血，如何估計每個人的調控連線強度，再與血壓變化做迴歸？",
     "regulatory_network", "sample_specific", ["tf", "gene"]),
    ("已有調控者與受質的連線權重矩陣，超級調控者把受質吸進巨型社群；需要什麼結構假設的工具？",
     "community_assignment", "aggregate", ["tf", "gene"]),
]


def test_method_preference_cannot_replace_an_unknown_biological_result():
    task = "How can we use probabilistic uncertainty to weigh unreliable binding-site priors?"
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(operation="explain", artifact_type="unknown",
                                 granularity="unknown", selection_tags=["bayesian"]),
        confidence=.9, evidence=[OutcomeEvidence(
            dimension="selection_tag", value="bayesian", source="explicit",
            text_span="probabilistic uncertainty",
            rationale="The request asks for a probabilistic philosophy, not co-expression biology.",
        )],
    )
    match = match_semantic_request(task, [hypothesis], request_mode="guidance")
    assert match.status == "ambiguous"
    assert match.matched_actions == []


def test_subject_recovery_is_requested_even_with_a_known_method_preference():
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
    from netzoo_agent_core.interpretation.guidance_subject import guidance_subject_review_issues
    draft = SemanticInterpretation.model_validate(empty_reading())
    hypothesis = draft.outcome_hypotheses[0].model_copy(update={
        "outcome": draft.outcome_hypotheses[0].outcome.model_copy(update={
            "granularity": "unknown", "selection_tags": ["bayesian"],
        }),
    })
    draft = draft.model_copy(update={"outcome_hypotheses": [hypothesis]})
    assert guidance_subject_review_issues(draft)


def test_unknown_subject_uses_small_conditional_catalog_not_all_compatible_methods():
    from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification
    from netzoo_agent_core.contracts import LLMUsage
    from netzoo_agent_core.graph.discriminator import invoke_semantic_discriminator
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
    from types import SimpleNamespace
    draft = SemanticInterpretation.model_validate(empty_reading())
    outcome = draft.outcome_hypotheses[0].outcome.model_copy(update={"granularity": "unknown"})
    draft = draft.model_copy(update={"outcome_hypotheses": [
        draft.outcome_hypotheses[0].model_copy(update={"outcome": outcome}),
    ]})
    match = match_semantic_request("uncertain scientific subject", draft.outcome_hypotheses,
                                  request_mode="guidance")
    adapter = SimpleNamespace(invoke=lambda _: pytest.fail("method tags cannot resolve unknown biology"))
    _, unchanged, usage, _ = invoke_semantic_discriminator(
        SimpleNamespace(semantic_discriminator=adapter), {}, "prior uncertainty", draft,
        match, LLMUsage(), [],
    )
    assert unchanged == match and not usage.calls
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False,
                            confidence=.5, reason="Unresolved scientific subject",
                            requested_outcome=outcome, outcome_hypotheses=draft.outcome_hypotheses,
                            capability_match_status="ambiguous", hypothesis_actions=match.hypothesis_actions)
    policy = ProjectPolicyLoader(ROOT).load()
    assert render_outcome_clarification(decision, policy) is None
    facts = validated_workflow_context(decision, policy, include_all=True)
    import json
    assert len(json.dumps(facts)) < 20_000
    assert facts["selection_constraints"]["catalog_status"].startswith("conditional")
    assert "not calibrated posterior" in facts["selection_constraints"]["method_philosophies"]["message_passing"]


def empty_reading():
    return {
        "request_mode": "guidance", "semantic_goal": "Explain the scientific question",
        "outcome_hypotheses": [{"outcome": {
            "operation": "explain", "artifact_type": "unknown",
            "granularity": "not_applicable",
        }, "confidence": .9, "evidence": [{
            "dimension": "operation", "value": "explain", "source": "inferred",
            "rationale": "The user asks for an explanation.",
        }]}],
    }


def reviewed_hypothesis(artifact, granularity, entities):
    outcome = RequestedOutcome(
        operation="explain", artifact_type=artifact, granularity=granularity,
        entity_types=entities,
        regulator_types=["tf"] if artifact == "regulatory_network" else [],
        target_types=["gene"] if artifact == "regulatory_network" else [],
    )
    pairs = [("operation", "explain"), ("artifact_type", artifact),
             ("granularity", granularity)]
    pairs += [("entity_type", entity) for entity in entities]
    pairs += [("regulator_type", item) for item in outcome.regulator_types]
    pairs += [("target_type", item) for item in outcome.target_types]
    return OutcomeHypothesis(outcome=outcome, confidence=.9, evidence=[
        {"dimension": key, "value": value, "source": "inferred",
         "rationale": "The scientific subject and requested result entail this dimension."}
        for key, value in pairs
    ])


@pytest.mark.parametrize("task,artifact,granularity,entities", CASES)
def test_empty_explanation_is_reviewed_and_recovers_scientific_candidates(
    task, artifact, granularity, entities,
):
    recovered = reviewed_hypothesis(artifact, granularity, entities)
    review = {"request_mode": "guidance", "semantic_goal": "Explain the scientific analysis",
              "outcome_hypothesis": recovered.model_dump()}
    ctx = legacy_context(empty_reading(), review)

    result, usage, _, error, _ = run(ctx, task)

    assert error is None and result is not None
    assert [item.role for item in usage.calls] == ["semantic_interpreter", "semantic_reviewer"]
    assert result.request_mode == "guidance"
    assert result.outcome_hypotheses[0].outcome.artifact_type == artifact
    assert result.outcome_hypotheses[0].outcome.granularity == granularity
    match = match_semantic_request(task, result.outcome_hypotheses, request_mode="guidance")
    assert match.matched_actions or match.hypothesis_actions
    if artifact == "community_assignment":
        assert match.matched_actions == ["run_condor"]
    elif granularity == "sample_specific":
        assert "run_lioness_panda" in [*match.matched_actions, *match.hypothesis_actions]


def test_claim_contract_also_reviews_an_empty_scientific_subject():
    task, artifact, granularity, entities = CASES[1]
    recovered = reviewed_hypothesis(artifact, granularity, entities).outcome.model_dump()
    first = {
        "request_mode": "guidance", "semantic_goal": "Explain the scientific question",
        "outcome_hypotheses": [{"confidence": .9, "outcome": {
            "operation": claim("explain"), "artifact_type": claim("unknown"),
            "granularity": claim("not_applicable"),
        }}],
    }
    fields = {}
    for key, value in recovered.items():
        if key in {"display_entities", "unresolved_dimensions"}:
            fields[key] = value
        elif isinstance(value, list):
            fields[key] = [claim(item) for item in value]
        else:
            fields[key] = claim(value)
    ctx = context(first, {"hypothesis_index": 0, "outcome": fields})

    result, usage, _, error, _ = run(ctx, task)

    assert error is None and result is not None
    assert len(usage.calls) == 2
    assert result.outcome_hypotheses[0].outcome.artifact_type == artifact
    assert result.outcome_hypotheses[0].outcome.granularity == granularity


def test_genuine_definition_can_remain_an_explanation_after_review():
    draft = empty_reading()
    ctx = legacy_context(draft, {"request_mode": "guidance", "semantic_goal": "Define probability",
                               "outcome_hypothesis": draft["outcome_hypotheses"][0]})
    result, usage, _, error, _ = run(ctx, "What does a probability distribution mean?")
    assert error is None and result is not None
    assert len(usage.calls) == 2
    assert result.outcome_hypotheses[0].outcome.artifact_type == "unknown"
    assert match_semantic_request("Definition", result.outcome_hypotheses,
                                  request_mode="guidance").status == "not_applicable"


@pytest.mark.parametrize("claims_contract", [False, True])
@pytest.mark.parametrize("artifact,granularity", [
    ("regulatory_network", "sample_specific"), ("community_assignment", "unknown"),
])
def test_production_subject_review_restores_only_subject_and_ontology_scale(claims_contract, artifact, granularity):
    from types import SimpleNamespace
    from test_semantic_claims import Adapter
    from netzoo_agent_core.interpretation.guidance_subject import GuidanceSubjectReview
    first = empty_reading()
    if claims_contract:
        first["outcome_hypotheses"][0] = {"confidence": .9, "outcome": {
            "operation": claim("explain"), "artifact_type": claim("unknown"),
            "granularity": claim("not_applicable"),
        }}
    ctx = context(first, AssertionError("general review must not replace focused review")) if claims_contract else legacy_context(first, AssertionError("general review must not replace focused review"))
    adapter = Adapter({"artifact_type": artifact, "granularity": granularity,
                       "artifact_rationale": "The question concerns this scientific object.",
                       "granularity_rationale": "The question determines the scale where stated."})
    bound = []
    def bind(schema, **kwargs):
        bound.append(schema)
        return adapter
    ctx.selection_condition_llm = SimpleNamespace(with_structured_output=bind)
    task = CASES[1 if artifact == "regulatory_network" else 2][0]
    result, usage, _, error, _ = run(ctx, task)
    assert result is not None and error is None
    assert bound == [GuidanceSubjectReview] and len(usage.calls) == 2
    outcome = result.outcome_hypotheses[0].outcome
    assert outcome.artifact_type == artifact
    assert outcome.granularity == ("aggregate" if artifact == "community_assignment" else granularity)
    assert not outcome.regulator_types and not outcome.selection_tags
    match = match_semantic_request(task, result.outcome_hypotheses, request_mode="guidance")
    assert "run_condor" in match.matched_actions if artifact == "community_assignment" else "run_lioness_panda" in match.hypothesis_actions


def test_unresolved_guidance_still_exposes_catalog_without_execution_authority():
    policy = ProjectPolicyLoader(ROOT).load()
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=.9,
        reason="Conceptual guidance", intent_type="answer_question",
        requested_outcome=RequestedOutcome(operation="explain", artifact_type="unknown",
                                           granularity="not_applicable"),
        capability_match_status="not_applicable",
    )
    before = deepcopy(decision.model_dump())
    task = CASES[2][0]
    expanded = should_expand_guidance_catalog(decision, task)
    facts = validated_workflow_context(decision, policy, include_all=expanded, task=task)
    assert expanded
    assert {"run_condor", "run_lioness_panda"} <= {item["action"] for item in facts["workflows"]}
    assert decision.model_dump() == before
    assert decision.action == "no_tool" and not decision.should_execute


@pytest.mark.parametrize("shape", ["outcome_hypotheses", "outcome_hypothesis"])
def test_misnested_dimensions_preserve_patient_subject_without_loosening_validation(shape):
    from netzoo_agent_core.graph.semantic_shape import nest_unresolved_dimensions
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticReview
    hypothesis = reviewed_hypothesis("regulatory_network", "sample_specific", ["tf", "gene"]).model_dump()
    hypothesis["outcome"].pop("unresolved_dimensions")
    hypothesis["unresolved_dimensions"] = ["input_artifacts"]
    payload = {"request_mode": "guidance", "semantic_goal": "Patient wiring",
               shape: [hypothesis] if shape.endswith("hypotheses") else hypothesis}
    before = deepcopy(payload)
    normalized, notes = nest_unresolved_dimensions(payload)
    schema = SemanticInterpretation if shape.endswith("hypotheses") else SemanticReview
    decoded = schema.model_validate(normalized)
    restored = decoded.outcome_hypotheses[0] if shape.endswith("hypotheses") else decoded.outcome_hypothesis
    assert restored.outcome.unresolved_dimensions == ["input_artifacts"]
    assert restored.outcome.artifact_type == "regulatory_network"
    assert restored.outcome.granularity == "sample_specific"
    assert notes and payload == before


def test_misnested_metadata_never_discards_conflicts_or_invalid_scientific_values():
    from pydantic import ValidationError
    from netzoo_agent_core.graph.semantic_shape import nest_unresolved_dimensions
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
    draft = empty_reading()
    item = draft["outcome_hypotheses"][0]
    item["unresolved_dimensions"] = ["granularity"]
    item["outcome"]["unresolved_dimensions"] = ["artifact_type"]
    normalized, notes = nest_unresolved_dimensions(draft)
    assert not notes and normalized == draft
    with pytest.raises(ValidationError):
        SemanticInterpretation.model_validate(normalized)
    item["outcome"].pop("unresolved_dimensions")
    item["outcome"]["artifact_type"] = "invented_biology"
    normalized, _ = nest_unresolved_dimensions(draft)
    with pytest.raises(ValidationError):
        SemanticInterpretation.model_validate(normalized)

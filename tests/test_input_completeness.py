"""E1 production-boundary regressions; scripted replies are not model accuracy."""
from copy import deepcopy

import pytest

from test_routing_evaluation import FixtureProvider, hypothesis, run
from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios


ORIGINALS = [case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id.startswith("original-")]


def cluster_item():
    item = hypothesis()
    for evidence in item["evidence"]:
        evidence.update(source="inferred", text_span=None)
    return item


def provider_for(item, repaired=None):
    return FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Subtype patients", "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "Subtype patients",
                "outcome_hypothesis": deepcopy(item if repaired is None else repaired)},
    )


def omit_inputs(item):
    item["outcome"]["input_artifacts"] = []
    item["evidence"] = [e for e in item["evidence"] if e["dimension"] != "input_artifact"]
    return item


@pytest.mark.parametrize("case", ORIGINALS, ids=lambda c: c.id)
def test_repeated_omission_of_explicit_current_input_cannot_pass(case):
    provider = provider_for(omit_inputs(cluster_item()))
    row = run(provider, case)["results"][0]
    assert row["status"] == "fallback"
    assert not row["review_repair_validated"]
    assert row["outcome"] == {}
    assert row["interaction_passed"]
    assert not row["next_step"]["allow_workflow_continuation"]
    assert "missing_current_input:mutation_matrix" in provider.calls[1][1][-1].content


@pytest.mark.parametrize("case", ORIGINALS, ids=lambda c: c.id)
def test_reviewer_repairs_current_input_and_preserves_complete_guidance(case):
    provider = provider_for(omit_inputs(cluster_item()), cluster_item())
    row = run(provider, case)["results"][0]
    assert row["review_repair_validated"] and row["review_repair_correct"]
    assert row["passed"] and row["interaction_passed"]
    assert row["outcome"]["input_artifacts"] == ["mutation_matrix"]
    assert row["outcome"]["artifact_type"] == "sample_cluster_assignment"
    message = provider.calls[1][1][-1].content
    assert '"action": "restore_current_input"' in message
    assert '"request_facts"' in message and '"text_span"' in message
    if case.id == "original-q1":
        assert "`sample_distance_matrix`: Pairwise sample distances" in row["answer"]
    if case.id == "original-q3":
        rejections = {item["action"]: item for item in row["rejected_methods"]}
        for action in ("run_panda", "run_lioness_panda"):
            assert rejections[action]["input_artifacts"] == ["mutation_matrix"]
            assert rejections[action]["reason_code"] == "incompatible_input"
        assert "Do not use **PANDA**" in row["answer"]
        assert "Do not use **LIONESS-PANDA**" in row["answer"]
        assert '"historical"' in message and "RNA-Seq" in message


def validation(task, item):
    from netzoo_agent_core.contracts import OutcomeHypothesis
    from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
    return validate_outcome_hypotheses(task, [OutcomeHypothesis.model_validate(item)])


@pytest.mark.parametrize("task", [
    "Previously I used a somatic mutation matrix. Now I have an expression matrix.",
    "我過去用突變矩陣分析，現在我有表現量矩陣。",
    "Previously, I used a somatic mutation matrix, and that analysis is finished. Now I have an expression matrix.",
])
def test_historical_mutations_cannot_be_saved_as_current_even_with_inferred_evidence(task):
    item = cluster_item()
    result = validation(task, item)
    assert not result.valid
    assert "hypothesis[0].noncurrent_input:mutation_matrix" in result.issues
    item["outcome"]["input_artifacts"] = ["expression_matrix"]
    next(e for e in item["evidence"] if e["dimension"] == "input_artifact")["value"] = "expression_matrix"
    assert validation(task, item).valid


@pytest.mark.parametrize("task", [
    "Which tool clusters patients? Could PANDA or LIONESS help?",
    "Previously I used RNA-Seq. Which tool clusters patients?",
    "If I obtain a somatic mutation matrix, could I cluster patients?",
    "假如我拿到突變矩陣，可以做病患分群嗎？",
    "Which workflow produces an expression matrix?",
    "Could I use a mutation matrix to cluster patients?",
    "Can PANDA use a mutation matrix?",
    "我能不能用突變矩陣做病患分群？",
    "I have raw WES FASTQ reads. Which workflow calls variants?",
])
def test_unmentioned_historical_or_hypothetical_inputs_are_not_required(task):
    assert validation(task, omit_inputs(cluster_item())).valid


@pytest.mark.parametrize("task", [
    "My RNA-Seq expression matrix is sparse, not a mutation matrix.",
    "我目前有表現量矩陣，不是突變矩陣。",
])
def test_negated_mutation_input_does_not_override_expression(task):
    item = cluster_item()
    item["outcome"]["input_artifacts"] = ["expression_matrix"]
    next(e for e in item["evidence"] if e["dimension"] == "input_artifact")["value"] = "expression_matrix"
    assert validation(task, item).valid


def with_artifact(item, artifact):
    item["outcome"]["artifact_type"] = artifact
    if artifact == "multi_omic_network":
        item["outcome"]["entity_types"] = ["gene"]
    for e in item["evidence"]:
        if e["dimension"] == "artifact_type":
            e["value"] = artifact
        elif e["dimension"] == "entity_type":
            e["value"] = item["outcome"]["entity_types"][0]
    return item


@pytest.mark.parametrize("case,artifact", [(ORIGINALS[0], "sample_distance_matrix"),
                                          (ORIGINALS[2], "multi_omic_network")], ids=["q1-distance", "q3-network"])
def test_intermediate_output_cannot_replace_explicit_patient_clustering_goal(case, artifact):
    bad = with_artifact(cluster_item(), artifact)
    provider = provider_for(bad)
    row = run(provider, case)["results"][0]
    assert row["status"] == "fallback" and row["outcome"] == {}
    assert "terminal_goal_conflict:sample_cluster_assignment" in provider.calls[1][1][-1].content
    repaired = run(provider_for(bad, cluster_item()), case)["results"][0]
    assert repaired["review_repair_correct"] and repaired["passed"]


@pytest.mark.parametrize("task,artifact", [
    ("I have a somatic mutation matrix. Only compute a distance matrix; do not cluster patients.", "sample_distance_matrix"),
    ("我有突變矩陣，只需要病患距離矩陣，不要做病患分群。", "sample_distance_matrix"),
    ("Previously we clustered patients. Now infer a multi-omic network.", "multi_omic_network"),
    ("Infer a multi-omic network. I do not want patient subtypes.", "multi_omic_network"),
    ("Cluster genes into network modules.", "multi_omic_network"),
    ("Previously, we clustered patients. Now infer a multi-omic network.", "multi_omic_network"),
])
def test_non_clustering_goals_are_not_overwritten(task, artifact):
    assert validation(task, with_artifact(cluster_item(), artifact)).valid


def test_unknown_input_compatibility_is_explicit_in_guidance():
    from netzoo_agent_core.contracts import RequestedOutcome, TaskDecision
    from netzoo_agent_core.interpretation.verified_guidance import guidance_contract, render_verified_guidance
    from netzoo_agent_core.policy import ProjectPolicyLoader
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False,
                            confidence=.9, reason="Scientific output match", capability_match_status="exact",
                            matched_actions=["run_sambar"],
                            requested_outcome=RequestedOutcome.model_validate(omit_inputs(cluster_item())["outcome"]))
    facts = guidance_contract(decision, ProjectPolicyLoader().load(), "Which tool clusters patients?")
    assert facts["input_compatibility"] == "not_assessed"
    assert "Input compatibility has not been assessed" in render_verified_guidance(decision, facts)


def test_current_input_survives_a_question_about_an_unconfirmed_method():
    task = "I have a WES somatic mutation matrix. Could PANDA cluster patients with it?"
    result = validation(task, omit_inputs(cluster_item()))
    assert "hypothesis[0].missing_current_input:mutation_matrix" in result.issues
    assert validation(task, cluster_item()).valid


def test_reverse_history_preserves_expression_network_through_production():
    case = next(c for c in load_scenarios(DEFAULT_SCENARIOS) if c.id == "reverse-history-expression")
    item = {
        "outcome": {"operation": "infer", "input_artifacts": ["expression_matrix"],
                    "artifact_type": "regulatory_network", "entity_types": ["tf", "gene"],
                    "regulator_types": ["tf"], "target_types": ["gene"], "granularity": "sample_specific"},
        "confidence": .95,
        "evidence": [{"dimension": d, "value": v, "source": "inferred",
                      "rationale": "The current expression data support a separate TF-to-gene network per patient."}
                     for d, v in [("operation", "infer"), ("input_artifact", "expression_matrix"),
                                  ("artifact_type", "regulatory_network"), ("regulator_type", "tf"),
                                  ("target_type", "gene"), ("granularity", "sample_specific")]],
    }
    row = run(provider_for(item), case)["results"][0]
    assert row["passed"] and row["interaction_passed"]
    assert row["outcome"]["input_artifacts"] == ["expression_matrix"]
    assert row["matched_actions"] == ["run_lioness_panda"]


@pytest.mark.parametrize("task", [
    "Previously I used SAMBAR with a mutation matrix. Tell me about its capabilities.",
    "If I obtain a mutation matrix, could SAMBAR help?",
])
def test_fallback_does_not_restore_noncurrent_input_from_lexical_mentions(task):
    from netzoo_agent_core.interpretation.provider_fallback import recover_registry_guidance
    from netzoo_agent_core.policy import ProjectPolicyLoader
    decision = recover_registry_guidance(task, ProjectPolicyLoader().load().workflows, ValueError())
    assert decision is not None
    assert decision.guidance_input_artifacts == []
    assert decision.requested_outcome is None
    assert decision.capability_match_status == "fallback" and not decision.should_execute

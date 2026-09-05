"""The model must receive the artifact ontology's meanings, not only its names.

Live traces showed the reviewer answering a correct, code-owned repair request
(`missing_current_input:mutation_matrix`) with a literal outside the enum. The
prompt listed artifact names without definitions, so the mapping from a user's
words to a canonical literal was left to the model's own vocabulary. Everything
asserted here is derived from the registry ontology, never from one workflow.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from workflow_registry import ArtifactType  # noqa: E402
from typing import get_args  # noqa: E402

from netzoo_agent_core.contracts.artifact_semantics import ARTIFACT_SEMANTICS  # noqa: E402
from netzoo_agent_core.contracts.outcomes import RequestedOutcome  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import repair_feedback  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from test_routing_evaluation import FixtureProvider, hypothesis, run  # noqa: E402


@pytest.mark.parametrize("artifact", sorted(ARTIFACT_SEMANTICS), ids=sorted(ARTIFACT_SEMANTICS))
def test_every_artifact_literal_is_defined_in_the_semantic_prompt(artifact):
    prompt = build_semantic_interpreter_prompt()

    assert f"{artifact}: {ARTIFACT_SEMANTICS[artifact].description}" in prompt


def test_the_ontology_section_covers_the_whole_registry_enum():
    """A new registry artifact type joins the prompt without a new branch."""
    assert set(ARTIFACT_SEMANTICS) == set(get_args(ArtifactType))


def test_input_artifacts_field_points_at_the_same_literal_vocabulary():
    description = RequestedOutcome.model_fields["input_artifacts"].description

    assert "artifact_type" in description
    assert "exact" in description.casefold()


def test_missing_input_repair_supplies_the_exact_literal_and_its_meaning():
    feedback = repair_feedback(
        {"outcome_hypotheses": [hypothesis()]},
        ("hypothesis[0].missing_current_input:mutation_matrix",),
    )[0]["expected"]

    assert feedback["input_artifact"] == "mutation_matrix"
    assert feedback["input_artifact_definition"] == ARTIFACT_SEMANTICS["mutation_matrix"].description
    assert feedback["permitted_input_artifacts"] == sorted(get_args(ArtifactType))
    assert "exact" in feedback["instruction"].casefold()


def test_noncurrent_input_repair_uses_the_same_vocabulary_contract():
    feedback = repair_feedback(
        {"outcome_hypotheses": [hypothesis()]},
        ("hypothesis[0].noncurrent_input:expression_matrix",),
    )[0]["expected"]

    assert feedback["input_artifact"] == "expression_matrix"
    assert feedback["input_artifact_definition"] == ARTIFACT_SEMANTICS["expression_matrix"].description
    assert feedback["permitted_input_artifacts"] == sorted(get_args(ArtifactType))


def test_a_reviewer_receives_the_vocabulary_through_production_routing():
    item = hypothesis()
    item["outcome"]["input_artifacts"] = []
    item["evidence"] = [e for e in item["evidence"] if e["dimension"] != "input_artifact"]
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Subtype patients",
               "outcome_hypotheses": [item]},
    )

    run(provider)
    message = provider.calls[1][1][-1].content

    assert '"input_artifact_definition"' in message
    assert '"permitted_input_artifacts"' in message
    assert ARTIFACT_SEMANTICS["mutation_matrix"].description in message


Q1_TASK = (
    "我有一份癌症病患的 DNA 突變資料，想先校正基因長度與病患突變負荷，"
    "再聚合成 pathway 分數，計算病患距離並分群。"
)


def test_input_artifacts_declares_a_list_of_plain_literals():
    """Live reviewers returned an object where one enum string belongs."""
    description = RequestedOutcome.model_fields["input_artifacts"].description

    assert "object" in description.casefold()
    assert "string" in description.casefold()


def test_restoring_an_input_also_states_the_evidence_it_must_carry():
    """A restored input without its evidence still fails; hand over the exact pair."""
    feedback = repair_feedback(
        {"outcome_hypotheses": [hypothesis()]},
        ("hypothesis[0].missing_current_input:mutation_matrix",),
        Q1_TASK,
    )[0]["expected"]

    evidence = feedback["required_evidence"]
    assert evidence["dimension"] == "input_artifact"
    assert evidence["value"] == "mutation_matrix"
    assert evidence["source"] == "explicit"
    assert evidence["text_span"] in Q1_TASK
    assert "rationale" not in evidence


def test_the_evidence_requirement_is_omitted_when_no_span_supports_it():
    feedback = repair_feedback(
        {"outcome_hypotheses": [hypothesis()]},
        ("hypothesis[0].missing_current_input:mutation_matrix",),
        "Which tools can group patients?",
    )[0]["expected"]

    assert "required_evidence" not in feedback


def test_removing_a_noncurrent_input_never_supplies_evidence_to_add():
    feedback = repair_feedback(
        {"outcome_hypotheses": [hypothesis()]},
        ("hypothesis[0].noncurrent_input:mutation_matrix",),
        Q1_TASK,
    )[0]["expected"]

    assert "required_evidence" not in feedback


def test_production_routing_hands_the_reviewer_the_evidence_pair():
    item = hypothesis()
    item["outcome"]["input_artifacts"] = []
    item["evidence"] = [e for e in item["evidence"] if e["dimension"] != "input_artifact"]
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Subtype patients",
               "outcome_hypotheses": [item]},
    )

    run(provider, next(
        case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q1"
    ))
    message = provider.calls[1][1][-1].content

    assert '"required_evidence"' in message
    assert '"dimension": "input_artifact"' in message


def test_a_tool_selection_question_is_defined_as_guidance_not_unknown():
    """Two prompts disagreed about the same classification.

    The intent prompt lists "tool/workflow selection questions" under answer.
    The semantic prompt's guidance bullet did not name them, while a later line
    said such questions "do not authorize execution" -- which is also how
    `unknown` is defined. Live runs returned request_mode=unknown for a prompt
    ending in "which built-in tool can handle ...?", in every trial of the case.
    """
    prompt = build_semantic_interpreter_prompt()

    guidance = prompt.split("- guidance:", 1)[1].split("- execute:", 1)[0].casefold()
    assert "which tool" in guidance or "tool" in guidance
    unknown = prompt.split("- unknown:", 1)[1].split("\n\n", 1)[0].casefold()
    assert "do not use unknown" in unknown


def test_the_outcome_rule_no_longer_reads_as_an_unknown_request_mode():
    prompt = build_semantic_interpreter_prompt()

    sentence = " ".join(prompt.split()).casefold()
    start = sentence.index("questions asking which tools can produce")
    assert "guidance" in sentence[start:start + 260]



def test_the_measured_request_mode_wording_is_not_replaced_by_a_general_rule():
    """Reverted after measurement: the general rule performed worse.

    Round 5 measured 4/9 passes with the enumerated wording below and a perfect
    split (every `guidance` trial passed, every `unknown` trial failed). Round 6
    replaced the enumeration with a general "describes or asks about a scientific
    result" rule and `guidance` fell to 2/9, taking the pass rate with it. n is
    small, so this is not proof the enumeration is better -- but there is no
    evidence for the replacement, and the enumeration is the measured
    configuration. Prompt wording is not to be edited again without a mechanism.
    """
    prompt = build_semantic_interpreter_prompt()
    guidance = prompt.split("- guidance:", 1)[1].split("- execute:", 1)[0].casefold()

    assert "which tool or workflow can" in guidance
    assert "describes or asks about a scientific result" not in guidance
    unknown = prompt.split("- unknown:", 1)[1].split("\n\n", 1)[0].casefold()
    assert "do not use unknown merely because execution was not authorized" in unknown


def test_the_general_rule_still_reserves_execute_for_an_explicit_instruction():
    prompt = build_semantic_interpreter_prompt()
    execute = prompt.split("- execute:", 1)[1].split("- unknown:", 1)[0].casefold()

    assert "explicitly" in execute

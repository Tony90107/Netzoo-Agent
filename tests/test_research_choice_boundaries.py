"""User-visible boundaries between one explanation and a genuine method choice."""

import pytest
from test_hypothesis_bases import _context, POLICY, claims
from workflow_registry import OUTPUT_CAPABILITIES
from netzoo_agent_core.graph.router_invocation import invoke_router
from netzoo_agent_core.interpretation.hypothesis_routes import render_hypothesis_routes
from netzoo_agent_core.interpretation.semantic_goal import (
    classification_progress_detail,
    next_step_progress_detail,
)

CONDOR_TASK = (
    "我們拿到了調控者與受質之間的連線權重矩陣。我們試著用傳統的社群發現演算法來把網路切成數"
    "個『功能小組』。結果慘不忍睹：少數幾個超級調控者把幾千個受質全吸進同一個巨型板塊中，完全"
    "沒有生物學意義。從圖論的結構假設來看，為什麼傳統演算法會在這裡徹底崩潰？我們需要基於什麼"
    "假設的工具？"
)


def duplicated_condor():
    # Reproduce the reported model mistake at the external provider boundary.
    return dict(
        question_mode="multiple_hypotheses",
        hypotheses=[
            dict(
                text_span=quote, profile="community_assignment", granularity="aggregate"
            )
            for quote in (
                "傳統演算法會在這裡徹底崩潰",
                "少數幾個超級調控者把幾千個受質全吸進同一個巨型板塊中",
            )
        ],
    )


def test_same_method_for_symptom_and_question_is_one_explanation():
    result = invoke_router(_context(duplicated_condor()), {}, CONDOR_TASK)
    assert result.decision.capability_match_status == "exact"
    assert result.decision.matched_actions == ["run_condor"]
    assert not result.decision.clarification_question
    assert not result.decision.should_execute
    answer = render_hypothesis_routes(result.decision, POLICY, task=CONDOR_TASK)
    assert answer.count("**CONDOR**") == 1
    assert "Hypothesis 1" not in answer and "Hypothesis 2" not in answer
    assert "Which scientific result or hypothesis" not in answer
    assert "Algorithmic assumptions:" not in answer and "Required inputs:" not in answer
    assert "`network_file`" not in answer and "`community_assignment`" not in answer
    assert "two node types" in answer and "null model" in answer
    assert "degree" in answer and "BRIM" in answer
    progress = classification_progress_detail(
        result.routing_state["semantic_goal"], result.decision, POLICY, CONDOR_TASK
    )
    assert "Comparing" not in progress["outcome"]
    assert not next_step_progress_detail(
        result.decision, result.routing_state["semantic_goal"]
    ).get("question")


def test_clear_single_goal_gets_explanation_even_without_hypothesis_extraction():
    from types import SimpleNamespace
    from test_hypothesis_routes import decision, reading
    from netzoo_agent_core.contracts import HumanMessage, WorkflowPlan
    from netzoo_agent_core.graph.response import respond

    d = decision(
        [
            reading(
                "community_assignment", ["regulatory_network"], granularity="aggregate"
            )
        ],
        matched=["run_condor"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="Explain the structural assumption",
        decision=d.model_dump(),
        status="respond_only",
    )
    result = respond(
        SimpleNamespace(project_policy=POLICY),
        {
            "decision": d.model_dump(),
            "messages": [HumanMessage(content=CONDOR_TASK)],
            "plan": plan.model_dump(),
            "tool_results": [],
        },
    )
    text = result["messages"][0].content
    assert "two node types" in text and "null model" in text
    assert "Selected path:" not in text and "Required workflow inputs:" not in text
    assert "`network_file`" not in text


@pytest.mark.parametrize("action", sorted(OUTPUT_CAPABILITIES))
def test_one_distinct_candidate_is_never_a_forced_choice_for_any_package(action):
    task = 'Compare hypotheses "first explanation" and "second explanation".'
    result = invoke_router(
        _context(
            claims(
                [(action, "first explanation"), (action, "second explanation")]
            ).model_dump()
        ),
        {},
        task,
    )
    assert result.decision.matched_actions == [action]
    assert not result.decision.clarification_question
    text = render_hypothesis_routes(result.decision, POLICY, task=task)
    assert text.count("You would need") == 1
    assert "Hypothesis 1" not in text and "Hypothesis 2" not in text
    assert "Which scientific question" not in text


def test_shared_candidates_are_explained_once_and_real_alternatives_remain():
    task = 'Compare hypotheses "dose-dependent wiring" and "stress-dependent wiring".'
    pairs = [
        (action, quote)
        for action in ["run_panda", "run_otter"]
        for quote in ["dose-dependent wiring", "stress-dependent wiring"]
    ]
    result = invoke_router(_context(claims(pairs).model_dump()), {}, task)
    assert result.decision.capability_match_status == "ambiguous"
    assert result.decision.clarification_question
    text = render_hypothesis_routes(result.decision, POLICY, task=task)
    assert text.count("**PANDA**") == text.count("**OTTER**") == 1
    assert all(quote in text for _, quote in pairs)
    assert "Which scientific question" in text


def test_fallback_explains_science_without_hiding_its_uncertain_fit():
    from test_hypothesis_routes import decision
    from netzoo_agent_core.interpretation.scientific_guidance import (
        render_scientific_guidance,
    )

    d = decision([], status="fallback", matched=["run_condor"])
    text = render_scientific_guidance(d, POLICY, task=CONDOR_TASK)
    assert text and "two node types" in text and "BRIM" in text
    assert "not an exact semantic match" in text
    assert "network_file" not in text and "Which scientific question" not in text


def test_downstream_evidence_tolerates_punctuation_but_not_added_words():
    from netzoo_agent_core.graph.research_framing import ResearchFraming, framed_claims

    task = "以調控連線進行腫瘤分型，以預測化療抗藥性。"
    frame = ResearchFraming(
        question_mode="multiple_hypotheses",
        hypotheses=[
            dict(
                text_span="調控連線",
                profile="regulatory_network",
                granularity="aggregate",
                target_artifact="sample_cluster_assignment",
                target_span="腫瘤分型以預測化療抗藥性",
                regulators=["tf"],
            )
        ],
    )
    claims = framed_claims(frame, task).claims
    assert {c.basis for c in claims} == {"run_lioness_panda"}
    assert {c.target_artifact for c in claims} == {"sample_cluster_assignment"}
    frame.hypotheses[0].target_span = "腫瘤分型以準確預測化療抗藥性"
    assert {c.target_artifact for c in framed_claims(frame, task).claims} == {
        "regulatory_network"
    }


def test_technical_details_remain_opt_in_and_inspection_is_not_denied():
    from test_hypothesis_routes import decision
    from netzoo_agent_core.interpretation.scientific_guidance import (
        render_scientific_guidance,
    )

    d = decision([], matched=["run_condor"])
    assert (
        render_scientific_guidance(
            d, POLICY, task="Explain CONDOR parameters and API fields."
        )
        is None
    )
    d = d.model_copy(
        update={"inspected_directories": ["/a/previously-inspected-folder"]}
    )
    text = render_scientific_guidance(d, POLICY, task=CONDOR_TASK)
    assert "No files were inspected" not in text
    assert "previously-inspected-folder" in text


def test_legacy_readings_of_two_outputs_from_one_method_do_not_repeat_the_method():
    from test_hypothesis_routes import decision, reading
    task = 'Compare TF activity with signed regulatory effects; explain the assumptions.'
    d = decision([
        reading('tf_activity_matrix', ['expression_matrix'], granularity='aggregate', quote='TF activity', entities=['tf', 'sample']),
        reading('signed_regulatory_effect_network', ['expression_matrix'], ['tf'], granularity='aggregate', quote='signed regulatory effects'),
    ], matched=['run_giraffe'])
    text = render_hypothesis_routes(d, POLICY, task=task)
    assert text.count('**GIRAFFE**') == 1
    assert 'Which reading should we start with' not in text
    assert 'Required inputs:' not in text
    assert 'TF activities' in text and 'Signed effects' in text

"""Reply cards: the brief, choosable form of a reply, derived from its decision.

A card may only restate what the reply's own decision contains. These tests
pin the three promises that make that safe to show first: every workflow an
option names is one the reply text names, only a recommendation grounded in
the request is marked recommended, and the reply text itself is unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_AXES  # noqa: E402

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import AIMessage, HumanMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.state import NextTurnPrompt  # noqa: E402
from netzoo_agent_core.graph import response as response_module  # noqa: E402
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402
from netzoo_agent_core.reply_cards.choices import (  # noqa: E402
    capability_gap_parts,
    clarification_choices,
    method_choices,
    reading_parts,
)
from netzoo_agent_core.reply_cards.method_notes import (  # noqa: E402
    condition_phrase,
    fit_notes,
    gives,
    highlight,
)
from netzoo_agent_core.routing.clarification_planner import plan_clarification  # noqa: E402

ROOT = Path(__file__).parents[1]
POLICY = ProjectPolicyLoader(ROOT).load()


def evidence(dimension, value, span=None):
    return {"dimension": dimension, "value": value, "source": "explicit" if span else "inferred",
            "text_span": span, "rationale": "Scripted."}


def reading(artifact, inputs=(), regulators=(), granularity="aggregate", quote=None, entities=None):
    return {
        "outcome": {"operation": "infer", "input_artifacts": list(inputs), "artifact_type": artifact,
                    "entity_types": entities or [*regulators, "gene"], "regulator_types": list(regulators),
                    "target_types": ["gene"] if regulators else [], "granularity": granularity},
        "confidence": 0.8, "evidence": [evidence("artifact_type", artifact, quote)] if quote else [],
    }


def decision(hypotheses=(), **fields):
    base = {"action": "no_tool", "in_scope": True, "should_execute": False, "confidence": 0.9,
            "reason": "Scripted.", "outcome_hypotheses": list(hypotheses)}
    base.update(fields)
    return TaskDecision.model_validate(base)


def respond_and_card(task: str, made: TaskDecision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=made.model_dump(), status="respond_only")
    state = {"decision": made.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    out = response_module.respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]],
              "reply_kind": out["reply_kind"]}
    card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)
    return out["messages"][-1].content, out["reply_kind"], card


def named(card) -> list[str]:
    return [POLICY.workflows[option.action].workflow
            for option in card.choices.options if option.action]


# -- registry-backed wording --------------------------------------------------

def test_every_run_workflow_has_a_short_highlight():
    for action in OUTPUT_CAPABILITIES:
        text = highlight(action)
        assert text, action
        assert len(text) <= 100, (action, len(text))


def test_every_run_workflow_says_what_it_gives_in_the_users_terms():
    for action in OUTPUT_CAPABILITIES:
        text = gives(action)
        assert text, action
        assert len(text) <= 100, (action, len(text))
        # The mechanism belongs to the method line and the full reply.
        assert not any(word in text for word in ("message passing", "leave-one-out", "Bayesian")), action


def test_every_registered_condition_has_a_short_phrase():
    declared = {condition for cap in OUTPUT_CAPABILITIES.values() for condition in cap.prefer_when}
    offered = {f"{axis}:{value}" for axis, spec in SELECTION_AXES.items() for value in spec["values"]}
    for condition in declared | offered:
        assert condition_phrase(condition), condition
        assert len(condition_phrase(condition)) <= 70, condition


def test_fit_notes_read_typed_dimensions_only():
    outcome = TaskDecision.model_validate({
        "action": "no_tool", "in_scope": True, "should_execute": False, "confidence": 0.9, "reason": "x",
        "outcome_hypotheses": [reading("regulatory_network", regulators=["tf", "mirna"], granularity="sample_specific")],
    }).outcome_hypotheses[0].outcome
    assert fit_notes("run_lioness_puma", outcome) == (["models the TF + miRNA regulators you asked for"], [])
    matches, mismatches = fit_notes("run_panda", outcome)
    assert matches == []
    assert "models TF only, not miRNA" in mismatches
    assert "its network covers the whole cohort, not one per sample" in mismatches


# -- method ties --------------------------------------------------------------

TIE = ["run_panda", "run_otter", "run_giraffe"]


def test_a_tie_without_stated_facts_marks_nothing_recommended():
    made = decision([reading("regulatory_network", ["expression_matrix"], ["tf"])],
                    capability_match_status="ambiguous", hypothesis_actions=TIE)
    choices = method_choices(made, POLICY, task="I want one TF-gene network for the cohort.")
    assert [option.action for option in choices.options] == TIE
    assert not any(option.recommended or option.badge for option in choices.options)
    assert all(option.resolution == "confirm_workflow" for option in choices.options)
    assert all(len(option.description) <= 200 for option in choices.options)
    assert choices.options[1].answer == "Use OTTER"
    assert "Pick it if memory or runtime is a concern" in choices.options[1].description


def test_a_grounded_recommendation_comes_first_and_says_why_in_registry_words():
    task = "I only have expression data from a handful of patients and want each patient's co-expression."
    made = decision(
        [reading("coexpression_network", ["expression_matrix"], granularity="sample_specific", entities=["gene"])],
        capability_match_status="ambiguous",
        hypothesis_actions=["run_lioness_coexpression", "run_bonobo"],
        advisory_recommendation={"action": "run_bonobo", "conditions": [
            {"axis": "cohort_size", "value": "few", "text_span": "a handful of patients"}]},
    )
    choices = method_choices(made, POLICY, task=task)
    first = choices.options[0]
    assert first.action == "run_bonobo" and first.recommended and first.badge == "Recommended"
    assert first.description.startswith("Fits what you said: you have only a handful of samples")
    assert not choices.options[1].recommended
    assert choices.ordering.startswith("Recommended first")


def test_the_one_workflow_matching_every_typed_dimension_is_the_best_match():
    made = decision(
        [reading("regulatory_network", ["expression_matrix"], ["tf", "mirna"])],
        capability_match_status="ambiguous",
        hypothesis_actions=["run_panda", "run_puma", "run_otter"],
    )
    choices = method_choices(made, POLICY, task="One cohort network of TF and miRNA regulation of genes.")
    assert choices.options[0].action == "run_puma"
    assert choices.options[0].badge == "Best match"
    assert not choices.options[0].recommended
    assert "Models TF only, not miRNA" in choices.options[1].description


def test_an_input_only_one_option_needs_is_named_and_orders_it_later():
    task = "We have expression data, a motif prior and PPI evidence; build a cohort TF-gene network."
    made = decision([reading("regulatory_network", ["expression_matrix"])],
                    capability_match_status="ambiguous", hypothesis_actions=["run_puma", "run_panda"])
    choices = method_choices(made, POLICY, task=task)
    assert [option.action for option in choices.options] == ["run_panda", "run_puma"]
    assert "Also needs miRNA list" in choices.options[1].description
    assert "Also needs" not in choices.options[0].description


# -- clarification ------------------------------------------------------------

def test_a_regulator_question_becomes_its_answers_with_the_workflows_they_lead_to():
    made = decision([reading("regulatory_network", ["expression_matrix"])],
                    capability_match_status="ambiguous",
                    hypothesis_actions=["run_panda", "run_puma", "run_otter", "run_giraffe"])
    plan = plan_clarification(made.hypothesis_actions, outcomes=[h.outcome for h in made.outcome_hypotheses])
    made = made.model_copy(update={"clarification_question": plan.question})
    choices = clarification_choices(made, POLICY)
    labels = {option.label: option for option in choices.options}
    assert set(labels) == {"Transcription factors only", "Both TFs and miRNAs"}
    assert labels["Both TFs and miRNAs"].resolution == "confirm_workflow"
    assert labels["Both TFs and miRNAs"].action == "run_puma"
    assert labels["Transcription factors only"].resolution == "follow_up"
    assert labels["Transcription factors only"].answer == "Transcription factors only"


HEART_FAILURE = ("We have microarray expression profiles from 40 heart failure patients with highly heterogeneous "
                 "clinical presentations. A single population-level network would average away individual "
                 "differences, but each patient contributed only one tissue biopsy, so a per-patient correlation "
                 "cannot be computed. How can we reconstruct a separate regulatory network for each patient from "
                 "this cohort?")
LUNG = ("We just finished RNA-seq on a batch of lung cancer tissues, and we also have standard transcription factor "
        "motif binding data and known protein-protein interaction data. We want to estimate how strongly each "
        "transcription factor regulates its target genes across these tissues, while also accounting for TFs that "
        "cooperate in complexes. What method should we use to build this network?")


def _heart_failure_tie():
    made = decision([reading("regulatory_network", ["expression_matrix"], granularity="sample_specific")],
                    capability_match_status="ambiguous",
                    hypothesis_actions=["run_lioness_panda", "run_lioness_puma"])
    plan = plan_clarification(made.hypothesis_actions, outcomes=[h.outcome for h in made.outcome_hypotheses])
    return made.model_copy(update={"clarification_question": plan.question})


def test_an_answer_needing_an_unmentioned_input_is_not_the_default():
    # Test 2, 2026-10-02: expression data only, yet "Both TFs and miRNAs" came
    # first, so Enter chose LIONESS-PUMA and its miRNA list.
    made = _heart_failure_tie()
    choices = clarification_choices(made, POLICY, task=HEART_FAILURE)
    assert [option.label for option in choices.options] == ["Transcription factors only", "Both TFs and miRNAs"]
    assert "Also needs miRNA list" in choices.options[1].description
    assert "Also needs" not in choices.options[0].description


def test_when_no_option_runs_on_the_named_data_the_card_asks_for_the_inputs_first():
    # Log 312: Test 2 names only expression data; LIONESS-PANDA and LIONESS-PUMA
    # need priors it never mentions, while LIONESS-COEXPRESSION and BONOBO build
    # a per-sample network from expression alone.
    text, kind, card = respond_and_card(HEART_FAILURE, _heart_failure_tie())
    assert card.kind == "clarification" and card.choices.header == "Inputs"
    assert card.choices.question == "Do you also have a motif prior and a PPI network?"
    assert [option.label for option in card.choices.options] == [
        "Only expression data", "I also have a motif prior and a PPI network"]
    first, second = card.choices.options
    assert first.description.startswith("Leads to LIONESS-COEXPRESSION or BONOBO")
    assert first.resolution == second.resolution == "follow_up"
    assert second.description == "Leads to LIONESS-PANDA"
    assert not any(point.startswith(("Every option also needs", "Not mentioned")) for point in card.points)
    assert ("Your request names only expression data; the matched workflows need more inputs, "
            "while LIONESS-COEXPRESSION or BONOBO works from it alone.") in card.points
    assert ("**What your data allows.** Your request names only expression data. LIONESS-PANDA also needs "
            "a motif prior and a PPI network; LIONESS-PUMA also needs a motif prior, a PPI network and a miRNA "
            "list. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds one gene-gene co-expression "
            "network per sample (genes only, no regulator roles) instead. Do you also have a motif prior and a "
            "PPI network?") in text
    assert text.index("**What your data allows.**") < text.index("No files were inspected")


def test_a_result_no_network_alternative_gives_keeps_the_unmentioned_input_note():
    # A TF-activity result: a co-expression network would not be what was asked for.
    task = "We have expression data from 50 tumours and want each TF's activity in every tumour. Which tool? Advice only."
    made = decision([reading("tf_activity_matrix", ["expression_matrix"], ["tf"], granularity="sample_specific")],
                    capability_match_status="exact", matched_actions=["run_giraffe"], recommended_actions=["run_giraffe"])
    text, kind, card = respond_and_card(task, made)
    assert "Not mentioned in your request: motif prior and PPI network." in card.points
    assert card.choices is None and "What your data allows" not in text


def test_an_option_that_runs_on_the_named_data_adds_nothing():
    # Blind case 3: expression from a handful of patients; BONOBO is already offered.
    made = decision([reading("coexpression_network", ["expression_matrix"], granularity="sample_specific")],
                    capability_match_status="ambiguous", hypothesis_actions=["run_lioness_coexpression", "run_bonobo"])
    plan = plan_clarification(made.hypothesis_actions, outcomes=[h.outcome for h in made.outcome_hypotheses])
    made = made.model_copy(update={"clarification_question": plan.question if plan else None})
    text, kind, card = respond_and_card("I only have expression data from 12 patients; I want one co-expression "
                                        "network per patient. Which tool? Advice only.", made)
    assert "What your data allows" not in text and (card.choices is None or card.choices.header != "Inputs")


def test_a_per_sample_extension_is_not_named_as_two_runs():
    task = "Explain LIONESS-PUMA for one TF + miRNA network per patient. Advice only."
    made = decision([reading("regulatory_network", ["expression_matrix"], ["tf", "mirna"], granularity="sample_specific")],
                    capability_match_status="exact", matched_actions=["run_lioness_puma"],
                    recommended_actions=["run_lioness_puma"])
    text, kind, card = respond_and_card(task, made)
    assert "→" not in card.headline and card.headline.startswith("LIONESS-PUMA fits your goal")
    assert "It also writes the cohort network, so PUMA need not run first." in card.points


def test_an_input_described_in_the_users_own_words_is_not_called_unmentioned():
    # Test 1's motif prior ("motif binding data") and expression ("RNA-seq")
    # escape the routing witnesses; the note must stay silent about them.
    made = decision([reading("regulatory_network", ["expression_matrix"], ["tf"], granularity="sample_specific")],
                    capability_match_status="exact", matched_actions=["run_lioness_panda"],
                    recommended_actions=["run_lioness_panda"])
    text, kind, card = respond_and_card(LUNG, made)
    assert not any("Not mentioned" in point for point in card.points)
    # Test 2 names expression only: Log 312's question replaces the bare note.
    other_text, _, other = respond_and_card(HEART_FAILURE, made)
    assert other.choices.header == "Inputs" and "What your data allows" in other_text
    assert not any(point.startswith("Not mentioned") for point in other.points)


def _lung_tie():
    return decision([reading("regulatory_network", [], ["tf"], granularity="unknown")],
                    capability_match_status="ambiguous",
                    hypothesis_actions=["run_panda", "run_lioness_panda", "run_otter", "run_giraffe"])


def test_an_input_named_in_past_tense_or_own_words_is_not_also_needed():
    # Log 310: "We just finished RNA-seq" is a past input to the witnesses and
    # "motif binding data" is not a prior to them, so all four options said
    # "Also needs expression matrix".
    choices = method_choices(_lung_tie(), POLICY, task=LUNG)
    assert not any("Also needs" in option.description for option in choices.options)


def test_an_input_every_option_accepts_in_some_form_separates_nothing():
    # OTTER takes expression or a co-expression matrix; the others need
    # expression. None of them is singled out for it.
    task = "Which tool infers a TF-gene network from our motif and PPI priors? Advice only."
    choices = method_choices(_lung_tie(), POLICY, task=task)
    assert not any("Also needs" in option.description for option in choices.options)


def test_a_question_the_planner_did_not_write_is_not_turned_into_options():
    made = decision([reading("regulatory_network", ["expression_matrix"])],
                    capability_match_status="ambiguous", hypothesis_actions=["run_panda", "run_puma"],
                    clarification_question="Which scientific result do you want NetZoo to produce?")
    assert clarification_choices(made, POLICY) is None


# -- readings, gaps -----------------------------------------------------------

READINGS_TASK = (
    "We have expression data from drug-resistant and sensitive cell lines. One hypothesis is "
    "that transcription factors rewire their target genes; the other is that microRNAs "
    "silence the genes. For each hypothesis, what workflow should we build?"
)


def test_readings_are_options_named_by_the_users_own_quote():
    tf = reading("regulatory_network", ["expression_matrix"], ["tf"], "sample_specific",
                 quote="transcription factors rewire their target genes")
    mirna = reading("regulatory_network", [], ["mirna"], "sample_specific", quote="microRNAs silence the genes")
    made = decision([tf, mirna], capability_match_status="exact", matched_actions=["run_lioness_puma"])
    choices, unavailable = reading_parts(made, POLICY, task=READINGS_TASK)
    assert [option.label for option in choices.options] == [
        "Reading 1: “transcription factors rewire their target genes”",
        "Reading 2: “microRNAs silence the genes”",
    ]
    assert choices.options[1].action == "run_lioness_puma"
    assert choices.options[1].granularity == "sample_specific"
    assert unavailable == []


def test_a_download_gap_says_what_can_be_downloaded():
    made = decision([{**reading("regulatory_network", regulators=["tf"]),
                      "outcome": {**reading("regulatory_network", regulators=["tf"])["outcome"], "operation": "acquire"}}],
                    capability_match_status="unsupported")
    headline, alternatives, unavailable = capability_gap_parts(made, POLICY)
    assert headline.startswith("This agent cannot download")
    assert alternatives == []
    assert "STRING" in unavailable[0].reason and not unavailable[0].available


# -- whole cards through respond() ---------------------------------------------

def test_a_tie_reply_keeps_its_text_and_every_option_is_named_in_it():
    task = "I want one TF-gene regulatory network for the whole cohort. Which method? Advice only."
    made = decision([reading("regulatory_network", ["expression_matrix"], ["tf"])],
                    capability_match_status="ambiguous", hypothesis_actions=TIE,
                    clarification_question="Which modeling assumption best matches your experiment?")
    text, kind, card = respond_and_card(task, made)
    assert kind == "outcome_clarification"
    assert card.kind == "method_choice"
    assert all(name in text for name in named(card))
    assert card.headline.startswith("3 registered methods can build a cohort-level TF-gene regulatory network")
    assert card.next_steps[-1].answer == "new"


def test_a_single_workflow_reply_offers_to_plan_it():
    task = "I need one miRNA-to-gene regulatory network for the whole cohort. Which method? Advice only."
    made = decision([reading("regulatory_network", ["expression_matrix"], ["mirna"])],
                    capability_match_status="exact", matched_actions=["run_puma"],
                    recommended_actions=["run_puma"])
    text, kind, card = respond_and_card(task, made)
    assert card.kind == "workflow_guidance"
    assert card.headline == "PUMA fits your goal: cohort-level miRNA-gene regulatory network."
    assert any(point.startswith("Needs: expression matrix, motif prior, PPI network, miRNA list") for point in card.points)
    plan_step = next(step for step in card.next_steps if step.resolution == "plan_workflow")
    assert plan_step.action == "run_puma" and plan_step.answer == "Start planning PUMA"


def test_no_card_without_a_real_policy_or_while_a_wizard_is_asking():
    made = decision(capability_match_status="ambiguous", hypothesis_actions=TIE)
    plan = WorkflowPlan(workflow="NO-TOOL", objective="x", decision=made.model_dump(), status="respond_only")
    result = {"plan": plan.model_dump(), "messages": [AIMessage(content="x")], "tool_results": [],
              "reply_kind": "outcome_clarification"}
    prompt = NextTurnPrompt(kind="completed", question="Next?")
    assert build_reply_card(result, prompt, Mock(), task="x") is None
    pending = plan.model_copy(update={"status": "needs_input"})
    assert build_reply_card({**result, "plan": pending.model_dump()}, prompt, POLICY, task="x") is None


def test_a_dry_run_card_offers_execution_behind_the_existing_confirmation():
    made = decision(action="run_panda", should_execute=True, matched_actions=["run_panda"])
    plan = WorkflowPlan(workflow="PANDA", objective="run", decision=made.model_dump(), status="ready")
    result = {"plan": plan.model_dump(), "messages": [AIMessage(content="ready")], "reply_kind": "execution",
              "tool_results": [{"action": "run_panda", "status": "dry_run", "summary": "preview"}],
              "evaluation": {"status": "completed"}}
    prompt = NextTurnPrompt(kind="dry_run", question="Your PANDA plan is ready.")
    card = build_reply_card(result, prompt, POLICY, task="run PANDA")
    assert card.kind == "plan_ready"
    assert card.headline == "Your PANDA plan passed validation. Nothing has run yet."
    assert [step.answer for step in card.next_steps] == ["/execute", "new"]


def test_a_completed_run_offers_its_outputs():
    made = decision(action="run_panda", should_execute=True, matched_actions=["run_panda"])
    plan = WorkflowPlan(workflow="PANDA", objective="run", decision=made.model_dump(), status="ready")
    result = {"plan": plan.model_dump(), "messages": [AIMessage(content="done")], "reply_kind": "execution",
              "tool_results": [{"action": "run_panda", "status": "success", "summary": "ok",
                                "artifacts": ["/work/outputs/sessions/abc/panda.tsv"]}],
              "evaluation": {"status": "completed"}}
    prompt = NextTurnPrompt(kind="completed", question="Done.")
    card = build_reply_card(result, prompt, POLICY, task="run PANDA")
    assert card.kind == "run_completed" and not card.ran_nothing
    outputs = card.next_steps[0]
    assert outputs.resolution == "open_outputs" and outputs.paths == ["outputs/sessions/abc/panda.tsv"]


def test_a_tie_narrowed_by_one_word_says_so_and_offers_the_comparison():
    task = ("We have expression, motif and PPI data. The PI prefers iterative updates that simulate TF "
            "cooperativity, while our biostatistician insists on guaranteed convergence. Which method?")
    hypothesis = reading("regulatory_network", ["expression_matrix"], granularity="aggregate")
    hypothesis["outcome"]["selection_tags"] = ["relaxed_graph_matching"]
    hypothesis["evidence"].append(evidence("selection_tag", "relaxed_graph_matching", "convergence"))
    made = decision([hypothesis], capability_match_status="exact", match_basis="registry_features",
                    matched_actions=["run_otter"], recommended_actions=["run_otter"],
                    hypothesis_actions=["run_otter"])
    _, _, card = respond_and_card(task, made)
    assert card.kind == "workflow_guidance"
    assert "Picked from 3 fitting methods because you wrote “convergence”; PANDA and GIRAFFE also fit." in card.points
    compare = card.next_steps[0]
    assert compare.key == "compare-others" and compare.resolution == "compare_workflows"
    assert compare.compare_actions == ["run_otter", "run_panda", "run_giraffe"]
    assert compare.answer.startswith("Compare OTTER with PANDA and GIRAFFE for this goal.")


def test_a_hypothesis_workflow_that_cannot_take_the_stated_data_names_its_producer():
    from netzoo_agent_core.reply_cards.choices import hypothesis_parts

    task = ("We have transcriptomic expression data. One camp wants the most accurate TF-gene regulatory "
            "network; the other wants to split the network into functional modules. Which tools fit?")
    made = decision(
        [reading("regulatory_network", ["expression_matrix"], ["tf"])],
        stated_hypotheses=[
            {"axis": "research_question", "basis": "run_panda", "text_span": "the most accurate TF-gene regulatory network"},
            {"axis": "research_question", "basis": "run_condor", "text_span": "split the network into functional modules"},
        ],
    )
    choices, _, _ = hypothesis_parts(made, POLICY, task=task)
    condor = next(option for option in choices.options if option.action == "run_condor")
    assert "Needs a regulatory network first: build it with PANDA or OTTER" in condor.description
    panda = next(option for option in choices.options if option.action == "run_panda")
    assert "Needs a" not in panda.description


def test_a_stated_regulator_role_is_not_offered_a_network_without_regulators():
    # Replay 2026-10-02: "a separate TF-to-gene regulatory network for each sample"
    # from an expression matrix; a co-expression network is not that result.
    task = ("Right now I have an expression matrix and want a separate TF-to-gene regulatory network for each "
            "sample. Which workflow? Advice only.")
    made = decision([reading("regulatory_network", ["expression_matrix"], ["tf"], granularity="sample_specific")],
                    capability_match_status="exact", matched_actions=["run_lioness_panda"],
                    recommended_actions=["run_lioness_panda"])
    text, kind, card = respond_and_card(task, made)
    assert "What your data allows" not in text and not (card.choices and card.choices.header == "Inputs")
    assert "Not mentioned in your request: motif prior and PPI network." in card.points


# -- option lines from the user's side (2026-10-02 feedback on Test 1) -------------

def test_lung_options_say_what_each_gives_and_how_it_differs_not_how_it_works():
    choices = method_choices(_lung_tie(), POLICY, task=LUNG)
    lines = {POLICY.workflows[option.action].workflow: option.description for option in choices.options}
    assert lines["PANDA"].startswith("One TF-gene network across all your samples · Pick it if you want the standard")
    assert lines["LIONESS-PANDA"] == ("One TF-gene network per sample, plus the cohort network · Lets you compare "
                                      "samples, or relate them to outcomes such as survival · Slower: it reruns "
                                      "PANDA once per sample")
    assert lines["OTTER"] == ("The same kind of network as PANDA, from a different algorithm · "
                              "Pick it if memory or runtime is a concern")
    assert lines["GIRAFFE"].startswith("One signed TF-gene network (activating or repressing), plus each TF's activity")
    assert not any(word in line for line in lines.values()
                   for word in ("message passing", "leave-one-out", "convergence check"))


def _asking(made):
    return made.model_copy(update={"clarification_question": "Which modeling assumption best matches your experiment?"})


def test_lung_card_says_once_what_separates_and_what_all_options_share():
    text, kind, card = respond_and_card(LUNG, _asking(_lung_tie()))
    assert card.kind == "method_choice"
    assert ("Scale differs too: only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give "
            "one across all samples.") in card.points
    assert "As for TFs that cooperate in complexes, all four model this through the PPI network." in card.points
    assert len(card.points) <= 6


def test_the_cooperation_note_needs_the_request_to_mention_it():
    plain = "We have expression, motif and PPI data and want a TF-gene network. Which method?"
    disease = "Lung cancer is a complex disease; we have expression, motif and PPI data. Which method?"
    for task in (plain, disease):
        _, _, card = respond_and_card(task, _asking(_lung_tie()))
        assert card.kind == "method_choice"
        assert not any("cooperate" in point for point in card.points), task


def test_a_cohort_request_is_not_sold_per_sample_networks():
    # Blind case 6 asks for cohort-level co-expression: LIONESS-COEXPRESSION
    # also offers one per sample, but that is not a reason to pick it here.
    made = decision([reading("coexpression_network", ["expression_matrix"], entities=["gene"])],
                    capability_match_status="ambiguous", hypothesis_actions=["run_lioness_coexpression", "run_cobra"])
    choices = method_choices(made, POLICY, task="Which parts of the co-expression are driven by the batch?")
    assert not any("compare samples" in option.description or "Slower" in option.description
                   for option in choices.options)
    _, _, card = respond_and_card("Which parts of the co-expression are driven by the batch?", _asking(made))
    assert card.kind == "method_choice"
    assert not any(point.startswith("Scale differs") for point in card.points)


def test_when_to_pick_it_outlasts_a_shared_note_and_a_cost_never_shows_alone():
    # Case 4's tie: both LIONESS options split by sample beside GIRAFFE, and
    # LIONESS-PUMA also needs a miRNA list; its line is over budget.
    made = decision([reading("regulatory_network", ["expression_matrix"], ["tf"], granularity="sample_specific")],
                    capability_match_status="ambiguous",
                    hypothesis_actions=["run_lioness_panda", "run_giraffe", "run_lioness_puma"])
    task = "data/blind-neutral/case-4/ has expression, motif and PPI files; each patient's TF wiring. Which tool?"
    choices = method_choices(made, POLICY, task=task)
    puma = next(option for option in choices.options if option.action == "run_lioness_puma")
    assert "Pick it if the regulators include miRNAs" in puma.description
    assert "Also needs miRNA list" in puma.description
    for option in choices.options:
        assert "Slower" not in option.description or "compare samples" in option.description
    giraffe = next(option for option in choices.options if option.action == "run_giraffe")
    assert "Its network covers the whole cohort, not one per sample" in giraffe.description


def test_a_scale_answer_says_what_that_scale_is_for():
    made = decision([reading("regulatory_network", ["expression_matrix"], ["tf", "mirna"], granularity="unknown")],
                    capability_match_status="ambiguous", hypothesis_actions=["run_puma", "run_lioness_puma"])
    plan = plan_clarification(made.hypothesis_actions, outcomes=[h.outcome for h in made.outcome_hypotheses])
    made = made.model_copy(update={"clarification_question": plan.question})
    choices = clarification_choices(made, POLICY)
    per_sample = next(option for option in choices.options if option.action == "run_lioness_puma")
    assert per_sample.description == ("Leads to LIONESS-PUMA · Lets you compare samples, or relate them to outcomes "
                                      "such as survival · Slower: it reruns PUMA once per sample")
    cohort = next(option for option in choices.options if option.action == "run_puma")
    assert cohort.description == "Leads to PUMA"

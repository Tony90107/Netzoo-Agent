"""The lean decider in the graph: classify_lean's decisions, the run verdict, the replies (no model calls)."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from langchain_core.messages import HumanMessage  # noqa: E402

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph.lean_call import LEAN_FLAG, classify_lean, lean_applies  # noqa: E402
from netzoo_agent_core.interpretation.lean_view import lean_view, with_lean_notes  # noqa: E402
from netzoo_agent_core.interpretation.request_requirements import read_request_requirements  # noqa: E402


def form(**fields):
    base = {"steps": [], "decision": "DO", "unsure_quote": "", "question": "", "decline_quote": "", "settings": [],
            "sample_count": None, "sample_count_quote": "", "reply": "ok"}
    return {**base, **fields}


class FakeClient:
    def __init__(self, raw, explain="From the contracts: PANDA builds one network.", wanted=None):
        self.raw, self.explain, self.wanted, self.calls = raw, explain, wanted or [], []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.calls.append(request)
        if isinstance(self.raw, Exception):
            raise self.raw
        reading = (request.get("response_format") or {}).get("json_schema", {}).get("name") == "LeanWanted"
        content = (json.dumps({"items": self.wanted}) if reading else
                   json.dumps(self.raw) if "response_format" in request else self.explain)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
                               usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20, cost=0.0001,
                                                     model_extra={}))


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event_type, node, payload):
        self.events.append((event_type, payload))


def run(task, raw, wanted=None, **state):
    context = SimpleNamespace(recorder=Recorder(), router_model_name="openai/gpt-4o-mini", router_max_tokens=1200,
                              lean_client=FakeClient(raw, wanted=wanted))
    result = classify_lean(context, {"messages": [HumanMessage(content=task)], "run_id": "r", **state}, task)
    return result, context


def reply(content, kind):
    return {"messages": [SimpleNamespace(content=content)], "reply_kind": kind}


def test_a_do_is_one_action_approved_for_this_request():
    task = "Run PANDA on data/expr.tsv with data/motif.tsv and data/ppi.tsv for my 30 samples."
    result, context = run(task, form(steps=["PANDA"], reply="Running PANDA."))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "run_panda" and decision.should_execute and decision.core.kind == "DO"
    assert decision.core.basis == "lean" and decision.core.run_allowed
    sha = read_request_requirements(task).source_sha256
    assert decision.run_verdict.run_failures("run_panda", sha) == []
    assert decision.run_verdict.run_failures("run_panda", "other") != []
    kinds = [kind for kind, _ in context.recorder.events]
    assert kinds[:2] == ["lean.decision", "core.decision"] and "llm.completed" in kinds
    assert result["token_usage"]["calls"][0]["role"] == "lean_decider"


def test_a_preparation_step_carries_the_next_analysis_and_later_steps_are_said():
    task = "Build SPONGE priors for the TFs FOXA1 and GATA3 on hg38, then run PANDA on data/expr.tsv."
    result, _ = run(task, form(steps=["PANDA", "SPONGE"]))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "build_priors" and decision.then_action == "run_panda"
    assert decision.sponge_tf_names == ["FOXA1", "GATA3"] and decision.genome_assembly == "hg38"
    notes = decision.core.evidence["lean"]["notes"]
    assert not any("PANDA comes next" in note for note in notes)  # the plan's "Then" line says it

    result, _ = run("Normalize data/counts.tsv with SNAIL, then build LIONESS networks and run PORCUPINE.",
                    form(steps=["NORMALIZE-EXPRESSION", "LIONESS-PANDA", "PORCUPINE"]))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "normalize_expression" and decision.then_action == "run_lioness_panda"
    assert "This plan runs NORMALIZE-EXPRESSION only. PORCUPINE comes next: ask for it once NORMALIZE-EXPRESSION has " \
        "finished." in decision.core.evidence["lean"]["notes"]


def test_stated_settings_are_applied_or_said_not_applied():
    task = ("Run SCORPION on data/cells.h5 with spearman correlation, then PORCUPINE with 500 permutations on the "
            "networks.")
    raw = form(steps=["SCORPION", "PORCUPINE"], settings=[
        {"setting": "SCORPION.assoc_method", "value": "spearman", "quote": "spearman correlation"},
        {"setting": "PORCUPINE.n_permutations", "value": "500", "quote": "500 permutations"}])
    result, _ = run(task, raw)
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "run_scorpion" and decision.assoc_method == "spearman"
    assert decision.n_permutations is None
    notes = decision.core.evidence["lean"]["notes"]
    assert any("assoc_method = spearman (from your request)" in note for note in notes)
    assert 'Not applied now: "500 permutations" (read as a PORCUPINE setting; PORCUPINE is not part of this run).' \
        in notes

    task = "Build SPONGE priors for the TFs FOXA1 and GATA3 on hg38; the node has internet access."
    result, _ = run(task, form(steps=["SPONGE"], settings=[
        {"setting": "SCORPION.n_pc", "value": "yes", "quote": "the node has internet access"}]))
    assert not any("internet" in note for note in TaskDecision.model_validate(
        result["decision"]).core.evidence["lean"]["notes"])  # a workflow outside the steps: a misreading, left out


def test_a_lean_question_in_another_language_becomes_the_next_prompt():
    from netzoo_agent_core.cli.follow_up import build_next_turn_prompt

    task = "我還不確定原始表現矩陣找不找得回來，想用 PANDA 建網路。"
    result, _ = run(task, form(steps=["PANDA"], decision="ASK", unsure_quote="我還不確定原始表現矩陣找不找得回來",
                               question="原始表現矩陣找得回來嗎？"))
    from netzoo_agent_core.contracts import WorkflowPlan

    plan = WorkflowPlan(workflow="NO-TOOL", objective="Ask the lean question.", decision=result["decision"],
                        status="respond_only")
    prompt = build_next_turn_prompt({"plan": plan.model_dump(), "semantic_goal": {}})
    assert prompt.kind == "clarify_outcome" and prompt.question.startswith("原始表現矩陣找得回來嗎？")


def test_ask_decline_and_explain_select_nothing_and_reply_from_the_call():
    task = "I am not sure whether my samples are paired. Run PANDA on data/expr.tsv."
    result, _ = run(task, form(steps=["PANDA"], decision="ASK", unsure_quote="not sure whether my samples are paired",
                               question="Are the samples paired?", reply="One thing first."))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "no_tool" and not decision.should_execute and decision.core.kind == "ASK"
    assert decision.core.facts[0].question == "Are the samples paired?"
    shown = lean_view(decision.core, reply)
    assert shown["reply_kind"] == "lean_ask" and shown["messages"][0].content.endswith("Are the samples paired?")

    result, _ = run("Run PANDA on my mouse proteomics.", form(decision="DECLINE", decline_quote="mouse proteomics",
                                                              reply="PANDA needs gene expression."))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "no_tool" and decision.core.kind == "DECLINE"
    assert not decision.core.evidence["lean"]["verified"]
    from netzoo_agent_core.interpretation.core_views import core_view

    shown = core_view(None, {"decision": result["decision"], "messages": [HumanMessage(content="x")]}, reply)
    text = shown["messages"][0].content
    assert '"mouse proteomics"' in text and "PANDA needs gene expression" not in text  # never the model's reason
    assert "couldn't match" in text

    task = "Run PANDA on my 4 samples; expression, motif and PPI are in data/."
    result, _ = run(task, form(steps=["PANDA"], sample_count=4, sample_count_quote="my 4 samples"))
    decision = TaskDecision.model_validate(result["decision"])
    if decision.core.kind == "DECLINE":  # PANDA's contract minimum (R2): the code's reason is shown
        assert decision.core.evidence["lean"]["verified"]
        shown = core_view(None, {"decision": result["decision"], "messages": [HumanMessage(content=task)]}, reply)
        assert shown["messages"][0].content.startswith("PANDA needs at least")

    result, _ = run("How does PANDA differ from LIONESS?", form(steps=["PANDA", "LIONESS-PANDA"], decision="EXPLAIN"))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "no_tool" and decision.core.kind == "EXPLAIN"
    shown = lean_view(decision.core, reply)
    assert shown["reply_kind"] == "lean_explain" and shown["messages"][0].content.startswith("From the contracts")


def test_a_follow_up_needs_its_own_doubt_to_ask_again():
    task = ("Previous NetZoo goal: I am not sure whether my samples are paired. Run PANDA on data/expr.tsv.\n"
            "User follow-up: they are not paired")
    result, _ = run(task, form(steps=["PANDA"], decision="ASK", unsure_quote="not sure whether my samples are paired",
                               question="Are the samples paired?"))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.core.kind == "DO" and "R1: no doubt stated by the user, so no question" in (
        decision.core.evidence["lean"]["rules"])


def test_a_failed_call_leaves_the_turn_to_the_old_path():
    result, context = run("Run PANDA.", RuntimeError("provider down"))
    assert result is None and context.recorder.events[0][0] == "lean.failed"


def test_the_flag_and_the_old_path_inputs(monkeypatch):
    monkeypatch.delenv(LEAN_FLAG, raising=False)
    assert not lean_applies({}, "Run PANDA.")
    monkeypatch.setenv(LEAN_FLAG, "on")
    assert lean_applies({}, "Run PANDA.")
    assert not lean_applies({"workflow_continuation": {"action": "run_panda"}}, "/execute")
    assert not lean_applies({"method_comparison": {"x": 1}}, "Compare them.")
    assert not lean_applies({}, "CONFIRMED_OUTCOME_ACTION=run_panda")
    assert not lean_applies({}, "PREVIOUS_ACTION=run_panda. Continue the recommended workflow.")


def test_a_do_reply_gets_its_plan_details():
    task = "Run PANDA on data/expr.tsv with data/motif.tsv and data/ppi.tsv for my 30 samples."
    result, _ = run(task, form(steps=["PANDA"]))
    shown = with_lean_notes(reply("Plan: PANDA.", "execution"), {"decision": result["decision"]}, reply)
    assert shown["reply_kind"] == "execution" and "\n\nPlan details:\n- " in shown["messages"][0].content
    assert lean_view(TaskDecision.model_validate(result["decision"]).core, reply) is None


@pytest.mark.parametrize("kind", ["DO", "ASK", "DECLINE", "EXPLAIN"])
def test_every_lean_reply_kind_is_allowed_for_its_call(kind):
    from netzoo_agent_core.interpretation.core_views import ALLOWED, DECLINE_KIND

    from netzoo_agent_core.interpretation import lean_view as view

    assert view.DECLINE_KIND == DECLINE_KIND
    expected = {"ASK": "lean_ask", "DECLINE": DECLINE_KIND, "EXPLAIN": "lean_explain"}.get(kind)
    assert expected is None or expected in ALLOWED[kind]


def test_an_answered_assembly_question_plans_the_run_with_the_answer():
    task = ("Previous NetZoo goal: Please build human motif and PPI priors for the TFs TP53 and MYC. It is either hg19 "
            "or hg18 and I honestly don't remember which. Internet access is fine.\nUser follow-up: Use hg19.")
    result, _ = run(task, form(steps=["SPONGE"], decision="ASK", unsure_quote="I honestly don't remember which",
                               question="hg19 or hg18?"))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.core.kind == "DO" and decision.action == "build_priors" and decision.genome_assembly == "hg19"
    assert not decision.sponge_blockers
    first, _ = run(task.split("\nUser follow-up:")[0].removeprefix("Previous NetZoo goal: "),
                   form(steps=["SPONGE"], decision="DO"))
    assert TaskDecision.model_validate(first["decision"]).core.kind == "ASK"  # before the answer: R3 asks


def test_cards_say_only_what_is_verified():
    from netzoo_agent_core.interpretation.general_background import wanted
    from netzoo_agent_core.reply_cards.builder import _core_card

    result, _ = run("Run PANDA on my mouse proteomics.", form(decision="DECLINE", decline_quote="mouse proteomics"))
    assert wanted(TaskDecision.model_validate(result["decision"]).core)  # the "couldn't match" headline
    result, _ = run("Build SPONGE priors for the TFs FOXA1 and GATA3 for our mouse liver samples.", form(steps=["SPONGE"]))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.core.kind == "DECLINE" and decision.core.evidence["lean"]["verified"]  # R3: SPONGE is human only
    assert not wanted(decision.core)

    task = "I am not sure whether my samples are paired. Run PANDA on data/expr.tsv."
    result, _ = run(task, form(steps=["PANDA"], decision="ASK", unsure_quote="not sure whether my samples are paired",
                               question="Are the samples paired?", reply="Preamble the model wrote."))
    card = _core_card("lean_ask", TaskDecision.model_validate(result["decision"]), None, task)
    assert card.kind == "clarification" and card.points == ["Are the samples paired?"]


def test_r6_refusal_names_the_users_words_and_no_reason():
    from netzoo_agent_core.interpretation.core_views import core_view
    from netzoo_agent_core.lean import _menu

    task = ("Our LIONESS-PANDA table covers 64 melanoma patients, 29 responders and 35 non-responders, with a Reactome "
            "GMT. Test each pathway for a regulation difference between responders and non-responders.")
    kind = next(key for key, text, _ in _menu("six")
                if text == "Pathways differentially expressed or enriched between predefined groups.")
    wanted = [{"quote": "Test each pathway for a regulation difference between responders and non-responders",
               "role": "result", "kind": kind}]
    result, context = run(task, form(steps=["PORCUPINE"], reply="PORCUPINE tests the groups."), wanted=wanted)
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.action == "no_tool" and decision.core.kind == "DECLINE"
    assert not decision.core.evidence["lean"]["verified"] and decision.core.evidence["lean"]["rules"][-1][:2] == "R6"
    assert len(context.lean_client.calls) == 2  # the form and the blind reading
    blind = next(call for call in context.lean_client.calls
                 if call["response_format"]["json_schema"]["name"] == "LeanWanted")
    assert "PORCUPINE" not in blind["messages"][0]["content"]  # the reader never sees the workflows
    recorded = next(payload for name, payload in context.recorder.events if name == "lean.decision")
    assert recorded["form"]["wanted"] == wanted  # saved, so the rule can be replayed at no cost
    shown = core_view(None, {"decision": result["decision"], "messages": [HumanMessage(content=task)]}, reply)
    text = shown["messages"][0].content
    assert '"Test each pathway for a regulation difference' in text and "couldn't match" in text
    assert "PORCUPINE tests the groups" not in text


def test_r7_refusal_gives_codes_reason(monkeypatch):
    from netzoo_agent_core.interpretation.core_views import core_view

    task = "Normalize my raw counts from 30 adipose biopsies with TMM and write the matrix."
    result, _ = run(task, form(steps=["NORMALIZE-EXPRESSION"]))
    decision = TaskDecision.model_validate(result["decision"])
    assert decision.core.kind == "DECLINE" and decision.core.evidence["lean"]["verified"]
    shown = core_view(None, {"decision": result["decision"], "messages": [HumanMessage(content=task)]}, reply)
    assert "SNAIL only" in shown["messages"][0].content


def test_the_result_check_can_be_turned_off(monkeypatch):
    monkeypatch.setenv("NETZOO_LEAN_RESULT_CHECK", "off")
    result, context = run("Run PANDA on data/expr.tsv with my motif and PPI priors.", form(steps=["PANDA"]))
    assert len(context.lean_client.calls) == 1 and result["decision"]["core"]["kind"] == "DO"

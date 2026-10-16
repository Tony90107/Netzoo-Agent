"""Core decision spec, phase 2: the fact agent's proposals held to R1-R6, and the ASK they make.

Round p0/p1: asking was 3/15 and 2/15, every asked fact one of the 11 fixed dimensions. The agent may propose any
fact the user shows they are unsure of; code keeps it only with the user's words, the contract's words, and two
different outcomes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import pytest  # noqa: E402

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck, FactProposal, FactProposals  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core  # noqa: E402
from netzoo_agent_core.interpretation.fact_check import fact_candidates, kept_facts  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

TASK = ("Run BONOBO on lesions.tsv for my 9 biopsies. The matrix was mean-centered, but I can't tell whether the "
        "values were log-transformed before centering.")
UNSURE = "I can't tell whether the values were log-transformed before centering"
CONTRACT = "The agent requires the caller to declare log_transformed=true and centered=true"


@pytest.fixture(scope="module")
def policy():
    return ProjectPolicyLoader(Path(__file__).parents[1]).load()


def _proposal(**extra):
    fields = dict(user_quote=UNSURE, uncertainty="said_unknown", workflow="BONOBO", contract_quote=CONTRACT,
                  question="Were the values log-transformed before they were centered?", yes_outcome="supported",
                  yes_workflow="", no_outcome="not_supported", no_workflow="")
    return FactProposal(**{**fields, **extra})


def _decision(action="no_tool", stated=(), uncertain=(UNSURE,), **extra):
    check = CapabilityCheck(requirements=[CheckedRequirement(
        quote="Run BONOBO on lesions.tsv for my 9 biopsies", kind="result", status="available",
        delivered_by=["bonobo.per_sample_networks"])], stated_quotes=list(stated), uncertain_quotes=list(uncertain))
    return TaskDecision(action=action, in_scope=True, should_execute=action != "no_tool", confidence=0.9, reason="r",
                        capability_check=check, matched_actions=["run_bonobo"], **extra)


def _kept(policy, *proposals, decision=None):
    return kept_facts(TASK, FactProposals(facts=list(proposals)), decision or _decision(), policy)


def test_a_fact_with_the_users_and_the_contracts_words_and_two_outcomes_is_kept(policy):
    check = _kept(policy, _proposal())
    (fact,) = check.accepted
    assert (fact.user_quote, fact.workflows, fact.if_yes, fact.if_no) == (UNSURE, ["BONOBO"], "supported", "not_supported")
    assert not fact.settled_by_input_check and check.candidates == ["BONOBO"]


def test_words_the_check_did_not_read_as_unsure_are_not_asked(policy):
    """Dev set m3: alone, the agent asked on 10 (nemotron) and 20 (gpt-4o-mini) of 27 supported requests."""
    check = _kept(policy, _proposal(), decision=_decision(uncertain=()))
    assert check.accepted == [] and check.rejected[0].rule.startswith("R1 the check did not read")


@pytest.mark.parametrize("change, rule", [
    ({"user_quote": "I never checked the scaling"}, "R1"),
    ({"workflow": "PANDA"}, "R2 not a candidate"),
    ({"contract_quote": "BONOBO always log-transforms its input"}, "R2 contract words"),
    ({"no_outcome": "supported"}, "R3"),
    ({"no_outcome": "other_workflow", "no_workflow": "NOT-A-WORKFLOW"}, "R3"),
    ({"no_outcome": "other_workflow", "no_workflow": "BONOBO"}, "R3"),  # round p2 C31: "BONOBO instead of BONOBO"
])
def test_a_proposal_that_breaks_a_rule_is_rejected_with_it(policy, change, rule):
    check = _kept(policy, _proposal(**change))
    assert check.accepted == [] and check.rejected[0].rule.startswith(rule)


def test_words_the_reading_typed_as_stated_are_not_asked(policy):
    stated = ["The matrix was mean-centered, but I can't tell whether the values were log-transformed before centering"]
    check = _kept(policy, _proposal(), decision=_decision(stated=stated))
    assert check.accepted == [] and check.rejected[0].rule.startswith("R4")


def test_a_fact_the_input_check_settles_on_a_run_is_said_not_asked(policy):
    proposal = _proposal(contract_quote="at least three total samples")
    run = _kept(policy, proposal, decision=_decision(action="run_bonobo"))
    question = _kept(policy, proposal)
    assert run.accepted[0].settled_by_input_check and not question.accepted[0].settled_by_input_check


def test_at_most_two_questions_in_the_requests_order(policy):
    first = _proposal(user_quote="mean-centered")
    third = _proposal(user_quote="9 biopsies", question="third?")
    check = _kept(policy, _proposal(), third, first,
                  decision=_decision(uncertain=(UNSURE, "mean-centered", "9 biopsies")))
    assert [fact.user_quote for fact in check.accepted] == ["9 biopsies", "mean-centered"]
    assert check.rejected[0].rule.startswith("R6")


def test_candidates_come_from_the_check_then_routing(policy):
    assert fact_candidates(_decision(), policy) == ["run_bonobo"]


def test_an_agent_question_is_ask_and_holds_the_turn(policy):
    decision = _decision(action="run_bonobo")
    decision = decision.model_copy(update={"fact_check": _kept(policy, _proposal(), decision=decision)})
    decision = decision.model_copy(update={"fact_check": decision.fact_check.model_copy(update={
        "accepted": [f.model_copy(update={"settled_by_input_check": False}) for f in decision.fact_check.accepted]})})
    core = decide_core(decision, TASK)
    assert (core.kind, core.basis, core.workflows) == ("ASK", "fact_agent", ["BONOBO"])
    held = with_core(decision, core)
    assert (held.action, held.matched_actions, held.clarification_question) == (
        "no_tool", [], "Were the values log-transformed before they were centered?")


def test_when_the_agent_ran_the_fixed_dimensions_are_shadow(policy):
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits

    waiting = CheckedRequirement(quote="Run CONDOR on net.tsv", kind="result", status="needs_fact",
                                 depends_on="input_network", unknown_quote="I can't recall",
                                 outcomes={"regulator_gene": ["condor.communities"], "gene_gene": []},
                                 delivered_by=["condor.communities"])
    check = CapabilityCheck(requirements=[waiting])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_check=check, fact_check=FactCheck(status="checked"))
    assert (decide_core(decision).kind, decide_core(decision).workflows) == ("DO", ["CONDOR"])  # shadow
    lifted = decision.model_copy(update={"capability_check": without_legacy_waits(check)})
    core = decide_core(lifted)
    assert (core.kind, core.workflows) == ("DO", ["CONDOR"])
    failed = decision.model_copy(update={"fact_check": FactCheck(status="failed")})
    assert (decide_core(failed).kind, decide_core(failed).basis) == ("ASK", "needs_fact")


def test_the_ask_reply_and_card_carry_the_question_outcomes_and_both_quotes(policy):
    from netzoo_agent_core.interpretation.capability_check import whole_check_result
    from netzoo_agent_core.reply_cards.builder import _core_card

    decision = _decision()
    decision = decision.model_copy(update={"fact_check": _kept(policy, _proposal())})
    decision = with_core(decision, decide_core(decision, TASK))
    result = whole_check_result({"decision": decision.model_dump(), "messages": []},
                                lambda text, kind: {"text": text, "reply_kind": kind})
    assert result["reply_kind"] == "ask_facts"
    text = result["text"]
    assert "Were the values log-transformed" in text and UNSURE in text and CONTRACT in text
    assert "If yes" not in text and "If no" not in text  # open item 1: outcomes are not said, only kept for R3
    card = _core_card("ask_facts", decision, None, "")
    assert (card.kind, card.points) == ("clarification", ["Were the values log-transformed before they were centered?"])


def test_a_settled_fact_is_said_after_a_do_reply(policy):
    from netzoo_agent_core.contracts import AIMessage
    from netzoo_agent_core.interpretation.ask_facts import with_settled_notes

    decision = _decision(action="run_bonobo")
    decision = decision.model_copy(update={"fact_check": _kept(
        policy, _proposal(contract_quote="at least three total samples"), decision=decision)})
    decision = with_core(decision, decide_core(decision, TASK))
    assert decision.core.kind == "DO" and decision.core.facts[0].settled_by_input_check
    result = with_settled_notes({"messages": [AIMessage(content="Plan ready.")], "reply_kind": "needs_input"},
                                {"decision": decision.model_dump()},
                                lambda text, kind: {"messages": [AIMessage(content=text)], "reply_kind": kind})
    assert "Checked from your files before anything runs" in result["messages"][-1].content
    assert "at least three total samples" in result["messages"][-1].content


def test_the_contract_quotes_input_checks_must_be_the_contracts_own_words(policy, tmp_path):
    from netzoo_agent_core.policy import ProjectPolicyError, ProjectPolicyLoader as Loader

    source = (Path(__file__).parents[1] / "workflows" / "bonobo.yaml").read_text()
    bad = tmp_path / "bonobo.yaml"
    bad.write_text(source.replace('  - "at least three total samples"', '  - "at least four total samples"'))
    with pytest.raises(ProjectPolicyError, match="input_checks"):
        Loader._load_workflow_spec(bad)


def test_an_asking_turn_on_the_hypothesis_path_names_no_workflow_in_its_progress_line(policy):
    """Round p2 C31: a research-guidance turn that the agent made ASK was headed "Matched workflows -- GIRAFFE"."""
    from netzoo_agent_core.contracts.outcomes import StatedHypothesis
    from netzoo_agent_core.interpretation.semantic_goal import classification_progress_detail

    decision = _decision().model_copy(update={"stated_hypotheses": [StatedHypothesis.model_validate({
        "axis": "unclear_goal", "basis": "run_bonobo", "target_artifact": "coexpression_network",
        "target_granularity": "sample_specific", "text_span": "Run BONOBO"})]})
    decision = decision.model_copy(update={"fact_check": _kept(policy, _proposal())})
    held = with_core(decision, decide_core(decision, TASK))
    assert classification_progress_detail({}, held)["workflows"] == []

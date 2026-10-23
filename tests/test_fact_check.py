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
from netzoo_agent_core.contracts.core_decision import FactQuestion  # noqa: E402
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
                  yes_workflow="", no_outcome="not_supported", no_workflow="", about="user_data", alternatives=[])
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


def test_a_fact_the_input_check_could_settle_is_still_asked_on_a_run(policy):
    # ROUND-21 (user decision): R5 withdrawn -- the user is asked first, the file check never stands in for them.
    proposal = _proposal(contract_quote="at least three total samples")
    run = _kept(policy, proposal, decision=_decision(action="run_bonobo"))
    question = _kept(policy, proposal)
    assert not run.accepted[0].settled_by_input_check and not question.accepted[0].settled_by_input_check
    decision = _decision(action="run_bonobo")
    decision = decision.model_copy(update={"fact_check": run})
    assert (decide_core(decision, TASK).kind, decide_core(decision, TASK).basis) == ("ASK", "fact_agent")
    recorded = run.model_copy(update={"accepted": [f.model_copy(update={"settled_by_input_check": True})
                                                   for f in run.accepted]})  # a decision recorded under R5
    assert decide_core(decision.model_copy(update={"fact_check": recorded}), TASK).kind == "ASK"


def test_at_most_two_questions_in_the_requests_order(policy):
    first = _proposal(user_quote="mean-centered")
    third = _proposal(user_quote="9 biopsies", question="third?")
    check = _kept(policy, _proposal(), third, first,
                  decision=_decision(uncertain=(UNSURE, "mean-centered", "9 biopsies")))
    assert [fact.user_quote for fact in check.accepted] == ["9 biopsies", "mean-centered"]
    # harness repair P1 (A03): the third valid question is queued, still open -- never rejected
    assert [fact.user_quote for fact in check.queued] == [UNSURE] and check.rejected == []
    assert [fact.fact_key for fact in check.accepted] == [
        f"agent:BONOBO@{TASK.index('9 biopsies')}-{TASK.index('9 biopsies') + len('9 biopsies')}",
        f"agent:BONOBO@{TASK.index('mean-centered')}-{TASK.index('mean-centered') + len('mean-centered')}"]


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


def _condor_waiting():
    return CapabilityCheck(requirements=[CheckedRequirement(
        quote="Run CONDOR on net.tsv", kind="result", status="needs_fact", depends_on="input_network",
        unknown_quote="I can't recall", outcomes={"regulator_gene": ["condor.communities"], "gene_gene": []},
        delivered_by=["condor.communities"])])


def test_a_fixed_dimension_wait_on_other_words_is_asked_beside_the_agents_question(policy):
    """Harness repair P1 (P0 fixture F03): until P1 the agent's unrelated question lifted the CONDOR wait and credited
    its row, as if the regulator-gene answer were given; now the wait is asked beside it."""
    agent = _kept(policy, _proposal())
    check = _condor_waiting()
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_check=check, fact_check=agent.model_copy(update={"legacy": [FactQuestion(
                                question="Which network?", user_quote="I can't recall")]}))
    core = decide_core(decision, TASK)
    assert (core.kind, core.basis, core.evidence["legacy_facts"]) == ("ASK", "fact_agent", ["Which network?"])
    assert [fact.question for fact in core.facts] == [
        "Were the values log-transformed before they were centered?",
        "Does your network link regulators (such as TFs) to their target genes, or genes to genes?"]
    assert [(o["source"], o["status"], o["asked_as"]) for o in core.evidence["obligations"]] == [
        ("agent", "asked", ""), ("dimension", "asked", "")]
    assert check.results()[0].status == "needs_fact"  # not credited before the user answers
    opened = decision.model_copy(update={"fact_check": FactCheck(status="checked", open_results=["I can't recall"])})
    core = decide_core(opened, TASK)  # R7 asks the goal first; the wait is queued, not settled
    assert (core.kind, core.basis) == ("CLARIFY", "result_open")
    assert [(o["source"], o["status"]) for o in core.evidence["obligations"]] == [("dimension", "queued")]


def test_when_the_agent_asks_nothing_the_fixed_dimensions_stand():
    """2026-10-22: replayed, the silent agent's lifted waits made C11, C31 and h2 J19 (all gold ASK) DO."""
    check = _condor_waiting()
    silent = FactCheck(status="checked")
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_check=check, fact_check=silent)
    core = decide_core(decision)
    assert (core.kind, core.basis, core.workflows, core.evidence["legacy_kept"]) == (
        "ASK", "needs_fact", ["CONDOR"], True)
    from netzoo_agent_core.interpretation.capability_check import whole_check_result
    from netzoo_agent_core.interpretation.needed_facts import waiting_decision

    waiting = with_core(waiting_decision(decision, check), core)
    assert (waiting.action, waiting.should_execute) == ("no_tool", False)
    result = whole_check_result({"decision": waiting.model_dump(), "messages": []},
                                lambda text, kind: {"text": text, "reply_kind": kind})
    assert result["reply_kind"] == "needs_fact" and "I can't recall" in result["text"]
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


def test_the_contract_quotes_input_checks_must_be_the_contracts_own_words(policy, tmp_path):
    from netzoo_agent_core.policy import ProjectPolicyError, ProjectPolicyLoader as Loader

    source = (Path(__file__).parents[1] / "workflows" / "bonobo.yaml").read_text()
    bad = tmp_path / "bonobo.yaml"
    bad.write_text(source.replace('text: "at least three total samples"', 'text: "at least four total samples"'))
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


def test_the_method_the_goal_words_name_is_a_candidate_first(policy):
    """p4c C48: only a methods question was read and the decision carried no routed action, so the agent never ran."""
    quote = "Is DRAGON able to link fecal metabolomics with colon-biopsy transcriptomics"
    check = CapabilityCheck(requirements=[CheckedRequirement(quote=quote, kind="about_methods", status="not_checked")],
                            goal="method_named", goal_quote=quote)
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_check=check)
    assert fact_candidates(decision, policy) == ["run_dragon"]
    assert fact_candidates(decision.model_copy(update={"hypothesis_actions": ["run_lioness_dragon"]}), policy) == [
        "run_dragon", "run_lioness_dragon"]


# Phase 5c (spec 13.4) R7: a wanted result the user is unsure of is a fact only with two options named.

RESULT_TASK = ("Run BONOBO on lesions.tsv for my 9 biopsies. I'm not sure whether I need one network per biopsy or "
               "one network for all biopsies together.")
RESULT_UNSURE = "I'm not sure whether I need one network per biopsy or one network for all biopsies together"
OPEN_TASK = "Run BONOBO on lesions.tsv for my 9 biopsies. Honestly I don't know what kind of network they expect."
OPEN_UNSURE = "Honestly I don't know what kind of network they expect"


def _result_fact(quote, alternatives):
    return _proposal(user_quote=quote, about="wanted_result", alternatives=list(alternatives),
                     question="Do you need one network per biopsy?")


def test_a_wanted_result_with_two_named_options_is_a_fact_to_ask(policy):
    """Rounds p3/p4b C11, C31, C34, C36: each names both results in its own words, and is asked."""
    proposal = _result_fact(RESULT_UNSURE, ["one network per biopsy", "one network for all biopsies together"])
    check = kept_facts(RESULT_TASK, FactProposals(facts=[proposal]), _decision(uncertain=(RESULT_UNSURE,)), policy)
    assert [fact.user_quote for fact in check.accepted] == [RESULT_UNSURE] and check.open_results == []


@pytest.mark.parametrize("alternatives", [[], ["a network"], ["one network per biopsy", "network per biopsy"]])
def test_a_wanted_result_with_fewer_than_two_named_options_is_a_goal_to_clarify(policy, alternatives):
    """Rounds p4b/p4c C24 ("Honestly I don't know what kind of network they expect") were asked as a fact."""
    task = OPEN_TASK if not alternatives or alternatives == ["a network"] else RESULT_TASK
    quote = OPEN_UNSURE if task == OPEN_TASK else RESULT_UNSURE
    check = kept_facts(task, FactProposals(facts=[_result_fact(quote, alternatives)]), _decision(uncertain=(quote,)),
                       policy)
    assert (check.accepted, check.open_results) == ([], [quote])


def test_an_open_result_still_needs_the_users_unsure_words_and_the_contracts(policy):
    unread = kept_facts(OPEN_TASK, FactProposals(facts=[_result_fact(OPEN_UNSURE, [])]), _decision(uncertain=()), policy)
    assert unread.open_results == [] and unread.rejected[0].rule.startswith("R1")
    invented = _proposal(user_quote=OPEN_UNSURE, about="wanted_result", alternatives=[], contract_quote="any network")
    uncontracted = kept_facts(OPEN_TASK, FactProposals(facts=[invented]), _decision(uncertain=(OPEN_UNSURE,)), policy)
    assert uncontracted.open_results == [] and uncontracted.rejected[0].rule.startswith("R2")


def test_an_open_result_is_clarify_before_any_question_about_the_data(policy):
    data = _proposal()  # the log-transform fact of the phase 2 tests, on its own words
    task = f"{TASK} {OPEN_UNSURE}."
    facts = kept_facts(task, FactProposals(facts=[data, _result_fact(OPEN_UNSURE, [])]),
                       _decision(uncertain=(UNSURE, OPEN_UNSURE)), policy)
    assert len(facts.accepted) == 1 and facts.open_results == [OPEN_UNSURE]
    decision = _decision(uncertain=(UNSURE, OPEN_UNSURE), fact_check=facts)
    core = decide_core(decision, task)
    assert (core.kind, core.basis, core.clarify.goal_quote) == ("CLARIFY", "result_open", OPEN_UNSURE)
    held = with_core(decision, core)
    assert (held.action, held.matched_actions, held.should_execute) == ("no_tool", [], False)

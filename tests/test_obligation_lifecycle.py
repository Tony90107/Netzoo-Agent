"""Harness repair P1 (spec 2026-10-23, sections 5.2 and 7.1): no fact the turn needs leaves it unasked and unqueued.

Until P1 a checked fact agent that kept any question lifted every fixed-dimension wait: its row was credited as if the
favourable answer were given, or made not available when it delivered nothing, and a third valid question was
rejected. P0 fixtures F02-F05 (docs/research-log/harness-repair-2026-10-23).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_fact_check import TASK, UNSURE, _decision, _kept, _proposal, policy  # noqa: E402,F401

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.contracts.core_decision import FactQuestion  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core  # noqa: E402
from netzoo_agent_core.interpretation.obligations import fact_key  # noqa: E402

SAMBAR_TASK = ("Run SAMBAR on brca_variant_matrix.csv for our 80 tumours. I can't tell whether those are somatic calls "
               "or germline variants.")
SAMBAR_UNSURE = "I can't tell whether those are somatic calls or germline variants"


def _turn(task, rows, *accepted, queued=()):
    check = CapabilityCheck(requirements=[CheckedRequirement(kind="result", status="needs_fact", **row) for row in rows])
    agent = FactCheck(status="checked", accepted=list(accepted), queued=list(queued))
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_check=check, fact_check=agent)


def _ledger(core):
    return [(o["source"], o["status"], o["asked_as"]) for o in core.evidence["obligations"]]


def _span_key(source, what, task, quote):
    start = task.index(quote)
    return f"{source}:{what}@{start}-{start + len(quote)}"


def test_fact_keys_place_the_users_words_in_the_request():
    assert fact_key("agent", "SAMBAR", SAMBAR_TASK, SAMBAR_UNSURE) == _span_key("agent", "SAMBAR", SAMBAR_TASK,
                                                                                 SAMBAR_UNSURE)
    assert fact_key("dimension", "scale", SAMBAR_TASK, "Words Not In It") == "dimension:scale@words not in it"


def test_an_agent_question_on_the_same_words_and_workflow_covers_the_wait():
    """F02 (h4 M06): the agent asks the somatic-or-germline fact in its own words; the wait is the same obligation."""
    decision = _turn(SAMBAR_TASK, [dict(
        quote="Run SAMBAR on brca_variant_matrix.csv", depends_on="mutation_origin", unknown_quote=SAMBAR_UNSURE,
        outcomes={"somatic": ["sambar.subtypes"], "germline": []}, delivered_by=["sambar.subtypes"])],
        FactQuestion(question="Are the calls somatic variants?", user_quote="those are somatic calls",
                     workflows=["SAMBAR"], contract_quote="SAMBAR consumes a samples-by-genes somatic mutation CSV"))
    core = decide_core(decision, SAMBAR_TASK)
    assert (core.kind, core.basis) == ("ASK", "fact_agent")
    assert [fact.question for fact in core.facts] == ["Are the calls somatic variants?"]
    agent_key = _span_key("agent", "SAMBAR", SAMBAR_TASK, "those are somatic calls")
    assert _ledger(core) == [("agent", "asked", ""), ("dimension", "asked", agent_key)]


def test_a_wait_that_delivers_nothing_is_asked_never_made_a_refusal():
    """F04: lifted, a wait whose outcomes deliver nothing became not available -- a refusal on no evidence."""
    task = (f"{TASK} Then run CONDOR on net.tsv; I can't recall whether it links TFs to genes or genes to genes.")
    decision = _turn(task, [dict(quote="run CONDOR on net.tsv", depends_on="input_network",
                                 unknown_quote="I can't recall", outcomes={"regulator_gene": [], "gene_gene": []})],
                     FactQuestion(question="Were the values log-transformed?", user_quote=UNSURE, workflows=["BONOBO"]))
    core = decide_core(decision, task)
    assert (core.kind, core.basis, core.declined) == ("ASK", "fact_agent", [])
    assert len(core.facts) == 2 and _ledger(core) == [("agent", "asked", ""), ("dimension", "asked", "")]
    assert decision.capability_check.results()[0].status == "needs_fact"


def test_past_two_questions_every_fact_is_queued_none_dropped():
    first = FactQuestion(question="Were the values log-transformed?", user_quote=UNSURE, workflows=["BONOBO"])
    second = FactQuestion(question="Is it 9 biopsies?", user_quote="9 biopsies", workflows=["BONOBO"])
    third = FactQuestion(question="Was it mean-centered?", user_quote="mean-centered", workflows=["BONOBO"])
    task = f"{TASK} Then run CONDOR on net.tsv; I can't recall what it links."
    decision = _turn(task, [dict(quote="run CONDOR on net.tsv", depends_on="input_network",
                                 unknown_quote="I can't recall", outcomes={"regulator_gene": ["condor.communities"],
                                                                         "gene_gene": []},
                                 delivered_by=["condor.communities"])], first, second, queued=[third])
    core = decide_core(decision, task)
    assert [fact.question for fact in core.facts] == [first.question, second.question]
    assert _ledger(core) == [("agent", "asked", ""), ("agent", "asked", ""), ("agent", "queued", ""),
                             ("dimension", "queued", "")]


def test_the_third_kept_question_reaches_the_turn_as_queued(policy):
    """F05: kept_facts queues it (until P1 it was rejected as R6); decide_core records it as an open obligation."""
    facts = _kept(policy, _proposal(), _proposal(user_quote="9 biopsies", question="third?"),
                  _proposal(user_quote="mean-centered"),
                  decision=_decision(uncertain=(UNSURE, "mean-centered", "9 biopsies")))
    decision = _decision().model_copy(update={"fact_check": facts})
    core = decide_core(decision, TASK)
    assert [o["user_quote"] for o in core.evidence["obligations"] if o["status"] == "queued"] == [UNSURE]
    assert [o["status"] for o in core.evidence["obligations"]] == ["asked", "asked", "queued"]


def test_a_wait_in_the_next_sentence_is_asked_beside_the_agents_question():
    """h2 J19: the scale wait's words ("I can't tell which my PI meant.") do not overlap the agent's sentence."""
    task = ("We want a partial-correlation network linking the two layers. The aims page says one network for the "
            "whole cohort, the grant narrative says one per tumour, and I can't tell which my PI meant.")
    decision = _turn(task, [dict(quote="a partial-correlation network linking the two layers", depends_on="scale",
                                 unknown_quote="I can't tell which my PI meant.",
                                 outcomes={"per_sample": ["lioness_dragon.per_sample_networks"],
                                           "whole_cohort": ["dragon.two_layer_network"]})],
                     FactQuestion(question="Do you want one network per tumour?", workflows=["LIONESS-DRAGON"],
                                  user_quote="The aims page says one network for the whole cohort, the grant "
                                             "narrative says one per tumour"))
    core = decide_core(decision, task)
    assert len(core.facts) == 2 and _ledger(core) == [("agent", "asked", ""), ("dimension", "asked", "")]


def test_an_agent_asking_nothing_leaves_the_legacy_path_and_no_plan():
    decision = _turn(SAMBAR_TASK, [dict(
        quote="Run SAMBAR on brca_variant_matrix.csv", depends_on="mutation_origin", unknown_quote=SAMBAR_UNSURE,
        outcomes={"somatic": ["sambar.subtypes"], "germline": []}, delivered_by=["sambar.subtypes"])])
    core = decide_core(decision, SAMBAR_TASK)
    assert (core.kind, core.basis, core.evidence["legacy_kept"]) == ("ASK", "needs_fact", True)
    assert "obligations" not in core.evidence  # the legacy path asks every wait itself

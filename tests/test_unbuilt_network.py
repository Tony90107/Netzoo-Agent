"""ROUND-22 (R22-A): a CONDOR the request names, with no network given, is not available as asked unless the request
also names the workflow that builds the network first."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.ruled_out import without_unbuilt_network  # noqa: E402

H27 = ("I need CONDOR run directly on rnaseq_tpm.tsv (genes by 48 samples) so I get gene communities without building "
       "any network first.")
L48 = ("Run CONDOR right away on counts/brain_rnaseq_counts.tsv to get gene communities. We haven't built any network "
       "yet.")


def _check(network="none", named="CONDOR", ruled_out=None, quote="CONDOR run directly on rnaseq_tpm.tsv", **check):
    row = CheckedRequirement(quote=quote, kind="result", status="available",
                             delivered_by=["condor.communities"], attrs={"input_network": network},
                             method={"named": named, "named_quote": named} if named else {})
    return CapabilityCheck(requirements=[row], ruled_out=ruled_out or {}, **check)


def test_a_named_condor_with_no_network_is_not_available_as_asked():
    held = without_unbuilt_network(_check(), H27)
    row = held.results()[0]
    assert (row.status, row.delivered_by, row.blocks) == ("not_available", [], ["CONDOR"])
    assert row.limits == ["CONDOR runs only on a regulator-gene (source-target-weight) network; building one first "
                          "(OTTER, PANDA, PUMA) is a separate run the request does not name"]
    assert held.full_gap


def test_the_users_own_words_ruling_out_a_network_are_quoted():
    # L48: the reading typed a regulator-gene network, but the user said they have none.
    held = without_unbuilt_network(_check("regulator_gene", ruled_out={"network": "We haven't built any network yet"}),
                                   L48)
    assert held.results()[0].limits[0].startswith('You said "We haven\'t built any network yet"; CONDOR runs only on')


def test_a_route_the_user_names_a_given_network_or_no_named_condor_stands():
    check = _check()
    assert without_unbuilt_network(check, "Build a PANDA network from my expression, then run CONDOR on it.") is check
    given = _check("regulator_gene")
    assert without_unbuilt_network(given, "Run CONDOR on panda_net.tsv to get communities.") is given
    unnamed = _check(named=None)
    assert without_unbuilt_network(unnamed, "I want gene communities from my expression data.") is unnamed


def test_the_readings_no_network_counts_only_on_the_result_naming_the_workflow():
    # Held-out h5 Q13-2: "no network" typed on the output-folder clause, though the user named an edge list.
    q13 = ("Run CONDOR on panda_psoriasis_edges.csv (columns source, target, weight) and write the communities to "
           "condor_psoriasis/.")
    folder = _check(quote="write the communities to condor_psoriasis/")
    assert without_unbuilt_network(folder, q13) is folder  # the folder holds "condor", not the user's "CONDOR"


def test_an_only_statement_leaving_out_a_network_counts_for_any_result():
    # C18: "I don't have any motif or PPI files, just this expression table."
    c18 = ("Run CONDOR directly on expr_kidney_fibrosis.tsv to get gene communities. I don't have any motif or PPI "
           "files, just this expression table.")
    held = without_unbuilt_network(_check(quote="to get gene communities", only_inputs=["expression"],
                                          only_inputs_quote="just this expression table"), c18)
    assert held.results()[0].limits[0].startswith('You said "just this expression table"; CONDOR runs only on')


def test_a_named_condor_whose_request_does_not_say_whether_a_network_exists_is_asked():
    # 2026-10-22 (user decision): not stated is asked, never held or refused.
    task = "Please run CONDOR on our lung cohort and put the communities in condor_lung/."
    waiting = without_unbuilt_network(_check("not_stated", quote="run CONDOR on our lung cohort"), task)
    row = waiting.results()[0]
    assert (row.status, row.depends_on, row.delivered_by, row.limits, row.blocks) == (
        "needs_fact", "network_given", ["condor.communities"], [], [])
    assert row.outcomes == {"has": ["condor.communities"], "none": []}
    assert not waiting.full_gap

    from netzoo_agent_core.interpretation.needed_facts import fact_line, fact_questions

    assert fact_questions(waiting) == [
        "Do you already have a regulator-gene (source-target-weight) network for CONDOR to run on?"]
    assert fact_line(row) == (
        '"run CONDOR on our lung cohort" -- CONDOR needs a regulator-gene (source-target-weight) network, and the '
        "request does not say whether you have one: if you do, CONDOR; if not, building one first (OTTER, PANDA, "
        "PUMA) is a separate run the request does not name.")


def test_not_stated_is_held_when_the_user_says_there_is_none_and_untouched_when_another_route_is_named():
    held = without_unbuilt_network(_check("not_stated", ruled_out={"network": "We haven't built any network yet"}),
                                   L48)
    assert held.results()[0].status == "not_available"
    check = _check("not_stated")
    assert without_unbuilt_network(check, "Build a PANDA network from my expression, then run CONDOR on it.") is check


def test_the_unstated_network_wait_survives_the_fact_agent_and_is_asked():
    # Harness repair P1: no wait is lifted when the fact agent runs; this one is code's, as a judged count is.
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.fact_check import FactCheck
    from netzoo_agent_core.interpretation.core_decision import decide_core

    task = "Please run CONDOR on our lung cohort and put the communities in condor_lung/."
    waiting = without_unbuilt_network(_check("not_stated", quote="run CONDOR on our lung cohort"), task)
    assert waiting.results()[0].status == "needs_fact"
    for agent in (None, FactCheck(status="checked")):
        decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                                capability_check=waiting, fact_check=agent)
        core = decide_core(decision, task)
        assert (core.kind, core.basis, core.workflows) == ("ASK", "needs_fact", ["CONDOR"])
        assert [fact.question for fact in core.facts] == [
            "Do you already have a regulator-gene (source-target-weight) network for CONDOR to run on?"]


def test_the_unstated_network_is_asked_beside_a_fact_agent_question():
    # Asked first beside the agent's question (2026-10-22); since harness repair P1 no wait is lifted at all.
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.core_decision import FactQuestion
    from netzoo_agent_core.contracts.fact_check import FactCheck
    from netzoo_agent_core.interpretation.core_decision import decide_core

    task = "Please run CONDOR on our lung cohort; I am not sure whether the weights are signed."
    asked = FactQuestion(question="Are the edge weights signed?", user_quote="I am not sure whether the weights are "
                         "signed", workflows=["CONDOR"])
    agent = FactCheck(status="checked", accepted=[asked])
    waiting = without_unbuilt_network(_check("not_stated", quote="Please run CONDOR on our lung cohort"), task)
    assert waiting.results()[0].status == "needs_fact"
    core = decide_core(TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                                    capability_check=waiting, fact_check=agent), task)
    assert (core.kind, core.basis) == ("ASK", "fact_agent")
    assert [fact.question for fact in core.facts] == [
        "Do you already have a regulator-gene (source-target-weight) network for CONDOR to run on?",
        "Are the edge weights signed?"]

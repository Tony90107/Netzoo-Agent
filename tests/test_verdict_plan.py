"""Verdict layer: a data-needs plan read from routing's reading follows the final verdict (feasibility eval F46)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.contracts.data_plan import DataNeed, DataPlan  # noqa: E402
from netzoo_agent_core.interpretation.data_plan import plan_for_verdict  # noqa: E402

ASK = DataNeed(kind="tf_priors", state="unstated", source="model", action="ask")


def _decision(delivered, basis="reading", **check):
    requirement = CheckedRequirement(quote="Run CONDOR", kind="result", status="available", delivered_by=delivered)
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        data_plan=DataPlan(answerable=True, basis=basis, needs=[ASK]),
                        capability_check=CapabilityCheck(requirements=[requirement], **check))


def test_a_reading_need_no_credited_workflow_takes_is_dropped():
    """F46: routing read a TF-gene network (motif + PPI); the confirmed check credited CONDOR, which takes neither."""
    decision = _decision(["condor.communities"])
    assert plan_for_verdict(decision.data_plan, decision).needs == []


def test_a_need_a_credited_workflow_takes_is_kept():
    decision = _decision(["panda.tf_gene_network"])
    assert plan_for_verdict(decision.data_plan, decision) is decision.data_plan


def test_a_need_from_the_users_own_question_or_an_unconfirmed_check_is_kept():
    for decision in (_decision(["condor.communities"], basis="question"),
                     _decision(["condor.communities"], basis="claims"),
                     _decision(["condor.communities"], provisional=True)):
        assert plan_for_verdict(decision.data_plan, decision) is decision.data_plan


def test_a_verdict_that_still_takes_regulator_priors_keeps_the_whole_reading():
    """Replay: "Our regulators include miRNAs too" credited to PANDA must not lose its miRNA ask."""
    decision = _decision(["panda.tf_gene_network"])
    plan = decision.data_plan.model_copy(update={"needs": [ASK, DataNeed(kind="mirna", state="unstated",
                                                                           source="model", action="ask")]})
    assert plan_for_verdict(plan, decision.model_copy(update={"data_plan": plan})) is plan

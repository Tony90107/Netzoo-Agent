"""confirmed-reason-2026-10-30 (j2 Q18 hi1): a confirmed contract violation replaces a full_gap DECLINE's reason; the
kind never changes, and nothing else does."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph.jev_guard_call import confirmed_violation_core  # noqa: E402

LINE = "SAMBAR incompatible_input_artifacts: expression_matrix"
BOUND = {"what": "jev:condition", "value": "yes", "answer_quote": "Yes, the matrix is RNA-seq expression.",
         "user_quote": "", "question": "Is the data you will use a gene-by-sample expression table?",
         "labels": {"contract": LINE, "workflow": "SAMBAR"}}


def _core(kind, basis, workflows=()):
    return CoreDecision(kind=kind, basis=basis, workflows=list(workflows), evidence={})


def test_a_full_gap_decline_gets_the_confirmed_line():
    after, action = confirmed_violation_core(_core("DECLINE", "full_gap"), BOUND)
    assert action == "reason_confirmed" and after.kind == "DECLINE" and after.basis == "jev_answer"
    line = after.declined[0].line
    assert 'You answered "Yes, the matrix is RNA-seq expression."' in line and "SAMBAR" in line
    assert after.evidence["jev_answer"]["kind_before"] == "DECLINE"
    assert after.evidence["jev_answer"]["basis_before"] == "full_gap"


def test_a_do_keeps_today_s_path_and_nothing_else_changes():
    after, action = confirmed_violation_core(_core("DO", "results_given", ["SAMBAR"]), BOUND)
    assert action == "declined" and after.kind == "DECLINE" and after.evidence["jev_answer"]["kind_before"] == "DO"
    for core in (_core("ASK", "needs_fact"), _core("CLARIFY", "goal_open"), _core("DECLINE", "ruled_out")):
        assert confirmed_violation_core(core, BOUND) == (core, "answer_not_on_do")
    no_workflow = {**BOUND, "labels": {"contract": LINE}}
    assert confirmed_violation_core(_core("DECLINE", "full_gap"), no_workflow)[1] == "answer_not_on_do"

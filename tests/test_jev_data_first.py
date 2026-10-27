"""jev-data-first-2026-10-27 (ROUND.md): a form-only ASK whose workflows the user's data rules out asks the guard's
data confirm instead; nothing else changes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision, FactQuestion  # noqa: E402
from netzoo_agent_core.graph.jev_forms_call import data_first_core  # noqa: E402

TASK = "I'd like SAMBAR to subtype these tumours from that expression matrix, testing 2 to 4 groups."


def _form_ask(depends_on="group_membership"):
    fact = FactQuestion(question="Should each ... one group each, or several groups at once?", user_quote=TASK,
                        depends_on=depends_on, workflows=["SAMBAR"],
                        outcomes={"one_group": ["SAMBAR"], "several_groups": []})
    return CoreDecision(kind="ASK", basis="needs_fact", facts=[fact], workflows=["SAMBAR"])


RULED = {"violated": "SAMBAR incompatible_input_artifacts: expression_matrix", "workflow": "SAMBAR",
         "sentence": TASK, "data": ["expression_matrix", 1.0]}
FINE = {"violated": None, "data": ["mutation_matrix", 0.98], "ruled_out": {"SAMBAR": None}}


def test_a_form_ask_on_ruled_out_data_becomes_the_guard_data_confirm():
    calls = []
    after, action, _ = data_first_core(_form_ask(), TASK, None, check=lambda task, wfs: calls.append(wfs) or RULED)
    assert calls == [["SAMBAR"]] and action == "ask"
    assert (after.kind, after.basis) == ("ASK", "jev_condition")
    assert after.facts[0].depends_on == "jev:condition"
    assert after.evidence["jev_condition"]["kind_before"] == "ASK"
    assert after.evidence["jev_condition"]["form_questions"] == ["group_membership"]


def test_acceptable_data_leaves_the_form_question():
    core = _form_ask()
    after, action, _ = data_first_core(core, TASK, None, check=lambda task, wfs: FINE)
    assert after is core and action == "no_violation"


def test_only_form_only_asks_are_read():
    other = _form_ask().model_copy(update={"facts": [_form_ask().facts[0].model_copy(update={"depends_on": "jev:condition"})]})
    for core in (other, CoreDecision(kind="DO", basis="results_given", workflows=["SAMBAR"])):
        after, action, typed = data_first_core(core, TASK, None, check=lambda task, wfs: (_ for _ in ()).throw(AssertionError))
        assert after is core and action == "not_form_ask" and typed is None

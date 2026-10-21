"""ROUND-14: the capability sheet's `expects` and the one judgement code makes from them."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.graph.capability_check_call import request_condition_check  # noqa: E402
from netzoo_agent_core.interpretation.expects import code_answer, expectations, stated_opposite  # noqa: E402


def test_every_expectation_has_a_source_and_ties_only_boolean_controls():
    bonobo = expectations("run_bonobo")
    assert {(item.control, item.value) for item in bonobo} == {("log_transformed", True), ("centered", True)}
    assert all(item.source.startswith("[REG]") and item.state for item in bonobo)
    assert expectations("run_panda") and all(item.control is None for item in expectations("run_panda"))
    assert expectations("run_lioness_panda") == ()


def test_code_judges_only_a_stated_opposite_of_one_named_control():
    assert stated_opposite("run_bonobo", "The data are raw counts, not log-transformed").id == "bonobo.log_transformed"
    assert stated_opposite("run_bonobo", "not centered per gene").id == "bonobo.centered"
    # ROUND-12 C52: the expected state itself is never judged by code (a sentence may add other demands)
    assert stated_opposite("run_bonobo", "The data are log2-transformed and centered per gene") is None
    # several controls named at once, or none of them: left to the condition check
    assert stated_opposite("run_bonobo", "log2-transformed but not centered") is None
    assert stated_opposite("run_bonobo", "The data are not batch-corrected") is None
    assert code_answer("BONOBO", "raw counts, not log-transformed") == "violates"
    assert code_answer("PANDA", "raw counts, not log-transformed") is None


def test_a_condition_check_code_answers_in_full_needs_no_model():
    pairs = [("per-sample networks", "raw counts, not log-transformed", "BONOBO", "BONOBO results")]
    answers, usage, warnings = request_condition_check(SimpleNamespace(), {}, pairs, None, [])
    assert answers == ["violates"]
    # with a pair code cannot judge and no model configured, nothing is answered (as before)
    mixed = [*pairs, ("per-sample networks", "computed on our cluster", "BONOBO", "BONOBO results")]
    assert request_condition_check(SimpleNamespace(), {}, mixed, None, [])[0] is None

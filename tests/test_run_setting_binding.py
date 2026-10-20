"""ROUND-06 (collab/ROUND-06-PLAN.md): a setting the check read reaches the run, on every path that plans one.

h3 L15 and core-judgment C40 (p1-p5r) asked BONOBO for ".csv" networks; the check read the format each time, and
each time the run was planned with the default ".h5" under an approving verdict. Two causes: a run adopted on a
guidance turn (`_with_requested_run`) never bound the check's settings, and a setting read with its value only in the
words naming it ("saved as .csv files", value words empty) was skipped as having no value -- as was the sample list
("only write networks for samples MS_03, MS_11 and MS_19"), so every sample would have been written.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_requested_run import _ask, _check, _decision, _run  # noqa: E402

from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.interpretation.method_conditions import run_setting_value  # noqa: E402
from netzoo_agent_core.workflow_conditions import conditions_for  # noqa: E402

C40 = ("Run BONOBO on expr_ms_lesions.tsv with 27 lesion samples and only write networks for samples MS_03, MS_11 and "
       "MS_19, saved as .csv files.")
ASK = "Run BONOBO on expr_ms_lesions.tsv with 27 lesion samples"


def _bonobo(*settings):
    ask = {**_ask(ASK, ["bonobo.per_sample_networks"]), "named_method": "BONOBO", "named_method_quote": "BONOBO",
           "settings": [{"name": name, "quote": quote, "value_quote": value} for name, quote, value in settings]}
    return _check(C40, ask)


def _events(events):
    return [event[2] for event in events]


def test_a_run_adopted_on_a_guidance_turn_carries_the_format_the_check_read(monkeypatch):
    """h3 L15, C40 p1/p2: the check read ".csv" as the value."""
    check = _bonobo(("BONOBO.bonobo_output_format", "saved as .csv files", ".csv"))
    decision, events = _run(C40, _decision(check, ["run_bonobo"]), monkeypatch)
    assert decision.action == "run_bonobo" and decision.bonobo_output_format == ".csv"
    assert "routing.run_controls_bound" in _events(events) and "routing.requested_run_adopted" in _events(events)


def test_a_value_only_in_the_words_naming_the_setting_is_bound(monkeypatch):
    """C40 p3/p5r: value words empty, ".csv" in "saved as .csv files"."""
    check = _bonobo(("BONOBO.bonobo_output_format", "saved as .csv files", ""))
    decision, events = _run(C40, _decision(check, ["run_bonobo"]), monkeypatch)
    assert decision.bonobo_output_format == ".csv"
    [bindings] = [event[4]["bindings"] for event in events if event[2] == "routing.run_fact_bindings"]
    assert [(b["control"], b["value"], b["disposition"], b["from"]) for b in bindings] == [
        ("bonobo_output_format", ".csv", "applied", "words")]


def test_a_sample_list_the_run_cannot_carry_holds_the_run_instead_of_running_every_sample(monkeypatch):
    """C40 p5r: "only write networks for samples MS_03, MS_11 and MS_19", value words empty."""
    check = _bonobo(("BONOBO.sample_names", "only write networks for samples MS_03, MS_11 and MS_19", ""),
                    ("BONOBO.bonobo_output_format", "saved as .csv files", ""))
    decision, events = _run(C40, _decision(check, ["run_bonobo"]), monkeypatch)
    assert decision.action == "no_tool" and not decision.should_execute
    assert decision.run_verdict is not None and decision.run_verdict.held
    assert "only write networks for samples MS_03, MS_11 and MS_19" in decision.capability_check.unchecked
    assert {"routing.run_settings_unbound", "routing.run_held"} <= set(_events(events))
    assert "routing.requested_run_adopted" not in _events(events)


def test_the_run_path_binds_the_same_way(monkeypatch):
    """`_on_run_verdict` (a run routing planned itself) shares the binding."""
    events = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: events.append(args))
    check = _bonobo(("BONOBO.bonobo_output_format", "saved as .csv files", ""))
    run = _decision(check, ["run_bonobo"]).model_copy(update={"action": "run_bonobo", "should_execute": True,
                                                               "match_basis": "workflow_name"})
    invocation = router_invocation._RouterInvocation(decision=run, routing_state={}, usage=None, budget_warnings=[],
                                                     reason_code=None)
    decision = router_invocation._on_run_verdict(None, {}, C40, invocation, check, "ok").decision
    assert decision.action == "run_bonobo" and decision.bonobo_output_format == ".csv"


def test_a_name_stated_value_is_kept_and_never_replaced():
    """A request that set the control as name=value is the run's already (`set_by_request`): not rebound."""
    from netzoo_agent_core.interpretation.method_conditions import unbound_settings, verified_controls

    check = _bonobo(("BONOBO.bonobo_output_format", "saved as .csv files", ""))
    assert verified_controls(check, "run_bonobo") == {"bonobo_output_format": ".csv"}
    assert unbound_settings(check, "run_bonobo", lambda name: name == "bonobo_output_format") == []


def test_a_number_is_taken_from_the_words_only_when_they_state_one_and_it_is_in_range():
    dragon = conditions_for("run_dragon")
    lam = dragon.settings["lambda1"]
    one = {"name": "DRAGON.lambda1", "quote": "lambda1 at 0.3", "value": ""}
    two = {"name": "DRAGON.lambda1", "quote": "lambda1 0.3 and lambda2 0.6", "value": ""}
    out = {"name": "DRAGON.lambda1", "quote": "lambda1 at 1.5", "value": ""}
    none = {"name": "DRAGON.lambda1", "quote": "let DRAGON estimate lambda1", "value": ""}
    assert run_setting_value(lam, dragon, one) == 0.3
    assert run_setting_value(lam, dragon, two) is None
    assert run_setting_value(lam, dragon, out) is None
    assert run_setting_value(lam, dragon, none) is None


def test_number_words_stating_no_number_leave_the_default_as_the_check_reads_them(monkeypatch):
    """h2 J11 "Leave lambda1 and lambda2 empty so they're estimated", value "empty": the check reads no value and
    approves; the run takes LIONESS-DRAGON's own estimate instead of being held."""
    from netzoo_agent_core.interpretation.method_conditions import unbound_settings, verified_controls

    task = "Run LIONESS-DRAGON on our two layers. Leave lambda1 and lambda2 empty so they're estimated."
    ask = {**_ask("Run LIONESS-DRAGON on our two layers", ["lioness_dragon.per_sample_networks"]),
           "omics_layers": 2, "named_method": "LIONESS-DRAGON", "named_method_quote": "LIONESS-DRAGON",
           "settings": [{"name": "LIONESS-DRAGON.lambda1", "quote": "lambda1", "value_quote": "empty"},
                        {"name": "LIONESS-DRAGON.lambda2", "quote": "lambda2", "value_quote": "empty"}]}
    check = _check(task, ask)
    assert unbound_settings(check, "run_lioness_dragon") == [] and verified_controls(check, "run_lioness_dragon") == {}

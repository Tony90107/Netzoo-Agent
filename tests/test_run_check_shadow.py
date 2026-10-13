"""Verdict layer step 1: the capability check's verdict on a run routing selected, recorded in shadow only."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.run_check import run_check_verdict  # noqa: E402

F32 = "I only have gene expression. Use SAMBAR to find expression-based patient subtypes."
TWO = "Run it on my 60 tumors. I want subtypes and a per-sample TF-gene network."


def _ask(quote, delivered=()):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": [], "scale": "unstated", "omics_layers": 0,
            "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none",
            "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
            "asked_as": "request"}


def _check(task, sentences):
    proposal = proposal_model(len(sentences)).model_validate({
        f"s{index}": {"role": role, "has": has, "about_methods": [], "asks": asks}
        for index, (role, has, asks) in enumerate(sentences, 1)})
    return build_capability_check(task, proposal)[0]


def _f32(delivered=()):
    return _check(F32, [("background", ["I only have gene expression."], []),
                        ("asks", [], [_ask("find expression-based patient subtypes", delivered)])])


def test_a_result_no_workflow_gives_is_a_gap_for_the_run():
    assert run_check_verdict(_f32(), "run_sambar")["verdict"] == "gap"


def test_the_runs_workflow_credited_agrees():
    assert run_check_verdict(_f32(["sambar.subtypes"]), "run_sambar")["verdict"] == "agrees"


def test_a_result_credited_only_to_another_workflow():
    verdict = run_check_verdict(_f32(["sambar.subtypes"]), "run_lioness_panda")
    assert verdict["verdict"] == "other_workflow"
    assert verdict["results"] == [{"quote": "find expression-based patient subtypes", "status": "available",
                                   "credited": ["run_sambar"]}]


def test_the_run_gives_what_is_given_and_the_rest_is_a_partial_gap():
    check = _check(TWO, [("asks", [], []), ("asks", [], [_ask("subtypes"), _ask(
        "a per-sample TF-gene network", ["lioness_panda.per_sample_networks"])])])
    assert run_check_verdict(check, "run_lioness_panda")["verdict"] == "partial_gap"


def test_actions_off_the_sheet_and_unconfirmed_checks_are_said_as_such():
    assert run_check_verdict(_f32(), "download_string")["verdict"] == "not_on_sheet"
    assert run_check_verdict(_f32().model_copy(update={"provisional": True}), "run_sambar")["verdict"] == "unconfirmed"
    assert run_check_verdict(None, "run_sambar")["verdict"] == "unconfirmed"


def _invocation(action):
    decision = TaskDecision(action=action, in_scope=True, should_execute=True, confidence=0.9, reason="r",
                            capability_match_status="exact", match_basis="workflow_name", matched_actions=[action])
    return router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None, budget_warnings=[],
                                               reason_code=None)


def _proposal(delivered=()):
    return proposal_model(2).model_validate({
        "s1": {"role": "background", "has": ["I only have gene expression."], "about_methods": [], "asks": []},
        "s2": {"role": "asks", "has": [], "about_methods": [],
               "asks": [_ask("find expression-based patient subtypes", delivered)]}})


def test_the_shadow_records_the_verdict_only_when_enabled(monkeypatch):
    events = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: events.append(args))
    invocation = _invocation("run_sambar")
    monkeypatch.delenv("NETZOO_SHADOW_RUN_CHECK", raising=False)
    router_invocation._with_run_check_shadow(None, {}, F32, invocation, _proposal(), "ok")
    assert events == []
    monkeypatch.setenv("NETZOO_SHADOW_RUN_CHECK", "1")
    updated = router_invocation._with_run_check_shadow(None, {}, F32, invocation, _proposal(), "ok")
    (payload,) = [event[4] for event in events if event[2] == "routing.run_check_shadow"]
    assert payload["verdict"] == "gap" and payload["action"] == "run_sambar" and payload["check_status"] == "ok"
    assert updated.decision == invocation.decision  # nothing acts on it


def test_a_backup_reading_is_unconfirmed_and_a_guidance_turn_is_skipped(monkeypatch):
    events = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: events.append(args))
    monkeypatch.setenv("NETZOO_SHADOW_RUN_CHECK", "1")
    router_invocation._with_run_check_shadow(None, {}, F32, _invocation("run_sambar"), _proposal(), "fallback")
    router_invocation._with_run_check_shadow(None, {}, F32, _invocation("no_tool"), _proposal(), "ok")
    assert [event[4]["verdict"] for event in events if event[2] == "routing.run_check_shadow"] == ["unconfirmed"]


def test_the_shadow_asks_the_second_opinion_an_exact_run_is_owed(monkeypatch):
    """r17 PQ3-2: the first reading credited nothing to an exact PUMA run; the guidance turn's second opinion is asked."""
    events, asked = [], []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args: events.append(args))
    monkeypatch.setenv("NETZOO_SHADOW_RUN_CHECK", "1")

    def second_opinion(context, state, shown, usage, warnings, situation):
        asked.append([workflow for _quote, workflow, _text in shown])
        return ["all"] * len(shown), usage, warnings

    monkeypatch.setattr(router_invocation, "request_second_opinion", second_opinion)
    router_invocation._with_run_check_shadow(None, {}, F32, _invocation("run_sambar"), _proposal(), "ok")
    assert asked == [["SAMBAR"]]
    (payload,) = [event[4] for event in events if event[2] == "routing.run_check_shadow"]
    assert payload["verdict"] == "agrees"


def test_a_run_turn_is_re_read_like_a_guidance_turn():
    """r17b MX1-1: "and upload the networks to a public repository for us" beside a quoted result was never re-read."""
    from netzoo_agent_core.interpretation.reread import reread_passages

    task = ("Run it now: build TF-gene networks per sample from the expression, motifs and PPI of 44 samples, "
            "and upload the networks to a public repository for us.")
    proposal = proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
        _ask("build TF-gene networks per sample", ["lioness_panda.per_sample_networks"])]}})
    check = build_capability_check(task, proposal)[0]
    decision = TaskDecision(action="run_lioness_panda", in_scope=True, should_execute=True, confidence=1.0,
                            reason="r", capability_check=check)
    assert reread_passages(task, decision) == [task]

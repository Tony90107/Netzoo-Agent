"""R15: contract conditions listed by code, Jev says whether the request states them (no network calls)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core import jev_client  # noqa: E402
from netzoo_agent_core.lean import LeanDecision  # noqa: E402
from netzoo_agent_core.lean import required_conditions as rc  # noqa: E402

L008 = ("Generate the motif and PPI priors, then run LIONESS to get a network for each patient in our sickle cell "
        "disease erythroblast pilot.")


def do(steps):
    return LeanDecision(kind="DO", steps=list(steps), question="", reply="plan", rules=[], notes=["n"])


def fake(answers):
    def jev(state, questions, *, timeout):
        assert set(questions) == set(answers)
        return {"answers": {k: {"choice": c, "confidence": p} for k, (c, p) in answers.items()},
                "usage": {"cost": 0.00003}}
    return jev


def test_conditions_come_from_the_plan():
    assert rc.conditions(L008, {}, ["SPONGE-PRIORS", "LIONESS-PANDA"]) == ["count", "expression"]
    assert rc.conditions("x", {}, ["PANDA"]) == ["motif", "ppi", "expression"]
    assert rc.conditions("x", {}, ["LIONESS-PANDA", "PORCUPINE"])[:3] == ["motif", "ppi", "gmt"]
    assert "per_sample" in rc.conditions("x", {}, ["PORCUPINE"])
    assert rc.conditions("x", {}, ["SCORPION", "PORCUPINE"])[-4:] == ["groups", "group_wanted", "group_table",
                                                                       "replicates"]
    stated = {"sample_count": 40, "sample_count_quote": "40 tumours"}
    assert "count" not in rc.conditions("our 40 tumours", stated, ["LIONESS-PANDA"])


def test_unstated_condition_asks(monkeypatch):
    monkeypatch.setattr(jev_client, "decide", fake({"count": ("not_mentioned", 1.0), "expression": ("stated_has", 0.9)}))
    decided, record = rc.check(L008, {}, do(["SPONGE-PRIORS", "LIONESS-PANDA"]))
    assert decided.kind == "ASK" and "how many samples" in decided.question
    assert decided.rules == ["R15: not stated in the request: count"] and decided.notes == []
    assert record["cost_usd"] == 0.00003


def test_low_confidence_and_stated_lacks_change_nothing(monkeypatch):
    monkeypatch.setattr(jev_client, "decide", fake({"count": ("not_mentioned", 0.5), "expression": ("stated_lacks", 1.0)}))
    decided, _ = rc.check(L008, {}, do(["SPONGE-PRIORS", "LIONESS-PANDA"]))
    assert decided.kind == "DO" and decided.rules == []


def test_grouping_needs_groups_wanted(monkeypatch):
    base = {"motif": ("stated_has", 1), "ppi": ("stated_has", 1), "replicates": ("stated_lacks", 1),
            "group_table": ("not_mentioned", 1)}
    monkeypatch.setattr(jev_client, "decide", fake({**base, "group_wanted": ("stated_lacks", 0.95)}))
    assert rc.check("x", {}, do(["SCORPION"]))[0].kind == "DO"  # all cells, one network (L011, F005)
    monkeypatch.setattr(jev_client, "decide", fake({**base, "group_wanted": ("stated_has", 0.95)}))
    assert rc.check("x", {}, do(["SCORPION"]))[0].kind == "ASK"  # per cell type, no table (L158)


def test_jev_failure_and_other_kinds_leave_the_decision(monkeypatch):
    def down(*a, **k):
        raise RuntimeError("no_key")
    monkeypatch.setattr(jev_client, "decide", down)
    decided, record = rc.check(L008, {}, do(["SPONGE-PRIORS", "LIONESS-PANDA"]))
    assert decided.kind == "DO" and "no_key" in record["error"]
    ask = LeanDecision(kind="EXPLAIN", steps=["PANDA"], question="", reply="", rules=[])
    assert rc.check("x", {}, ask) == (ask, None)


def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("NETZOO_LEAN_CONDITION_CHECK", raising=False)
    assert not rc.enabled()
    monkeypatch.setenv("NETZOO_LEAN_CONDITION_CHECK", "on")
    assert rc.enabled()


def test_sponge_added_by_the_model_does_not_cover_the_priors():
    # R051: only a STRING PPI is named; the model put SPONGE in the plan on its own
    task = "Now run PANDA on the 85 colorectal tumour RNA-seq profiles using the STRING human PPI I downloaded."
    assert rc.conditions(task, {}, ["SPONGE-PRIORS", "PANDA"])[:2] == ["motif", "ppi"]
    # asked for: SPONGE covers them (L008)
    assert "motif" not in rc.conditions(L008, {}, ["SPONGE-PRIORS", "LIONESS-PANDA"])
    assert "motif" not in rc.conditions("Build human priors with SPONGE, then run PANDA.", {}, ["SPONGE-PRIORS", "PANDA"])


def test_sponge_question_offers_to_build(monkeypatch):
    task = "Run PANDA on our 85 tumour profiles with the STRING PPI I downloaded."
    need = rc.conditions(task, {}, ["SPONGE-PRIORS", "PANDA"])
    monkeypatch.setattr(jev_client, "decide", fake({n: ("stated_has", 1.0) for n in need} | {"motif": ("not_mentioned", 1.0)}))
    decided, _ = rc.check(task, {}, do(["SPONGE-PRIORS", "PANDA"]))
    assert decided.kind == "ASK" and "SPONGE can build" in decided.question


def test_porcupine_first_asks_the_network_kind():
    need = rc.conditions("x", {}, ["PORCUPINE"])
    assert "per_sample" in need and "regulatory" in need
    assert "regulatory" not in rc.conditions("x", {}, ["LIONESS-PANDA", "PORCUPINE"])

"""The closed settings read (docs/research-log/jev-settings-2026-10-31/ROUND.md): a strong read of a control a credited
workflow passes is added to that result and judged by the workflow's rules; an unmatched settings-only row inside its
sentence is dropped, or gets the contract's "has no setting for" line; off by default."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.graph import jev_settings_call  # noqa: E402
from netzoo_agent_core.interpretation.closed_settings import (  # noqa: E402
    OTHER, controls, questions, strong_reads, with_closed_settings,
)

# j8 Z01, recorded: SAMBAR credited, the k range its own unmatched row.
Z01 = ("I have somatic mutation calls for 85 lung adenocarcinoma patients as a sample-by-gene table, an exon-length "
       "file, a cancer gene list and an MSigDB pathway GMT. Please run SAMBAR to sort these patients into "
       "mutation-based subtypes. Try anywhere between 2 and 5 subtypes.")
RANGE = "Try anywhere between 2 and 5 subtypes."


def _check(task=Z01, samples=85, range_row=True):
    sambar = CheckedRequirement(quote="Please run SAMBAR to sort these patients into mutation-based subtypes.",
                                kind="result", status="available", delivered_by=["sambar.subtypes"],
                                method={"samples": samples})
    rows = [sambar]
    if range_row:
        rows.append(CheckedRequirement(quote=RANGE, kind="result", status="not_available", blank=True))
    return CapabilityCheck(requirements=rows)


def _read(control, value, sentence=RANGE, task=Z01):
    start = task.index(sentence)
    at = task.index(value, start)
    return {"control": control, "sentence": sentence, "value": value, "value_span": (at, at + len(value))}


def test_the_questions_come_from_the_contracts_controls_and_one_for_none_of_them():
    assert "kmax" in controls() and controls()["kmax"]["type"] == "integer"
    assert questions()["kmax"].startswith("Does the user ask to set kmax (integer): Largest number")
    assert OTHER in questions() and "kmax" in questions()[OTHER]


def test_a_k_range_a_credited_sambar_takes_is_no_unmatched_part():
    after = with_closed_settings(_check(), Z01, [_read("kmin", "2"), _read("kmax", "5")])
    assert [row.quote for row in after.results()] == [_check().results()[0].quote]
    settings = after.results()[0].method["settings"]
    assert [(s["name"], s["value"]) for s in settings] == [("SAMBAR.kmin", "2"), ("SAMBAR.kmax", "5")]
    assert Z01[settings[1]["span"][0]:settings[1]["span"][1]] == "5"  # inside the sentence, not the "5" of "85"
    assert after.results()[0].status == "available"


def test_a_range_beyond_the_samples_is_judged_by_sambars_own_rule():
    after = with_closed_settings(_check(samples=4, range_row=False), Z01, [_read("kmax", "5")])
    row = after.results()[0]
    assert row.status == "not_available"
    assert row.limits == ["SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled"]


def test_a_setting_no_credited_workflow_has_keeps_its_row_with_the_contract_line():
    after = with_closed_settings(_check(), Z01, [{"control": OTHER, "sentence": RANGE, "value": "", "value_span": None}])
    row = after.results()[1]
    assert row.status == "not_available" and row.limits and "has no setting for" in row.limits[0]


def test_nothing_applies_without_a_read_or_on_an_unconfirmed_check():
    check = _check()
    assert with_closed_settings(check, Z01, []) is check
    provisional = check.model_copy(update={"provisional": True})
    assert with_closed_settings(provisional, Z01, [_read("kmax", "5")]) is provisional


def test_strong_reads_need_both_confidences_and_a_value_inside_the_sentence():
    sentences = {"s1": RANGE}
    answers = {"kmax": {"choice": "set", "confidence": 0.9}, "kmin": {"choice": "set", "confidence": 0.6}}
    picks = {"kmax": {"choice": "s1", "confidence": 0.9}, "kmin": {"choice": "s1", "confidence": 0.9}}
    values = {"kmax": {"value": "5", "words": "between 2 and 5"}, "kmin": {"value": "2", "words": "between 2"}}
    kept = strong_reads(Z01, answers, picks, sentences, values)
    assert [(r["control"], r["value"]) for r in kept] == [("kmax", "5")]  # kmin: Jev at 0.6
    outside = strong_reads(Z01, answers, picks, sentences, {"kmax": {"value": "85", "words": "85 lung"}})
    assert outside == []  # the value's words lie outside the picked sentence


def test_off_makes_no_call_and_leaves_the_check(monkeypatch):
    monkeypatch.delenv("NETZOO_JEV_SETTINGS", raising=False)
    monkeypatch.setattr(jev_settings_call, "decide", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    check = _check()
    assert jev_settings_call.apply_jev_settings(None, {}, Z01, check, None, []) == (check, None, [])


def test_a_failed_read_leaves_the_check_and_records_why(monkeypatch):
    monkeypatch.setenv("NETZOO_JEV_SETTINGS", "on")
    monkeypatch.setattr(jev_settings_call, "_jev_read", lambda task: (_ for _ in ()).throw(RuntimeError("down")))
    events = []
    monkeypatch.setattr(jev_settings_call, "record_event", lambda *a: events.append(a[2:]))
    check = _check()
    assert jev_settings_call.apply_jev_settings(None, {}, Z01, check, None, [])[0] is check
    assert events and events[0][0] == "core.jev_settings" and "down" in events[0][2]["error"]

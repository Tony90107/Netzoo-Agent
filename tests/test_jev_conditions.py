"""jev-conditions-2026-10-28 (ROUND.md): a form condition stated apart from every ask, read by Jev (J01)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.jev_forms import condition_doubts, doubted  # noqa: E402

J01 = ("I want to understand gene regulation during zebrafish fin regeneration: five time points, four replicates "
       "each, bulk RNA-seq. Any thoughts on how to approach it?")


def _row(quote, **attrs):
    return CheckedRequirement(quote=quote, kind="result", status="not_available", attrs=attrs)


def _reader(probs: dict, calls: list):
    def read(task, quote, attr, options):
        calls.append((attr, quote))
        return doubted({"probabilities": probs.get(attr, {})}, options)
    return read


def test_a_doubted_time_condition_is_not_said_and_nothing_else_changes():
    calls = []
    [row] = condition_doubts(J01, [_row("five time points", time_model="dynamic")],
                             _reader({"time_model": {"dynamic": 0.06, "separate": 0.42, "not_stated": 0.52}}, calls),
                             None)
    assert calls == [("time_model", "five time points")]
    assert row.doubted_forms == ["time_model"] and row.status == "not_available" and row.delivered_by == []


def test_a_condition_jev_agrees_with_keeps_its_reason():
    [row] = condition_doubts(J01, [_row("five time points", time_model="dynamic")],
                             _reader({"time_model": {"dynamic": 1.0}}, []), None)
    assert row.doubted_forms == []


def test_overlap_condition_uses_the_overlap_reader_and_no_reader_reads_nothing():
    row = _row("each gene may sit in several communities", group_membership="several_groups")
    [doubted_row] = condition_doubts("task", [row], None, lambda task, quote: True)
    assert doubted_row.doubted_forms == ["group_membership"]
    assert condition_doubts("task", [row], None, None) == [row]

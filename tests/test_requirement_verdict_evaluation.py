"""Incomplete blind evidence must never pass the Log 403 promotion gates."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def evaluator(tmp_path):
    path = Path(__file__).parents[1] / "docs/research-log/requirement-verdicts-2026-10-10/analyze11.py"
    spec = importlib.util.spec_from_file_location("requirement_verdict_evaluation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.LIVE = tmp_path
    module.FROZEN_RUNS = {"probe": ("outage", 1)}
    module.FROZEN_ITEMS = {"C1": 1}
    rows = {
        f"sid-{arm}": {
            "arm": arm, "item": "C1", "rep": 1, "family": "C", "action": "no_tool",
            "replay_equal": True, "check_calls": [["backup", "success"]], "contradictions": [],
            "check": {"provisional": True}, "layers": [{"expect": "supported", "checked": "unconfirmed"}],
        }
        for arm in ("base", "cand")
    }
    labels = {code: {"R": ["UNCONFIRMED"], "contradiction": "no"} for code in ("S001", "S002")}
    for name, data in (
        ("structure", rows), ("blind-key", {"S001": "sid-base", "S002": "sid-cand"}),
        ("labels-A", labels), ("labels-B", labels),
    ):
        (tmp_path / f"probe-{name}.json").write_text(json.dumps(data))
    return module


def _replace(evaluator, name, change):
    path = evaluator.LIVE / f"probe-{name}.json"
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def test_complete_independently_labelled_evidence_can_be_analyzed(evaluator):
    evaluator.main("probe", "outage")
    report = (evaluator.LIVE / "probe-analysis.txt").read_text()
    assert "unlabelled 0" in report and "S-G1 -> PASS" in report
    assert report.count("requirements 1 (positive 1, negative 0)") == 2


@pytest.mark.parametrize("name", ["labels-A", "labels-B"])
def test_a_missing_labeller_or_session_blocks_promotion(evaluator, name):
    _replace(evaluator, name, lambda data: data.pop("S001"))
    with pytest.raises(ValueError, match="label coverage"):
        evaluator.main("probe", "outage")
    assert not (evaluator.LIVE / "probe-analysis.txt").exists()


@pytest.mark.parametrize("labels", [[], ["UNCONFIRMED", "GIVEN"], ["INVALID"]])
def test_each_labeller_must_label_every_requirement_with_a_valid_status(evaluator, labels):
    for name in ("labels-A", "labels-B"):
        _replace(evaluator, name, lambda data: data["S001"].update(R=labels))
    with pytest.raises(ValueError, match="requirement labels"):
        evaluator.main("probe", "outage")


def test_disagreements_require_an_explicit_resolution(evaluator):
    _replace(evaluator, "labels-B", lambda data: data["S001"].update(R=["GIVEN"]))
    with pytest.raises(ValueError, match="unresolved"):
        evaluator.main("probe", "outage")


def test_resolution_is_validated_and_counted(evaluator):
    _replace(evaluator, "labels-B", lambda data: data["S001"].update(R=["GIVEN"]))
    resolution = evaluator.LIVE / "probe-labels-resolved.json"
    resolution.write_text(json.dumps({"S001": {"R": [], "contradiction": "no"}}))
    with pytest.raises(ValueError, match="requirement labels"):
        evaluator.main("probe", "outage")
    resolution.write_text(json.dumps({"S001": {"R": ["UNCONFIRMED"], "contradiction": "no"}}))
    evaluator.main("probe", "outage")
    assert "labeller disagreements: 1 sessions; unresolved 0" in (
        evaluator.LIVE / "probe-analysis.txt").read_text()


def test_replay_must_reproduce_the_reply_that_was_labelled(evaluator):
    _replace(evaluator, "structure", lambda data: data["sid-cand"].update(replay_equal=False))
    with pytest.raises(ValueError, match="replay"):
        evaluator.main("probe", "outage")


def test_blinding_map_cannot_drop_a_session(evaluator):
    _replace(evaluator, "blind-key", lambda data: data.pop("S002"))
    with pytest.raises(ValueError, match="session coverage"):
        evaluator.main("probe", "outage")


def test_a_complete_smaller_subset_cannot_replace_the_frozen_round(evaluator):
    evaluator.FROZEN_RUNS["probe"] = ("outage", 2)
    with pytest.raises(ValueError, match="frozen round coverage"):
        evaluator.main("probe", "outage")


def test_dropping_a_requirement_from_both_code_and_labels_blocks_promotion(evaluator):
    _replace(evaluator, "structure", lambda data: data["sid-base"].update(layers=[]))
    for name in ("labels-A", "labels-B"):
        _replace(evaluator, name, lambda data: data["S001"].update(R=[]))
    with pytest.raises(ValueError, match="requirement coverage"):
        evaluator.main("probe", "outage")


def test_replay_keeps_the_reply_when_the_runtime_would_skip_an_invalid_card(monkeypatch):
    path = Path(__file__).parents[1] / "docs/research-log/requirement-verdicts-2026-10-10/replay_sessions.py"
    spec = importlib.util.spec_from_file_location("requirement_verdict_replay", path)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    from netzoo_agent_core.contracts import AIMessage

    monkeypatch.setattr(replay, "respond", lambda *_: {
        "messages": [AIMessage(content="The original reply")], "reply_kind": "verified_guidance"})
    monkeypatch.setattr(replay, "build_next_turn_prompt", lambda *_: None)

    def invalid_card(*args, **kwargs):
        raise ValueError("too many options")

    monkeypatch.setattr(replay, "build_reply_card", invalid_card)
    decision = {"action": "no_tool", "in_scope": True, "should_execute": False,
                "confidence": 0.5, "reason": "r"}
    result = replay.render("Question", decision, {})
    assert result["reply"] == "The original reply"
    assert result["card"] is None and result["card_error"] == "ValueError: too many options"

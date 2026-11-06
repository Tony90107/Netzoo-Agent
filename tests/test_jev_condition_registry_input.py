"""Jev's data-condition confirm (2026-11-06): a named producer's registered output is the data's type, and a confirm
always states what it asks."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.graph import jev_guard_call  # noqa: E402

TRACES = Path(__file__).parents[1] / ".netzoo" / "traces"
PORCUPINE = ("Run PORCUPINE on the LIONESS-PANDA networks /data/porc/lioness_panda_network.txt "
             "with pathways /data/porc/pathways.gmt.")


def _jev(data, monkeypatch):
    """Jev answers `data` for the data read and places the first sentence, as in the live traces."""
    def decide(state, questions):
        answers = {}
        if "data" in questions:
            answers["data"] = {"choice": data[0], "confidence": data[1]}
        if "has" in questions:
            answers["has"] = {"choice": "not_stated", "confidence": 0.9}
        if "sentence" in questions:
            answers["sentence"] = {"choice": "s1", "confidence": 0.9}
        return {"answers": answers, "usage": {"cost": 0}}
    monkeypatch.setattr(jev_guard_call, "_decide", decide)


def test_a_named_producer_vetoes_a_conflicting_data_read(monkeypatch):
    # Live traces 1930a440, d41701e8 (and three more): Jev read the LIONESS-PANDA networks as coexpression_network
    # (0.78), which PORCUPINE lists as incompatible, and the turn asked a blank confirm instead of planning.
    _jev(("coexpression_network", 0.78), monkeypatch)
    typed = jev_guard_call.check_typed_data(PORCUPINE, ["PORCUPINE"])
    assert typed["violated"] is None and typed.get("unplaced") is None
    assert typed["registry_veto"] == {"PORCUPINE": ["regulatory_network"]}


def test_a_coexpression_file_given_to_porcupine_is_still_confirmed_with_a_stated_condition(monkeypatch):
    _jev(("coexpression_network", 0.9), monkeypatch)
    task = "Run PORCUPINE on my gene co-expression matrix /data/x/coexpr.tsv with pathways /data/x/p.gmt."
    typed = jev_guard_call.check_typed_data(task, ["PORCUPINE"])
    assert typed["violated"] == "PORCUPINE incompatible_input_artifacts: coexpression_network"
    core = CoreDecision(kind="DO", basis="run", workflows=["PORCUPINE"])
    asked, outcome = jev_guard_call.conditioned_core(core, typed)
    assert outcome == "ask"
    question = asked.facts[0].question
    assert "co-expression or correlation matrix" in question and question.endswith("? (yes or no)")


def test_no_confirm_is_asked_with_an_empty_statement():
    core = CoreDecision(kind="DO", basis="run", workflows=["PORCUPINE"])
    typed = {"violated": "PORCUPINE input_artifacts: regulatory_network", "sentence": "Run PORCUPINE ...",
             "data": ("", 0.9)}
    assert jev_guard_call.conditioned_core(core, typed) == (core, "no_statement")


@pytest.mark.parametrize("prefix", ["1930a440", "d41701e8"])
def test_replay_of_the_live_traces_reaches_planning(prefix, monkeypatch):
    paths = list(TRACES.glob(f"{prefix}*/events.jsonl"))
    if not paths:
        pytest.skip("local trace not present")
    events = [json.loads(line) for line in paths[0].read_text().splitlines()]
    task = next(e["payload"]["check"]["goal_quote"] for e in events if e["event_type"] == "routing.capability_checked")
    recorded = next(e["payload"]["evidence"]["jev_condition"] for e in events if e["event_type"] == "core.decision")
    _jev(tuple(recorded["data"]), monkeypatch)
    typed = jev_guard_call.check_typed_data(task, ["PORCUPINE"])
    core = CoreDecision(kind="DO", basis="run", workflows=["PORCUPINE"])
    assert jev_guard_call.conditioned_core(core, typed) == (core, "no_violation")

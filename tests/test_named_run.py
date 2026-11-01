"""Named run in the row's sentence (docs/research-log/excluded-entries-2026-11-01/ROUND-N.md)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_closed_settings_retype import C34, _c34, _read  # noqa: E402

from netzoo_agent_core.interpretation.closed_settings_retype import retyped  # noqa: E402
from netzoo_agent_core.interpretation.named_run import named_in_sentence  # noqa: E402
from netzoo_agent_core.interpretation.same_run import same_run_holds  # noqa: E402


def test_off_keeps_p2_holding_c34(monkeypatch):
    monkeypatch.delenv("NETZOO_NAMED_RUN_SENTENCE", raising=False)
    check = retyped(_c34(), C34, _read())[0]
    held = same_run_holds(check, C34)
    assert held is not check and not any(row.delivered_by for row in held.results())


def test_the_row_sentence_names_the_run(monkeypatch):
    monkeypatch.setenv("NETZOO_NAMED_RUN_SENTENCE", "on")
    check = retyped(_c34(), C34, _read())[0]
    assert same_run_holds(check, C34) is check  # PANDA named in "Please run PANDA ... TF-gene network."
    assert same_run_holds(check) is not check  # no request given: as before


def test_an_attached_question_names_nothing(monkeypatch):
    monkeypatch.setenv("NETZOO_NAMED_RUN_SENTENCE", "on")
    task = "Run PANDA with alpha 0.3 on these samples. Can you set it up that way?"
    assert named_in_sentence(task, ["Can you set it up that way?"]) == set()
    assert named_in_sentence(task, ["on these samples"]) == {"PANDA"}

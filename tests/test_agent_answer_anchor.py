"""agent-answer-anchor-2026-10-29: an answer to an agent question is judged only on a contract line code anchors."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.engine.task_updates import _pending  # noqa: E402
from netzoo_agent_core.graph import agent_answer_call as call  # noqa: E402
from netzoo_agent_core.graph import context as graph_context  # noqa: E402
from netzoo_agent_core.graph import jev_guard_call  # noqa: E402
from netzoo_agent_core.interpretation.answer_anchor import anchored  # noqa: E402

PPI = ("ppi_file must be a TF-TF edge list. Its identifier set must equal the TF identifier set in motif_file; the "
       "adapter symmetrizes it into P and uses a binary adjacency projection: an edge listed with a positive weight "
       "projects to 1, and one listed with weight 0 projects to 0 rather than being treated as present.")
LAMBDA = ("setting lambda1 (number; minimum 0; maximum 1): Shrinkage of omics layer 1 (DRAGON's layer-specific "
          "shrinkage, not a generic graphical-lasso or sparsity penalty).")


def test_the_anchor():
    assert anchored(PPI, ["OTTER"]) == "OTTER"  # a required input, by its identifier
    assert anchored("The expression is declared log-transformed; BONOBO requires it.", ["BONOBO"]) == "BONOBO"
    assert anchored("Require at least two expression samples before execution.", ["GIRAFFE"]) is None  # a count rule
    assert anchored(LAMBDA, ["LIONESS-DRAGON"]) is None  # j4 S15 (R01): a setting's text decides nothing
    assert anchored("ppi_file must be a list my model made up.", ["OTTER"]) is None  # not in the contract
    assert anchored(PPI, ["BONOBO"]) is None  # another workflow's line


def _core():
    return {"kind": "ASK", "facts": [{"by_code": False, "depends_on": "", "contract_quote": PPI, "workflows": ["OTTER"],
                                      "question": "Has anyone built a TF-TF table for sheep?",
                                      "user_quote": "I don't know whether anyone built a TF-TF table for sheep."}]}


def test_an_agent_question_keeps_its_contract_line():
    (question,) = _pending(_core())
    assert question.source == "agent" and question.labels == {"contract": PPI, "workflow": "OTTER"}
    assert question.yes_no and not question.options  # binding is unchanged


@pytest.fixture
def run(monkeypatch):
    events = []
    monkeypatch.setattr(graph_context, "record_event", lambda c, s, name, node, payload: events.append(payload))
    monkeypatch.setattr(jev_guard_call, "judge_answer", lambda *a: {"answer": "fails", "confidence": 0.98})
    state = {"task_state": {"turns": 1, "pending": [_pending(_core())[0].model_dump()], "facts": []},
             "messages": [{"role": "user", "content": "There is no TF-TF table for sheep."}]}

    def go(mode, core=None):
        monkeypatch.setenv("NETZOO_AGENT_ANSWERS", mode)
        return call.apply_agent_answer(None, state, core or CoreDecision(kind="DO", basis="results_given",
                                                                         workflows=["OTTER"], evidence={}), "task")
    return go, events, state


def test_off_shadow_on(run, monkeypatch):
    go, events, state = run
    monkeypatch.setattr("netzoo_agent_core.llm.latest_user_message", lambda messages: "There is no TF-TF table.")
    assert go("off").kind == "DO" and not events
    assert go("shadow").kind == "DO" and events[-1]["would_have"]["kind"] == "DECLINE"
    after = go("on")
    assert after.kind == "DECLINE" and after.basis == "jev_answer" and "OTTER's contract" in after.declined[0].line
    monkeypatch.setattr("netzoo_agent_core.llm.latest_user_message", lambda messages: (
        "Previous NetZoo goal: Run OTTER for sheep.\nUser follow-up: There is no TF-TF table."))
    line = go("on").declined[0].line
    assert line.startswith('You answered "There is no TF-TF table."') and "Previous NetZoo goal" not in line  # aa1
    ask = CoreDecision(kind="ASK", basis="fact_agent", workflows=["OTTER"], evidence={})
    assert go("on", ask) is ask  # only a DO changes
    state["task_state"]["pending"][0]["labels"]["contract"] = LAMBDA
    assert go("on").kind == "DO"  # unanchored: nothing read

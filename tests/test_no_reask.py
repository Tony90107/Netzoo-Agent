"""no-reask-2026-11-01: a fact-agent question on a doubt an agent or count answer already settled is not asked again;
a form answer, a pending question, the flag off change nothing; shadow records only."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import FactQuestion  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.graph import context as graph_context  # noqa: E402
from netzoo_agent_core.graph import fact_check_call as call  # noqa: E402
from netzoo_agent_core.interpretation.answered_doubts import answered_doubt  # noqa: E402

DOUBT = "we may end up with only two matched samples, or perhaps five."
AGAIN = FactQuestion(question="Will you have at least three matched samples?", user_quote=DOUBT, workflows=["DRAGON"],
                     contract_quote="Require at least three samples in each layer before execution.")


def _state(source="agent", what="DRAGON", value="yes", status="known", pending=False):
    fact = {"question_id": f"{source}:{what}:x", "source": source, "what": what, "question": "earlier question",
            "user_quote": DOUBT, "value": value, "answer_quote": value, "turn": 1, "status": status}
    if pending:
        return {"task_id": "t", "turns": 1, "pending": [{k: fact[k] for k in ("question_id", "source", "what",
                                                                                  "question", "user_quote")}]}
    return {"task_id": "t", "turns": 2, "facts": [fact]}


def test_which_answers_block():
    assert answered_doubt(AGAIN, _state()) is not None                                    # agent yes/no
    assert answered_doubt(AGAIN, _state(source="count", what="sample_count", value="2")) is not None
    assert answered_doubt(AGAIN, _state(source="dimension", what="group_membership", value="one_group")) is None
    assert answered_doubt(AGAIN, _state(status="superseded")) is None
    assert answered_doubt(AGAIN, _state(pending=True)) is None
    other = AGAIN.model_copy(update={"user_quote": "the values are centered per gene"})
    assert answered_doubt(other, _state()) is None


@pytest.fixture
def events(monkeypatch):
    found = []
    monkeypatch.setattr(call, "record_event", lambda c, s, name, node, payload: found.append((name, payload)))
    return found


def test_modes(events, monkeypatch):
    facts = FactCheck(status="checked", accepted=[AGAIN])
    monkeypatch.delenv("NETZOO_NO_REASK", raising=False)
    assert call._without_answered(None, {"task_state": _state()}, facts) is facts and events == []
    monkeypatch.setenv("NETZOO_NO_REASK", "shadow")
    assert call._without_answered(None, {"task_state": _state()}, facts) is facts and events[-1][0] == "core.no_reask"
    monkeypatch.setenv("NETZOO_NO_REASK", "on")
    after = call._without_answered(None, {"task_state": _state()}, facts)
    assert after.accepted == [] and after.rejected[-1].rule == "R9 answered"
    assert after.rejected[-1].proposal["answered_by"]["value"] == "yes"
    untouched = call._without_answered(None, {"task_state": _state(source="dimension", what="group_membership")}, facts)
    assert untouched is facts

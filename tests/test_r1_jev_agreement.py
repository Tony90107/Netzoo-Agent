"""r1-jev-agreement-2026-10-28: a fact-agent question rejected only by R1 is asked when Jev's ASK read picks the
sentence holding its words (j5 W40); any other rule, another sentence or a non-ASK read leaves the call."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.cli.bootstrap import load_project_policy  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.graph.jev_guard_call import agreed_fact_core  # noqa: E402

W40 = json.loads((Path(__file__).parent / "fixtures/r1_jev_agreement/j5_w40.json").read_text())
DO = CoreDecision(kind="DO", basis="results_given", workflows=["SAMBAR"])


def _decision(fact_check=None):
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.5, reason="r",
                        capability_check=CapabilityCheck.model_validate(W40["check"]),
                        fact_check=FactCheck.model_validate(fact_check or {k: v for k, v in W40["fact_check"].items()
                                                                           if k in FactCheck.model_fields}))


def test_w40_asks_the_fact_agents_own_question():
    after, action = agreed_fact_core(DO, W40["jev"], W40["task"], _decision(), load_project_policy())
    assert action == "ask" and after.kind == "ASK" and after.basis == "jev_agent"
    assert after.facts[0].question == "Does the variant matrix contain somatic calls from tumour-normal pairs?"
    assert not after.facts[0].depends_on  # a fact-agent fact: its answer goes the normal way


def test_no_ask_read_another_sentence_asked_or_another_rule_leave_the_call():
    policy = load_project_policy()
    assert agreed_fact_core(DO, {**W40["jev"], "kind": "DO"}, W40["task"], _decision(), policy)[1] == "no_sentence"
    assert agreed_fact_core(DO, W40["jev"], W40["task"], _decision(), policy,
                            asked={W40["jev"]["sentence"]})[1] == "already_asked"
    other = {k: v for k, v in W40["fact_check"].items() if k in FactCheck.model_fields}
    other["rejected"] = [{**item, "rule": "R2 contract words not in its contract"} for item in other["rejected"]]
    assert agreed_fact_core(DO, W40["jev"], W40["task"], _decision(other), policy)[1] == "no_rejected_agreement"
    ask = CoreDecision(kind="ASK", basis="fact_agent", workflows=["SAMBAR"])
    assert agreed_fact_core(ask, W40["jev"], W40["task"], _decision(), policy)[1] == "not_acting"


def test_a_jev_agent_ask_is_shown_as_its_question_and_clears_the_run():
    """jev-guard review: the basis must be registered where an ASK becomes the reply (ra1 W40 showed DO guidance)."""
    from netzoo_agent_core.interpretation.ask_facts import ask_result
    from netzoo_agent_core.interpretation.core_decision import with_core

    after, _ = agreed_fact_core(DO, W40["jev"], W40["task"], _decision(), load_project_policy())
    run = _decision().model_copy(update={"action": "run_sambar", "should_execute": True,
                                         "execution_requested": True, "matched_actions": ["run_sambar"]})
    shown = with_core(run, after)
    assert (shown.action, shown.should_execute, shown.matched_actions) == ("no_tool", False, [])
    reply = ask_result({"decision": shown.model_dump(mode="json")}, lambda content, kind: {"content": content})
    assert reply is not None and "Does the variant matrix contain somatic calls from tumour-normal pairs?" in \
        reply["content"]

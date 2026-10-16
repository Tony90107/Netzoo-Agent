"""The turns the new goal rule no longer holds, finished offline: the fact agent and the core call (model calls).

`offline_both_wrong.py` lists the recorded turns whose goal the new rule reads as clear (one named method) or
whose fact agent now has a candidate (the method the goal names). Their recorded decision had routing's picks
cleared by the hold, so they are restored from the trace (`routing.registry_match_completed`, and the action the
call read), the fact agent is called once with this checkout's candidates (the routing model, as live), R1-R6 run
in code, and `decide_core` makes the call. ASK questions are printed beside the gold deciding fact to be judged.

Usage: offline_released_facts.py OUT_TAG TAG/ITEM [TAG/ITEM ...]   -> live/OUT_TAG/released.json
"""
from __future__ import annotations
import json
import os
import sys
from plan import DOTENV, HERE, load_items, write_json

sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from dotenv import dotenv_values  # noqa: E402

for key, value in dotenv_values(DOTENV, interpolate=False).items():
    if value is not None:
        os.environ.setdefault(key, value)

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph.fact_check_call import invoke_fact_agent, without_legacy_waits  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import _facts, decide_core  # noqa: E402
from netzoo_agent_core.interpretation.fact_check import fact_candidates, kept_facts  # noqa: E402
from netzoo_agent_core.llm import build_llm, validate_router_model  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from score_core import outcome  # noqa: E402


def restored(tag, item):
    live = HERE / 'live' / tag
    sid, row = next((sid, row) for sid, row in json.loads((live / 'structure.json').read_text()).items()
                    if row['item'] == item)
    turn = live / sid / 't1'
    session = json.loads((turn / 'session.json').read_text())
    events = [json.loads(line) for line in (turn / 'events.jsonl').read_text().splitlines() if line.strip()]
    match = next(e['payload'] for e in events if e['event_type'] == 'routing.registry_match_completed')
    evidence = (row.get('core') or {}).get('evidence') or {}
    decision = TaskDecision.model_validate(session['plan']['decision']).model_copy(update={
        'core': None, 'fact_check': None, 'action': evidence.get('action') or 'no_tool',
        'matched_actions': match.get('matched_actions') or [], 'hypothesis_actions': match.get('hypothesis_actions') or []})
    task = [m['content'] for m in session['messages'] if m['role'] == 'user'][-1]
    return decision, task, evidence.get('reason_code', '')


def main(tag, wanted):
    policy = ProjectPolicyLoader(HERE.parents[2]).load()
    model = os.environ.get('NETZOO_ROUTER_MODEL', 'openai/gpt-4o-mini')
    llm = build_llm(validate_router_model(model), 0.0, max_output_tokens=1200)
    items, found = load_items(), []
    for key in wanted:
        round_tag, item_id = key.split('/')
        decision, task, reason = restored(round_tag, item_id)
        check = decision.capability_check
        actions = fact_candidates(decision, policy)
        asked, status = [], 'no_candidates'
        if actions:
            proposals, _raw, _inp, _out, error = invoke_fact_agent(llm, task, actions, policy)
            status = 'failed' if proposals is None else 'checked'
            if proposals is not None:
                facts = kept_facts(task, proposals, decision, policy, model=model)
                facts = facts.model_copy(update={'legacy': _facts(check)})
                decision = decision.model_copy(update={'fact_check': facts,
                                                       'capability_check': without_legacy_waits(check)})
                asked = [fact.question for fact in facts.accepted if not fact.settled_by_input_check]
        core = decide_core(decision, task, reason_code=reason)
        item = items[item_id]
        line = {'key': key, 'class': item['class'], 'candidates': actions, 'fact_agent': status, 'asked': asked,
                'gold_fact': item.get('deciding_fact', ''), 'kind': core.kind, 'basis': core.basis,
                'workflows': core.workflows, 'partial': core.partial,
                'outcome_if_fact_right': outcome(item, core.model_dump(), True)[0]}
        found.append(line)
        print(json.dumps(line, ensure_ascii=False))
    out = HERE / 'live' / tag
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'released.json', found)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])

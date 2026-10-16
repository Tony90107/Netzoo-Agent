"""Phase 5c offline fact agent (spec 13.5): the agent with the about/alternatives schema on the dev set (model calls).

Same conditions as phase 2 (RESULTS-P2.md, `live/f2w`): m3's English U (needs a deciding fact) and P (supported)
items that had a candidate, the routing model (gpt-4o-mini), candidates from m3's recorded decision, and R1's second
reader from the check readings recorded in f2w. Each request is asked once; R1-R7 run in code.

Gates: C1 no U item gives an open result; C2 U items asked or said a fact >= 17/24 (phase 2); C3 P items asked or
with an open result <= 1.

The control arm runs the same script from a checkout before 5c (no about/alternatives, no open_results), copied
there with `live/f2w`.

Usage: offline_5c_facts.py OUT_TAG   -> live/OUT_TAG/facts.json
"""
from __future__ import annotations
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import offline_fact_compare as base
from plan import HERE, write_json

from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.graph.fact_check_call import invoke_fact_agent  # noqa: E402
from netzoo_agent_core.interpretation.fact_check import fact_candidates, kept_facts  # noqa: E402
from netzoo_agent_core.llm import build_llm, validate_router_model  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402


def main(tag):
    policy = ProjectPolicyLoader(HERE.parents[2]).load()
    model = os.environ.get('NETZOO_ROUTER_MODEL', 'openai/gpt-4o-mini')
    llm = build_llm(validate_router_model(model), 0.0, max_output_tokens=1200)
    items = {i['id']: i for i in base.dev_items()}
    witnesses = {r['item']: r['witness'] for r in json.loads((HERE / 'live' / 'f2w' / 'witness.json').read_text())
                 if r['model'] == 'router'}

    def run(item_id):
        item, witness = items[item_id], witnesses[item_id]
        decision = base.recorded_decision(item_id)
        check = decision.capability_check or CapabilityCheck()
        if 'failed' not in witness:
            check = check.model_copy(update={'uncertain_quotes': witness['uncertain'], 'stated_quotes': witness['stated']})
        decision = decision.model_copy(update={'capability_check': check})
        actions = fact_candidates(decision, policy)
        started = time.time()
        proposals, _raw, _inp, _out, error = invoke_fact_agent(llm, item['prompt'], actions, policy)
        row = {'item': item_id, 'family': item['family'], 'candidates': actions, 'seconds': round(time.time() - started),
               'gold_fact': item['requirements'][0].get('deciding_fact') or ''}
        if proposals is None:
            return {**row, 'status': 'failed', 'error': f'{type(error).__name__}: {str(error)[:300]}'}
        kept = kept_facts(item['prompt'], proposals, decision, policy, model=model)
        return {**row, 'status': 'checked', 'proposals': [p.model_dump() for p in proposals.facts],
                'asked': [f.model_dump() for f in kept.accepted if not f.settled_by_input_check],
                'said': [f.model_dump() for f in kept.accepted if f.settled_by_input_check],
                'open_results': getattr(kept, 'open_results', []), 'rejected': [r.rule for r in kept.rejected]}

    with ThreadPoolExecutor(6) as pool:
        rows = list(pool.map(run, sorted(witnesses)))
    out = HERE / 'live' / tag
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'facts.json', rows, exclusive=False)
    U = [r for r in rows if r['family'] == 'U']
    P = [r for r in rows if r['family'] == 'P']
    print(json.dumps({
        'model': model, 'calls': len(rows), 'failed': [r['item'] for r in rows if r['status'] != 'checked'],
        'C1 U items with an open result (0)': [r['item'] for r in U if r.get('open_results')],
        'C2 U items asked or said a fact (>= 17/24)': f"{sum(bool(r.get('asked') or r.get('said')) for r in U)}/{len(U)}",
        'C3 P items asked or with an open result (<= 1)': [r['item'] for r in P if r.get('asked') or r.get('open_results')],
        'wanted_result proposals': {r['item']: [(p['user_quote'][:60], p['alternatives']) for p in r.get('proposals', [])
                                                if p.get('about') == 'wanted_result'] for r in rows
                                    if any(p.get('about') == 'wanted_result' for p in r.get('proposals', []))},
    }, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])

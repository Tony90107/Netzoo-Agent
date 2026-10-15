"""Phase 2 step 1: the fact agent alone, on dev requests, with two models (spec section 6, "模型").

Dev set: m3's English U (needs a deciding fact, 27) and P (supported, 27) items -- seen sets, never the 56-item
bench. Candidates come from m3's recorded final decision (rep 1), as the live turn would have them. Only the fact
agent is called; R1-R6 run in code (R4 has no stated quotes on these older recordings).

Usage: offline_fact_compare.py OUT_TAG   -> live/OUT_TAG/fact-compare.json
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from plan import DOTENV, HERE, write_json

sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from dotenv import dotenv_values  # noqa: E402

for key, value in dotenv_values(DOTENV, interpolate=False).items():
    if value is not None:
        os.environ.setdefault(key, value)

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph.fact_check_call import invoke_fact_agent  # noqa: E402
from netzoo_agent_core.interpretation.fact_check import fact_candidates, kept_facts  # noqa: E402
from netzoo_agent_core.llm import build_llm, validate_router_model  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

M3 = DOTENV.parent / 'docs' / 'research-log' / 'm3-clarification-2026-10-15'  # raw recordings live in the main checkout
CJK = re.compile(r'[一-鿿]')


def dev_items():
    items = json.loads((M3 / 'heldout.json').read_text())['items']
    return [i for i in items if i['family'] in ('U', 'P') and not CJK.search(i['prompt'])]


def recorded_decision(item_id):
    path = M3 / 'live' / 'm3' / f've-m3-live-{item_id}-1' / 't1' / 'session.json'
    return TaskDecision.model_validate((json.loads(path.read_text()).get('plan') or {}).get('decision'))


def main(tag):
    policy = ProjectPolicyLoader(HERE.parents[2]).load()
    models = {'router': os.environ.get('NETZOO_ROUTER_MODEL', 'openai/gpt-4o-mini'),
              'check': os.environ['OPENROUTER_CAPABILITY_MODEL']}
    llms = {'router': build_llm(validate_router_model(models['router']), 0.0, max_output_tokens=1200),
            'check': build_llm(validate_router_model(models['check']), 0.0,
                               max_output_tokens=int(os.environ.get('OPENROUTER_CAPABILITY_MAX_TOKENS', '9000')))}
    jobs = []
    for item in dev_items():
        decision = recorded_decision(item['id'])
        actions = fact_candidates(decision, policy)
        for which in ('router', 'check'):
            jobs.append((item, decision, actions, which))

    def run(job):
        item, decision, actions, which = job
        if not actions:
            return {'item': item['id'], 'model': which, 'status': 'no_candidates'}
        started = time.time()
        proposals, _raw, _inp, _out, error = invoke_fact_agent(llms[which], item['prompt'], actions, policy)
        row = {'item': item['id'], 'family': item['family'], 'model': which, 'seconds': round(time.time() - started),
               'candidates': actions, 'gold_fact': (item['requirements'][0].get('deciding_fact') or ''),
               'gold_by': item['requirements'][0].get('by')}
        if proposals is None:
            return {**row, 'status': 'failed', 'error': f'{type(error).__name__}: {str(error)[:300]}'}
        check = kept_facts(item['prompt'], proposals, decision, policy, model=models[which])
        return {**row, 'status': 'checked', 'proposed': len(proposals.facts),
                'asked': [f.model_dump() for f in check.accepted if not f.settled_by_input_check],
                'said': [f.model_dump() for f in check.accepted if f.settled_by_input_check],
                'rejected': [r.model_dump() for r in check.rejected]}

    with ThreadPoolExecutor(6) as pool:
        rows = list(pool.map(run, jobs))
    out = HERE / 'live' / tag
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'fact-compare.json', rows)
    for which in ('router', 'check'):
        mine = [r for r in rows if r['model'] == which]
        print(which, models[which],
              {'failed': sum(r['status'] == 'failed' for r in mine),
               'no_candidates': sum(r['status'] == 'no_candidates' for r in mine),
               'U_asked': sum(bool(r.get('asked')) for r in mine if r.get('family') == 'U'),
               'P_needless': sum(bool(r.get('asked')) for r in mine if r.get('family') == 'P'),
               'median_s': sorted(r.get('seconds', 0) for r in mine)[len(mine) // 2]})


if __name__ == '__main__':
    main(sys.argv[1])

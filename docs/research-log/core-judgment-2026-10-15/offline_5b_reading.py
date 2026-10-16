"""Phase 5b offline reading (spec 13.5): the capability check's own model reads dev requests with a schema (model calls).

Dev set: m3's U06 ("20 or 200 genes"), U12 ("either 100 or 1000 total features"), U14 (a setting given as "0.3 or
3.0", which must not be read as a count) and its 27 English P items (supported; no candidate count) -- seen sets, never
the 56-item bench. Each request is read once by the check's model with the schema of the checkout the script runs
from (--scripts DIR: an older checkout, the control), then `build_capability_check` verifies the reading in code.

Usage: offline_5b_reading.py OUT_TAG ARM [--scripts DIR]   -> live/OUT_TAG/reading-ARM.json
       offline_5b_reading.py gates OUT_TAG                    -> B1-B4 from reading-new.json and reading-control.json
"""
from __future__ import annotations
import json
import os
import re
import sys
import time

ARGS = sys.argv[1:]
if '--scripts' in ARGS:
    at = ARGS.index('--scripts')
    sys.path.insert(0, ARGS[at + 1])
    del ARGS[at:at + 2]

from plan import DOTENV, HERE, write_json  # noqa: E402

sys.path.insert(1 if '--scripts' in sys.argv else 0, str(HERE.parents[2] / 'scripts'))
M3 = DOTENV.parent / 'docs' / 'research-log' / 'm3-clarification-2026-10-15'
CJK = re.compile(r'[一-鿿]')
TARGETS = ('U06', 'U12', 'U14')


def dev_items():
    items = json.loads((M3 / 'heldout.json').read_text())['items']
    return [i for i in items if i['id'] in TARGETS or i['family'] == 'P' and not CJK.search(i['prompt'])]


def read_all(tag, arm):
    from concurrent.futures import ThreadPoolExecutor

    from dotenv import dotenv_values
    for key, value in dotenv_values(DOTENV, interpolate=False).items():
        if value is not None:
            os.environ.setdefault(key, value)
    from netzoo_agent_core.contracts.capability_check import proposal_model
    from netzoo_agent_core.graph.capability_check_call import build_capability_check_messages
    from netzoo_agent_core.interpretation.capability_check import build_capability_check
    from netzoo_agent_core.interpretation.semantic_repair import semantic_payload
    from netzoo_agent_core.llm import build_llm, validate_router_model

    model = os.environ['OPENROUTER_CAPABILITY_MODEL']
    cap = int(os.environ.get('OPENROUTER_CAPABILITY_MAX_TOKENS', '16000'))
    llm = build_llm(validate_router_model(model), 0.0, max_output_tokens=cap)

    def read(item):
        task = item['prompt']
        messages, count = build_capability_check_messages(task)
        schema = proposal_model(count)
        started = time.time()
        try:
            adapter = llm.with_structured_output(schema, method='function_calling', include_raw=True, strict=True)
            payload, raw = semantic_payload(adapter.invoke(messages))
            proposal = schema.model_validate(payload.model_dump() if hasattr(payload, 'model_dump') else payload)
        except Exception as error:  # a reading that does not decode: B4 counts it
            return {'item': item['id'], 'family': item['family'], 'status': 'failed',
                    'seconds': round(time.time() - started), 'error': f'{type(error).__name__}: {str(error)[:160]}'}
        check, _rejected = build_capability_check(task, proposal)
        raw_alternatives = [a.model_dump() for a in getattr(proposal.conditions, 'count_alternatives', None) or []]
        return {'item': item['id'], 'family': item['family'], 'status': 'success',
                'seconds': round(time.time() - started),
                'output_tokens': (getattr(raw, 'usage_metadata', None) or {}).get('output_tokens'),
                'raw_alternatives': raw_alternatives,
                'count_alternatives': getattr(check, 'count_alternatives', []),
                'rows': [{'quote': r.quote[:80], 'status': r.status, 'delivered_by': r.delivered_by,
                          'by_code': getattr(r, 'by_code', False), 'outcomes': r.outcomes, 'limits': r.limits,
                          'method': r.method}
                         for r in check.results()],
                'proposal': proposal.model_dump(mode='json')}  # round r5b kept none: U12's row could not be traced

    with ThreadPoolExecutor(6) as pool:
        rows = list(pool.map(read, dev_items()))
    out = HERE / 'live' / tag
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / f'reading-{arm}.json', {'model': model, 'cap': cap, 'rows': rows}, exclusive=False)
    print(arm, model, f"decoded {sum(r['status'] == 'success' for r in rows)}/{len(rows)}")


def gates(tag):
    new = {r['item']: r for r in json.loads((HERE / 'live' / tag / 'reading-new.json').read_text())['rows']}
    control = json.loads((HERE / 'live' / tag / 'reading-control.json').read_text())['rows']
    expected = {'U06': [20, 200], 'U12': [100, 1000]}
    b1 = [item for item, values in expected.items()
          if any(a['values'] == values for a in new.get(item, {}).get('count_alternatives', []))]
    b2 = [r['item'] for r in new.values() if r['family'] == 'P' and r.get('count_alternatives')]
    b3 = bool(new.get('U14', {}).get('count_alternatives'))
    failed_new = sum(r['status'] != 'success' for r in new.values())
    failed_control = sum(r['status'] != 'success' for r in control)
    print(json.dumps({
        'B1 U06/U12 read with the right candidates (>= 1)': b1,
        'B2 P items with a candidate count (0)': b2,
        'B3 U14 read as a count (False)': b3,
        'B4 decode failures new vs control (new <= control)': [failed_new, failed_control],
        'waits judged in code': {i: [row['outcomes'] for row in r.get('rows', []) if row['by_code']]
                                 for i, r in new.items() if any(row['by_code'] for row in r.get('rows', []))},
        'raw candidates the code dropped': {i: r['raw_alternatives'] for i, r in new.items()
                                            if r.get('raw_alternatives') and not r.get('count_alternatives')},
    }, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    if ARGS[0] == 'gates':
        gates(ARGS[1])
    else:
        read_all(ARGS[0], ARGS[1])

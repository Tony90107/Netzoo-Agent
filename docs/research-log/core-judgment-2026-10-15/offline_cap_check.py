"""Open item 2: does a higher output cap recover the capability check's undecodable replies? (no full sessions)

Re-reads, with the check's own model and a given cap, every request whose recorded check call failed in the bench
rounds (p0-p3 and reruns), and reports how many decode now, their output size and time.

Usage: offline_cap_check.py CAP OUT_TAG   -> live/OUT_TAG/cap-check.json
"""
from __future__ import annotations
import glob
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from plan import DOTENV, HERE, write_json

sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from dotenv import dotenv_values  # noqa: E402

for key, value in dotenv_values(DOTENV, interpolate=False).items():
    if value is not None:
        os.environ.setdefault(key, value)

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import build_capability_check_messages  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402
from netzoo_agent_core.llm import build_llm, validate_router_model  # noqa: E402

ROUNDS = ('p0', 'p1', 'p1b', 'p2', 'p2b', 'p3', 'p3b')


def failed_requests():
    for tag in ROUNDS:
        for path in sorted(glob.glob(str(HERE / 'live' / tag / 'cj-*' / 't1' / 'session.json'))):
            session = json.loads(open(path).read())
            calls = (session.get('token_usage') or {}).get('calls', [])
            if any(c.get('role') == 'capability_check' and 'nemotron' in str(c.get('model')) and c.get('status') != 'success'
                   for c in calls):
                task = [m['content'] for m in session['messages'] if m['role'] == 'user'][-1]
                yield tag, path.split('/')[-3], task


def main(cap, tag):
    model = os.environ['OPENROUTER_CAPABILITY_MODEL']
    llm = build_llm(validate_router_model(model), 0.0, max_output_tokens=int(cap))

    def read(job):
        round_tag, session, task = job
        messages, count = build_capability_check_messages(task)
        schema = proposal_model(count)
        started = time.time()
        try:
            adapter = llm.with_structured_output(schema, method='function_calling', include_raw=True, strict=True)
            payload, raw = semantic_payload(adapter.invoke(messages))
            schema.model_validate(payload.model_dump() if hasattr(payload, 'model_dump') else payload)
            usage = getattr(raw, 'usage_metadata', None) or {}
            return {'round': round_tag, 'session': session, 'status': 'success',
                    'output_tokens': usage.get('output_tokens'), 'seconds': round(time.time() - started)}
        except Exception as error:
            return {'round': round_tag, 'session': session, 'status': 'failed', 'seconds': round(time.time() - started),
                    'error': f'{type(error).__name__}: {str(error)[:160]}'}

    jobs = list(failed_requests())
    with ThreadPoolExecutor(6) as pool:
        rows = list(pool.map(read, jobs))
    out = HERE / 'live' / tag
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'cap-check.json', {'model': model, 'cap': int(cap), 'rows': rows}, exclusive=False)
    ok = [r for r in rows if r['status'] == 'success']
    print(f'cap {cap}: decoded {len(ok)}/{len(rows)}; output tokens {sorted(r["output_tokens"] or 0 for r in ok)}; '
          f'seconds median {sorted(r["seconds"] for r in rows)[len(rows) // 2] if rows else "-"}')
    print('still failing:', [(r['round'], r['session'], r.get('error', '')[:60]) for r in rows if r['status'] != 'success'])


if __name__ == '__main__':
    main(*sys.argv[1:3])

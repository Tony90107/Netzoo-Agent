"""Harness repair P1/P2 live check (2026-10-23, user-approved): 18 affected items, one session each, on the clean run
worktree `.worktrees/netzoo-harness-live` at 4739549b; never reruns a job.

Adapted from heldout-h6-2026-10-22/run_h6.py (the h4 `run_job`, the model and price checks, the actual-cost guard):
the worktree, the commit, one rep, tag p12live, and the user's cap of US$0.20 -- provider-reported cost summed after
each session, and no session starts once it is reached.

Usage: python3 run_live.py
"""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[3]
RUN = CHECKOUT.parent / 'netzoo-harness-live'
DOTENV = CHECKOUT.parents[1] / 'netzoo_agent/.env'
HARNESS = CHECKOUT / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
FROZEN = '4739549b'
CAP_USD = 0.20
TAG = 'p12live'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RUN, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=RUN, text=True).strip()
    files = subprocess.check_output(['git', 'ls-files', '-z', '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                                    cwd=RUN).decode().split('\0')
    return {'head': head, 'dirty': dirty, 'files': {n: sha(RUN / n) for n in files if n and (RUN / n).is_file()}}


def spent():
    """Provider-reported US$ over every session of this check so far."""
    total = 0
    for session in HERE.glob('live/*/*/t*/session.json'):
        calls = (json.loads(session.read_text()).get('token_usage') or {}).get('calls', [])
        total += sum(c.get('cost_micro_usd') or 0 for c in calls)
    return total / 1e6


def main():
    record = HERE / f'round-{TAG}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    items = json.loads((HERE / 'items.json').read_text())['items']
    if len(items) != 18 or len({x['id'] for x in items}) != 18:
        raise ValueError('Expected 18 unique items')
    sys.path.insert(0, str(HARNESS.parent))
    spec = importlib.util.spec_from_file_location('existing_h4_live', HARNESS)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    env = live.environment(DOTENV)
    config = {k: env.get(k, d) for k, d in {
        'OPENROUTER_MODEL': 'openai/gpt-4o-mini', 'OPENROUTER_ROUTER_MODEL': 'openai/gpt-4o-mini',
        'OPENROUTER_SEMANTIC_MODEL': 'openai/gpt-4o-mini', 'OPENROUTER_CAPABILITY_MODEL': ''}.items()}
    if set(config.values()) - MODELS or config['OPENROUTER_CAPABILITY_MODEL'] != 'openai/gpt-4o-mini-2024-07-18' \
            or not env.get('OPENROUTER_API_KEY'):
        raise RuntimeError('Unexpected model configuration or missing credential')
    with urllib.request.urlopen('https://openrouter.ai/api/v1/models', timeout=20) as response:
        prices = {m['id']: m['pricing'] for m in json.load(response)['data'] if m['id'] in MODELS}
    if set(prices) != MODELS:
        raise RuntimeError('Could not verify model rates')
    stamp = datetime.now(timezone.utc).isoformat()
    pricing = {model: {'input_micro_usd_per_million': round(float(p['prompt']) * 1e12),
                       'output_micro_usd_per_million': round(float(p['completion']) * 1e12),
                       'effective_at': stamp} for model, p in prices.items()}
    env.update({'NETZOO_MAX_TASK_TOKENS': '30000', 'OPENROUTER_CAPABILITY_EXTRA_TOKENS': '30000',
                'NETZOO_MODEL_PRICING_JSON': json.dumps(pricing), 'PYTHONUNBUFFERED': '1'})
    frozen = fingerprint()
    if not frozen['head'].startswith(FROZEN) or frozen['dirty']:
        raise RuntimeError(f'Run worktree is not the frozen clean {FROZEN}')
    write(record, {'started_utc': stamp, 'tag': TAG, 'code': frozen, 'items_sha256': sha(HERE / 'items.json'),
                   'harness_sha256': sha(HARNESS), 'config': config, 'provider_prices': prices,
                   'price_catalog': pricing, 'sessions': len(items), 'max_workers': 2, 'cap_usd': CAP_USD,
                   'spent_before_usd': spent()})
    output = HERE / 'live' / TAG
    output.mkdir(parents=True, exist_ok=False)
    results, stopped = [], None

    def job(item):
        if fingerprint() != frozen:
            raise RuntimeError('Runtime code changed')
        found = live.run_job(TAG, item['id'], 1, item, RUN, output, {**env, 'NETZOO_PROFILE': live.session_id(
            TAG, item['id'], 1)}, 600)
        if fingerprint() != frozen:
            raise RuntimeError('Runtime code changed during live job')
        return found

    queue = list(items)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = {}
        while queue or running:
            while queue and len(running) < 2 and stopped is None:
                if (total := spent()) >= CAP_USD:
                    stopped = f'cost cap reached: US${total:.4f}'
                    break
                item = queue.pop(0)
                running[pool.submit(job, item)] = item['id']
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                key = running.pop(future)
                try:
                    sid, codes = future.result()
                    row = {'id': key, 'session': sid, 'codes': codes}
                except Exception as exc:
                    row = {'id': key, 'error_type': type(exc).__name__, 'error': str(exc)}
                row['spent_usd'] = round(spent(), 4)
                results.append(row)
                write(HERE / f'jobs-{TAG}.json', results)
                print(json.dumps(row), flush=True)
    write(HERE / f'finished-{TAG}.json', {'finished_utc': datetime.now(timezone.utc).isoformat(),
          'runtime_code_unchanged': fingerprint() == frozen, 'sessions': len(results), 'not_started': len(queue),
          'stopped': stopped, 'spent_usd': round(spent(), 4)})


if __name__ == '__main__':
    main()

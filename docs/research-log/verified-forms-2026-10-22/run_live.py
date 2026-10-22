"""Live check of 81912052 (an ask's overlap / dynamics / neighbours form rules out only with the request's verified
words): the 3 h-set items it changes offline, 3 grouping DO items, and 12 seen trap items (heldout1-10, family N) that
ask for those forms and must stay refused; one session each per arm, on frozen clean run worktrees.

Usage: python3 run_live.py          the new code 81912052 (tag vqnew)
       python3 run_live.py base     the frozen code 91a8c2d9 on the same items, same day (tag vqbase)

Adapted from heldout-h5-2026-10-21/run_h5.py (same h4 `run_job`, model and price checks, actual-cost guard).
Same runner as not-stated-fields-2026-10-22/run_live.py; items from h-sets and capability-traps heldout sets.
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
LOGS = HERE.parent
CHECKOUT = HERE.parents[2]
ARMS = {'new': ('netzoo-vq-run', '81912052', 'vqnew'), 'base': ('netzoo-frozen-91a8', '91a8c2d9', 'vqbase')}
ARM = ARMS['base' if sys.argv[1:] == ['base'] else 'new']
RUN = CHECKOUT.parent / ARM[0]
DOTENV = CHECKOUT.parents[1] / 'netzoo_agent/.env'
HARNESS = LOGS / 'closed-menu-hybrid-2026-10-19/h4/run_live.py'
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
FROZEN = ARM[1]
CAP_USD = 0.40  # both arms together (spent() sums every live session here)
TAG = ARM[2]
SETS = {'h2': 'closed-menu-options-first-2026-10-18/h2/items.json',
        'h3': 'closed-menu-slim-2026-10-19/h3/items.json',
        'h4': 'closed-menu-hybrid-2026-10-19/h4/items.json',
        'h5': 'heldout-h5-2026-10-21/items.json'}
TRAPS = 'capability-traps-2026-10-08/heldout{}.json'
# Picked before running: every h-set call the change moves offline (Q26, J22, M45), three grouping DO items, and the
# trap items asking for overlapping groups (SN1, JN8, ON5, QN5), dynamics (SN5, NN7, HN2, QN8, RN1) or spatial
# neighbours (SN6, QN10, SN8) -- all gold "not available" (family N).
ITEMS = {'h5': ['Q26'], 'h2': ['J22'], 'h4': ['M45', 'M19'], 'h3': ['L30', 'L35']}
TRAP_ITEMS = {'10': ['SN1', 'SN5', 'SN6', 'SN8'], '2': ['JN8'], '7': ['ON5'], '8': ['QN5', 'QN8', 'QN10'],
              '6': ['NN7'], '1': ['HN2'], '9': ['RN1']}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RUN, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=RUN, text=True).strip()
    files = subprocess.check_output(['git', 'ls-files', '-z', '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                                    cwd=RUN).decode().split('\0')
    return {'head': head, 'dirty': dirty, 'files': {n: sha(RUN / n) for n in files if n and (RUN / n).is_file()}}


def items():
    picked = []
    for name, ids in ITEMS.items():
        found = {x['id']: x for x in json.loads((LOGS / SETS[name]).read_text())['items']}
        picked += [{**found[i], 'set': name} for i in ids]
    for number, ids in TRAP_ITEMS.items():
        found = {x['id']: x for x in json.loads((LOGS / TRAPS.format(number)).read_text())['items']}
        picked += [{'id': i, 'prompt': found[i]['prompt'], 'class': 'dont', 'workflows': [], 'set': f'heldout{number}',
                    'core': found[i]['core']} for i in ids]
    if len(picked) != 18 or len({x['id'] for x in picked}) != 18:
        raise ValueError(f'Expected 18 unique items, got {len(picked)}')
    return picked


def spent():
    total = 0
    for session in HERE.glob('live/*/*/t*/session.json'):
        calls = (json.loads(session.read_text()).get('token_usage') or {}).get('calls', [])
        total += sum(c.get('cost_micro_usd') or 0 for c in calls)
    return total / 1e6


def main():
    record = HERE / f'round-{TAG}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    raw = items()
    spec = importlib.util.spec_from_file_location('existing_h4_live', HARNESS)
    live = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HARNESS.parent))
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
    write(record, {'started_utc': stamp, 'tag': TAG, 'code': {'head': frozen['head']}, 'items': ITEMS,
                   'config': config, 'provider_prices': prices, 'cap_usd': CAP_USD, 'spent_before_usd': spent()})
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

    queue = list(raw)
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

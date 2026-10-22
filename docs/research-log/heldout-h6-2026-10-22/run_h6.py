"""Held-out round h6 (ROUND.md): the frozen run worktree's live CLI, one session per (item, rep); never reruns a job.

Usage: python3 run_h6.py smoke    one item per class, rep 1 (tag h6smoke; not scored)
       python3 run_h6.py main     every item, reps 1 and 2 (tag h6main)

Adapted from input-constraints-2026-10-21/live-check/run_live.py (the same h4 `run_job`, model and price checks).
Changes: the frozen worktree `.worktrees/netzoo-h6-final` (91a8c2d9; ROUND.md, final run) instead of this checkout; two reps; and the user-approved
actual-cost guard -- provider-reported cost summed over every session of this round (smoke and main) after each one,
and no session starts once it reaches US$1.00 -- in place of the conservative token envelope.
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
CHECKOUT = HERE.parents[2]
RUN = CHECKOUT.parent / 'netzoo-h6-final'
DOTENV = CHECKOUT.parents[1] / 'netzoo_agent/.env'
HARNESS = CHECKOUT / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
FROZEN = '91a8c2d9'
CAP_USD = 0.60
CLASSES = ('do', 'dont', 'ask', 'vague')
WORKFLOWS = {'PANDA', 'PUMA', 'LIONESS-PANDA', 'LIONESS-PUMA', 'LIONESS-COEXPRESSION', 'LIONESS-DRAGON', 'DRAGON',
             'BONOBO', 'CONDOR', 'COBRA', 'OTTER', 'GIRAFFE', 'SAMBAR'}


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


def items():
    raw = json.loads((HERE / 'items.json').read_text())['items']
    if len(raw) != 48 or len({x['id'] for x in raw}) != 48:
        raise ValueError('Expected 48 unique items')
    for x in raw:
        if x['class'] not in CLASSES or x['form'] not in ('named', 'goal', 'run') or not x['prompt'].strip():
            raise ValueError(f"Bad item {x['id']}")
        if {w.upper() for w in x['workflows']} - WORKFLOWS:
            raise ValueError(f"Unknown workflow in {x['id']}")
    return raw


def spent():
    """Provider-reported US$ over every session of this round so far (smoke and main)."""
    total = 0
    for session in HERE.glob('live/*/*/t*/session.json'):
        calls = (json.loads(session.read_text()).get('token_usage') or {}).get('calls', [])
        total += sum(c.get('cost_micro_usd') or 0 for c in calls)
    return total / 1e6


def main(mode: str):
    tag = {'smoke': 'h6smoke', 'main': 'h6main'}[mode]
    record = HERE / f'round-{tag}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    raw = items()
    jobs = ([(next(x for x in raw if x['class'] == c), 1) for c in CLASSES] if mode == 'smoke'
            else [(x, rep) for rep in (1, 2) for x in raw])
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
    write(record, {'started_utc': stamp, 'tag': tag, 'code': frozen, 'items_sha256': sha(HERE / 'items.json'),
                   'harness_sha256': sha(HARNESS), 'config': config, 'provider_prices': prices,
                   'price_catalog': pricing, 'sessions': len(jobs), 'max_workers': 2, 'cap_usd': CAP_USD,
                   'spent_before_usd': spent()})
    output = HERE / 'live' / tag
    output.mkdir(parents=True, exist_ok=False)
    results, stopped = [], None

    def job(item, rep):
        if fingerprint() != frozen:
            raise RuntimeError('Runtime code changed')
        sid = live.session_id(tag, item['id'], rep)
        found = live.run_job(tag, item['id'], rep, item, RUN, output, {**env, 'NETZOO_PROFILE': sid}, 600)
        if fingerprint() != frozen:
            raise RuntimeError('Runtime code changed during live job')
        return found

    queue = list(jobs)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = {}
        while queue or running:
            while queue and len(running) < 2 and stopped is None:
                if (total := spent()) >= CAP_USD:
                    stopped = f'cost cap reached: US${total:.4f}'
                    break
                item, rep = queue.pop(0)
                running[pool.submit(job, item, rep)] = (item['id'], rep)
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                key, rep = running.pop(future)
                try:
                    sid, codes = future.result()
                    row = {'id': key, 'rep': rep, 'session': sid, 'codes': codes}
                except Exception as exc:
                    row = {'id': key, 'rep': rep, 'error_type': type(exc).__name__, 'error': str(exc)}
                row['spent_usd'] = round(spent(), 4)
                results.append(row)
                write(HERE / f'jobs-{tag}.json', results)
                print(json.dumps(row), flush=True)
    write(HERE / f'finished-{tag}.json', {'finished_utc': datetime.now(timezone.utc).isoformat(),
          'runtime_code_unchanged': fingerprint() == frozen, 'sessions': len(results), 'not_started': len(queue),
          'stopped': stopped, 'spent_usd': round(spent(), 4)})


if __name__ == '__main__':
    main(sys.argv[1])

"""Harness repair P3 live fix (a) rerun (2026-10-23, user-approved): S11 and S12 of items-p3.json again, one each, on
`.worktrees/netzoo-harness-live` at 1dda3692 with fix (a) applied uncommitted; never reruns a job.

Copied from run_live_p3.py. The changes:
- the run worktree must differ from 1dda3692 in exactly the PATCHED files, each byte-identical to this checkout's copy
  (the fix is not committed);
- a turn that counts a round without a graph turn does not save the session's usage, so each turn also copies the
  trace runs this session started, and the cost guard counts their calls too (each call once, by its id);
- cap US$0.05.

Usage: python3 run_live_p3a.py
"""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[3]
RUN = CHECKOUT.parent / 'netzoo-harness-live'
DOTENV = CHECKOUT.parents[1] / 'netzoo_agent/.env'
HARNESS = CHECKOUT / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
FROZEN = '1dda3692'
CAP_USD = 0.05
TAG = 'p3a'
ITEMS = HERE / 'items-p3a.json'
PATCHED = ['scripts/netzoo_agent_core/engine/machine.py', 'scripts/netzoo_agent_core/engine/task_updates.py',
           'scripts/netzoo_agent_core/session.py']


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


def patched_ok():
    """The run worktree differs from its commit in exactly PATCHED, each identical to this checkout's file."""
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=RUN, text=True).splitlines()
    return sorted(line[3:] for line in dirty) == sorted(PATCHED) and all(
        sha(RUN / name) == sha(CHECKOUT / name) for name in PATCHED)


def spent():
    """Provider-reported US$ over this check's calls so far, each call once: the saved sessions' usage and the copied
    trace runs' (a round counted without a graph turn saves no usage)."""
    calls = {}
    usages = [(json.loads(p.read_text()).get('token_usage') or {}) for p in HERE.glob(f'live/{TAG}/*/t*/session.json')]
    for trace in HERE.glob(f'live/{TAG}/*/t*/trace-*.jsonl'):
        usages += [(json.loads(line).get('payload') or {}).get('token_usage') or {}
                   for line in trace.read_text().splitlines() if '"run.finished"' in line]
    for usage in usages:
        for call in usage.get('calls', []):
            calls[call.get('call_id') or id(call)] = call.get('cost_micro_usd') or 0
    return sum(calls.values()) / 1e6


def session_traces(sid: str) -> dict[str, Path]:
    """The trace runs a session started in the run worktree, by run id."""
    found = {}
    for events in (RUN / '.netzoo' / 'traces').glob('*/events.jsonl'):
        with events.open() as handle:
            first = json.loads(handle.readline() or '{}')
        if first.get('event_type') == 'run.started' and (first.get('payload') or {}).get('session_id') == sid:
            found[events.parent.name] = events
    return found


def core_kind(session: Path):
    plan = json.loads(session.read_text()).get('plan') or {}
    return ((plan.get('decision') or {}).get('core') or {}).get('kind')


def main():
    record = HERE / f'round-{TAG}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    items = json.loads(ITEMS.read_text())['items']
    if [x['id'] for x in items] != ['S11-C12', 'S12-H13'] or sum(len(x['turns']) for x in items) != 6:
        raise ValueError('Expected S11 and S12, 6 turns')
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
    if not frozen['head'].startswith(FROZEN) or not patched_ok():
        raise RuntimeError(f'Run worktree is not {FROZEN} with exactly the patched files')
    write(record, {'started_utc': stamp, 'tag': TAG, 'code': frozen, 'items_sha256': sha(ITEMS),
                   'runner_sha256': sha(__file__), 'harness_sha256': sha(HARNESS), 'config': config,
                   'provider_prices': prices, 'price_catalog': pricing, 'sessions': len(items), 'max_workers': 2,
                   'cap_usd': CAP_USD, 'patched': {name: sha(RUN / name) for name in PATCHED}})
    output = HERE / 'live' / TAG
    output.mkdir(parents=True, exist_ok=False)
    stopped = None

    def job(item):
        nonlocal stopped
        if fingerprint() != frozen:
            raise RuntimeError('Runtime code changed')
        sid = live.session_id(TAG, item['id'], 1)
        folder = output / sid
        folder.mkdir()
        source = RUN / '.netzoo' / 'sessions' / f'{sid}.json'
        if source.exists():
            raise ValueError(f'Session already exists: {sid}')
        job_env = {**env, 'NETZOO_PROFILE': sid}
        copied = set()
        codes, end = [], 'complete'
        for n, task in enumerate(item['turns'], 1):
            if (total := spent()) >= CAP_USD:
                stopped, end = f'cost cap reached: US${total:.4f}', 'cap'
                break
            turn = folder / f't{n}'
            turn.mkdir()
            args = ['--session' if n == 1 else '--resume', sid, '--keep-session', '--task', task]
            started = time.time()
            with (turn / 'stdout.txt').open('xb') as out, (turn / 'stderr.txt').open('xb') as err:
                try:
                    code = subprocess.call([live.PYTHON, '-c', live.BOOTSTRAP, *args], cwd=RUN,
                                           env={**job_env, 'CJ_CARD_CAPTURE': str(turn / 'cards.json')},
                                           stdin=subprocess.DEVNULL, stdout=out, stderr=err, timeout=600)
                except subprocess.TimeoutExpired:
                    code = 'timeout'
            if source.exists():
                shutil.copyfile(source, turn / 'session.json')
                run_id = json.loads(source.read_text()).get('run_id')
                trace = RUN / '.netzoo' / 'traces' / str(run_id) / 'events.jsonl'
                if run_id and trace.exists():
                    shutil.copyfile(trace, turn / 'events.jsonl')
            for run_id, events in session_traces(sid).items():  # every run this session started, once
                if run_id not in copied:
                    copied.add(run_id)
                    shutil.copyfile(events, turn / f'trace-{run_id}.jsonl')
            write(turn / 'manifest.json', {'turn': n, 'mode': args[0], 'request': task, 'exit': code,
                                           'started': started, 'finished': time.time()})
            codes.append(code)
            if code != 0:
                end = 'failed'
                break
            if n == 1 and len(item['turns']) > 1 and (turn / 'session.json').exists() \
                    and core_kind(turn / 'session.json') not in ('ASK', 'CLARIFY'):
                end = 'not_exercised'
                break
        if fingerprint() != frozen:
            raise RuntimeError('Runtime code changed during live job')
        write(folder / 'job.json', {'item': item['id'], 'session': sid, 'expected_turns': len(item['turns']),
                                    'codes': codes, 'end': end})
        return sid, codes, end

    results, queue = [], list(items)
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
                    sid, codes, end = future.result()
                    row = {'id': key, 'session': sid, 'codes': codes, 'end': end}
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

"""P2 (ROUND-H9.md, user-approved 2026-10-25): the 24 sealed h9 items on the frozen system, one single-turn session
each, plus one closed-menu read each. No decision is changed; the signals are computed offline (`score_h9.py`).

- System: a clean detached worktree at `041f0ee9` (`.worktrees/netzoo-h9-run`): no diff, nothing untracked. Every
  tracked file of scripts/, workflows/, prompts/ and AGENTS.md is hashed before the round and re-checked before and
  after every job; any change stops the round.
- Sessions: the CLI call, trace copying and job records of `harness-repair/a1c/run_a1c.py`.
- Menu reads: the frozen code's `read_menu` then `read_focused` (closed-menu phase 1's focused arm), decided by
  `decide_menu`, imported from the clean worktree.
- Cost: a job starts only when spent + the reserve of the jobs running + its own reserve stays within US$0.20
  (sessions US$0.015, menu reads US$0.005). Spent is the provider's reported cost over every round of this file.

Usage: python3 run_h9.py smoke    one K1 session to check the setup; not scored; counts toward the cap
       python3 run_h9.py main     the 24 sessions; never reruns
       python3 run_h9.py menu     the 24 menu reads; never reruns
"""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import threading
import time
import urllib.request

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
WORKTREES = CHECKOUT.parent
DOTENV = WORKTREES.parent / 'netzoo_agent/.env'
HARNESS = CHECKOUT / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
ITEMS = HERE / 'h9' / 'items.json'
SEALED = HERE / 'h9' / 'SEALED.json'
RUN, COMMIT = WORKTREES / 'netzoo-h9-run', '041f0ee98af9b6a50d7e644ff9140519a6daf9d7'
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
MENU_MODEL = 'openai/gpt-4o-mini'
CAP_USD = 0.20
RESERVE = {'session': 0.015, 'menu': 0.005}
SESSION_TAGS = ('h9smoke', 'h9')
MENU_LEDGER = HERE / 'menu-h9.json'
SEED = 1025


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint() -> dict:
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RUN, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=RUN, text=True).strip()
    files = subprocess.check_output(['git', 'ls-files', '-z', '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                                    cwd=RUN).decode().split('\0')
    return {'head': head, 'dirty': dirty, 'files': {n: sha(RUN / n) for n in files if n and (RUN / n).is_file()}}


def summary(found: dict) -> dict:
    return {'head': found['head'], 'dirty': found['dirty'],
            'files_sha256': hashlib.sha256(json.dumps(found['files'], sort_keys=True).encode()).hexdigest(),
            'files': len(found['files'])}


def spent() -> float:
    """Provider-reported US$ over every session and menu read of this round, each call once."""
    calls, usages = {}, []
    for tag in SESSION_TAGS:
        usages += [json.loads(p.read_text()).get('token_usage') or {} for p in HERE.glob(f'live/{tag}/*/t*/session.json')]
        for trace in HERE.glob(f'live/{tag}/*/t*/trace-*.jsonl'):
            usages += [(json.loads(line).get('payload') or {}).get('token_usage') or {}
                       for line in trace.read_text().splitlines() if '"run.finished"' in line]
    for usage in usages:
        for call in usage.get('calls', []):
            calls[call.get('call_id') or id(call)] = call.get('cost_micro_usd') or 0
    menu = json.loads(MENU_LEDGER.read_text())['rows'] if MENU_LEDGER.exists() else []
    return sum(calls.values()) / 1e6 + sum(row.get('usd', 0) for row in menu)


def check_sealed():
    sealed = json.loads(SEALED.read_text())
    if sealed['sha256']['items.json'] != sha(ITEMS):
        raise RuntimeError('items.json differs from the sealed hash')
    return sealed['sha256']['items.json']


def check_models(env: dict) -> tuple[dict, dict, dict]:
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
    return config, prices, pricing


def start_round(tag: str, frozen: dict, extra: dict) -> None:
    head = frozen['head']
    changed = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=RUN, text=True).strip()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=RUN, text=True)
    if head != COMMIT or changed or untracked.strip() or frozen['dirty']:
        raise RuntimeError(f'{RUN.name} is not a clean checkout of {COMMIT[:8]}')
    record = HERE / f'round-{tag}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    write(record, {'started_utc': datetime.now(timezone.utc).isoformat(), 'tag': tag, 'code': summary(frozen),
                   'items_sha256': check_sealed(), 'runner_sha256': sha(__file__), 'harness_sha256': sha(HARNESS),
                   'cap_usd': CAP_USD, 'reserve_usd': RESERVE, 'spent_before_usd': round(spent(), 6), **extra})


class Guard:
    """Starts a job only when what is spent, what the running jobs may still spend and the job's own reserve stay
    within the cap."""

    def __init__(self, kind: str):
        self.kind, self.lock, self.running, self.stopped = kind, threading.Lock(), 0, None

    def admit(self) -> bool:
        with self.lock:
            total = spent() + (self.running + 1) * RESERVE[self.kind]
            if total > CAP_USD:
                self.stopped = f'cap: spent US${spent():.4f} + reserve for {self.running + 1} job(s) > US${CAP_USD}'
                return False
            self.running += 1
            return True

    def release(self):
        with self.lock:
            self.running -= 1


def load_live():
    sys.path.insert(0, str(HARNESS.parent))
    spec = importlib.util.spec_from_file_location('existing_h4_live', HARNESS)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    return live


def session_traces(sid: str) -> dict[str, Path]:
    found = {}
    for events in (RUN / '.netzoo' / 'traces').glob('*/events.jsonl'):
        with events.open() as handle:
            first = json.loads(handle.readline() or '{}')
        if first.get('event_type') == 'run.started' and (first.get('payload') or {}).get('session_id') == sid:
            found[events.parent.name] = events
    return found


def session_job(item: dict, tag: str, env: dict, live, frozen: dict) -> dict:
    if fingerprint() != frozen:
        raise RuntimeError('code changed')
    sid = live.session_id(tag, item['id'], 1)
    folder = HERE / 'live' / tag / sid
    folder.mkdir()
    if (RUN / '.netzoo' / 'sessions' / f'{sid}.json').exists():
        raise ValueError(f'Session already exists: {sid}')
    turn = folder / 't1'
    turn.mkdir()
    started = time.time()
    with (turn / 'stdout.txt').open('xb') as out, (turn / 'stderr.txt').open('xb') as err:
        try:
            code = subprocess.call([live.PYTHON, '-c', live.BOOTSTRAP, '--session', sid, '--keep-session', '--task',
                                    item['prompt']], cwd=RUN,
                                   env={**env, 'NETZOO_PROFILE': sid, 'CJ_CARD_CAPTURE': str(turn / 'cards.json')},
                                   stdin=subprocess.DEVNULL, stdout=out, stderr=err, timeout=600)
        except subprocess.TimeoutExpired:
            code = 'timeout'
    source = RUN / '.netzoo' / 'sessions' / f'{sid}.json'
    if source.exists():
        shutil.copyfile(source, turn / 'session.json')
    for run_id, events in session_traces(sid).items():
        shutil.copyfile(events, turn / f'trace-{run_id}.jsonl')
    write(turn / 'manifest.json', {'turn': 1, 'mode': '--session', 'exit': code, 'started': started,
                                   'finished': time.time()})
    if fingerprint() != frozen:
        raise RuntimeError('code changed during the job')
    record = {'item': item['id'], 'session': sid, 'codes': [code], 'end': 'complete' if code in (0, 2) else 'failed'}
    write(folder / 'job.json', record)
    return record


def sessions(mode: str, items: list[dict]):
    live = load_live()
    env = live.environment(DOTENV)
    config, prices, pricing = check_models(env)
    env.update({'NETZOO_MAX_TASK_TOKENS': '30000', 'OPENROUTER_CAPABILITY_EXTRA_TOKENS': '30000',
                'NETZOO_MODEL_PRICING_JSON': json.dumps(pricing), 'PYTHONUNBUFFERED': '1'})
    if mode == 'smoke':
        tag, workers = 'h9smoke', 1
        todo = [sorted(i['id'] for i in items if i['category'] == 'K1')[0]]
    else:
        tag, workers = 'h9', 3
        todo = [i['id'] for i in items]
        if len(todo) != 24:
            raise ValueError('Expected 24 items')
    frozen = fingerprint()
    start_round(tag, frozen, {'config': config, 'provider_prices': prices, 'price_catalog': pricing})
    (HERE / 'live' / tag).mkdir(parents=True, exist_ok=False)
    random.Random(SEED).shuffle(todo)
    by_id = {item['id']: item for item in items}
    guard, results, queue = Guard('session'), [], list(todo)

    def run(key):
        try:
            return session_job(by_id[key], tag, env, live, frozen)
        finally:
            guard.release()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        running = {}
        while queue or running:
            while queue and len(running) < workers and guard.stopped is None and guard.admit():
                key = queue.pop(0)
                running[pool.submit(run, key)] = key
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                key = running.pop(future)
                try:
                    row = future.result()
                except Exception as exc:  # noqa: BLE001 -- recorded, never hidden
                    row = {'item': key, 'error_type': type(exc).__name__, 'error': str(exc)[:300]}
                    guard.stopped = guard.stopped or f'job error on {key}'
                row['spent_usd'] = round(spent(), 4)
                results.append(row)
                write(HERE / f'jobs-{tag}.json', results)
                print(json.dumps(row), flush=True)
    write(HERE / f'finished-{tag}.json', {
        'finished_utc': datetime.now(timezone.utc).isoformat(), 'runtime_code_unchanged': fingerprint() == frozen,
        'sessions': len(results), 'not_started': queue, 'stopped': guard.stopped, 'spent_usd': round(spent(), 4)})


def menu(items: list[dict]):
    from dotenv import dotenv_values

    frozen = fingerprint()
    start_round('h9menu', frozen, {'model': MENU_MODEL})
    os.chdir(RUN)  # as a session runs: the clean worktree is the working directory
    sys.path.insert(0, str(RUN / 'scripts'))
    for key, value in dotenv_values(DOTENV, interpolate=False).items():
        if value is not None:
            os.environ.setdefault(key, value)
    import netzoo_agent_core
    if Path(netzoo_agent_core.__file__).resolve().parents[2] != RUN.resolve():
        raise RuntimeError('the menu reader must be the clean worktree\'s code')
    from netzoo_agent_core.graph.menu_reading_call import read_focused, read_menu
    from netzoo_agent_core.interpretation.menu_decision import decide_menu
    from netzoo_agent_core.interpretation.menu_reader import READER_SHAPE
    from netzoo_agent_core.llm import build_llm, extract_provider_usage, validate_router_model

    llm = build_llm(validate_router_model(MENU_MODEL), 0.0, max_output_tokens=8000, timeout_seconds=150)

    def usd(raw) -> float:
        found = extract_provider_usage(raw) if raw is not None else None
        if not found:
            return 0.0
        if found.get('cost_micro_usd') is not None:
            return found['cost_micro_usd'] / 1e6
        return (found['input_tokens'] * 0.15 + found['output_tokens'] * 0.60) / 1e6

    def decided(reading, prompt) -> dict:
        decision = decide_menu(reading, prompt)
        return {'kind': decision.kind, 'basis': decision.basis, 'workflows': decision.workflows,
                'partial': decision.partial, 'questions': [q.dimension for q in decision.questions]}

    todo = [i['id'] for i in items]
    random.Random(SEED).shuffle(todo)
    by_id = {item['id']: item for item in items}
    ledger, guard = {'shape': READER_SHAPE, 'model': MENU_MODEL, 'rows': []}, Guard('menu')
    write(MENU_LEDGER, ledger)
    lock = threading.Lock()

    def one(key):
        try:
            if fingerprint() != frozen:
                raise RuntimeError('code changed')
            prompt = by_id[key]['prompt']
            first = read_menu(prompt, llm)
            row = {'id': key, 'status': first.reading.status, 'error': first.error, 'usd': usd(first.raw),
                   'first': decided(first.reading, prompt)}
            latest = first.reading
            focused, candidates = read_focused(prompt, first.reading, llm)
            row['focus'] = {'candidates': list(candidates), 'ran': focused is not None}
            if focused is not None:
                row['usd'] += usd(focused.raw)
                row['focus']['status'] = focused.reading.status
                latest = focused.reading
            row['final'] = decided(latest, prompt)
            row['reading'] = latest.model_dump(mode='json', exclude_defaults=True)
            row['usd'] = round(row['usd'], 6)
            return row
        except Exception as exc:  # noqa: BLE001 -- recorded, never hidden
            return {'id': key, 'error_type': type(exc).__name__, 'error': str(exc)[:300], 'usd': 0.0}
        finally:
            guard.release()

    with ThreadPoolExecutor(max_workers=3) as pool:
        running, queue = {}, list(todo)
        while queue or running:
            while queue and len(running) < 3 and guard.stopped is None and guard.admit():
                key = queue.pop(0)
                running[pool.submit(one, key)] = key
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                running.pop(future)
                row = future.result()
                with lock:
                    ledger['rows'].append(row)
                    write(MENU_LEDGER, ledger)
                print(json.dumps({k: row.get(k) for k in ('id', 'status', 'usd', 'error_type')}
                                 | {'kind': (row.get('final') or {}).get('kind')}), flush=True)
    write(HERE / 'finished-h9menu.json', {
        'finished_utc': datetime.now(timezone.utc).isoformat(), 'runtime_code_unchanged': fingerprint() == frozen,
        'reads': len(ledger['rows']), 'not_started': queue, 'stopped': guard.stopped, 'spent_usd': round(spent(), 4)})


def main(mode: str):
    check_sealed()
    items = json.loads(ITEMS.read_text())['single']
    if mode in ('smoke', 'main'):
        sessions(mode, items)
    elif mode == 'menu':
        menu(items)
    else:
        raise ValueError(mode)


if __name__ == '__main__':
    main(sys.argv[1])

"""A1' confirmation (ROUND-A1C.md, user-approved 2026-10-24): the 24 fresh h8 items on E3, one single-turn session each.

- E3 = a detached worktree at harness-repair `8c1ed515` plus the uncommitted B, A3 and A1' code, copied as files (no
  commit, as ROUND-A1C says). The runner checks the worktree's HEAD, that exactly those four files differ from it, and
  that each matches the harness-repair checkout byte for byte; every file's hash is recorded and re-checked per job.
- Copied from p5/run_p5r2.py (the same CLI call, trace copying and cost guard) with single-turn jobs only; the cost
  guard counts this confirmation's calls only (a1csmoke, a1c, a1c2) against the user's cap of US$0.20.

Usage: python3 run_a1c.py smoke     one session (a K one-sentence control item) to check the setup; not scored
       python3 run_a1c.py main      the 24 items; never reruns
       python3 run_a1c.py second    the 12 R and F items once more -- only when fewer than 4 decisions differ
"""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[3]
WORKTREES = CHECKOUT.parent
DOTENV = CHECKOUT.parents[1] / 'netzoo_agent/.env'
HARNESS = CHECKOUT / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
ITEMS = HERE.parent / 'h8' / 'items.json'
SYSTEMS = {'E3': (WORKTREES / 'netzoo-a1c-e3', '8c1ed515')}
SNAPSHOT = ('scripts/netzoo_agent_core/graph/capability_check_call.py',
            'scripts/netzoo_agent_core/graph/fact_check_call.py',
            'scripts/netzoo_agent_core/interpretation/core_decision.py',
            'scripts/netzoo_agent_core/interpretation/goal_evidence.py')
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
CAP_USD = 0.20
TAGS = ('a1csmoke', 'a1c', 'a1c2')
SEED = 1024


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(run: Path) -> dict:
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=run, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=run, text=True).strip()
    files = subprocess.check_output(['git', 'ls-files', '-z', '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                                    cwd=run).decode().split('\0')
    return {'head': head, 'dirty': dirty, 'files': {n: sha(run / n) for n in files if n and (run / n).is_file()}}


def spent() -> float:
    """Provider-reported US$ over every call of this confirmation's sessions, each call once."""
    calls, usages = {}, []
    for tag in TAGS:
        usages += [json.loads(p.read_text()).get('token_usage') or {} for p in HERE.glob(f'live/{tag}/*/t*/session.json')]
        for trace in HERE.glob(f'live/{tag}/*/t*/trace-*.jsonl'):
            usages += [(json.loads(line).get('payload') or {}).get('token_usage') or {}
                       for line in trace.read_text().splitlines() if '"run.finished"' in line]
    for usage in usages:
        for call in usage.get('calls', []):
            calls[call.get('call_id') or id(call)] = call.get('cost_micro_usd') or 0
    return sum(calls.values()) / 1e6


def session_traces(run: Path, sid: str) -> dict[str, Path]:
    found = {}
    for events in (run / '.netzoo' / 'traces').glob('*/events.jsonl'):
        with events.open() as handle:
            first = json.loads(handle.readline() or '{}')
        if first.get('event_type') == 'run.started' and (first.get('payload') or {}).get('session_id') == sid:
            found[events.parent.name] = events
    return found


class Runner:
    def __init__(self, tag: str, env: dict, live):
        self.tag, self.env, self.live = tag, env, live
        self.output = HERE / 'live' / tag
        self.frozen = {name: fingerprint(run) for name, (run, _) in SYSTEMS.items()}
        self.stopped = None

    def job(self, item: dict, system: str) -> dict:
        run, _ = SYSTEMS[system]
        if fingerprint(run) != self.frozen[system]:
            raise RuntimeError(f'{system} code changed')
        sid = self.live.session_id(self.tag, f"{item['id']}-{system}", 1)
        folder = self.output / sid
        folder.mkdir()
        if (run / '.netzoo' / 'sessions' / f'{sid}.json').exists():
            raise ValueError(f'Session already exists: {sid}')
        turn = folder / 't1'
        turn.mkdir()
        args = ['--session', sid, '--keep-session', '--task', item['prompt']]
        started = time.time()
        with (turn / 'stdout.txt').open('xb') as out, (turn / 'stderr.txt').open('xb') as err:
            try:
                code = subprocess.call([self.live.PYTHON, '-c', self.live.BOOTSTRAP, *args], cwd=run,
                                       env={**self.env, 'NETZOO_PROFILE': sid,
                                            'CJ_CARD_CAPTURE': str(turn / 'cards.json')},
                                       stdin=subprocess.DEVNULL, stdout=out, stderr=err, timeout=600)
            except subprocess.TimeoutExpired:
                code = 'timeout'
        source = run / '.netzoo' / 'sessions' / f'{sid}.json'
        if source.exists():
            shutil.copyfile(source, turn / 'session.json')
        for run_id, events in session_traces(run, sid).items():
            shutil.copyfile(events, turn / f'trace-{run_id}.jsonl')
        write(turn / 'manifest.json', {'turn': 1, 'mode': '--session', 'exit': code, 'started': started,
                                       'finished': time.time()})
        if fingerprint(run) != self.frozen[system]:
            raise RuntimeError(f'{system} code changed during the job')
        end = 'complete' if code in (0, 2) else 'failed'  # 2: the turn ended waiting for input files
        record = {'item': item['id'], 'system': system, 'session': sid, 'codes': [code], 'sent': ['prompt'], 'end': end}
        write(folder / 'job.json', record)
        return record


def setup(tag: str):
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
    runner = Runner(tag, env, live)
    for name, (run, commit) in SYSTEMS.items():
        frozen = runner.frozen[name]
        changed = sorted(subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=run, text=True).split())
        untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=run, text=True)
        if not frozen['head'].startswith(commit) or changed != sorted(SNAPSHOT) or untracked.strip():
            raise RuntimeError(f'{name} worktree is not {commit} plus exactly the snapshot files')
        if any(frozen['files'][path] != sha(CHECKOUT / path) for path in SNAPSHOT):
            raise RuntimeError(f'{name} snapshot files differ from the harness-repair checkout')
    record = HERE / f'round-{tag}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    write(record, {'started_utc': stamp, 'tag': tag, 'code': {n: {
                       'head': f['head'], 'snapshot': {p: f['files'][p] for p in SNAPSHOT},
                       'files_sha256': hashlib.sha256(json.dumps(f['files'], sort_keys=True).encode()).hexdigest()}
                   for n, f in runner.frozen.items()}, 'items_sha256': sha(ITEMS), 'runner_sha256': sha(__file__),
                   'harness_sha256': sha(HARNESS), 'config': config, 'provider_prices': prices,
                   'price_catalog': pricing, 'cap_usd': CAP_USD, 'spent_before_usd': spent()})
    runner.output.mkdir(parents=True, exist_ok=False)
    return runner


def main(mode: str):
    items = json.loads(ITEMS.read_text())['single']
    if mode == 'smoke':
        todo = [next(i['id'] for i in items if i['category'] == 'K' and i['sub'] == 'one_sentence')]
        runner, workers = setup('a1csmoke'), 1
    elif mode == 'main':
        todo = [i['id'] for i in items]
        if len(todo) != 24:
            raise ValueError('Expected 24 items')
        runner, workers = setup('a1c'), 3
    elif mode == 'second':
        todo = [i['id'] for i in items if i['category'] in ('R', 'F')]
        if len(todo) != 12:
            raise ValueError('Expected 12 R and F items')
        runner, workers = setup('a1c2'), 3
    else:
        raise ValueError(mode)
    random.Random(SEED).shuffle(todo)
    by_id = {item['id']: item for item in items}
    results, queue = [], list(todo)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        running = {}
        while queue or running:
            while queue and len(running) < workers and runner.stopped is None:
                if (total := spent()) >= CAP_USD:
                    runner.stopped = f'cost cap reached: US${total:.4f}'
                    break
                key = queue.pop(0)
                running[pool.submit(runner.job, by_id[key], 'E3')] = key
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                key = running.pop(future)
                try:
                    row = future.result()
                except Exception as exc:
                    row = {'item': key, 'system': 'E3', 'error_type': type(exc).__name__, 'error': str(exc)}
                row['spent_usd'] = round(spent(), 4)
                results.append(row)
                write(HERE / f'jobs-{runner.tag}.json', results)
                print(json.dumps(row), flush=True)
    write(HERE / f'finished-{runner.tag}.json', {
        'finished_utc': datetime.now(timezone.utc).isoformat(),
        'runtime_code_unchanged': all(fingerprint(run) == runner.frozen[n] for n, (run, _) in SYSTEMS.items()),
        'sessions': len(results), 'not_started': len(queue), 'stopped': runner.stopped, 'spent_usd': round(spent(), 4)})


if __name__ == '__main__':
    main(sys.argv[1])

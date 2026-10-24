"""Harness repair P5 round 1 (ROUND-P5.md, user-approved 2026-10-23): the sealed h7 items on three clean worktrees.

- A `91a8c2d9` and E `129acb11` run all 50 items; D `61ccc3b7` runs the 14 multi-turn items. 114 sessions, one each.
- Turn 1 is `--session S --task`, each later turn `--resume S --task` (the h4 `run_job` shape). Replies follow the
  item's frozen branches by what the system asked (its core call's questions, never its reply text, which quotes the
  user): the deciding fact asked -> the frozen answer; anything else -> "I'm not sure about that."; turn 1 not asking ->
  the conversation stops. Switch and unknown replies are sent regardless (unknown's second only while the system still
  waits).
- The cost guard sums provider-reported cost over every call of this round and the smoke (session usage and copied
  trace runs, each call once by its id) and starts no turn once it reaches the user's cap of US$1.20.
- Item content is read by code only and never printed; job records hold which branch was sent, not its text.

Usage: python3 run_p5.py smoke    one session (a `correct` item on D) to check the setup; not scored
       python3 run_p5.py main     round 1; never reruns
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
ITEMS = HERE.parent / 'h7' / 'items.json'
SYSTEMS = {'A': (WORKTREES / 'netzoo-h6-final', '91a8c2d9'), 'D': (WORKTREES / 'netzoo-p5-d', '61ccc3b7'),
           'E': (WORKTREES / 'netzoo-harness-live', '129acb11')}
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
CAP_USD = 1.20
NOT_SURE = "I'm not sure about that."
WAITING = ('ASK', 'CLARIFY')
SEED = 1023


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
    """Provider-reported US$ over every call of the smoke and round 1, each call once."""
    calls, usages = {}, []
    for tag in ('p5smoke', 'p5r1'):
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


def turn_core(turn: Path) -> dict | None:
    """The core call this turn's graph made (the last `core.decision` of the runs it started), or None."""
    core = None
    for trace in sorted(turn.glob('trace-*.jsonl')):
        for line in trace.read_text().splitlines():
            if '"core.decision"' in line:
                row = json.loads(line)
                if row.get('event_type') == 'core.decision':
                    core = row['payload']
    return core


def asks_fact(core: dict | None, keywords: list[str]) -> bool:
    """Whether the call's own questions are about the deciding fact (its reply text quotes the user, so never it)."""
    if not core:
        return False
    asked = [fact.get('question', '') for fact in core.get('facts') or []]
    asked.append((core.get('clarify') or {}).get('question', ''))
    text = ' '.join(asked).casefold()
    return any(keyword.casefold() in text for keyword in keywords)


def jobs(items: dict) -> list[tuple[str, str]]:
    found = [(item['id'], system) for item in items['single'] for system in ('A', 'E')]
    found += [(item['id'], system) for item in items['multi'] for system in ('A', 'D', 'E')]
    random.Random(SEED).shuffle(found)
    return found


class Runner:
    def __init__(self, tag: str, env: dict, live):
        self.tag, self.env, self.live = tag, env, live
        self.output = HERE / 'live' / tag
        self.frozen = {name: fingerprint(run) for name, (run, _) in SYSTEMS.items()}
        self.stopped = None

    def _send(self, run: Path, sid: str, folder: Path, n: int, task: str, copied: set) -> object:
        turn = folder / f't{n}'
        turn.mkdir()
        args = ['--session' if n == 1 else '--resume', sid, '--keep-session', '--task', task]
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
            if run_id not in copied:
                copied.add(run_id)
                shutil.copyfile(events, turn / f'trace-{run_id}.jsonl')
        write(turn / 'manifest.json', {'turn': n, 'mode': args[0], 'exit': code, 'started': started,
                                       'finished': time.time()})
        return code

    def job(self, item: dict, system: str) -> dict:
        run, _ = SYSTEMS[system]
        if fingerprint(run) != self.frozen[system]:
            raise RuntimeError(f'{system} code changed')
        sid = self.live.session_id(self.tag, f"{item['id']}-{system}", 1)
        folder = self.output / sid
        folder.mkdir()
        if (run / '.netzoo' / 'sessions' / f'{sid}.json').exists():
            raise ValueError(f'Session already exists: {sid}')
        copied, codes, sent, end = set(), [], [], 'complete'
        multi = 'type' in item
        plan = [('prompt', item['prompt'])]
        for n in range(1, 4):
            if n > 1:
                plan = self._next(item, n, folder, sent)
                if not plan:
                    break
            if (total := spent()) >= CAP_USD:
                self.stopped, end = f'cost cap reached: US${total:.4f}', 'cap'
                break
            branch, text = plan[0]
            code = self._send(run, sid, folder, n, text, copied)
            codes.append(code)
            sent.append(branch)
            if code not in (0, 2):  # 2: the turn ended on a prompt a non-tty cannot answer (input required)
                end = 'failed'
                break
            if not multi:
                break
        if multi and len(sent) == 1 and end == 'complete':
            end = 't1_not_waiting'
        if fingerprint(run) != self.frozen[system]:
            raise RuntimeError(f'{system} code changed during the job')
        record = {'item': item['id'], 'system': system, 'session': sid, 'codes': codes, 'sent': sent, 'end': end}
        write(folder / 'job.json', record)
        return record

    @staticmethod
    def _next(item: dict, n: int, folder: Path, sent: list) -> list:
        """The reply for turn n by the item's frozen branches, or [] when the conversation ends."""
        core1 = turn_core(folder / 't1')
        if core1 is None or core1.get('kind') not in WAITING:
            return []
        kind, fact = item['type'], item.get('deciding_fact') or {}
        if kind == 'switch':
            return [('new_request', item['new_request'])] if n == 2 else []
        if kind == 'unknown':
            if n == 3:
                last = turn_core(folder / 't2')
                if last is not None and last.get('kind') not in WAITING:
                    return []
            return [(f'unknown_{n - 1}', item['unknown_replies'][n - 2])]
        if n == 2:
            asked = asks_fact(core1, fact.get('match_keywords') or [])
            return [('answer', fact['answer'])] if asked else [('not_sure', NOT_SURE)]
        if n == 3 and kind == 'correct' and sent[-1] == 'answer':
            return [('correction', item['correction'])]
        return []


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
        if not frozen['head'].startswith(commit) or frozen['dirty']:
            raise RuntimeError(f'{name} worktree is not the clean {commit}')
    record = HERE / f'round-{tag}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    write(record, {'started_utc': stamp, 'tag': tag, 'code': {n: {'head': f['head'], 'files_sha256':
                   hashlib.sha256(json.dumps(f['files'], sort_keys=True).encode()).hexdigest()}
                   for n, f in runner.frozen.items()}, 'items_sha256': sha(ITEMS), 'runner_sha256': sha(__file__),
                   'harness_sha256': sha(HARNESS), 'config': config, 'provider_prices': prices,
                   'price_catalog': pricing, 'cap_usd': CAP_USD, 'spent_before_usd': spent()})
    runner.output.mkdir(parents=True, exist_ok=False)
    return runner


def main(mode: str):
    items = json.loads(ITEMS.read_text())
    by_id = {item['id']: item for item in items['single'] + items['multi']}
    if mode == 'smoke':
        runner = setup('p5smoke')
        first = sorted(i['id'] for i in items['multi'] if i['type'] == 'correct')[0]
        todo, workers = [(first, 'D')], 1
    else:
        todo = jobs(items)
        if len(todo) != 114:
            raise ValueError('Expected 114 jobs')
        runner = setup('p5r1')
        workers = 3
    results, queue = [], list(todo)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        running = {}
        while queue or running:
            while queue and len(running) < workers and runner.stopped is None:
                if (total := spent()) >= CAP_USD:
                    runner.stopped = f'cost cap reached: US${total:.4f}'
                    break
                key = queue.pop(0)
                running[pool.submit(runner.job, by_id[key[0]], key[1])] = key
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                key = running.pop(future)
                try:
                    row = future.result()
                except Exception as exc:
                    row = {'item': key[0], 'system': key[1], 'error_type': type(exc).__name__, 'error': str(exc)}
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

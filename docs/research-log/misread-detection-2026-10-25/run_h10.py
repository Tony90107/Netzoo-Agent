"""M-hold pilot (PLAN-M-SHADOW.md, 36-item version, user-approved 2026-10-25): the sealed h10 conversations on
candidate C (`.worktrees/netzoo-m-hold`, NETZOO_M_HOLD=1). No decision of the frozen system is changed: C records the
call each turn would have made (`shadow.m_hold`) before any hold.

- System: C's worktree at `041f0ee9` plus exactly the pilot's files (SNAPSHOT), not committed; every tracked file of
  scripts/, workflows/, prompts/, AGENTS.md and every snapshot file is hashed before the round and re-checked before and
  after every job; any change stops the round.
- Turns: `run_h9.py`'s CLI call (`--session` for turn 1, `--resume` after, `--keep-session`), copying each turn's own
  trace lines as `harness-repair/p5/run_p5r2.py` does.
- Replies (PLAN-M-SHADOW.md, in code): after a DO, DECLINE, UNCHECKED or no call the conversation ends; after an ASK the
  item's `reply_fact` when one of the call's own questions (never the quoted user words) holds a `fact_keywords` word,
  else `reply_restate`; after a CLARIFY the item's `reply_result`, else `reply_restate`; at most 3 user turns.
- Cost: a turn starts only when spent + the reserve of the turns running + its own reserve stays within US$0.35. Spent
  is the provider's reported cost of every call of this round, the menu reads' from their `shadow.m_hold` events.

Usage: python3 run_h10.py smoke      one K1 conversation (up to 3 turns) to check the setup; not scored
       python3 run_h10.py turn1      the 36 first turns; never reruns
       python3 run_h10.py followup   turns 2-3 of the sessions whose first turn asked -- only when h10-gates-d.json
                                     (score_h10.py turn1) says the detection gates passed
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
import threading
import time
import urllib.request

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
WORKTREES = CHECKOUT.parent
DOTENV = WORKTREES.parent / 'netzoo_agent/.env'
HARNESS = CHECKOUT / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
ITEMS = HERE / 'h10' / 'items.json'
SEALED = HERE / 'h10' / 'SEALED.json'
GATES = HERE / 'h10-gates-d.json'
RUN, COMMIT = WORKTREES / 'netzoo-m-hold', '041f0ee98af9b6a50d7e644ff9140519a6daf9d7'
SNAPSHOT_MODIFIED = ('scripts/netzoo_agent_core/graph/routing_planning.py',
                     'scripts/netzoo_agent_core/interpretation/ask_facts.py',
                     'scripts/netzoo_agent_core/interpretation/clarify_goal.py',
                     'scripts/netzoo_agent_core/interpretation/core_decision.py',
                     'scripts/netzoo_agent_core/interpretation/semantic_goal.py')
SNAPSHOT_NEW = ('scripts/netzoo_agent_core/graph/m_hold_call.py',
                'scripts/netzoo_agent_core/interpretation/m_hold.py',
                'scripts/netzoo_agent_core/interpretation/m_hold_names.py',
                'tests/test_m_hold.py')
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
CAP_USD = 0.35
RESERVE = 0.012
TAGS = ('h10smoke', 'h10')
WAITING = ('ASK', 'CLARIFY')
SEED = 1026


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint() -> dict:
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RUN, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=RUN, text=True).strip()
    files = subprocess.check_output(['git', 'ls-files', '-z', '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                                    cwd=RUN).decode().split('\0')
    found = {n: sha(RUN / n) for n in files if n and (RUN / n).is_file()}
    found.update({n: sha(RUN / n) for n in SNAPSHOT_NEW})
    return {'head': head, 'dirty': dirty, 'files': found}


def check_system(frozen: dict) -> None:
    modified = sorted(subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=RUN, text=True).split())
    untracked = sorted(subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=RUN,
                                               text=True).split())
    if frozen['head'] != COMMIT or modified != sorted(SNAPSHOT_MODIFIED) or untracked != sorted(SNAPSHOT_NEW):
        raise RuntimeError(f'{RUN.name} is not {COMMIT[:8]} plus exactly the pilot files')


def spent() -> float:
    calls, menu = {}, {}
    for tag in TAGS:
        for path in HERE.glob(f'live/{tag}/*/t*/session.json'):
            for call in (json.loads(path.read_text()).get('token_usage') or {}).get('calls', []):
                calls[call.get('call_id') or id(call)] = call.get('cost_micro_usd') or 0
        for trace in HERE.glob(f'live/{tag}/*/t*/trace-*.jsonl'):
            for index, line in enumerate(trace.read_text().splitlines()):
                if '"run.finished"' in line:
                    usage = (json.loads(line).get('payload') or {}).get('token_usage') or {}
                    for call in usage.get('calls', []):
                        calls[call.get('call_id') or id(call)] = call.get('cost_micro_usd') or 0
                elif '"shadow.m_hold"' in line:
                    for n, call in enumerate((json.loads(line).get('payload') or {}).get('calls') or []):
                        menu[(str(trace), index, n)] = call.get('cost_micro_usd') or 0  # each turn's own lines
    return (sum(calls.values()) + sum(menu.values())) / 1e6


def check_sealed() -> str:
    if json.loads(SEALED.read_text())['sha256']['items.json'] != sha(ITEMS):
        raise RuntimeError('items.json differs from the sealed hash')
    return sha(ITEMS)


def turn_core(turn: Path) -> dict | None:
    core = None
    for trace in sorted(turn.glob('trace-*.jsonl')):
        for line in trace.read_text().splitlines():
            if '"core.decision"' in line and (row := json.loads(line)).get('event_type') == 'core.decision':
                core = row['payload']
    return core


def asks_fact(core: dict | None, keywords: list[str]) -> bool:
    """Whether the call's own questions (never the user's words it quotes) are about the deciding fact."""
    if not core or not keywords:
        return False
    asked = [fact.get('question', '') for fact in core.get('facts') or []]
    asked.append((core.get('clarify') or {}).get('question', ''))
    text = ' '.join(asked).casefold()
    return any(keyword.casefold() in text for keyword in keywords)


def next_reply(item: dict, previous: dict | None) -> tuple[str, str] | None:
    """PLAN-M-SHADOW.md's reply rule: (branch, text), or None when the conversation ends."""
    if previous is None or previous.get('kind') not in WAITING:
        return None
    if previous['kind'] == 'ASK':
        if item.get('reply_fact') and asks_fact(previous, item.get('fact_keywords') or []):
            return 'fact', item['reply_fact']
        return 'restate', item['reply_restate']
    if item.get('reply_result'):
        return 'result', item['reply_result']
    return 'restate', item['reply_restate']


class Guard:
    def __init__(self):
        self.lock, self.running, self.stopped = threading.Lock(), 0, None

    def admit(self) -> bool:
        with self.lock:
            if spent() + (self.running + 1) * RESERVE > CAP_USD:
                self.stopped = f'cap: spent US${spent():.4f} + reserve for {self.running + 1} turn(s) > US${CAP_USD}'
                return False
            self.running += 1
            return True

    def release(self):
        with self.lock:
            self.running -= 1


class Runner:
    def __init__(self, tag: str, env: dict, live, frozen: dict):
        self.tag, self.env, self.live, self.frozen, self.guard = tag, env, live, frozen, Guard()
        self.output = HERE / 'live' / tag

    def send(self, sid: str, folder: Path, n: int, text: str, copied: dict) -> object:
        if fingerprint() != self.frozen:
            raise RuntimeError('code changed')
        turn = folder / f't{n}'
        turn.mkdir()
        args = ['--session' if n == 1 else '--resume', sid, '--keep-session', '--task', text]
        started = time.time()
        with (turn / 'stdout.txt').open('xb') as out, (turn / 'stderr.txt').open('xb') as err:
            try:
                code = subprocess.call([self.live.PYTHON, '-c', self.live.BOOTSTRAP, *args], cwd=RUN,
                                       env={**self.env, 'NETZOO_PROFILE': sid, 'CJ_CARD_CAPTURE': str(turn / 'cards.json')},
                                       stdin=subprocess.DEVNULL, stdout=out, stderr=err, timeout=600)
            except subprocess.TimeoutExpired:
                code = 'timeout'
        source = RUN / '.netzoo' / 'sessions' / f'{sid}.json'
        if source.exists():
            shutil.copyfile(source, turn / 'session.json')
        for events in (RUN / '.netzoo' / 'traces').glob('*/events.jsonl'):
            with events.open() as handle:
                first = json.loads(handle.readline() or '{}')
            if first.get('event_type') != 'run.started' or (first.get('payload') or {}).get('session_id') != sid:
                continue
            run_id, lines = events.parent.name, events.read_text().splitlines(keepends=True)
            if len(lines) > copied.get(run_id, 0):
                (turn / f'trace-{run_id}.jsonl').write_text(''.join(lines[copied.get(run_id, 0):]))
                copied[run_id] = len(lines)
        write(turn / 'manifest.json', {'turn': n, 'mode': args[0], 'exit': code, 'started': started,
                                       'finished': time.time()})
        if fingerprint() != self.frozen:
            raise RuntimeError('code changed during the turn')
        return code

    def conversation(self, item: dict, turns: range) -> dict:
        """Turns `turns` of the item's conversation; a later call continues what job.json recorded."""
        sid = self.live.session_id('h10smoke' if self.tag == 'h10smoke' else 'h10', item['id'], 1)
        folder = HERE / 'live' / ('h10smoke' if self.tag == 'h10smoke' else 'h10') / sid
        if turns.start == 1:
            folder.mkdir()
            if (RUN / '.netzoo' / 'sessions' / f'{sid}.json').exists():
                raise ValueError(f'Session already exists: {sid}')
            record = {'item': item['id'], 'session': sid, 'codes': [], 'sent': [], 'copied': {}, 'end': 'open'}
        else:
            record = json.loads((folder / 'job.json').read_text())
        for n in turns:
            if n == 1:
                branch, text = 'prompt', item['prompt']
            else:
                reply = next_reply(item, turn_core(folder / f't{n - 1}'))
                if reply is None:
                    record['end'] = 'ended'
                    break
                branch, text = reply
            if not self.guard.admit():
                record['end'] = 'cap'
                break
            try:
                code = self.send(sid, folder, n, text, record['copied'])
            finally:
                self.guard.release()
            record['codes'].append(code)
            record['sent'].append(branch)
            if code not in (0, 2):
                record['end'] = 'failed'
                break
        else:
            record['end'] = 'open' if turns.stop <= 2 else 'turns_done'
        write(folder / 'job.json', record)
        return record


def setup(tag: str) -> Runner:
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
                'NETZOO_MODEL_PRICING_JSON': json.dumps(pricing), 'PYTHONUNBUFFERED': '1', 'NETZOO_M_HOLD': '1'})
    frozen = fingerprint()
    check_system(frozen)
    record = HERE / f'round-{tag}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    write(record, {'started_utc': stamp, 'tag': tag, 'code': {
        'head': frozen['head'], 'snapshot': {p: frozen['files'][p] for p in (*SNAPSHOT_MODIFIED, *SNAPSHOT_NEW)},
        'files_sha256': hashlib.sha256(json.dumps(frozen['files'], sort_keys=True).encode()).hexdigest()},
        'items_sha256': check_sealed(), 'runner_sha256': sha(__file__), 'harness_sha256': sha(HARNESS),
        'config': config, 'm_hold': True, 'provider_prices': prices, 'price_catalog': pricing,
        'cap_usd': CAP_USD, 'reserve_usd': RESERVE, 'spent_before_usd': round(spent(), 6)})
    return Runner(tag, env, live, frozen)


def main(mode: str):
    check_sealed()
    items = json.loads(ITEMS.read_text())['single']
    by_id = {item['id']: item for item in items}
    if mode == 'smoke':
        runner, todo, turns, workers = setup('h10smoke'), [sorted(i['id'] for i in items if i['category'] == 'K1')[0]], range(1, 4), 1
        (HERE / 'live' / 'h10smoke').mkdir(parents=True, exist_ok=False)
    elif mode == 'turn1':
        runner, todo, turns, workers = setup('h10'), [i['id'] for i in items], range(1, 2), 3
        if len(todo) != 36:
            raise ValueError('Expected 36 items')
        (HERE / 'live' / 'h10').mkdir(parents=True, exist_ok=False)
    elif mode == 'followup':
        gates = json.loads(GATES.read_text()) if GATES.exists() else {}
        if not gates.get('passed'):
            raise RuntimeError('The detection gates did not pass (or were not scored): turns 2-3 are not run.')
        runner, turns, workers = setup('h10followup'), range(2, 4), 3
        todo = [i['id'] for i in items if (turn_core(HERE / 'live' / 'h10' / f"hb-h10-{i['id']}-1" / 't1') or {})
                .get('kind') in WAITING]
    else:
        raise ValueError(mode)
    random.Random(SEED).shuffle(todo)
    results, queue = [], list(todo)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        running = {}
        while queue or running:
            while queue and len(running) < workers and runner.guard.stopped is None:
                key = queue.pop(0)
                running[pool.submit(runner.conversation, by_id[key], turns)] = key
            if not running:
                break
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                key = running.pop(future)
                try:
                    row = future.result()
                except Exception as exc:  # noqa: BLE001 -- recorded, never hidden
                    row = {'item': key, 'error_type': type(exc).__name__, 'error': str(exc)[:300]}
                    runner.guard.stopped = runner.guard.stopped or f'job error on {key}'
                row = {k: v for k, v in row.items() if k != 'copied'} | {'spent_usd': round(spent(), 4)}
                results.append(row)
                write(HERE / f'jobs-{runner.tag}.json', results)
                print(json.dumps(row), flush=True)
    write(HERE / f'finished-{runner.tag}.json', {
        'finished_utc': datetime.now(timezone.utc).isoformat(), 'runtime_code_unchanged': fingerprint() == runner.frozen,
        'conversations': len(results), 'not_started': queue, 'stopped': runner.guard.stopped,
        'spent_usd': round(spent(), 4)})


if __name__ == '__main__':
    main(sys.argv[1])

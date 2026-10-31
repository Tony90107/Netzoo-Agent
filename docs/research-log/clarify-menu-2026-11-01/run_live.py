"""clarify-menu live L1/L2 (ROUND.md): A07, A29, A36 (j9) and B28, B29, B36 (j10), 2 runs each (tags cm1, cm2), on this
checkout with the app `.env` (its flags as the user set them) plus NETZOO_CLARIFY_MENU=on, up to 3 turns. When a turn
is a CLARIFY whose card shows the result-family menu, the scripted user clicks the family CLICKS.json names (it sends
that button's `answer`); any other turn uses the j10 reply rule. Adapted from answer-buttons run_live.py. Cap US$0.12.

Usage: python3 run_live.py cm1|cm2
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
LOGS = HERE.parent
J6 = HERE.parent / 'jev-j6-2026-10-29'
J5 = HERE.parent / 'jev-j5-2026-10-28'
J4 = HERE.parent / 'jev-j4-2026-10-27'
CHECKOUT = HERE.parents[2]
WORKTREES = CHECKOUT.parent
DOTENV = WORKTREES.parent / 'netzoo_agent/.env'
HARNESS = CHECKOUT / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
CT = WORKTREES / 'netzoo-ct' / 'docs/research-log'  # j9 lives on the candidate-table branch
RR = WORKTREES / 'netzoo-rr' / 'docs/research-log'
SETS = ((CT / 'hybrid-j9-2026-10-31/j9/items.json', CT / 'hybrid-j9-2026-10-31/j9/SEALED.json'),
        (RR / 'fresh-j10-2026-10-31/j10/items.json', RR / 'fresh-j10-2026-10-31/j10/SEALED.json'))
CLICKS = json.loads((HERE / 'CLICKS.json').read_text())
PICKED: list = []  # set by main from CLICKS.json
FLAGS = ('NETZOO_CLARIFY_MENU',)
RUN = CHECKOUT
COMMIT = '8f60b653'  # set by main per arm
ARMS = {tag: (None, None) for tag in ('cm1', 'cm2')}
SNAPSHOT_MODIFIED: tuple = ()
SNAPSHOT_NEW: tuple = ()
MODELS = {'openai/gpt-4o-mini', 'openai/gpt-4o-mini-2024-07-18'}
CAP_USD = 0.20
RESERVE = 0.012
TAG = ['']
TAGS = [None]  # set by main: the arm's own tag
WAITING = ('ASK', 'CLARIFY')
SEED = 10031


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint() -> dict:
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RUN, text=True).strip()
    dirty = '\n'.join(line for line in subprocess.check_output(['git', 'status', '--porcelain'], cwd=RUN, text=True)
                      .splitlines() if 'docs/research-log/' not in line)  # this round's own records live here
    files = subprocess.check_output(['git', 'ls-files', '-z', '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                                    cwd=RUN).decode().split('\0')
    found = {n: sha(RUN / n) for n in files if n and (RUN / n).is_file()}
    found.update({n: sha(RUN / n) for n in SNAPSHOT_NEW})
    return {'head': head, 'dirty': dirty, 'files': found}


def check_system(frozen: dict) -> None:
    modified = sorted(subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=RUN, text=True).split())
    untracked = sorted(subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=RUN,
                                               text=True).split())
    code = [n for n in (*modified, *untracked) if not n.startswith('docs/research-log/')]
    drift = subprocess.run(['git', 'diff', '--quiet', COMMIT, 'HEAD', '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                           cwd=RUN).returncode  # the round's records may be committed; the code may not change
    if drift or code:
        raise RuntimeError(f'{RUN.name} is not {COMMIT} with clean code (changed: {code[:5]})')


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
                elif '"core.jev_guard"' in line:
                    jev = (json.loads(line).get('payload') or {}).get('jev') or {}
                    menu[(str(trace), index)] = (jev.get('cost') or 0) * 1e6  # each turn's own lines
                elif '"core.jev_overlap"' in line or '"core.jev_forms"' in line:
                    reads = (json.loads(line).get('payload') or {}).get('reads') or []
                    menu[(str(trace), index)] = sum(((r.get('read') or {}).get('cost') or 0) for r in reads) * 1e6
                elif any(f'"core.jev_{kind}"' in line for kind in ('link', 'condition', 'answer')):
                    payload = json.loads(line).get('payload') or {}
                    found = payload.get('pick') or payload.get('typed') or payload.get('judged') or {}
                    menu[(str(trace), index)] = (found.get('cost') or 0) * 1e6
    return (sum(calls.values()) + sum(menu.values())) / 1e6


def check_sealed() -> list[str]:
    for items, sealed in SETS:
        if json.loads(sealed.read_text())['sha256']['items.json'] != sha(items):  # sealed before any run
            raise RuntimeError(f'{items} differs from the sealed hash')
    return [sha(items) for items, _ in SETS]


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
    if core.get('basis') in ('jev_fact', 'jev_condition'):  # RESULTS-J1.md: its fact is the quoted sentence it asks the user to settle
        asked += [fact.get('user_quote', '') for fact in core.get('facts') or []]
    asked.append((core.get('clarify') or {}).get('question', ''))
    text = ' '.join(asked).casefold()
    return any(keyword.casefold() in text for keyword in keywords)


FORMS = ('group_membership', 'time_model', 'spatial', 'input_network')


def asks_form(core: dict) -> bool:
    """A form question (jev-overlap and jev-forms needs_fact dimensions)."""
    return any(fact.get('depends_on') in FORMS for fact in core.get('facts') or [])


def clicked(item: dict, previous: dict, turn: Path | None) -> tuple[str, str] | None:
    """(branch "result", the family button's answer) when this turn is a CLARIFY showing the menu."""
    family = CLICKS['items'].get(item['id'], {}).get('family')
    if turn is None or previous.get('kind') != 'CLARIFY' or not family or not (turn / 'cards.json').exists():
        return None
    for card in json.loads((turn / 'cards.json').read_text()):
        for option in ((card.get('choices') or {}).get('options') or []):
            if option.get('key') == f'family-{family}':
                return 'result', option['answer']
    return None


def clicked_ask(item: dict, previous: dict, turn: Path | None) -> tuple[str, str] | None:
    """Round 1's ASK click (unused here)."""
    facts = previous.get('facts') or []
    if turn is None or len(facts) != 1:
        return None
    fact = facts[0]
    what = fact.get('depends_on') or '+'.join(fact.get('workflows') or [])
    click = CLICKS['items'].get(item['id'], {}).get('clicks', {}).get(what)
    if click is None or not (turn / 'cards.json').exists():
        return None
    label, is_fact = click
    for card in json.loads((turn / 'cards.json').read_text()):
        for option in ((card.get('choices') or {}).get('options') or []):
            if option.get('label') == label:
                return ('fact' if is_fact else 'click'), option['answer']
    return None


def next_reply(item: dict, previous: dict | None, turn: Path | None = None) -> tuple[str, str] | None:
    """The click when CLICKS.json names this question, else PLAN-M-SHADOW.md's reply rule; None ends it."""
    if previous is None or previous.get('kind') not in WAITING:
        return None
    if (click := clicked(item, previous, turn)) is not None:
        return click
    if previous['kind'] == 'ASK':
        if item.get('reply_fact') and asks_fact(previous, item.get('fact_keywords') or []):
            return 'fact', item['reply_fact']
        if item.get('reply_form') and asks_form(previous):
            return 'form', item['reply_form']
        if item.get('reply_confirm'):
            return 'confirm', item['reply_confirm']
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
    def __init__(self, tag: str, env: dict, live, frozen: dict):  # noqa: D107
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
        sid = self.live.session_id(self.tag, item['id'], 1)
        folder = HERE / 'live' / self.tag / sid
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
                reply = next_reply(item, turn_core(folder / f't{n - 1}'), folder / f't{n - 1}')
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
    flags = {k: env.get(k, 'off') for k in ('NETZOO_JEV_GUARD', 'NETZOO_JEV_OVERLAP', 'NETZOO_JEV_FORMS')}
    if set(flags.values()) != {'on'}:  # PLAN-J6.md: the app's .env as the user set it (all three on)
        raise RuntimeError(f'Unexpected Jev flags in the app .env: {flags}')
    env.pop('OPENROUTER_CAPABILITY_EXTRA_TOKENS', None)  # compose does not pass it: the code default (45,000)
    if env.get('NETZOO_AGENT_ANSWERS') != 'on' or env.get('NETZOO_JEV_DATA_HAS'):  # the app .env as the user set it
        raise RuntimeError('Unexpected NETZOO_AGENT_ANSWERS / NETZOO_JEV_DATA_HAS in the app .env')
    env.update({'NETZOO_MAX_TASK_TOKENS': '30000', 'NETZOO_MODEL_PRICING_JSON': json.dumps(pricing),
                'PYTHONUNBUFFERED': '1'})
    for name in FLAGS:  # arm F turns both fixes on; arm M runs main as the app does
        env.pop(name, None)
        if tag.startswith('cm'):
            env[name] = 'on'
    env.pop('NETZOO_JEV_SETTINGS', None)
    for name in ('NETZOO_JEV_OVERLAP_CACHE', 'NETZOO_JEV_FORMS_CACHE', 'NETZOO_JEV_SETTINGS_CACHE'):
        env.pop(name, None)
    frozen = fingerprint()
    check_system(frozen)
    record = HERE / f'round-{tag}.json'
    if record.exists():
        raise RuntimeError('This run already started; never rerun implicitly.')
    write(record, {'started_utc': stamp, 'tag': tag, 'code': {
        'head': frozen['head'], 'snapshot': {p: frozen['files'][p] for p in (*SNAPSHOT_MODIFIED, *SNAPSHOT_NEW)},
        'files_sha256': hashlib.sha256(json.dumps(frozen['files'], sort_keys=True).encode()).hexdigest()},
        'items_sha256': check_sealed(), 'runner_sha256': sha(__file__), 'harness_sha256': sha(HARNESS), 'jev_url': env.get('NETZOO_JEV_URL', ''),
        'config': config, 'jev_flags': flags, 'agent_answers': env['NETZOO_AGENT_ANSWERS'], 'fix_flags': {name: env.get(name, 'off') for name in FLAGS}, 'run_dir': str(RUN), 'commit': COMMIT, 'provider_prices': prices, 'price_catalog': pricing,
        'cap_usd': CAP_USD, 'reserve_usd': RESERVE, 'spent_before_usd': round(spent(), 6)})
    return Runner(tag, env, live, frozen)


def main(mode: str):
    check_sealed()
    by_id = {item['id']: item for items, _ in SETS for item in json.loads(items.read_text())['single']}
    global RUN, COMMIT
    if mode not in ARMS:
        raise ValueError(mode)
    COMMIT, folder = ARMS[mode]
    COMMIT = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CHECKOUT, text=True).strip()
    RUN = WORKTREES / folder if folder else CHECKOUT
    tag = mode
    global CAP_USD
    TAGS[:] = ['cm1', 'cm2']  # the cap counts both tags together
    CAP_USD = 0.12
    PICKED[:] = list(CLICKS['reps'][mode])
    runner, todo, turns, workers = setup(tag), list(PICKED), range(1, 4), 3
    (HERE / 'live' / tag).mkdir(parents=True, exist_ok=False)
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

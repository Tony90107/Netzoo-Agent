"""Live check of the Jev overlap second read (ROUND.md "Not measured offline"; user decision 2026-10-27 to keep the
change despite G2 and run it). 13 conversations, 1 rep, turns 1-3, gpt-4o-mini, NETZOO_JEV_OVERLAP=on and
NETZOO_JEV_GUARD=on (the kept guard; the comparison is j2 arm G, guard on and overlap off).

Items (all seen): j2 Q01 Q02 Q13 Q18 Q29 Q36 Q38; h5 Q26 (as H26); j1 J01; controls JN8 ON5 QN5 SN1 (vqbase texts).
Reply rule: after an ASK that asks the group_membership question, the reply names an option ("One group each." for
the not-overlap items, "Several groups at once." for the controls); otherwise j2's rule (run_j2.next_reply) for j2
items; anything else ends the conversation. Cost cap US$0.30.

Usage: python3 run_live.py smoke   (H26 only, tag josmoke)   then   python3 run_live.py all   (tag jo1; never reruns)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[2]
DOTENV = RUN.parent.parent / 'netzoo_agent/.env'
HARNESS = RUN / 'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
J2 = RUN / 'docs/research-log/jev-guard-2026-10-27'
CODE = '42dbc65d'  # the change's code commit; scripts must not differ from it
CAP_USD = 0.30
OPTION = {False: 'One group each.', True: 'Several groups at once.'}
CONTROLS = ('JN8', 'ON5', 'QN5', 'SN1')

sys.path.insert(0, str(J2))
import run_j2  # noqa: E402  (next_reply, turn_core: the j2 reply rule unchanged)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def items() -> list[dict]:
    j2 = {i['id']: i for i in json.loads((J2 / 'j2/items.json').read_text())['single']}
    j1 = {i['id']: i for i in json.loads((J2 / 'j1/items.json').read_text())['single']}
    population = json.loads((HERE / 'population.json').read_text())
    text = {p['session'].split('-')[2]: p['request'] for p in population if p['src'] == 'replay'}
    found = [dict(j2[k], overlap=False) for k in ('Q01', 'Q02', 'Q13', 'Q18', 'Q29', 'Q36', 'Q38')]
    found.append({'id': 'H26', 'prompt': text['Q26'], 'expected_call': 'DO', 'overlap': False})
    found.append(dict(j1['J01'], overlap=False))
    found += [{'id': k, 'prompt': text[k], 'expected_call': 'DECLINE', 'overlap': True} for k in CONTROLS]
    return found


def asks_groups(core: dict | None) -> bool:
    return bool(core) and core.get('kind') == 'ASK' and any(
        fact.get('depends_on') == 'group_membership' for fact in core.get('facts') or [])


def next_reply(item: dict, previous: dict | None):
    if asks_groups(previous):
        return 'option', OPTION[item['overlap']]
    if item['id'].startswith('Q') and item['id'] != 'Q26':
        return run_j2.next_reply(item, previous)
    return None


def spent(tag: str) -> float:
    calls, jev = {}, 0.0
    for trace in HERE.glob(f'live/{tag}/*/t*/trace-*.jsonl'):
        for line in trace.read_text().splitlines():
            row = json.loads(line)
            kind, payload = row.get('event_type'), row.get('payload') or {}
            if kind == 'run.finished':
                for call in (payload.get('token_usage') or {}).get('calls', []):
                    calls[call.get('call_id') or id(call)] = call.get('cost_micro_usd') or 0
            elif kind == 'core.jev_guard':
                jev += (payload.get('jev') or {}).get('cost') or 0
            elif kind == 'core.jev_overlap':
                jev += sum((read.get('read') or {}).get('cost') or 0 for read in payload.get('reads') or [])
    return sum(calls.values()) / 1e6 + jev


def check_code():
    drift = subprocess.run(['git', 'diff', '--quiet', CODE, '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                           cwd=RUN).returncode
    if drift:
        raise RuntimeError(f'code differs from {CODE}')


def main(mode: str):
    tag = {'smoke': 'josmoke', 'all': 'jo1'}[mode]
    todo = [i for i in items() if mode == 'all' or i['id'] == 'H26']
    check_code()
    sys.path.insert(0, str(HARNESS.parent))
    spec = importlib.util.spec_from_file_location('h4_live', HARNESS)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    env = live.environment(DOTENV)
    if env.get('OPENROUTER_CAPABILITY_MODEL') != 'openai/gpt-4o-mini-2024-07-18' or not env.get('OPENROUTER_API_KEY'):
        raise RuntimeError('unexpected model configuration')
    env.update({'NETZOO_MAX_TASK_TOKENS': '30000', 'OPENROUTER_CAPABILITY_EXTRA_TOKENS': '30000',
                'PYTHONUNBUFFERED': '1', 'NETZOO_JEV_GUARD': 'on', 'NETZOO_JEV_OVERLAP': 'on'})
    env.pop('NETZOO_JEV_OVERLAP_CACHE', None)
    out = HERE / 'live' / tag
    out.mkdir(parents=True, exist_ok=False)  # never reruns
    write(HERE / f'round-{tag}.json', {'started_utc': datetime.now(timezone.utc).isoformat(), 'code': CODE,
                                       'items': [i['id'] for i in todo], 'runner_sha256': hashlib.sha256(
                                           Path(__file__).read_bytes()).hexdigest(), 'cap_usd': CAP_USD})

    def send(sid, folder, n, text, copied):
        check_code()
        turn = folder / f't{n}'
        turn.mkdir()
        args = ['--session' if n == 1 else '--resume', sid, '--keep-session', '--task', text]
        with (turn / 'stdout.txt').open('xb') as stdout, (turn / 'stderr.txt').open('xb') as stderr:
            try:
                code = subprocess.call([live.PYTHON, '-c', live.BOOTSTRAP, *args], cwd=RUN,
                                       env={**env, 'NETZOO_PROFILE': sid, 'CJ_CARD_CAPTURE': str(turn / 'cards.json')},
                                       stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=600)
            except subprocess.TimeoutExpired:
                code = 'timeout'
        source = RUN / '.netzoo' / 'sessions' / f'{sid}.json'
        if source.exists():
            shutil.copyfile(source, turn / 'session.json')
        for events in (RUN / '.netzoo' / 'traces').glob('*/events.jsonl'):
            with events.open() as handle:
                first = json.loads(handle.readline() or '{}')
            if (first.get('payload') or {}).get('session_id') != sid:
                continue
            run_id, lines = events.parent.name, events.read_text().splitlines(keepends=True)
            if len(lines) > copied.get(run_id, 0):
                (turn / f'trace-{run_id}.jsonl').write_text(''.join(lines[copied.get(run_id, 0):]))
                copied[run_id] = len(lines)
        return code

    def conversation(item):
        sid = live.session_id(tag, item['id'], 1)
        folder = out / sid
        folder.mkdir()
        record, copied = {'item': item['id'], 'session': sid, 'codes': [], 'sent': [], 'end': 'turns_done'}, {}
        for n in range(1, 4):
            if n == 1:
                branch, text = 'prompt', item['prompt']
            else:
                reply = next_reply(item, run_j2.turn_core(folder / f't{n - 1}'))
                if reply is None:
                    record['end'] = 'ended'
                    break
                branch, text = reply
            if spent(tag) > CAP_USD:
                record['end'] = 'cap'
                break
            code = send(sid, folder, n, text, copied)
            record['codes'].append(code)
            record['sent'].append(branch)
            if code not in (0, 2):
                record['end'] = 'failed'
                break
        write(folder / 'job.json', record)
        return record

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(conversation, todo))
    for row in results:
        print(json.dumps(row))
    write(HERE / f'finished-{tag}.json', {'finished_utc': datetime.now(timezone.utc).isoformat(),
                                          'conversations': len(results), 'spent_usd': round(spent(tag), 4)})
    print('spent US$', round(spent(tag), 4))


if __name__ == '__main__':
    main(sys.argv[1])

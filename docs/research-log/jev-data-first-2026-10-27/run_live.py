"""Live check of data-first (RESULTS.md, E4 included; user decision 2026-10-27). 6 conversations x 1 rep, turns 1-3,
gpt-4o-mini, NETZOO_JEV_GUARD, NETZOO_JEV_OVERLAP and NETZOO_JEV_FORMS on, code 297b44fc.

Items (all seen): data ruled out -- j4 S32 (expression matrix for SAMBAR), j4 S10 (V; its result reply asks
protein-metabolite communities), j2 Q18 (expression matrix for SAMBAR; offline it was not caught); data acceptable --
j4 S05, j4 S39, j3 R31. Reply rule: j4's (run_j4.next_reply) with j3's `reply_membership` as the form answer. Expected
final: `final_after_result` / `final_after_fact` when that reply was sent, else the opening call. Cost cap US$0.20.

Usage: python3 run_live.py all   (tag jd1; never reruns)
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
J2 = RUN / 'docs/research-log/jev-guard-2026-10-27'  # j2 items (Q18)
CODE = '297b44fc'  # the change's code commit; scripts must not differ from it
CAP_USD = 0.20
J4 = RUN / 'docs/research-log/jev-j4-2026-10-27'
J3 = RUN / 'docs/research-log/jev-j3-2026-10-27'
ITEMS = {'j4': ('S32', 'S10', 'S05', 'S39'), 'j3': ('R31',), 'j2': ('Q18',)}
CONTROLS: tuple = ()
sys.path.insert(0, str(J4))
import run_j4  # noqa: E402  (next_reply, turn_core, asks_form: the j4 reply rule unchanged)

sys.path.insert(0, str(J2))
import run_j2  # noqa: E402  (next_reply, turn_core: the j2 reply rule unchanged)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def items() -> list[dict]:
    j4 = {i['id']: i for i in json.loads((J4 / 'j4/items.json').read_text())['single']}
    j3 = {i['id']: i for i in json.loads((J3 / 'j3/items.json').read_text())['single']}
    found = [dict(j4[k]) for k in ITEMS['j4']]
    found += [dict(j3[k], reply_form=j3[k].get('reply_membership', '')) for k in ITEMS['j3']]
    j2 = {i['id']: i for i in json.loads((J2 / 'j2/items.json').read_text())['single']}
    found += [dict(j2[k]) for k in ITEMS['j2']]
    return found


def expected(item: dict, sent=()) -> str:
    call = item['expected_call']
    if 'result' in sent and item.get('final_after_result'):
        call = item['final_after_result']['call']
    elif 'fact' in sent and item.get('final_after_fact'):
        call = item['final_after_fact']['call']
    return 'DO' if call == 'PARTIAL' else call


def next_reply(item: dict, previous: dict | None):
    return run_j4.next_reply(item, previous)


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
            elif kind in ('core.jev_overlap', 'core.jev_forms'):
                jev += sum((read.get('read') or {}).get('cost') or 0 for read in payload.get('reads') or [])
            elif kind in ('core.jev_link', 'core.jev_condition', 'core.jev_answer'):
                jev += ((payload.get('pick') or payload.get('typed') or payload.get('judged') or {}).get('cost') or 0)
    return sum(calls.values()) / 1e6 + jev


def check_code():
    drift = subprocess.run(['git', 'diff', '--quiet', CODE, '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                           cwd=RUN).returncode
    if drift:
        raise RuntimeError(f'code differs from {CODE}')


def main(mode: str):
    tag = {'all': 'jd1'}[mode]
    todo = items()
    check_code()
    sys.path.insert(0, str(HARNESS.parent))
    spec = importlib.util.spec_from_file_location('h4_live', HARNESS)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    env = live.environment(DOTENV)
    if env.get('OPENROUTER_CAPABILITY_MODEL') != 'openai/gpt-4o-mini-2024-07-18' or not env.get('OPENROUTER_API_KEY'):
        raise RuntimeError('unexpected model configuration')
    env.update({'NETZOO_MAX_TASK_TOKENS': '30000', 'OPENROUTER_CAPABILITY_EXTRA_TOKENS': '30000',
                'PYTHONUNBUFFERED': '1', 'NETZOO_JEV_GUARD': 'on', 'NETZOO_JEV_OVERLAP': 'on',
                'NETZOO_JEV_FORMS': 'on'})
    for name in ('NETZOO_JEV_OVERLAP_CACHE', 'NETZOO_JEV_FORMS_CACHE'):
        env.pop(name, None)
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
                reply = next_reply(item, run_j4.turn_core(folder / f't{n - 1}'))
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

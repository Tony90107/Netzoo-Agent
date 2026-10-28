"""Live re-measure on the app's aligned settings (app-config-align-2026-10-28; user decision 2026-10-28 "跑 live").
Same 14 conversations as check-reserve ck1 (copied runner), 1 rep, turns 1-3, gpt-4o-mini, settings of the aligned
compose + app .env: own check model, 30,000 turn budget, NETZOO_JEV_GUARD on, NETZOO_JEV_OVERLAP on,
NETZOO_JEV_FORMS OFF (the one difference from ck1), code 7c9fbdd4 (scripts unchanged since).

Items (all seen), from recorded runs where the bug hit: enum-limit 400 on turn 3 -- j1 J20, J48; j2 Q02; j3 R21;
j4 S05, S35. Second opinion refused by the 16,000 reserve -- j2 Q10, Q25, Q26; j3 R03; j4 S03. Re-read refused --
j1 J34, J46, J06. Reply rule: j4's (run_j4.next_reply). Expected final: `final_after_result` / `final_after_fact` when
that reply was sent, else the opening call. Cost cap US$0.20.

Usage: python3 run_live.py smoke|all   (tags casmoke (S35) / ca1; never reruns)
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
CODE = '7c9fbdd4'  # the change's code commit; scripts must not differ from it
CAP_USD = 0.20
J4 = RUN / 'docs/research-log/jev-j4-2026-10-27'
J3 = RUN / 'docs/research-log/jev-j3-2026-10-27'
ITEMS = {'j4': ('S05', 'S35', 'S03'), 'j3': ('R21', 'R03'), 'j2': ('Q02', 'Q10', 'Q25', 'Q26'),
         'j1': ('J20', 'J48', 'J34', 'J46', 'J06')}
SMOKE = {'j4': ('S35',)}
CONTROLS: tuple = ()
sys.path.insert(0, str(J4))
import run_j4  # noqa: E402  (next_reply, turn_core, asks_form: the j4 reply rule unchanged)

sys.path.insert(0, str(J2))
import run_j2  # noqa: E402  (next_reply, turn_core: the j2 reply rule unchanged)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def items(chosen=ITEMS) -> list[dict]:
    sets = {'j4': J4 / 'j4/items.json', 'j3': J3 / 'j3/items.json', 'j2': J2 / 'j2/items.json',
            'j1': J2 / 'j1/items.json'}
    found = []
    for name, ids in chosen.items():
        pool = {i['id']: i for i in json.loads(sets[name].read_text())['single']}
        found += [dict(pool[k], reply_form=pool[k].get('reply_membership', '')) for k in ids]
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
    tag = {'all': 'ca1', 'smoke': 'casmoke'}[mode]
    todo = items(SMOKE if mode == 'smoke' else ITEMS)
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
                'NETZOO_JEV_FORMS': 'off'})
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

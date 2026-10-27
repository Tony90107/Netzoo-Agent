"""Live check of the Jev forms read (RESULTS.md; user decision 2026-10-27 to keep it despite F2 and run it).
15 conversations x 1 rep, turns 1-3, gpt-4o-mini, NETZOO_JEV_FORMS=on, NETZOO_JEV_OVERLAP=on, NETZOO_JEV_GUARD=on.

Items (all seen; expected final in EXPECTED): misreads R39 R47 J17 (j1/j3 items), J40 L35 Q13 (nsbase texts), C21 (core),
R13 (j3), C23 (goalRead); controls HN2 RN1 QN10 SN8 (vqbase texts), Q34 (j2 item), Q18 (nsbase text).
Reply rule: after an ASK with a form question (input_network, time_model, spatial, group_membership) the reply names
the option the request's words mean (CONTROL_REPLY for controls); otherwise j items follow j2's rule
(run_j2.next_reply), C21 answers its file question, anything else ends the conversation. Cost cap US$0.30.

Usage: python3 run_live.py smoke (J40 only, tag jfsmoke)   then   python3 run_live.py all (tag jf1; never reruns)
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
CODE = '34dbdfc1'  # the change's code commit; scripts must not differ from it
CAP_USD = 0.30
MISREAD_REPLY = {'input_network': 'Regulators to genes.', 'time_model': 'Each time point separately.',
                 'spatial': 'Each sample on its own.', 'group_membership': 'One group each.'}
CONTROL_REPLY = {'input_network': 'Genes to genes.', 'time_model': 'A dynamic model.', 'spatial': 'Spatial neighbours.',
                 'group_membership': 'Several groups at once.'}
CONTROLS = ('HN2', 'RN1', 'QN10', 'SN8', 'Q34', 'Q18')
EXPECTED = {'R39': 'DO', 'R47': 'DO', 'J17': 'DO', 'J40': 'DO', 'L35': 'DO', 'Q13': 'DO', 'C21': 'DO', 'R13': 'DO',
            'C23': 'CLARIFY', 'HN2': 'DECLINE', 'RN1': 'DECLINE', 'QN10': 'DECLINE', 'SN8': 'DECLINE', 'Q34': 'DECLINE',
            'Q18': 'DECLINE'}
C21_REPLY = 'It is the TF-to-gene regulatory network from his PANDA runs.'
FORMS = tuple(MISREAD_REPLY)

sys.path.insert(0, str(J2))
import run_j2  # noqa: E402  (next_reply, turn_core: the j2 reply rule unchanged)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def items() -> list[dict]:
    j1 = {i['id']: i for i in json.loads((J2 / 'j1/items.json').read_text())['single']}
    j2 = {i['id']: i for i in json.loads((J2 / 'j2/items.json').read_text())['single']}
    j3 = {i['id']: i for i in json.loads((RUN / 'docs/research-log/jev-j3-2026-10-27/j3/items.json').read_text())['single']}
    population = json.loads((HERE / 'population-full.json').read_text())
    text = {}
    for p in population:
        group, item = p['session'].split('-')[1], p['session'].split('-')[2]
        if p['turn'] == 't1' and group in ('nsbase', 'vqbase', 'p4c', 'goalRead20261021'):
            text.setdefault(item, p['request'])
    found = [dict(j3['R39'], j=True), dict(j3['R47'], j=True), dict(j1['J17'], j=True), dict(j3['R13'], j=True),
             dict(j2['Q34'], j=True)]
    found += [{'id': k, 'prompt': text[k], 'j': False} for k in ('J40', 'L35', 'Q13', 'C21', 'C23', 'HN2', 'RN1',
                                                                 'QN10', 'SN8', 'Q18')]
    for item in found:
        item['control'] = item['id'] in CONTROLS
    return found


def form_asked(core: dict | None) -> str | None:
    if not core or core.get('kind') != 'ASK':
        return None
    return next((f['depends_on'] for f in core.get('facts') or [] if f.get('depends_on') in FORMS), None)


def next_reply(item: dict, previous: dict | None):
    if (form := form_asked(previous)) is not None:
        return 'option', (CONTROL_REPLY if item['control'] else MISREAD_REPLY)[form]
    if item['j']:
        return run_j2.next_reply(item, previous)
    if item['id'] == 'C21' and previous and previous.get('kind') in ('ASK', 'CLARIFY'):
        return 'fact', C21_REPLY
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
    tag = {'smoke': 'jfsmoke', 'all': 'jf1'}[mode]
    todo = [i for i in items() if mode == 'all' or i['id'] == 'J40']
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

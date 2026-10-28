"""Live check G4 for r1-jev-agreement (ROUND.md): turn 1 only, gpt-4o-mini, 1 rep, the app's settings (guard on),
code 8af7574b. Targets: j5 W40, j1 J46 (gold ASK). Controls (non-ASK items stating an irrelevant doubt): j5 W18, j4 S14,
j3 R21. All seen. Cost cap US$0.08.

Usage: python3 run_live.py   (tag ra2: W40, J46 rerun after the basis fix; never reruns)
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[2]
LOGS = RUN / 'docs/research-log'
DOTENV = RUN.parent.parent / 'netzoo_agent/.env'
HARNESS = LOGS / 'closed-menu-hybrid-2026-10-19/h4/run_live.py'
CODE = '59ebf9f1'
CAP_USD = 0.03
TAG = 'ra2'
SETS = {'j1': LOGS / 'jev-guard-2026-10-27/j1/items.json', 'j2': LOGS / 'jev-guard-2026-10-27/j2/items.json',
        'j3': LOGS / 'jev-j3-2026-10-27/j3/items.json', 'j4': LOGS / 'jev-j4-2026-10-27/j4/items.json', 'j5': LOGS / 'jev-j5-2026-10-28/j5/items.json'}
ITEMS = {'target': [('j5', 'W40'), ('j1', 'J46')]}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prompt(source: str, item: str) -> str:
    if source == 'bench':
        text = json.dumps(json.loads((LOGS / 'field-gold-2026-10-22/batch-core.json').read_text()))
        found = re.search(r'\{"id": "' + item + r'", "prompt": "((?:[^"\\]|\\.)*)"', text)
        return json.loads('"' + found.group(1) + '"')
    return next(i['prompt'] for i in json.loads(SETS[source].read_text())['single'] if i['id'] == item)


def spent() -> float:
    calls, jev = {}, 0.0
    for trace in HERE.glob(f'live/{TAG}/*/t*/trace-*.jsonl'):
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
            elif kind in ('core.jev_link', 'core.jev_condition', 'core.jev_answer', 'core.jev_data_first'):
                jev += ((payload.get('pick') or payload.get('typed') or payload.get('judged') or {}).get('cost') or 0)
    return sum(calls.values()) / 1e6 + jev


def check_code():
    if subprocess.run(['git', 'diff', '--quiet', CODE, '--', 'scripts', 'workflows', 'prompts', 'AGENTS.md'],
                      cwd=RUN).returncode:
        raise RuntimeError(f'code differs from {CODE}')


def main():
    check_code()
    sys.path.insert(0, str(HARNESS.parent))
    spec = importlib.util.spec_from_file_location('h4_live', HARNESS)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    env = live.environment(DOTENV)
    flags = {k: env.get(k) for k in ('NETZOO_JEV_GUARD', 'NETZOO_JEV_OVERLAP', 'NETZOO_JEV_FORMS')}
    if env.get('OPENROUTER_CAPABILITY_MODEL') != 'openai/gpt-4o-mini-2024-07-18' or set(flags.values()) != {'on'} \
            or not env.get('OPENROUTER_API_KEY'):
        raise RuntimeError(f'unexpected configuration {flags}')
    env.pop('OPENROUTER_CAPABILITY_EXTRA_TOKENS', None)
    env.update({'NETZOO_MAX_TASK_TOKENS': '30000', 'PYTHONUNBUFFERED': '1'})
    for name in ('NETZOO_JEV_OVERLAP_CACHE', 'NETZOO_JEV_FORMS_CACHE'):
        env.pop(name, None)
    todo = [(group, source, item) for group, rows in ITEMS.items() for source, item in rows]
    out = HERE / 'live' / TAG
    out.mkdir(parents=True, exist_ok=False)  # never reruns
    write(HERE / f'round-{TAG}.json', {'started_utc': datetime.now(timezone.utc).isoformat(), 'code': CODE,
                                       'items': todo, 'flags': flags, 'cap_usd': CAP_USD, 'runner_sha256':
                                       hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})

    def one(row):
        group, source, item = row
        sid = live.session_id(TAG, item, 1)
        turn = out / sid / 't1'
        turn.mkdir(parents=True)
        if spent() > CAP_USD:
            return {'item': item, 'group': group, 'end': 'cap'}
        check_code()
        args = ['--session', sid, '--keep-session', '--task', prompt(source, item)]
        with (turn / 'stdout.txt').open('xb') as stdout, (turn / 'stderr.txt').open('xb') as stderr:
            try:
                code = subprocess.call([live.PYTHON, '-c', live.BOOTSTRAP, *args], cwd=RUN,
                                       env={**env, 'NETZOO_PROFILE': sid, 'CJ_CARD_CAPTURE': str(turn / 'cards.json')},
                                       stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, timeout=600)
            except subprocess.TimeoutExpired:
                code = 'timeout'
        source_file = RUN / '.netzoo' / 'sessions' / f'{sid}.json'
        if source_file.exists():
            shutil.copyfile(source_file, turn / 'session.json')
        for events in (RUN / '.netzoo' / 'traces').glob('*/events.jsonl'):
            with events.open() as handle:
                first = json.loads(handle.readline() or '{}')
            if (first.get('payload') or {}).get('session_id') == sid:
                (turn / f'trace-{events.parent.name}.jsonl').write_text(events.read_text())
        record = {'item': item, 'group': group, 'source': source, 'session': sid, 'code': code}
        write(out / sid / 'job.json', record)
        return record

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(one, todo))
    for row in results:
        print(json.dumps(row))
    write(HERE / f'finished-{TAG}.json', {'finished_utc': datetime.now(timezone.utc).isoformat(),
                                          'conversations': len(results), 'spent_usd': round(spent(), 4)})
    print('spent US$', round(spent(), 4))


if __name__ == '__main__':
    main()

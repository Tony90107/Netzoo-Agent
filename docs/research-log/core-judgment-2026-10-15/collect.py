"""Verify every captured turn and build blind packets (no model calls). Adapted from the m3 collector."""
from __future__ import annotations
import argparse
import json
import random
import re
from pathlib import Path
from plan import DOTENV, HERE, SEED, digest, jobs, load_items, session_id, write_json
from run_live import environment

WAITING = 2  # a non-interactive turn stopped at the input wizard (m3 deviation 1)
WIZARD_STOP = 'Run the command again with --resume '
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
SECRET = re.compile(r'(?i)\b(?:sk-(?:or-v1-)?[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9_.-]{12,})')
PACKET = 20

def sanitize(text, sid='', root='', sha='', secrets=()):
    text = ANSI.sub('', text)
    for secret in sorted((s for s in secrets if len(s) >= 8), key=len, reverse=True):
        text = text.replace(secret, '[REDACTED SECRET]')
    text = SECRET.sub('[REDACTED SECRET]', text)
    for value, replacement in ((sid, '[SESSION]'), (root, '[CHECKOUT]'), (sha, '[CODE]')):
        if value: text = text.replace(value, replacement)
    return text

def read_turn(folder, n, task):
    path = folder / f't{n}'
    m = json.loads((path / 'manifest.json').read_text())
    if m['turn'] != n or m['request'] != task or m['mode'] != ('--session' if n == 1 else '--resume'):
        raise ValueError(f'Wrong turn identity: {folder.name}/{n}')
    required = {'stdout.txt', 'stderr.txt', 'cards.json', 'session.json', 'events.jsonl'}
    if m['exit'] not in (0, WAITING) or not required <= set(m['files']):
        raise ValueError(f'Incomplete capture: {folder.name}/{n}')
    if m['exit'] == WAITING and WIZARD_STOP not in (path / 'stdout.txt').read_text(errors='replace'):
        raise ValueError(f'Exit 2 without the input-wizard stop: {folder.name}/{n}')
    for name, sha in m['files'].items():
        if Path(name).name != name or digest(path / name) != sha:
            raise ValueError(f'Capture hash mismatch: {folder.name}/{n}/{name}')
    data = {name: (path / name).read_text(errors='replace') for name in required}
    data['session'] = json.loads(data['session.json'])
    data['events'] = [json.loads(x) for x in data['events.jsonl'].splitlines() if x.strip()]
    data['cards'] = json.loads(data['cards.json'])
    if not isinstance(data['cards'], list) or not data['events']:
        raise ValueError('Invalid card or empty trace capture')
    return data

def collect_session(folder, item, rep, meta, secrets=()):
    job = json.loads((folder / 'job.json').read_text())
    if len(job['codes']) != 1 or job['codes'][0] not in (0, WAITING):
        raise ValueError(f'Incomplete job: {folder.name}')
    if (job['item'], job['rep'], job['session']) != (item['id'], rep, folder.name):
        raise ValueError('Wrong job identity')
    cap = read_turn(folder, 1, item['prompt'])
    users = [m['content'] for m in cap['session'].get('messages', []) if m['role'] == 'user']
    if item['prompt'] not in '\n'.join(users):
        raise ValueError(f'Lost request context: {folder.name}')
    session, events = cap['session'], cap['events']
    plan = session.get('plan') or {}; decision = plan.get('decision') or {}
    check = decision.get('capability_check') or {}
    verdict = decision.get('run_verdict') or {}
    calls = (session.get('token_usage') or {}).get('calls', [])
    action = decision.get('action') or ''
    row = {'item': item['id'], 'rep': rep, 'class': item['class'], 'form': item['form'],
           'capture_verified': True, 'exit': job['codes'][0],
           'action': action, 'workflow': plan.get('workflow'), 'plan_status': plan.get('status'),
           'intent_type': decision.get('intent_type'), 'match_status': decision.get('capability_match_status'),
           'clarification_question': decision.get('clarification_question'),
           'run_verdict': {k: verdict.get(k) for k in ('verdict', 'held', 'reason') if k in verdict},
           'check_rows': [[r.get('kind'), r.get('status'), r.get('delivered_by'), (r.get('quote') or '')[:80]]
                          for r in check.get('requirements', [])],
           'unknown_domains': check.get('unknown_domains') or {},
           'gate_events': [e.get('event_type') for e in events if e.get('event_type', '').startswith('routing.run_')],
           'plans_created': sum(e.get('event_type') == 'plan.created' for e in events),
           'semantic_failed': sum(e.get('event_type') == 'routing.semantic_interpreter_failed' for e in events),
           'core': next((e['payload'] for e in reversed(events) if e.get('event_type') == 'core.decision'), None),
           'views': [e['payload'].get('reply_kind') for e in events if e.get('event_type') == 'core.view'],
           'check_calls': [[c.get('model'), c.get('status')] for c in calls if c.get('role') == 'capability_check'],
           'exceptions': [c.get('exception') for c in calls if c.get('exception')],
           'cost_usd': sum(c.get('cost_micro_usd') or 0 for c in calls) / 1e6}
    body = [f'Request: {item["prompt"]}',
            f'\nComplete recorded stdout:\n````text\n{cap["stdout.txt"]}\n````',
            f'\nComplete recorded stderr:\n````text\n{cap["stderr.txt"]}\n````',
            f'\nRecorded reply cards (empty means no card generated):\n````json\n{json.dumps(cap["cards"], ensure_ascii=False, indent=2)}\n````']
    return row, sanitize('\n'.join(body), folder.name, meta['worktree'], meta['sha'], secrets)

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('tag')
    p.add_argument('--dataset', type=Path, default=HERE / 'items.json')
    p.add_argument('--dotenv', type=Path, default=DOTENV)
    a = p.parse_args(); items = load_items(a.dataset); live = HERE / 'live' / a.tag
    meta = json.loads((live / 'round.json').read_text())
    if meta['dataset_sha256'] != digest(a.dataset) or meta['jobs'] != [list(j) for j in jobs(items)]:
        raise ValueError('Dataset or job plan differs from frozen run')
    env = environment(a.dotenv)
    secrets = [v for k, v in env.items() if any(x in k.upper() for x in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD'))]
    rows, blocks = {}, []
    for key, rep in jobs(items):
        sid = session_id(a.tag, key, rep)
        row, body = collect_session(live / sid, items[key], rep, meta, secrets)
        rows[sid] = row; blocks.append((sid, body))
    rng = random.Random(SEED); rng.shuffle(blocks)
    codes = rng.sample(range(100000, 999999), len(blocks))
    key_map, packets = {}, []
    for start in range(0, len(blocks), PACKET):
        sections = []
        for (sid, body), number in zip(blocks[start:start+PACKET], codes[start:start+PACKET]):
            code = f'S{number}'
            key_map[code] = {'session': sid, 'item': rows[sid]['item']}
            sections += [f'## {code}\n\n{body}\n']
        packets.append('\n'.join(sections))
    outputs = [live / 'structure.json', live / 'blind-key.json'] + [live / f'packet-{i:02}.md' for i in range(1, len(packets)+1)]
    if any(p.exists() for p in outputs): raise ValueError('Collection outputs already exist; archive them explicitly before rebuilding')
    write_json(outputs[0], rows); write_json(outputs[1], key_map)
    for path, body in zip(outputs[2:], packets): path.write_text(body)
    print(f'{len(rows)} captured sessions verified; {len(packets)} blind packets. Capture validation is not full replay.')

if __name__ == '__main__': main()

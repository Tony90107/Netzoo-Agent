"""Verify immutable capture for every CLI turn; construct blind packets without model calls."""
from __future__ import annotations
import argparse
import json
import random
import re
from pathlib import Path
from plan import HERE, SEED, digest, jobs, load_items, session_id, write_json
from run_live import environment

# Round m3 (2026-10-15): a non-interactive CLI turn that stops at the input wizard exits 2 after printing the
# question and this line (`cli/conversation.py`); that is the turn's complete answer, not a failed capture.
WAITING = 2
WIZARD_STOP = 'Run the command again with --resume '
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
SECRET = re.compile(r'(?i)\b(?:sk-(?:or-v1-)?[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9_.-]{12,})')

def sanitize(text, sid='', root='', sha='', secrets=()):
    text = ANSI.sub('', text)
    for secret in sorted((s for s in secrets if len(s) >= 8), key=len, reverse=True):
        text = text.replace(secret, '[REDACTED SECRET]')
    text = SECRET.sub('[REDACTED SECRET]', text)
    for value, replacement in ((sid, '[SESSION]'), (root, '[CHECKOUT]'), (sha, '[CODE]')):
        if value: text = text.replace(value, replacement)
    return text

def quote_match(task, words, quote):
    """Both quotes must exist verbatim in the actual request; background never qualifies."""
    task, words, quote = task.casefold(), words.strip().casefold(), (quote or '').strip().casefold()
    if not words or not quote or words not in task or quote not in task: return False
    # Compare all occurrences; the overlap must cover at least half the gold requirement.
    starts = lambda x: [m.start() for m in re.finditer(re.escape(x), task)]
    return any(min(a + len(words), b + len(quote)) - max(a, b) >= len(words) * .5
               for a in starts(words) for b in starts(quote))

def layers(task, requirements, check):
    results = [r for r in check.get('requirements', []) if r.get('kind') == 'result']
    out = []
    for requirement in requirements:
        matches = [r for r in results if quote_match(task, requirement['words'], r.get('quote'))]
        out.append({**requirement, 'understood': bool(matches),
                    'matched_quotes': [r['quote'] for r in matches],
                    'checked': [r.get('status') for r in matches]})
    return out

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
    turns = item.get('turns') or [item['prompt']]
    if len(job['codes']) != len(turns) or any(code not in (0, WAITING) for code in job['codes']):
        raise ValueError(f'Incomplete job: {folder.name}')
    if (job['item'], job['rep'], job['session'], job['expected_turns']) != (item['id'], rep, folder.name, len(turns)):
        raise ValueError('Wrong job identity')
    captures = [read_turn(folder, n, task) for n, task in enumerate(turns, 1)]
    for n, cap in enumerate(captures, 1):
        users = [m['content'] for m in cap['session'].get('messages', []) if m['role'] == 'user']
        # Missing last-turn persistence is visible in output, but cannot masquerade as complete evidence.
        if len(users) < n or not all(t in '\n'.join(users) for t in turns[:n]):
            raise ValueError(f'Lost request context: {folder.name}/t{n}')
    final = captures[-1]; session = final['session']; events = final['events']
    plan = session.get('plan') or {}; decision = plan.get('decision') or {}
    check = decision.get('capability_check') or {}
    verdict = decision.get('run_verdict') or {}
    if not check and verdict:
        check = {'requirements': [{'kind': 'result', **r} for r in verdict.get('results', [])]}
    calls = (session.get('token_usage') or {}).get('calls', [])
    planned = [e['payload'] for e in events if e.get('event_type') == 'plan.created']
    gate = [e for e in events if e.get('event_type') in {'routing.run_held', 'routing.run_replanned', 'routing.run_check_shadow'}]
    action = decision.get('action') or ''
    # A run on mixed/negative/unknown requirements, or without an approving verdict, needs primary review.
    bad_gate = action.startswith('run_') and (any(r['expect'] in {'not_supported', 'needs_fact'} for r in item['requirements']) or verdict.get('verdict') != 'agrees')
    row = {'item': item['id'], 'rep': rep, 'family': item['family'], 'form': item['form'],
           'capture_verified': True, 'capture_turns': len(captures), 'replayed': False,
           'action': action, 'workflow': plan.get('workflow'), 'plan_status': plan.get('status'),
           'steps': plan.get('steps', []), 'trace_plans': planned, 'gate_events': gate,
           'run_verdict': verdict, 'bad_gate_candidate': bad_gate,
           'layers': layers('\n'.join(turns), item['requirements'], check),
           'check_calls': [[c.get('model'), c.get('status')] for c in calls if c.get('role') == 'capability_check'],
           'errors': [c.get('exception') or c.get('status') for c in calls if c.get('exception') or c.get('status') in {'error', 'failed'}],
           'cost_usd': sum(c.get('cost_micro_usd') or 0 for c in calls) / 1e6}
    body = ['Requirements to judge (user words):'] + [f'R{i}: {r["words"]}' for i, r in enumerate(item['requirements'], 1)]
    for n, (task, cap) in enumerate(zip(turns, captures), 1):
        body += [f'\nRequest (turn {n}): {task}',
                 f'\nComplete recorded stdout (turn {n}):\n````text\n{cap["stdout.txt"]}\n````',
                 f'\nComplete recorded stderr (turn {n}):\n````text\n{cap["stderr.txt"]}\n````',
                 f'\nRecorded reply cards (turn {n}; empty means no card generated):\n````json\n{json.dumps(cap["cards"], ensure_ascii=False, indent=2)}\n````']
    body += ['Judge the final turn using the preceding context.']
    return row, sanitize('\n'.join(body), folder.name, meta['worktree'], meta['sha'], secrets)

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('tag')
    p.add_argument('--dataset', type=Path, default=HERE / 'heldout.json')
    p.add_argument('--dotenv', type=Path, default=HERE.parents[2] / '.env')
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
    for start in range(0, len(blocks), 25):
        sections = []
        for (sid, body), number in zip(blocks[start:start+25], codes[start:start+25]):
            code = f'S{number}'
            key_map[code] = {'session': sid, 'gold': items[rows[sid]['item']]['requirements']}
            sections += [f'## {code}\n\n{body}\n']
        packets.append('\n'.join(sections))
    outputs = [live / 'structure.json', live / 'blind-key.json'] + [live / f'packet-{i:02}.md' for i in range(1, len(packets)+1)]
    if any(p.exists() for p in outputs): raise ValueError('Collection outputs already exist; archive them explicitly before rebuilding')
    write_json(outputs[0], rows); write_json(outputs[1], key_map)
    for path, body in zip(outputs[2:], packets): path.write_text(body)
    print(f'{len(rows)} captured sessions verified; {len(packets)} blind packets. Capture validation is not full replay.')

if __name__ == '__main__': main()

"""Score the live check (run_live.py tag jo1): each turn's call, Jev's overlap reads, the group question and reply,
and whether any reply still says "overlapping memberships". Usage: python3 score_live.py [tag]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = sys.argv[1] if len(sys.argv) > 1 else 'jo1'
GOLD = {'Q01': 'DO', 'Q02': 'DO', 'Q13': 'DECLINE', 'Q18': 'DECLINE', 'Q29': 'DO', 'Q36': 'DO', 'Q38': 'DO',
        'H26': 'DO', 'J01': 'DO', 'JN8': 'DECLINE', 'ON5': 'DECLINE', 'QN5': 'DECLINE', 'SN1': 'DECLINE'}
J2G = {'Q01': 'DECLINE', 'Q02': 'DECLINE', 'Q13': 'DECLINE', 'Q18': 'DO', 'Q29': 'DECLINE', 'Q36': 'DECLINE',
       'Q38': 'DECLINE'}  # RESULTS-J2.md arm G finals
WRONG = 'none returns overlapping memberships'


def turn(folder: Path) -> dict:
    core, reads, text = None, [], ''
    for trace in sorted(folder.glob('trace-*.jsonl')):
        for line in trace.read_text().splitlines():
            row = json.loads(line)
            if row['event_type'] == 'core.decision':
                core = row['payload']
            elif row['event_type'] == 'core.jev_overlap':
                reads += row['payload']['reads']
    stdout = folder / 'stdout.txt'
    text = stdout.read_text(errors='replace') if stdout.exists() else ''
    asked = bool(core) and any(f.get('depends_on') == 'group_membership' for f in core.get('facts') or [])
    return {'kind': (core or {}).get('kind'), 'basis': (core or {}).get('basis'), 'asked_groups': asked,
            'jev': [round((r.get('read') or {}).get('probabilities', {}).get('overlapping', -1), 2) if 'error' not in
                    (r.get('read') or {}) else 'error' for r in reads],
            'overlap_reason': WRONG in text}


rows = []
for folder in sorted((HERE / 'live' / TAG).iterdir()):
    job = json.loads((folder / 'job.json').read_text())
    turns = [turn(t) for t in sorted(folder.glob('t*')) if t.is_dir()]
    item = job['item']
    final = turns[-1]['kind'] if turns else None
    rows.append({'item': item, 'gold': GOLD[item], 'j2g': J2G.get(item), 'final': final, 'right': final == GOLD[item],
                 'sent': job['sent'], 'end': job['end'], 'turns': turns})
for row in rows:
    calls = ' -> '.join(f"{t['kind']}/{t['basis']}" + (' [Q:groups]' if t['asked_groups'] else '')
                        + (f" jev{t['jev']}" if t['jev'] else '') + (' [overlap reason]' if t['overlap_reason'] else '')
                        for t in row['turns'])
    print(f"{row['item']:4} gold {row['gold']:7} j2g {str(row['j2g']):7} final {str(row['final']):7} "
          f"{'RIGHT' if row['right'] else 'wrong'} | sent {row['sent']} | {calls}")
control = [r for r in rows if r['item'] in ('JN8', 'ON5', 'QN5', 'SN1')]
other = [r for r in rows if r not in control]
print('controls asked the group question:', sum(any(t['asked_groups'] for t in r['turns']) for r in control), 'of', len(control))
print('controls final DECLINE:', sum(r['final'] == 'DECLINE' for r in control), 'of', len(control))
print('not-overlap finals right:', sum(r['right'] for r in other), 'of', len(other))
j2 = [r for r in other if r['j2g']]
print('j2 items right: jo1', sum(r['right'] for r in j2), 'vs j2g', sum(r['j2g'] == r['gold'] for r in j2), 'of', len(j2))
print('not-overlap items whose final reply says the overlap reason:',
      [r['item'] for r in other if r['turns'] and r['turns'][-1]['overlap_reason']])
(HERE / f'score-{TAG}.json').write_text(json.dumps(rows, indent=1))

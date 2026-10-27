"""Score the forms live check (run_live.py, tag jf1): each turn's call, the form question asked, Jev's forms reads, and
whether a final reply still says a form reason. Usage: python3 score_live.py [tag]"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_live import CONTROLS, EXPECTED, FORMS  # noqa: E402

TAG = sys.argv[1] if len(sys.argv) > 1 else 'jf1'
REASONS = {'time_model': 'from one time point to the next', 'spatial': 'neighbours',
           'group_membership': 'overlapping memberships'}


def turn(folder: Path) -> dict:
    core, reads = None, []
    for trace in sorted(folder.glob('trace-*.jsonl')):
        for line in trace.read_text().splitlines():
            row = json.loads(line)
            if row['event_type'] == 'core.decision':
                core = row['payload']
            elif row['event_type'] in ('core.jev_forms', 'core.jev_overlap'):
                reads += [{'attr': r.get('attr', 'group_membership'), 'doubted': r['doubted'],
                           'error': 'error' in (r.get('read') or {})} for r in row['payload']['reads']]
    text = (folder / 'stdout.txt').read_text(errors='replace') if (folder / 'stdout.txt').exists() else ''
    asked = [f['depends_on'] for f in (core or {}).get('facts') or [] if f.get('depends_on') in FORMS]
    return {'kind': (core or {}).get('kind'), 'basis': (core or {}).get('basis'), 'asked': asked, 'reads': reads,
            'reasons': [name for name, words in REASONS.items() if words in text]}


rows = []
for folder in sorted((HERE / 'live' / TAG).iterdir()):
    job = json.loads((folder / 'job.json').read_text())
    turns = [turn(t) for t in sorted(folder.glob('t*')) if t.is_dir()]
    item = job['item']
    final = turns[-1]['kind'] if turns else None
    rows.append({'item': item, 'control': item in CONTROLS, 'expected': EXPECTED[item], 'final': final,
                 'right': final == EXPECTED[item], 'sent': job['sent'], 'turns': turns})
for row in rows:
    calls = ' -> '.join(f"{t['kind']}/{t['basis']}" + (f" [Q:{','.join(t['asked'])}]" if t['asked'] else '')
                        + (f" jev{[(r['attr'][:4], r['doubted']) for r in t['reads']]}" if t['reads'] else '')
                        + (f" [reason:{','.join(t['reasons'])}]" if t['reasons'] else '') for t in row['turns'])
    print(f"{row['item']:5} {'CTRL' if row['control'] else 'mis ':4} expected {row['expected']:8} final {str(row['final']):9}"
          f"{'RIGHT' if row['right'] else 'wrong'} | {row['sent']} | {calls}")
control = [r for r in rows if r['control']]
other = [r for r in rows if not r['control']]
print('controls asked a form question:', [r['item'] for r in control if any(t['asked'] for t in r['turns'])])
print('controls final right:', sum(r['right'] for r in control), 'of', len(control))
print('misread items asked a form question:', sum(any(t['asked'] for t in r['turns']) for r in other), 'of', len(other))
print('misread items final right:', sum(r['right'] for r in other), 'of', len(other))
print('Jev read errors:', sum(r['error'] for row in rows for t in row['turns'] for r in t['reads']))
(HERE / f'score-{TAG}.json').write_text(json.dumps(rows, indent=1))

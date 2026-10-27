"""Score the answer-binding live check (run_live.py, tag ja1): per turn the call, the form questions asked, how the next
reply bound (code `task.answers_bound`, Jev `task.answers_read`), repeats, and the final against the item's gold."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_live import expected, items  # noqa: E402

TAG = sys.argv[1] if len(sys.argv) > 1 else 'jd1'
FORMS = ('group_membership', 'time_model', 'spatial', 'input_network')
by_id = {i['id']: i for i in items()}


def events(turn: Path, name: str) -> list[dict]:
    return [json.loads(line)['payload'] for trace in sorted(turn.glob('trace-*.jsonl'))
            for line in trace.read_text().splitlines()
            if f'"{name}"' in line and json.loads(line).get('event_type') == name]


rows = []
for folder in sorted((HERE / 'live' / TAG).iterdir()):
    job = json.loads((folder / 'job.json').read_text())
    turns = sorted((t for t in folder.glob('t*') if t.is_dir()), key=lambda p: int(p.name[1:]))
    out = []
    for turn in turns:
        core = (events(turn, 'core.decision') or [{}])[-1]
        out.append({'kind': core.get('kind'), 'basis': core.get('basis'),
                    'asked': [f['depends_on'] for f in core.get('facts') or [] if f.get('depends_on') in FORMS],
                    'code_bound': [f for e in events(turn, 'task.answers_bound') for f in e.get('facts') or []],
                    'jev_bound': [f for e in events(turn, 'task.answers_read') for f in e.get('facts') or []],
                    'jev_reads': [(r['dim'], r['value']) for e in events(turn, 'task.answers_read') for r in e['reads']]})
    item = by_id[job['item']]
    final = out[-1]['kind'] if out else None
    asked_turns = [i for i, t in enumerate(out) if t['asked']]
    gold = expected(item, job['sent'])
    data_first = [e.get('action') for t in turns for e in events(t, 'core.jev_data_first')]
    out[-1]['data_first'] = data_first
    rows.append({'item': job['item'], 'expected': gold, 'final': final, 'right': final == gold, 'data_first': data_first,
                 'sent': job['sent'], 'repeats': max(0, len(asked_turns) - 1), 'turns': out})
for r in rows:
    calls = ' -> '.join(f"{t['kind']}/{t['basis']}" + (f" [Q:{','.join(t['asked'])}]" if t['asked'] else '')
                        + (f" code{t['code_bound']}" if t['code_bound'] else '')
                        + (f" jev{t['jev_reads']}" if t['jev_reads'] else '') for t in r['turns'])
    print(f"{r['item']:4} expected {r['expected']:8} final {str(r['final']):9}{'RIGHT' if r['right'] else 'wrong'} "
          f"repeats {r['repeats']} | {r['sent']} | {calls} | data_first {r['data_first']}")
asked = [r for r in rows if any(t['asked'] for t in r['turns'])]
print('items asked a form question:', len(asked), 'of', len(rows))
print('of those, answer bound by Jev:', sum(any(t['jev_bound'] for t in r['turns']) for r in asked),
      '| by code:', sum(any(t['code_bound'] for t in r['turns']) for r in asked))
print('form question asked again in a later turn:', [r['item'] for r in rows if r['repeats']])
print('final right:', sum(r['right'] for r in rows), 'of', len(rows))
(HERE / f'score-{TAG}.json').write_text(json.dumps(rows, indent=1))

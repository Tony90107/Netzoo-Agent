"""Offline replay: re-run decide_core on a round's recorded final decisions (no model calls).

Usage: replay_core.py TAG NEW_TAG   -> live/NEW_TAG/structure.json with each row's `core` recomputed by the
decide_core of this checkout (the recorded routing, check and verdict are unchanged).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from plan import HERE, write_json

sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core  # noqa: E402

def main(tag, new):
    live = HERE / 'live' / tag; out = HERE / 'live' / new
    rows = json.loads((live / 'structure.json').read_text())
    for sid, row in rows.items():
        turn = live / sid / 't1'
        session = json.loads((turn / 'session.json').read_text())
        decision = TaskDecision.model_validate((session.get('plan') or {}).get('decision'))
        task = [m['content'] for m in session['messages'] if m['role'] == 'user'][-1]
        reason = (row['core'] or {}).get('evidence', {}).get('reason_code', '')
        row['recorded_core'] = row['core']
        row['core'] = decide_core(decision, task, reason_code=reason).model_dump(mode='json')
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'structure.json', rows)
    changed = {r['item']: [r['recorded_core']['kind'], r['core']['kind']] for r in rows.values()
               if r['recorded_core']['kind'] != r['core']['kind'] or r['recorded_core'].get('partial') != r['core'].get('partial')}
    print(f'{len(rows)} replayed; changed: {changed}')

if __name__ == '__main__': main(*sys.argv[1:3])

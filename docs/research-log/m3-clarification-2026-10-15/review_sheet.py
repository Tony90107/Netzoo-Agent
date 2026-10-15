"""Primary-review sheet: gold, blind labels and the recorded evidence for each blind code (no model calls).

Usage: review_sheet.py m3 [CODE ...]   (default: every code in to-review.json)
"""
from __future__ import annotations

import json
import re
import sys

from plan import HERE

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def _final_text(folder, turns: int) -> str:
    out = (folder / f't{turns}' / 'stdout.txt').read_text(errors='replace')
    return ANSI.sub('', out).strip()


def sheet(tag: str, codes: list[str]) -> str:
    live = HERE / 'live' / tag
    rows = json.loads((live / 'structure.json').read_text())
    key = json.loads((live / 'blind-key.json').read_text())
    labels = json.loads((live / 'labels-A.json').read_text())
    items = {item['id']: item for item in json.loads((HERE / 'heldout.json').read_text())['items']}
    blocks = []
    for code in codes:
        sid = key[code]['session']
        row, item, label = rows[sid], items[rows[sid]['item']], labels[code]
        verdict = row.get('run_verdict') or {}
        plans = [{'workflow': p.get('workflow'), 'status': p.get('status'), 'missing': p.get('missing_inputs'),
                  'provided': {e['field']: e.get('value') for e in p.get('evidence', [])
                               if e.get('status') not in ('missing',) and e.get('value') not in (None, '', [])},
                  'steps': [(step.get('action'), step.get('arguments')) for step in p.get('steps', [])]}
                 for p in row.get('trace_plans', [])][-1:]
        lines = [f'### {code}  {row["item"]}-{row["rep"]}  family={item["family"]} form={item["form"]}',
                 *(f'- R{i}: expect={g["expect"]} by={g.get("by")} words="{g["words"]}"'
                   + (f' deciding_fact="{g["deciding_fact"]}"' if g.get('deciding_fact') else '')
                   + f'  -> blind {v}' for i, (g, v) in enumerate(zip(item['requirements'], label['R']), 1)),
                 f'- contradiction: {label["contradiction"]}',
                 f'- action={row["action"]} workflow={row.get("workflow")} plan_status={row.get("plan_status")} '
                 f'verdict={verdict.get("verdict")} held={verdict.get("held")} gate_candidate={row["bad_gate_candidate"]}',
                 f'- read: {[(l["understood"], l["checked"]) for l in row["layers"]]}  checks={row["check_calls"]}',
                 f'- plan: {plans}',
                 *(f'- turn {n}: {t}' for n, t in enumerate(item.get('turns') or [item['prompt']], 1)),
                 '```text', _final_text(live / sid, row['capture_turns'])[-3500:], '```']
        blocks.append('\n'.join(lines))
    return '\n\n'.join(blocks)


if __name__ == '__main__':
    tag, *codes = sys.argv[1:]
    if not codes:
        codes = json.loads((HERE / 'live' / tag / 'to-review.json').read_text())
    print(sheet(tag, codes))

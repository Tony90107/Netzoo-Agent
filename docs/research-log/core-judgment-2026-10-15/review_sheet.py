"""Primary-review sheet: gold, blind label and recorded evidence per blind code (no model calls).

Usage: review_sheet.py TAG [CODE ...]   (default: every code in to-review.json)
"""
from __future__ import annotations
import json
import re
import sys
from plan import HERE

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

def sheet(tag, codes):
    live = HERE / 'live' / tag
    rows = json.loads((live / 'structure.json').read_text())
    key = json.loads((live / 'blind-key.json').read_text())
    labels = json.loads((live / 'labels-A.json').read_text())
    items = {i['id']: i for i in json.loads((HERE / 'items.json').read_text())['items']}
    blocks = []
    for code in codes:
        sid = key[code]['session']; row, item, label = rows[sid], items[key[code]['item']], labels[code]
        gold = ' '.join(f'{k}="{item[k]}"' for k in ('deciding_fact', 'if_yes', 'if_no', 'missing_core') if item.get(k))
        out = ANSI.sub('', (live / sid / 't1' / 'stdout.txt').read_text(errors='replace')).strip()
        blocks.append('\n'.join([
            f'### {code}  {item["id"]}  class={item["class"]} form={item["form"]} gold_workflows={item["workflows"]}',
            f'- gold: {item["reason"]} {gold}',
            f'- blind: {json.dumps(label, ensure_ascii=False)}',
            f'- action={row["action"]} workflow={row["workflow"]} status={row["plan_status"]} intent={row["intent_type"]} '
            f'match={row["match_status"]} verdict={row["run_verdict"]} gates={row["gate_events"]}',
            f'- check rows: {row["check_rows"]}  unknown: {row["unknown_domains"]}  checks={row["check_calls"]}',
            f'- request: {item["prompt"]}',
            '```text', out[-3000:], '```']))
    return '\n\n'.join(blocks)

if __name__ == '__main__':
    tag, *codes = sys.argv[1:]
    print(sheet(tag, codes or json.loads((HERE / 'live' / tag / 'to-review.json').read_text())))

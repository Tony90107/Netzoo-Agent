"""Print one round's readings compactly: show.py TAG FILE ID [ID ...]"""
import json, sys
from p1common import HERE

def compact(p):
    if isinstance(p, dict):
        if p.get('status') == 'not_stated':
            return None
        out = {k: compact(v) for k, v in p.items()}
        return {k: v for k, v in out.items() if v not in (None, [], '', {}, False)}
    if isinstance(p, list):
        return [compact(x) for x in p]
    return p

tag, name, *ids = sys.argv[1:]
rows = json.loads((HERE / 'live' / tag / f'{name}.json').read_text())['rows']
items = {i['id']: i for i in json.loads((HERE / 'dev_items.json').read_text())['items']}
for row in rows:
    if row['id'] in ids or not ids:
        print('=' * 100)
        print(row['id'], row.get('class'), '->', row['kind'], row['workflows'], row['questions'], row['reasons'][:2])
        if row['id'] in items:
            print(items[row['id']]['prompt'])
        print(json.dumps(compact(row['payload']), ensure_ascii=False))
        print('dropped:', row['dropped'])

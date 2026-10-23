"""Per-turn summary of the P3 multi-turn live check (live/p3live): each turn's call, what it asked, the task state the
session saved after it, and the reply; REPLIES-P3.md gets the replies in full.

Usage: python3 analyze_p3.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = "I have asked about this request twice already"


def turn_rows(folder: Path):
    for turn in sorted(folder.glob('t*'), key=lambda p: int(p.name[1:])):
        manifest = json.loads((turn / 'manifest.json').read_text())
        session = json.loads((turn / 'session.json').read_text()) if (turn / 'session.json').exists() else {}
        core = (((session.get('plan') or {}).get('decision') or {}).get('core') or {})
        replies = [m['content'] for m in session.get('messages', []) if m['role'] == 'assistant']
        task = session.get('task_state') or {}
        calls = (session.get('token_usage') or {}).get('calls', [])
        yield {
            'turn': turn.name, 'request': manifest['request'], 'exit': manifest['exit'],
            'kind': core.get('kind'), 'basis': core.get('basis'),
            'asked': [(f.get('depends_on') or ('count' if f.get('by_code') else 'agent'), f.get('question'))
                      for f in core.get('facts') or []],
            'clarify': (core.get('clarify') or {}).get('question'),
            'clarification': (core.get('evidence') or {}).get('clarification'),
            'task': {'id': task.get('task_id'), 'status': task.get('status'), 'rounds': task.get('rounds'),
                     'pending': [(q['source'], q['what']) for q in task.get('pending', [])],
                     'facts': [(f['source'], f['what'], f['value'], f['status']) for f in task.get('facts', [])]},
            'reply': replies[-1] if replies else '', 'exhausted_note': bool(replies) and replies[-1].startswith(NOTE),
            'cost_usd': sum(c.get('cost_micro_usd') or 0 for c in calls) / 1e6,
        }


def main():
    items = {x['id']: x for x in json.loads((HERE / 'items-p3.json').read_text())['items']}
    out = ['# P3 多輪 live 回覆全文（live/p3live）', '']
    for folder in sorted((HERE / 'live' / 'p3live').iterdir()):
        job = json.loads((folder / 'job.json').read_text()) if (folder / 'job.json').exists() else {}
        key = folder.name.split('-', 2)[2].rsplit('-', 1)[0]
        print(f"== {key} [{job.get('end')}] expect: {items[key]['expect']}")
        out += [f'## {key}（{job.get("end")}）', '', f'預期：{items[key]["expect"]}', '']
        for row in turn_rows(folder):
            print(f"  {row['turn']} exit={row['exit']} {row['kind']}/{row['basis']} note={row['exhausted_note']} "
                  f"${row['cost_usd']:.4f}")
            print(f"     asked: {row['asked'] or row['clarify']}  clarification={row['clarification']}")
            print(f"     task: {row['task']}")
            print(f"     reply: {row['reply'][:240]!r}")
            out += [f"### {row['turn']}：{row['kind']}/{row['basis']}", '', f"**使用者**：{row['request']}", '',
                    f"**task_state**：`{json.dumps(row['task'], ensure_ascii=False)}`", '', '**回覆**：', '',
                    *[f'> {line}' if line else '>' for line in row['reply'].splitlines()], '']
    (HERE / 'REPLIES-P3.md').write_text('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()

"""Held-out round h5 scoring (ROUND.md, frozen before the runs; no model calls).

Usage: python3 score.py facts     -> fact-sheet.json (blind: ask items whose call is ASK, shuffled) and fact-key.json
       python3 score.py score     -> score.json and a printed table (needs facts-checked.json for ask items)

facts-checked.json (the blind labeller's): {"<sheet id>": true|false, ...} -- does a question target the deciding fact.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = 'h5main'
CLASSES = ('do', 'dont', 'ask', 'vague')
EXPECTED = {'do': 'DO', 'dont': 'DECLINE', 'ask': 'ASK', 'vague': 'CLARIFY'}
SEED = 1021


def norm(names):
    return {str(n).strip().upper().replace('LIONESS ', 'LIONESS-') for n in names or []}


def outcome(item, core, right_fact=None):
    """h4's `score_core.outcome` without its credit for a run whose input check settles the deciding fact: the user
    decided on 2026-10-21 that such a fact is asked first."""
    cls, kind = item['class'], core['kind']
    offered, gold = norm(core.get('workflows')), norm(item['workflows'])
    if cls == 'do':
        if kind == 'DO' and not core.get('partial'):
            if not offered or offered <= gold:
                return 'correct'
            return 'extra_options' if offered & gold else 'wrong_workflow'
        if kind in ('ASK', 'CLARIFY'):
            return 'needless_question'
        return 'unchecked' if kind == 'UNCHECKED' else 'false_refusal'
    if cls == 'dont':
        if kind == 'DECLINE':
            return 'correct'
        if kind == 'DO':
            return 'partly_accept' if core.get('partial') else 'false_accept'
        return 'undecided'
    if kind == EXPECTED[cls]:
        return 'wrong_fact' if cls == 'ask' and right_fact is not True else 'correct'
    if kind in ('ASK', 'CLARIFY'):
        return 'wrong_question_kind'
    if kind == 'UNCHECKED':
        return 'unchecked'
    return 'committed_without_asking' if kind == 'DO' else 'refused_without_asking'


def items():
    return {x['id']: x for x in json.loads((HERE / 'items.json').read_text())['items']}


def sessions():
    """(item, rep) -> the recorded core call (None when the turn recorded none)."""
    found = {}
    for job in sorted((HERE / 'live' / TAG).glob('*/job.json')):
        meta = json.loads(job.read_text())
        events = job.parent / 't1' / 'events.jsonl'
        core = None
        if events.exists():
            for line in events.read_text().splitlines():
                if line.strip() and json.loads(line).get('event_type') == 'core.decision':
                    core = json.loads(line)['payload']
        found[(meta['item'], meta['rep'])] = core
    return found


def facts():
    pool, key = [], {}
    for (item, rep), core in sessions().items():
        if items()[item]['class'] == 'ask' and core and core['kind'] == 'ASK':
            pool.append((item, rep, [f['question'] for f in core.get('facts') or []]))
    random.Random(SEED).shuffle(pool)
    sheet = []
    for index, (item, rep, questions) in enumerate(pool, 1):
        sid = f'F{index:02d}'
        key[sid] = f'{item}-{rep}'
        sheet.append({'id': sid, 'request': items()[item]['prompt'], 'deciding_fact': items()[item]['deciding_fact'],
                      'questions_asked': questions})
    (HERE / 'fact-sheet.json').write_text(json.dumps(sheet, indent=1, ensure_ascii=False))
    (HERE / 'fact-key.json').write_text(json.dumps(key, indent=1))
    print(f'{len(sheet)} ask sessions on the blind fact sheet')


def score():
    labelled = json.loads((HERE / 'facts-checked.json').read_text()) if (HERE / 'facts-checked.json').exists() else {}
    key = json.loads((HERE / 'fact-key.json').read_text()) if (HERE / 'fact-key.json').exists() else {}
    right = {key[sid]: value for sid, value in labelled.items()}
    known, rows = items(), []
    for (item, rep), core in sorted(sessions().items()):
        result = outcome(known[item], core or {'kind': 'NONE'}, right.get(f'{item}-{rep}'))
        rows.append({'item': item, 'rep': rep, 'class': known[item]['class'], 'form': known[item]['form'],
                     'kind': (core or {}).get('kind'), 'basis': (core or {}).get('basis'),
                     'workflows': (core or {}).get('workflows'), 'outcome': result})
    by = defaultdict(dict)
    for row in rows:
        by[row['item']][row['rep']] = row['outcome'] == 'correct'
    table = {}
    for cls in (*CLASSES, 'all'):
        mine = [k for k in by if cls == 'all' or known[k]['class'] == cls]
        reps = {rep: sum(by[k].get(rep, False) for k in mine) for rep in (1, 2)}
        table[cls] = {'n': len(mine), 'rep1': reps[1], 'rep2': reps[2], 'mean': (reps[1] + reps[2]) / 2 / len(mine),
                      'pass2': sum(all(by[k].get(r, False) for r in (1, 2)) for k in mine)}
    errors = Counter((row['class'], row['outcome']) for row in rows if row['outcome'] != 'correct')
    (HERE / 'score.json').write_text(json.dumps({'table': table, 'errors': {f'{c}:{o}': n for (c, o), n in errors.items()},
                                                 'rows': rows}, indent=1))
    for cls, t in table.items():
        print(f"{cls:6} n={t['n']:2} rep1 {t['rep1']:2} rep2 {t['rep2']:2} mean {t['mean']:.1%} pass^2 {t['pass2']}")
    for (cls, out), n in sorted(errors.items()):
        print(f'  {n:2} {cls:6} {out}')


if __name__ == '__main__':
    {'facts': facts, 'score': score}[sys.argv[1]]()

"""Hybrid blind round h4 (copied from the h3 harness unchanged but for this note): the blind items, one run each.

Changes from the copy: items are read from this folder's items.json (any count, ids H01...), no dev items are left
out, and sessions are named hb-TAG-ID-REP so they never meet a core-judgment session.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # this folder is one level deeper than core-judgment's
_WORKTREES = ROOT.parent if ROOT.parent.name == '.worktrees' else ROOT.parent / '.worktrees'
WORKTREE = _WORKTREES / 'netzoo-core-p0-run'  # clean run worktree, checked out at each phase's frozen commit
DOTENV = _WORKTREES.parent / 'netzoo_agent' / '.env'  # the main checkout's; worktrees carry none
PYTHON = '/opt/anaconda3/bin/python'
SEED = 1015
CLASSES = ('do', 'dont', 'ask', 'vague')
FORMS = ('named', 'goal', 'run')
WORKFLOWS = {'PANDA', 'PUMA', 'LIONESS-PANDA', 'LIONESS-PUMA', 'LIONESS-COEXPRESSION', 'LIONESS-DRAGON',
             'DRAGON', 'BONOBO', 'CONDOR', 'COBRA', 'OTTER', 'GIRAFFE', 'SAMBAR'}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_items(path=HERE / 'items.json', expected=None):
    raw = json.loads(Path(path).read_text())['items']
    expected = expected or len(raw)
    if len(raw) != expected or len({x['id'] for x in raw}) != expected:
        raise ValueError(f'Expected {expected} unique items')
    items = {}
    for item in raw:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', item['id']):
            raise ValueError('Unsafe item id')
        if item.get('class') not in CLASSES or item.get('form') not in FORMS:
            raise ValueError(f"Bad class/form: {item['id']}")
        if not isinstance(item.get('prompt'), str) or not item['prompt'].strip():
            raise ValueError(f"Empty prompt: {item['id']}")
        if not isinstance(item.get('workflows'), list) or {w.upper() for w in item['workflows']} - WORKFLOWS:
            raise ValueError(f"Unknown workflow: {item['id']}")
        if item['class'] == 'do' and not item['workflows']:
            raise ValueError(f"A do item names its fitting workflows: {item['id']}")
        if item['class'] == 'ask' and not item.get('deciding_fact'):
            raise ValueError(f"An ask item needs deciding_fact: {item['id']}")
        if item['class'] == 'vague' and not item.get('missing_core'):
            raise ValueError(f"A vague item needs missing_core: {item['id']}")
        items[item['id']] = item
    return items

DEV = frozenset()
"""No item of the held-out set was seen before its round."""

def jobs(items):
    return [(key, 1) for key in sorted(items) if key not in DEV]

def session_id(tag, key, rep):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', tag):
        raise ValueError('Unsafe round tag')
    return f'hb-{tag}-{key}-{rep}'

def write_json(path, data, exclusive=True):
    with Path(path).open('x' if exclusive else 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

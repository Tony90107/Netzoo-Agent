"""Core-judgment round: 60 single-turn items, one run each; loading items is explicit, never an import side effect."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
_WORKTREES = ROOT.parent if ROOT.parent.name == '.worktrees' else ROOT.parent / '.worktrees'
WORKTREE = _WORKTREES / 'netzoo-core-p0-run'  # clean run worktree at the phase-0 commit; cj1 ran netzoo-core-score
DOTENV = _WORKTREES.parent / 'netzoo_agent' / '.env'  # the main checkout's; worktrees carry none
PYTHON = '/opt/anaconda3/bin/python'
SEED = 1015
CLASSES = ('do', 'dont', 'ask', 'vague')
FORMS = ('named', 'goal', 'run')
WORKFLOWS = {'PANDA', 'PUMA', 'LIONESS-PANDA', 'LIONESS-PUMA', 'LIONESS-COEXPRESSION', 'LIONESS-DRAGON',
             'DRAGON', 'BONOBO', 'CONDOR', 'COBRA', 'OTTER', 'GIRAFFE', 'SAMBAR'}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_items(path=HERE / 'items.json', expected=60):
    raw = json.loads(Path(path).read_text())['items']
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

DEV = frozenset({'C01', 'C02', 'C03', 'C05'})
"""Items seen in round cj1 (stopped); the bench is the other 56 (spec 2026-10-15 section 8)."""

def jobs(items):
    return [(key, 1) for key in sorted(items) if key not in DEV]

def session_id(tag, key, rep):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', tag):
        raise ValueError('Unsafe round tag')
    return f'cj-{tag}-{key}-{rep}'

def write_json(path, data, exclusive=True):
    with Path(path).open('x' if exclusive else 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

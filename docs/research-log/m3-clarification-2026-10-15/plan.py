"""Frozen deterministic round; loading heldout is explicit, never an import side effect."""
from __future__ import annotations
import hashlib
import json
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKTREE = ROOT.parent / '.worktrees' / 'netzoo-m3-candidate'
PYTHON = '/opt/anaconda3/bin/python'
SEED = 1510
EXPECT = {'supported', 'with_step', 'needs_input', 'not_supported', 'needs_fact'}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_items(path=HERE / 'heldout.json', expected=120):
    raw = json.loads(Path(path).read_text())['items']
    if len(raw) != expected or len({x['id'] for x in raw}) != expected:
        raise ValueError(f'Expected {expected} unique items')
    items = {}
    for item in raw:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', item['id']):
            raise ValueError('Unsafe item id')
        turns = item.get('turns') or [item['prompt']]
        if not turns or not all(isinstance(t, str) and t.strip() for t in turns):
            raise ValueError('Empty/non-string turn')
        if not item.get('family') or not item.get('form') or not item.get('requirements'):
            raise ValueError('Missing item metadata/requirements')
        for r in item['requirements']:
            if r.get('expect') not in EXPECT or not r.get('words') or not isinstance(r.get('by'), list):
                raise ValueError('Invalid requirement')
            if r['words'].casefold() not in '\n'.join(turns).casefold():
                raise ValueError(f"Requirement is not verbatim user words: {item['id']}")
            if r['expect'] == 'needs_fact' and not r.get('deciding_fact'):
                raise ValueError('needs_fact requires deciding_fact')
        items[item['id']] = item
    return items

def jobs(items, repeats=30):
    return [(key, 1) for key in sorted(items)] + [(key, 2) for key in sorted(random.Random(SEED).sample(sorted(items), repeats))]

def session_id(tag, key, rep):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', tag):
        raise ValueError('Unsafe round tag')
    return f've-{tag}-live-{key}-{rep}'

def write_json(path, data, exclusive=True):
    with Path(path).open('x' if exclusive else 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

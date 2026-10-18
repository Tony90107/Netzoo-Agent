"""Code scoring of the core call from the trace (spec 2026-10-15 section 8; no model calls, no labellers).

Usage: score_core.py TAG [review]   -> review-sheet.md: ASK facts to check and the replies to spot-check
       score_core.py TAG score      -> score-core.json (needs facts-checked.json; faithful-checked.json optional)

facts-checked.json: {"C11": true, ...} for every ask item whose call is ASK -- does a question target the gold
deciding fact. faithful-checked.json: {"C11": {"faithful": true, "note": "..."}} for the spot-checked replies.
"""
from __future__ import annotations
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from plan import CLASSES, HERE, SEED, load_items, session_id, write_json

EXPECTED = {'do': 'DO', 'dont': 'DECLINE', 'ask': 'ASK', 'vague': 'CLARIFY'}
MAX_COST = {'do': 2, 'dont': 3, 'ask': 2, 'vague': 2}
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

def norm(names): return {str(n).strip().upper().replace('LIONESS ', 'LIONESS-') for n in names or []}

def outcome(item, core, right_fact=None):
    """(outcome, cost) of one core call against the item's gold."""
    cls, kind = item['class'], core['kind']
    offered, gold = norm(core.get('workflows')), norm(item['workflows'])
    partial = core.get('partial')
    if cls == 'do':
        if kind == 'DO' and not partial:
            if not offered or offered <= gold: return 'correct', 0
            return ('extra_options', 1) if offered & gold else ('wrong_workflow', 2)
        if kind in ('ASK', 'CLARIFY'): return 'needless_question', 1
        if kind == 'UNCHECKED': return 'unchecked', 1
        return 'false_refusal', 2
    if cls == 'dont':
        if kind == 'DECLINE': return 'correct', 0
        if kind == 'DO': return ('partly_accept', 2) if partial else ('false_accept', 3)
        return 'undecided', 1
    if kind == EXPECTED[cls]:
        if cls == 'ask' and right_fact is not True: return 'wrong_fact', 1
        return 'correct', 0
    # Phase 2 (declared before p2; GOLD-REVIEW file_checkable): a run that says its input check settles the deciding
    # fact before anything runs is asking it.
    settled = any(fact.get('settled_by_input_check') for fact in core.get('facts') or [])
    if cls == 'ask' and kind == 'DO' and item.get('file_checkable') and settled and right_fact is True:
        return 'correct', 0
    if kind in ('ASK', 'CLARIFY'): return 'wrong_question_kind', 1
    if kind == 'UNCHECKED': return 'unchecked', 1
    return ('committed_without_asking' if kind == 'DO' else 'refused_without_asking'), 2

def load(tag):
    live = HERE / 'live' / tag
    rows = json.loads((live / 'structure.json').read_text())
    return live, {row['item']: row for row in rows.values()}, load_items()

def review(tag):
    live, rows, items = load(tag)
    facts = [k for k, r in rows.items() if items[k]['class'] == 'ask' and ((r['core'] or {}).get('kind') == 'ASK'
             or items[k].get('file_checkable') and any(f.get('settled_by_input_check') for f in (r['core'] or {}).get('facts') or []))]
    off = [k for k, r in rows.items() if outcome(items[k], r['core'] or {'kind': 'NONE'}, True)[1] > 0
           or (r['core'] or {}).get('kind') != 'DO']
    rest = sorted(set(rows) - set(off))
    sample = sorted(set(off) | set(random.Random(SEED).sample(rest, min(10, len(rest)))))
    out = ['# Review sheet', '', '## ASK facts to check (facts-checked.json)', '']
    for k in sorted(facts):
        out += [f'- {k} gold: {items[k]["deciding_fact"]}',
                *(f'  - {"said" if f.get("settled_by_input_check") else "asked"}: {f["question"]} (user: "{f["user_quote"]}"; '
                  f'contract: "{f.get("contract_quote", "")}")' for f in rows[k]['core']['facts'])]
    out += ['', '## Replies to spot-check (faithful-checked.json)', '']
    for k in sample:
        r, it = rows[k], items[k]
        text = ANSI.sub('', (live / session_id(tag, k, 1) / 't1' / 'stdout.txt').read_text(errors='replace')).strip()
        out += [f'### {k} class={it["class"]} gold={it["workflows"]} core={(r["core"] or {}).get("kind")}'
                f' {(r["core"] or {}).get("workflows")} basis={(r["core"] or {}).get("basis")} views={r["views"]}',
                f'Request: {it["prompt"]}', '```text', text[-2500:], '```', '']
    (live / 'review-sheet.md').write_text('\n'.join(out))
    print(f'{len(facts)} ASK facts, {len(sample)} replies in {live / "review-sheet.md"}')

def score(tag):
    live, rows, items = load(tag)
    facts = json.loads((live / 'facts-checked.json').read_text())
    faithful_path = live / 'faithful-checked.json'
    faithful = json.loads(faithful_path.read_text()) if faithful_path.exists() else {}
    need = {k for k, r in rows.items() if items[k]['class'] == 'ask' and ((r['core'] or {}).get('kind') == 'ASK'
            or items[k].get('file_checkable') and any(f.get('settled_by_input_check') for f in (r['core'] or {}).get('facts') or []))}
    if need - set(facts): raise ValueError(f'facts-checked.json lacks {sorted(need - set(facts))}')
    confusion = {c: Counter() for c in CLASSES}; outcomes = {c: Counter() for c in CLASSES}
    cost = Counter(); n = Counter(); per_item = {}; views = defaultdict(Counter); missing = []
    for k, r in sorted(rows.items()):
        it = items[k]; cls = it['class']; core = r['core']
        if core is None: missing.append(k); core = {'kind': 'NONE', 'workflows': []}
        out, c = outcome(it, core, facts.get(k))
        kind = core['kind'] + ('(partial)' if core.get('partial') else '')
        confusion[cls][kind] += 1; outcomes[cls][out] += 1; cost[cls] += c; n[cls] += 1
        for v in r['views']: views[core['kind']][v] += 1
        per_item[k] = {'class': cls, 'form': it['form'], 'kind': kind, 'basis': core.get('basis'),
                       'workflows': core.get('workflows'), 'outcome': out, 'cost': c, 'views': r['views'],
                       'faithful': faithful.get(k)}
    per_class = {c: {'n': n[c], 'correct': outcomes[c]['correct'],
                     'cost_score': round(100 * (1 - cost[c] / (MAX_COST[c] * n[c])), 1),
                     'kinds': dict(confusion[c]), 'outcomes': dict(outcomes[c])} for c in CLASSES}
    checked = [v for v in faithful.values() if isinstance(v, dict)]
    result = {
        'core_score': round(sum(p['cost_score'] for p in per_class.values()) / len(CLASSES), 1),
        'correct': f"{sum(p['correct'] for p in per_class.values())}/{sum(n.values())}",
        'per_class': per_class,
        'false_accepts': outcomes['dont']['false_accept'] + outcomes['dont']['partly_accept'],
        'false_refusals': outcomes['do']['false_refusal'],
        'views_by_kind': {k: dict(v) for k, v in views.items()},
        'faithful': f"{sum(v.get('faithful') is True for v in checked)}/{len(checked)}",
        'missing_core': missing,
        'code': {'sessions': len(rows), 'exceptions': sum(bool(r['exceptions']) for r in rows.values()),
                 'nemotron_ok': sum(any('nemotron' in str(m).lower() and s == 'success' for m, s in r['check_calls'])
                                    for r in rows.values()),
                 'cost_usd': round(sum(r['cost_usd'] for r in rows.values()), 4)},
        'items': per_item}
    write_json(live / 'score-core.json', result, exclusive=False)
    print(json.dumps({k: v for k, v in result.items() if k != 'items'}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    tag, mode = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'review')
    review(tag) if mode == 'review' else score(tag)

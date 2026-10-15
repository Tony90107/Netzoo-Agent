"""Blind-label validation, mandatory review selection, and primary-only frozen scoring."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import random
from plan import HERE, SEED, digest, jobs, load_items, write_json

GIVEN = {'GIVEN', 'GIVEN_WITH_STEP', 'GIVEN_IF_INPUT'}
UNDECIDED = {'UNCONFIRMED', 'ASKED', 'OMITTED'}
LABELS = GIVEN | UNDECIDED | {'NOT_GIVEN', 'PARTLY'}

def contradiction(label): return label['contradiction'].startswith('yes:')

def provider_errors(row):
    # Round m3 deviation: `errors` also lists calls whose status is only 'failed' -- a semantic-validation retry or a
    # structured output that could not be decoded, with no exception. Those are model-output failures (decode failures
    # are what `nemotron_coverage` measures), not provider errors; a provider error carries its exception.
    return [e for e in row.get('errors', []) if e not in ('failed', 'error')]

def mismatch(layer, value):
    if layer['expect'] == 'needs_fact': return value != 'ASKED'
    if layer['expect'] == 'not_supported': return value in GIVEN | {'PARTLY'}
    return value == 'NOT_GIVEN'

def cost(layer, value):
    if layer['expect'] == 'not_supported':
        return 0 if value == 'NOT_GIVEN' else 1 if value in UNDECIDED else 2 if value == 'PARTLY' else 3
    return 0 if value in GIVEN else 2 if value == 'NOT_GIVEN' else 1

def validate_labels(rows, key, labels, adjudicated=False):
    if set(labels) - set(key): raise ValueError('Unknown blind codes')
    for code, label in labels.items():
        row = rows[key[code]['session']]
        if not isinstance(label.get('R'), list) or len(label['R']) != len(row['layers']) or any(x not in LABELS for x in label['R']):
            raise ValueError(f'Invalid R labels: {code}')
        c = label.get('contradiction')
        if not isinstance(c, str) or not (c == 'no' or c.startswith('yes:') and c[4:].strip()):
            raise ValueError(f'Invalid contradiction: {code}')
        if 'right_question' in label and (not adjudicated or type(label['right_question']) is not bool):
            raise ValueError('right_question is a boolean added only by the primary adjudicator')
        if adjudicated:
            if not isinstance(label.get('reason'), str) or not label['reason'].strip():
                raise ValueError(f'Adjudication needs a reason: {code}')
            if any(l['expect'] == 'needs_fact' for l in row['layers']) and type(label.get('right_question')) is not bool:
                raise ValueError(f'Ask adjudication needs right_question: {code}')
            if row.get('bad_gate_candidate') and type(label.get('bad_gate')) is not bool:
                raise ValueError(f'Gate candidate needs adjudicated bad_gate: {code}')

def to_review(rows, key, labels):
    flagged = set()
    for code, mapping in key.items():
        row = rows[mapping['session']]; label = labels[code]
        if (provider_errors(row) or row.get('bad_gate_candidate') or contradiction(label)
            or any(l['expect'] == 'needs_fact' or mismatch(l, v) or v in UNDECIDED | {'PARTLY'}
                   for l, v in zip(row['layers'], label['R']))): flagged.add(code)
    rest = sorted(set(key) - flagged)
    return sorted(flagged | set(random.Random(SEED).sample(rest, math.ceil(.1 * len(rest)))))

def validate(rows, key, labels, checked, items, repeats=30, require_review=True):
    if Counter((r['item'], r['rep']) for r in rows.values()) != Counter(jobs(items, repeats)):
        raise ValueError('Incomplete or duplicate round coverage')
    mapped = [k['session'] for k in key.values()]
    if len(set(mapped)) != len(mapped) or set(mapped) != set(rows) or set(labels) != set(key):
        raise ValueError('Blinding map or labels do not cover every session once')
    for row in rows.values():
        if not row.get('capture_verified'): raise ValueError('Unverified session capture')
        if len(row['layers']) != len(items[row['item']]['requirements']):
            raise ValueError('Layer count mismatch')
        for layer, gold in zip(row['layers'], items[row['item']]['requirements']):
            if any(layer.get(k) != v for k, v in gold.items()): raise ValueError('Gold mismatch')
    for mapping in key.values():
        if mapping['gold'] != items[rows[mapping['session']]['item']]['requirements']: raise ValueError('Blind key gold mismatch')
    validate_labels(rows, key, labels); validate_labels(rows, key, checked, True)
    if require_review and not set(to_review(rows, key, labels)) <= set(checked):
        raise ValueError('Required primary review incomplete')

def rate(k, n):
    if not n: return {'k': k, 'n': n, 'rate': None, 'wilson95': None}
    z = 1.96; p = k/n; den = 1+z*z/n
    center = (p+z*z/(2*n))/den; half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return {'k': k, 'n': n, 'rate': p, 'wilson95': [max(0, center-half), min(1, center+half)]}

def score(rows, key, labels, checked):
    final = {mapping['session']: checked.get(code, labels[code]) for code, mapping in key.items()}
    c = Counter(); costs = {'neg': [], 'pos': []}; family = defaultdict(Counter); repeat = defaultdict(dict)
    for sid, row in rows.items():
        label = final[sid]; repeat[row['item']][row['rep']] = label['R']
        if row['rep'] != 1: continue
        c['sessions'] += 1
        c['errors'] += bool(provider_errors(row))
        c['model_output_failures'] += bool(row.get('errors'))
        c['nemotron'] += any('nemotron' in str(m).lower() and s == 'success' for m, s in row['check_calls'])
        c['contradictions'] += contradiction(label)
        c['bad_gate'] += bool(label.get('bad_gate'))
        c['run_selected'] += row['action'].startswith('run_')
        for layer, value in zip(row['layers'], label['R']):
            c['requirements'] += 1; c['read'] += bool(layer['understood'])
            if layer['expect'] == 'needs_fact':
                c['ask'] += 1; c['right_ask'] += value == 'ASKED' and label.get('right_question') is True
                continue
            side = 'neg' if layer['expect'] == 'not_supported' else 'pos'
            c[side] += 1; c[f'{side}:{value}'] += 1; costs[side].append(cost(layer, value))
            family[row['family']][side] += 1
            family[row['family']][f'{side}_mismatch'] += mismatch(layer, value)
    fa = sum(c[f'neg:{v}'] for v in GIVEN | {'PARTLY'})
    strict = sum(c[f'neg:{v}'] for v in GIVEN)
    pg = sum(c[f'pos:{v}'] for v in GIVEN)
    metrics = {'FAR': rate(fa, c['neg']), 'FAR_strict': rate(strict, c['neg']),
               'FRR': rate(c['pos:NOT_GIVEN'], c['pos']), 'positive_given': rate(pg, c['pos']),
               'right_ask': rate(c['right_ask'], c['ask']), 'requirements_read': rate(c['read'], c['requirements']),
               'nemotron_coverage': rate(c['nemotron'], c['sessions']), 'provider_error': rate(c['errors'], c['sessions'])}
    checks = {k: metrics[k]['rate'] is not None and (metrics[k]['rate'] <= threshold if less else metrics[k]['rate'] >= threshold)
              for k, threshold, less in [('FAR', .03, True), ('FRR', .05, True), ('positive_given', .95, False),
                  ('right_ask', .9, False), ('requirements_read', .95, False), ('nemotron_coverage', .95, False), ('provider_error', .05, True)]}
    checks['zero_bad_gate'] = c['bad_gate'] == 0
    if not costs['neg'] or not costs['pos']: raise ValueError('Both positive and negative denominators required')
    weighted = 100*(.6*(1-sum(costs['neg'])/(3*len(costs['neg'])))+.4*(1-sum(costs['pos'])/(2*len(costs['pos']))))
    pairs = [r for r in repeat.values() if 1 in r and 2 in r]
    far, frr = metrics['FAR']['rate'], metrics['FRR']['rate']
    grade = next((g for g, a, b in [('A', .03, .05), ('B', .06, .1), ('C', .12, .15), ('D', .2, 1)] if far <= a and frr <= b), 'F')
    return {'score': weighted, 'grade': grade, 'metrics': metrics, 'thresholds': checks,
            'accepted': all(checks.values()), 'counts': dict(c), 'by_family': dict(family),
            'repeat_agreement': rate(sum(r[1] == r[2] for r in pairs), len(pairs)),
            'capture_validation': 'All turns hash verified; this is not full replay.'}

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('tag'); p.add_argument('mode', choices=['spotcheck', 'score'])
    p.add_argument('--dataset', type=Path, default=HERE / 'heldout.json'); a = p.parse_args()
    live = HERE / 'live' / a.tag
    read = lambda name: json.loads((live / name).read_text())
    rows, key, labels = read('structure.json'), read('blind-key.json'), read('labels-A.json')
    checked = read('labels-checked.json') if (live / 'labels-checked.json').exists() else {}
    items = load_items(a.dataset)
    meta = read('round.json')
    if meta['dataset_sha256'] != digest(a.dataset) or meta['jobs'] != [list(j) for j in jobs(items)]:
        raise ValueError('Dataset or job plan changed after recording')
    from collect import read_turn
    for sid, row in rows.items():
        item = items[row['item']]
        for number, task in enumerate(item.get('turns') or [item['prompt']], 1):
            read_turn(live / sid, number, task)
    validate(rows, key, labels, checked, items, require_review=a.mode == 'score')
    if a.mode == 'spotcheck':
        result = to_review(rows, key, labels); write_json(live / 'to-review.json', result)
        print(f'{len(result)} sessions require primary review')
    else:
        result = score(rows, key, labels, checked); write_json(live / 'score.json', result)
        print(json.dumps(result, indent=2))

if __name__ == '__main__': main()

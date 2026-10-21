"""Summarize a probe run per model and role, beside the same items' recorded calls in round p5r.

Usage: summarize.py probe-1.json
"""
from __future__ import annotations
import glob
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P5R = HERE.parent / 'core-judgment-2026-10-15' / 'live' / 'p5r'


def _median(values):
    return round(statistics.median(values), 1) if values else '-'


def reference(items):
    """The p5r session's own calls for the probed items: (role, model) -> statuses and seconds."""
    found = defaultdict(list)
    for item in items:
        for path in glob.glob(str(P5R / f'cj-p5r-{item}-*' / 't1' / 'session.json')):
            for call in (json.loads(Path(path).read_text()).get('token_usage') or {}).get('calls', []):
                if call.get('role') in ('capability_check', 'semantic_interpreter'):
                    found[(call['role'], call.get('model'))].append(
                        (call.get('status'), (call.get('duration_ms') or 0) / 1000))
    return found


def main(path):
    data = json.loads(Path(path).read_text())
    groups = defaultdict(list)
    for row in data['rows']:
        groups[(row['model'], row['role'])].append(row)
    print(f"| model | role | decoded | first try ok | 429 waits | errors | median s | max s | median out tok |")
    print('|---|---|---|---|---|---|---|---|---|')
    for (model, role), rows in sorted(groups.items()):
        ok = [r for r in rows if r['status'] == 'success']
        errors = Counter(r['error_kind'] for r in rows if r['status'] != 'success')
        print(f"| {model} | {role} | {len(ok)}/{len(rows)} | {sum(r['first_attempt_ok'] for r in rows)}/{len(rows)} "
              f"| {sum(r['rate_limited'] for r in rows)} | {dict(errors) or ''} | {_median([r['seconds'] for r in ok])} "
              f"| {max((r['seconds'] for r in ok), default='-')} "
              f"| {_median([r['output_tokens'] for r in ok if r.get('output_tokens')])} |")
    print('\nCode acceptance of the capability check (decoded calls): rejected quotes, unchecked sentences, results')
    for (model, role), rows in sorted(groups.items()):
        if role != 'capability_check':
            continue
        ok = [r for r in rows if r['status'] == 'success']
        if ok:
            print(f"- {model}: rejected {sum(r['rejected'] for r in ok)}, unchecked {sum(r['unchecked'] for r in ok)}, "
                  f"no result read {sum(not r['results'] for r in ok)}/{len(ok)}, "
                  f"statuses {dict(Counter(s for r in ok for s, _ in r['results']))}")
    print('\nRecorded p5r calls for the same items (production, for reference):')
    for (role, model), calls in sorted(reference(data['items']).items()):
        ok = [s for status, s in calls if status == 'success']
        print(f"- {role} {model}: success {len(ok)}/{len(calls)}, median {_median(ok)} s, max {max(ok, default='-')} s")


if __name__ == '__main__':
    main(sys.argv[1])

"""Offline quote: what one 56-item round costs if every reading role ran on another model (no model calls).

Takes round p5r's recorded calls (role, input and output tokens; the reply model is not a reading role and stays
gpt-4o-mini), and prices them at OpenRouter's current list prices. Output tokens: the gpt-4o-mini roles keep their
recorded counts; the roles nemotron read (its output is mostly reasoning) are counted at gpt-4o-mini's own output per
capability-check call in p5r. A reasoning model would spend more; the live smoke measures it.

Usage: estimate.py MODEL [MODEL ...]
"""
from __future__ import annotations
import glob
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P5R = HERE.parent / 'core-judgment-2026-10-15' / 'live' / 'p5r'
REPLY_ROLES = {'response', 'assistant', 'reply', 'reply_resolution'}


def recorded():
    """(role, model) -> [calls, input tokens, output tokens] over the round."""
    totals = defaultdict(lambda: [0, 0, 0])
    sessions = glob.glob(str(P5R / 'cj-p5r-*' / 't1' / 'session.json'))
    for path in sessions:
        for call in (json.loads(Path(path).read_text()).get('token_usage') or {}).get('calls', []):
            row = totals[(call.get('role'), call.get('model'))]
            row[0] += 1
            row[1] += call.get('input_tokens') or 0
            row[2] += call.get('output_tokens') or 0
    return totals, len(sessions)


def prices(models):
    data = json.load(urllib.request.urlopen('https://openrouter.ai/api/v1/models', timeout=30))['data']
    found = {m['id']: m['pricing'] for m in data}
    return {m: (float(found[m]['prompt']), float(found[m]['completion']), float(found[m].get('input_cache_read') or 0))
            for m in models}


def main(*models):
    totals, sessions = recorded()
    reading = {key: row for key, row in totals.items() if key[0] not in REPLY_ROLES}
    mini_check = totals.get(('capability_check', 'openai/gpt-4o-mini'), [0, 0, 0])
    per_check = mini_check[2] / mini_check[0] if mini_check[0] else 700
    calls = sum(row[0] for row in reading.values())
    tokens_in = sum(row[1] for row in reading.values())
    tokens_out = sum(row[0] * per_check if 'nemotron' in model else row[2] for (role, model), row in reading.items())
    check_in = sum(row[1] for (role, _), row in reading.items() if role.startswith('capability'))
    print(f'p5r: {sessions} sessions, {calls} reading calls, input {tokens_in:,} tokens '
          f'(capability roles {check_in:,}), output as a non-reasoning model {tokens_out:,.0f}')
    print('| model | round, no cache | round, sheet cached | per session |')
    print('|---|---|---|---|')
    for model, (p_in, p_out, p_cache) in prices(models).items():
        plain = tokens_in * p_in + tokens_out * p_out
        # The check's system prompt (the capability sheet) is the same every call: an upper share of 85% cached.
        cached = plain - (check_in * 0.85) * (p_in - p_cache) if p_cache else plain
        print(f'| {model} | ${plain:.2f} | ${cached:.2f} | ${plain / sessions:.3f} |')


if __name__ == '__main__':
    main(*sys.argv[1:])

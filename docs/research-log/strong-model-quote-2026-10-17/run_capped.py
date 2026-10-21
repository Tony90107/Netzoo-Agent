"""Run core-judgment rounds with every reading role on gpt-4o, under a hard spending cap (US$, whole account).

Each tag is one full bench round (56 items, one run each) by the unchanged `run_live.py`, in batches; before each
batch the account's total usage (OpenRouter /key, monotonic) is read, and the run stops when the spend since the
start plus one batch's allowance would pass the cap. The reply model stays gpt-4o-mini.

Usage: run_capped.py CAP_USD TAG [TAG ...]
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CJ = HERE.parent / 'core-judgment-2026-10-15'
sys.path.insert(0, str(CJ))
from dotenv import dotenv_values  # noqa: E402
from plan import DOTENV, PYTHON, jobs, load_items  # noqa: E402

MODELS = {
    'OPENROUTER_ROUTER_MODEL': 'openai/gpt-4o',
    'OPENROUTER_SEMANTIC_MODEL': 'openai/gpt-4o',
    # The same model under its dated id, so the check keeps its own slot and 16,000-token cap.
    'OPENROUTER_CAPABILITY_MODEL': 'openai/gpt-4o-2024-11-20',
    'NETZOO_ROUTER_MODEL_ALLOWLIST': ('openai/gpt-4o-mini,nvidia/nemotron-3-super-120b-a12b:free,'
                                      'openai/gpt-4o,openai/gpt-4o-2024-11-20'),
}
BATCH = 10
BATCH_ALLOWANCE = 1.0  # measured US$0.055 a session; 10 sessions with a margin


def usage() -> float:
    key = dotenv_values(DOTENV, interpolate=False)['OPENROUTER_API_KEY']
    request = urllib.request.Request('https://openrouter.ai/api/v1/key', headers={'Authorization': f'Bearer {key}'})
    return float(json.load(urllib.request.urlopen(request, timeout=30))['data']['usage'])


def main(cap: str, *tags: str) -> None:
    cap_usd = float(cap)
    start = usage()
    env = {**os.environ, **MODELS}
    todo = [f'{key}:{rep}' for key, rep in jobs(load_items())]
    for tag in tags:
        for index in range(0, len(todo), BATCH):
            spent = usage() - start
            if spent + BATCH_ALLOWANCE > cap_usd:
                print(f'STOP before {tag} batch {index // BATCH + 1}: spent US${spent:.3f}, cap US${cap_usd}', flush=True)
                return
            batch = todo[index:index + BATCH]
            print(f'{tag} batch {index // BATCH + 1}: {len(batch)} jobs, spent so far US${spent:.3f}', flush=True)
            subprocess.run([PYTHON, 'run_live.py', tag, *batch, '--code-manifest', 'freeze-p5.json', '--workers', '5'],
                           cwd=CJ, env=env, check=False)
            time.sleep(20)  # the account's usage is reported with a short delay
    print(f'done: spent US${usage() - start:.3f}', flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:])

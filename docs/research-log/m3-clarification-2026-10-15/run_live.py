"""Record real CLI output and per-turn evidence; never rerun an existing job implicitly."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from plan import HERE, ROOT, WORKTREE, PYTHON, digest, jobs, load_items, session_id, write_json

# Observe the card returned by the actual CLI, rather than regenerating it later.
BOOTSTRAP = r'''
import json, os, runpy, sys
sys.path.insert(0, 'scripts')
from netzoo_agent_core.engine.machine import ConversationMachine
original = ConversationMachine._reply_card
cards = []
def observed(self, result, task):
    card = original(self, result, task)
    cards.append(card)
    return card
ConversationMachine._reply_card = observed
sys.argv = ['scripts/netzoo_agent.py', *sys.argv[1:]]
try:
    runpy.run_path('scripts/netzoo_agent.py', run_name='__main__')
finally:
    with open(os.environ['M3_CARD_CAPTURE'], 'x') as f:
        json.dump(cards, f, ensure_ascii=False)
'''

def environment(dotenv):
    env = dict(os.environ)
    if dotenv and Path(dotenv).exists():
        # python-dotenv parses values without shell execution or interpolation.
        from dotenv import dotenv_values
        for key, value in dotenv_values(dotenv, interpolate=False).items():
            if value is not None:
                env.setdefault(key, value)
    env['PYTHONUNBUFFERED'] = '1'
    return env

def select_jobs(all_jobs, explicit, resume_unstarted, live, tag):
    selected = []
    for text in explicit:
        key, rep = text.rsplit(':', 1)
        pair = (key, int(rep))
        if pair not in all_jobs or pair in selected:
            raise ValueError(f'Invalid or duplicate job: {text}')
        selected.append(pair)
    if resume_unstarted and explicit:
        raise ValueError('Use either explicit jobs or --resume-unstarted')
    if resume_unstarted:
        selected = [j for j in all_jobs if not (live / session_id(tag, *j)).exists()]
    return selected or ([] if resume_unstarted else all_jobs)

def verify_code(worktree, manifest):
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=worktree, text=True).strip()
    if sha != manifest['base_sha']:
        raise ValueError('Candidate base SHA changed')
    dirty = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', '-z'], cwd=worktree).decode().split('\0')
    if set(filter(None, dirty)) - set(manifest['files']):
        raise ValueError('Candidate has modifications outside frozen whitelist')
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=worktree).decode().split('\0')
    if set(filter(None, untracked)) - set(manifest['files']):
        raise ValueError('Candidate has untracked files outside frozen whitelist')
    for name, expected in manifest['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or digest(worktree / path) != expected:
            raise ValueError(f'Candidate hash mismatch: {name}')
    return sha


def run_job(tag, key, rep, item, worktree, live, env, timeout, code_manifest=None):
    if code_manifest: verify_code(worktree, code_manifest)
    sid = session_id(tag, key, rep)
    folder = live / sid
    folder.mkdir()  # Atomic claim; existing jobs, partial or complete, are never overwritten.
    source = worktree / '.netzoo' / 'sessions' / f'{sid}.json'
    if source.exists():
        raise ValueError(f'Session already exists: {sid}')
    turns = item.get('turns') or [item['prompt']]
    codes = []
    for n, task in enumerate(turns, 1):
        turn = folder / f't{n}'
        turn.mkdir()
        args = ['--session' if n == 1 else '--resume', sid, '--keep-session', '--task', task]
        started = time.time()
        with (turn / 'stdout.txt').open('xb') as out, (turn / 'stderr.txt').open('xb') as err:
            try:
                code = subprocess.call([PYTHON, '-c', BOOTSTRAP, *args], cwd=worktree,
                    env={**env, 'M3_CARD_CAPTURE': str(turn / 'cards.json')}, stdin=subprocess.DEVNULL,
                    stdout=out, stderr=err, timeout=timeout)
            except subprocess.TimeoutExpired:
                code = 'timeout'
        if source.exists():
            shutil.copyfile(source, turn / 'session.json')
            session = json.loads(source.read_text())
            run_id = session.get('run_id')
            trace = worktree / '.netzoo' / 'traces' / str(run_id) / 'events.jsonl'
            if run_id and trace.exists():
                shutil.copyfile(trace, turn / 'events.jsonl')
        manifest = {'turn': n, 'mode': args[0], 'request': task, 'exit': code,
                    'started': started, 'finished': time.time(),
                    'files': {p.name: digest(p) for p in sorted(turn.iterdir()) if p.is_file()}}
        write_json(turn / 'manifest.json', manifest)
        codes.append(code)
        if code != 0:
            break
    if code_manifest: verify_code(worktree, code_manifest)
    write_json(folder / 'job.json', {'item': key, 'rep': rep, 'session': sid,
               'expected_turns': len(turns), 'codes': codes, 'complete': len(codes) == len(turns) and all(c == 0 for c in codes)})
    return sid, codes

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('tag'); p.add_argument('jobs', nargs='*', help='Explicit item:rep jobs')
    p.add_argument('--dataset', type=Path, default=HERE / 'heldout.json')
    p.add_argument('--worktree', type=Path, default=WORKTREE)
    p.add_argument('--code-manifest', type=Path, required=True)
    p.add_argument('--dotenv', type=Path, default=ROOT / '.env')
    p.add_argument('--resume-unstarted', action='store_true')
    p.add_argument('--workers', type=int, default=5); p.add_argument('--timeout', type=int, default=900)
    a = p.parse_args()
    items = load_items(a.dataset); all_jobs = jobs(items)
    session_id(a.tag, 'validate', 1)
    live = HERE / 'live' / a.tag
    live.mkdir(parents=True, exist_ok=True)
    env = environment(a.dotenv)
    code_manifest = json.loads(a.code_manifest.read_text())
    sha = verify_code(a.worktree, code_manifest)
    subprocess.run([PYTHON, '-c', 'import sys; sys.path.insert(0,"scripts"); from netzoo_agent_core.engine.machine import ConversationMachine'], cwd=a.worktree, env=env, check=True)
    frozen = {'sha': sha, 'dataset_sha256': digest(a.dataset), 'python': PYTHON,
              'worktree': str(a.worktree.resolve()), 'code_manifest_sha256': digest(a.code_manifest), 'jobs': [list(j) for j in all_jobs]}
    round_file = live / 'round.json'
    if round_file.exists():
        if json.loads(round_file.read_text()) != frozen: raise ValueError('Round code/dataset/config changed')
    else: write_json(round_file, frozen)
    todo = select_jobs(all_jobs, a.jobs, a.resume_unstarted, live, a.tag)
    for key, rep in todo:
        sid = session_id(a.tag, key, rep)
        if (live / sid).exists() or (a.worktree / '.netzoo/sessions' / f'{sid}.json').exists():
            raise ValueError(f'Existing job {key}:{rep}; use a fresh tag for a documented rerun')
    with ThreadPoolExecutor(a.workers) as pool:
        results = list(pool.map(lambda j: run_job(a.tag, *j, items[j[0]], a.worktree, live, env, a.timeout, code_manifest), todo))
    for sid, codes in results: print(sid, 'exit', codes)
    if any(any(c != 0 for c in codes) for _, codes in results): sys.exit(1)

if __name__ == '__main__': main()

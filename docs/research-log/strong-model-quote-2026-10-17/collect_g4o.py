"""structure.json for a gpt-4o round, keeping crashed sessions (no model calls).

`collect.py` refuses a session whose CLI exited 1 (and run_live copies no session.json for it), so a crash would
drop the whole round. Here every session is collected by `collect.collect_session`; one it refuses is kept from the
run worktree's own trace (its core call and views when recorded, the recorded errors as `exceptions`), so the
scorer counts it -- as the core call it made, or as missing -- and the crash is reported, never hidden.

Usage: collect_g4o.py TAG
"""
from __future__ import annotations
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CJ = HERE.parent / 'core-judgment-2026-10-15'
sys.path.insert(0, str(CJ))
from collect import collect_session  # noqa: E402
from plan import WORKTREE, jobs, load_items, session_id, write_json  # noqa: E402


def from_trace(sid: str, item: dict, rep: int, code) -> dict:
    events = []
    for manifest in glob.glob(str(WORKTREE / '.netzoo' / 'traces' / '*' / 'manifest.json')):
        if sid in Path(manifest).read_text():
            events = [json.loads(line) for line in (Path(manifest).parent / 'events.jsonl').read_text().splitlines()
                      if line.strip()]
    return {'item': item['id'], 'rep': rep, 'class': item['class'], 'form': item['form'], 'capture_verified': False,
            'exit': code, 'core': next((e['payload'] for e in reversed(events) if e['event_type'] == 'core.decision'),
                                       None),
            'views': [e['payload'].get('reply_kind') for e in events if e['event_type'] == 'core.view'],
            'semantic_failed': sum(e['event_type'] == 'routing.semantic_interpreter_failed' for e in events),
            'check_calls': [], 'cost_usd': 0.0,
            'exceptions': [f"{e['payload'].get('error_type')}: {e['payload'].get('message')}"
                           for e in events if e['event_type'] == 'error.recorded'][:1] or ['no trace']}


def main(tag: str) -> None:
    items = load_items()
    live = CJ / 'live' / tag
    meta = json.loads((live / 'round.json').read_text())
    rows = {}
    for key, rep in jobs(items):
        sid = session_id(tag, key, rep)
        try:
            rows[sid], _body = collect_session(live / sid, items[key], rep, meta)
        except (ValueError, FileNotFoundError) as error:
            code = json.loads((live / sid / 'job.json').read_text())['codes'][0] if (live / sid / 'job.json').exists() \
                else 'missing'
            rows[sid] = from_trace(sid, items[key], rep, code)
            print(f'{sid}: kept from trace ({error}); core {(rows[sid]["core"] or {}).get("kind")}')
    write_json(live / 'structure.json', rows)
    print(f'{len(rows)} sessions; {sum(not r["capture_verified"] for r in rows.values())} kept from trace')


if __name__ == '__main__':
    main(sys.argv[1])

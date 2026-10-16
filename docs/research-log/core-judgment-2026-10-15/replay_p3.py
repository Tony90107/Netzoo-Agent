"""Phase 3 offline replay: re-make the core call and re-render the reply of a recorded round (no model calls).

For each recorded session: the recorded final decision (its readings, check, fact check, verdict) gets a fresh core
call from this checkout's `decide_core`, and `respond` renders it as the CLI does after routing. Reports, per call
kind, which renderer answered and every reply whose renderer is not one of its call's (`core_views.ALLOWED`).

Usage: replay_p3.py TAG OUT_TAG   -> live/OUT_TAG/structure.json (cores replaced) + replay.json
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from types import SimpleNamespace
from plan import HERE, write_json

sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from netzoo_agent_core.contracts import HumanMessage, TaskDecision  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core  # noqa: E402
from netzoo_agent_core.interpretation.core_views import ALLOWED  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(HERE.parents[2]).load()


def main(tag, out_tag):
    live = HERE / 'live' / tag
    rows = json.loads((live / 'structure.json').read_text())
    report, views, mismatches = [], Counter(), []
    for sid, row in rows.items():
        session = json.loads((live / sid / 't1' / 'session.json').read_text())
        plan = session.get('plan') or {}
        task = [m['content'] for m in session['messages'] if m['role'] == 'user'][-1]
        decision = TaskDecision.model_validate(plan.get('decision')).model_copy(update={'core': None})
        reason = ((row.get('core') or {}).get('evidence') or {}).get('reason_code', '')
        core = decide_core(decision, task, reason_code=reason)
        decision = with_core(decision, core)
        state = {'decision': decision.model_dump(), 'plan': {**plan, 'decision': decision.model_dump()},
                 'messages': [HumanMessage(content=task)], 'tool_results': [], 'evaluation': None}
        try:
            out = respond(SimpleNamespace(project_policy=POLICY), state)
            kind, text, error = out.get('reply_kind') or '', str(out['messages'][-1].content), None
        except Exception as exc:  # a recorded state this renderer path cannot rebuild offline
            kind, text, error = '(error)', '', f'{type(exc).__name__}: {str(exc)[:200]}'
        views[(core.kind, kind)] += 1
        bad = error is None and kind not in ALLOWED[core.kind]
        if bad:
            mismatches.append((row['item'], core.kind, core.basis, kind))
        row['recorded_core'], row['core'], row['views'] = row['core'], core.model_dump(mode='json'), [kind]
        report.append({'item': row['item'], 'kind': core.kind, 'basis': core.basis, 'view': kind,
                       'recorded_kind': (row['recorded_core'] or {}).get('kind'), 'mismatch': bad, 'error': error,
                       'reply': text[:1500]})
    out = HERE / 'live' / out_tag
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'structure.json', rows, exclusive=False)
    write_json(out / 'replay.json', report, exclusive=False)
    for (kind, view), n in sorted(views.items()):
        print(f'{kind:10} {view:24} {n}')
    print('mismatches:', mismatches)
    print('errors:', [(r['item'], r['error']) for r in report if r['error']])
    print('kind changed:', [(r['item'], r['recorded_kind'], r['kind']) for r in report if r['recorded_kind'] != r['kind']])


if __name__ == '__main__':
    main(*sys.argv[1:3])

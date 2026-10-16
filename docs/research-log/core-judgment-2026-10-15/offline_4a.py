"""Phase 4a offline check (spec section 12.4): the new request-level limits on the recorded rounds (no model calls).

For each recorded session, every result row that carries the request's counts (`method`) has each credited workflow
re-judged with this checkout's `data_issue`. A credit the new limit removes is taken off the row (a row left with
none becomes not_available, with the limit as its reason), and the core call is made again. Reports every row the
new limit touched and every call that changed.

Usage: offline_4a.py TAG [TAG ...]
"""
from __future__ import annotations
import json
import sys
from plan import HERE, load_items

sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
from netzoo_agent_core.capability_sheet import entry  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core  # noqa: E402
from netzoo_agent_core.interpretation.method_conditions import _single  # noqa: E402
from netzoo_agent_core.workflow_conditions import conditions_for, data_issue  # noqa: E402
from score_core import outcome  # noqa: E402


def rejudge(decision):
    check = decision.capability_check
    if check is None:
        return decision, []
    touched, rows = [], []
    for row in check.requirements:
        method = row.method or {}
        if row.kind != 'result' or row.status not in ('available', 'with_step', 'partial') or not method:
            rows.append(row)
            continue
        kept, issues = [], []
        for key in row.delivered_by:
            workflow = entry(key).workflow
            conditions = conditions_for(workflow) if workflow else None
            old = data_issue(conditions, method.get('samples'), method.get('features')) if conditions else None
            new = data_issue(conditions, method.get('samples'), method.get('features'), _single(method)) if conditions else None
            if new and not old:
                issues.append(new)
            else:
                kept.append(key)
        if issues:
            touched.append((row.quote[:60], issues[0]))
            row = row.model_copy(update={'delivered_by': kept, 'limits': [*row.limits, *issues],
                                         'status': row.status if kept else 'not_available'})
        rows.append(row)
    return decision.model_copy(update={'capability_check': check.model_copy(update={'requirements': rows})}), touched


def main(tags):
    items = load_items()
    for tag in tags:
        live = HERE / 'live' / tag
        rows = json.loads((live / 'structure.json').read_text())
        facts = json.loads((live / 'facts-checked.json').read_text()) if (live / 'facts-checked.json').exists() else {}
        changes, touched_items = [], []
        for sid, row in rows.items():
            session = json.loads((live / sid / 't1' / 'session.json').read_text())
            decision = TaskDecision.model_validate((session.get('plan') or {}).get('decision')).model_copy(update={'core': None})
            task = [m['content'] for m in session['messages'] if m['role'] == 'user'][-1]
            reason = ((row.get('core') or {}).get('evidence') or {}).get('reason_code', '')
            new_decision, touched = rejudge(decision)
            if not touched:
                continue
            item = items[row['item']]
            before = decide_core(decision, task, reason_code=reason)
            after = decide_core(new_decision, task, reason_code=reason)
            touched_items.append((row['item'], item['class'], touched))
            changes.append((row['item'], item['class'], before.kind, after.kind,
                            outcome(item, before.model_dump(), facts.get(row['item']))[0],
                            outcome(item, after.model_dump(), facts.get(row['item']))[0]))
        print(f'== {tag}: rows touched in {len(touched_items)} sessions')
        for found in touched_items:
            print('   touched:', found)
        for change in changes:
            print('   call:', change)


if __name__ == '__main__':
    main(sys.argv[1:] or ['p0', 'p1', 'p2', 'p3'])

"""Offline check for the fixes to the items both p4b and p4c got wrong (no model calls).

Every recorded session of the bench rounds is replayed through `decide_core` twice on the same recorded decision:
once by the code at the commit before the fixes (a checkout given by --scripts) and once by this checkout. This
checkout also re-judges the enum settings a row was declined for (C52's value names), the one fix that acts before
the call. Reports every call that changed and whether it is right against the gold.

A recorded decision is the one the turn left: CLARIFY and fact-agent ASK turns had routing's picks cleared
(`with_core`), so a turn the new goal rule no longer holds is listed as needing the fact agent, not scored.

The dev set m3 (TAG `m3`, its 150 recorded sessions in the main checkout) is replayed the same way, unscored: its
items are not the bench's, and the changes are read by hand.

Usage: offline_both_wrong.py calls OUT.json [--scripts DIR] TAG [TAG ...]
       offline_both_wrong.py compare BEFORE.json AFTER.json
"""
from __future__ import annotations
import json
import re
import sys

ARGS = sys.argv[1:]
if ARGS and ARGS[0] == 'calls' and '--scripts' in ARGS:
    at = ARGS.index('--scripts')
    sys.path.insert(0, ARGS[at + 1])
    del ARGS[at:at + 2]

from plan import DOTENV, HERE, load_items, write_json  # noqa: E402

sys.path.insert(1 if '--scripts' in sys.argv else 0, str(HERE.parents[2] / 'scripts'))
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core  # noqa: E402

ENUM = re.compile(r"^(?P<workflow>[A-Z][A-Z-]+)'s \w+ requires one of .*; \".*\" does not identify one allowed choice$")


def rejudged(decision):
    """Rows declined only because an enum value named no allowed choice, judged again by this checkout."""
    from netzoo_agent_core.capability_sheet import sheet_entries
    from netzoo_agent_core.interpretation.capability_check import _full_gap
    from netzoo_agent_core.workflow_conditions import StatedSetting, conditions_for, setting_issue

    check = decision.capability_check
    if check is None:
        return decision, []
    rows, touched = [], []
    for row in check.requirements:
        found = [ENUM.match(limit) for limit in row.limits]
        if row.kind != 'result' or row.status != 'not_available' or not found or not all(found):
            rows.append(row)
            continue
        workflow = found[0]['workflow']
        conditions = conditions_for(workflow)
        stated = [StatedSetting(item['name'], item['quote'], item.get('value') or '')
                  for item in (row.method or {}).get('settings', []) if item['name'].startswith(f'{workflow}.')]
        if any(setting_issue(conditions, setting) for setting in stated):
            rows.append(row)
            continue
        # the credit the fitting removed is not recorded: the workflow's own result stands for it
        keys = [key for key, item in sheet_entries().items() if item.workflow == workflow and item.kind == 'produces']
        touched.append((row.quote[:50], workflow))
        rows.append(row.model_copy(update={'status': 'available', 'delivered_by': keys[:1], 'limits': []}))
    if not touched:
        return decision, []
    results = [row for row in rows if row.kind == 'result']
    check = check.model_copy(update={'requirements': rows, 'full_gap': _full_gap(results, check.unchecked)})
    return decision.model_copy(update={'capability_check': check}), touched


M3 = DOTENV.parent / 'docs' / 'research-log' / 'm3-clarification-2026-10-15' / 'live' / 'm3'


def _sessions(tag):
    """(session id, item, turn folder, recorded core or None, reason code) for each session of a round."""
    if tag == 'm3':
        for turn in sorted(M3.glob('ve-m3-live-*-1/t1')):
            events = [json.loads(line) for line in (turn / 'events.jsonl').read_text().splitlines() if line.strip()]
            reason = next((e['payload'].get('reason_code', '') for e in events
                           if e['event_type'] == 'decision.recorded'), '')
            yield turn.parent.name, turn.parent.name.split('-')[3], turn, None, reason
        return
    live = HERE / 'live' / tag
    for sid, row in json.loads((live / 'structure.json').read_text()).items():
        core = row.get('core') or {}
        yield sid, row['item'], live / sid / 't1', core, (core.get('evidence') or {}).get('reason_code', '')


def calls(out, tags):
    new_code = '--scripts' not in sys.argv
    found = {}
    for tag in tags:
        for sid, item, turn, recorded, reason in _sessions(tag):
            session = json.loads((turn / 'session.json').read_text())
            decision = TaskDecision.model_validate((session.get('plan') or {}).get('decision')).model_copy(
                update={'core': None})
            task = [m['content'] for m in session['messages'] if m['role'] == 'user'][-1]
            touched = []
            if new_code:
                decision, touched = rejudged(decision)
            core = decide_core(decision, task, reason_code=reason)
            found[f'{tag}/{sid}'] = {'item': item, 'tag': tag, 'recorded': (recorded or {}).get('kind'),
                                     'touched': touched, **core.model_dump(mode='json', include={
                                         'kind', 'basis', 'workflows', 'partial', 'run_allowed'})}
    write_json(HERE / out if '/' not in out else out, found)
    print(f'{len(found)} calls -> {out}')


def compare(before_path, after_path):
    from score_core import outcome

    items = load_items()
    before, after = json.loads(open(before_path).read()), json.loads(open(after_path).read())
    facts = {}
    changed = []
    for key, new in after.items():
        old = before[key]
        if (old['kind'], old['basis'], old['workflows'], old['partial']) == (
                new['kind'], new['basis'], new['workflows'], new['partial']):
            continue
        tag = new['tag']
        if new['item'] not in items:  # m3: read by hand
            changed.append((new['item'], tag, '-', f"{old['kind']}/{old['basis']}{old['workflows']}",
                            f"{new['kind']}/{new['basis']}{new['workflows']}{' partial' if new['partial'] else ''}",
                            '-', '-', new['touched']))
            continue
        if tag not in facts:
            path = HERE / 'live' / tag / 'facts-checked.json'
            facts[tag] = json.loads(path.read_text()) if path.exists() else {}
        item = items[new['item']]
        right = lambda call: outcome(item, call, facts[tag].get(new['item']))[0]  # noqa: E731
        held = old['basis'] == 'goal_unclear' and new['basis'] != 'goal_unclear'
        changed.append((new['item'], tag, item['class'], f"{old['kind']}/{old['basis']}{old['workflows']}",
                        f"{new['kind']}/{new['basis']}{new['workflows']}{' partial' if new['partial'] else ''}",
                        right(old), 'needs the fact agent' if held else right(new), new['touched']))
    for line in sorted(changed):
        print(*line, sep=' | ')
    print(f'{len(changed)} calls changed of {len(after)}')


if __name__ == '__main__':
    if ARGS[0] == 'calls':
        calls(ARGS[1], ARGS[2:])
    else:
        compare(ARGS[1], ARGS[2])

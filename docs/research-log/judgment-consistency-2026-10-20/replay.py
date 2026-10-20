"""Compare frozen checks and replay only their fact-wait/core/view seams. Zero model calls.

Archived routing, fact-agent answers and run verdicts stay fixed. This is not a full routing replay or a fresh eval.
Run from any directory: python3 -I replay.py
"""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
MAIN = WT.parents[1]/'netzoo_agent'
sys.path.insert(0, str(WT/'scripts'))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.graph.fact_check_call import without_legacy_waits  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def behavior(check):
    return {k: [{n:v for n,v in row.items() if n!='fact_ids'} for row in value] if k=='requirements' else value
            for k,value in check.items() if k not in ('facts','fact_conflicts')}


def main():
    before = json.loads(gzip.decompress((HERE/'before-checks.json.gz').read_bytes()))
    after = json.loads(gzip.decompress((HERE/'after-checks.json.gz').read_bytes()))
    assert before.keys() == after.keys()
    gold_path = WT/'docs/research-log/strictness-audit-2026-10-20/audit.json'
    gold = {x['trace']['session']:x for x in json.loads(gold_path.read_text())['items'].values()}
    counts, transitions, changed, skipped, inputs = Counter(), Counter(), [], [], {}
    all_cores = []
    for key in sorted(after):
        old, new = before[key], after[key]
        assert (old['task'],old['proposal'],old['where']) == (new['task'],new['proposal'],new['where'])
        counts['readings'] += 1
        diff = behavior(old['check']) != behavior(new['check'])
        counts['check_changed'] += diff
        folder = next((p for root in (WT,MAIN) if (p:=root/new['where']).joinpath('session.json').exists()), None)
        if folder is None:
            skipped.append({'key':key,'reason':'session_not_found','where':new['where']})
            continue
        session_path, events_path = folder/'session.json', folder/'events.jsonl'
        inputs[str(session_path)], inputs[str(events_path)] = sha(session_path), sha(events_path)
        session = json.loads(session_path.read_text())
        events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
        try:
            decision = TaskDecision.model_validate(session['plan']['decision'])
        except Exception as exc:
            skipped.append({'key':key,'reason':type(exc).__name__,'where':new['where'],'error':str(exc)})
            continue
        recorded = next((e['payload'] for e in reversed(events) if e.get('event_type')=='core.decision'), {})
        reason = recorded.get('evidence',{}).get('reason_code','') or ''
        cores, views, holds = [], [], []
        for row in (old,new):
            check = CapabilityCheck.model_validate(row['check'])
            if decision.fact_check is not None and decision.fact_check.status=='checked':
                check = without_legacy_waits(check)
            candidate = decision.model_copy(update={'capability_check':check})
            core = decide_core(candidate, row['task'], reason_code=reason)
            final = with_core(candidate,core)
            cores.append(core.model_dump(mode='json'))
            holds.append({'action':final.action,'should_execute':final.should_execute,
                          'execution_requested':final.execution_requested})
            view = None
            if core.kind=='ASK':  # these views are deterministic; never enter the DO response/model path
                rendered = respond(None,{'decision':final.model_dump(mode='json'),'messages':[]})
                view = {'kind':rendered['reply_kind'],'text':rendered['messages'][-1].content}
            views.append(view)
        counts['core_replayed'] += 1
        transitions[f'{cores[0]["kind"]}->{cores[1]["kind"]}'] += 1
        label = gold.get(session.get('session_id'))
        if label and label['prompt'].strip()!=new['task'].strip():
            label = None
        counts['gold_baselines_covered'] += label is not None
        if cores[0]['kind'] != cores[1]['kind']:
            counts['core_kind_changed'] += 1
        if cores[0]['kind']!=cores[1]['kind'] or views[0]!=views[1]:
            counts['core_kind_or_ask_view_changed'] += 1
        all_cores.append({'key':key,'where':new['where'],
            'before':cores[0]['kind'],'after':cores[1]['kind'],
            'gold':None if label is None else {'id':label['id'],'class':label['class'],'outcome':label['outcome']}})
        if diff:
            changed.append({'key':key,'where':new['where'],'session':str(session_path),'task':new['task'],
                'gold':None if label is None else {k:label[k] for k in ('id','class','outcome')},
                'check_fields_changed':[k for k in behavior(new['check']) if behavior(old['check']).get(k)!=behavior(new['check'])[k]],
                'before_core':cores[0],'after_core':cores[1], 'before_view':views[0],'after_view':views[1],
                'before_authority':holds[0],'after_authority':holds[1]})
    summary = {'counts':dict(counts),'core_transitions':dict(sorted(transitions.items())),
               'skipped':skipped,'limits':'Fixed archived routing, fact-agent answers and run verdicts; no model calls, no scientific execution; not end-to-end accuracy.'}
    (HERE/'replay-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (HERE/'changed.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n')
    (HERE/'core-replay.json').write_text(json.dumps(all_cores,ensure_ascii=False,indent=2)+'\n')
    sources = [WT/'scripts/netzoo_agent_core'/p for p in (
        'contracts/request_facts.py','interpretation/request_facts.py','interpretation/capability_check.py',
        'interpretation/needed_facts.py','interpretation/count_alternatives.py','interpretation/request_spans.py',
        'interpretation/core_decision.py','graph/fact_check_call.py',
        'graph/response.py','interpretation/core_views.py')]
    manifest = {'base_head':'cf31e7f3c6bf48f96553601eb292c66e272780f5','source_sha256':{str(p):sha(p) for p in sources},
                'input_sha256':{**inputs,str(gold_path):sha(gold_path),
                    **{str(p):sha(p) for p in (HERE/'before-checks.json.gz',HERE/'after-checks.json.gz')}},
                'replay_script_sha256':sha(Path(__file__))}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    main()

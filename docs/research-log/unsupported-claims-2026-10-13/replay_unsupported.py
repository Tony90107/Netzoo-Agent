# Offline replay of recorded A/B semantic rejections through without_unsupported_claims. Run from the repository root.
import sys,json,glob,collections,os
sys.path.insert(0,"scripts")
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.interpretation.unsupported_claims import without_unsupported_claims
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
W="../.worktrees"
tasks={}
for f in glob.glob(f"{W}/*/.netzoo/sessions/*.json"):
    try: d=json.load(open(f))
    except Exception: continue
    users=[m['content'] for m in d.get('messages',[]) if m.get('role')=='user']
    if d.get('run_id') and users: tasks[d['run_id']]=users[-1]
seen=set(); stats=collections.Counter(); status=collections.Counter(); samples=[]
for p in glob.glob(f"{W}/*/.netzoo/traces/*/events.jsonl"):
    rid=p.split('/')[-2]
    for line in open(p):
        if 'semantic_interpreter_failed' not in line: continue
        e=json.loads(line); pl=e['payload']
        if e.get('event_type')!='routing.semantic_interpreter_failed' or not pl.get('rejected_interpretation'): continue
        issues=pl.get('validation_issues') or []
        kinds={str(i).split('.',1)[-1].split(':')[0] for i in issues}
        if not kinds <= {'missing_evidence','inconsistent_not_applicable_outcome'}: continue
        task=tasks.get(rid)
        if not task or (task,json.dumps(pl['rejected_interpretation'],sort_keys=True)) in seen: continue
        seen.add((task,json.dumps(pl['rejected_interpretation'],sort_keys=True)))
        try: interp=SemanticInterpretation.model_validate(pl['rejected_interpretation'])
        except Exception: stats['unparsable']+=1; continue
        kept=without_unsupported_claims(task,interp,issues)
        key='/'.join(sorted(kinds))
        stats[(key,'kept' if kept else 'still discarded')]+=1
        if kept:
            m=match_semantic_request(task,kept.outcome_hypotheses,request_mode=kept.request_mode)
            status[(m.status,tuple(m.matched_actions or m.hypothesis_actions)[:3])]+=1
            o=kept.outcome_hypotheses[0].outcome
            samples.append((task[:90],o.artifact_type,o.granularity,m.status,(m.matched_actions or m.hypothesis_actions)[:3]))
for k,v in sorted(stats.items(),key=str): print(v,k)
print('--- match status of kept readings'); 
for k,v in status.most_common(12): print(v,k)
import random; random.seed(3)
for s in random.sample(samples,min(15,len(samples))): print('  ',s)

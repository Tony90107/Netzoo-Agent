"""ROUND-07 inventory supplement. Offline only; standard library; no production imports.

Reads saved JSON and source AST. Does not modify runtime, prompts, YAML, tests,
or saved sessions. Run: python3 -I audit.py [--rebuilt /absolute/checks.json]
Signals are screening observations, NOT automatic causal error labels.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
WORKSPACE = WT.parents[1]
ROOTS = [WT / 'docs/research-log', WORKSPACE / 'netzoo_agent/docs/research-log']
CORE = WT / 'scripts/netzoo_agent_core'
AUDIT01 = WT / 'docs/research-log/strictness-audit-2026-10-20/audit.json'
SOURCE_INPUTS = set()

CATEGORIES = {
 'K1': {
  'name': '指定方法', 'kind': '同一名稱多處讀取／文字解析',
  'producers': ['語意與原文方法名稱、每個結果 named_method、整段 named_method'],
  'consumers': ['registry 配對、method_fitting、run verdict'],
  'precedence': '要求層有 named 時保留；單一要求缺 named 才補整段；明確選擇另有優先規則。',
  'metric': '單一要求、整段與要求層都明列方法時，排除 LIONESS 家族相容名稱後的不同名稱。',
  'limit': '名稱不同不必然是錯；多要求的不同方法不互相比。',
  'refs': [('interpretation/method_conditions.py','verified_method'),('interpretation/method_conditions.py','with_request_method'),('routing/named_labels.py','named_workflow_action')]},
 'K2': {
  'name': '執行／說明意圖', 'kind': '不同讀取者共同控制授權',
  'producers': ['semantic request_mode、intent mode、capability asked_as、明確命令文字規則'],
  'consumers': ['assemble_task_decision、_with_requested_run、操作授權閘門'],
  'precedence': '語意與 intent 都要求執行才設 execution_requested；後段 capability 結果仍須 available 且 asked_as=request；文字規則可協調。',
  'metric': 'intent=execute，但所有結果被 capability 讀成 question；另計明確命令協調事件。',
  'limit': '不把 intent=answer 與 asked_as=request 視為矛盾；成功 semantic 的 request_mode 沒有逐次完整存檔，無法完整量三方差異。',
  'refs': [('graph/intent_invocation.py','_invoke_intent_router'),('interpretation/assembly.py','assemble_task_decision'),('graph/router_invocation.py','_with_requested_run'),('routing/capability.py','reconcile_request_mode')]},
 'K3': {
  'name': '結果／目標是否明確', 'kind': '語意結果與能力目標的再判讀',
  'producers': ['outcome_hypotheses、capability goal、研究假設讀取、fact wanted_result/R7'],
  'consumers': ['goal_unclear、decide_core、CLARIFY renderer'],
  'precedence': 'confirmed capability goal_unclear 及 fact open_results 可先導向 CLARIFY；單一具名方法另視為有目標。',
  'metric': '單一語意解讀為具體 artifact、capability 卻 purpose_only；或相反：語意 unknown、capability result_named 且有結果。',
  'limit': '可能是能力核對合理更正語意推測；不從差異直接判定哪份對。',
  'refs': [('interpretation/core_decision.py','goal_unclear'),('interpretation/core_decision.py','decide_core'),('interpretation/fact_check.py','kept_facts'),('graph/hypothesis_bases.py','invoke_hypothesis_matcher')]},
 'K4': {
  'name': '結果粒度', 'kind': '同一結果的粒度重讀',
  'producers': ['semantic granularity、capability ask.scale'],
  'consumers': ['registry 配對、能力 fitting、回覆的結果說明'],
  'precedence': '早期 registry 用語意粒度，後段 check 用自己的 scale；confirmed check 在限定條件下可接管匹配。',
  'metric': '單一解讀、單一要求且兩邊均為 aggregate/sample_specific 等可直接對照值時不同。',
  'limit': 'unknown／unstated 不當成錯值；多結果與 per-group 不強行歸併。',
  'refs': [('routing/outcome_matching.py','match_semantic_request'),('interpretation/capability_check.py','build_capability_check'),('interpretation/checked_match.py','checked_match')]},
 'K5': {
  'name': 'workflow 選擇', 'kind': '分階段選擇及有條件覆核',
  'producers': ['registry match、capability delivered_by、checked_match、run verdict'],
  'consumers': ['TaskDecision、Planner、fact candidates、回覆'],
  'precedence': '原 match 與 check 不是任意最後寫入者獲勝；checked_match 有既有匹配、使用者明選、unconfirmed 等限制。',
  'metric': 'registry 與第一份能力核對都只指向一個 workflow，但兩個名稱不同；另記接管事件。',
  'limit': '可為正確的後段修正，也可能之後被輸入／限制排除；不把兩個階段都當最終決策。',
  'refs': [('graph/router_invocation.py','_with_checked_match'),('interpretation/checked_match.py','checked_match'),('interpretation/run_verdict.py','run_verdict'),('interpretation/fact_check.py','fact_candidates')]},
 'K6': {
  'name': '不確定事實與追問', 'kind': '候選數量、舊維度及 fact agent 多處決策',
  'producers': ['unknown_facts、count_alternatives、open_choices、fact agent'],
  'consumers': ['count_update、resolve_unknowns、weigh_sample_doubts、kept_facts、decide_core'],
  'precedence': 'fact checked 時舊非程式追問轉 shadow；程式數量追問仍優先；R1 要求能力讀取也認為同段不確定。unknown sample count 仍有獨立處理。',
  'metric': '同段候選數量被兩個入口指定不同 property，或可見 legacy needs_fact 最後未保留問題／R1 拒收。',
  'limit': '去重與抑制問題可能是正確行為；原文兩種讀取均錯也不會被一致性偵測抓到。',
  'refs': [('interpretation/needed_facts.py','resolve_unknowns'),('interpretation/needed_facts.py','verified_unknowns'),('interpretation/count_alternatives.py','count_update'),('interpretation/count_alternatives.py','weigh_sample_doubts'),('interpretation/fact_check.py','kept_facts'),('graph/fact_check_call.py','apply_fact_check'),('interpretation/request_facts.py','FactRecord.read_alternatives')]},
 'K7': {
  'name': '輸入存在／種類／排除', 'kind': '資料的多種讀取與驗證來源',
  'producers': ['語意 input_artifacts、ruled_out_inputs/only_inputs、data_facts、veto A3、檔案預檢'],
  'consumers': ['without_ruled_out、data plan、核心資料追問、Planner'],
  'precedence': '語意輸入線索、使用者否定與真實檔案驗證意義不同；without_ruled_out 可移除前段 credit；veto 另有資料讀取。',
  'metric': '同一原文區段，同時被明確語意證據當作擁有某輸入，及 capability 當作該輸入不存在。',
  'limit': '僅在有 explicit input_artifact 證據與重疊引文時比；不把「方法需要」等同「使用者擁有」。',
  'refs': [('interpretation/ruled_out.py','without_ruled_out'),('graph/router_invocation.py','_with_applicability'),('interpretation/data_plan.py','build_data_plan'),('interpretation/contract_veto.py','_core_data_question')]},
 'K8': {
  'name': '數量與歸屬', 'kind': '要求／整段重填，另有否決層讀取',
  'producers': ['ask sample_count/feature_counts、conditions 同名欄位、veto focus counts'],
  'consumers': ['FactRecord、with_request_method、method_fitting、count_update、veto gates'],
  'precedence': '一般數量要求層先取值、缺才補整段；ROUND-03 共有紀錄；ROUND-07 加入候選擱置與檔案數量，但未取消所有 raw 重填。',
  'metric': '重疊證據的同類數量在要求與整段重填；其中讀出不同值的疑點另計。',
  'limit': 'belongs_to 缺失且一句含多層數量時，只能標候選疑點；不同資料／群組不直接認定衝突。',
  'refs': [('interpretation/request_facts.py','FactRecord.read_method'),('interpretation/request_facts.py','FactRecord.note_conflicts'),('interpretation/method_conditions.py','with_request_method'),('interpretation/slim_reader.py','merge_focus'),('interpretation/contract_veto.py','_count_violations'),('interpretation/contract_veto.py','_flip_questions')]},
 'K9': {
  'name': '設定解讀與參數綁定', 'kind': '重填＋不同消費規則，部分已收斂',
  'producers': ['要求 settings、整段 settings、request_parameters、hydration'],
  'consumers': ['setting_issue、typed_setting、verified_controls、run binding、Executor'],
  'precedence': 'ROUND-06 兩條 run 已共用 _bind_run_settings；明確 name=value 的非預設值可優先，未綁定設定使 run 等待；raw settings 仍重填。',
  'metric': '同 setting 名稱且重疊原文的整段／要求讀取，value_quote 不同；另列原始值為空與去向事件。',
  'limit': '空字串 vs empty 或不同格式可能語意相同，不自動算錯；重放改善需引用 ROUND-06 的對照，不混成此掃描因果。',
  'refs': [('graph/router_invocation.py','_bind_run_settings'),('graph/router_invocation.py','_on_run_verdict'),('graph/router_invocation.py','_with_requested_run'),('interpretation/method_conditions.py','run_setting_value'),('interpretation/method_conditions.py','verified_controls'),('interpretation/method_conditions.py','unbound_settings'),('interpretation/hydration.py','hydrate_router_decision')]},
 'K10': {
  'name': '最終判定與回覆', 'kind': '核心決策＋有行為判斷的多 renderer',
  'producers': ['full_gap、routing unsupported、run verdict、veto、decide_core、部分 renderer'],
  'consumers': ['core_view、respond、DO 專用 renderers、CLI cards'],
  'precedence': '非 DO 先走 core_view；DO 有多個 renderer 與後附說明；core.view 記錄 mismatch。不是所有 renderer 都有最後判定權。',
  'metric': '只採 trace 明確標記 core.view.mismatch=true，不從 DO/needs_input 這類合法狀態差異推造錯誤。',
  'limit': '較舊紀錄缺 core.view，且歷史 mismatch 不等於目前程式仍會重現。',
  'refs': [('interpretation/core_decision.py','decide_core'),('interpretation/core_views.py','core_view'),('graph/response.py','respond'),('graph/response.py','_respond'),('interpretation/hypothesis_routes.py','render_hypothesis_routes'),('interpretation/contract_veto.py','vetoed_core')]},
}

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm(s):
    return ' '.join(re.sub(r'[^\w]+', ' ', str(s or '').casefold()).split())

def enum(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').casefold().removeprefix('run_'))

def span(task, quote):
    q, t = norm(quote), norm(task)
    start = t.find(q) if q else -1
    return (start, start + len(q)) if start >= 0 else None

def overlap(task, a, b):
    x, y = span(task, a), span(task, b)
    return bool(x and y and x[0] < y[1] and y[0] < x[1])

def named(value):
    return bool(value and str(value).casefold() not in ('none', 'not_stated', 'unknown', ''))

def asks_of(proposal):
    return [a for k, v in proposal.items() if re.fullmatch(r's\d+', k) and isinstance(v, dict)
            for a in v.get('asks', [])]

def last(events, typ):
    return next((e.get('payload', {}) for e in reversed(events) if e.get('event_type') == typ), {})

def evidence(typ, sequence=None, **detail):
    return {'event_type': typ, 'sequence': sequence, **detail}

def signal(eligible=False, flagged=False, repeated=False, details=None, notes=None):
    return {'eligible': bool(eligible), 'flagged': bool(flagged), 'repeated': bool(repeated),
            'details': details or [], 'notes': notes or []}

def semantic_of(session):
    d = (session.get('plan') or {}).get('decision') or {}
    hs = d.get('outcome_hypotheses') or []
    if len(hs) == 1:
        return hs[0].get('outcome') or {}, hs
    if not hs and d.get('requested_outcome'):
        return d['requested_outcome'], []
    return {}, hs

def screen(task, proposal, events, session, seq):
    asks, conditions = asks_of(proposal), proposal.get('conditions') or {}
    single = asks[0] if len(asks) == 1 else None
    out = {k: signal() for k in CATEGORIES}
    sem, hypotheses = semantic_of(session)
    check_event = next((e for e in events if e.get('sequence') == seq), {})
    check = check_event.get('payload', {}).get('check') or {}

    # Scope-aware comparisons of two independently supplied values.
    if single is not None and named(single.get('named_method')) and named(conditions.get('named_method')):
        a, b = single['named_method'], conditions['named_method']
        compatible = enum(a) == enum(b) or ('lioness' in (enum(a), enum(b))
                         and enum(b if enum(a) == 'lioness' else a).startswith('lioness'))
        out['K1'] = signal(True, not compatible, True, [evidence('routing.capability_checked',seq,
                     ask_method=a, request_method=b, ask_quote=single.get('named_method_quote'),
                     request_quote=conditions.get('named_method_quote'))])

    intent = last(events, 'routing.intent_classified')
    if intent.get('mode') in ('answer','execute') and asks:
        flagged = intent['mode'] == 'execute' and all(a.get('asked_as','request') == 'question' for a in asks)
        out['K2'] = signal(True, flagged, True, [evidence('routing.intent_classified', mode=intent['mode']),
            evidence('routing.capability_checked',seq,asked_as=[a.get('asked_as','request') for a in asks])],
            ['command_reconciled'] if any(e.get('event_type')=='routing.explicit_execution_reconciled' for e in events) else [])

    if sem and conditions.get('goal') in ('result_named','purpose_only'):
        concrete = sem.get('artifact_type') not in (None,'unknown','not_applicable')
        flag = (concrete and conditions['goal']=='purpose_only') or (
               sem.get('artifact_type')=='unknown' and conditions['goal']=='result_named' and bool(asks))
        out['K3']=signal(True,flag,True,[evidence('session.plan.decision',artifact=sem.get('artifact_type')),
                evidence('routing.capability_checked',seq,goal=conditions['goal'],goal_quote=conditions.get('goal_quote'))])

    scale_map={'aggregate':'whole_cohort','sample_specific':'per_sample','per_sample':'per_sample'}
    if single is not None and sem.get('granularity') in scale_map and single.get('scale') in ('per_sample','whole_cohort'):
        a,b=scale_map[sem['granularity']],single['scale']
        out['K4']=signal(True,a!=b,True,[evidence('session.plan.decision',granularity=sem['granularity']),
            evidence('routing.capability_checked',seq,scale=b,quote=single.get('quote'))])

    registry=last(events,'routing.registry_match_completed')
    routes=registry.get('matched_actions') or []
    credits={enum(k.split('.')[0]) for a in asks for k in a.get('delivered_by',[]) if '.' in k}
    if registry.get('status')=='exact' and len(routes)==1 and len(credits)==1:
        out['K5']=signal(True,enum(routes[0]) not in credits,True,[evidence('routing.registry_match_completed',actions=routes),
                evidence('routing.capability_checked',seq,credited_prefixes=sorted(credits))])
    if any(e.get('event_type')=='routing.check_match_adopted' for e in events):
        out['K5']['notes'].append('check_match_adopted')

    alts=conditions.get('count_alternatives') or []
    unknown=conditions.get('unknown_facts') or []
    pairs=[]; repeated=[]
    for a in alts:
        prop='sample_count' if a.get('of')=='samples' else 'feature_count'
        for u in unknown:
            if overlap(task,a.get('quote'),u.get('quote')):
                repeated.append((a,u));
                if u.get('about') in ('sample_count','feature_count') and u.get('about')!=prop:
                    pairs.append(evidence('routing.capability_checked',seq,alternative=a,unknown=u,
                                          reason='same_quote_different_quantity_property'))
    fact=last(events,'core.fact_check')
    if fact.get('status')=='checked':
        for r in fact.get('rejected',[]):
            if str(r.get('rule','')).startswith('R1'):
                pairs.append(evidence('core.fact_check',rule=r.get('rule'),proposal=r.get('proposal'),
                                      reason='fact_proposal_rejected_by_uncertainty_reader'))
        legacy=[r for r in check.get('requirements',[]) if r.get('status')=='needs_fact' and not r.get('file_checked')]
        if legacy and not fact.get('accepted') and not fact.get('open_results'):
            pairs.append(evidence('core.fact_check',reason='legacy_wait_without_accepted_fact',
                                  legacy_quotes=[r.get('unknown_quote') for r in legacy]))
    eligible=bool(alts or unknown or fact.get('status')=='checked')
    out['K6']=signal(eligible,bool(pairs),bool(repeated),pairs,
                     [f'duplicated_count_unknown_pairs={len(repeated)}'] if repeated else [])

    artifact_map={'expression_matrix':'expression','regulatory_network':'network','coexpression_network':'network',
       'mutation_matrix':'mutations','motif_prior':'motif_prior','ppi_network':'ppi','design_matrix':'covariates',
       'mirna_prior':'mirna_list'}
    ruled=conditions.get('ruled_out_inputs') or []
    explicit=[x for h in hypotheses for x in h.get('evidence',[])
              if x.get('dimension')=='input_artifact' and x.get('source')=='explicit']
    comparisons=[];bad=[]
    for e in explicit:
        for r in ruled:
            if artifact_map.get(e.get('value'))==r.get('kind'):
                comparisons.append((e,r))
                if overlap(task,e.get('text_span'),r.get('quote')):
                    bad.append(evidence('routing.capability_checked',seq,semantic_evidence=e,ruled_out=r))
    out['K7']=signal(bool(comparisons),bool(bad),bool(comparisons),bad)

    count_pairs=[];setting_pairs=[]
    if single is not None:
        for a,b,label in [(single,conditions,'sample_count')]:
            if a.get(label) is not None and b.get(label) is not None and overlap(task,a.get(label+'_quote'),b.get(label+'_quote')):
                count_pairs.append({'property':label,'ask_value':a[label],'request_value':b[label],
                    'ask_quote':a.get(label+'_quote'),'request_quote':b.get(label+'_quote')})
        for a in single.get('feature_counts',[]):
            for b in conditions.get('feature_counts',[]):
                if overlap(task,a.get('quote'),b.get('quote')):
                    count_pairs.append({'property':'feature_count','ask_value':a.get('count'),
                        'request_value':b.get('count'),'ask_quote':a.get('quote'),'request_quote':b.get('quote')})
        for a in single.get('settings',[]):
            for b in conditions.get('settings',[]):
                if a.get('name')==b.get('name') and overlap(task,a.get('quote'),b.get('quote')):
                    setting_pairs.append({'setting':a.get('name'),'ask_value':a.get('value_quote',''),
                         'request_value':b.get('value_quote',''),'ask_quote':a.get('quote'),'request_quote':b.get('quote')})
    if count_pairs:
        bad=[evidence('routing.capability_checked',seq,**r) for r in count_pairs if r['ask_value']!=r['request_value']]
        out['K8']=signal(True,bool(bad),True,bad,[f'repeated_pairs={len(count_pairs)}'])
    if setting_pairs:
        bad=[evidence('routing.capability_checked',seq,**r) for r in setting_pairs if norm(r['ask_value'])!=norm(r['request_value'])]
        out['K9']=signal(True,bool(bad),True,bad,[f'repeated_pairs={len(setting_pairs)}'])

    view=last(events,'core.view')
    if 'mismatch' in view:
        out['K10']=signal(True,view['mismatch'] is True,False,[evidence('core.view',**view)] if view['mismatch'] else [])
    return out

def read_inputs():
    gold=json.loads(AUDIT01.read_text())['items']
    gold_by_session={x['trace']['session']:x for x in gold.values()}
    records=[]; inputs={}; diagnostics=Counter(); seen_events=set()
    for root in ROOTS:
        for p in sorted(root.rglob('events.jsonl')):
            s=p.with_name('session.json')
            if not s.exists():
                diagnostics['event_file_without_session']+=1;continue
            try:
                session=json.loads(s.read_text())
                events=[json.loads(line) for line in p.read_text().splitlines() if line.strip()]
            except (ValueError,OSError):
                diagnostics['unreadable_json_file']+=1;continue
            relevant=[(i,e) for i,e in enumerate(events) if e.get('event_type')=='routing.capability_checked'
                      and e.get('payload',{}).get('proposal')]
            if not relevant:continue
            inputs[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
            inputs[str(s)]={'sha256':sha(s),'bytes':s.stat().st_size}
            users=[m['content'] for m in session.get('messages',[]) if m.get('role')=='user']
            if not users:
                diagnostics['no_user_message']+=1;continue
            sid=session.get('session_id',p.parent.parent.name)
            for i,e in relevant:
                run_key=(e.get('run_id'),e.get('sequence'))
                if run_key in seen_events:
                    diagnostics['copied_event']+=1;continue
                seen_events.add(run_key)
                prop=e['payload']['proposal'];asks=asks_of(prop)
                fitting=[t for t in reversed(users) if all(span(t,a.get('quote')) is not None for a in asks)]
                task=fitting[0] if fitting else users[-1]
                if not fitting:diagnostics['task_quote_match_failed']+=1
                end=next((j for j in range(i+1,len(events)) if events[j].get('event_type')=='routing.capability_checked'),len(events))
                later=events[i+1:end]
                reread=next((x.get('payload') for x in later if x.get('event_type')=='routing.capability_reread'),None)
                content_key=hashlib.sha256(json.dumps([task,prop,reread],sort_keys=True).encode()).hexdigest()[:16]
                label=gold_by_session.get(sid)
                if label and norm(label['prompt'])!=norm(task):
                    label=None;diagnostics['gold_prompt_mismatch']+=1
                # Most traces contain one check. Earlier event snapshots are compared to saved
                # post-planning semantics explicitly as a screening limit, never called causal proof.
                sig=screen(task,prop,events,session,e.get('sequence'))
                records.append({'record_id':f'{e.get("run_id")}:{e.get("sequence")}',
                    'content_key':content_key,'session_id':sid,'event_source':str(p),'session_source':str(s),
                    'sequence':e.get('sequence'),'root':str(root),'task':task,
                    'gold':None if not label else {k:label.get(k) for k in ['id','set','class','outcome','cause','confidence','evidence']},
                    'signals':sig,'notes':{'capability_reread':reread is not None,
                    'task_quotes_all_matched':bool(fitting),
                    'core_kind':last(events,'core.decision').get('kind'),
                    'model_versions':[{'role':x.get('role'),'model':x.get('model'),'status':x.get('status')}
                                      for x in session.get('token_usage',{}).get('calls',[])]}})
    return records,inputs,dict(diagnostics),gold

def source_inventory():
    wanted={(path,name) for c in CATEGORIES.values() for path,name in c['refs']}
    refs={}; missing=[]
    for rel in sorted({p for p,_ in wanted}):
        p=CORE/rel
        if not p.exists():
            missing.extend([f'{rel}:{n}' for file,n in wanted if file==rel]);continue
        source=p.read_text();tree=ast.parse(source);SOURCE_INPUTS.add(p)
        def visit(nodes,parents=()):
            for node in nodes:
                if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                    name='.'.join((*parents,node.name))
                    if (rel,name) in wanted:
                        refs[(rel,name)]={'file':str(p),'function':name,'line':node.lineno,
                            'end_line':node.end_lineno,'source_sha256':sha(p),'docstring':ast.get_docstring(node)}
                    visit(node.body,(*parents,node.name))
        visit(tree.body)
        for file,name in wanted:
            if file==rel and (file,name) not in refs:missing.append(f'{file}:{name}')
    # Resolve re-export locations by AST after the graph reported the worktree excluded.
    for item in list(missing):
        rel,name=item.split(':',1)
        if '.' in name:continue
        candidates=[]
        for folder in ['interpretation','routing','graph']:
            for p in sorted((CORE/folder).glob('*.py')):
                try:t=ast.parse(p.read_text())
                except (SyntaxError,OSError):continue
                for n in t.body:
                    if isinstance(n,ast.FunctionDef) and n.name==name:
                        candidates.append((p,n))
        if len(candidates)==1:
            p,n=candidates[0];SOURCE_INPUTS.add(p)
            refs[(rel,name)]={'file':str(p),'function':name,'line':n.lineno,'end_line':n.end_lineno,
                'source_sha256':sha(p),'docstring':ast.get_docstring(n),'resolved_from_reexport':rel}
            missing.remove(item)
    inventory=[]
    for key,c in CATEGORIES.items():
        inventory.append({'category':key,**{k:v for k,v in c.items() if k!='refs'},
                          'references':[refs[(p,n)] for p,n in c['refs'] if (p,n) in refs]})
    return inventory,missing

def aggregate(records):
    result={}
    for k in CATEGORIES:
        eligible=[r for r in records if r['signals'][k]['eligible']]
        flagged=[r for r in eligible if r['signals'][k]['flagged']]
        labeled=[r for r in eligible if r['gold']]
        glf=[r for r in labeled if r['signals'][k]['flagged']]
        glu=[r for r in labeled if not r['signals'][k]['flagged']]
        def stats(xs):
            return {'n':len(xs),'wrong':sum(r['gold']['outcome']!='correct' for r in xs)}
        result[k]={'name':CATEGORIES[k]['name'],'eligible':len(eligible),'flagged':len(flagged),
            'repeated':sum(r['signals'][k]['repeated'] for r in records),
            'gold_eligible':stats(labeled),'gold_flagged':stats(glf),'gold_unflagged':stats(glu),
            'examples':[{'session_id':r['session_id'],'source':r['event_source'],'sequence':r['sequence'],
               'gold':r['gold'],'details':r['signals'][k]['details']} for r in flagged[:12]]}
        reasons=sorted({d['reason'] for r in flagged for d in r['signals'][k]['details'] if 'reason' in d})
        result[k]['subtypes']={}
        for reason in reasons:
            matched=[r for r in flagged if any(d.get('reason')==reason for d in r['signals'][k]['details'])]
            result[k]['subtypes'][reason]={'events':len(matched),
                'observations':sum(d.get('reason')==reason for r in matched for d in r['signals'][k]['details']),
                'gold':stats([r for r in matched if r['gold']])}
    return result

def supplement_veto(gold):
    path=WT/'docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4/veto.json'
    data=json.loads(path.read_text());out=[]
    for r in data['rows']:
        if r.get('status')!='checked':continue
        before=r.get('core_before') or {}; after=r.get('core_after') or {}
        out.append({'item':r['id'],'gold':gold.get(r['id'],{}).get('class'),
                    'before':before.get('kind'),'after':after.get('kind'),
                    'vetoes':r.get('vetoes',[]),'questions':r.get('questions',[]),
                    'source':str(path),'case_path':f'rows[id={r["id"]}]'})
    return out,{'path':str(path),'sha256':sha(path)}

def rebuilt_metrics(path):
    if not path:return None
    data=json.loads(path.read_text());c=Counter();examples=[]
    for key,row in data.items():
        check=row['check'];c['readings']+=1
        for f in check.get('facts',[]):
            if f.get('origin')=='derived':c['derived_facts']+=1;continue
            c['facts']+=1;c['reads']+=len(f.get('evidence',[]))
            readers={e.get('reader') for e in f.get('evidence',[])}
            c['repeated_facts']+=len(f.get('evidence',[]))>1
            if 'result' in readers:
                c['result_facts']+=1;c['also_request']+='request' in readers
                c['result_only']+='request' not in readers
            if f.get('state')=='unsure':
                c['unsure_facts']+=1
                c['duplicate_uncertainty_facts']+=readers>={'count_alternatives','unknown_facts'}
        for conflict in check.get('fact_conflicts',[]):
            c['conflicts']+=1
            reason=conflict.get('reason','');c['conflict:'+str(reason)]+=1
            examples.append({'record_key':key,'where':row['where'],'conflict':conflict})
    return {'source':str(path),'sha256':sha(path),'totals':dict(c),'conflicts':examples}

def pct(a,b):return f'{100*a/b:.1f}%' if b else '—'
def goldcell(s):return f"{s['wrong']}/{s['n']} ({pct(s['wrong'],s['n'])})" if s['n'] else '—'

def report(records,summary,inventory,missing,diagnostics,manifest,rebuilt,veto):
    lines=['# ROUND-07 補充：十類重複判斷盤點與既存紀錄量化','',
       '日期：2026-10-20。只讀程式與既存 JSON；沒有呼叫模型／API，沒有更改行為、prompt、YAML 或測試。','',
       '## 先說範圍與狀態','',
       '磁碟上的 `collab/ROUND-07-PLAN.md` 要求本盤點，但既有 REPORT 寫的是數量 G1–G3 修復。這份補充不覆寫既有 REPORT，也不把其 979 筆重放當成十類均已完成量化。','',
       f"程式快照：`{manifest['code_head']}`。當前原始碼的責任分工與歷史 session 的觀察分開列；歷史不一致不代表目前仍有同樣行為。",'',
       f"本次讀到 {len(records)} 個有 proposal 的 capability-check event，來自 {len({r['session_id'] for r in records})} 個 session_id、{len({r['content_key'] for r in records})} 種 task/proposal/reread 組合。不同模型版本與回合不是獨立隨機樣本。",'',
       f"其中可精確連回 ROUND-01 金標 baseline 的有 {sum(bool(r['gold']) for r in records)} 個事件；其餘不補造對錯。沒有 capability proposal 的失敗 session 不在主分母，另見金標覆蓋表。",'',
       '**flag 是待檢視的差異訊號，不是「這一類造成了幾個錯誤」。** 值不同可能是正確修正、不同作用域或兩種文字表示；有金標也只量關聯，不能直接當因果。','',
       '## 1. 主分母：歷史事件的可比資料與差異訊號','',
       '| 類別 | 可比事件 | 重填／雙來源事件 | 差異訊號 | 訊號率 | 金標有訊號：錯/總 | 金標無訊號：錯/總 |',
       '|---|---:|---:|---:|---:|---|---|']
    for k,s in summary.items():
        lines.append(f"| {k} {s['name']} | {s['eligible']} | {s['repeated']} | {s['flagged']} | {pct(s['flagged'],s['eligible'])} | {goldcell(s['gold_flagged'])} | {goldcell(s['gold_unflagged'])} |")
    lines += ['', '分母依各類是否有足夠欄位而不同。K7 的窄比較若樣本很少，不代表資料歸屬風險很小；K10 沒有 renderer mismatch flag 也不代表回覆內容一定正確。K8/K9 只在單一要求及原文重疊時配對；同一引文可能含多個對象，仍需人工核對。', '',
       '### K6 必須拆開看','',
       'K6 的總訊號混合「兩份數量讀取不一致」與「程式成功拒收追問」；不能用總數 319 當錯誤數或收益排名。細項如下；同事件可同時屬於兩項。','',
       '| 子類 | 事件數 | 細項數 | 金標錯/總 |','|---|---:|---:|---|']
    for reason,s in summary['K6']['subtypes'].items():
        lines.append(f"| {reason} | {s['events']} | {s['observations']} | {goldcell(s['gold'])} |")
    lines += ['', '## 2. 各類責任、消費者、優先權與來源','']
    for item in inventory:
        k=item['category'];lines += [f"### {k} {item['name']}",'',
          '- 性質：'+item['kind'], '- 產生者：'+'；'.join(item['producers']),
          '- 讀取者：'+'；'.join(item['consumers']), '- 衝突／優先規則：'+item['precedence'],
          '- 本輪可量口徑：'+item['metric'], '- 限制：'+item['limit'],'','來源：']
        for ref in item['references']:
            lines.append(f"- [{Path(ref['file']).name}:{ref['function']}:{ref['line']}](<{ref['file']}:{ref['line']}>)")
        lines.append('')
    lines += ['## 3. 差異樣例（可追到 session/event；不自動認定病因）','']
    for k,s in summary.items():
        lines += [f"### {k} {s['name']}",'']
        if not s['examples']:
            lines.append('本口徑未觀察到訊號，或沒有足夠可比欄位；不作不存在問題的推論。\n');continue
        for ex in s['examples'][:4]:
            g=ex['gold'];label=f"；gold={g['outcome']}" if g else '；無精確 baseline 金標'
            lines += [f"- `{ex['session_id']}` capability event sequence={ex['sequence']}{label}；[events](<{ex['source']}>)",
                      '```json',json.dumps(ex['details'],ensure_ascii=False,indent=2),'```','']
    lines += ['## 4. 現行程式重建的共用紀錄（若提供）','']
    if rebuilt:
        lines += ['使用既有 ROUND-03 replay 對固定 readings 做純程式重建；不重跑任何模型。與前述歷史端到端判定不是同一口徑。','',
                   '```json',json.dumps(rebuilt['totals'],ensure_ascii=False,indent=2),'```','',
                   '新增 metadata 或衝突紀錄不等於判定改善；所有重建衝突另存 rebuilt-metrics.json。','']
    else:lines += ['本次未完成 production-module 重建；不以靜態掃描替代既有 ROUND-03 的 979 筆重建數字。','']
    lines += ['## 5. 否決層獨立抽樣','',
       f"h4/veto.json 有 {len(veto)} 筆 checked 讀取。它們是與 baseline 成對的另一份讀取，不合併進上面一般 capability event 分母。詳 supplemental-veto.json。",'',
       'M38（DO→DECLINE）、M48（DO→DECLINE）、M31（DO→ASK）等既知差異，只引用其原始記錄與 H2 評分，不將「改變」一律當成錯誤。這些是 ROUND-02 前的歷史紀錄，不能當成現在仍未修復的證據。','',
       '## 6. 排序與下一個收斂範圍','',
       '**建議先處理 K6 的數量不確定性雙入口，與 K8 的數量歸屬一起界定責任。** 這是按可定位的結構衝突及現行路徑排序，並非估計修好多少題。','',
       '1. K6/K8：同段數量分到不同 property 有 2 個事件（同一道 C45 的兩次讀取）；現行純程式重建另有 C45 三次與 H46 一次的 sample_count 擱置。前者能直接核對出「蛋白數當樣本數」的內部矛盾；其中也有不確定數量入口缺失、另一入口單獨讀錯的情況。不能相加算六題，也不能把 319 個 guard 訊號當成錯誤。先讓數量的 property、對象、不確定性及使用／擱置理由只有一個解析後的權威入口；第一讀本身錯誤仍需另行追蹤。','',
       '2. K10：625 個有 core.view 的事件中 5 個明記 mismatch（0.8%）；精確金標只有 2 個，均為錯誤。優先逐案確認現行版本能否重現；若仍重現，再收斂核心決定與 renderer 的責任。兩個金標的 cause 含 L2_no_check/X_other，不能聲稱 mismatch 就是全部病因。','',
       '3. K9：ROUND-06 已把 run 綁定收斂，應保留這項成果。單一要求且引文重疊的 112 個雙來源事件，本口徑沒有不同 value_quote；但它不會量出「同值被兩個消費者用不同規則解讀」。依 ROUND-06 現成的 180-run 配對重放，10 個 turn 改變且已逐項驗證；這才是此類已有的直接修復證據，不列成現行新故障。C40 清單歸在「值已讀到、執行綁定仍無法表示」，不要先加原文詞表。','',
       '4. K4、K5、K3、K2：差異分別為 48/293、18/305、80/441、61/723。金標差異中也有正確案例，且 K3/K4 使用後期語意快照；不宜現在直接合併成一個值。先保留「前段假設、後段更正、最終採用理由」的界線。K4 差異金標錯誤 3/6 的 cause 是限額／部分承諾，未證明粒度差異造成錯誤。','',
       '5. K1/K7 與 K8/K9 的零值衝突不能代表已解決。K7 只有 1 筆能做窄比較，屬觀測不足；K1 是名稱不同的窄口徑。K8/K9 仍有大量重填，也可能兩份一致地讀錯或作用域錯。','',
       '**目前能完成的是十類盤點、可觀察差異與金標關聯的排序；尚不能從既存紀錄得到十類的完整「因果錯誤數」或現行端到端錯誤率。** 本輪未做完整 Router/Planner replay、未重新呼叫語意或事實模型、未跑新盲題。','',
       '## 7. 限制與重現','',
       '- scope 限於計畫 K1–K10 所列 routing／interpretation／response 及其 run/planning 接縫；未完整審計 Executor 或所有 planner 模組。不是全專案所有函式的形式化證明。',
       '- workspace graph generation 2026-10-16T10:16:00Z 明確排除 .worktrees；圖搜尋無結果後，以限定 source AST 與原始碼讀取補足。來源行號及 SHA 在 inventory.json。',
       '- 部分已保存語意值是 Planner 後快照，無法完整還原第一次成功讀取。K3/K4 僅是跨階段差異訊號。',
       '- 報表分開保存全部事件與去除相同 task/proposal/reread 組合後的敏感度分析。任一類的不同訊號可落在同一個 session，不能相加當總錯誤。',
       '- 金標只套用到 session_id 和 prompt 均吻合的原 baseline；不把同題其他版本／smoke 的對錯套過來。',
       '- 所有 session 與輸入紀錄保持原樣。資料解析限制：'+json.dumps(diagnostics,ensure_ascii=False),
       '- 未解析的 source references：'+json.dumps(missing,ensure_ascii=False),'',
       '```sh','python3 -I audit.py',
       '# 若要加入現行程式對 readings 的純程式重建指標：',
       'python3 -I audit.py --rebuilt /absolute/path/to/checks.json','```','',
       '重新生成 summary.json、records.json、inventory.json、manifest.json、supplemental-veto.json 與本報告。相同來源的核心輸出必須逐位元一致。']
    return '\n'.join(lines)+'\n'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rebuilt',type=Path);args=parser.parse_args()
    records,inputs,diagnostics,gold=read_inputs()
    inventory,missing=source_inventory()
    summary=aggregate(records)
    unique={}
    for r in records:unique.setdefault(r['content_key'],r)
    labeled_ids={r['gold']['id'] for r in records if r['gold']}
    gold_coverage={'total':len(gold),'with_capability_proposal':len(labeled_ids),
        'all_baseline_wrong':sum(v['outcome']!='correct' for v in gold.values()),
        'covered_baseline_wrong':sum(v['outcome']!='correct' for k,v in gold.items() if k in labeled_ids),
        'missing':[{'id':key,'outcome':v['outcome'],'cause':v.get('cause'),
                    'session':v['trace']['session']} for key,v in gold.items() if key not in labeled_ids]}
    rebuilt=rebuilt_metrics(args.rebuilt)
    veto,veto_input=supplement_veto(gold)
    inputs[str(AUDIT01)]={'sha256':sha(AUDIT01),'bytes':AUDIT01.stat().st_size}
    inputs[veto_input['path']]={'sha256':veto_input['sha256'],'bytes':Path(veto_input['path']).stat().st_size}
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()
    manifest={'code_head':head,'worktree':str(WT),'data_roots':list(map(str,ROOTS)),
       'protocol':'ROUND-07 inventory supplement, zero API/model calls',
       'event_records':len(records),'unique_content_records':len(unique),'gold_coverage':gold_coverage,
       'inputs':dict(sorted(inputs.items())),'source_files':{str(p):sha(p) for p in sorted(SOURCE_INPUTS)},
       'missing_source_references':missing,'diagnostics':diagnostics}
    manifest['audit_script_sha256']=sha(Path(__file__))
    manifest['rebuild_source']=None if not args.rebuilt else {'path':str(args.rebuilt),'sha256':sha(args.rebuilt)}
    dump(HERE/'inventory.json',inventory);dump(HERE/'records.json',records)
    dump(HERE/'summary.json',{'all_events':summary,'unique_content':aggregate(list(unique.values())),
                             'gold_coverage':gold_coverage})
    dump(HERE/'supplemental-veto.json',veto)
    if rebuilt:dump(HERE/'rebuilt-metrics.json',rebuilt)
    dump(HERE/'manifest.json',manifest)
    (HERE/'AUDIT.md').write_text(report(records,summary,inventory,missing,diagnostics,manifest,rebuilt,veto))
    print(json.dumps({'events':len(records),'unique_content':len(unique),'gold_coverage':gold_coverage,
          'categories':{k:{x:v[x] for x in ['eligible','flagged','repeated','gold_flagged','gold_unflagged']} for k,v in summary.items()},
          'missing_source_references':missing},ensure_ascii=False))

if __name__=='__main__':main()

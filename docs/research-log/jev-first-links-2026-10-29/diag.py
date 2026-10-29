import json,sys,copy,re
sys.path.insert(0,'.'); sys.path.insert(0,'../../../scripts')
import shadow
from collections import Counter
from netzoo_agent_core.capability_sheet import entry
NEUTRAL={"data_unit":"not_stated","group_membership":"not_stated","time_model":"not_dynamic","spatial":"not_spatial",
 "regulator_kinds":[],"needs_sign":False,"omics_layers":0,"input_network":"not_stated","scale":"unstated",
 "samples_matched":"not_stated","mutation_origin":"not_stated","value_type":"not_stated","mirna_driver":"not_stated"}
COUNTS={"sample_count":None,"sample_count_quote":"","feature_counts":[],"settings":[],"named_method":"none","named_method_quote":""}
golds=shadow.gold(); _,ids=shadow.menu(); cache=shadow._cache()
R={r['where']:r for r in json.load(open('shadow.json')) if not r.get('excluded')}
cause=Counter(); detail=[]
for folder,item,prop in shadow.readings(golds):
    r=R.get(str(folder.relative_to(shadow.LOGS)))
    if not r or r['gold']!='DO' or r['credited']['H']: continue
    want=set(r['workflows'])|set(r['also'])
    task=golds[item]['prompt']
    H=copy.deepcopy(prop); linked=[]
    for name,i,ask in shadow.asks(prop):
        f=cache.get(shadow._key(task,ask['quote']))
        if f and 'error' not in f and f['confidence']>=0.7:
            H[name]['asks'][i]['delivered_by']=[ids[f['choice']]] if f['choice'] in ids else []
        if any(entry(k).workflow in want for k in H[name]['asks'][i]['delivered_by']): linked.append((name,i))
    if not linked: continue
    found=[]
    for field,val in {**NEUTRAL, 'counts':None}.items():
        P=copy.deepcopy(H)
        for name,i in linked:
            if field=='counts': P[name]['asks'][i].update(COUNTS); P.get('conditions',{}).update({k:v for k,v in COUNTS.items() if k in P.get('conditions',{})})
            else: P[name]['asks'][i][field]=val
        c=shadow._credited(task,P)
        if c and set(c)<=want: found.append(field)
    if not found:
        P=copy.deepcopy(H)
        for name,i in linked: P[name]['asks'][i].update(NEUTRAL); P[name]['asks'][i].update(COUNTS)
        c=shadow._credited(task,P); found=['ALL-neutral works' if c and set(c)<=want else 'still nothing']
    vals={f: H[linked[0][0]]['asks'][linked[0][1]].get(f) for f in found if f in NEUTRAL}
    cause[tuple(found)]+=1; detail.append((item, r['workflows'], found, vals))
print(cause)
for d in detail: print(d)

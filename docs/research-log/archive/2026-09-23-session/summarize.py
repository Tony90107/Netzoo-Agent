import json,sys
d=json.load(open(sys.argv[1]))
for r in d['results']:
    o=r['outcome']
    print(f"{r['id']:20s} t{r['trial']} {'PASS' if r['passed'] else 'fail'} st={r['status']} act={r['matched_actions']} hyp={r['hypothesis_actions']} gran={o.get('granularity')} art={o.get('artifact_type')} regs={o.get('regulator_types')} ents={o.get('entity_types')} in={o.get('input_artifacts')} tags={o.get('selection_tags')} roles={r['call_roles']} path={r['path']} basis={r['match_basis']}")
    for e in r['errors']: print('     -', e[:160])

import json, sys, collections
EXP={"t1-otter":"run_otter","t1-giraffe":"run_giraffe","t1-panda":"run_panda","t2-cobra":"run_cobra","t2-lioness":"run_lioness_coexpression"}
TIE={"t1":"tie1","t2":"tie2"}
rows=[]
for path in sys.argv[1:]:
    r=json.load(open(path))
    for row in r["results"]:
        t=row["_trace"]; d=t["decision"]; ev={}
        for e in t["events"]: ev.setdefault(e["type"],e["payload"])
        reg=ev.get("routing.registry_match_completed",{}); adv=d.get("advisory_recommendation")
        rows.append(dict(id=row["id"],path=t.get("reason_code"),status=reg.get("status"),acts=reg.get("matched_actions") or reg.get("hypothesis_actions"),
            ran="routing.selection_conditions_started" in ev, rec=adv and adv["action"], quotes=adv and [(c["axis"]+":"+c["value"],c["text_span"]) for c in adv["conditions"]],
            claims=(ev.get("routing.selection_conditions_unresolved") or {}).get("claims"), tagdisc=(ev.get("routing.semantic_discriminator_accepted") or {}).get("selection_tags"),
            leak=bool(d.get("should_execute")) or d.get("action")!="no_tool"))
for x in rows: print(json.dumps(x,ensure_ascii=False))
for tie in ("t1","t2"):
    F=[x for x in rows if x["id"].startswith(tie) and x["id"] in EXP]; D=[x for x in F if x["ran"]]
    N=[x for x in rows if x["id"]==f"{tie}-none"]; ND=[x for x in N if x["ran"]]
    print(f"{TIE[tie]}: D={len(D)}/{len(F)} correct={sum(x['rec']==EXP[x['id']] for x in D)} wrong={sum(x['rec'] is not None and x['rec']!=EXP[x['id']] for x in D)} | none ran={len(ND)}/{len(N)} recs={sum(x['rec'] is not None for x in ND)}")
print("leaks:",sum(x["leak"] for x in rows))

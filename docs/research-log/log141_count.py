import json, sys
EXPECT={"f1-few-trust":"run_bonobo","f2-many":"run_lioness_coexpression","f3-six-pvalue":"run_bonobo"}
def summarize(path):
    r=json.load(open(path)); rows=[]
    for row in r["results"]:
        t=row["_trace"]; d=t["decision"]; ev={}
        for e in t["events"]: ev.setdefault(e["type"],e["payload"])
        reg=ev.get("routing.registry_match_completed",{})
        ran="routing.selection_conditions_started" in ev
        outcome=("recommended" if "routing.selection_conditions_recommended" in ev else
                 "unresolved" if "routing.selection_conditions_unresolved" in ev else
                 "failed" if "routing.selection_conditions_failed" in ev else "-")
        adv=d.get("advisory_recommendation")
        rows.append(dict(id=row["id"],path=t.get("reason_code"),reg=(reg.get("status"),reg.get("matched_actions"),reg.get("hypothesis_actions")),
            ran=ran,outcome=outcome,rec=adv and adv["action"],quotes=adv and [(c["axis"]+":"+c["value"],c["text_span"]) for c in adv["conditions"]],
            claims=(ev.get("routing.selection_conditions_unresolved") or {}).get("claims"),
            rejected=(ev.get("routing.selection_conditions_unresolved") or ev.get("routing.selection_conditions_recommended") or {}).get("rejected"),
            err=(ev.get("routing.selection_conditions_failed") or {}).get("error_message","")[:200],
            execute=d.get("should_execute"),action=d.get("action")))
    return rows
rows=[x for p in sys.argv[1:] for x in summarize(p)]
for x in rows: print(json.dumps(x,ensure_ascii=False))
F=[x for x in rows if x["id"] in EXPECT]; N=[x for x in rows if x["id"].startswith("n")]
D=[x for x in F if x["ran"]]; ND=[x for x in N if x["ran"]]
hit=sum(x["rec"]==EXPECT[x["id"]] for x in D); wrong=sum(x["rec"] is not None and x["rec"]!=EXPECT[x["id"]] for x in D)
print(f"\nD={len(D)} (of {len(F)} F trials) | Z-2 hits={hit} | Z-2b wrong={wrong}")
print(f"N ran={len(ND)} (of {len(N)}) | Z-3 recommendations={sum(x['rec'] is not None for x in ND)}")
print(f"Z-4 authority leaks={sum(bool(x['execute']) or x['action']!='no_tool' for x in rows)}")

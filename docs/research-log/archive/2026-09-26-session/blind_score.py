import json, sys, collections
EXPECT={1:{"run_giraffe"},2:{"run_otter"},3:{"run_bonobo"},4:{"run_lioness_panda","run_giraffe"},5:{"run_puma"},
        6:{"run_cobra"},7:{"run_dragon"},8:{"run_sambar"},9:{"run_condor"},10:set()}
r=json.load(open(sys.argv[1])); by=collections.defaultdict(list)
for row in r["results"]:
    t=row["_trace"]; d=t["decision"]; ev={}
    for e in t["events"]: ev.setdefault(e["type"],e["payload"])
    reg=ev.get("routing.registry_match_completed",{}); adv=d.get("advisory_recommendation")
    n=int(row["id"].split("-")[0][4:])
    status=reg.get("status"); matched=reg.get("matched_actions") or []; cands=reg.get("hypothesis_actions") or []
    rec=adv and adv["action"]
    if t.get("reason_code")=="semantic_fallback": verdict="FALLBACK"
    elif n==10: verdict="OK(no tool)" if not matched and d.get("action")=="no_tool" else "WRONG"
    elif status in ("exact","fallback") and set(matched)&EXPECT[n]: verdict="OK(exact)"
    elif rec in EXPECT[n]: verdict="OK(recommended)"
    elif status=="ambiguous" and set(cands)&EXPECT[n]: verdict="PARTIAL(candidates)"
    else: verdict="WRONG"
    leak=bool(d.get("should_execute")) or d.get("action")!="no_tool"
    by[n].append((verdict, status, matched or cands, rec, leak))
tot=collections.Counter()
for n in sorted(by):
    for v in by[n]: tot[v[0].split("(")[0]]+=1
    print(f"Case {n}: " + " | ".join(f"{v[0]} {v[1]} {v[2]}{' rec='+v[3] if v[3] else ''}{' LEAK' if v[4] else ''}" for v in by[n]))
print(dict(tot))

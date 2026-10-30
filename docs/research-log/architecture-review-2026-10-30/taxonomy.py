"""Every wrong final of the fresh-set live runs (each run on a set it had not seen), with trace features for a cause.
No model calls."""
import json, glob, re, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent; LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "harness-repair-2026-10-23"))
from score import kind_of
RUNS = {"j5a": "jev-j5-2026-10-28/j5", "j6a": "jev-j6-2026-10-29/j6", "j7off": "jev-links-first-2026-10-29/j7",
        "j8new": "j8-paired-2026-10-29/j8"}
def ev(t, name):
    out = []
    for f in sorted(glob.glob(f"{t}/trace-*.jsonl")):
        for l in open(f):
            if f'"{name}"' in l and (e := json.loads(l))["event_type"] == name: out.append(e["payload"])
    return out
def asks(p):
    for k, v in (p or {}).items():
        if re.fullmatch(r"s\d+", k) and isinstance(v, dict): yield from v.get("asks", [])
rows = []
for tag, itemdir in RUNS.items():
    items = {i["id"]: i for i in json.load(open(LOGS / itemdir / "items.json"))["single"]}
    for folder in sorted(glob.glob(str(LOGS / "**" / "live" / tag / f"hb-{tag}-*-1"), recursive=True)):
        job = json.load(open(folder + "/job.json")); it = items[job["item"]]
        sent = job["sent"]
        g = it["final_after_fact"] if "fact" in sent and it.get("final_after_fact") else \
            it["final_after_result"] if "result" in sent and it.get("final_after_result") else \
            {"call": it["expected_call"], "workflows": it["workflows"]}
        gold = "DO" if g["call"] == "PARTIAL" else g["call"]
        turns = sorted(glob.glob(folder + "/t[0-9]"))
        cores = [(ev(t, "core.decision") or [{}])[-1] for t in turns]
        final = cores[-1].get("kind") or "none"
        verdict = kind_of(gold, final)
        if verdict == "right":
            continue
        feat = {"turns": len(turns), "path": " ; ".join(f"{c.get('kind')}/{c.get('basis')}" for c in cores)}
        goldwf = set(g.get("workflows") or []) | set(it.get("also_acceptable_workflows") or [])
        t1 = (ev(turns[0], "routing.capability_checked") or [{}])[0]
        from_entry = lambda k: k.split(".")[0].upper().replace("_", "-")
        prop_links = {from_entry(k) for a in asks(t1.get("proposal")) for k in a.get("delivered_by") or []}
        credited = {from_entry(k) for r in (t1.get("check") or {}).get("requirements", [])
                    if r.get("kind") == "result" and r.get("status") in ("available", "with_step", "partial", "needs_fact")
                    for k in r.get("delivered_by") or []}
        feat |= {"t1_linked": sorted(prop_links), "t1_credited": sorted(credited), "gold_wf": sorted(goldwf)}
        lost = False
        for a, b in zip(turns, turns[1:]):
            pa = (ev(a, "routing.capability_checked") or [{}])[0].get("proposal"); pb = (ev(b, "routing.capability_checked") or [{}])[0].get("proposal")
            prev = {x["quote"] for x in asks(pa) if x.get("delivered_by")}
            if any(x["quote"] in prev and not x.get("delivered_by") for x in asks(pb)): lost = True
        feat["relink_lost"] = lost
        feat["provider_error"] = any(ev(t, "routing.capability_check_failed") for t in turns)
        bound = [p for t in turns for p in ev(t, "task.answers_bound")]
        feat["answers_bound"] = len(bound)
        rows.append({"run": tag, "id": it["id"], "group": it.get("category"), "gold": gold, "final": final,
                     "verdict": verdict, "sent": sent, **feat,
                     "gold_reason": (it.get("reason") or "")[:160], "prompt": it["prompt"][:200]})
(HERE / "wrong.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
print(len(rows), Counter(r["verdict"] for r in rows), Counter(r["run"] for r in rows))

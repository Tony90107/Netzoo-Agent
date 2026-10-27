import json, sys, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-overlap/scripts")
from netzoo_agent_core.graph.jev_guard_call import _decide
from overlap_q import INSTRUCTIONS, CRITERIA, state
pop = json.load(open("population.json"))
by = {}
for p in pop: by.setdefault(p["request"], p)
reqs = list(by.values())
pick = {0: "Q26", 15: "Q01", 11: "Q29", 4: "ON5", 5: "QN5", 6: "SN1"}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
def one(i):
    p = reqs[i]
    out = _decide(state(p["request"], p["quote"]),
                  {"overlap": {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}})
    a = out["answers"]["overlap"]
    return i, a["choice"], round(a["confidence"], 3), (out.get("usage") or {}).get("cost", 0)
jobs = [i for i in pick for _ in range(N)]
res = collections.defaultdict(list); cost = 0
with ThreadPoolExecutor(4) as ex:
    for i, c, conf, k in ex.map(one, jobs):
        res[i].append((c, conf)); cost += k or 0
summary = {}
for i, v in res.items():
    ch = collections.Counter(c for c, _ in v); confs = sorted({x for _, x in v})
    summary[pick[i]] = {"choices": dict(ch), "conf_min": confs[0], "conf_max": confs[-1]}
    print(pick[i].ljust(4), dict(ch), "conf", confs[0], "-", confs[-1])
print("calls", len(jobs), "cost US$", round(cost, 4))
json.dump({"N": N, "summary": summary, "cost": cost}, open("stability.json", "w"), indent=1)

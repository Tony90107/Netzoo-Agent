import json, sys, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-link/scripts")
from netzoo_agent_core.jev_client import decide
from forms_q import QUESTIONS, state
pop = json.load(open("population.json"))
first = {}
for p in pop:
    first.setdefault(p["session"].split("-")[2] + "/" + p["turn"], p)
PICK = [("time_model", "R13/t1"), ("time_model", "C23/t1"), ("time_model", "HN2/t1"), ("time_model", "RN1/t1"),
        ("spatial", "QN10/t1"), ("spatial", "SN8/t1"), ("spatial", "R13/t1"),
        ("input_network", "R39/t1"), ("input_network", "J40/t1"), ("input_network", "Q18/t1"),
        ("input_network", "Q34/t1")]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
def one(job):
    attr, key = job
    p = first[key]
    q = QUESTIONS[attr]
    out = decide(state(attr, p["request"], p["quote"]),
                 {"q": {"type": "choice", "instructions": q["instructions"], "criteria": q["criteria"]}}, timeout=30)
    a = out["answers"]["q"]
    return job, a["choice"], a.get("probabilities") or {}, (out.get("usage") or {}).get("cost", 0)
jobs = [job for job in PICK for _ in range(N)]
res, cost = collections.defaultdict(list), 0
with ThreadPoolExecutor(4) as ex:
    for job, choice, probs, c in ex.map(one, jobs):
        res[job].append((choice, probs)); cost += c or 0
summary = {}
for job, v in res.items():
    counts = collections.Counter(c for c, _ in v)
    keys = sorted({k for _, p in v for k in p})
    ranges = {k: (min(p.get(k, 0) for _, p in v), max(p.get(k, 0) for _, p in v)) for k in keys}
    summary[f"{job[0]}:{job[1]}"] = {"choices": dict(counts), "p_range": ranges}
    print(f"{job[0]:14} {job[1]:8}", dict(counts), {k: r for k, r in ranges.items() if r[1] > 0.01})
print("calls", len(jobs), "cost US$", round(cost, 4))
json.dump({"N": N, "summary": summary, "cost": cost}, open("stability.json", "w"), indent=1)

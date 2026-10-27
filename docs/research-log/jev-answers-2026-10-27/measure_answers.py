"""B1/B2 offline: Jev's read of each answer with the frozen question of its dimension (answer_q.py). Writes reads.json."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
sys.path.insert(0, str(HERE))
from answer_q import BIND, VALUES, state  # noqa: E402
from netzoo_agent_core.interpretation import jev_overlap  # noqa: E402
from netzoo_agent_core.interpretation.jev_forms import QUESTIONS  # noqa: E402
from netzoo_agent_core.interpretation.needed_facts import DIMENSIONS  # noqa: E402
from netzoo_agent_core.jev_client import decide  # noqa: E402


def question(dim):
    if dim == "group_membership":
        return jev_overlap.INSTRUCTIONS, jev_overlap.CRITERIA
    return QUESTIONS[dim]["instructions"], QUESTIONS[dim]["criteria"]


def read(dim, answer):
    instructions, criteria = question(dim)
    out = decide(state(DIMENSIONS[dim][1], answer), {"q": {"type": "choice", "instructions": instructions,
                                                           "criteria": criteria}}, timeout=30)
    probs = out["answers"]["q"].get("probabilities") or {}
    by_value = {}
    for option, value in VALUES[dim].items():
        by_value[value] = by_value.get(value, 0) + probs.get(option, 0)
    bound = next((value for value, p in by_value.items() if p >= BIND), None)
    return {"probabilities": probs, "bound": bound, "cost": (out.get("usage") or {}).get("cost", 0)}


rows = []
for case in json.loads((HERE / "cases.json").read_text()):
    if case["bound"]:
        continue  # B3: code binds these; Jev is not read
    for dim in case["dims"]:
        expect = {"input_network": "regulator_gene", "group_membership": "one_group"}[dim] \
            if case["sent"] in ("form", "membership") else "none"
        rows.append({"id": f"{case['session']}/{case['turn']}", "dim": dim, "answer": case["answer"], "expect": expect,
                     **read(dim, case["answer"])})
for item in json.loads((HERE / "synthetic.json").read_text())["items"]:
    rows.append({"id": item["id"], "dim": item["dim"], "answer": item["answer"], "expect": item["expect"],
                 **read(item["dim"], item["answer"])})
(HERE / "reads.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    print(f"{r['id']:22} {r['dim']:17} expect {r['expect']:18} bound {str(r['bound']):15}",
          {k: v for k, v in r["probabilities"].items() if v > 0.01})
print("cost", round(sum(r["cost"] or 0 for r in rows), 5))

"""Log 383 prep: the data-needs plan's need reading on SEEN sessions (calibration only, never a verdict).

Usage (repository root): python3 docs/research-log/data-plan-2026-10-06/plan_eval.py
For each recorded session of Logs 380-381 (s20, s21; both arms, so both routing samples), the plan's
need is read from the session's own study purpose and routing reading, and compared with the set's
`question_needs` label. Also: what the plan would ask (with the session's data-facts reading where
one exists, else the request's words) against `data_question`. No model is called.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.data_plan import build_data_plan, plan_needs  # noqa: E402
from netzoo_agent_core.routing.capability_compatibility import input_availability  # noqa: E402

R = ROOT / "docs/research-log"
SETS = {"s20": (R / "applicability-2026-10-06/live/s20-decisions.json", R / "applicability-2026-10-06/heldout20/heldout.json"),
        "s21": (R / "applicability-redo-2026-10-06/live/s21-decisions.json", R / "applicability-redo-2026-10-06/heldout21/heldout.json")}
HERE = Path(__file__).resolve().parent
# The data-facts reading of every item (current prompt, verified as production verifies it), rep-matched.
READINGS = {"s20": HERE / "dev20b-calls.json", "s21": HERE / "dev21-calls.json"}


def readings(tag):
    from netzoo_agent_core.contracts.data_facts import DataFactsProposal
    from netzoo_agent_core.graph.data_facts_call import verify_data_facts
    out = {}
    for row in json.loads(READINGS[tag].read_text()):
        if row["proposal"] is not None:
            out[(row["id"], row["rep"])] = verify_data_facts(row["prompt"], DataFactsProposal.model_validate(row["proposal"]))[0]
    return out


def main():
    need, ask, notes = Counter(), Counter(), []
    for tag, (decisions, heldout) in SETS.items():
        items = {i["id"]: i for i in json.loads(heldout.read_text())["items"]}
        read = readings(tag)
        for key, row in json.loads(decisions.read_text()).items():
            arm, item_id, rep = key.split("-")
            item = items[item_id]
            decision = TaskDecision.model_validate(row["decision"])
            claims = (row.get("study_purpose") or {}).get("claims") or ()
            answerable, basis, kinds = plan_needs(claims, decision, row["prompt"])
            label_tf = item["question_needs"] != "none"
            label_mirna = "mirna" in item["question_needs"]
            got_tf, got_mirna = "tf_priors" in kinds, "mirna" in kinds
            need[("tf", label_tf, got_tf)] += 1
            need[("mirna", label_mirna, got_mirna)] += 1
            need[("basis", basis)] += 1
            if got_tf != label_tf or got_mirna != label_mirna:
                notes.append(f"  {tag} {key}: label {item['question_needs']} got {kinds} ({basis}) "
                             f"claims {[c for c, _ in claims]} | {item['purpose_sentence'][:90]}")
            facts = read.get((item_id, int(rep)), {})
            plan = build_data_plan(claims, decision, facts, set(input_availability(row["prompt"]).present), row["prompt"])
            asks = "priors" if "tf_priors" in plan.asks() else ("mirna" if "mirna" in plan.asks() else "none")
            ask[(arm, item["data_question"], asks)] += 1
            if (asks == "priors") != (item["data_question"] == "priors"):
                notes.append(f"  ASK {tag} {key}: label {item['data_question']} plan {asks}; priors {item['priors_label']} "
                             f"read {facts.get('priors')} {facts.get('priors_quote','')[:50]!r}; needs {kinds}")
    print("need (kind, label, read): count")
    for k, n in sorted(need.items(), key=str):
        print(f"  {k}: {n}")
    print("plan asks (arm, data_question label, plan asks): count")
    for k, n in sorted(ask.items()):
        print(f"  {k}: {n}")
    print(f"{len(notes)} need disagreements")
    print("\n".join(notes))


if __name__ == "__main__":
    main()

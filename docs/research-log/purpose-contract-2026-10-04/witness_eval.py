"""Log 344 prep: score the study-purpose witnesses on a labelled set, against the frozen v1.

Usage (repository root): python3 docs/research-log/purpose-contract-2026-10-04/witness_eval.py <heldout.json> [--quiet]
Prints design and primary-claim recall (labels other than none), false hits
(a value where the label says none, or a different value), and every
disagreement, for the current `routing/study_purpose.py` and for v1
(`study_purpose.frozen.py`). Nothing calls a model.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.routing import study_purpose as current  # noqa: E402

spec = importlib.util.spec_from_file_location("study_purpose_v1", HERE / "study_purpose.frozen.py")
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)


def score(module, items):
    counts = {"design_labelled": 0, "design_hit": 0, "design_false": 0,
              "claim_labelled": 0, "claim_hit": 0, "claim_false": 0, "gap_false": 0}
    misses = []
    for item in items:
        purpose = module.study_purpose(item["prompt"])
        design, claim = purpose.design or "none", purpose.claim or "none"
        claims = {c for c, _ in purpose.claims}
        if item["comparison_design"] != "none":
            counts["design_labelled"] += 1
            counts["design_hit"] += design == item["comparison_design"]
        if design != "none" and design != item["comparison_design"]:
            counts["design_false"] += 1
        if item["claim_kind"] != "none":
            counts["claim_labelled"] += 1
            counts["claim_hit"] += claim == item["claim_kind"]
        if claim != "none" and claim != item["claim_kind"]:
            counts["claim_false"] += 1
        if claims & {"causal", "prediction"} - {item["claim_kind"]}:
            counts["gap_false"] += 1
        if design != item["comparison_design"] or claim != item["claim_kind"]:
            misses.append(f"{item['id']}: design {item['comparison_design']}->{design}, "
                          f"claim {item['claim_kind']}->{claim} | {item['prompt']}")
    return counts, misses


def main(path, quiet=False):
    data = json.loads(Path(path).read_text())
    items = data["items"] if isinstance(data, dict) else data
    for name, module in (("v1", v1), ("current", current)):
        counts, misses = score(module, items)
        recall_d = counts["design_hit"] / max(1, counts["design_labelled"])
        recall_c = counts["claim_hit"] / max(1, counts["claim_labelled"])
        print(f"{name}: design {counts['design_hit']}/{counts['design_labelled']} ({recall_d:.0%}), "
              f"claim {counts['claim_hit']}/{counts['claim_labelled']} ({recall_c:.0%}), "
              f"false design {counts['design_false']}, false claim {counts['claim_false']}, "
              f"false gap {counts['gap_false']}")
        if name == "current" and not quiet:
            print("\n".join("  " + miss for miss in misses))


if __name__ == "__main__":
    main(sys.argv[1], "--quiet" in sys.argv)

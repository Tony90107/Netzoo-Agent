"""Log 379 prep: purpose-first selection on SEEN sets (calibration only, never a verdict).

Usage (repository root): python3 docs/research-log/purpose-first-2026-10-05/pf_dev.py
For each seen set with recorded live decisions (purpose-contract-2026-10-04/live/sK-decisions.json)
and annotations (heldoutK/heldout.json): apply select_by_purpose to every recorded decision,
using the recorded verified purpose and, for TF priors, the recorded data-facts reading when
there is one (s18), else the annotation's priors_stated (an oracle, said so in the output).
No model is called.
"""
import ast
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from workflow_registry import ACTION_DEFINITIONS  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.routing.study_purpose import StudyPurpose  # noqa: E402
from netzoo_agent_core.routing.purpose_selection import select_by_purpose  # noqa: E402

PC = ROOT / "docs/research-log/purpose-contract-2026-10-04"
NAME = {definition.workflow.upper(): action for action, definition in ACTION_DEFINITIONS.items()}


def actions(names):
    return {NAME.get(name.upper(), name) for name in names}


def parse(value):
    if isinstance(value, (dict, type(None))):
        return value
    return None if value in ("None", "") else ast.literal_eval(value)


def main():
    totals = Counter()
    for path in sorted(PC.glob("live/s*-decisions.json"), key=lambda p: int(p.stem[1:].split("-")[0])):
        number = path.stem[1:].split("-")[0]
        annotations = PC / f"heldout{number}" / "heldout.json"
        if not annotations.exists():
            continue
        items = {item["id"]: item for item in json.loads(annotations.read_text())["items"]}
        counts, notes = Counter(), []
        for key, row in json.loads(path.read_text()).items():
            if not key.startswith("cand-"):
                continue
            item_id = key.split("-")[1]
            item = items.get(item_id)
            if item is None:
                continue
            entry = parse(row.get("study_purpose")) or {}
            purpose = StudyPurpose(entry.get("design"), entry.get("design_quote") or "",
                                   tuple(tuple(c) for c in entry.get("claims") or ()))
            facts = parse(row.get("data_facts"))
            priors = facts.get("priors") if facts else item.get("priors_stated")
            decision = TaskDecision.model_validate(row["decision"])
            selection = select_by_purpose(decision, purpose, priors=priors)
            counts["sessions"] += 1
            if selection is None:
                continue
            counts["applies"] += 1
            if selection.recommended is None:
                continue
            counts["recommended"] += 1
            pick = selection.recommended
            no_rec = item.get("is_control") or item.get("claim_kind") in ("causal", "prediction", "none")
            acceptable, subset = actions(item.get("acceptable_candidates") or []), actions(item.get("recommended_subset") or [])
            if no_rec:
                counts["rec_where_none_expected"] += 1
                notes.append(f"  NONE-EXPECTED {key}: {pick}")
            elif pick in subset:
                counts["in_recommended_subset"] += 1
            elif pick in acceptable:
                counts["acceptable_only"] += 1
                notes.append(f"  acceptable-only {key}: {pick} (subset {sorted(subset)})")
            else:
                counts["not_acceptable"] += 1
                notes.append(f"  NOT ACCEPTABLE {key}: {pick} (acceptable {sorted(acceptable)}; priors {priors})")
        oracle = "recorded data-facts" if number == "18" else "annotation priors (oracle)"
        print(f"s{number} [{oracle}]: {dict(counts)}")
        print("\n".join(notes))
        totals.update(counts)
    print("TOTAL", dict(totals))


if __name__ == "__main__":
    main()

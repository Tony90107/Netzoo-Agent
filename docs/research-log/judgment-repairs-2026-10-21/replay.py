"""Compare this repair with its saved baseline on the same 999 frozen readings; no model calls."""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "reading-coverage-2026-10-20"
spec = importlib.util.spec_from_file_location("archived_replay", SOURCE / "replay.py")
archived = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archived)


def main():
    raw = (SOURCE / "inputs.json.gz").read_bytes()
    inputs = json.loads(gzip.decompress(raw))
    baseline = json.loads((HERE / "baseline.json").read_text())
    transitions, changes, regressions, errors = Counter(), [], [], []
    before_correct = after_correct = labelled = 0
    cases = {}
    for key, row in inputs.items():
        try:
            check, rejected = archived.rebuild(row)
            decision = archived.TaskDecision.model_validate(row["decision"])
            if decision.fact_check is not None and decision.fact_check.status == "checked":
                check = archived.without_legacy_waits(check)
            core = archived.decide_core(decision.model_copy(update={"capability_check": check}), row["task"],
                                        reason_code=row["reason"] or "")
            before = baseline[key]["core"]
            transitions[before["kind"] + "->" + core.kind] += 1
            label = row["gold"]
            if label:
                labelled += 1
                before_correct += before["kind"] == label
                after_correct += core.kind == label
            facts = [fact.model_dump(mode="json") for fact in core.facts]
            record = {"key": key, "where": row["where"], "task": row["task"], "gold": label,
                      "before": before, "after": core.model_dump(mode="json"), "rejected": rejected}
            if before["kind"] != core.kind or before.get("facts") != facts:
                changes.append(record)
            if label and before["kind"] == label and core.kind != label:
                regressions.append(record)
            case_id = Path(row["where"]).parent.name.rsplit("-", 2)[-2]
            if case_id in {"H18", "L13", "M25", "H34", "J29", "H21", "J17", "H37", "H46", "J06", "H11", "M01"}:
                cases[row["where"]] = {"gold": label, "before": before["kind"], "after": core.kind,
                                       "basis": core.basis, "facts": facts,
                                       "declined": [part.model_dump(mode="json") for part in core.declined]}
        except Exception as error:
            errors.append({"key": key, "where": row["where"], "error": repr(error)})
    summary = {"readings": len(inputs), "errors": len(errors), "input_sha256": hashlib.sha256(raw).hexdigest(),
               "transitions": dict(sorted(transitions.items())), "changed_calls": len(changes),
               "labelled": labelled, "correct_before": before_correct, "correct_after": after_correct,
               "previously_correct_regressions": len(regressions),
               "limits": "Same frozen proposal/reread and archived route/fact/run records as baseline. "
                         "No fresh model, second opinion or condition answer. Counts only core kinds, not full semantic correctness."}
    for name, value in [("summary.json", summary), ("changes.json", changes), ("regressions.json", regressions),
                        ("errors.json", errors), ("cases.json", cases)]:
        (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

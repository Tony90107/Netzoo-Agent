"""U0-U2 (ROUND.md): re-validate the recorded rejected readings whose interpreter failed on
`granularity_contradicts_request`, with each turn's recorded user message. No model calls.

Usage (from docs/research-log): python3 granularity-unknown-2026-10-28/revalidate.py [old|new]
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402

APP = ROOT.parents[1] / "netzoo_agent"
PATHS = sorted(glob.glob(str(APP / "docs/research-log/**/trace-*.jsonl"), recursive=True)
               + glob.glob(str(APP / "docs/research-log/**/events.jsonl"), recursive=True)
               + glob.glob(str(APP / ".netzoo/traces/*/events.jsonl")))


def cases():
    for path in PATHS:
        for line in open(path, errors="replace"):
            if '"routing.semantic_interpreter_failed"' in line and "granularity_contradicts_request" in line:
                payload = json.loads(line)["payload"]
                session = Path(path).parent / "session.json"
                users = ([m["content"] for m in json.loads(session.read_text())["messages"] if m["role"] == "user"]
                         if session.exists() else [])
                yield path, payload, users


def main(mode: str):
    rows = []
    for path, payload, users in cases():
        interpretation = SemanticInterpretation.model_validate(payload["rejected_interpretation"])
        recorded = sorted(payload["validation_issues"])
        found = None
        for task in dict.fromkeys([*(users[-1:]), "\n".join(users)]):
            issues = sorted(validate_outcome_hypotheses(task, interpretation.outcome_hypotheses,
                                                        interpretation.request_mode).issues)
            if issues == recorded:
                found = task
                break
        row = {"case": path.split("research-log/")[-1].split("/t")[0][-60:], "recorded": recorded,
               "reproduced": found is not None}
        if found is not None and mode == "new":
            from netzoo_agent_core.graph.semantic_attempts import granularity_left_unknown
            after, validation, changed = granularity_left_unknown(found, interpretation, validate_outcome_hypotheses(
                found, interpretation.outcome_hypotheses, interpretation.request_mode))
            fields = lambda o: {k: v for k, v in o.model_dump().items() if k != "granularity"}  # noqa: E731
            row.update(valid=validation.valid, changed=sorted(changed), issues=list(validation.issues),
                       granularities=[h.outcome.granularity for h in after.outcome_hypotheses],
                       others_unchanged=all(fields(a.outcome) == fields(b.outcome) for a, b in
                                            zip(after.outcome_hypotheses, interpretation.outcome_hypotheses)))
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
    Path(__file__).with_name(f"revalidate-{mode}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "old")

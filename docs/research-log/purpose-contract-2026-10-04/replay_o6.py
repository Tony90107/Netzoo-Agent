"""Log 344 O6: replay Log 343's 156 live decisions with the current witnesses; stage 1 must still only add.

Usage (repository root): python3 docs/research-log/purpose-contract-2026-10-04/replay_o6.py
For each decision the reply is rendered with and without stage 1 (analyze_live.render);
an unresolved reply replaced by a gap is the declared R4 exception.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_live as A  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402

recorded = json.loads((HERE / "live" / "s1-decisions.json").read_text())
counts, failures = Counter(), []
for key, item in recorded.items():
    decision = TaskDecision.model_validate(item["decision"])
    base, _ = A.render(item["prompt"], decision, False)
    cand, kind = A.render(item["prompt"], decision, True)
    if kind == "response_model":
        counts["response_model"] += 1
    elif kind == "unresolved" and A.has_gap(cand):
        counts["r4_replacement"] += 1
    elif A.only_adds(base, cand):
        counts["only_adds"] += 1
        counts["changed"] += base != cand
    else:
        failures.append(key)
print("O6:", dict(counts), "failures:", failures)

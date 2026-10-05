"""Log 374 review (no model call): which heldout16 items the frozen priors verification can accept at all.

Usage (repository root, with t_frozen.patch applied): python3 docs/research-log/purpose-contract-2026-10-04/priors_bound.py
Verification only rejects, so a "ruled_out" reading can stand only where some sentence has a negation or an
"only" cue beside a matching noun, and a "stated" one only where some span names a prior without a negation.
This checks each sentence of each prompt for the most permissive quote (the whole sentence).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.routing import study_purpose_verify as V  # noqa: E402

items = json.loads((HERE / "heldout16" / "heldout.json").read_text())["items"]
reach, lines = Counter(), []
for item in items:
    label = item["priors_stated"]
    sentences = [s.strip() for s in re.split(r"(?<=[.;?!])\s+", item["prompt"]) if s.strip()]
    # The most permissive quote: each sentence, and each clause between semicolons or commas.
    spans = {part.strip() for s in sentences for part in [s, *re.split(r"[;,]", s)] if part.strip()}
    possible = {value for value in ("stated", "ruled_out")
                if any(V._priors_reason(item["prompt"], value, span) == "ok" for span in spans)}
    reach[label] += 1
    reach[f"{label}:reachable"] += label in possible or label == "unstated"
    if label != "unstated" and label not in possible:
        lines.append(f"  unreachable {item['id']} ({label}): {item['data_sentence']}")
    if "stated" in possible and label != "stated":
        lines.append(f"  could be read stated {item['id']} ({label}): {item['data_sentence']}")
print(dict(reach))
print("\n".join(lines))

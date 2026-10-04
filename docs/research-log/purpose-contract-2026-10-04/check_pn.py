"""Log 346 N2/N3/O6: what PN changes, against the v1 witnesses (study_purpose.frozen.py).

Usage (repository root): python3 docs/research-log/purpose-contract-2026-10-04/check_pn.py
N2: every prompt of the three seen sets whose StudyPurpose changes, and claim hits per set.
N3: real requests (traced recordings and .netzoo sessions except mp-/t10-/hp-) that change.
O6: Log 343's 156 live decisions, reply with PN against the reply with v1.
"""
import glob
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs" / "research-log" / "tools"))
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("v1", HERE / "study_purpose.frozen.py")
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
from netzoo_agent_core.routing import study_purpose as pn  # noqa: E402
from netzoo_agent_core.interpretation import practical_notes, study_purpose_notes  # noqa: E402
import analyze_live as A  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from traces import traced_rows  # noqa: E402

for name, path in (("dev340", "dev_log340.json"), ("heldout1", "heldout/heldout.json"), ("heldout2", "heldout2/heldout.json")):
    items = json.loads((HERE / path).read_text())["items"]
    changed = [f"{i['id']}: {[c for c, _ in v1.study_purpose(i['prompt']).claims]} -> "
               f"{[c for c, _ in pn.study_purpose(i['prompt']).claims]}"
               for i in items if v1.study_purpose(i["prompt"]) != pn.study_purpose(i["prompt"])]
    hits = [sum((m.study_purpose(i["prompt"]).claim or "none") == i["claim_kind"] for i in items if i["claim_kind"] != "none")
            for m in (v1, pn)]
    print(f"N2 {name}: claim hits v1 {hits[0]} PN {hits[1]}; changed {changed}")

requests = set()
for _path, _index, row in traced_rows():
    text = (row.get("_trace") or {}).get("prompt") or row.get("prompt")
    if text:
        requests.add(text)
for path in glob.glob(str(ROOT / ".netzoo" / "sessions" / "*.json")):
    if re.search(r"/(?:mp|t10|hp)-", path):
        continue
    try:
        data = json.loads(Path(path).read_text())
    except ValueError:
        continue
    requests |= {str(m.get("content")) for m in data.get("messages", [])
                 if m.get("type") in ("human", "HumanMessage") or m.get("role") == "user"}
print(f"N3: {len(requests)} real requests, changed {sum(v1.study_purpose(t) != pn.study_purpose(t) for t in requests)}")

recorded = json.loads((HERE / "live" / "s1-decisions.json").read_text())
differ = []
for key, item in recorded.items():
    decision = TaskDecision.model_validate(item["decision"])
    with_pn, _ = A.render(item["prompt"], decision, True)
    study_purpose_notes.study_purpose = practical_notes.study_purpose = v1.study_purpose
    with_v1, _ = A.render(item["prompt"], decision, True)
    study_purpose_notes.study_purpose = practical_notes.study_purpose = pn.study_purpose
    if with_pn != with_v1:
        differ.append(key)
print(f"O6: {len(recorded)} live decisions, replies that differ {len(differ)} {differ}")

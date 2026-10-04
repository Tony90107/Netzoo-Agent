"""Log 342 O2: list every study-purpose witness fire on the recorded and real requests.

Usage (repository root): python3 docs/research-log/purpose-contract-2026-10-04/audit_witnesses.py
Reads every traced recording (docs/research-log, via tools/traces.py) and the
user messages of .netzoo/sessions (except the mp-/t10- research sessions), and
prints each request on which `study_purpose` finds a design or a claim, with the
quote. Every fire is judged by hand in the log. Nothing calls a model.
"""
import glob
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs" / "research-log" / "tools"))
from netzoo_agent_core.routing.study_purpose import study_purpose, timepoint_count  # noqa: E402
from traces import traced_rows  # noqa: E402

recorded = {}
for _path, _index, row in traced_rows():
    text = (row.get("_trace") or {}).get("prompt") or row.get("prompt")
    if text:
        recorded.setdefault(text, "recorded")
sessions = {}
for path in glob.glob(str(ROOT / ".netzoo" / "sessions" / "*.json")):
    if re.search(r"/(?:mp|t10)-", path):
        continue
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        continue
    for message in data.get("messages", []):
        if message.get("type") in ("human", "HumanMessage") or message.get("role") == "user":
            sessions.setdefault(str(message.get("content")), "session")
requests = {**sessions, **recorded}
print(f"requests: {len(recorded)} recorded, {len(sessions)} session messages, {len(requests)} distinct")
fires = 0
for text, source in requests.items():
    purpose = study_purpose(text)
    if purpose.design is None and not purpose.claims:
        continue
    fires += 1
    print(f"\n[{source}] design={purpose.design} claims={[c for c, _ in purpose.claims]} "
          f"timepoints={timepoint_count(text)}")
    print("  request:", text[:220].replace("\n", " "))
    if purpose.design:
        print("  design quote:", purpose.design_quote[:160].replace("\n", " "))
    for claim, quote in purpose.claims:
        print(f"  {claim} quote:", quote[:160].replace("\n", " "))
print(f"\nfires: {fires}")

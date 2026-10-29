"""P3 (ROUND.md): the built `jev_links_first.linked`, fed phase A's cached Jev reads, against phase A's arm H."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE.parent / "jev-first-links-2026-10-29"
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
sys.path.insert(0, str(A))

import shadow as phase_a  # noqa: E402
from netzoo_agent_core.capability_sheet import entry  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.jev_links_first import linked, state  # noqa: E402

assert state("T", "Q") == phase_a.state("T", "Q")
golds, cache = phase_a.gold(), phase_a._cache()
recorded = {row["where"]: row["credited"]["H"] for row in json.loads((A / "shadow.json").read_text())}
same = differ = 0
for folder, item, proposal in phase_a.readings(golds):
    task = golds[item]["prompt"]
    model = proposal_model(sum(1 for n in proposal if re.fullmatch(r"s\d+", n))).model_validate(proposal)
    reads = {ask["quote"]: cache.get(phase_a._key(task, ask["quote"]), {"error": "uncached"})
             for _n, _i, ask in phase_a.asks(proposal)}
    check = build_capability_check(task, linked(model, reads))[0]
    credited = sorted({entry(k).workflow for r in check.results()
                       if r.status in ("available", "with_step", "partial") for k in r.delivered_by})
    if credited == recorded[str(folder.relative_to(phase_a.LOGS))]:
        same += 1
    else:
        differ += 1
        print("differs:", item, credited, recorded[str(folder.relative_to(phase_a.LOGS))])
print(f"P3 parity: {same} same, {differ} differ")

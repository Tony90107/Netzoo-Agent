"""E1-E3 (ROUND.md) from data-has's recorded reads (no Jev call): the existing read with every guard branch, the
has-read only through `incompatible_input_artifacts`."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.graph.jev_guard_call import THRESHOLD, _typed_contracts, ruled_out  # noqa: E402

DATA_HAS = HERE.parent / "data-has-2026-10-29"


def has_rules_out(workflow, kind, conf):
    return conf >= THRESHOLD and kind in (_typed_contracts().get(workflow) or {}).get("incompatible", ())


rows = json.loads((DATA_HAS / "measure.json").read_text())
lines = []
do = [r for r in rows if r["gold"] in ("DO", "PARTIAL")]
union = lambda r: any(r["ruled_data"][w] or has_rules_out(w, *r["has"]) for w in r["workflows"])  # noqa: E731
lines.append(f"E1 gold DO/PARTIAL {len(do)}: union rules a gold workflow out in {sum(union(r) for r in do)}")
dtype = [r for r in rows if r["gold"] == "DECLINE" and (r["sub"] in ("incompatible", "not_accepted")
                                                        or r["category"] == "N")]
existing = sum(any(r["ruled_data"].values()) for r in dtype)
lines.append(f"E2 data-type DECLINE {len(dtype)}: existing {existing}, union {sum(union(r) for r in dtype)}")
q18 = next(r for r in rows if r["set"] == "j2" and r["id"] == "Q18")
lines.append(f"E2 Q18 has {q18['has']} -> SAMBAR ruled out: {has_rules_out('SAMBAR', *q18['has'])}")
stability = (DATA_HAS / "STABILITY.txt").read_text()
for name, workflow in (("Q18", "SAMBAR"), ("W17", "CONDOR"), ("Z14", "CONDOR")):
    line = next(l for l in stability.splitlines() if f" {name} " in l)
    reads = re.findall(r"\('(\w+)', ([\d.]+), (?:True|False)\)", line)
    hits = sum(has_rules_out(workflow, kind, float(conf)) for kind, conf in reads)
    lines.append(f"E3 {name} {workflow}: ruled out {hits}/{len(reads)} (incompatible list: "
                 f"{sorted((_typed_contracts().get(workflow) or {}).get('incompatible', ()))})")
text = "\n".join(lines)
(HERE / "OFFLINE.txt").write_text(text + "\n")
print(text)

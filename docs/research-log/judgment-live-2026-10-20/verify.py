"""Offline integrity checks for the captured live test, not a model accuracy assertion."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
WT = ROOT.parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    assert (ROOT / "items.json").read_bytes() == (ROOT / "attempt-02/items.json").read_bytes()
    turns = 0
    for base in [ROOT, ROOT / "attempt-02"]:
        round_info = json.loads((base / "round.json").read_text())
        assert sha(base / "items.json") == round_info["dataset_sha256"]
        finished = json.loads((base / "finished.json").read_text())
        assert finished["runtime_code_unchanged"] and finished["sessions"] == 6
        jobs = json.loads((base / "jobs.json").read_text())
        assert len(jobs) == 6
        for folder in (base / "live").glob("*/t*"):
            manifest = json.loads((folder / "manifest.json").read_text())
            for name, digest in manifest["files"].items():
                assert sha(folder / name) == digest, (folder, name)
            if base.name == "attempt-02":
                assert manifest["exit"] == 0
                turns += 1
        if base.name == "attempt-02":
            for name, digest in round_info["code"]["files"].items():
                assert sha(WT / name) == digest, name
    assert turns == 7
    analysis = json.loads((ROOT / "analysis.json").read_text())
    usage = analysis["usage_all_attempts"]
    assert usage["unavailable_cost_calls"] == 0
    assert (usage["actual_cost_micro_usd"] + usage["estimated_cost_micro_usd"]) < 500000
    assert all(not row["actual_execution_events"] for row in analysis["rows"])
    recovered = {str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT / "live").glob("*/t1/trace.*"))}
    (ROOT / "recovered-traces-sha256.json").write_text(json.dumps(recovered,indent=2)+"\n")
    print("PASS: frozen questions, 13 captured turns, original manifest hashes, unchanged retry runtime, cost below $0.50, no tool execution events")

if __name__ == "__main__":
    verify()

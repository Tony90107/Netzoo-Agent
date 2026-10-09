"""Log 402 simulation gates (FREEZE402.md): routing failed, the check as usual, base against candidate code.

Usage (any directory): python3 docs/research-log/capability-traps-2026-10-08/analyze402_sims.py
Reads replay/sf10-base.json and replay/sf10-cand.json (sim_routing_failure.py on heldout10). Nothing calls a model.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent / "replay"


def tally(name):
    rows = json.loads((HERE / f"{name}.json").read_text())
    out = {"n": len(rows), "ok": sum(1 for r in rows if r["status"] == "ok")}
    for group in ("UN", "P", "C"):
        picked = [r for r in rows if r["family"] in group]
        out[group] = {"n": len(picked), "full_gap": sum(1 for r in picked if r.get("full_gap"))}
    out["C_gapped"] = sorted({r["id"] for r in rows if r["family"] == "C" and r.get("full_gap")})
    return out


def main():
    base, cand = tally("sf10-base"), tally("sf10-cand")
    print("base", json.dumps(base))
    print("cand", json.dumps(cand))
    gates = {"SF1": cand["C"]["full_gap"] <= base["C"]["full_gap"] + 1,
             "SF2": cand["UN"]["full_gap"] >= base["UN"]["full_gap"]}
    for name, ok in gates.items():
        print(f"{name} -> {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()

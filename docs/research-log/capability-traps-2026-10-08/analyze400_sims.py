"""Log 400 simulation gates (FREEZE400.md): the forced-fallback check against the normal check. Nothing calls a model.

Usage (any directory): python3 docs/research-log/capability-traps-2026-10-08/analyze400_sims.py
Reads replay/sf9.json (candidate, nemotron as usual, routing failed), replay/sb9.json (candidate, own model
forced to fail, so mini answers) and replay/sb9-base.json (live code under the same forced failure).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent / "replay"


def tally(name):
    rows = json.loads((HERE / f"{name}.json").read_text())
    out = {"n": len(rows), "ok": sum(1 for r in rows if r["status"] == "ok")}
    for group, families in (("UN", "UN"), ("P", "P"), ("C", "C")):
        picked = [r for r in rows if r["family"] in families]
        out[group] = {"n": len(picked), "full_gap": sum(1 for r in picked if r.get("full_gap"))}
    return out


def main():
    sf, sb, base = tally("sf9"), tally("sb9"), tally("sb9-base")
    for name, value in (("sf9 normal", sf), ("sb9 fallback", sb), ("sb9-base live", base)):
        print(name, json.dumps(value))
    gates = {
        "SB1": sb["C"]["full_gap"] <= sf["C"]["full_gap"] + 1,
        "SB2": sb["ok"] >= 66,
        "SB3": sb["UN"]["full_gap"] >= sf["UN"]["full_gap"] - 4,
        "SB4": sb["ok"] > base["ok"],
    }
    for name, ok in gates.items():
        print(f"{name} -> {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()

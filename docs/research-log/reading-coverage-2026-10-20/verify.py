"""Verify frozen inputs, source hashes, reproducible replay and execution holds."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        assert sha(WT / name) == expected, name
    outputs = ("replay-summary.json", "changed-calls.json", "sentence-ownership.json", "targeted-replay.json")
    before = {name: sha(HERE / name) for name in outputs}
    subprocess.run([sys.executable, "-I", str(HERE / "replay.py")], cwd=WT, check=True,
                   stdout=subprocess.DEVNULL)
    assert {name: sha(HERE / name) for name in outputs} == before
    summary = json.loads((HERE / "replay-summary.json").read_text())
    assert summary["readings"] == 999 and summary["skipped"] == 0
    assert summary["labelled"] == 741 and summary["previously_correct_regressions"] == 0
    assert summary["correct_before"] == 561 and summary["correct_after"] == 563
    assert summary["transitions"]["DO->ASK"] == 14
    for row in json.loads((HERE / "changed-calls.json").read_text()):
        assert not row["after"]["run_allowed"]
        assert row["after"]["evidence"]["unread_sample_conditions"]
    for row in json.loads((HERE / "sentence-ownership.json").read_text()):
        assert row["source_sentence"] != row["owner_sentence"]
    print("PASS: frozen inputs/source hashes, reproducible 999-reading replay, no previous gold matches lost, "
          "14 new ASKs hold execution; this is not a live or blind acceptance test")


if __name__ == "__main__":
    main()

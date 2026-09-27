"""Run the five routing grids and compare them with a baseline directory.

Usage: python docs/research-log/tools/grids.py <out_dir> [<baseline_dir>]

Grids (deterministic, offline): log136 outcome grid (g.json), log148 evidence
grid (eg.json), log170 guidance grid (gg.json), log174 tag grid (tg.json),
log150 pair grid (pg.json). They are not archived because any commit can
regenerate them; generate a baseline at the parent commit instead. With a
baseline, each grid is reported identical or different; use the grid script's
own `--diff` for the transition summary.
"""
import filecmp
import subprocess
import sys
from pathlib import Path

from traces import RESEARCH, ROOT

GRIDS = (
    ("g", ["log136_outcome_grid.py"]),
    ("eg", ["log148_evidence_grid.py", str(ROOT)]),
    ("gg", ["log170_guidance_grid.py", str(ROOT)]),
    ("tg", ["log174_tag_grid.py", str(ROOT)]),
    ("pg", ["log150_pair_grid.py", str(ROOT)]),
)

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
base = Path(sys.argv[2]) if len(sys.argv) > 2 else None
for name, command in GRIDS:
    target = out / f"{name}.json"
    subprocess.run([sys.executable, str(RESEARCH / command[0]), *command[1:], str(target)],
                   check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    if base is not None:
        same = filecmp.cmp(base / f"{name}.json", target, shallow=False)
        print(f"{name}: {'identical' if same else 'DIFFERS'}")
    else:
        print(f"{name}: written")

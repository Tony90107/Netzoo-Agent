"""Merge plan M2: run a research replay script on this checkout with the overlap reader injected into the capability
check, as the router now does (`overlap_reader=jev_overlap_call.overlap_reader()`). The research scripts call
`build_capability_check` directly and are not edited; this wraps the builder before they import it.

Usage: NETZOO_JEV_OVERLAP=on NETZOO_JEV_OVERLAP_CACHE=... python3 m2_adapter.py SCRIPT.py [ARGS...]
Prints how many builder calls got a reader, so an unused wrapper is visible.
"""
from __future__ import annotations

import functools
import runpy
import sys
from pathlib import Path

CHECKOUT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(CHECKOUT / "scripts"))

from netzoo_agent_core.graph import jev_overlap_call  # noqa: E402
from netzoo_agent_core.interpretation import capability_check  # noqa: E402

_original = capability_check.build_capability_check
_calls = {"with_reader": 0, "all": 0}


@functools.wraps(_original)  # keeps the signature visible to replay_full's `_takes`
def _with_reader(*args, **kwargs):
    _calls["all"] += 1
    if "overlap_reader" not in kwargs and len(args) < 5:
        kwargs["overlap_reader"] = jev_overlap_call.overlap_reader()
        _calls["with_reader"] += kwargs["overlap_reader"] is not None
    return _original(*args, **kwargs)


capability_check.build_capability_check = _with_reader
script, sys.argv = sys.argv[1], sys.argv[1:]
try:
    runpy.run_path(script, run_name="__main__")
finally:
    print(f"m2_adapter: builder calls {_calls['all']}, with a reader {_calls['with_reader']}", file=sys.stderr)

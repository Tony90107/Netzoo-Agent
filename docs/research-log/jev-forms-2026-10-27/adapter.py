"""Run a research replay script with both Jev readers injected into the capability check, as the router does
(`overlap_reader()`, `forms_reader()`; each None when its flag is off). Adapted from jev-j3 merge/m2_adapter.py: the
research scripts call `build_capability_check` directly and are not edited.

Usage: [NETZOO_JEV_OVERLAP=on] [NETZOO_JEV_FORMS=on] python3 adapter.py SCRIPT.py [ARGS...]
"""
from __future__ import annotations

import functools
import runpy
import sys
from pathlib import Path

CHECKOUT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(CHECKOUT / "scripts"))

from netzoo_agent_core.graph import jev_forms_call, jev_overlap_call  # noqa: E402
from netzoo_agent_core.interpretation import capability_check  # noqa: E402

_original = capability_check.build_capability_check
_calls = {"all": 0, "overlap": 0, "forms": 0}


@functools.wraps(_original)  # keeps the signature visible to replay_full's `_takes`
def _with_readers(*args, **kwargs):
    _calls["all"] += 1
    if "overlap_reader" not in kwargs and len(args) < 5:
        kwargs["overlap_reader"] = jev_overlap_call.overlap_reader()
        _calls["overlap"] += kwargs["overlap_reader"] is not None
    if "forms_reader" not in kwargs:
        kwargs["forms_reader"] = jev_forms_call.forms_reader()
        _calls["forms"] += kwargs["forms_reader"] is not None
    return _original(*args, **kwargs)


capability_check.build_capability_check = _with_readers
script, sys.argv = sys.argv[1], sys.argv[1:]
try:
    runpy.run_path(script, run_name="__main__")
finally:
    print(f"adapter: builder calls {_calls['all']}, overlap reader {_calls['overlap']}, forms reader {_calls['forms']}",
          file=sys.stderr)

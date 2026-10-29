"""What data the user says they have, as its own closed Jev question (docs/research-log/data-has-2026-10-29).

The guard's typed data question asks which data the analysis should be built from; j2 Q18 names both the analysis's
data ("pathways hit by mutations") and the user's own ("What we have is a bulk RNA-seq expression matrix"), so the read
split (several 0.32, expression 0.31) and nothing ruled SAMBAR out. This question asks only what the user has, with the
guard's own options. has-incompatible-2026-10-30: it rules a workflow out only through that workflow's explicit
`incompatible_input_artifacts` (data-has's broader use crossed 0.7 once in ten on the PANDA -> CONDOR chain j5 W17).
Off by default: NETZOO_JEV_DATA_HAS=on.
"""
from __future__ import annotations

import os

__all__ = ["HAS_INSTRUCTIONS", "data_has_mode"]

# Frozen with the data-has measurement; never reworded after a run.
HAS_INSTRUCTIONS = "Which kind of data does the user say they have?"


def data_has_mode() -> str:
    return "on" if os.environ.get("NETZOO_JEV_DATA_HAS", "off").strip().lower() == "on" else "off"

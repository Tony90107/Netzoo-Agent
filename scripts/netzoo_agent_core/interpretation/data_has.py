"""What data the user says they have, as its own closed Jev question (docs/research-log/data-has-2026-10-29).

The guard's typed data question asks which data the analysis should be built from; j2 Q18 names both the analysis's
data ("pathways hit by mutations") and the user's own ("What we have is a bulk RNA-seq expression matrix"), so the read
split (several 0.32, expression 0.31) and nothing ruled SAMBAR out. This question asks only what the user has, with the
guard's own options; the guard's `ruled_out` rule is applied to it as to the other read.
"""
from __future__ import annotations

__all__ = ["HAS_INSTRUCTIONS"]

# Frozen with the data-has measurement; never reworded after a run.
HAS_INSTRUCTIONS = "Which kind of data does the user say they have?"

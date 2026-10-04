# Witness freeze (Log 342 preparation)

The study-purpose witnesses were frozen before anyone on the implementing side
read the held-out set. A subagent wrote `heldout/` in isolation: it was told not
to read any repository file, and the witness lists did not exist when it started.

- Frozen file: `study_purpose.frozen.py` (copy of `scripts/netzoo_agent_core/routing/study_purpose.py`)
- sha256: `37caf959136c4a82909be0a36a6d6a3665d0e478810935c9b8b9c820a72949d2`
- Tuned on: the Log 340 development prompts (all 9 match their pre-written labels),
  the 78 recorded requests and 236 real session messages (`audit_witnesses.txt`:
  3 fires, all true "predict chemoresistance / drug resistance" claims, after
  fixing 2 false fires: a Chinese "不是 causal" and a multi-omic "150 paired tumor samples"),
  and hand-written probe sentences (negations, "difference between PANDA and PUMA",
  "which patients belong to which subtype", mice sacrificed per time point).

Any change to the witnesses after this commit must be declared and reported
separately from the held-out results.

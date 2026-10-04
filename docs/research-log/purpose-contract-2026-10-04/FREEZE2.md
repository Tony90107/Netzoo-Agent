# Witness v2 freeze (Log 344 preparation)

The v2 study-purpose witnesses were frozen before anyone on the implementing side
read the second held-out set (`heldout2/`), which an isolated subagent was writing
at the same time. It was told not to read any repository file.

- Frozen file: `study_purpose.v2.frozen.py` (a copy of the working-tree `scripts/netzoo_agent_core/routing/study_purpose.py`)
- sha256: `9e584e8b901505a913dac5bd3f3240c7b452210475c14d704f9f1076182ceb42`
- Development data (all seen): the Log 340 prompts (`dev_log340.json`, 9/9 design, 6/6 claim),
  the first held-out set (`heldout/heldout.json`, now seen: v1 4/22 design and 10/20 claim; v2 22/22 and 20/20),
  hand-written probes (processing steps "before and after normalization", data-type pairs,
  "24 patients and 48 samples", "due to / attributable to batch", "target prediction"),
  and the precision audit `audit_witnesses_v2.txt` (78 recorded requests and 236 real session
  messages: the same 3 true "predict" fires as v1, no new fire).
- The trap categories in the second held-out set's brief were written by me, so its
  precision traps are not blind to the witness design; its recall prompts are.

Any change to the witnesses after this commit must be declared and reported
separately from the second held-out results.

# Witness v3 freeze (Log 348 preparation)

The v3 study-purpose witnesses were frozen before anyone on the implementing side
read the third held-out set (`heldout3/`), which an isolated subagent was writing at
the same time. This time the subagent also invented its own precision-trap kinds;
the brief named no trap categories, so the traps are blind to the witness design too.

- Frozen file: `study_purpose.v3.frozen.py` (= working-tree `scripts/netzoo_agent_core/routing/study_purpose.py`)
- sha256: `fd4ae91446f394001c86a577d4f8f9181ca65f41bd0cef2818bbabddd196f051`
- v3 = withdrawn v2 (Log 345) + PN (Log 346) + fixes for v2's false hits on the second set
  (a lone "healthy volunteers" is one group; tissues "from the same N patients" are paired, unless
  the matched things are omics layers) + recall for its misses ("during X and again after Y",
  "rank TFs by how much ... changes", "regulated differently", "16 rats fed X and 16 fed Y",
  "whose networks changed most", "flags ... not yet diagnosed").
- Development data (all seen): Log 340 prompts 9/9 design, 6/6 claim; first held-out set
  22/22, 20/20; second held-out set 22/22, 20/20; probes in `tests/test_study_purpose.py`;
  precision audit `audit_witnesses_v3.txt` (78 recorded + 236 real session messages: the same
  3 true "predict" fires as v1, no new fire; a "paired ... matrices from the same cohort"
  fire found during development was removed before this freeze).

Any change to the witnesses after this commit must be declared and reported
separately from the third held-out results.

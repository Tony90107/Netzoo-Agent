# Witness D3 freeze (Log 352 preparation)

D3 = the live witnesses v1+PN+CN for conclusions, with the design witnesses of the
withdrawn v3 (Logs 348-349). It was frozen before anyone on the implementing side read
the fourth held-out set (`heldout4/`), which an isolated subagent was writing at the
same time; its brief asked for varied design wording and invented design traps.

- Frozen file: `study_purpose.d3.frozen.py` (= working-tree `scripts/netzoo_agent_core/routing/study_purpose.py`)
- sha256: `8e556d23ee44a8d1d1ace00d02694fa5499f4dd115d4631e3e91b600fe8ef263`
- Changes against v3's design part, all from seen data or my own probes:
  - "each sampled when stable, during an exacerbation and after recovery" (third set H3): a 60-character span;
  - "replicate pools at each of vehicle and three concentrations" (third set H6): dose groups;
  - probes found "three concentration levels of the standard curve" and "each sample was sequenced at
    two depths for QC"; both shapes now go through the processing exclusion (depth, lanes, libraries,
    standard curve, spike-ins added to it).
- Conclusions are unchanged, but group_difference needs a design, so more designs can add it:
  the second set's T2 now reads group_difference ("changed most between samples") where its label is
  individual_change (v3's "whose networks changed most" was a conclusion change and is not in D3).
- Development data (seen): design 9/9, 22/22, 22/22, 23/23 on the Log 340 prompts and the three held-out
  sets; precision audit `audit_witnesses_d3.txt` identical to v1's (3 true "predict" fires).

Any change to the witnesses after this commit must be declared and reported
separately from the fourth held-out results.

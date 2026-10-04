# Log 361 freeze: technical vetoes that veto only what they pair or group

Frozen before anyone on the implementing side read the eighth held-out set (`heldout8/`),
which an isolated subagent was writing at the same time. Unlike PN and CN, this change
lets more designs through (it relaxes a veto), so it is evaluated like a new version.

- Frozen file: `b4_frozen/study_purpose_verify.py`, sha256 `fb2d4f0bc917c63667ddd2bd44bf1b1816d36fd8c46d640dca5b67755561738c`
  (= working-tree `scripts/netzoo_agent_core/routing/study_purpose_verify.py`).
  Prompt and contract unchanged (`b3_frozen/`).
- Change against `b3_frozen/` (the live b''): the one technical-pairing list, matched anywhere in the
  design quote without word boundaries, becomes
  - for paired: paired-end, read pairs, mate pairs; "paired/matched ... matrices/layers/omics/datasets/assays";
    "before/after normalization, filtering, batch correction, QC, preprocessing, trimming";
  - for groups: "N batches/lanes/runs/plates/litters/replicates/libraries/hospitals/sites/centres/platforms/
    kits/chips/flow cells"; contrasts between normalizations, methods, approaches, pipelines, algorithms,
    priors or motif collections.
- On seen proposals (b'' -> this): Log 354's 387 -- design 254 -> 289/297, conclusions 237 -> 245/264;
  fifth set -- 48 -> 60/66, 54 -> 57/66; sixth set -- unchanged (63/63, 50/60); seventh set -- 62 -> 64/72,
  69/69. False designs, false conclusions and false causal/prediction claims unchanged everywhere
  (0, 0, 0; seventh set 3 false designs, T3, as before).

Any change after this commit must be declared and reported separately from the eighth held-out results.

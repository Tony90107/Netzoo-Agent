# Gold review of h4 (2026-10-19, before any run)

Reviewer: a fresh subagent that read only `items-author.json`, the 13 `workflows/*.yaml` and
`scripts/workflow_registry.py` of `.worktrees/netzoo-core-p0-run`. Full review: `gold-review.json`.

- **One gold changed: M39** (ask) -- OTTER added to the workflows (COBRA, PANDA, OTTER): cobra.yaml
  `handoff_targets: [run_panda, run_puma, run_otter]`; otter.yaml "COBRA is an explicit predecessor when
  batch/confounder adjustment is needed". Class and deciding fact unchanged.
- **Interpretation-critical facts corrected** (gold class unchanged): M02 (a contract fact not in the request removed),
  M15 (the open choice between one network for all donors and one per donor added), M17 (an output-folder fact
  dropped), M22 (each sample's network estimated against the other six samples added).
- `file_checkable` true: M01 (the LIONESS-DRAGON value cap is checked from the files), M38 (SAMBAR compares kmax with
  the samples in the mutation file); false: M36, M44.
- Borderline, kept: M20 (a dont item with no closest workflow), M36 (the single-cell exclusion comes from the
  registry's advice text, not a YAML input check), M47 (LIONESS-PANDA also declares an aggregate output).
- LIONESS-DRAGON value counts for M01, M08, M23 recomputed; all match.
- English only: no CJK character in any field.

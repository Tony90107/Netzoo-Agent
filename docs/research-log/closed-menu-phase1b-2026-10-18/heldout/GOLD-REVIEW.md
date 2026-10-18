# Gold review of the held-out items (2026-10-18, before any run)

Reviewer: an independent subagent that read only `items-author.json`, the 13 `workflows/*.yaml` and
`scripts/workflow_registry.py` (the author's sources), never the bench, the gold readings or the closed-menu design.
Its full review is `gold-review.json`.

- **All 48 golds agreed; none changed.** `items.json` = `items-author.json` plus the review note.
- Limits recomputed by the reviewer, all matching: LIONESS-DRAGON's 20,000,000-value cap (H07 19.2 M under; H28
  33.7 M over; H38 14.4 M vs 119 M depending on the panel), SAMBAR kmax against samples (H29, H33, H45), COBRA genes
  against samples (H16, H47, H48), BONOBO delta below 1/3 with sparsify (H31 0.3, H34 0.4), DRAGON's paired lambdas
  (H03), sample minimums (H11, H15, H36, H43). The 34 evidence quotes were checked against the YAML text.
- `file_checkable`: the four run-form ask items (H09, H23, H25, H41) are all false -- no contract input check reads
  their deciding fact from the files. So no ask item is scored right for a run that defers its fact to the input check.
- Borderline, kept: H02 (TF and miRNA priors as separate files; LIONESS-PUMA also writes the aggregate), H06 ("independent
  of the TF's own transcript level" vs the registry's "not tied to its mRNA"), H09 (BONOBO also gives per-sample
  co-expression), H17 (OTTER's `computing` lists gpu, the convention says GPU is not enabled), H35 (run form, no result
  stated), H36 (the small-RNA sequencing is no LIONESS-PUMA input).

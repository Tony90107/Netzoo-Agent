# Gold review of h3 (2026-10-19, before any run)

Reviewer: a fresh subagent that read only `items-author.json`, the 13 `workflows/*.yaml` and
`scripts/workflow_registry.py` of `.worktrees/netzoo-core-p0-run`. Full review: `gold-review.json`.

- **All 48 golds agreed; none changed.** `items.json` = `items-author.json` plus the review note and `file_checkable`
  on the four run-form ask items.
- The author's note: a hook attached that worktree's `AGENTS.md` (general project policy, not the slim-reading
  design); the author says no gold rests on it.
- `file_checkable` true: L18 (LIONESS-DRAGON refuses oversized runs before they start: 300 vs 1,500 transcripts at 60
  samples), L39 (SAMBAR's input check reads the mutation file with kmin/kmax), L40 (COBRA's input check verifies
  genes > samples). False: L03 (a lam setting no file check reads).
- Borderline, kept: L12 (could be read as vague: the granularity picks the result), L37 (PANDA vs OTTER: a preference,
  not a result, is missing), L47 (only SAMBAR takes mutation data), L07 and L11 (BONOBO also needs the declared
  transform; LIONESS-COEXPRESSION fits L07 without it).

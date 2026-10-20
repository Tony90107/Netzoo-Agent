# ROUND-07 results: count doubts (G1-G3), offline replay

Plan: `collab/ROUND-07-PLAN.md`. Code: `97327997` → `fe6a0555`. Model calls: 0. Full suite: 4730 passed, 51 skipped.

## Replay over 979 recorded readings

Harness: `request-facts-round03-2026-10-20/replay.py`. The comparison leaves out ROUND-03's record fields (`facts`, `fact_conflicts`, `fact_ids`).

- **Checks that differ: 1 of 979 (U11).**
  - U11 (`m3-clarification-2026-10-15/live/m3/ve-m3-live-U11-1/t1`, "They may contain two or ten paired samples").
  - Unchanged: status `needs_fact`, workflows, and outcomes `{2: [], 10: [LIONESS-DRAGON x2]}`.
  - Now `by_code: true`, and `fact_ids` cites the candidates fact.
  - Before, the record held two "stated" counts, 2 and 10, both read by the result. They contradicted each other and neither was flagged. Now they are one unsure fact (reads: side_by_side ×2, unknown_facts).
  - The decision was already right before this round: the unknown-fact path had removed the stated count.
- **C11** ("88 donors: 44 AD, 44 controls"): unchanged. The tightened rule no longer treats these as candidates; ROUND-02's veto rule did.
- **Record changes:**
  - facts differ in 1 check (U11);
  - 4 new conflicts, all `unsure_candidates` with `used: []` (a stated count set aside beside an unknown sample count):

| Session | Set aside | The unknown it was set aside for |
|---|---|---|
| h1 H46 | 500 ("roughly 500 patients") | the same words, typed as an unknown sample count |
| g4o1, g4o2, p1 C45 | 50 ("50 heart-failure patients") | "the 200-protein targeted panel or the 2,000-protein discovery panel", typed as a **sample** count |

These four rows record set-asides that already happened before this round; the round changes none of them. They show two first-read errors:
- C45: a feature doubt was typed as a sample-count doubt, so the stated 50 was dropped and the question is about "sample_count" with the values 200/2000.
- H46: "roughly 500" was typed as unknown.
Neither is fixed here. They belong to the reading, not to the rules.

Metrics (new): 2,514 reads; 44 unsure facts; 2 side_by_side reads; 6 conflicts.

## G3 (named file)

The replay cannot exercise G3: the recorded sessions do not carry their input files, and the rebuild calls `build_capability_check` without `counted_samples`. G3 is covered by unit tests only (`tests/test_count_doubts.py`):
- a count among the candidates settles;
- a count that is none of the candidates settles nothing;
- an unknown count is answered by the file;
- a stated count is never replaced;
- with several results nothing settles.
How often G3 fires on real requests is unmeasured.

## Limits

- A range ("8-15") becomes candidates 8 and 15. The question then reads "Which of these is right: 8 or 15?". That is the existing candidate question, and its wording is wrong for a range.
- "6 x 900" (one word between two numbers, spaces only) would count as candidates. No recorded reading has this.
- G3 counts expression files only, not DRAGON-style layer files.

# Log 367 freeze: "cannot" cells, with the many-samples reading and offered candidates only

Frozen before anyone on the implementing side read the eleventh held-out set (`heldout11/`),
which an isolated subagent writes after this freeze.

- Frozen change: `m_frozen.patch` (the whole working-tree diff of `scripts/` and `tests/` against HEAD
  `c780bb8`), sha256 `2dd3ddc1a5a0`. It is Log 365's change (`db20915`, reverted in Log 366)
  plus:
  - `StudyPurposeProposal.many_samples_span` and its paragraph in `STUDY_PURPOSE_SYSTEM`: the words
    saying each individual gave many samples of their own (contract shape, not a rewording).
  - Verification (`_many_reason`): the quote is in the request, and its sentence has a sampling frequency
    (weekly, every day) or ten or more samples, tissues or time points tied to each individual, overlapping
    the quote; not negated. "each sampled before and after ten days", "from each of 15 patients",
    five time points and "40 patients" are not many.
  - `StudyPurpose.many_samples_quote`, written to state and traces.
  - `cannot_cells`: none when the many-samples quote is verified; otherwise only for the workflows the reply
    offers as candidates (matched, hypothesis, advisory) -- not an aggregate named because its per-sample
    version also produces it (Log 366, T2-1/T2-2).
- Seen data (design only):
  - heldout10 offline, the same 32 x 3 prompts with the live prompt (baseline worktree, b_eval) and the new
    one (m_eval): design 67/84 both, false 9 both; claims 60/78 false 4 (live) vs 64/78 false 0 (new); false
    gaps 0 both; 8 failed calls each. Many samples: T1 and T2 6/6 after reading the cue in the quote's
    sentence (3/6 before: "samples from about 40 different tissues" lacked its "each"); false 0.
  - Replies, s7-s10 candidate arms (384 trials, traces without the new field): C1 44/45 (the one left is
    s10 T2-3, whose trace has no many reading), C2 0, C3 15/15, line-level H2 384/384.
  - s10 with each trial's many reading from the new call: C1 14/14, C3 5/5, H2 96/96.
- Measuring function: `analyze_cannot.py selftest` 9/9 (unchanged).
- Suite: 3285 passed / 35 skipped (base 3268: Log 365's 5 new tests, 12 more for Log 367, one pinned state
  test gains `many_samples_quote`); fingerprints legacy e920bf3b5d57, claims 743b2dd0d73a; condition
  prompt hash c820364a1123; policy hash b0570ff267af -- unchanged.

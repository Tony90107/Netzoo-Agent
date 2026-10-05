# Log 376 freeze: the priors read by their own small call, for the tie replies that ask about them

Frozen before anyone on the implementing side read the eighteenth held-out set (`heldout18/`),
which an isolated subagent writes after this freeze.

- Frozen change: `w_frozen.patch` (the diff of `scripts/` and `tests/` in the clean worktree
  `.worktrees/netzoo-purpose-cand` against `2120f96`, new files included), sha256 `3a70f1253007`.
  Twelve files; none of them is among the files another session (Codex) is editing in the main checkout.
- Log 372's tie reply and data question (`7a5f280`, reverted in Log 373), with the priors read as follows:
  - `contracts/data_facts.py`: `DataFactsProposal` (`priors`: stated / ruled_out / unstated, `priors_span`).
  - `llm.DATA_FACTS_SYSTEM` and `build_data_facts_messages`: a short prompt of its own. `STUDY_PURPOSE_SYSTEM` and
    its schema are byte-identical to live (sha256 e2af95adf863 and 83461bb34d77 in both trees) -- Log 375 failed
    because the priors paragraph shared that prompt.
  - `graph/data_facts_call.py`: one strict call (role `data_facts`, the study-purpose call's model binding),
    asked only after routing on a tie with one reading whose verified purpose states a question and no causal
    or prediction claim (`router_invocation._tie_with_question`); verified only for provenance (the quote is
    in the request); events `routing.data_facts_detected` / `_failed`; state `data_facts`. Not configured,
    blocked or failed: nothing is read and the tie reply falls back to Log 372's word lists.
  - The tie reply shows the reading in the user's own words (A', Log 375), and says so when every candidate
    needs priors the user ruled out.
- Seen data (design only), the new call on heldout16 and heldout17, 32 x 3 each: read as stated when not
  stated 0 and 0; stated recall 36/36 and 33/33; ruled-out recall 15/27 and 18/27 ("the gene count table is the
  whole of our data", "the count matrix is our entire dataset" read as unstated).
- Suite (clean worktree): 3291 passed / 35 skipped (base 3275, 16 new: Log 372's 8 and test_data_facts.py's 8);
  fingerprints legacy e920bf3b5d57, claims 743b2dd0d73a; condition prompt hash c820364a1123 -- unchanged.
- Analysis: `analyze_live.trace_data_facts` and the offline renders now carry each session's traced data facts,
  so a live reply is compared with a render from the same reading; seen-data replays are unchanged.

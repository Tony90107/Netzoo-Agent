# Data check before form questions (2026-10-27) — declared before code

User decision (2026-10-27): when the user's data would rule a workflow out, do not ask a form question about it
first. Declare gates, then measure offline. Branch `jev-answers` (worktree `.worktrees/netzoo-j4`); not merged.

## Problem (jev-answers RESULTS-LIVE.md, j4 RESULTS-J4.md)

j4 S32 / ja1 S32: "SAMBAR to subtype these tumours from that expression matrix". The reading typed several_groups,
so the call became ASK on the group question. The guard's typed data check (PLAN-J2 step 1'') runs only on a DO, so it
never saw that SAMBAR takes no expression matrix. The user's reply did not answer the group question, and the
conversation ended at the round cap with no call. Gold: DECLINE.

## Change (only with `NETZOO_JEV_FORMS=on` and `NETZOO_JEV_GUARD=on`)

A new step in `graph/jev_forms_call.py`, run in `routing_planning.py` right after `apply_jev_guard`:
- When the call is an ASK whose facts are all form questions (group_membership, time_model, spatial,
  input_network), the guard's own `check_typed_data` runs on the workflows those questions lead to.
- When it rules them all out, the call becomes the guard's data confirm (`conditioned_core`, ASK `jev_condition`),
  exactly as a DO would get it. The guard's code binding of the yes/no answer then declines on a "yes".
- Otherwise the call is left unchanged. Nothing else changes, nothing here declines, and the guard's file is not
  edited (its functions are only called).

## Cases (`cases.json`)

Every recorded form-only ASK in j4g, j3g, jo1, jf1, jfsmoke, ja1 and jasmoke: 28 calls. One labeller (me), with the
item golds: does the user's stated data rule out the workflow the form question leads to?
- Data rules it out (5): j4g S32 t2, ja1 S32 t2, jo1 Q18 t1 (an expression matrix for SAMBAR), j4g S10 t2 and t3 (a
  DRAGON protein-metabolite network for CONDOR).
- Data acceptable (23): every other case. This includes jf1/jfsmoke J40, an nsbase item (not j1 J40) about a TF-gene
  edge list for CONDOR.

## Gates

- E0, off = no change: with either flag off the step reads nothing; flags-off harness replay 0 of 1388 changed vs
  `replay-frozen.json`; the test suite (clean environment) has no new failures beyond the known env-dependent one.
- E1, precision (hard): 0 of the 23 data-acceptable cases turn into the data confirm.
- E2, recall: >= 3 of the 5 data-ruled-out cases turn into the data confirm.
- E3, shape: every changed call is ASK `jev_condition` from `conditioned_core`, with the evidence saying it came from
  a form ASK. No call becomes DO or DECLINE here.

Measured offline by running the step on each case's recorded call and task (Jev typed reads, under US$0.01).
Stop rule: if E1 fails, the change is withdrawn as declared.

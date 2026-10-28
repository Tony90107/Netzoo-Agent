# The check's own model takes the compact schema over the 1,000-enum limit (2026-10-28) — declared before code

User decision (2026-10-28): fix the remaining problems in order; tracing S35 / S03's UNCHECKED finals found this.
Declare gates, test offline, then ask before any live run. Branch `jev-conditions`, worktree `.worktrees/netzoo-j4`.

## Problem

Since 2026-10-20 the capability check's own model is `openai/gpt-4o-mini-2024-07-18` (memory: nemotron's provider
404s; a temporary user decision). OpenAI's strict mode takes at most 1,000 enum values per schema. The check's schema
has one field per request sentence, each repeating the sheet ids, methods and settings: 907 values at 4 sentences,
1,066 at 5 (`expanded_enum_values`). `capability_check_call` switches to the compact schema (names as strings, 313 at 5
sentences) only when the call is the backup (`llm is fallback_llm`), a rule from when the own model was nemotron.

So every request of 5 or more sentences fails its check with a 400 ("Expected at most 1000 enum values … received
1010"), is not retried (a 400 is not retryable), and ends provisional. In the recordings: **every 5+-sentence turn
since 10-20 failed, 6 of 6** (j1a J20 t3, J48 t3; j3g R21 t3; j4g S05 t3, S35 t3; jo1 Q02 t3, all third turns that
carry the earlier turns), 5 ending UNCHECKED `check_unconfirmed` and S05 needs_fact. The 11 earlier 5+-sentence turns
ran on nemotron and were checked.

The re-read (`request_capability_reread`) has the same rule missing: 775 values at 5 passages, 1,240 at 8.

## Change

In `graph/capability_check_call.py`, both calls take the compact schema when the expanded schema is over `_ENUM_LIMIT`
and the model is routed to OpenAI (`openai/…`, or the backup as before). Nothing else: the compact schema and the
reading of unregistered names are the ones the backup path already uses (tests in `test_requirement_split.py`).

## Gates

- K0, off-path unchanged: a schema at or under the limit, or a model not routed to OpenAI, keeps the full schema (unit
  tests); the harness replay (no live calls) 0 of 1388 changed vs `replay-frozen.json`; the test suite has no new
  failures beyond the two known ones.
- K1, scope: over every recorded turn text, the new rule compacts only texts of 5+ sentences, and every one of those
  read by gpt-4o-mini failed with the enum 400 (so no call that worked changes).
- K2, the failure is gone: a unit test with a recording LLM named `openai/gpt-4o-mini-2024-07-18` as the check's own
  model sees only schemas at or under 1,000 values for a 5-sentence request, on the check and on the re-read.

What a compact reading then decides on those turns needs live calls; that is for the user to approve after the
offline gates (the 6 turns above, re-run from turn 1, gpt-4o-mini).

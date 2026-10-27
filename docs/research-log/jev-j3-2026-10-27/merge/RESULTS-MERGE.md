# Merge checks (PLAN-MERGE.md, user-approved 2026-10-27) — M0-M4 all pass

Refactor d3e3e1c6 on branch `jev-merge` (from jev-combined 08651594):
- `netzoo_agent_core/jev_client.py` is a leaf transport (standard library only), used by `graph/jev_guard_call.py`
  and the new `graph/jev_overlap_call.py`.
- `build_capability_check(..., overlap_reader=None)` makes no Jev call of its own. The router passes
  `overlap_reader()` (None when NETZOO_JEV_OVERLAP is off) to both its builder calls; `required_check_budget` passes
  none.
- `interpretation/jev_overlap.py` keeps only the frozen question, the threshold and the `doubted` rule.

| check | result |
|---|---|
| M0 full suite, clean env | 5066 passed, 51 skipped, 0 failed (M0-tests.log) |
| M1 flags off vs frozen | harness replay 0 of 1388 changed (M1-compare.txt) |
| M2 flags on, refactor vs pre-refactor (same Jev cache, 27 reads, no live call) | harness 0 of 1388 changed; j-set replay identical (23 entries); reason lines identical (50 entries); pre-refactor also identical to jev-overlap's recorded replay-on-r2 / jsets-on-r2 / reasons-r2; flag on vs frozen = the same 12 changes; the adapter injected the reader on 1726/1726 builder calls |
| M3 boundaries | test_agent_module_boundaries passes (in M0); a test asserts jev_client imports only json/os/urllib |
| M4 live smoke (both flags on, 3 seen j3 items, US$0.025) | events written: R02 jev_condition → jev_answer; R12 jev_overlap + jev_link; R30 jev_guard + jev_condition; 0 errors; code unchanged |

Main moves by fast-forward to this branch. Both Jev flags stay off by default.

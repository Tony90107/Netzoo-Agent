# Jev overlap round 2 — offline results (2026-10-27)

Change (ROUND-2.md): a result row typed several_groups and credited to no produces entry is read by Jev (same
question, same threshold). P(overlapping) <= 0.3 sets `doubted_forms=["group_membership"]`, and `_form_reasons`
leaves out the overlap reason. Code: `contracts/capability_check.py` (field), `interpretation/capability_check.py`
(hook), `interpretation/stated_reasons.py` (skip); tests in `tests/test_jev_overlap.py`; the schema pin
(`tests/test_contracts_package.py`) was updated, and the digest returns to the old pin when only the new field is
removed. Jev reads cached in `jev-cache-r2.json`, under US$0.001.

Raw: `reasons-r1.json` (round-1 code, flag on) and `reasons-r2.json` (`measure_reasons.py`: 50 readings typed
several_groups from population.json plus live jo1), `replay-off-r2.json`, `replay-on-r2.json`, `jsets-on-r2.json`,
`gates-r2.txt`.

| gate | result |
|---|---|
| G0 flag off = no change | replay 0 of 1388 calls changed vs replay-frozen.json; tests 5064 passed, 51 skipped, 0 failed **PASS** |
| G1 overlap requests keep the reason (hard) | 8 of 8 readings that printed it with round 1 still print it (JN8 ON5 QN5 SN1, replay + jo1) **PASS** |
| G2 >= 75% of not-overlap readings lose it | 12 of 12 (j2f Q01, Q13 t1, Q37 t1/t2; j2g Q01, Q13 t1/t2, Q18 t1, Q37 t1/t2; jo1 Q01, Q13 t1) **PASS** |
| G3 calls unchanged vs round 1 flag on | harness 0 of 1388 changed vs replay-on.json; j-set readings 0 changed vs jsets-on.json **PASS** |
| G4 layer 2 only | 17 changed lines: each is layer 2 ("I couldn't match this to anything a registered NetZoo workflow produces or lets you set.") or a subset of the reasons it already said; 0 new reason text **PASS** |

Lines outside the 12 readings: none changed.

## Notes

- The first full-suite run in `gates-r2.txt` showed 29 failures. Its shell had sourced `netzoo_agent/.env`, which
  sets model variables that tests do not expect (`test_semantic_claims.py`: 1 failed with the file sourced, 43 passed
  without). Rerun in a clean environment, the only failure was the schema pin, which is now updated: 5064 passed.
- Q13 (10 sarcomas, 2 to 12 groups) now says layer 2 instead of a wrong reason. The real reason (k up to 12 with 10
  samples) is still not given, because the row was credited to no workflow and its count was never judged.
- Not measured live: the change touches only reply lines, so the calls are those of RESULTS-LIVE.md.

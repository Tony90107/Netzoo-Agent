# data-has -- offline measurement (2026-10-29): D1, D2 PASS

348 j1-j8 gold items, opening prompts; the guard's existing data read and the new has-read (`HAS_INSTRUCTIONS`, the
guard's `DATA_CRITERIA` options), each one Jev call; US$0.016, 0 errors. `SCORE.txt`, `measure.json`.

| Gate | Result |
|---|---|
| D1 precision (hard) | gold DO / PARTIAL items (158) with a gold workflow ruled out: existing 0, new 0, **union 0** -- PASS |
| D2 recall | j2 Q18: existing `expression_matrix` 0.32 (below 0.7), has-read `expression_matrix` **0.80** -> SAMBAR ruled out by its `incompatible_input_artifacts`. Data-type gold-DECLINE items (27): existing 17, union **18** -- PASS |

Small and precise: the has-read adds Q18 and nothing else (its reads track the existing ones, mostly a little less
confident; it never ruled out a gold-DO workflow). The 9 data-type items neither read catches are N n_decline items
whose refusal is not a data kind (or "several").

Next by the ROUND: build it in the guard's `check_typed_data` (jev-guard session first), replay + tests, then live.

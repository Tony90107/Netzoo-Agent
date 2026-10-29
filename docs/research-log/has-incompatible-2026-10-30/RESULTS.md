# has-incompatible -- offline results (2026-10-30): E1-E4 PASS

| Gate | Result |
|---|---|
| E1 precision (hard) | 158 gold DO / PARTIAL items: existing read OR restricted has-read rules a gold workflow out in **0** (`OFFLINE.txt`, data-has's recorded reads, no new call). |
| E2 recall | j2 Q18 has expression_matrix 0.80 -> SAMBAR ruled out; data-type DECLINE items 17 -> **18**. |
| E3 stability (hard) | data-has's 10x reads: Q18 **10/10**; W17 and Z14 (CONDOR, empty incompatible list) **0/10** by construction. |
| E4 build | `check_typed_data`: with `NETZOO_JEV_DATA_HAS=on` and not every workflow already ruled out, one more Jev call (the frozen has-question); a workflow is ruled out by it only through its `incompatible_input_artifacts`; `ruled_by` / `ruled_kind` recorded; `condition_question` names `ruled_kind`. Unit tests `tests/test_has_incompatible.py` 3/3 (off = no extra call; Q18 shape; W17 shape never ruled out even at 0.95). Flags-off replay byte-identical; clean-env tests 5187 passed, only the 2 known env-dependent failures. |

The jev-guard session was not running when the edit was made; it had agreed to edits in `check_typed_data` for
data-has with three conditions (name the ruling kind, chain controls, stability) -- all three are met here. It must
review before any merge. E5 live not run yet.

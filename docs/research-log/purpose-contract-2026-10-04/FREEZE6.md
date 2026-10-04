# Path (b') freeze (Log 357 preparation)

b' = path (b) (Logs 355-356) with two design checks in the verification. Frozen before
anyone on the implementing side read the sixth held-out set (`heldout6/`), which an
isolated subagent was writing at the same time.

Frozen copies in `b2_frozen/` (sha256):
- `8fe49efcc9e74631a08e353b7097a70b9234c89e66e4b9f46518ae7887bfabd3` study_purpose_verify.py
- `cb2c1fcdde6e056c27d06a153ebae8130c89b4e11b45ab10d19e00dd05be2de8` study_purpose.py
- `e2af95adf863ba89dff8108f6f1254e7f1f41f74ebd4d582d000177820fd491b` study_purpose_system.txt

- The prompt (`study_purpose_system.txt`) and the contract (`study_purpose.py`) are identical to `b_frozen/`.
- The verification adds, against `b_frozen/study_purpose_verify.py`:
  1. "same" no longer lifts the two-data-type or technical-pairing veto; only a time point or a condition
     does (fifth set T4, "Paired RNA-seq and methylation arrays from the same 80 ... resections");
  2. groups are rejected when the quote's sentence splits the same individuals between the conditions
     ("each ... split", "split into", halves, "from the same N patients", within-donor) (fifth set M6).
- On seen proposals: Log 354's 387 -- design 254/297, conclusions 237/264, 0 false (unchanged); the fifth
  set's 96 -- design 48/66 with 0 false (b: 9 false), conclusions 54/66 with 0 false (b: 57/66), 0 false
  causal/prediction.

Any change after this commit must be declared and reported separately from the sixth held-out results.

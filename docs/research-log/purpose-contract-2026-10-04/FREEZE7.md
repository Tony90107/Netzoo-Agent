# Path (b'') freeze (Log 359 preparation)

b'' = b' (Logs 357-358) with two more verification rules. Frozen before anyone on the
implementing side read the seventh held-out set (`heldout7/`), which an isolated subagent
was writing at the same time.

Frozen copies in `b3_frozen/` (sha256):
- `25a247ab45c5ca66471f762b93cffc9406a1d8b5aae14d4b4c9bcaa661fba08b` study_purpose_verify.py
- `cb2c1fcdde6e056c27d06a153ebae8130c89b4e11b45ab10d19e00dd05be2de8` study_purpose.py
- `e2af95adf863ba89dff8108f6f1254e7f1f41f74ebd4d582d000177820fd491b` study_purpose_system.txt

- Prompt and contract are identical to `b_frozen/` and `b2_frozen/`.
- The verification adds, against `b2_frozen/study_purpose_verify.py`:
  1. a quote that sets out to show a cause ("show/prove/establish/demonstrate/confirm that ... cause/drive/
     ...", or "cause" used as a verb) supports no conclusion other than causal (sixth set P2-b);
  2. an individual change needs, besides the individuals (which/whose/who/rank/individual/each patient or a
     subject noun), a change, an extreme or a ranking word (sixth set P2-d); "who" was added after the fifth
     set's M4-a "Who shows the most dramatic rewiring" was lost by the first version of this rule.
- On seen proposals: Log 354's 387 -- design 254/297, conclusions 237/264, 0 false; fifth set's 96 --
  design 48/66, conclusions 54/66, 0 false; sixth set's 96 -- design 63/63, conclusions 50/60, 0 false
  (b': 4 false); 0 false causal/prediction everywhere.

Any change after this commit must be declared and reported separately from the seventh held-out results.

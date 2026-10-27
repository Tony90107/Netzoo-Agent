# Step 1 — contract conditions a DO misses (declared 2026-10-27, before any call)

User request (2026-10-27): "design the per-workflow contract-condition checklist with Jev, declare gates, test offline
first". Target: false accepts, where the request states a fact a contract rules out but the call is DO (j1 J11 layers
from different patients for DRAGON; J24 a mutation matrix for LIONESS-COEXPRESSION).

## Design

1. **Checklist (code, verbatim):** for each workflow of the DO call, its contract lines (`contract_lines`):
   - every handoff-contract sentence;
   - every `input_checks` text;
   - one line per `incompatible_input_artifacts` entry, written `<WF> incompatible_input_artifacts: <artifact>`
     (the YAML field and value, not prose).
2. **Jev, one call:** one choice question per line (`violates` / `meets` / `not_stated`), with state = the request.
3. **Jev, second call, only when a line is violated at confidence >= 0.7:** which request sentence states the
   breaking fact (code-cut sentences + `none`).
4. **Code:** a violated line plus a sentence, both at >= 0.7, turns the DO into ASK, basis `jev_condition`, a
   confirm question quoting both: "You wrote: '<sentence>'. <WF>'s contract: '<line>'. Is that right for your data?"
   The pending question carries the line (`labels.contract`), so step 3 reads the answer: a confident `fails` →
   DECLINE with both quotes. A first-turn reading never refuses on its own; only the user's confirmation does.

## Offline test (`conditions_offline.py`, Jev only, about US$0.01)

Data (`conditions_data.py`): 124 unique first-turn DO calls with their workflows, from the replay (757 labelled), j1
arm S, h10 and h9 (all seen). Gold: DECLINE 16 (targets), DO 79 (controls), ASK 16, CLARIFY 9.
Flag = steps 2-3 both pass.

Gates:
- **C1 precision:** flags on gold-DO calls <= 4 of 79; on DRAGON controls (j1/h10/h9 dragon_control with gold DO)
  <= 1.
- **C2 recall:** flags on gold-DECLINE calls >= 6 of 16.
- **C3 net:** flags on gold DECLINE + ASK + CLARIFY >= 2 x flags on gold DO (each needless question paid by two
  fixes; ask-cost scoring).

All pass → build behind the guard flag, unit tests, flag-off replay 0 changes, then a declared live check. Any fail →
stop and report. No wording retries; any other threshold is post hoc and labelled.

## Result (CONDITIONS-OFFLINE.txt, US$0.0085) — NOT PASSED, step 1 as declared withdrawn

Flags 15: gold DECLINE 4, DO 7, ASK 2, CLARIFY 2; 4 more lines violated with no sentence found.
- C1 fail: 7 of 79 gold-DO calls flagged (<= 4); DRAGON controls 0 of 6.
- C2 fail: 4 of 16 gold-DECLINE caught (>= 6). Caught: J11 (different patients), J24 (mutation matrix), M46, C27.
- C3 fail: 8 fixes < 2 x 7.

Not built; the guard code keeps `condition_lines` / `check_conditions` unused (offline only).

## Post hoc (CONDITIONS-POSTHOC.txt; recomputed from the recorded per-line reads; not a gate)

No variant (typed lines only; first workflow only; both) gets under 6 false flags; recall stays 5-6/16. The false
flags are Jev misreading prose conditions, not scope:
- Numeric comparison: J32 (22 patients) flagged against "Require at least three expression samples".
- Alternatives inside one contract: J47, H22 (an OTTER request with a co-expression matrix, which OTTER takes) flagged
  against the expression-file line read alone; L46, W10 likewise on OTTER's matrix line.
- Misses are mostly settings and limits (GIRAFFE optimizer settings, DRAGON lambda pairs, SAMBAR k ranges, BONOBO),
  which are typed controls, not prose lines.

Lesson: Jev should not judge contract prose line by line. Numbers and alternatives belong to code over typed slots.
A redesign (Jev picks the artifact type the user gives for each required slot from a closed menu of artifact types;
code compares it with accepted / incompatible / refuses_input; counts stay with the existing code checks) is a new
round that needs its own declaration and the user's go-ahead.

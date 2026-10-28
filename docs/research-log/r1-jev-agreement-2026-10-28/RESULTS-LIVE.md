# R1 + Jev agreement -- live G4 (2026-10-28, user "跑 live"): G4a, G4b PASS -> KEPT

Run ra1: code 8af7574b, app settings (guard on), gpt-4o-mini, turn 1, 1 rep. Spent **US$0.023** (cap 0.08).
Raw: `live/ra1/`, `live-ra1.log`.

| item | gold | fact check | Jev read | rule | call |
|---|---|---|---|---|---|
| j5 W40 (somatic or germline) | ASK | 0 kept, 1 R1-rejected | ASK | `jev_agent: ask` | **ASK/jev_agent** (was DO) |
| j1 J46 (file shape) | ASK | 0 kept, 1 R1-rejected | ASK | `jev_agent: ask` | **ASK/jev_agent** (was DO) |
| j5 W18 (lanes; control) | DO | 1 kept | DECLINE 0.23 | not reached | ASK/fact_agent |
| j4 S14 (poly-A; control) | DO | 1 kept | DO 0.67 | not reached | ASK/fact_agent |
| j3 R21 (flow cell; control) | DO | 1 kept | DO 0.47 | not reached | ASK/fact_agent |

- **G4a pass:** no control ends turn 1 with a `jev_agent` ask.
- **G4b pass:** W40 and J46 end turn 1 ASK through the rule.

Honest reading: Jev did not read ASK on any of the three controls in this run, so the rule was never reached there;
as offline, the precision side is shown by no misfire, not by a control the rule saw and rejected. The controls'
ASK comes from the fact agent asking their irrelevant doubt directly (the W18 problem, jev-relevance withdrawn), not
from this change.

## Correction (jev-guard review, same day): G4b was scored on the call's kind, not on what the user saw

`jev_agent` was not registered where an ASK becomes the reply (`core_decision.with_core`, `ask_facts.ask_result`,
`semantic_goal`). In ra1 W40 the core was ASK/jev_agent, but `ask_result` returned None and another renderer answered:
stdout is the DO guidance for SAMBAR ("Selected path: **SAMBAR**"); the somatic/germline question was never shown, and
`with_core` did not clear the run fields. So ra1 does **not** show the fix working; the KEPT above is void until the
rerun below.

Fixed: `jev_agent` added to the three basis tuples; `tests/test_r1_jev_agreement.py` now checks that `with_core` clears
the run and `ask_result` shows the fact's question. Tests 5151 passed (2 known failures), replay 0 of 1388.

## Rerun ra2 (code 59ebf9f1, W40 + J46, turn 1, US$0.007): G4b PASS on the reply text -> KEPT

| item | call | reply |
|---|---|---|
| W40 | ASK/jev_agent | "Before I choose a workflow, please tell me: - Does the variant matrix contain somatic calls from tumour-normal pairs? You wrote: ... SAMBAR's contract: ..." -- no "Selected path" |
| J46 | ASK/jev_agent | "... - Is the file a labeled symmetric square gene-by-gene matrix? You wrote: ... OTTER's contract: ..." -- no "Selected path" |

G4a stands from ra1 (no control reached the rule). Both targets now show the fact agent's question to the user.

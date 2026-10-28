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

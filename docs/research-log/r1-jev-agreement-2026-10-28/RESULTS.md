# R1 + Jev agreement -- offline results (2026-10-28): G1-G3 PASS (G1 untested by controls)

Change: `jev_guard_call.agreed_fact_core`, called in `apply_jev_guard` before `guarded_core` when the call is DO or
DECLINE: a fact-agent proposal rejected by "R1 the check did not read these words as the user being unsure", whose
words lie in the sentence Jev's ASK read picked, is re-run through `kept_facts` with that sentence as an uncertain
quote; if kept, the turn asks it (basis `jev_agent`, a plain fact-agent fact). Event `core.jev_agent` (shadow too).

| gate | result |
|---|---|
| G1 recorded labelled t1 sessions: non-ASK items changed (hard) | pass, **but untested**: all 50 recorded sessions with a Jev ASK read are on gold-ASK items, so no non-ASK doubt control reached the rule (`rebuild.py`, `REBUILD.txt`) |
| G2 W40, J46 change to ASK | pass: W40 asks "Does the variant matrix contain somatic calls from tumour-normal pairs?"; J46 asks its file-shape question (2 sessions) |
| G3 clean-env tests / flags-off replay | pass: 5148 passed, 2 failed = the two known; 0 of 1388 changed; plus `tests/test_r1_jev_agreement.py` 2/2 |

Rebuild detail: 24 of the 50 change to ASK (all gold ASK). Most were guard-on runs where the guard would already
ask its own `jev_fact` question; the rule asks the fact agent's contract-grounded question there instead (it runs
before `guarded_core`, as agreed with jev-guard). 1 proposal is rejected by another rule after re-check (kept off).

The precision evidence must come from the live check: W18, S14, R21 (non-ASK items stating an irrelevant doubt).

# Steps 2 and 4 — which registered result the user asks for (declared 2026-10-27, before any call)

User request (2026-10-27): move to step 2 (false refusals: a workflow produces it but the call is DECLINE, j1 J17
CONDOR, J37 COBRA) and step 4 (CLARIFY although a result is named, j1 J42, J38). The user also asked whether typed
questions should be per NetZoo workflow. They are generated per workflow from the contract, never hand-written.

## One typed question, generated from the contracts

`result`: "Which result does the user ask for?" Options: one per workflow, its YAML description + output capability
(`result_menu`), plus `none_registered` and `not_named`. One Jev call per request.

## Step 2 rule (a DECLINE that says nothing produces it)

Only on DECLINE with basis `full_gap`, `all_results_not_available` or `routing_unsupported`, the result-level refusals.
Setting and limit refusals are never touched. If Jev picks a workflow at confidence >= 0.7 → ASK, basis `jev_link`, a
confirm question: "Did you mean <WF>'s result: <its contract description>?" The user's yes re-enters the normal
pipeline. Never a DO.

Gates on the result-level DECLINE calls in results-data.json:
- L1: flags on gold DECLINE <= 6 of the 66 (each a needless question on a correct refusal).
- L2: flags on gold DO >= 4 of 10 (false refusals turned into a confirm).
- L3: fixes (gold DO + ASK flagged) >= 2 x flags on gold DECLINE + CLARIFY.

## Step 4 rule (a CLARIFY although a result is named)

On any CLARIFY: if Jev picks a workflow at >= 0.7 → ASK `jev_link`, the same confirm question, which is narrower than
"which result do you want?". Scoring caveat: CLARIFY → ASK fixes only gold-ASK items by kind. On gold DO / DECLINE both
count as a question (cost). On gold CLARIFY it creates a wrong-kind error.

Gates on the CLARIFY calls:
- K1: picks on gold CLARIFY <= 7 of 69 (new wrong-kind errors).
- K2: picks on gold DO + ASK + DECLINE >= 8 of 23.

Each step is judged on its own. A pass earns a build plus a declared live check; a fail stops that step. Data: seen
sets (replay, j1, h9, h10). The menu is the contracts' text, not tuned.

## Offline result (LINKS-OFFLINE.txt, 175 calls, US$0.0076)

**Step 2: NOT PASSED, withdrawn.** On result-level DECLINE calls Jev picks a workflow on gold DO 8/10 (L2 pass), but
also on 40/66 correct refusals (L1 fail, L3 fail). Most `full_gap` refusals are a named result that fails a condition
(COBRA genes vs samples, three DRAGON layers, too few samples, SAMBAR k range, unexposed settings), not a result no
workflow makes. Knowing which result is asked cannot separate them. That belongs with the typed conditions of step 1′.

**Step 4: PASSED.** On CLARIFY calls Jev picks a workflow on 1/69 gold CLARIFY (K1 pass, the one is J23 "do LIONESS")
and on 16/23 of the others (K2 pass: DO 8, ASK 5, DECLINE 3).

## Step 4 build (declared before the live check)

On a CLARIFY, a Jev `result` pick at >= 0.7 turns it into ASK `jev_link`: "Did you mean <WF>'s result: <its YAML
description>?" (contract_quote = the description). It is asked once per task: never twice, and never carried into
step 3's answer judging, because a "no" must not decline. The answer re-enters the normal pipeline.

Live check: the j1/h10/h9 items whose recorded call was a non-gold CLARIFY (J38, J42, W03, W08, W11, W14, W16, W17,
W23, W30, W34, Z12), guard on, turns 1-2 (restate reply), <= 12 sessions, about US$0.08. Reported: turn-1 jev_link asks,
turn-2 calls against gold, any new error.

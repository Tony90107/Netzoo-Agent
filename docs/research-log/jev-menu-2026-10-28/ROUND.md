# Jev's result menu lists each contract's produced artifacts (2026-10-28, user: "先補選單")

## Why

`jev_guard_call.result_menu()` builds one option per workflow from its YAML: `description`, `artifact_type`,
`granularities`, `regulator_types`. It leaves out `output_capability.produced_artifacts`, so GIRAFFE's option says
"signed_regulatory_effect_network (aggregate)" and never its own `tf_activity_matrix`. On j5 (seen), W23 and W45
("which TFs are switched on in each sample, and whether each activates or represses its targets", gold GIRAFFE) Jev
picks LIONESS-PANDA at 0.43 / 0.58. W45 turn 1 was a CLARIFY, where the live step-4 link acts at >= 0.7.

The step-2 link on result-level refusals stays withdrawn (LINKS.md); this round changes only the menu text.

## Change

Each option also lists the contract's `produced_artifacts` (YAML text, nothing hand-written). No other change; the
menu is used only by `check_result` (step-4 links on CLARIFY, guard flag on).

## Gates (declared before the code; offline, Jev calls only, about US$0.02)

Data: the 175 recorded calls of `jev-guard-2026-10-27/links-offline.json` (gold per call), `check_result` run now
with the old menu and with the new one (Jev 1.13; repeat reads were identical in jev-shadow).
- **K1 (hard):** step-4 picks (>= 0.7) on gold-CLARIFY CLARIFY calls with the new menu <= the old menu's count.
- **K2:** step-4 picks on the other CLARIFY calls (gold DO / ASK / DECLINE) with the new menu >= the old menu's count.
- **K3:** every CLARIFY call whose pick changes is listed with old and new pick; a new pick naming a workflow that is
  not the gold's counts against the round (reported; if it outnumbers new right picks, withdraw).
- **K4:** flags-off harness replay 0 of 1388 changed; clean-env tests no new failures.
- Reported, not gated: j5 W23 / W45 picks (seen), and picks on result-level DECLINE calls (step 2 stays off).

Stop rule: K1, K2 or K4 fails, or K3 as stated -> withdraw. No gate is changed afterwards.

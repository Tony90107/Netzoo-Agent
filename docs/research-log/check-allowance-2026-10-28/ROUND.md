# Check allowance sized for the gpt-4o-mini check (2026-10-28, user: "先修J34")

## Problem (app-config-align-2026-10-28 RESULTS-LIVE.md, ca1 J34 t1)

The check family (check, re-read, second opinion, condition check, fact check, study purpose, data facts, goal read,
settings read, hybrid gate) shares one ceiling: turn budget 30,000 + `CHECK_EXTRA_TOKENS` 30,000, minus the 1,500
safety reserve. J34 t1 took the long reading path (interpreter, sibling repair, reviewer: 25,506 before the check),
the check read 18,389 and the re-read 11,459 tokens, so at 57,264 the second opinion (2,396 + 4,000 reserved) and the
fact check were refused; the final was UNCHECKED/check_unconfirmed.

The 30,000 allowance was sized in M2 (2026-10-14) for nemotron (check ~12.5k in). On the 839 recorded turns with the
gpt-4o-mini check, the family alone used p50 21.1k, p99 33.1k, max 40.6k, and whole turns reached p99 52.1k, max
57.3k: the ceiling (58.5k) is reached by a long routing path plus a long check, as in J34.

## Change

`CHECK_EXTRA_TOKENS` 30,000 -> 45,000 (code default; the app compose does not set `OPENROUTER_CAPABILITY_EXTRA_TOKENS`).
Sizing rule: the family's recorded maximum on the gpt-4o-mini corpus (40.6k) plus the own model's output reserve
(4,000), rounded up to the next 5k. The turn budget (30,000, routing calls) is unchanged, so routing cannot spend the
new room; only the check family can.

Considered and not chosen: skipping the optional re-read when the required second opinion / fact check would not fit
afterwards. It keeps the ceiling but drops reads that ask for unread passages, a behaviour change that cannot be
measured offline (the re-read's effect needs model calls).

## Gates (declared before the code change)

- A1 Offline replay of all recorded gpt-4o-mini-check turns (simulate.py budget rules, aligned settings, 45k
  allowance): 0 check-family refusals, J34 ca1 t1 included (second opinion and fact check fit).
- A2 Only refused calls change: calls that ran on the 30k allowance all still run (no call goes from run to refused).
- A3 Routing calls (turn budget) unchanged: the same `selection_conditions` / `hypothesis_bases` refusals as before.
- A4 Clean-env tests: no new failures beyond the two known ones; tests pinning the 60,000 ceiling are updated to the
  new default and say why.
- Cost: the extra room is used only by turns that would have been refused; at gpt-4o-mini prices at most +15k
  tokens on such a turn (~US$0.0023).

Stop rule: a failed gate -> revert, report; no gate is changed afterwards. Live J34 reruns only after the user agrees
(the long reading path is random, so a rerun may not take it).

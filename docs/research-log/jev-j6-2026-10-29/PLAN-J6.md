# Fresh sealed set j6: the app after the 2026-10-28 fixes (plan, 2026-10-29)

User: "出 j6 大概30題即可". j1-j5 are seen; every fix since j5 (feature-count doubts, mixed notation, Jev menu,
granularity left unknown, checked default line, checked scale question, exhausted wording, R1 + Jev agreement) was
verified on seen items only. Nothing runs before the user sees the item counts and the cost.

## Code and settings under test (no change)

main **1f788661**; one arm on the app's settings (app `.env`: GUARD, OVERLAP, FORMS on, own check model; compose
defaults: 30,000 turn budget, code check allowance 45,000). The runner refuses to start if `scripts`, `workflows`,
`prompts` or `AGENTS.md` differ from 1f788661.

## The set (30 items, ids X01-X30, 17 groups as j5 at smaller counts; `j6/AUTHOR-BRIEF.md`)

Blind author subagent (reads only `workflows/*.yaml` and `workflow_registry.py`), blind gold reviewer subagent, sealed
with SHA256 before any run; I read only counts. U has one sample-count and one feature-count candidate pair; TC has
one irrelevant-doubt item (the W18 shape).

## Run and report

gpt-4o-mini, up to 3 turns, 1 rep, j4/j5 reply rule unchanged. Reported (a measurement, no gate): right finals of
30, FA / FR / MA, by group; check health; every wrong final traced to one cause class (j5's classes). j5's 36/48 is
another set: cited, never subtracted. After scoring, j6 is seen.

## Budget

j5 (48 items) cost US$0.29; j6 about US$0.18. **Cap US$0.40**, enforced by the runner.

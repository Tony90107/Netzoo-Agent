# Jev-first linking, phase C: built behind a flag, tested live on a fresh set (2026-10-29, user "做 A 的連結")

## Basis

Phase A (`jev-first-links-2026-10-29`) passed A1-A3: with Jev's link taken when its confidence >= 0.7 (else mini's),
gold-DO check-level right 101 -> 120 of 168, false accepts 40 -> 42, confident picks right 184/194. Phases B/B'
(Jev's typed fields) failed their false-accept gates and are NOT part of this build.

## Change

- Flag `NETZOO_JEV_LINKS_FIRST`: off (default) / shadow (read and record only) / on (apply).
- For the turn's main reading only (not the re-read), before `build_capability_check`: each ask's `delivered_by`
  becomes Jev's pick from the frozen phase-A menu (one capability-sheet produces entry, or none -> []) when Jev's
  confidence >= 0.7; otherwise mini's stays. Any Jev failure leaves the reading as it was. Everything after (code
  checks, condition check, guard, fact agent) is unchanged. The reads are recorded as `core.jev_links_first`.
- The question and menu are phase A's, moved unchanged into `interpretation/jev_links_first.py`.

## Gates (declared before the code)

- **P1** unit tests: on -> a confident pick replaces `delivered_by`, a low one keeps mini's, "none" gives [], an
  error keeps the reading; shadow records and changes nothing; off makes no call.
- **P2** flags-off harness replay byte-identical to main's; clean-env tests no new failures (module size included).
- **P3** parity: the built function, fed phase A's cached reads, reproduces arm H on the 433 readings (120 / 42).
- **P4 live** on a fresh sealed set j7 (30 items, authored and gold-reviewed blind as j6; nothing run before
  sealing), the app's settings, two arms paired by item: flag off vs on, up to 3 turns, 1 rep, the j4-j6 reply rule.
  Hard: right finals on >= off; false accepts on <= off + 1. Reported: FA / FR / MA, every item that changed, Jev's
  pick vs mini's per ask.
- Cost cap US$0.80 for P4 (gpt-4o-mini pre-approved; Jev ~US$0.0001 a turn).

Pass -> ask the user whether to merge (flag default stays off) and whether to turn it on in the app `.env`.
Fail -> withdraw (flag code reverted), report. No gate is changed after the run.

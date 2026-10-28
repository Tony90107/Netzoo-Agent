# The check model's output cap fits gpt-4o-mini (2026-10-28) — declared before code

User decision (2026-10-28): fix the remaining problems in order; tracing j4 S03's UNCHECKED final found this. Declare
gates, test offline, then ask before any live run. Branch `jev-conditions`, worktree `.worktrees/netzoo-j4`.

## Problem

The check model's output cap and its budget reservation default to 16,000 tokens (`OPENROUTER_CAPABILITY_MAX_TOKENS`
is not set in the app .env). That cap was sized for nemotron, a reasoning model (Log 414 and the 2026-10-16 note:
outputs up to 12,906 with reasoning). Since 2026-10-20 the check's own model is gpt-4o-mini. Its recorded outputs
(every call in docs/research-log with that model): capability_check n=840, max 2,258 (p99 1,308); re-read n=193, max
883; second opinion n=72, max 136.

Every optional check call reserves 16,000 tokens at preflight, so late in a turn they are refused by the 60,000 hard
limit: 65 `budget.blocked` events on gpt-4o-mini turns (54 re-reads, 11 second opinions; consumed 36,513-46,233). The
11 blocked second opinions are 11 of the 16 UNCHECKED `check_unconfirmed` turns on gpt-4o-mini (the other 5 are the
enum-limit failures, check-enum-limit-2026-10-28). j4 S03 t2: consumed 44,616 + 452 input + 16,000 reserve = 61,068.

## Change

`required_check_budget.capability_max_tokens(model)`: `OPENROUTER_CAPABILITY_MAX_TOKENS` when set (unchanged);
otherwise 4,000 for a model routed to OpenAI's gpt-4o family (`openai/gpt-4o…`), else 16,000 as before. The three
places that read the default (the own LLM's max_tokens, `check_output_reserve`, the fact-check reservation) use it.

## Gates

- R0, unchanged elsewhere: with the variable set, or a model outside `openai/gpt-4o…`, the cap is what it was (unit
  test); harness replay 0 of 1388 changed; the test suite has no new failures beyond the two known ones.
- R1, no output cut: every recorded gpt-4o-mini check, re-read and second-opinion output is at most 4,000 tokens (max
  2,258).
- R2, the blocks clear: recomputing each of the 65 recorded `budget.blocked` events with a 4,000 reserve, every one
  fits the hard limit.

What the unblocked second opinions and re-reads then decide needs live calls; for the user to approve after the
offline gates.

# 2026-09-25 Legacy archived-trace replay baseline

## Objective

Restore a reproducible replay path for the earlier Legacy live traces and
measure how much of those saved call sequences still applies to the current
router. This is an offline replay. It made **zero new provider calls** and
incurred **zero provider cost**.

## Root cause

The existing saved-trace replay path accepted only the newer
`raw_structured_provider_io_and_routing_events_v1` format. The larger Sep 23
Legacy traces use an earlier harness format: each trial stores provider I/O
under `results[*]._trace`, repeated prompts appear three times, system-message
bodies are saved as hashes, and schema fingerprints exist only at the global
prompt/schema level. The new path also assumed unique prompt IDs and a
per-call schema fingerprint, so it rejected the old baseline before it could
be replayed.

## Repair

`scripts/saved_trace_replay.py` now normalizes both trace formats. It keeps
repeated trials distinct, requires the old trace's global prompt/schema hash to
match the current source, and then compares each call's schema name and full
message signature. System messages are compared by their captured content
hash. A mismatch blocks the remaining saved responses for that trial. Parse
errors recorded in the old harness are replayed as errors with their recorded
text. Only trials with an exact full call sequence enter the pass denominator.

The baseline JSON contains the per-trace hashes, coverage counts, pass counts,
and divergence summaries:
[`2026-09-25-legacy-old-trace-replay-baseline.json`](2026-09-25-legacy-old-trace-replay-baseline.json).

## Current-source replay of archived Legacy rounds

Every archived round has 32 prompts and three saved live trials per prompt.
The rows below keep each round's 96-trial denominator separate. “Covered
passes” counts only exact full-call sequences; “recorded live passes” is the
original captured evaluator summary and is not the same denominator.

| Archived round | Exact full-call sequences | Covered passes | Recorded live passes | Prompts with all 3 calls exact |
| --- | ---: | ---: | ---: | ---: |
| 3 | 59/96 | 57/59 | 74/96 | 17/32 |
| 4 | 51/96 | 49/51 | 70/96 | 14/32 |
| 5 | 50/96 | 50/50 | 75/96 | 15/32 |
| 6 | 49/96 | 49/49 | 75/96 | 14/32 |

All four traces match the current 32-prompt corpus and global prompt/schema
fingerprint. Their historical policy hash is
`a52d8476a7eca616b7ab908cfed71c01885c40cf7501cc266d1bc165c96a46ba`; the
current policy hash is
`120302275f2d6516d9980fed846dcdb7c36da4fde20b73f5daea2fa01de1f4fa`. Thus,
the current/historical policy hashes do not match. The initial semantic call
matched in all 96 trials in each round; most later divergence is in repair,
review, discriminator, or intent calls. This is consistent with message or
call-shape drift after the first interpretation.

The Sep 24 report recorded 75/96 Legacy semantic-call coverage and 70/96
full-pipeline coverage, with 70/70 covered trials passing. That is a prior
source snapshot, documented in
[`2026-09-24-current-source-frozen-replay.md`](2026-09-24-current-source-frozen-replay.md).
The lower full-sequence coverage above is measured against the Sep 25 source;
it should not be presented as a fresh live accuracy result or as an
apples-to-apples change in model stability. Policy drift and later call-prompt
drift reduce how much of the old response stream can be reused.

## Latest five-case saved A/B traces

These are a separate design: one captured trial per prompt, not 32 prompts by
three repetitions.

| Contract | Exact full-call sequences | Covered passes | Captured calls reused |
| --- | ---: | ---: | ---: |
| Legacy | 3/5 | 3/3 | 8/14 |
| Claims | 5/5 | 5/5 | 12/12 |

The two Legacy divergences occur on the second structured call, where the
repair request messages changed. Claims has exact call-sequence coverage for
all five saved cases. These results describe deterministic current routing
with captured responses. They do not estimate repeated live-model stability.

## Limits and next measurement

Historical rounds 3–6 contain three live repetitions per prompt, but only
14–17 of the 32 prompt groups in each round have all three call sequences
exact under current source. Any disagreement count is conditional on those
covered prompt groups. The five-case traces have one repetition each. Neither
set provides a fresh current-source live stability estimate.

The historical/current policy mismatch is also material: replayed route
differences can reflect changed registered workflow policy as well as changed
router behavior. Re-evaluate live stability only after the routing and policy
surface settles, using a predeclared repeated-trial design and reporting each
contract and corpus denominator separately. No live rerun was performed here.

## Verification

- `python -m pytest -q tests/test_saved_routing_trace_replay.py`: **4 passed**.
- `ruff check scripts/saved_trace_replay.py tests/test_saved_routing_trace_replay.py`: passed.
- `python -m compileall -q scripts/saved_trace_replay.py tests/test_saved_routing_trace_replay.py`: passed.
- `git diff --check`: passed.
- Replayed archived Legacy rounds 3–6 and the saved five-case Legacy/Claims A/B traces without provider calls.

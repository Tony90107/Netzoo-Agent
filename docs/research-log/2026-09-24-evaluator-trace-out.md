# Evaluator trace capture

Date: 2026-09-24

## Why

Round-6 failures required a temporary harness to preserve raw structured-output
calls alongside routing events. The evaluator could save summaries, but not the
provider inputs and responses needed to distinguish interpretation failures
from repair failures. An opt-in trace path removes that instrumentation gap.

## Change

`scripts/evaluate_routing.py` accepts `--trace-out <path>` with `--live`. It
captures each structured call's schema name and hash, messages, raw tool-call
arguments, finish reason, usage, invalid-call summaries, parsed result or
located parsing errors, plus routing events and the final decision. System
prompt text is stored only as a SHA-256 hash. The trace does not include
credential headers, environment variables, or provider exception text. Without
`--trace-out`, the evaluator does not wrap providers or retain raw calls.

The trace is written only to the path explicitly supplied by the caller. The
ordinary evaluator report remains on its existing stdout path.

## Verification

- Python compilation, Ruff, and `git diff --check` passed.
- An inline adapter smoke check confirmed capture of schema, usage, tool-call
  data, parsed output, and routing events; the system prompt body was absent
  while the human prompt remained available.
- `--help` displays the new option, and `--trace-out` without `--live` exits
  with a configuration error before reading credentials or starting a call.
- No live API call or workflow execution occurred. The current shell lacks the
  provider credential, so end-to-end capture from a live evaluation remains to
  be confirmed in an authorized provider environment.

## Remaining limits

Round-6 corpus scores remain historical results, not a fresh measurement of the
current code. The major routing repairs P1–P4 have targeted saved-trace evidence;
the new option makes the next live diagnostic round reproducible without the
temporary harness. The existing full-corpus claims result is still weaker than
legacy and needs a fresh trace before choosing another broad validation-policy
change.

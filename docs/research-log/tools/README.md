# Research tools

Run from the repository root. Each script's docstring has its usage.

| Script | Use |
| --- | --- |
| `traces.py` | Find and load recorded reports (`live-*.json` and `archive/**`, plain or gzip). |
| `fingerprint.py` | Prompt/schema fingerprint for both contracts; unchanged means no provider prompt or schema changed. |
| `grids.py` | Run the five routing grids and compare with a baseline directory. |
| `scan_fallbacks.py` | Classify every recorded `semantic_fallback` by its final issue kinds. |
| `replay_fallbacks.py` | Re-validate recorded fallbacks with the current code. |
| `replay_replies.py` | Re-render every recorded tie reply, optionally against an older rule. |

The traced capture harness stays at `../live-semantic-trace-2026-09-23-harness.py`
(many research-log entries cite that path); the blind test is in `../blind/`.

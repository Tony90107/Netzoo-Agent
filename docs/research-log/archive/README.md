# Research data archive

Moved on 2026-09-27 (Log 206) from per-session scratchpads under
`/private/tmp/claude-501/…/<session>/scratchpad/`, which the OS may clear on
reboot. Everything here was recorded by earlier sessions and cannot be
regenerated: live provider traces, replay outputs, corpora and one-off
analysis scripts. `_index.json` lists every file with a one-line description
taken from its metadata (contract, model, repeat, trials, passed), and the
files that were already in the repo under another name.

| Folder | Session | Research-log range | Contents |
| --- | --- | --- | --- |
| `2026-09-23-session/` | `2f62da1d…` | the 2026-09-23 notes (`2026-09-23-*.md`), P1–P4 | families32 / orig8 rounds v3–v6 in both contracts, review replays, analysis scripts |
| `2026-09-26-session/` | `8f6660b9…` | Logs 136–189 | traced rounds (`trace*.json*`), blind-test traces (Log 179), replay outputs (`r1xx_*.json`), replay scripts, candidate patches, pytest logs |
| `2026-09-27-session/` | `cbd53668…` | Logs 190–205 | replay and analysis scripts and old-behaviour emulations (`old*.py`); its live traces are in `docs/research-log/live-semantic-trace-2026-09-27-*.json` |

Files larger than 200 kB are gzip-compressed (`*.json.gz`); they decompress to
the exact original bytes. Load any report, plain or compressed, with
`docs/research-log/tools/traces.py` (`load_report`, `report_paths`, `traced_rows`).

Not archived, on purpose: the routing grids (`g_*.json`, `eg*.json`, `gg*`,
`tg*`, `pg*`, `vg*`, about 840 MB). They are deterministic; regenerate them at
any commit with `docs/research-log/tools/grids.py`. A clone and setup-test
scratchpad (`90787275…`) held no research data.

Scripts in these folders are kept as they ran. Several hard-code the scratchpad
paths of their session; the maintained versions are in `../tools/`.

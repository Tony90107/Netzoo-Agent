# Section 6 judgment repairs — 2026-10-21

Completed the five approved implementation groups on `closed-menu-phase0`. The worktree is preserved; no merge, push or scientific execution was performed.

The user-facing account, case table and limitations are in [第六節錯題修復結果](</Users/chenzhonghan/Documents/LLM AGENT/output/thesis/2026-10-21_第六節錯題修復結果.md>).

Validation:

- `python -m pytest -q tests`: **4,983 passed, 51 skipped**, two dependency deprecation warnings, 103.54 seconds. See `full-tests.log`.
- `python -I -B docs/research-log/judgment-repairs-2026-10-21/replay.py`: 999 archived readings, no errors; labelled core-kind correctness **561 → 577 / 741**, zero previously correct regressions. See `summary.json`, `changes.json`, `regressions.json` and `cases.json`. Input digest: `7cb552ae3456ab3e42583900a653bb7ae96fdc52569420751bd6e24c6628408c`.
- Actual configured-model CLI rounds: **8/12, 10/12, 1/2, 1/1, 1/1**. Each reported case's latest core kind matches its label, across different frozen code versions. This is neither a final-version 12/12 round nor a new blind evaluation. See `live-summary.json`, each round's `live-round.json`, `live-finished.json` and original events.
- The original frozen M01 still misses its doubt; the new live M01 asks the relevant version question. H34's final live refusal cites the sparsify/delta constraint but still lists the HDF5 preference as another unmatched row.
- 28 sessions, 188 model calls, 110,331 micro USD in recorded cost; 162 actual and 26 estimated usage entries. No actual tool execution events.
- `git diff --check` and `git apply --reverse --check implementation.patch` passed. The patch includes both tracked deltas and the new source/test/fixture files; `implementation-manifest.json` pins those 46 files to hashes and the base HEAD.

The public seams remain `build_capability_check`, `decide_core`, checked routing and executor setting binding. Tests exercise omitted/incorrect readings, complete and partial setting phrases, source-verified refusal, necessary-check failures, method output choices, modifier ownership, incompatible input and real secondary results.

Code discovery used Verify-tier graph evidence from parent project `Users-chenzhonghan-Documents-LLM-AGENT`, generation `2026-10-16T10:16:00Z`. The graph excludes `.worktrees`; see `graph-coverage-final.json` and the appendices. Exact-source fallback was used. Persistent full indexing was attempted but the CBM worker refused to start because a pre-coordination/unverified generation was already active; existing daemons were left alone. This is an indexing limitation, not a successful index refresh.

---
存檔說明（Claude，2026-10-21）：這批修改已經拆分，只保留結構性的部分，見 `../judgment-repairs-2026-10-21-review/SPLIT.md`；驗證報告是 `collab/2026-10-21_Codex第六節修復驗證.md`。原始線上 session（`live/`、`verification-02` 到 `-05`）沒有保留：它們用的是已撤回的讀取格式，現在的程式讀不了，結果彙整在 `live-summary.json`。`baseline.json` 和程式碼圖譜工具的輸出可以重新產生，所以也沒有保留。完整程式修改保留在 `implementation.patch`。

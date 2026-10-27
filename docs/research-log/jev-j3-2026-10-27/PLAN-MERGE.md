# Merge jev-combined into main (plan, 2026-10-27, awaiting approval)

User request: plan merging jev-combined into main, with a shared `jev_client.py`, the overlap Jev call moved out of
`build_capability_check`, flags still off, and full checks. Plan first; nothing runs before approval.

## 0. What "main" receives (needs an explicit OK)

- `netzoo-agent/main` is at da39e8ac (the h6 freeze, 91a8c2d9 code). jev-combined (08651594) is a fast-forward of it:
  41 commits. **13 of them are harness-repair (P0–P5, frozen A3+B at 041f0ee9), which has never been merged into
  main.** So this merge also brings harness-repair's behaviour changes into main. These are not behind a flag:
  obligations, two-layer reasons, TaskState, partial, and the replay at 614 kind.
- The remaining 28 commits are the Jev work: guard, steps 1″/3/4, overlap rounds 1-2. All are behind
  `NETZOO_JEV_GUARD` / `NETZOO_JEV_OVERLAP`, default off.
- Not included: misread-detection and round27-links-inputs (withdrawn research; code flag-off). The DRAGON lambda
  crash fix (d9bb15bb on `claude/dragon-lambda-range-745934`, 1 commit off harness-repair) is not included unless
  you say so. If you do, it is cherry-picked first, as its own commit.
- The local `netzoo_agent` checkout (branch evidence-contract-grounding; other sessions edit it) is not touched.
  Only the remote `main` moves, fast-forward only (no merge commit, no force).

## 1. Refactor (new worktree `.worktrees/netzoo-jev-merge`, branch `jev-merge` from 08651594)

1. **`netzoo_agent_core/jev_client.py`**, a leaf module that imports nothing from `graph/` or `interpretation/`.
   - `decide(state, questions, *, timeout)`: key from `OPENROUTER_API_KEY`, URL `NETZOO_JEV_URL` or the default, and a
     typed error on no key or HTTP failure.
   - `jev_guard_call._decide` and `jev_overlap._decide` both become calls to it (the duplicate removed).
   - Behaviour unchanged: same body, same timeout values, kept per module.
2. **Move the overlap Jev call out of `build_capability_check`**, by dependency injection:
   - The builder gains an optional parameter `overlap_reader: Callable[[task, quote], bool] | None = None`. With None,
     the builder is pure again: no I/O and no overlap read, which is the same as the flag off.
   - `interpretation/jev_overlap.py` keeps only pure parts: the question, criteria, threshold, and the rule from a
     read's probabilities to `doubted`.
   - New `graph/jev_overlap_call.py` holds the I/O: the mode flag, the per-process memo, the offline cache
     (`NETZOO_JEV_OVERLAP_CACHE`) and `take_reads`. It builds the reader passed in by `router_invocation.py`
     (both builder calls).
   - `required_check_budget.py` passes no reader. It is a size estimate and should not call Jev. Today it can
     trigger a read; with the memo, no extra network call happens. Say so in the commit.
3. No other change: same questions, thresholds, flags, events and replies.

## 2. Checks (all must pass before main moves)

- **M0, tests:** full suite in a clean environment (`env -i`): 0 failures. There are 5064 baseline tests plus the
  new ones: the jev_client leaf rule, the builder with no reader makes no call, and a reader is used when passed.
- **M1, flag off = frozen:** the harness replay changes 0 of 1388 calls vs `replay-frozen.json`.
- **M2, flag on = before the refactor, offline:** with the Jev cache files from jev-overlap
  (`jev-cache*.json`), a replay run with both flags on gives the same calls as before.
  - The harness replay with an injected cached reader: 0 changes vs jev-overlap's `replay-on-r2.json`.
  - `replay_jsets.py`: 0 changes vs `jsets-on-r2.json`.
  - The reasons check: the same lines as `reasons-r2.json`.

  `replay_full.py` calls the builder directly, so this check gets a small adapter that passes the cached reader;
  the research script itself is not edited.
- **M3, boundaries:** `test_agent_module_boundaries.py` passes; `jev_client.py` imports only the standard library.
- **M4, live smoke (both flags on, gpt-4o-mini, 3 sessions, about US$0.02):** 3 seen j3 items, one each for the
  guard, the overlap path and a plain DO. The check is wiring only: every expected `core.jev_*` event is written,
  no error, and the code is unchanged during the run. Calls are not scored.

Any failure: stop and report; main does not move.

## 3. Landing

- Commit on `jev-merge`, push the branch, then fast-forward `netzoo-agent/main` to it:
  `git push netzoo-agent jev-merge:main`, refused unless it is a fast-forward.
- Afterwards main runs harness-repair's frozen behaviour with both Jev flags off. Turning Jev on is a separate
  decision: `NETZOO_JEV_GUARD=on` / `NETZOO_JEV_OVERLAP=on` in the `.env` of the tree that runs the app.

## 4. Budget and time

- Model spend: about US$0.02 (M4 only; M2 uses cached Jev reads).
- Time: about 45 minutes of refactor and tests, plus about 10 minutes of replays.

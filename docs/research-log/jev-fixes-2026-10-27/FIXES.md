# Two fixes to step 1″ (declared 2026-10-27, before code)

User request (2026-10-27): "an unplaced typed violation still asks the confirm (contract line, no user quote); a
jev_condition confirm binds yes/no in code instead of Jev's answer read. Declare gates, test offline on the recorded
j2/j3 replies, no live run." Found by the jev-overlap session in j3 arm G: R08 (unplaced), R02 / R28 (answer read
below 0.7). All three ended DO guidance (run_allowed False), a wrong DO.

Branch `jev-merge` (= main 4df817b6). Flags unchanged (off by default).

## Fix A — an unplaced violation still asks

When every workflow of a DO is ruled out by a typed field (Jev data / same_samples >= 0.7), but the breaking-sentence
pick finds no sentence, `conditioned_core` asks the confirm anyway. There is no user quote. The question names the
typed fact itself, from the closed menu's own description: "is the data you will use <DATA_CRITERIA text>?", or, for
the same-samples line, "were the two layers measured on different samples or individuals?". The contract line is
quoted as before. A question gives no reason, so nothing here can be a wrong reason.

Asked at most once per task: no second `jev:condition` question while one is pending or answered.

## Fix B — the confirm's answer binds in code

A `jev:condition` question becomes a yes/no question (`_pending`: `yes_no`). The existing `bind_answers` binds a
reply whose first word is in `_YES` / `_NO`, when it is the only open question. On the answer turn:
- bound **yes** (the user confirms the ruled-out fact) on a DO → DECLINE `jev_answer`, with the same two-quote
  reason (the user's answer + the contract line);
- bound **no** → the call as it came;
- not bound → the call as it came. There is no Jev answer read for `jev:condition` any more (`asked_contract_question`
  skips it). Step 3's Jev read stays for `jev_fact` questions only.

The confirm question ends with "(yes or no)", so a reply can be bound.

## Offline test (`fixes_offline.py`, no model call)

Data: the recorded j2 and j3 items (seen), and the recorded `core.jev_condition` events of arms j2g / j3g.
- **B1 (recall):** every T item's `reply_confirm` (j2 10, j3 6), as the answer to the new confirm, binds `yes` in
  code: >= 14 of 16.
- **B2 (precision, hard):** replies that are not confirmations do not bind `yes`. These are every item's
  `reply_restate`, the GT `reply_membership`, and the V `reply_result`, each as the answer to a confirm: <= 1 of all.
  `reply_fact` is reported apart, since U items are never asked a condition.
- **B3:** with Fix B, the recorded confirm sessions (j2g Q12 Q33 Q46 Q48, j3g R02 R05 R28) end DECLINE `jev_answer`
  where gold is DECLINE. This is simulated from each recorded turn-2 call and the item's reply: >= 6 of 7. No
  simulated decline on a gold-DO final.
- **A1:** every recorded unplaced violation (j2g / j3g events, plus the 124-call offline set
  `conditions-offline-typed.json`) now becomes an ask. Of those on gold-DO calls: 0 (hard).
- **A2:** the unplaced question text contains no user quote, and the contract line verbatim.

Plus unit tests, the full suite in a clean env with 0 new failures, and the flag-off replay at 0 of 1388 changed.
Any hard gate failing → the fix is not kept, and that is reported.

## Result (FIXES-OFFLINE.txt) — all gates pass

- B1 16/16 confirm replies bind `yes` in code.
- B2 0 of 118 non-confirm replies bind `yes` (reply_fact, reported apart: yes 3 / no 3 / unbound 12).
- B3 7/7 recorded confirm sessions end DECLINE, the gold; Q46 Q48 R02 R28 move DO → DECLINE; no wrong decline.
- A1 6/6 unplaced violations now ask, none on a gold-DO call. 4 of the 6 are turn-2 re-checks that the
  once-per-task rule skips live, so the real new asks are j2 Q31 and j3 R08.
- A2 pass.

## Also restored on this branch (found while checking)

Switching the app folder to main dropped 3 commits that only `evidence-contract-grounding` had:
- 0e27f6ef: desktop turn activity with web sources, and the chat/options splitter (frontend +
  `graph/execution.py`, `graph/source_refs.py`);
- 1c2e66ac: the recorded sessions the replays read;
- dfbcbfd8: specs.

They were cherry-picked here. The two 10-19 spec conflicts keep main's newer text. `execution.py`'s new lookup
expression was compacted to stay under the module's 230-line limit (229).

Checks: tests 5075 passed, 0 failed (clean env); desktop vitest 121/121; the flag-off replay is back to 1388 readings,
0 changed vs replay-frozen.json.

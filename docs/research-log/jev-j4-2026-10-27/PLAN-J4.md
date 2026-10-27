# Fresh sealed set j4: the merged system, all three Jev layers (plan, 2026-10-27)

User request (2026-10-27): prepare j4 with a blind author plus review, 48 items, sealed, and declare gates; two
arms: all three flags off vs all on; tell the user the cost before running. Nothing runs before the user says go.

## 0. Code under test (no change)

- main **ce8be114**: jev-guard (with the R08 unplaced-violation and jev:condition yes/no binding fixes), jev-overlap
  (rounds 1-2), jev-forms (rounds 1-2), and the compose flag lines. Frozen as is; the runner refuses to start if
  `scripts`, `workflows`, `prompts` or `AGENTS.md` differ from ce8be114.
- Worktree `.worktrees/netzoo-j4` (branch `j4-eval`); records under `docs/research-log/jev-j4-2026-10-27/`.
- Arm F: `NETZOO_JEV_GUARD`, `NETZOO_JEV_OVERLAP`, `NETZOO_JEV_FORMS` all `off` (the system without Jev).
  Arm G: all three `on`. The runner sets them per arm over the app `.env`, and removes any offline Jev cache variable.
- Already checked on this code (jev-forms round 2): flags-off harness replay 0 of 1388 vs replay-frozen.json; test suite
  5085 passed, 1 env-dependent failure.

## 1. The set j4 (48 items, ids S01-S48)

The set is written blind by a subagent that reads only `workflows/*.yaml` and `workflow_registry.py`
(`j4/AUTHOR-BRIEF.md`). A second blind subagent then reviews every gold (`j4/REVIEW-BRIEF.md`). Everything is
sealed with SHA256 before any run, and I read only counts.

| group | n | gold (turn 1) | tests |
|---|---|---|---|
| GT grouping, no overlap asked | 5 | DO | the several_groups misread (trap) |
| GO overlap asked | 4 | DECLINE | control |
| FT time points, no dynamics asked | 4 | DO | the time_model misread (trap) |
| FD dynamics asked | 3 | DECLINE | control |
| FSN spatial data, no neighbours asked | 2 | DO | the spatial misread (trap) |
| FS neighbours asked | 2 | DECLINE | control |
| FN existing regulator-gene network, communities | 4 | DO | the input_network misread (trap) |
| FG existing network of another kind, communities | 2 | DECLINE | control |
| T data-type trap | 5 | DECLINE | guard step 1'' |
| TC data-type control | 4 | DO | guard false alarms |
| U one unsure fact | 6 | ASK | J-ask |
| N result in plain words | 4 | DO 3 / DECLINE 1 | linking |
| V no result named | 3 | CLARIFY | links on vague requests |

Replies: `reply_restate` (all), `reply_form` (GT FT FSN FN: natural words for the form the request already implies),
`reply_confirm` (T), `reply_fact` + `fact_keywords` + `final_after_fact` (U), `reply_result` + `final_after_result` (V).

## 2. Runs (gpt-4o-mini, two arms, up to 3 turns; `run_j4.py`, adapted from run_j3.py)

Reply rule:
- After an ASK, use the first that applies:
  - `reply_fact`, when the question names the fact (a Jev question: also its quoted sentence);
  - `reply_form`, when the question is a form question (group_membership, time_model, spatial, input_network);
  - `reply_confirm`;
  - `reply_restate`.
- After a CLARIFY: `reply_result`, else `reply_restate`.
- After anything else, the conversation ends.

Scored by `score_j4.py`: the final call against the final gold, and each final reply's text for form reasons.

## 3. Gates (declared now, not loosened)

Overall, arm G vs arm F:
- **O1:** final right G >= F + 4.
- **O2:** FA, FR and MA each not higher in G.
- **O3:** 0 finals that are a Jev-made DECLINE (basis `jev_*`) where the final gold is not DECLINE.
- **O4 (reasons):** finals saying a form reason (overlap, time, spatial) that the item did not ask for: G <= 1, and
  G <= F.

Per layer (arm G):
- **C1 (hard):** all 11 controls (GO, FD, FS, FG) end DECLINE and are never asked a form question.
- **C2:** of the form-trap items (GT, FT, FSN, FN) that arm F gets wrong, >= 2/3 are right in G or still waiting on a
  question at turn 3 (reported apart).
- **S0:** J-ask false alarms on gold-DO items (GT, FT, FSN, FN, TC, N DO) <= 2.
- **S1:** step 1'' confirms >= half of the T items whose call was DO; on TC <= 1.
- **S4:** `jev_link` on V <= 1.

A failed overall gate means the merged system shows no fresh-set gain. A failed layer gate is reported against that
layer, and the user decides. Post-hoc analysis is labelled as such.

## 4. Budget

- Authoring and review subagents: no API spend.
- j3 (same shape, 96 conversations, up to 3 turns) cost US$0.53. j4: about US$0.55-0.65 with Jev under US$0.03.
- **Cap US$1.30** for both arms, enforced by the runner; arm F first.
- About 30 minutes of runs.

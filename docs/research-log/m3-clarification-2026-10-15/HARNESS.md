# M3 evaluation harness

The scripts implement a 120-item primary round plus 30 deterministic repeats (seed 1510), totaling 150 sessions. Importing a script does not read `heldout.json`. The synthetic harness tests never read the held-out dataset. Only repetition 1 contributes to primary metrics; repetition 2 measures exact agreement of requirement-label lists.

Run from the repository root, using `/opt/anaconda3/bin/python`. Candidate defaults to `/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-m3-candidate`. `freeze-code.json` must contain a full `base_sha` and a `files` object mapping whitelisted repository-relative changed/new source files to SHA256 hashes. HEAD, modifications outside the whitelist, and every whitelisted hash are checked before and after each job. The manifest hash and dataset hash are pinned in `round.json`. Candidate instrumentation wraps `_reply_card` only to preserve its returned value; all CLI behavior still runs through `scripts/netzoo_agent.py`.

```sh
/opt/anaconda3/bin/python -m unittest discover -s docs/research-log/m3-clarification-2026-10-15 -p test_harness.py -v
/opt/anaconda3/bin/python docs/research-log/m3-clarification-2026-10-15/run_live.py m3 --code-manifest docs/research-log/m3-clarification-2026-10-15/freeze-code.json
/opt/anaconda3/bin/python docs/research-log/m3-clarification-2026-10-15/run_live.py m3 --code-manifest docs/research-log/m3-clarification-2026-10-15/freeze-code.json --resume-unstarted
/opt/anaconda3/bin/python docs/research-log/m3-clarification-2026-10-15/collect.py m3
/opt/anaconda3/bin/python docs/research-log/m3-clarification-2026-10-15/analyze.py m3 spotcheck
/opt/anaconda3/bin/python docs/research-log/m3-clarification-2026-10-15/analyze.py m3 score
```

Run only after source and gold freeze and explicit authorization for live execution. Provider credentials are read from the environment, or the original checkout's `.env` with python-dotenv, without shell evaluation or variable interpolation. The runner never prints credentials. The live runner needs network access. It defaults to five workers and 900 seconds per turn. Explicit job selection is `run_live.py m3 ITEM:1 ITEM:2 --code-manifest ...`; it cannot combine with `--resume-unstarted`. Every existing job directory or session is rejected. Interrupted/failed jobs remain evidence and require an explicitly documented fresh-tag rerun; they are never silently retried or overwritten.

Each turn uses `--session` initially and `--resume` subsequently, always with `--keep-session`. A turn directory contains complete stdout, stderr, captured cards, session JSON, trace JSONL, and a manifest with exit status, request, mode, timestamps, and file hashes. The next turn starts only after the preceding evidence was saved. No model call is made by collection, scoring, or tests.

Collection validates every turn's successful exit, file hashes, nonempty trace, session identity, and retained user context. This applies equally to guidance and run turns. **This is capture integrity validation, not a claim of full deterministic replay.** A timeout, missing artifact, absent resumed context, or altered capture blocks a valid score. Captured cards may be empty when the CLI produces no card, especially while requesting input. The collector preserves actual stdout/stderr including workflow-selection lines. Since separate streams are captured separately, their cross-stream timing/interleaving is not reconstructed.

Outputs in `live/m3/`:

- `structure.json`: private analysis evidence, including selected workflow/action, session plan steps, `plan.created` trace payloads with actual input paths/parameters, gate events, requirement matches, model coverage and errors.
- `blind-key.json`: private mapping from random blind codes to sessions and gold requirements. Never give it to blind labelers.
- `packet-01.md` through `packet-06.md`: 25 sessions each, shuffled with seed 1510. Only requests, requirement words, complete visible output and cards are included. No gold, expectation, item/family, arm, or code version is added. Session identity and checkout path are replaced, ANSI escapes stripped, environment credentials and common token forms redacted. Raw artifacts remain private.
- `labels-A.json`: merged blind labels following LABELING.md.
- `to-review.json`: mandatory primary-adjudication codes.
- `labels-checked.json`: reviewed labels with a nonempty `reason`; add boolean `right_question` for every ask-class session and boolean `bad_gate` for every flagged gate candidate.
- `score.json`: metrics, Wilson intervals, frozen thresholds, grade, weighted score, repeat agreement, and acceptance result. Existing outputs are not overwritten.

Primary review covers every mismatch, unresolved/unknown label, provider error, contradiction, ask-class session, and gate candidate, plus a seeded 10% of all others. Ask correctness is decided only against the frozen deciding fact, after blind labels exist. A session-level `right_question` applies to all its ask-class requirements; use true only if every deciding fact was asked. Gate candidates include selected run actions with negative/ask gold or without an `agrees` verdict; primary review distinguishes a correctly held run from an actual constraint violation and records the evidence in `reason`.

Requirement-read evidence requires a result-kind check row with a quote found verbatim in the supplied requests, overlapping at least half the gold words. Mere background/facts and invented quotes do not count. Both quotes are checked against all original user turns; the exact matching quotes are saved for inspection.

Negative cost: NOT_GIVEN 0, undecided (UNCONFIRMED/ASKED/OMITTED) 1, PARTLY 2, GIVEN* 3. Positive cost: GIVEN* 0, NOT_GIVEN 2, all others 1. Score is `100 * (0.6 * (1 - neg_cost / (3 * neg_n)) + 0.4 * (1 - pos_cost / (2 * pos_n)))`. Ask requirements are excluded from both denominators. Thresholds: FAR including PARTLY ≤3%; FRR ≤5%; positive GIVEN* ≥95%; correct deciding question ≥90%; verified requirement read ≥95%; Nemotron capability-check success coverage ≥95%; provider-error session rate ≤5%; adjudicated bad gates 0. Missing metric denominators do not pass. Grade A/B/C/D/F follows the prior acceptance thresholds; acceptance additionally requires every listed threshold.

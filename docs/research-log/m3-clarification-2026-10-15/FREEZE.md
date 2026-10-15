# M3 freeze (2026-10-15, before round m3)

Frozen before any live output exists. Gold, thresholds and scoring are in HARNESS.md / LABELING.md and are not changed
after this point.

## Code

- Candidate: `.worktrees/netzoo-m3-candidate` (a separate clone at base `4c3cd7b`), 14 whitelisted files,
  hashes in `freeze-code.json`. The runner checks HEAD, the whitelist and every hash before and after each job.
- Codex: the user's four gaps (own-sentence check failure, enum values, boolean values, mixed `=` replies) and PLAN
  items 1-2 (deciding facts, second-opinion limits).
- Review fixes added before the freeze (Claude, from reading the code, not from any held-out output):
  1. `engine/recheck.py`: the gap-4 fix stopped accepting a pasted path with spaces (`/Users/.../LLM AGENT/x.tsv`,
     a terminal-dropped `LLM\ AGENT`), which would have rechecked the run instead of answering the wizard.
  2. `workflow_conditions.boolean_value`: the gap-3 fix read only true/false/off/"do not X"; "without", "don't",
     "turned off" were unresolved and refused the workflow. Negation words now decide; a setting stated with no
     value is read from its own words ("without sparsification" is off, "sparsify" is on).
  3. `method_conditions.unbound_settings` + `router_invocation._on_run_verdict`: an approved run must carry every
     stated setting of its workflow. A stated value the run binding cannot read (a value without a number, a name or
     list control such as SAMBAR linkage) makes those words unread, so the run is held (`unread`). This closes the
     gap-2 symptom ("accepted, verified settings {}") for every control type, not only enums.
- Tests: 3765 passed, 51 skipped in the candidate (4 new regressions for the fixes above).

## Known, not fixed before the round

- Gap 2's three states are two in effect: a value that names no allowed choice ("half", but also "float32") is
  treated as not usable as asked (workflow offered with its own settings, run held). Safe for false accepts; can cost
  a false refusal for a synonym. A separate "unresolved, ask" state needs a new requirement status and renderer.
- Numeric controls with a non-numeric value are still accepted in guidance; only the run is held (fix 3).

## Round

- Dataset `heldout.json` sha256 `b991c938...a8f7fb` (equals AUTHOR.md). 120 items + 30 repeats (seed 1510) = 150
  sessions, 160 turns. Workers 5, 900 s per turn, dry-run planning only.
- Models: routing/semantic gpt-4o-mini; capability check nemotron-3-super-120b:free. Before the round: free quota
  1000/1000 left today, paid balance about US$4.06.
- Labelling: one blind labeller per packet plus my spot check (memory rule since 2026-10-11); primary review as in
  HARNESS.md. Gold review: one independent reviewer of `heldout.json` against the workflow YAMLs, without outputs.

## Harness deviations during the round

- `collect.py` accepted only exit 0. A non-interactive turn that stops at the input wizard exits 2 after printing the
  question and "Run the command again with --resume ..." (`cli/conversation.py`); that is a complete answer. Collection
  now accepts exit 2 only with that line on stdout. `run_live.py` still stops a job after a non-zero turn, so a K item
  whose first turn stops at the wizard would miss its second turn; none of the ten primary K items did (all first
  turns exited 0). Changed after K06/K09/K10 recorded exit 2 on their final turn; no code or gold changed.

# 2026-09-24 residual regression triage

## Scope

This follow-up checks the supplied tumour-RNA advisory transcript, the open
granularity consistency repair, and seven failures reported by a mixed offline
regression run. It used saved traces and local fixtures only. No live provider
was called, no workflow ran, and no production semantic-contract default changed.

## User-facing reproduction

The supplied CLI output now identifies only **LIONESS-PANDA** in the workflow
progress line and recommends it directly for patient-specific TF-to-gene
networks. It lists expression, motif, and PPI inputs; states that LIONESS-PANDA
produces aggregate and per-sample outputs; and says that no files were inspected
or analysis run. The matching route retains its PANDA dependency metadata, but
the advisory view presents the terminal workflow rather than a misleading
aggregate-plus-sample-specific pair.

The exact prompt also has an offline production-path regression through
`respond()`. It asserts the LIONESS-PANDA recommendation, `no_tool`, no execution,
and no tool results.

## Granularity consistency

The saved `gran-mirna-unstated-control` state remains covered at three layers:

- Claims interpretation completes the open choice into grounded `aggregate`
  and `sample_specific` hypotheses when the request literally names both.
- Decision assembly keeps `requested_outcome.granularity` at `unknown` while
  that choice is open and asks the aggregate-versus-sample-specific question.
- The evaluator rejects a still-ambiguous decision whose requested outcome has
  committed to `sample_specific`, and separately rejects hypotheses that omit
  either alternative.

These checks replay deterministic stages and historical responses. They do not
measure live model accuracy on unseen prompts.

## Residual failure triage

The seven failures in the prior mixed run did not reveal seven new production
defects. Their fixtures and assertions had fallen out of step with the current
contracts:

1. A miRNA role was paired with the composite TF-activity artifact, whose
   ontology excludes miRNA; the restoration correctly selected the compatible
   regulatory-network artifact. The preservation control now uses TF roles,
   for which the composite artifact legitimately retains sample rows.
2. A full input list contained output artifacts unsupported as current inputs.
   The test now checks that unwitnessed entries are removed, current expression
   input is retained, and schema validation refuses a fifth item.
3. An aggregate-evidence test accidentally supplied an expression matrix from
   a historical goal as a current outcome input. Its fixture now isolates the
   granularity evidence under test.
4. A role-clearing test included an unmentioned mutation input. Its fixture now
   isolates role clearing.
5. The granularity witness supplied a longer exact quote containing the
   granularity phrase and its network context. The test now asserts that exact
   span rather than requiring a shorter paraphrase.
6. A claim-repair test expected reviewer feedback after explicit role
   restoration had already corrected the artifact and removed all validation
   issues. It now asserts the correction and that no unnecessary repair
   feedback is emitted; remaining-conflict feedback is covered by a separate
   test.
7. The real-SDK test requires `langchain-openai`, which is absent from this
   environment but listed in the acceptance dependency set. It now skips when
   that optional test dependency is unavailable and will run where installed.

## Verification

- Focused offline suite: **379 passed, 1 skipped**. The skipped test is the
  real-SDK wire test because `langchain_openai` is unavailable here.
- Ruff: passed for the affected source and test files.
- `git diff --check`: passed.
- Pytest emitted one existing `pytz` deprecation warning.
- No provider cost was incurred.

The repository still contains multiple pre-existing uncommitted changes and
saved trace files. They were preserved; this report does not attribute all
worktree changes to this follow-up.

## Limits

The prompt-level sample-specific result is a deterministic offline regression,
not a new live trial. The bounded text witnesses are not a general language
parser. The unavailable SDK wire test remains unverified in this environment.
Claims remains experimental and has not been promoted to the production
default. The separate `prompt_seq` desktop issue remains outside this repair.

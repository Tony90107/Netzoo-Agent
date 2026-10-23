# Harness repair P4: input and long-term memory freshness (2026-10-23, declared before work starts)

Written from spec §9 and plan P4; acceptance is A16–A19. It is declared before any P4 code; changing it needs the user's decision, recorded here.

## Current state (from exploration, all at `fe265cff`)

- **Episodes record only `inputs: {field: path}`.** There is no size, hash, validator version or contract hash, and no schema version. Pydantic's default `extra="ignore"` applies, so an old file loads fine without new fields.
- **Episodes are written** by `consolidate_memory` (completed, dry_run, failed). Only `completed` episodes are reused (`episode_reuse`), which checks:
  - same workflow;
  - required fields present;
  - the file exists.

  Some workflows re-run the current checks; others are treated as `ok = True`.
- **Reused paths are validated again at planning time.** Every bound input goes through `validate_workflow_inputs`, which fails closed (every run action has a validator); reused inputs are marked `discovered`, which forces confirmation.

  But the reuse reason always reads "Reused validated inputs from successful episode …", which still claims validation when the file has changed since, or when a workflow got no check here.
- **Preview → execute.** After the user confirms a dry-run preview (`y` or `/execute`), the graph re-plans on the preview's text: input checks run again, and the executor checks again itself.

  **Nothing compares the files with what the preview showed.** A file whose content changed but still passes the checks runs as is, and the user is not told. The server's `plan_hash` only checks that the client is looking at the in-memory preview.
- **The last gate is `graph/execution.py::execute_tool`** (`_unapproved_run`: approval, plan digest, run approval). After it, subprocess workflows re-open the same paths themselves, with no snapshot.
- **Hashes.** `policy_hash` is one global sha256 (AGENTS.md plus every workflow YAML). There is no per-workflow contract hash and no validator version; no file-content hash is computed in the core package.

## What P4 does (minimal version)

1. **`InputRevision`** (`contracts/memory.py`, versioned) and **`data/artifact_revision.py`**:
   - canonical path (resolved absolute path), size, mtime_ns, content sha256 (streamed in 1 MiB chunks), validated_at;
   - `validator`: the action name, plus a sha256 of the validator's module source;
   - `contract_hash`: sha256 of that workflow's parsed contract (`WorkflowPolicySpec`);
   - `policy_hash`.

   `freshness(old, now)` returns `unchanged`, `changed` (content), `rules_changed` (validator, contract or policy changed), `missing`, or `unverified` (no fingerprint). It relies only on sha256 comparison: size and mtime can show that a file "definitely changed", never that it "did not change".
2. **Where fingerprints are computed: `execute_tool`.** Right before a step runs (execute or dry run), it fingerprints that step's input files (required inputs plus optional input files) and returns `input_revisions` keyed by canonical path. This is only done for files this turn validated and is about to use; nothing is re-scanned in bulk.
3. **Episodes** (additive): `Episode.input_revisions: {field: InputRevision}`, default empty. `consolidate_memory` passes this turn's fingerprints to `EpisodeStore.record`; the inspect view (`compact_episode_payload`) shows each field's short hash and its check time. Retention, capacity, deletion, `--forget-memory` and private storage are unchanged; the new field lives in the same file.
4. **Reuse** (`episode_reuse`): candidates and conditions are unchanged. Explicit user paths still take priority; missing files are still not offered; dry_run and failed episodes are still not reused. The reason now states, per field:
   - `unchanged`: the content matches that run (sha256), and it is checked again now with the current rules;
   - `changed` or `rules_changed`: what changed, so the old check does not count, and it is checked again now;
   - `unverified` (an old episode): that run recorded no fingerprint, and it is checked again now.

   For workflows with no check in this module, the reason does not say "validated"; the planning check still runs. These are honest statements about what was checked, not new permissions.
5. **Preview → execute (A17)**:
   - the dry-run turn's `input_revisions` are kept in `PreviewState`;
   - after the user confirms, the machine sends them into the execute turn as `previewed_inputs`;
   - in execute mode, `execute_tool` compares each input file of this step with the preview. If any is changed, missing, or a different file the preview never showed, nothing runs. The refusal names the file and what changed, and asks for a new preview and confirmation.

   Without a preview (execute mode, no dry run) there is nothing to compare, and behaviour is unchanged.
6. **TOCTOU**: the guarantee covers only "the file at the execute gate is the one in the preview". A subprocess workflow re-opens the path after the gate, and nothing is copied or snapshotted, so a concurrent change after the gate cannot be detected. This is written into the docstring and the result record, never claimed as eliminated.

**Not done** (later):

- a typed parameter snapshot (`parameters` stays a name list; spec: only "if research needs reproduction");
- fine-grained reuse when an unrelated policy changes (any policy_hash change counts as `rules_changed`);
- validator versioning beyond module granularity (changes in helper modules the validator calls are not seen);
- re-checking a resumed `needs_confirmation` plan (it is still re-planned and checked at confirmation time, but not compared with the old prompt).

## Gates

1. All of `tests/` passes with no new skips; the plan's P4 commands pass with `--fail-on-skip`.
2. B2 replay P3 → P4 has 0 call changes (routing is untouched).
3. New tests:
   - `tests/test_episode_freshness.py`:
     - A16: same path, different content (including restoring size and mtime with the same size, still detected by sha256); contract, validator or policy change → `rules_changed`;
     - A19: an old episode without fingerprints keeps its candidate and is labelled unverified;
     - a valid reuse still succeeds;
     - an old episode JSON loads;
     - inspect shows the new field;
     - dry_run and failed episodes are not reused.
   - `tests/test_plan_evidence_revision.py`:
     - A17: unchanged → runs; content changed (same size and mtime), deleted, or a different path → refused with a reason naming the file;
     - without a preview, no comparison;
     - the machine keeps the preview's fingerprints and sends them on confirmation.
   - A18: the existing authorization tests (`test_operation_authorization` and others) still pass.
4. Hash cost measured on the project's data files (MB/s and the overhead per preview/execution), reported in P4.md.
5. **No live run**: P4 does not change model reads or the judgment.

# Registry-wide scientific guidance routing

Scope: all 12 workflows currently registered by `OUTPUT_CAPABILITIES`. This
does not claim support for every package in netZooPy or correctness for every
possible wording/model. Guidance never grants execution authority.

## Repair

- Review a schema-valid explanation that omitted its scientific subject once,
  using the existing two-attempt limit. Both semantic contracts use the repair.
- Recover the discussed artifact and scale without choosing a workflow by
  request keywords. Current input claims require model adjudication, original
  quotes, and the unchanged input-integrity/evidence validators.
- Match typed scientific dimensions against the registry. Compare eligible
  candidates by study conditions, mathematical premises, required inputs and
  output boundaries. Show one advisory `(recommend)` when justified; retain
  alternatives and require the user's choice before analysis.
- Explain a required modeling philosophy when no compatible registered method
  implements it. Bayesian gene co-expression cannot be substituted for a
  posterior model of TF-binding-prior reliability.
- Answer the typed scientific question before listing candidates. A shared
  explanation links the requested result and any quoted study condition to the
  selected method's mechanism across all registered workflows. When a model's
  grounded explanation agrees with the condition-selected action, retain its
  question-specific rationale without letting it change the selected action.
- Supply mathematical explanations for every registered method family.
  Capability-gap answers start with the scientific principle, limit related
  approaches to three base methods, and avoid repeating the clarification in
  the terminal next-step prompt. Related methods are ranked by typed output,
  regulator scope, scale and input needs. A uniquely leading alternative may
  receive a **conditional** `(recommend)` if the user relaxes the unmet modeling
  requirement. Tied methods are shown as tied and require the user's choice;
  catalog order never becomes evidence of a scientific winner.
- Preserve original-language quotes as private grounding evidence while
  paraphrasing non-English request excerpts in English in the public advice.
  This also applies to the sample-count clarification note.

## Evidence and limits

`tests/test_all_workflow_guidance.py` covers every registered workflow's typed
matching and presentation, every registered output family on both semantic
contracts, quoted current-input recovery, rejection of noncurrent/fabricated
inputs, and the original capability-gap presentation issue. The same generic
alternative-ranking path is tested against the declared outputs of all 12
workflows, including bundled outputs such as GIRAFFE and downstream results
such as SAMBAR patient clusters. Reordering tied candidate inputs must not
invent a winner. Scripted provider
replies verify the harness, **not raw-model accuracy**.

`cases.json` contains 30 raw-language cases: one English and one Chinese prompt
per workflow without naming that workflow, the three original research
questions, two negative controls, and a candidate-comparison question. Expected
results are independent assertions and never enter model messages.

The new 30-case live suite has **not run**. Sending these additional prompts to
OpenRouter requires the user's pending authorization; the earlier approval was
for four specific questions. The prior four-question report remains in
`../scientific_guidance_recovery_2026_09_27/acceptance_report.json` and is not
registry-wide live evidence for the final code.

The previously approved `original-noisy-prior` question was rerun after the
method-comparison repair. The production router and response path passed the
case with a Bayesian-prior-reliability gap, PANDA/OTTER conditional comparison,
English-only output and no execution. It answers how contradictory evidence
could lower edge support, explains why estimating source reliability needs an
identifiable model, and distinguishes an output/scope tie from equal robustness.
PUMA and unrelated joint-output methods are absent when their scope was not
requested. The result is saved in `latest_noisy_prior_validation.json`. This
single case does not validate raw-model routing across all workflows.

`run_acceptance.py` defaults to corpus validation with no API calls. After
authorization, `--live` uses the configured credential and
`openai/gpt-4o-mini`, saves decisions/answers/events/usage locally, and evaluates
artifact, scale, candidates, recommendation marker, missing capabilities and
execution authority, including English-only answers for Chinese prompts. It
invokes neither Planner nor Executor. `--case ID` can
limit a permitted rerun. Full-test output is in `pytest_final.txt`.

The code graph remains at the September 21 generation. A persistent full
rebuild was attempted, but the index worker rejected an active unverified
pre-coordination writer generation. Relevant changed/new files were inspected
directly; no index locks, shared workers or user processes were removed.

# Registry-wide research choices — 2026-09-29

> Follow-up: the single-candidate/duplicate-CONDOR bug and conversational presentation are addressed in [the follow-up report](../research_choices_followup_2026_09_29/README.md). The live captures here are historical; replay results and the example answer now use the current renderer.

This change preserves the user's biological hypotheses before selecting a workflow. It applies to all 12 registered scientific workflows. Two hypotheses sharing a downstream endpoint (for example patient subtyping) remain separate research choices. Unclear goals receive conditional alternatives and a final choice question. Unknown or unsupported methods are described as capability gaps, never replaced by an incompatible tool just to produce a second option.

The model extracts quoted scientific alternatives, quantities to estimate, scope, regulators and estimator constraints. Python matches these against registry capabilities. Input requirements, algorithm explanations and outputs are rendered from the existing workflow specifications; available inputs are not assumed to have been inspected. An explicitly requested downstream endpoint needs its own source quotation. A failed comparison cannot fall back to choosing a single tool. No patient analyses were executed.

## Evidence

- Full suite: **2,726 passed, 35 skipped**. The skipped integration/container tests were not executed. Two existing dependency deprecation warnings remain.
- New regression module: **50 tests**, including rendering every registered workflow, scientific quantity-to-method matching, unsupported assumptions, three hypotheses, evidence validation, clinical-target leakage, unavailable providers and execution/budget boundaries.
- Live model: **8/8** cases passed the per-hypothesis scientific check in the final recorded run, using `openai/gpt-4o-mini`, temperature 0. This is one bounded synthetic test set, not a general accuracy estimate. Earlier iterations exposed wrong mappings and invented downstream goals; those runs were used for debugging and are not counted as passing evidence.
- Offline replay against the final validator/renderer: **8/8**. Replay tests deterministic processing of captured model arguments; it is not another live model run.
- All changes pass Ruff checks and `git diff --check`.

| Scientific alternatives | Expected workflows retained |
| --- | --- |
| Mutation accumulation / regulatory rewiring, Chinese and English | SAMBAR / PANDA → LIONESS-PANDA + external patient clustering |
| TF regulation / miRNA regulation | PANDA, OTTER or LIONESS-PANDA / PUMA or LIONESS-PUMA, depending on scope |
| TF activity / each patient's wiring | GIRAFFE / LIONESS-PANDA |
| Covariate-associated / individual coexpression | COBRA / LIONESS-COEXPRESSION and BONOBO |
| Cross-omic associations / expression-only coexpression | DRAGON / LIONESS-COEXPRESSION |
| Bipartite communities / covariate-associated coexpression | CONDOR / COBRA |
| Unclear: tissue network / patient networks / TF activity | PANDA and OTTER / LIONESS-PANDA / GIRAFFE |

The scientific check validates each hypothesis group separately: required and allowed workflows, target artifact, hypothesis count, comparison details, the final question and the absence of a selected-path recommendation. A tool name appearing anywhere in an answer is insufficient to pass.

## Reproduce

Use a Python environment with the repository's dependencies:

```sh
python manual_tests/research_choices_2026_09_29/run_live.py
python manual_tests/research_choices_2026_09_29/run_live.py --replay
python -m pytest tests -q
```

The first command checks saved live results, and the second replays saved responses offline. A new paid/network run requires the explicit flag:

```sh
python manual_tests/research_choices_2026_09_29/run_live.py --live --model openai/gpt-4o-mini
```

The live command uses the configured `.env` credentials and the eight synthetic prompts in `cases.json`. It overwrites the recorded live results/trace in this directory. The answer key is never sent to the model. No patient data or local analysis inputs are transmitted.

## Files and limitations

- `corrected-original-answer.md`: final renderer's answer to the original Chinese question. Agent-facing answers remain English under project policy.
- `cases.json`: independent expected hypothesis groups and tools.
- `live-results.json`, `live-trace.json`, `live-science-check.json`: last live run and checks.
- `replay-results.json`, `replay-science-check.json`: deterministic replay after final cleanup.

Scientific extraction still depends on a language model. Exact source quotation establishes provenance, not proof that the scientific interpretation is correct. Invalid quotations or unavailable providers cause a clarification/failure response rather than a single-tool recommendation. An unsupported hypothesis remains a visible gap. Missing priors are listed as requirements, not evidence that the method is impossible.

The original example's scientific wording was also corrected: SAMBAR uses normalization, pathway aggregation and distance-based clustering, not NMF; a pathway mutation score does not establish permanent functional loss. PANDA/LIONESS edge weights estimate regulatory support rather than measured binding strength, and cross-sectional samples do not establish temporal rewiring. Sources: [SAMBAR documentation](https://netzoo.github.io/netZooR/articles/SAMBAR.html), [LIONESS paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6463816/).

Codebase Memory MCP tools were unavailable in this session. Source and tests were inspected directly; no graph refresh or coverage verification is claimed.

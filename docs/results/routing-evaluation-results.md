# Quantitative results: contract-level repair and model capability in LLM tool routing

Draft results section for the NetZoo routing agent. Every number below is
recomputed from the committed JSON reports in `docs/research-log/`; the commands
are in §7. Each result is labelled **pre-registered** or **descriptive**, and
every confound we know of is stated with the result rather than in a footnote.

---

> **Superseded by `netzoo-routing-findings.md`**, which adds the corpus-coverage
> and execution-layer findings and the cheap model's noise floor. This file is
> kept as the measurement record for the version named below.
>
> **Version boundary.** Every number in this document measures the routing
> system as of commit `8a6ddc5`. A later change reduced the keyword-based
> registry fallback and made the second semantic call conditional; rounds taken
> after it are not comparable to the rounds below, and the fallback-derived
> figures (class **B1**) in particular describe behaviour that no longer exists.
> The results stand as measurements of that version and are labelled as such.

## 1. System and task

The agent maps a free-text request from a domain scientist onto one registered
NetZoo workflow (12 runnable capabilities: PANDA, PUMA, LIONESS variants, SAMBAR,
CONDOR, DRAGON, COBRA, OTTER, GIRAFFE, …). Routing is two-stage: a language model
emits a typed `RequestedOutcome` (operation, input artifacts, output artifact
type, entity/regulator/target roles, granularity, registry tags) with per-field
evidence; a deterministic layer validates that structure against an ontology and
matches it against the capability registry. The model never names a workflow.

## 2. Benchmark and protocol

- **Corpus**: 14 authored prompts (`tests/routing_scenarios.json`), covering
  positive cases, paraphrases, history-bearing requests where a previously used
  tool must *not* be recommended, and negative controls where the correct
  behaviour is to recommend nothing. English, Chinese, and mixed.
- **Trials**: unless stated, each round is `--repeat 3`, i.e. 42 trials, at
  temperature 0.
- **Configuration fingerprints**: every report records SHA-256 digests of the
  corpus, the policy, and the prompt+schema bundle. Two rounds are only compared
  when the digests match; each comparison below states which digests were held
  fixed.
- **Pre-registration**: acceptance criteria, including the threshold counts,
  were written into the research log *before* each paid round and were not edited
  afterwards. Post-hoc analyses are labelled descriptive.

## 3. Metrics

Each trial is assigned exactly one class, ordered by how it affects a scientist
acting on the output:

| Class | Meaning |
| --- | --- |
| **A** | Correct tool **and** no error in `input_artifacts`, `artifact_type`, `granularity`, `entity_types`, `request_mode` |
| **B1** | Correct tool, but no validated structured outcome (registry fallback) |
| **B2** | Correct tool, outcome present, at least one parameter wrong or absent |
| **C** | A tool was expected and none was recommended (silence) |
| **D** | A tool was recommended and it was the wrong one |

Safety is tracked separately: **D**, recommendation of an explicitly forbidden
action, and any unauthorized execution.

`A` is the primary quality metric because a correct tool with wrong parameters
still produces the wrong analysis.

---

## 4. Experiment 1 — Controlled A/B: field-scoped repair vs whole rewrite

**Design (matched controls).** When the deterministic validator rejects a first
interpretation, a second model call repairs it. We compare two contracts for that
call: the baseline asks for a complete replacement structure; the candidate asks
for a *patch* naming only the fields to change, with omitted fields carried
forward verbatim from the first pass. **Both arms are injected with identical
reconstructed first-pass proposals**, so the only variable is the repair
contract. Both arms then face the identical strict validator; call count and
token budget are unchanged.

**Result.**

| Suite | Baseline | Candidate |
| --- | --- | --- |
| missing-input | 0 / 9 | 5 / 9 |
| cross-field | 0 / 9 | 3 / 9 |
| missing-input (confirmation) | **0 / 15** | **8 / 15** |
| **Pooled** | **0 / 33 (0.0%, 95% CI 0.0–10.4%)** | **16 / 33 (48.5%, 95% CI 32.5–64.8%)** |

Risk difference **+48.5 pp (95% CI +32.2 to +67.6)**. Fisher exact (two-sided):
**p = 3×10⁻⁶** pooled; **p = 0.0022** for the pre-registered confirmation round
alone (**p = 0.0011** one-sided, the statistic declared in advance).

**Status: pre-registered.** The confirmation round's criterion and its three
guardrails were written before it ran and executed by
`scripts/compare_repair_rounds.py`.

**Confound to state:** injected proposals are reconstructions of observed error
*classes*, not captured model text, so this measures the repair contract under
those classes, not end-to-end accuracy.

---

## 5. Experiment 2 — Model capability

**Design (single variable).** Two consecutive rounds with **byte-identical
code** (the only commit between them touched documentation), identical corpus,
policy and prompt digests, differing only in the routing model.

| Metric | gpt-4o-mini (n=42) | gpt-4o (n=42) | Fisher (2-sided) |
| --- | --- | --- | --- |
| **A** (right tool + right parameters) | 8 (19.0%, CI 10–33%) | **18 (42.9%, CI 29–58%)** | **p = 0.033** |
| Correct tool | 27 (64.3%) | 33 (78.6%) | p = 0.227 |
| Silence (C) | 15 (35.7%) | 9 (21.4%) | p = 0.227 |
| Full-pass | 7 (16.7%) | 13 (31.0%) | p = 0.200 |

Risk difference on **A**: **+23.8 pp (95% CI +6.3 to +43.6)**.

**Corroboration (descriptive, confounded).** Pooling all rounds per model —
which spans several code revisions and is therefore *not* single-variable —
correct-tool rate is 51/84 (60.7%) for mini against 136/168 (81.0%) for gpt-4o,
Fisher **p = 7.6×10⁻⁴**.

**Reading.** The composite metric **A** separates the models at n=42 while the
raw correct-tool rate does not. Requiring the parameters to be right as well as
the tool roughly doubles the sensitivity of the benchmark at fixed cost.

**Status: the round was pre-registered** (with a stricter, unmet threshold on
correct-tool rate); the **A** comparison reported here is **descriptive**.

---

## 6. Experiment 3 — Benchmark resolution (methodological)

**Design.** Two rounds with **no code difference whatsoever** — the intervening
commit added a reporting field and changed no behaviour — same model, corpus,
policy and prompt digests. All variation is provider execution variance at
temperature 0.

| Metric | Round A | Round B | Difference |
| --- | --- | --- | --- |
| Correct tool | 33 / 42 | 36 / 42 | **3 trials (7.1 pp)** |
| **A** | 18 / 42 | 19 / 42 | 1 trial |
| Full-pass | 15 / 42 | 16 / 42 | 1 trial |

**The highest correct-tool rate recorded in the whole study (36/42) came from
re-running unchanged code.** 8 of 14 prompts gave inconsistent results across
their own three trials in an earlier round.

**Consequence.** On a 14-prompt × 3-trial benchmark, a difference of ≤3 trials
is indistinguishable from run-to-run variance. Reported improvements of that size
— including several we initially recorded ourselves and later withdrew — do not
survive. Detecting an effect of ~5/42 requires either many more prompts or a
matched-control design like Experiment 1.

The same replicate on **gpt-4o-mini**, also with no code difference:

| Metric | Round A | Round B | Difference |
| --- | --- | --- | --- |
| Correct tool | 28 / 42 | 28 / 42 | **0** |
| **A** | 17 / 42 | 19 / 42 | 2 trials |
| Silence (C) | 14 / 42 | 14 / 42 | **0** |
| Full-pass | 15 / 42 | 16 / 42 | 1 trial |

Fisher p = 1.0 (correct tool) and p = 0.83 (**A**). The cheaper model's floor is
**narrower** than the stronger model's, not wider as we predicted before running:
±0–2 trials against ±3.

Two consequences. First, an effect must clear roughly 3 trials on this benchmark
to be readable at all, on either model. Second, **diagnostic issue counts are far
noisier than trial outcomes**: the same two identical mini rounds differ by 21
occurrences of one issue family (63 vs 42) while every trial-level metric moves
by at most 2. Mechanism claims stated in issue counts therefore need effect sizes
in the tens, which is how the interventions in this project were in fact judged.

**Status: pre-registered as a replicate** (declared before running that the
difference would define the noise floor and could not be attributed to anything).

---

## 7. Experiment 4 — Safety

Across **294 trials** spanning both models and seven rounds:

- recommendations of a **wrong tool: 0**
- recommendations of an **explicitly forbidden action: 0** (prompts that name a
  previously used tool that must not be reused)
- **unauthorized executions: 0**

0/294 gives a 95% upper bound of **1.02%** (rule of three).

Failures are silence or under-specification, not confident error: the
deterministic layer refuses to emit a workflow it cannot validate, and degrades
to a clarification question or a registry-level suggestion.

**Status: descriptive**, but the zero counts were pre-registered veto conditions
in every intervention round: any wrong or forbidden recommendation would have
withdrawn the change under test.

---

## 8. Limitations

1. **Corpus size and provenance.** 14 prompts, written by the system's authors.
   Expected answers encode their judgement. Nothing here generalises to unseen
   request styles, and Experiment 3 shows the corpus is the binding constraint on
   resolution.
2. **Single provider family.** Both models are OpenAI via OpenRouter. No claim
   about other providers.
3. **Temperature 0 is not determinism.** Experiment 3 quantifies the residual.
4. **Cross-round comparisons.** Only Experiments 1 and 3, and the primary table
   of Experiment 2, hold code fixed. The pooled figure in §5 does not, and is
   labelled accordingly.
5. **`A` depends on the corpus's expected parameters**, which are a modelling
   choice, not ground truth from execution. We did not run the workflows and
   compare biological outputs.

## 9. Reproducibility

Reports are committed as JSON with their configuration digests:
`docs/research-log/live-full-corpus-round*.json` (end-to-end rounds) and
`docs/research-log/repair-replay-*.json` (Experiment 1). Offline analysis needs
no provider:

```bash
python -m pytest -q --ignore=tests/test_sambar_container.py
python scripts/compare_repair_rounds.py BASELINE.json CANDIDATE.json
python scripts/analyze_patch_evidence.py docs/research-log/live-*.json
```

A live round (billable) is:

```bash
python scripts/evaluate_routing.py --live --model MODEL --repeat 3 --max-calls 130 --json
```

The narrative record, including every criterion declared before its round and
every prediction that failed, is `docs/research-log/sambar-agent-routing.md`.

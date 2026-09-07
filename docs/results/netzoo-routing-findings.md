# Contract-level routing for scientific workflows: what held, what did not, and what the benchmark could not see

Paper-ready findings for the NetZoo routing agent. This supersedes
`routing-evaluation-results.md`, which remains as the measurement record for one
earlier version. Every number here is recomputed from committed JSON reports and
committed test fixtures; §8 lists the commands. Each claim is labelled
**pre-registered** or **descriptive**, and confounds are stated with the claim.

The narrative record — including every criterion declared before its round and
every prediction that failed — is `docs/research-log/sambar-agent-routing.md`.

---

## 1. System

The agent maps a free-text request from a domain scientist onto one registered
NetZoo workflow. Routing is two-stage. A language model emits a typed
`RequestedOutcome` — operation, input artifacts, output artifact type,
entity/regulator/target roles, granularity, registry tags — with per-field
evidence. A deterministic layer then validates that structure against an
ontology and matches it against a capability registry of 12 runnable workflows.
**The model never names a workflow.** That is a structural property, and §6
argues it is the reason one safety number is what it is.

## 2. Benchmark and protocol

- **Corpus**: 19 authored prompts, English/Chinese/mixed, covering positive
  cases, paraphrases, history-bearing requests where a previously used tool must
  *not* be recommended, and negative controls where the correct behaviour is to
  recommend nothing. Fourteen were pre-existing; §5 explains the five added and
  what they cost in comparability.
- **Trials**: `--repeat 3`, temperature 0.
- **Fingerprints**: every report records SHA-256 digests of corpus, policy and
  the prompt+schema bundle, plus the review policy and provider contract in use.
  Rounds are compared only when the digests match, and each comparison below
  says which were held fixed.
- **Pre-registration**: acceptance criteria, with threshold counts, were written
  into the research log before each paid round and not edited afterwards.

## 3. Metrics

One class per trial, ordered by consequence for someone acting on the output:

| Class | Meaning |
| --- | --- |
| **A** | Correct tool **and** no error in `input_artifacts`, `artifact_type`, `granularity`, `entity_types`, `request_mode` |
| **B1** | Correct tool, no validated structured outcome |
| **B2** | Correct tool, outcome present, at least one parameter wrong or absent |
| **C** | A tool was expected and none recommended |
| **D** | A tool was recommended and it was the wrong one |

**A** is primary: a correct tool with wrong parameters still produces the wrong
analysis. §4.2 shows this composite separates conditions that the raw
correct-tool rate cannot.

---

## 4. Results

### 4.1 A field-scoped repair contract beats a whole rewrite

**Matched controls.** When the validator rejects a first interpretation, a second
model call repairs it. Baseline asks for a replacement structure; candidate asks
for a *patch* naming only the fields to change, omitted fields carried forward
verbatim. **Both arms receive identical injected first-pass proposals**, face the
identical validator, and use the same call and token budget, so the only variable
is the contract.

| Suite | Baseline | Candidate |
| --- | --- | --- |
| missing-input | 0 / 9 | 5 / 9 |
| cross-field | 0 / 9 | 3 / 9 |
| missing-input (confirmation) | **0 / 15** | **8 / 15** |
| **Pooled** | **0 / 33** (0.0%, 95% CI 0.0–10.4) | **16 / 33** (48.5%, CI 32.5–64.8) |

Risk difference **+48.5 pp** (95% CI +32.2 to +67.6). Fisher exact two-sided
**p = 3×10⁻⁶** pooled; **p = 0.0022** for the pre-registered confirmation round
alone (p = 0.0011 one-sided, the statistic declared in advance).

**Pre-registered.** *Confound:* injected proposals reconstruct observed error
classes, not captured model text, so this measures the contract under those
classes, not end-to-end accuracy.

### 4.2 Model capability dominates, and the composite metric is what shows it

**Single variable:** two consecutive rounds with byte-identical code (the only
intervening commit touched documentation), identical corpus, policy and prompt
digests.

| Metric | gpt-4o-mini (n=42) | gpt-4o (n=42) | Fisher |
| --- | --- | --- | --- |
| **A** | 8 (19.0%, CI 10–33) | **18 (42.9%, CI 29–58)** | **p = 0.033** |
| Correct tool | 27 (64.3%) | 33 (78.6%) | p = 0.227 |
| Silence (C) | 15 (35.7%) | 9 (21.4%) | p = 0.227 |

Risk difference on **A**: **+23.8 pp** (95% CI +6.3 to +43.6).

**The composite separates the models at n=42 while the raw correct-tool rate does
not.** Requiring the parameters as well as the tool roughly doubles the
benchmark's sensitivity at fixed cost — a reusable point for anyone evaluating
tool-selecting agents.

*Corroboration, confounded:* pooling all rounds per model (spanning several code
revisions, therefore not single-variable) gives 51/84 (60.7%) against 136/168
(81.0%), p = 7.6×10⁻⁴.

Round pre-registered; the **A** comparison itself is descriptive.

### 4.3 One class of failure is model capability, and it disappears

Evidence entries may cite the request; the validator rejects a citation it cannot
find in the text. Across three rounds on the cheap model, **27 rejected citations
were all of one kind — the entry claimed an explicit quote and supplied none;
"quoted text absent from the request" occurred zero times.** A pre-registered
criterion put that at ≥2/3 of clusters; the observed value was 3/3.

On the stronger model the family vanishes: **0 of 270 explicit entries omit their
quote.** So it is a capability limit, not a contract defect — and a contract
change proposed for it was argued against on that basis and never made.

**Pre-registered.**

### 4.4 Benchmark resolution: most reported gains here are noise

Replicates with **no code difference at all**, same model, corpus, policy and
prompt digests. All variation is provider execution variance at temperature 0.

| Model | Metric | Round A | Round B | Difference |
| --- | --- | --- | --- | --- |
| gpt-4o | Correct tool | 33 / 42 | 36 / 42 | **3 trials** |
| gpt-4o | **A** | 18 / 42 | 19 / 42 | 1 |
| gpt-4o-mini | Correct tool | 28 / 42 | 28 / 42 | **0** |
| gpt-4o-mini | **A** | 17 / 42 | 19 / 42 | 2 |

**The highest correct-tool rate recorded in the study, 36/42, came from
re-running unchanged code.** A third replicate arose by accident: a conditional
that never fired made two nominally different arms byte-identical in behaviour,
and their spread matched.

Two thresholds follow, and they differ by an order of magnitude:

- **trial-level scores** need about **3 trials** of difference to be readable;
- **diagnostic issue counts** need effects **in the tens** — the same two
  identical cheap-model rounds differ by **21** occurrences of one issue family
  while every trial-level metric moves by at most 2.

Several improvements this project initially recorded, including ones we reported
ourselves, do not survive this and were withdrawn. Detecting ~5/42 effects needs
many more prompts or a matched-control design as in §4.1.

**Pre-registered** as replicates.

### 4.5 Safety, and why the zero was a coverage artifact

On the 14-prompt corpus, across **294 trials**, both models, seven rounds:
**0 wrong-tool recommendations, 0 forbidden actions, 0 unauthorized
executions** — a 95% upper bound of 1.02% by the rule of three.

**That zero did not survive covering the rest of the registry.** On the
19-prompt corpus the first round produced **3 wrong-tool recommendations in 57
trials (5.3%)**, all deterministic, all in a newly covered capability pair, and
all with `status = exact` and a semantic basis — confident recommendations, not
hedged fallbacks. Nothing about the system changed; the corpus stopped hiding it.

So the honest statement is not "this system does not recommend wrong tools". It
is: **the wrong-tool rate was 0/294 on a corpus exercising 6 of 12 capabilities,
and 3/57 on one exercising 11 of 12.** §5.4 gives the mechanism, which is a
single ontology rule that the prompt states, the model breaks, and the registry
then amplifies into a confident answer.

Forbidden actions and unauthorized executions remain at zero on both corpora.

The zero counts were pre-registered veto conditions in every intervention round;
this round was pre-registered as a baseline, with the note — written before it
ran — that a non-zero wrong-tool count would be a pre-existing defect revealed by
the new corpus rather than a regression. It was.

---

## 5. What the benchmark could not see

Everything in §4 measures routing. Three defects were invisible to all of it.

### 5.1 Half the registry had no test case

The 14-prompt corpus exercised **6 of 12** runnable capabilities. PUMA, OTTER,
GIRAFFE, BONOBO and LIONESS-coexpression had none, so no measurement could have
revealed a defect in them.

Reachability was checked before authoring cases, because an expectation no
outcome can satisfy would depress the score permanently for a reason unrelated to
the model. Five are reachable through their own registry tags and now have cases;
coverage is **11 of 12**.

### 5.2 PANDA cannot be uniquely recommended

```
run_panda   = {aggregate_network, tf_gene_regulation}
run_otter   = {aggregate_network, tf_gene_regulation, relaxed_graph_matching}
run_giraffe = {aggregate_network, tf_gene_regulation, tfa}
```

PANDA's tag set is a **proper subset** of both. Any outcome carrying PANDA's tags
also satisfies OTTER's and GIRAFFE's prerequisites, so a rule that requires
exactly one surviving candidate can never select it. **NetZoo's flagship method
is structurally unreachable**, and no routing metric could show it because no
case asked for it. The same shape had been found once before for CONDOR.

A test now requires every capability to be reachable or listed as knowingly not,
forbids the corpus from expecting an unreachable one, and fails if a reachable
capability has no case.

### 5.3 The ontology's claims about artifacts were never checked against a run

Recorded outputs of pinned runs are checked against the artifact contracts the
router relies on. Three findings, recorded rather than corrected:

1. **Declared orientation disagrees with the output.** `gene_mutation_scores` is
   described as "Gene-by-sample"; SAMBAR's actual artifact is sample-by-gene. The
   description is prose, so this may be a documentation defect — **but nothing in
   the system could tell the difference.**
2. **Sample coverage is silently lost.** SAMBAR's pathway artifact covers **247**
   of the **248** samples present in its own gene-level artifact, a strict
   subset. Plausibly intrinsic to the method — a patient whose mutations are all
   filtered cannot be normalised by mutation burden — but from the requester's
   position it is an unannounced loss, and the agent never mentions it.
   **Routing correctness and output completeness are different properties.**
3. **One artifact type, three serialisations.** PANDA writes a tab-separated
   header; **PUMA writes no header at all**; LIONESS-PUMA writes a
   space-separated header above tab-separated rows. All three declare
   `regulatory_network`. Routing treats it as one thing; at the file level it is
   not, and no consumer can parse them uniformly.

### 5.4 One stated rule, broken by the model, amplified by the registry

The prompt tells the model: *a sample-specific result does not by itself make
`sample` an entity inside the result.* Two capabilities nevertheless declare
`sample` among their entities, and for one pair that makes the rule decisive:

| Outcome (same request, only `entity_types` differs) | Match |
| --- | --- |
| `entity_types=["gene"]` | **exact `run_lioness_coexpression`** — correct |
| `entity_types=["gene","sample"]` | **exact `run_bonobo`** — wrong, and confident |
| `entity_types=[]` | ambiguous, both candidates |

The model wrote `["gene","sample"]` in all three trials of the per-sample
coexpression prompt, and the registry turned that one extra value into a
different workflow. **A documented rule that nothing enforces became a
wrong-tool recommendation.**

The coupling also runs the other way. With the natural value `["gene"]`, an
exact entity-set match to LIONESS-coexpression **outranks BONOBO's own unique
`bayesian` tag**, so the tag is never consulted: BONOBO is reachable only by
omitting `entity_types` or by committing the rule violation above. It is
*conditionally* unreachable — the correct outcome cannot select it — which is a
distinct defect from PANDA's absolute case in §5.2.

The corollary is uncomfortable and worth stating: the sibling prompt asking for
Bayesian per-sample coexpression scored 3/3, **for the wrong reason** — two of
its three trials named no `bayesian` tag at all and were selected by the same
mistaken entity value. A passing case is not evidence of comprehension.

**Scope:** these check identifier families, axis orientation, sample coverage and
required/forbidden columns. **Numbers are not compared and this is not biological
validation.** A full execution benchmark additionally needs fixed input bundles,
reference values with justified tolerances, and per-workflow biological
assertions; that does not exist.

---

## 6. Two claims worth stating as design results

**Consistency is not comprehension.** Across three intervention rounds, validator
issue counts, full-pass rate and internal-agreement measures all improved
markedly while the correct-tool rate stayed inside the noise floor of §4.4. An
outcome and its evidence can agree and be wrong together. The system needed a
*separate* terminal-goal check to catch requests for patient clustering answered
with a patient network, and that check still fires 5–9 times per round — direct
evidence that consistency checking does not subsume it.

**Part of the safety record is structural, not learned.** The contract forbids
the model from naming a workflow, so it cannot name a wrong one; selection is
deterministic from typed fields. A design in which the model proposes candidates
and a checker filters them would move that guarantee from "impossible" to
"caught", and §4.5's bound would have to be re-earned rather than inherited.

## 7. Limitations

1. **Corpus size and provenance.** Nineteen prompts written by the system's
   authors; expected answers encode their judgement. The five added cases form
   **three goal families, not five independent tasks** — independence is bounded
   by the size of the tool set — and paraphrase groups should be treated as one
   statistical unit. §4.4 shows corpus size is the binding constraint on
   resolution.
2. **Corpus change breaks comparability.** The digest changed when the five cases
   were added; rounds before and after are not directly comparable. The original
   fourteen remain scoreable as a subset.
3. **Single provider family.** Both models are OpenAI via OpenRouter.
4. **Temperature 0 is not determinism.** §4.4 quantifies the residual.
5. **`A` is graded against expected parameters, not execution.** §5.3 is the
   first step toward closing this and closes only the structural part.
6. **One reported architecture change is unmeasured by design.** An experimental
   provider contract that removes the evidence/outcome duplication is implemented
   but off by default; the controlled result in §4.1 does not transfer to it, and
   on the cheap model the failure class it targets does not occur at all.

## 8. Reproducibility

```bash
# offline, no provider needed
python -m pytest -q --ignore=tests/test_sambar_container.py
python scripts/compare_repair_rounds.py BASELINE.json CANDIDATE.json
python scripts/analyze_patch_evidence.py docs/research-log/live-*.json

# billable
python scripts/evaluate_routing.py --live --model MODEL --repeat 3 \
  --max-calls 180 --review-policy when_needed --semantic-contract legacy --json
```

Reports: `docs/research-log/live-*.json` (end-to-end) and
`repair-replay-*.json` (§4.1). Execution fixtures with provenance:
`tests/fixtures/execution/`. Guards: `tests/test_capability_corpus_coverage.py`,
`tests/test_execution_artifact_contracts.py`.

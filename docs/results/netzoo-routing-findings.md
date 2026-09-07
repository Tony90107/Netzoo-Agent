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

### 4.5 Safety, and why the first zero was a coverage artifact

On the original 14-prompt corpus — which exercised **6 of 12** capabilities —
294 trials across both models produced **0 wrong-tool recommendations, 0
forbidden actions, 0 unauthorized executions**, a 95% upper bound of 1.02% by
the rule of three.

**That zero did not survive covering the rest of the registry.** Extending the
corpus to 11 of 12 capabilities, with no change to the system, produced **3
wrong-tool recommendations in 57 trials (5.3%)** — all deterministic, all in a
newly covered capability pair, all reported as `exact` with a semantic basis.
Confident recommendations, not hedged fallbacks.

After the causes were fixed (§5.4, §5.5), a 60-trial round on the 12-of-12
corpus is back to **0 wrong-tool recommendations, 0 forbidden actions, 0
unauthorized executions**.

The sequence is the result, not any single number:

| Corpus | Capabilities covered | Trials | Wrong-tool |
| --- | --- | --- | --- |
| 14 prompts | 6 / 12 | 294 | **0** |
| 19 prompts | 11 / 12 | 57 | **3** |
| 20 prompts, causes fixed | 12 / 12 | 60 | **0** |

A safety rate is a statement about a corpus, not about a system. Ours was
0/294 partly because half the registry was never asked for.

Forbidden actions and unauthorized executions are zero throughout.

### 4.6 How often does the model supply the information that picks the tool?

**Three trials in 27.**

Several prompts fit more than one capability on the coarse dimensions the corpus
originally recorded; what separates them is a role or a registry tag. The corpus
now records that discriminator per prompt and the scorer requires it. Across the
27 trials of the nine annotated prompts, **24 omit it** — the model named a tool
without producing the information that chose it, and a deterministic preference
in the matcher covered the gap.

**All 24 were scored fully correct before this measurement existed.** That single
number is the sharpest evidence for §6's first claim: internal consistency and
even a correct tool name are not comprehension, and a benchmark that grades only
the answer cannot tell the difference.

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

### 5.2 PANDA could not be recommended at all, and neither could two others

```
run_panda                = {aggregate_network, tf_gene_regulation}
run_otter                = {aggregate_network, tf_gene_regulation, relaxed_graph_matching}
run_giraffe              = {aggregate_network, tf_gene_regulation, tfa}
run_lioness_coexpression = {coexpression, sample_specific}
run_bonobo               = {bayesian, coexpression, sample_specific}
```

Three nesting relations, and in each the **subset** member is the baseline
method while the supersets are its specialisations. A tie-break requiring
exactly one surviving candidate can never select a subset member, so
**NetZoo's flagship method was structurally unrecommendable** — and no routing
metric could reveal it, because no corpus prompt asked for it.

The fix is one rule, and it is a statement about scientific requests rather than
a heuristic: *a request that names no specialisation is asking for the
baseline*, so among candidates carrying every declared tag the unique minimum
under subset order wins. All 12 capabilities are now uniquely reachable and the
corpus covers all 12.

A test requires every capability to be reachable or listed as knowingly not,
forbids the corpus from expecting an unreachable one, and fails if a reachable
capability has no case.

### 5.3 The ontology's claims about artifacts were never checked against a run

Recorded outputs of pinned runs are checked against the artifact contracts the
router relies on. Three findings, recorded rather than corrected:

1. **Declared orientation disagrees with the output.** `gene_mutation_scores` is
   described as "Gene-by-sample"; SAMBAR's actual artifact is sample-by-gene. The
   description is prose, so this may be a documentation defect — **but nothing in
   the system could tell the difference.**
2. **Sample coverage is silently lost, and the loss is the method's.** SAMBAR's
   pathway artifact covers **247** of the **248** samples in its own gene-level
   artifact. §5.6 settles the attribution: upstream netZooPy's own ground truth
   carries the same 247 columns, so a patient whose retained mutations sum to
   zero cannot be normalised by mutation burden. Not a defect to fix — but the
   agent never tells the requester that a sample was dropped.
   **Routing correctness and output completeness are different properties**,
   and only an execution-layer check could say which of the two this was.
3. **One artifact type, three serialisations.** PANDA writes a tab-separated
   header; **PUMA writes no header at all**; LIONESS-PUMA writes a
   space-separated header above tab-separated rows. All three declare
   `regulatory_network`. Routing treats it as one thing; at the file level it is
   not, and no consumer can parse them uniformly.

### 5.4 One stated rule, broken by the model, amplified by an arbitrary preference

The prompt tells the model: *a sample-specific result does not by itself make
`sample` an entity inside the result.* Two capabilities nevertheless declared
`sample` among their entities, and for one pair that made the rule decisive:

| Outcome (same request, only `entity_types` differs) | Match |
| --- | --- |
| `entity_types=["gene"]` | exact `run_lioness_coexpression` |
| `entity_types=["gene","sample"]` | **exact `run_bonobo`** — wrong, and confident |

The model wrote `["gene","sample"]` in all three trials, and that one extra value
selected a different workflow. **A documented rule that nothing enforced became a
wrong-tool recommendation.**

Correcting the declarations took three attempts, and the two failures located the
real cause. Removing `sample` makes the two capabilities tie on entities — and
the matcher then reported `exact` anyway, because its specificity score counted
**how many granularities a capability supports beyond the one requested**. The
request names one value and both candidates support it; that one of them also
supports another says nothing here. That term alone decided the tie, first
visibly through an explicit-name path (an execute request naming
LIONESS-COEXPRESSION resolved to BONOBO) and then on the direct matching path,
where an existing test correctly demanded a clarification and got a confident
answer instead.

Removing that one term, and only that one, resolved it. Excess on **roles and
entities is kept**: a capability that also handles regulators the request never
mentioned may need priors the user does not have, and this was measured, not
assumed — refusing `exact` for any tie broke exactly that legitimate case and two
corpus prompts depending on it.

The prompt in question now returns a clarification question in all three trials,
which is the correct answer: the request does not distinguish the two
capabilities.

### 5.5 A registered label that is an ordinary English word

`inspect_inputs`, a validation step, is labelled `inputs`. Its name pattern is
therefore the bare word, so **"I have three inputs and want a network."**
resolves to it, and a live round recommended that non-workflow as `status =
exact` with basis `workflow_name`.

The rule is about the label, not the action: a method name is a deliberate
reference and so is a multi-word step label, but a single common English word is
not — unless the action is one the router can recommend. Excluding every
supporting action instead was tried and was too broad; naming `WEB-SEARCH`
deliberately is legitimate and an existing test said so.

This is the second defect a corpus prompt exposed rather than a metric. It was
also the occasion for a methodological correction of our own: the guardrail for
the change under test was written as "wrong-tool recommendations = 0" where an
earlier round had correctly written "= 0 *attributable to this change*". Under
the literal wording a clean change would have been withdrawn for an unrelated
defect. Criteria need their phrasing checked, not only their thresholds.

**Scope:** these check identifier families, axis orientation, sample coverage and
required/forbidden columns of outputs recorded earlier.

### 5.6 Execution-layer verification, and the three defects it found

The pinned image carries netZooPy 0.11.0, and netZooPy ships ground-truth files
together with the inputs that produce them. So a workflow can be run through the
production path and compared against **reference values its own authors wrote**.
Five of the twelve capabilities are now covered. Three reproduced their
references immediately; **two did not, and the discrepancies were real defects in
this system** — one of them silently wrong, one of them a capability that could
never execute at all.

| Workflow | Component | Result |
| --- | --- | --- |
| SAMBAR | pathway × sample scores | agrees to **3.5 × 10⁻¹⁸** |
| COBRA | `psi` | agrees to **5.3 × 10⁻¹¹** |
| COBRA | `D` (eigenvalues) | agrees to **1.3 × 10⁻¹²** |
| COBRA | `G` (gene loadings) | agrees to **3.7 × 10⁻¹⁵** |
| COBRA | `Q` (eigenvectors) | agrees, via reconstruction |
| OTTER | TF × gene network | **defect: 80.3% of the PPI network fabricated** |
| GIRAFFE | `R_hat`, `TFA_hat` | **defect: could not execute at all** |
| GIRAFFE | PPI input format | **defect: documented format unreachable** |
| CONDOR | regulator and target memberships | agrees **label-for-label** |
| CONDOR | partition under a newer igraph | agrees up to relabelling |

After the fixes, GIRAFFE reproduces upstream's reference to 1.5 × 10⁻⁶
(`R_hat`) and 4.3 × 10⁻⁸ (`TFA_hat`), inside upstream's own `atol=1e-5`.

CONDOR needs a different kind of assertion, and saying why sharpens what these
checks are for. Upstream ships **two** reference files per side, one of them
suffixed `v9igraph`, because community *numbering* moves with the igraph
version. Our image carries igraph 1.0.0 and agrees label-for-label with the
primary reference; against the `v9igraph` variant the labels differ but the
**partition is identical** — every community maps onto exactly one of theirs.
Asserting the partition rather than the labels states the claim that actually
holds, and it is the claim a biologist depends on, since community numbers are
arbitrary and only the grouping is a result. The test also asserts that the
labels still *disagree* with the `v9igraph` variant, so that if the two
references ever converge the premise cannot fail silently. The four artifacts
are byte-identical across repeated runs, so this wrapper's community detection
is deterministic even though the method's is randomised in general.

**The tolerances are not ours.** Each test calls upstream's own assertion for
that method verbatim — the pandas
`assert_frame_equal(..., rtol=1e-10, check_exact=False)` from
`tests/test_cobra.py`, and `np.testing.assert_allclose(..., atol=1e-5)` from
`tests/test_giraffe.py`. That mattered rather than being merely tidy: pandas
applies a default `atol=1e-8` alongside `rtol`, and with 400 samples against
4000 genes COBRA's covariance is rank-deficient, so its trailing eigenvalue is
zero in exact arithmetic and floating-point dust in practice (ours
1.3 × 10⁻¹³, upstream −6.3 × 10⁻¹⁴). A pure relative comparison against zero is
undefined; upstream's combined criterion is the correct instrument, not a more
forgiving one. `Q` is compared through the covariance reconstructed from `Q` and
`psi`, as upstream compares it, because eigenvectors are sign-ambiguous.

**The assertions discriminate.** Injecting a relative perturbation into a
reference value, the check catches 10⁻⁶ and 10⁻⁹ and stops detecting at 10⁻¹¹,
where the absolute error falls under the `atol` floor — a measured detection
threshold, not an assertion that passes against any output.

#### Defect 1 — OTTER: 80.3% of a PPI network fabricated, silently

The PPI adapter required a three-column edge list (source, target, weight),
validated the weight as numeric, and then **discarded it**, assigning `1.0` to
every listed pair. The line above it, building the TF-gene matrix, used the
weight correctly.

Two things had to be kept apart. Discarding PPI *confidences* is a **documented
design choice** — `workflows/otter.yaml` states the adapter "uses a binary
adjacency projection" — so it is not a hidden bug, though it does deviate from
what netZooPy's `otter(W, P, C)` accepts. But projecting a weight of **0** to
`1.0` is wrong under every reading, the documented binary one included: an
interaction the input file explicitly declares absent was turned into one
present.

Measured on upstream's own OTTER toy data (661 TFs): of the 436,260 off-diagonal
cells, 350,312 are genuinely absent and 85,948 present. Writing that PPI network
out as an edge list and reading it back therefore **fabricated 80.3% of the
network as interacting**, substituting a fully connected graph for a sparse one,
and moved the resulting regulatory network by 1.5 × 10⁻⁵ against values of order
7 × 10⁻⁶ — an error the size of the signal, reported without any warning.

#### Defect 2 — GIRAFFE: a registered capability that could never run

netZooPy's `Giraffe(expression, prior, ppi)` takes the prior **gene-by-TF**
(upstream's test passes `motif.T`) and returns regulation the same way round.
Our adapter builds it **TF-by-gene** and the call was made without converting,
so on upstream's toy data the API failed with
`The size of tensor a (913) must match the size of tensor b (87)`. Any request
whose gene count differs from its TF count — that is, every real request —
could not execute.

It survived because `settings.EXECUTE_TOOLS` defaults to `False`, so nothing
executed the path, and because the one mocked test used a fixture with **two
genes and two TFs**. A square prior makes an orientation error invisible; the
mock even asserted `prior.shape == (2, 2)`, which holds either way. **A
symmetric fixture cannot detect a transposition** — a methodological point that
generalises well beyond this workflow, and the reason the replacement test uses
three genes and two TFs.

#### Defect 3 — GIRAFFE: a documented input format that was unreachable

The PPI reader's dense-matrix detection required `rows == columns - 1` *and* an
ID token in the first cell. The second implies a header row, which makes an
n × n matrix read as (n+1) × (n+1), so `rows == columns`. The two conditions
cannot hold together, and every well-formed labelled square matrix — a format
the registry explicitly documents — fell through to the edge-list branch and was
rejected. The old condition instead fired on the wrong input: a three-column
edge list with header `tf/gene/weight` and one data row is 2 × 3 and starts with
an ID token, so it was *misread* as a matrix. Format is now decided by matching
the header against the TF set rather than by shape arithmetic.

#### Severity is not uniform, and the difference matters

All three defects passed routing, passed field validation, and satisfied every
structural contract. But they are not equally dangerous, and collapsing them
would misstate the result:

| Defect | Failure mode | Danger to a user |
| --- | --- | --- |
| OTTER PPI projection | **wrong numbers, no warning** | highest |
| GIRAFFE orientation | execution error | fail-safe |
| GIRAFFE PPI format | input rejected | fail-safe |

Only the first is silent. A biologist running OTTER would have received a
plausible-looking regulatory network computed from a PPI graph that was 80%
invented, with nothing anywhere in the system indicating a problem. The two
GIRAFFE defects are serious — one made a registered capability unusable — but
they announce themselves.

**No other layer in this system could have caught any of them.** Each request
routed to the correct workflow, every field validated, every structural contract
held, and OTTER's output had the right shape, the right identifiers and finite
values throughout. The defects lived in the arithmetic and at the API boundary.
This is the concrete answer to what §5.1–5.5 could not see, and the strongest
argument in this work for verifying execution rather than only routing.

#### What the verification method itself cost

OTTER **cannot** be checked against upstream's `test_otter.csv`, because that
reference was generated from a weighted P while our documented projection is
binary. The reference used instead is upstream's *code* —
`netZooPy.otter.otter` called directly on independently constructed matrices —
upstream's implementation standing in where its file is unreachable. That is a
weaker claim than SAMBAR's, COBRA's and GIRAFFE's, and is stated as such; it
still checks everything the adapter contributes (identifier mapping, ordering,
orientation, projection), and it is what caught the bug. GIRAFFE's reference
comes from upstream's own recipe, PANDA intersection-mode preprocessing, so the
comparison isolates this wrapper's contribution from PANDA's.

**Our layer is stricter than the methods' own tests, in the direction that
protects the user.** Upstream's COBRA test pairs design rows with expression
columns *by position* — `X.csv` indexed `1, 2, 3…` against expression columns
`V1, V2, …` — and our wrapper refuses that, requiring sample IDs that match.
Upstream's OTTER files are unlabeled matrices; ours requires identifiers.
Reproducing upstream's numbers meant making their positional conventions
explicit rather than relaxing our checks. A mispaired covariate would not
error — it would silently produce a confidently wrong result.

Two further things follow. Committed artifacts stop being "files we once
produced" and become files that still reproduce. And §5.3's second finding is
settled: SAMBAR's dropped sample is upstream behaviour, because upstream's
ground truth drops it too. **That distinction is the point of having an
execution layer: it separates our defect from the method's behaviour, and no
routing or structural check can.**

One further observation is recorded rather than acted on, because it is a
usability defect and not a correctness one. Feed CONDOR a well-formed
three-column network whose columns are named for the study
(`pollinator, plant, interactions`) rather than for the contract, and it is
rejected with *"weight column must be numeric when present; numeric ratio is
99.8%"*. That 99.8% is 442/443: the unrecognised header row was counted as data.
The weight column is entirely numeric, and the actual fix is to rename the
columns. The rejection is defensible — the contract does specify `source` and
`target` — but the message sends the user to inspect their numbers. Unlike the
three defects above, the user gets an error rather than a result, so this is
left as a product decision.

**What still does not exist** is per-workflow *biological* assertion for the
other seven capabilities — and given that two of the first five checked
contained defects, the prior that the unchecked seven are correct should be
weak. The pattern extends wherever upstream ships a reference, but not
uniformly. PANDA and PUMA are the awkward case, and worth stating precisely
rather than as a flat impossibility. Each has two paths: a precomputed one that
requires `--coexpression` and so computes something other than what upstream's
reference was generated from, and a plain one that shells out to netZooPy's own
`netzoopy panda` CLI. The plain path is in principle comparable, but upstream's
reference values come from its *class* API, while **upstream's own CLI test
asserts only `returncode == 0` and never compares a single value** — so a
value-level comparison there means reconstructing the class defaults through CLI
flags (`--save_memory`, `--save_tmp`, `--rm_missing`, and the `modeProcess`
variants, each with its own reference file) and then defending that
reconstruction as equivalent. That is a real gap rather than a closed one, and
it is left open rather than papered over with a comparison whose reference we
would have had to choose ourselves. The checks
are opt-in (`NETZOO_RUN_DOCKER_TESTS=1`) so the offline gate stays fast —
skipped, not absent.

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

1. **Corpus size and provenance.** Twenty prompts written by the system's
   authors; expected answers encode their judgement. The six added cases form
   **four goal families, not six independent tasks** — independence is bounded
   by the size of the tool set — and paraphrase groups should be treated as one
   statistical unit. §4.4 shows corpus size is the binding constraint on
   resolution.
2. **Corpus change breaks comparability, three times.** The digest changed when
   the five cases were added, again when PANDA's case was added, and again when
   the discriminators were recorded. Rounds are comparable only within a digest;
   the original fourteen remain scoreable as a subset, and §4.4's noise floors
   were measured within a single digest each.
3. **Single provider family.** Both models are OpenAI via OpenRouter.
4. **Temperature 0 is not determinism.** §4.4 quantifies the residual.
5. **`A` is graded against expected parameters, not execution.** §5.3 is the
   first step toward closing this and closes only the structural part. §4.6
   tightens `A` to require the discriminator, which is what a correct outcome
   must contain, but still not what the workflow actually produced.
6. **Every defect in §5 was found by widening the corpus or by checking the
   registry against itself — none by a routing metric.** That is the section's
   point, and it is also its limitation: we do not know how many remain, only
   that the metrics would not show them.
7. **One reported architecture change is unmeasured by design.** An experimental
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

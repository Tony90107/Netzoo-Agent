# Quantitative scientific and routing-stability evidence for mutation-to-pathway subtyping

Date: 2026-09-10
Status: paper-ready evidence note. Published biological results, observed live-agent results, and deterministic software-verification results are reported separately. No post-intervention live-model accuracy estimate is claimed.

## 1. Scientific claim

For a request whose current input is a sparse whole-exome somatic-mutation matrix and whose terminal goal is patient subtyping, the scientifically appropriate transformation is:

\[
\text{sparse gene mutations}
\rightarrow \text{length- and burden-adjusted gene scores}
\rightarrow \text{pathway scores}
\rightarrow \text{sample distances}
\rightarrow \text{cluster assignments}.
\]

In the registered NetZoo workflows, this outcome corresponds to SAMBAR. PANDA and LIONESS-PANDA infer regulatory networks from expression-compatible inputs; they do not accept a somatic-mutation matrix under their current registered contracts.

## 2. Mechanistic basis

Let \(N_{ij}\) be the number of non-silent mutations in sample \(i\) and gene \(j\), and let \(L_j\) be the number of non-overlapping exonic base pairs in gene \(j\). SAMBAR calculates a mutation-rate-adjusted gene score:

\[
G_{ij}=
\frac{N_{ij}/L_j}
{\sum_{j'} N_{ij'}/L_{j'}}.
\]

Let \(M_{jq}\) indicate whether gene \(j\) belongs to pathway \(q\). The pathway score is:

\[
P_{iq}=
\frac{
\sum_{j \in q} G_{ij}/\sum_{q'}M_{jq'}
}{
\sum_j M_{jq}
}.
\]

The first equation corrects mutation counts for gene/exon length and the sample's overall cancer-associated mutation rate. The second corrects the pathway aggregate for pathway size and for genes annotated to multiple pathways. The output is a pathway-by-sample score matrix, not a patient-specific mutation network. Sample distances and cluster assignments are separate downstream artifacts.

## 3. Quantitative evidence from the original SAMBAR study

These are published biological results, not measurements produced by the present agent.

### 3.1 Cohort and feature-space reduction

| Quantity | Reported value |
| --- | ---: |
| TCGA cancer types | 23 |
| Downloaded mutation samples | 6,406 |
| Patients after primary-tumour selection and replicate merging | 5,992 |
| Samples removed for zero cancer-associated mutation rate | 108 |
| Samples removed for no retained pathway mutation | 79 |
| Final primary tumours | 5,805 |
| Annotated genes before cancer-gene filtering | 19,065 |
| Retained cancer-associated genes | 2,219 |
| Initial canonical pathways | 1,135 |
| Pathways removed for no cancer-associated mutation | 69 |
| Final pathway features | 1,066 |

### 3.2 De-sparsification and sample separation

| Measure | Gene-level representation | Pathway-level representation |
| --- | ---: | ---: |
| Median mutated features per sample | 91 genes | 103 pathways |
| Mean fraction of features mutated within a cancer type | 54.8% | 84.2% |
| Across-cancer range | 6.1%–95.1% | 43.4%–93.8% |
| Association with cancer-type sample size | Pearson \(R=0.49\), \(p=0.017\) | \(p=0.099\), not significant |
| Reported median between-sample distance under the selected metric | 21, Mahalanobis | 108, binomial |

The distance values use different metrics and scales. Their raw ratio must not be described as a 5.14-fold increase in predictive accuracy or clustering performance.

### 3.3 Clinical and biological associations

| Result | Quantitative finding |
| --- | --- |
| Prognostic mutation subtypes | Significant survival-associated subtypes in 3 cancer types |
| ACC example | 74- and 12-patient clusters; log-rank \(p=0.0027\) |
| LAML example | Poor-survival group of 14 versus groups of 23 and 144; log-rank \(p=1.4\times10^{-4}\) |
| Permutation assessment | 10,000 label permutations; Benjamini–Hochberg-adjusted \(p<0.01\) |
| Subtype–drug associations | 251 associations across 15/23 cancer types |
| Tumours covered by CMap-enriched associations | 689/5,805, or 12% |
| Pan-cancer solution | 9 subtypes; mean size 581, range 74–2,194 |
| Recurrent pathway organization | 202 pathways grouped into 4 overarching sets |
| RPPA Akt validation | 0.459 versus 0.0756; \(t=2.34\), \(p=0.0198\) |
| RPPA DNA-damage validation | 0.283 versus 0.158; \(t=2.45\), \(p=0.0146\) |

Important limitations include residual mutation-rate structure in UCEC (13 samples, \(t=13.4\), \(p=1.27\times10^{-8}\)), batch associations, small prognostic subtypes, pathway-definition dependence, and retrospective rather than prospective clinical validation.

## 4. Observed repeatability problem in the supplied live runs

The attachment contains two independent invocations of the same Chinese prompt using `openai/gpt-4o-mini` at routing temperature 0.

| Observable | Run 1 | Run 2 |
| --- | --- | --- |
| Semantic result | Rejected after repair | Accepted after repair |
| Final routing status | No validated workflow | Exact |
| Selected workflow | None | `run_sambar` |
| PANDA/LIONESS-PANDA rejected | No final recommendation available | Both rejected as incompatible |
| Unauthorized execution | 0 | 0 |
| User-visible classification time | Not reported | 5.04 s |

Observed exact-routing success was therefore \(1/2=50\%\). The Wilson 95% confidence interval is 9.45%–90.55%. This interval is intentionally reported because \(n=2\) is far too small to estimate population-level routing accuracy.

The matched local traces are:

- failed: `.netzoo/traces/d0ebe7b1-f225-42c5-baf1-d6670a24f94f/events.jsonl`;
- successful: `.netzoo/traces/a90028b0-8984-4690-aeef-4402daee2ee3/events.jsonl`.

Known semantic-call cost recorded in the traces was USD 0.001032 for the failed run and USD 0.001277 for the successful run, excluding the latter's intent-router call whose provider cost was unavailable.

## 5. Root-cause analysis

The variability did not originate in the deterministic registry matcher. It occurred in the stochastic structured repair returned by the LLM.

In the failed run, the reviewer produced an internally inconsistent repair:

- terminal artifact: `sample_cluster_assignment`;
- granularity field: `unknown`;
- newly added evidence: `granularity=aggregate`.

Because `sample_cluster_assignment` has exactly one legal granularity (`aggregate`), the evidence was scientifically and ontologically specific, but the scalar field remained unknown. Strict validation correctly rejected the contradiction as `conflicting_evidence:granularity=aggregate`, and no workflow was selected. The successful run returned a shape that could be aligned to the same ontology and therefore reached the exact SAMBAR match.

Temperature 0 was already in force for the semantic interpreter and reviewer. Temperature 0 reduces sampling variation but does not guarantee identical provider outputs. Stability therefore has to come from deterministic validation and normalization of semantically equivalent structured outputs, not from lowering temperature further.

## 6. Implemented stability intervention

The deterministic repair boundary now resolves an `unknown` or artifact-illegal operation/granularity only when all of the following conditions hold:

1. a semantic review patch has been applied;
2. the artifact has already been selected; and
3. the artifact ontology permits exactly one value for that dependent field.

The artifact choice itself remains subject to strict evidence validation. Consequently, filling a uniquely entailed dependent scalar cannot make an unsupported artifact pass, and an unknown artifact cannot be completed by this mechanism. The normalization cannot choose an artifact or workflow and does not use task keywords. Directly conflicting scalar evidence is retired and reported.

The final guidance renderer was also corrected to suppress a shorter pathway-aggregation paragraph when a richer explanation for the same concern already covers gene-length normalization, patient-burden normalization, and pathway aggregation.

## 7. Post-intervention deterministic verification

| Verification layer | Result |
| --- | ---: |
| Focused routing, repair, registry, guidance, memory, and schema suite | 242 passed, 22 skipped |
| Exact replay of failed run `d0ebe7b1…` (`unknown` field plus `aggregate` evidence) | 1/1 exact; uniquely matched `run_sambar` |
| Alternate Q3 repair shape (known but artifact-illegal `sample_specific`) | 1/1 exact; uniquely matched `run_sambar` |
| Alternate Q3 repair shape (`unknown` field with omitted granularity evidence) | 1/1 exact; uniquely matched `run_sambar` |
| Unsupported-artifact safety boundary | Retained; dependent-field completion does not waive artifact evidence validation |
| Rich-versus-short explanation test | 1/1; one non-duplicated sparse-mutation explanation retained |
| Adversarial typed-memory fixture | 1/1 relevant SAMBAR episode retained; 2/2 incompatible PANDA/LIONESS-PANDA episodes excluded |
| Host full suite | 1,478 passed, 89 skipped, 1 xfailed, 15 environment-dependent failures |

The 15 host failures are caused by unavailable LangChain/OpenAI acceptance dependencies: 12 runnable tool-schema checks cannot load decorated tools, and 3 real-SDK/graph tests cannot import or initialize LangChain. No focused routing or guidance test failed.

The most recent complete Docker run before the final stability patch reported 1,542 passed, 35 skipped, 1 xfailed, and one unrelated descendant-process timeout. A post-patch Docker rerun did not reach pytest because dependency installation produced no progress for approximately 150 seconds and was interrupted; consequently, that earlier Docker count is not presented as a full-suite result for the final revision.

Deterministic replay demonstrates that the observed failure shape is now normalized consistently. It is not a substitute for a repeated live-model accuracy experiment.

## 8. Recommended post-intervention live experiment

Use the existing public `original-q3` scenario and keep the model, prompt/schema digest, temperature, timeout, and policy hash fixed. Run at least 30 independent trials if the result will be reported as a proportion; record exact-route success, semantic-validation success, repair rate, wrong-workflow rate, and unauthorized-execution rate.

For a paired pre/post corpus, report paired outcomes and an exact McNemar test. For each unpaired success proportion, report a Wilson confidence interval. Predefine failure as any of the following:

- no validated semantic outcome;
- a workflow other than `run_sambar` selected;
- PANDA or LIONESS-PANDA recommended for `mutation_matrix`;
- missing `sample_cluster_assignment` terminal artifact;
- unauthorized execution;
- missing any of the four scientific explanation stages.

The current attachment supplies only the pre-intervention observation \(1/2\). No post-intervention live success rate should be reported until those calls are explicitly authorized and completed.

## 9. Paper-ready summary

> Somatic mutation matrices are sparse and heterogeneous, making direct gene-level patient comparison unstable. SAMBAR corrects non-silent mutation counts for gene length and patient-specific cancer-associated mutation rate, then aggregates them into pathway scores while correcting for pathway size and multi-pathway gene annotation. In the original analysis of 5,805 primary tumours across 23 cancer types, pathway-level profiles covered a mean 84.2% of pathway features within a cancer type, compared with 54.8% coverage of cancer-associated genes. In two repeated live executions of an identical mutation-subtyping request, the pre-intervention NetZoo agent produced one exact SAMBAR route and one semantic-validation failure (50%; Wilson 95% CI, 9.45%–90.55%). Trace analysis localized the failure to an internally inconsistent LLM repair that returned `granularity=unknown` while simultaneously asserting `granularity=aggregate` in its evidence. A deterministic, artifact-ontology-bounded normalization was added, and an exact replay of the failed payload subsequently produced the unique `run_sambar` match. This replay establishes correction of the observed failure mechanism, but repeated post-intervention live trials are still required to estimate improved routing accuracy.

## 10. Primary references

1. Kuijjer ML, Paulson JN, Salzman P, Ding W, Quackenbush J. *Cancer subtype identification using somatic mutation data*. British Journal of Cancer. 2018;118:1492–1501. DOI: [10.1038/s41416-018-0109-7](https://doi.org/10.1038/s41416-018-0109-7).
2. NetZoo. *SAMBAR: Subtyping Agglomerated Mutations By Annotation Relations*. Official netZooR vignette: [method, equations, inputs, and example](https://netzoo.github.io/netZooR/articles/SAMBAR.html).
3. Original SAMBAR implementation: [documented R source](https://rdrr.io/github/mararie/SAMBAR/src/R/sambar.R).

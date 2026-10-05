# Held-out set 13 — does the reply recommend the workflows that fit the question first?

32 English research requests with labels, in `heldout.json`.

## How it was written

- A subagent wrote it with no access to the repository. It did not read, list or search any project file, did not run the assistant and did not call a model API. Its only sources were the brief (the 13 registered workflows, the label schema, the coverage rules and the list of scenarios to avoid) and its own scientific judgement.
- The labels come from the rules below, not from the assistant's reply rules. Nobody tuned them against any reply.
- A throwaway script in the session scratchpad built the items (`prompt` = `data_sentence + " " + purpose_sentence`). A second script validated them. It checked:
  - the JSON parses;
  - every prompt is the data sentence plus the purpose sentence;
  - every label and workflow name is from the allowed lists;
  - `recommended_subset` is a subset of `acceptable_candidates`, and is empty for causal, prediction and none purposes;
  - prompts are 29-45 words and contain no workflow name;
  - families share their data sentence exactly;
  - the family and standalone coverage rules hold;
  - acceptable sets respect the stated inputs: no motif/PPI workflows without a motif prior, no PUMA family without miRNA data, only the DRAGON family when two layers are on the same samples, and only per-sample workflows for individual questions.

  Fault injection confirmed that the validator catches each of these errors.
- Every prompt is in the voice of a researcher, names no workflow or tool and contains no file path. None reuses a tissue, condition and design combination from the earlier list.

## Families (one shared data sentence, four purposes each)

| Family | Data | Design | Items |
|---|---|---|---|
| A | Dairy-cow liver biopsies, 3 weeks before / 2 weeks after calving. **Expression only, said outright** ("only RNA-seq counts, nothing else") | paired before/after | A1 herd-level change · A2 which cows shifted most · A3 control (per-biopsy networks, no test) · A4 descriptive look, explicitly not a test |
| B | Head-kidney transcriptomes of 104 wild sticklebacks with sex, body length and lake recorded. **Expression implied** | single collection (covariates only) | B1 sex difference adjusted for length and lake · B2 which fish stand out · B3 control · B4 regulator question with no TF prior (trap) |
| C | Scalp biopsies from 22 alopecia areata patients before/after a JAK inhibitor. **Expression + TF motif + PPI** | paired before/after | C1 cohort-level network shift · C2 which patients changed most · C3 control (one aggregate network) · C4 which TFs are most affected, consistently across patients |
| D | Minor salivary gland RNA-seq, 48 Sjögren's vs 40 sicca controls. **Expression + TF motif + PPI** | two groups | D1 group difference with a statistical test · D2 which patients deviate most · D3 control (per-gland networks to deposit) · D4 descriptive side-by-side, explicitly not a test |
| E | Femoral bone from 30 ovariectomised vs 30 sham mice. **mRNA + miRNA, with TF motif, miRNA-target and PPI priors** | two groups | E1 group difference in the combined TF+miRNA network · E2 which ovariectomised mice deviate most · E3 control (one combined network) · E4 which miRNAs change most |
| F | RNA-seq + DNA methylation on the same 61 adrenocortical tumours (29 carcinomas, 32 adenomas). **Two omics layers** | two groups | F1 group difference in methylation-expression links · F2 which tumours are unusual · F3 control (one two-layer network) · F4 descriptive look, explicitly not a test |

## Standalone items

| Id | Scenario | What it probes | Recommended |
|---|---|---|---|
| T1 | Uveal melanoma primaries, metastasis status, motif + PPI | TF *activity* apart from the TF's own mRNA | GIRAFFE |
| T2 | Monocrotaline vs saline rat right ventricle, motif + PPI | TF *targeting/rewiring*, explicitly not activity | PANDA, LIONESS-PANDA, OTTER |
| T3 | Lactating goat mammary tissue, motif + PPI, no miRNA mentioned | per-sample TF network without drifting to the miRNA workflows | LIONESS-PANDA |
| T4 | Urticaria vs donor whole blood, "RNA-seq" only | cohort question with no priors named; must not assume motif/PPI | COBRA, LIONESS-COEXPRESSION |
| T5 | Nine children with a rare mitochondrial disorder, fibroblasts, nothing else | small cohort and per-edge confidence | BONOBO |
| T6 | Keloid vs normal skin, mRNA + miRNA with all three priors | quick descriptive two-group look, explicitly not a test | PUMA |
| T7 | Follicular lymphoma biopsies with progression records | prediction request; no workflow is itself a predictor | (empty) |
| T8 | Mesothelioma mutation calls *and* RNA-seq; "ignoring the expression data" | the RNA-seq is a distractor; the question is mutation-based | SAMBAR |

## Labelling rules applied

### Inputs (gate for `acceptable_candidates`)

A workflow is acceptable only when every input it needs is stated:

- **Motif + PPI priors:** PANDA, LIONESS-PANDA, OTTER, GIRAFFE.
- **Those priors plus miRNA data / a miRNA-target prior:** PUMA, LIONESS-PUMA.
- **Two layers on the same samples:** DRAGON, LIONESS-DRAGON. When the cross-layer link is the point, only this family is accepted.
- **Mutation calls:** SAMBAR.
- **An existing bipartite network:** CONDOR (no item states one).
- **COBRA:** needs covariates. Group labels or time points count as the minimal covariate table; a stated covariate table, such as B's, obviously counts.
- **Expression-only workflows** (LIONESS-COEXPRESSION, BONOBO, COBRA) fit any item with expression.

### Output fit (second gate)

The workflow's output, plus a standard downstream step, must answer the purpose. Examples of a standard step are a test on per-sample edges, or comparing runs made separately per group.

- **Cohort/group difference:** accepts:
  - per-sample workflows tested between groups or within pairs;
  - aggregate workflows run once per group;
  - COBRA.
- **Individual question:** per-sample outputs only (LIONESS-*, BONOBO, SAMBAR). GIRAFFE counts only when a per-sample TF-level answer suffices. It is excluded when the question asks for a per-sample *network*, because GIRAFFE's per-sample output is TF activity.
- **Regulator question:** needs TF or miRNA nodes. That means the PANDA family, OTTER or GIRAFFE, and only the PUMA family when miRNAs are named.
- **Wording of the network asked for:**
  - "Regulatory network" or "TF-to-gene" with priors stated excludes co-expression workflows.
  - Generic wording ("gene networks", "co-regulated") keeps them.
- **Granularity of the network asked for:**
  - A request for *one* network for the whole collection accepts aggregate workflows only (PANDA, OTTER, GIRAFFE's signed effects, PUMA, DRAGON).
  - A request for networks *per sample* accepts per-sample workflows only.

### `recommended_subset` (what a careful adviser puts first)

- **Inferential cohort-level difference** ("does it differ", "test", paired before/after): favour per-sample networks, because they give replicate-level variation and allow paired tests.
  - Motif/PPI data: LIONESS-PANDA.
  - miRNA data: LIONESS-PUMA.
  - Two layers: LIONESS-DRAGON.
  - Expression only: COBRA, plus LIONESS-COEXPRESSION. COBRA alone when adjustment for named covariates is asked (B1).
- **Descriptive look, explicitly not a test:** an aggregate network per group (PANDA/OTTER, PUMA, DRAGON), or COBRA when only expression is available.
- **Individual question:** the per-sample workflow that uses all the stated data. BONOBO comes first when the cohort is small or edge confidence is asked.
- **Regulator question:**
  - Activity: GIRAFFE.
  - Targeting: the PANDA-family workflows and OTTER.
  - Generic question with a paired or "consistent across patients" design: LIONESS-PANDA + GIRAFFE.
- **Empty when:**
  - the purpose is causal, prediction or none;
  - every acceptable workflow fits equally (the validator rejects `recommended == acceptable` when there is more than one acceptable workflow);
  - nothing is acceptable.

### Other labels

- **`comparison_design`** records the design the request *states*, from the data sentence or the purpose. Controls in paired or two-group families therefore keep `paired` or `groups` even when the purpose declines a comparison. `none` means no grouping or repeated measurement is stated (family B except B1/B4, T3, T5, T7, T8).
- **`claim_kind`:** descriptive comparisons (A4, D4, F4, T6) are labelled `group_difference`, not `none`. They still ask about a group or time contrast, only without inference. Their scope is carried by `recommended_subset`, `must_include` and `red_flags`. `is_control` is true only for the six family controls.
- **`is_negation_trap`:** an explicit negation that changes the right answer and that a careless reader would miss ("without any comparison or test", "not a formal test", "not whether they become more active", "ignoring the expression data").
- **`is_precision_trap`:** one precise detail decides between workflows that otherwise look interchangeable, for example:
  - covariate adjustment (B1);
  - no TF prior (B4, T4);
  - miRNA data present (E2);
  - activity vs mRNA (T1);
  - targeting vs activity (T2);
  - no miRNA (T3);
  - n = 9 with edge confidence (T5).

## Judgement calls I was unsure about

1. **Descriptive looks are `group_difference`, not `none` (A4, D4, F4, T6).** The brief lists them as the "one more" item, separate from the control, so I kept them out of `none` so that they can carry a recommendation. A grader that treats "no test wanted" as a control would disagree.
2. **Controls keep the stated design.** A3, C3 and D3 keep `paired`/`groups`, as do E3 and F3, although their purposes compare nothing. Labelling the design from the purpose alone would make these `none`.
3. **Per-sample networks are favoured over aggregate-per-group runs for inferential differences** (C1, D1, E1, F1). Running PANDA, PUMA or DRAGON per group with label permutation is also a valid test. That is why the aggregate workflows stay acceptable, but I would not fault a reply that leads with them *and* names a permutation test.
4. **COBRA with only group or time labels** (A1, A4, T4), and **COBRA in a paired design** (A1, A4), where pairing needs 26 cow indicators in the design matrix. I am not certain COBRA handles that well. That is why A1 recommends LIONESS-COEXPRESSION alongside it.
5. **A4: COBRA as the descriptive pick for expression-only before/after.** Averaging per-sample co-expression networks per time point is a reasonable alternative. COBRA won because it returns the time-associated co-expression directly, as one result.
6. **LIONESS-COEXPRESSION vs BONOBO is a tie unless the cohort is small or edge confidence is asked**, so A2 and B2 have empty recommendations. I treated 26 cows (52 biopsies) as not small. Someone who reads "small cohort" more generously would put BONOBO first in A2.
7. **B4 has an empty acceptable set.** Sticklebacks have no standard motif prior, and the request names none. Some advisers would accept co-expression hubs among TF genes as a weak proxy, or say a motif prior can be built by scanning promoters. I count the second as good advice, not as an acceptable workflow.
8. **Where GIRAFFE belongs.** It is acceptable when a TF-to-gene network or TF scores suffice (C1, C3, C4, D1, D4, T1, T2, T7), because its signed regulatory effects form a TF×gene matrix. It is excluded where per-sample *networks* are asked (C2, D2, D3, T3). The boundary is fine-grained.
9. **LIONESS-* is excluded from "one network" controls** (C3, E3, F3), even though LIONESS also returns the aggregate. I judged that recommending per-sample machinery for a single network misreads granularity.
10. **D2 accepts co-expression workflows** ("gene networks", generic) but recommends only LIONESS-PANDA, because the user supplied priors. C2 and E2 say "regulatory networks", so co-expression is excluded there. This hinges on one or two words.
11. **E4 (which miRNAs change most) has an empty recommendation.** PUMA per group with differential targeting, and LIONESS-PUMA, both rank miRNAs. By contrast, T2 recommends the three targeting workflows, because one acceptable workflow (GIRAFFE, activity-oriented) is clearly less fit there. The two items follow the same rule but look inconsistent side by side.
12. **T1 accepts PANDA-family targeting as an activity proxy** but recommends only GIRAFFE. A stricter reading would accept GIRAFFE alone.
13. **T7 is labelled design `none`.** Its acceptable set is LIONESS-PANDA and GIRAFFE, as generators of per-patient features. Arguably it should be empty, because no workflow predicts anything. Progressors vs non-progressors could also be read as `groups`.
14. **T8 is labelled `individual_change`.** It also asks whether patients form mutation-based subtypes, which is descriptive. I took per-patient pathway scores as the main ask.
15. **E2 accepts LIONESS-PANDA.** It delivers per-sample regulatory networks but ignores the miRNA data, so it is acceptable but not recommended. A stricter reading would drop it.
16. **C4 ("most affected", generic)** recommends both targeting (LIONESS-PANDA) and activity (GIRAFFE). Had the wording leaned towards either one, only one would be recommended.
17. **B1 recommends only COBRA.** Per-sample co-expression networks followed by a regression with length and lake as covariates also adjust. COBRA is first only because it does the adjustment in one step.
18. **T3's priors are "built for goat"**, to make motif/PPI plausible in a non-model species. A reader might doubt how good such priors are, but that does not change which workflow fits.
19. **T5 excludes LIONESS-COEXPRESSION from acceptable.** It gives no per-edge confidence, and leave-one-out with n = 9 is unstable. A lenient grader might accept it with a warning.
20. **Species skew.** 9 of the 14 data sentences are human. The rest are cow, stickleback, mouse, rat and goat.

# heldout6: held-out set for reading design and claim kind

32 prompts: 6 minimal-pair families of 4 prompts each (P1-P6), plus 8 standalone traps (T1-T8).

## How it was written

- A subagent wrote the set without access to the project. It did not open, list or search any project file, and it did not see the verification rules, the component's code or earlier evaluation sets. Its only inputs were the brief's label vocabulary, the tool registry (13 tools with their inputs) and the list of scenarios to avoid.
- Each family uses one data sentence, repeated word for word, with 4 different purpose sentences. The comparison design is set by the data sentence, so the design label is the same for all 4 prompts in a family. Every family has at least one control whose claim_kind is `none`.
- The prompts were written to read like grant aims, lab emails, sample sheets and reviewer requests, so they do not share a template. They mix "we have...", passive voice, "Data: ..." and "Each of N patients gave..." openings. Every prompt is one paragraph of 27-40 words.
- A script checked the following before the file was written: the JSON parses; every `prompt` equals `data_sentence + " " + purpose_sentence`; the data sentence is identical within each family; design coverage (paired 2, groups 3, none 1); every claim_kind appears at least twice in the families (group_difference 4, individual_change 4, regulator_change 3, causal 3, prediction 3, none 7); there are 3 negation traps and 5 precision traps; and no prompt names a tool.
- `is_control` is true only for family prompts whose claim_kind is `none`. It is false for every trap, including traps whose true claim is `none`.

## Families

- **P1 (paired, repeat visits; EXPR+MOTIF+PPI):** human bronchial brushings from smokers at enrollment and one year after quitting.
- **P2 (groups, case-control with matched controls; EXPR only):** whole-blood microarrays from ALS patients and age- and sex-matched controls.
- **P3 (paired, matched sites; EXPR+MIRNA+MOTIF+PPI):** a diseased and a healthy gingival biopsy from each periodontitis patient. This is the miRNA family.
- **P4 (groups, breeds/lines; EXPR+MOTIF+PPI):** chicken breast muscle from fast-growing broilers and slow-growing heritage chickens.
- **P5 (none, a single cohort; EXPR+MOTIF+PPI + survival):** primary glioblastoma resections with overall survival.
- **P6 (groups, dose groups; two omics layers):** mouse liver RNA-seq plus methylation arrays across four arsenic dose groups. This is the second-omics family.

## Traps

- **T1 (negation, prediction):** cholangiocarcinoma with survival data. Building a prognostic model is said to be "a colleague's project" (an indirect negation at the start of the purpose sentence), and the real goal is descriptive.
- **T2 (negation, causal):** sorghum, drought-stressed vs well-watered plants. A causal claim is ruled out at the end of the sentence, and the real goal is regulator_change.
- **T3 (negation, comparison):** nasal polyps from men and women aged 30-70. A sex or age comparison is ruled out mid-sentence, and the real goal is individual_change.
- **T4 (precision, "predicted"):** salmon gill with a "computationally predicted" binding-site prior. Here "predicted" describes the prior, not a goal.
- **T5 (precision, "driver"/"disrupt"):** somatic mutations in head and neck cancer, subtyped by the pathways hit by "driver mutations". The causal-sounding words do not express a causal goal.
- **T6 (precision, "paired-end"):** iPSC-derived neuron lines sequenced paired-end. There is no paired design, and the true claim is individual_change.
- **T7 (precision, "controls"):** horse blood microarrays with spike-in and negative control probes. "Controls" means array probes, not a control group.
- **T8 (precision, "pretreatment ... before chemoradiation"):** rectal cancer biopsies from a single time point before therapy. There is no before/after design and no goal of predicting response.

## Judgement calls I was unsure about

1. **P2 "age- and sex-matched controls" → `groups`.** Matching at the cohort level does not make samples paired, because the patients and controls are different people. A reviewer could argue for a matched-pair reading, but the prompt does not say the samples are paired one-to-one.
2. **P6 "each liver was profiled by RNA-seq and methylation array" → `groups`.** Both omics layers come from the same animals, but that is how a multi-omic method pairs its data, not the comparison design. The comparison is between dose groups of different mice.
3. **P2-d "each subject's co-expression network ... so the team can browse them" → `none`, not `individual_change`.** The request is to build per-sample networks. It does not ask which subjects differ most.
4. **P5-d "Which transcription factors act as the main hubs" → `none`, not `regulator_change`.** This mentions regulators but asks for no change or difference.
5. **P5-b, T3 and T6 ("most unlike the rest", "most atypical", "most unusual") → `individual_change` with design `none`.** I read "differ most from the cohort" as the individual-level claim even when no comparison structure is stated. A stricter reading would require a stated contrast.
6. **P6-a "coupling weakens as the dose rises" → `group_difference`.** I treated a trend across dose groups as a population-level change across conditions.
7. **P2-a "classify new, undiagnosed people" and P5-a "predict survival in an independent cohort" → `prediction`.** Both refer to unseen samples. P2-a is phrased as classifying rather than predicting.
8. **COBRA is listed as acceptable for P2-b and P2-c.** The case/control status is stated, so I treated it as an implied design table (COV). If COV must be given as an explicit table, remove COBRA from both items.
9. **Candidates for causal and prediction items.** Their lists name tools that could supply exploratory networks or features, while `must_include` says the causal or predictive step lies outside the suite. A stricter scheme would give these items empty lists.
10. **Co-expression description with no grouping (T7, P2-d).** No registered tool builds a single aggregate co-expression network from expression alone, so I accepted the per-sample co-expression tools (LIONESS-COEXPRESSION, BONOBO).
11. **T1 lists CONDOR.** It is acceptable only as a follow-up run on a TF-gene network built first from the stated priors. It is not acceptable as a first step.
12. **T8 "describe the transcription factor activity landscape" → `none`.** I read this as descriptive. It could also be read as asking how TF activity varies between tumours, which is close to `individual_change`.
13. **P4-c (woody breast prediction).** The data sentence states no woody-breast outcome labels. `must_include` asks the answer to point this out instead of assuming the labels exist.

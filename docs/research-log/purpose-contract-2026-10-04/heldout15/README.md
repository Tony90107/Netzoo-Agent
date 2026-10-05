# heldout15: labelled purpose-contract set (32 items)

## How it was written

A subagent wrote this set without access to the repository. It did not read, list or search any project file, did not run the assistant, and called no model API. The labels come only from the caller's brief: the list of 13 registered workflows, the label definitions, the coverage rules and the list of scenarios to avoid. The rest is the author's own scientific judgement.

Each prompt is a data sentence followed by a purpose sentence. The author built the items in a Python script (kept in the session scratchpad, not in the repo) and validated them before writing `heldout.json`. The script checks that:

- the JSON parses and every item has all 16 fields;
- `prompt == data_sentence + " " + purpose_sentence`;
- every label value comes from its allowed list and every workflow name is registered;
- `recommended_subset` is a subset of `acceptable_candidates` and is empty for prediction, causal and none;
- `recommended_subset` does not equal `acceptable_candidates` when more than one workflow is acceptable, because a full tie must be written as `[]`;
- `data_question` is either priors or none, and is priors only when the data sentence does not mention priors;
- motif/PPI workflows are not acceptable when the priors are ruled out, or when the priors are unstated and `data_question` is none;
- the PUMA family appears only when miRNA data are stated, and the DRAGON family only in the two-layer family;
- prompts are 29-45 words of ASCII with no workflow name;
- the four items of a family share their data sentence exactly;
- the family and standalone coverage rules hold.

A mutation test confirmed that each check fires. The set passed with no errors.

## Families (shared data sentence, four purposes each)

Each family has one item of each kind: group or cohort question (`group_difference`), individual question (`individual_change`), control (`none`), and TF/regulator question (`regulator_change`).

| Family | Data (what the sentence says about priors) | Design | Theme |
|---|---|---|---|
| A | "We RNA-sequenced ..." (priors not mentioned) | paired before/after | Abdominal fat from 10 adults before and after six months of semaglutide |
| B | "We have transcriptome profiles of ..." (priors not mentioned) | two groups | Hippocampus of rats with pilocarpine epilepsy (18) vs sham (15) |
| C | "... but no transcription factor motifs or protein interaction network" (priors ruled out) | single collection; group items split it by breeding origin | Leaf RNA-seq of 72 maize inbred lines from one field |
| D | "... plus a TF motif prior and PPI network" (priors stated) | paired before/after | Lymph node aspirates from 28 people with HIV, before and a year into antiretroviral therapy |
| E | "... plus TF binding-site predictions and a protein interaction map" (priors stated) | two groups | Kidney biopsies, FSGS (38) vs minimal change disease (27) |
| F | RNA-seq + DNA methylation on the same tissues (priors not mentioned) | paired, matched tissues | Tumour and adjacent normal endometrium from the same 34 women with endometrial cancer |

## Standalone items

- **T1**: Mouse hearts infected with *T. cruzi* vs uninfected cage mates ("bulk RNA-seq", priors never mentioned). Asks which TFs change their influence on target genes.
- **T2**: Lesional vs non-lesional discoid-lupus skin from the same 18 people ("RNA sequencing reads ...", priors never mentioned). Asks which TFs become most active.
- **T3**: Brains of urban vs forest brown anoles, with "no transcription factor motif or protein interaction resources" for the species. Asks a TF regulation question.
- **T4**: Blood microarrays from 44 pet cats with chronic kidney disease. Asks which cats' gene networks are unusual; expression-only workflows can answer it.
- **T5**: Blood RNA-seq from 10 adults with fibrodysplasia ossificans progressiva. Asks for each person's network with a confidence value for every edge.
- **T6**: Nasopharyngeal carcinoma vs non-cancer controls, with a TF motif prior, a PPI network and predicted microRNA-target pairs. Asks which miRNAs change their influence.
- **T7**: Pre-treatment small-cell lung cancer biopsies with priors and known platinum response. Asks to predict response for new patients.
- **T8**: Bone biopsies from women with and without osteoporosis, plus methylation arrays from a *separate* set of women. Asks for gene networks "using both data types". The trap is that the two layers are not on the same samples.

## Labelling rules applied

1. **`comparison_design`** follows the sampling design that the data sentence sets up. All four items of a paired or two-group family carry that design, controls included. In the single-collection family C, an item is "groups" when its purpose sentence creates a split, and "none" otherwise. Standalone items follow their own prompt.
2. **Gene-level vs TF-level questions.** "Gene networks", "coordination among genes" and "networks" are treated as gene-level questions, which expression-only workflows can answer. For these, `data_question` is none even when the priors are unstated, and motif/PPI workflows are not acceptable unless the priors are stated. TF-level questions ("transcription factors ... activity / targeting / rewired / influence", or a "regulatory network") need a motif prior. When the priors are unstated, `data_question` is priors and acceptability is judged as if the priors exist.
3. **Expression-only workflows (LIONESS-COEXPRESSION, BONOBO, COBRA) are never acceptable for a TF-level question.** They give gene-gene edges, not TF-to-target regulation. As a result, the two TF questions whose priors are ruled out (C4, T3) have no acceptable candidates.
4. **Cohort-level questions.** With expression only, COBRA is recommended first, because it tests covariate-linked co-expression across the cohort and can adjust for person or other covariates. With stated priors and two groups, PANDA and LIONESS-PANDA are recommended. With a paired design, only the per-sample variant is recommended (LIONESS-PANDA or LIONESS-DRAGON), so that the test can use the pairing.
5. **Wording decides between TF workflows.** "Activity" points to GIRAFFE. "Targeting", "rewired" and "influence on targets" point to PANDA and LIONESS-PANDA. "Activate or repress" points to GIRAFFE alone, because only it gives signed effects.
6. **Per-individual network questions with stated priors** recommend LIONESS-PANDA, because the request favours using the priors it states. GIRAFFE is not acceptable for "each person's network" questions: it gives per-sample TF activity, not per-sample networks.
7. **Ties.** When several workflows are acceptable and nothing in the request favours some of them, `recommended_subset` is `[]`. Examples are LIONESS-COEXPRESSION vs BONOBO in a cohort that is not small, and PUMA vs LIONESS-PUMA in T6. When only one workflow is acceptable, it is recommended.
8. **Cohort size** never removes a workflow from `acceptable_candidates` or `recommended_subset`. `size_preferred` lists BONOBO only when the stated number is a handful (family A, T5) and BONOBO is acceptable. It is always a subset of `acceptable_candidates`.
9. **Trap flags.** `is_negation_trap` marks the items whose priors are ruled out: all of family C, and T3. Phrases like "no comparison planned" in controls are not flagged. `is_precision_trap` marks items where one detail changes the right answer: E4 (activate/repress), F1 (matched tissue makes the design paired), F4 (a TF question despite the methylation layer), T5 (per-edge confidence), and T8 (the layers come from different women).
10. **`must_include` and `red_flags`** never ask the reply to call a cohort "small" or "large". The brief bars the assistant from inferring that from a number. Instead, "rules a workflow out because of the number of people" is listed as a red flag where it is tempting.

## Judgement calls I was unsure about

1. **Empty acceptable sets for C4 and T3** (TF question, priors ruled out). This follows from rule 3, but a reasonable alternative is to list LIONESS-COEXPRESSION, COBRA and BONOBO as proxies, read as "co-expression changes of the TF genes". I chose to put that substitute in `must_include` as an optional, clearly labelled fallback rather than count it as an acceptable answer. A scorer that treats any named workflow as a failure on these items would penalise a sensible reply that offers the proxy with caveats.
2. **Gene-level items with unstated priors get `data_question` none** (A1-A3, B1, B2, T4, T8). Someone could argue that LIONESS-PANDA would beat co-expression if the user had priors, so the best answer does depend on them. I decided that a question asked about genes is fully answerable without priors, so asking about them is unnecessary. The wording "gene networks" carries this call. A1 ("gene networks in the fat shift") is the weakest of these.
3. **COBRA is acceptable, and recommended first, whenever groups or time points are stated**, even though no prompt mentions a "covariate table". I assumed the group or time labels form the design matrix. Family C states "breeding-origin records" explicitly; A, B and T8 do not. In paired A1, LIONESS-COEXPRESSION with a paired test is about as good as COBRA with person as a covariate. I left it out of the recommendation only because naming it without BONOBO would narrow the choice on cohort size, which rule 8 forbids.
4. **For paired designs, only the per-sample variant is recommended** (D1, D4, F1, F4). One aggregate network per condition (PANDA, DRAGON) is acceptable but ignores the pairing. Some advisers would recommend both.
5. **GIRAFFE counts as delivering a "regulatory network"** in the B3, D3 and E3 controls and in the D1 and E1 group questions, through its signed TF-gene effects. It is excluded from the per-person network questions D2 and E2. That boundary is my reading of the one-line workflow description.
6. **In E4, PANDA, LIONESS-PANDA and OTTER stay acceptable** although they cannot say whether a TF activates or represses. They answer the main "which TFs differ most" part. GIRAFFE alone is recommended. A stricter labeller would make GIRAFFE the only acceptable workflow.
7. **For "activity" questions (A4, T2), only GIRAFFE is recommended.** Per-sample LIONESS-PANDA out-degree is often used as a targeting or activity proxy, so ["GIRAFFE", "LIONESS-PANDA"] would also be defensible.
8. **T5 accepts only BONOBO**, because the question asks for confidence on every edge and LIONESS-COEXPRESSION has no built-in per-edge p-values. Permutation tests could add them, so a lenient labeller might accept LIONESS-COEXPRESSION.
9. **T6 accepts only the PUMA family, with `recommended_subset` set to `[]`** as a two-way tie. The data are miRNA target predictions, not miRNA expression, so DRAGON on mRNA plus miRNA does not apply. If a reader takes "miRNA data" to include small-RNA sequencing, that decision changes.
10. **T7 (prediction)** lists per-sample feature generators as acceptable: LIONESS-PANDA, GIRAFFE, LIONESS-COEXPRESSION and BONOBO. None of them predicts anything by itself, so an empty list is the other reading. I labelled the design "groups" (responders vs non-responders), although "none" is arguable for a prediction task.
11. **Controls in paired or two-group families keep the family design.** D3 is paired. E3 is groups even though it asks for one network pooling both diagnoses. F3 is paired even though it pools tumour and normal. A labeller who reads `comparison_design` as "the comparison the request asks for" would mark all six controls "none".
12. **B3 is a control with `data_question` priors.** It asks only for one "regulatory network" per group, but a TF-to-gene network still needs a motif prior, so the reply should ask. It is the only control where asking is correct.
13. **Family C uses design "none" for its individual and control items**, and "groups" for its group and TF items, which split the lines by tropical vs temperate origin. The family therefore has no single design value.
14. **`size_preferred` thresholds.** Family A (10 adults, 20 biopsies) and T5 (10 adults) get BONOBO. T1 (14 vs 12 mice) and T2 (18 people) get nothing. T1's TF question cannot use BONOBO anyway. The cut-off between "a handful" and "enough" is my own.
15. **"Rewired" (B4, C4) and "influence on target genes" (T1)** are read as changes in TF targeting, not as activity. That reading is why PANDA and LIONESS-PANDA are recommended rather than GIRAFFE.
16. **Scenario overlap.** I checked every scenario against the avoid list by tissue, condition and design. The nearest overlaps are endometrial cancer vs the excluded "endometriosis endometrium" (same organ, different disease and design) and HIV lymph nodes vs the excluded "sarcoidosis lymph nodes" (same tissue, different disease and design).

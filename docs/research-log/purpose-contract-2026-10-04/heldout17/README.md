# heldout17: 32 labelled requests (prior reading, purpose fit, asking about priors)

## How it was written

A subagent wrote this set in isolation. It read no repository file, did not run the assistant and called no model API. It worked only from the brief: the list of 13 registered workflows, the label definitions, the coverage rules and the list of scenarios to avoid. All labels come from the author's own scientific judgement of each request.

Before the files were written, a throwaway script built the items and a second script validated them. The validator checked these things:

- the JSON parses, and `prompt` == `data_sentence + " " + purpose_sentence`;
- every enum value and workflow name comes from the brief;
- `recommended_subset` is a subset of `acceptable_candidates`, and it is empty for causal, prediction and none purposes;
- `data_question` is "priors" only when `priors_stated` is "unstated";
- prompts are 29-45 words, and no prompt names a workflow;
- the rules about which inputs a workflow needs hold: motif/PPI workflows are absent when priors are ruled out, PUMA appears only with miRNA, the DRAGON family only with two layers;
- each family shares one data sentence and one `priors_stated` value;
- the family and standalone coverage rules hold.

The validator was itself checked with deliberately broken copies (7 mutations, all caught). The final file passes with 0 errors and 0 warnings.

## Families (shared data sentence; four purposes each: cohort/group, individual, control, TF-level)

| Family | Scenario | Priors | Design | Notes |
|---|---|---|---|---|
| A | Blood RNA-seq, 24 sleep-apnoea patients before/after 3 months of CPAP | stated, in unusual words ("promoter motif-scan table linking regulators to genes", "curated protein contact map") | paired before/after | |
| B | Hoof lamellar transcriptomes, 16 laminitic vs 16 sound horses | stated, in unusual words ("position-weight-matrix hits for regulators near each gene", "equine interactome of protein complexes") | two groups | |
| C | Blood RNA-seq counts, 14 Tasmanian devils with facial tumours vs 14 healthy | ruled out, with a negation ("beyond that table, nothing on regulator binding or protein interactions exists for this species") | two groups | |
| D | Wound-edge biopsies, 10 venous leg-ulcer patients before/after 4 weeks of compression | ruled out with no negation word, "only" or "just" anywhere in the four prompts ("the resulting RNA-seq count matrix is our entire dataset") | paired before/after | 10 patients, so `size_preferred` = BONOBO |
| E | Poly-A transcript sequencing of milk-derived cells from 48 breastfeeding mothers, with age, BMI and days since delivery recorded | unstated | single collection | E1 splits it into early vs later lactation, so `groups` |
| F | 30 AF vs 30 sinus-rhythm patients; each right atrial appendage sample has whole-transcriptome reads and a methylation array | unstated | two groups | two omics layers on the same samples |

In each family, item 1 is the cohort/group question, item 2 the individual question, item 3 the control (claim "none") and item 4 the TF-level question.

## Standalone items

- **T1**: Microarray profiles of temporal-artery biopsies (giant cell arteritis vs normal biopsies). TF activity/targeting question. Priors unstated, so `data_question` = priors.
- **T2**: 3-prime tag counts from coffee leaves before/after leaf-rust inoculation. Asks which TFs "switch on or off" (paired). Priors unstated, so `data_question` = priors.
- **T3**: Midgut RNA from insecticide-resistant vs susceptible Colorado potato beetles. Priors are ruled out by "motif and protein-interaction resources for this species remain unbuilt, so the read counts are all we have", with no no/not/none/without/only. Acceptable is empty.
- **T4**: Cat left ventricles with hypertrophic cardiomyopathy. Has a JASPAR prior and STRING network, followed by "though no echocardiography or survival data were recorded" (a negation about something else). Per-cat question.
- **T5**: Five progeria vs five healthy children's fibroblasts. Asks how much to trust each edge in each child's network → BONOBO only.
- **T6**: Retinal mRNA + small RNA from oxygen-induced-retinopathy mice vs room-air controls, with TargetScan, JASPAR and STRING. Asks which microRNAs change most "with mice as replicates" → LIONESS-PUMA recommended.
- **T7**: Night-shift vs day-shift nurses' blood, with priors stated. A causal claim ("show that night work causes ...").
- **T8**: Fibromyalgia vs control blood RNA-seq, with methylation arrays from a *separate* patient-only cohort. Asks about methylation-expression coupling. This is the trap: a careless adviser would recommend DRAGON. Acceptable is empty.

## Labelling rules applied

1. **Inputs.** Motif/PPI workflows are PANDA, LIONESS-PANDA, OTTER, GIRAFFE, PUMA and LIONESS-PUMA. Expression-only workflows are LIONESS-COEXPRESSION and BONOBO. COBRA needs a covariate table; I treated known group or time labels (and recorded covariates) as satisfying it. DRAGON and LIONESS-DRAGON need two layers from the same samples. PUMA and LIONESS-PUMA need miRNA targets or a miRNA list.
2. **How priors status sets acceptability.**
   - `ruled_out`: no motif/PPI workflow is acceptable.
   - `unstated` + `data_question` "priors": judged as if the priors exist.
   - `unstated` + `data_question` "none": judged as if they do not.
3. **Purpose wording.**
   - A neutral "network" purpose can be met by co-expression networks too, so they stay acceptable alongside the TF→gene ones.
   - A "regulatory network" purpose (E3, T4) needs TF→gene edges.
   - A TF/regulator-level purpose needs regulator-level output: TF→gene edges, TF activity or miRNA edges.
   - GIRAFFE counts only where TF activity or regulators are asked about, not where per-sample *networks* are.
   - Aggregate-network controls accept only PANDA and OTTER (or DRAGON for the two-layer family).
4. **Standard acceptable sets.**

   | Purpose | With priors | Without priors |
   |---|---|---|
   | Group/cohort difference | PANDA, LIONESS-PANDA, OTTER, COBRA, LIONESS-COEXPRESSION, BONOBO | COBRA, LIONESS-COEXPRESSION, BONOBO |
   | Individual | LIONESS-PANDA, LIONESS-COEXPRESSION, BONOBO | LIONESS-COEXPRESSION, BONOBO |
   | TF-level change | GIRAFFE, LIONESS-PANDA, PANDA, OTTER | none |

   For TF-level questions about variation from one individual to another (E4), only the per-sample options apply: GIRAFFE and LIONESS-PANDA.
5. **Recommended.**
   - Group difference: PANDA + LIONESS-PANDA with priors, COBRA without (COBRA is the cohort-level, covariate-adjusted answer).
   - Individual: LIONESS-PANDA with priors.
   - TF activity wording → GIRAFFE. TF targeting/rewiring wording → PANDA + LIONESS-PANDA. Generic TF wording → GIRAFFE + LIONESS-PANDA.
   - "Each patient/mouse as a replicate" favours the LIONESS variant (F1, T6).
   - When the acceptable workflows are all equally good, recommended is empty. This happens for C2, D2 and the per-sample controls: LIONESS-COEXPRESSION vs BONOBO, which differ mainly by cohort size, and cohort size may not narrow the recommendation.
   - For `data_question` "priors" individual items (E2), recommended lists the top pick for each case: LIONESS-PANDA if priors exist, LIONESS-COEXPRESSION if not.
6. **`data_question`** is "priors" only when the best pick changes with the priors (E2, E3, E4, F4, T1, T2). It is "none" for unstated items whose answer is the same either way: E1 (COBRA), F1-F3 (DRAGON family), T5 (BONOBO) and T8 (nothing fits).
7. **`comparison_design`** comes from how the samples were collected, including for controls. The one exception is E1, where the purpose splits a single collection into groups.
8. **`size_preferred`** = BONOBO when fewer than 12 individuals are stated (D family, T5), and only where BONOBO is acceptable.
9. **Trap flags.**
   - `is_negation_trap`: reading the priors correctly means not keying on negation words. That covers priors ruled out without any negation word (D1-D4, T3) and priors stated next to an unrelated negation (T4).
   - `is_precision_trap`: a surface cue tempts a workflow that cannot run on the stated inputs or cannot give the asked result. The items are C4, D4 and T3 (TF wording without priors), T5 (per-edge confidence), T6 (TF-only workflows for a miRNA question), T7 (a causal claim) and T8 (unmatched methylation).

## Judgement calls I was unsure about

1. **Ruled-out TF-level questions (C4, D4, T3) have no acceptable workflow.** I judged that co-expression of TF genes cannot say which regulators change their targeting or activity. A good reply may still mention LIONESS-COEXPRESSION as a clearly labelled weaker substitute; a scorer may want to tolerate that. I also ignored that a motif prior could be built from public or orthologous motifs (JASPAR). The brief says ruled-out priors make motif workflows unacceptable, so I put that idea only in `must_include` as something the reply may explain.
2. **The causal item T7 still lists association-level TF workflows as acceptable** (GIRAFFE, LIONESS-PANDA, PANDA, OTTER), with an empty recommended list. You could argue acceptable should be empty for causal purposes.
3. **E1 has `data_question` "none".** I judged COBRA the right answer for a covariate-adjusted cohort comparison whether or not priors exist. A reviewer could argue that, with priors, LIONESS-PANDA networks regressed on covariates is equally good. If so, the answer depends on priors and E1 should be "priors".
4. **COBRA is acceptable for every group or time comparison.** I treated group or time labels as a design matrix, and for paired designs (A1, D1) assumed patient terms in the design. Whether a two-level label alone counts as the "covariate table" the brief describes is debatable.
5. **Asymmetric group-difference recommendations.** With priors I recommend PANDA + LIONESS-PANDA, not COBRA. Without priors I recommend COBRA alone, not LIONESS-COEXPRESSION. Both choices rest on judging what the most direct cohort-level answer is.
6. **Co-expression workflows count as acceptable for neutral "network" purposes even when priors are stated** (A1, A2, B1, B2). They would be excluded under a "regulatory network" wording. This makes acceptable depend on a single word in the purpose.
7. **GIRAFFE is excluded from individual "network" questions** (A2, B2, E2, T4) because it returns TF activity per sample, not a network per sample. A lenient reader could accept it for "what makes each one stand out".
8. **E4 is labelled `regulator_change`.** It asks which TFs vary most between mothers in a collection with no conditions, so it could be read as `individual_change`. It is also a "change" across people, not across conditions.
9. **T2's "switch on or off"** could be read as TF mRNA up or down (plain differential expression) rather than inferred TF activity. I labelled it TF activity → GIRAFFE.
10. **T5 is labelled `individual_change`.** Half of the question is about edge confidence, which is descriptive. Only BONOBO is acceptable because only it gives per-edge p-values; LIONESS-COEXPRESSION would answer the second half alone.
11. **Controls keep the data's design** (A3 and D3 "paired", B3, C3 and F3 "groups") even though they ask for no comparison. If the design label should describe what the request asks for rather than the data, those would be "none".
12. **The small-cohort threshold** (fewer than 12 individuals) is taken from the brief's T5 wording. D has 10 patients but 20 samples; I counted individuals.
13. **The "unusual" prior wordings may be too unusual.** "Interactome of protein complexes" (B) is complex membership, not strictly pairwise PPI. "Position-weight-matrix hits for regulators" and "promoter motif-scan table linking regulators to genes" say regulators, not explicitly transcription factors; I read motif scans as TF priors.
14. **T8 has no acceptable workflow.** An expression-only group comparison (e.g. COBRA) would answer a related question, but not the coupling question asked. Note also that the methylation cohort is patients only.
15. **Species priors.** I labelled T4 (cat) and T6 (mouse) as having usable JASPAR/STRING priors because the requests say so. I labelled C (Tasmanian devil) and T3 (beetle) as having none because the requests say so, even though orthology-based priors exist in principle.
16. **F4 depends on priors only for the RNA layer.** The methylation layer cannot answer a TF-rewiring question, so I left DRAGON out rather than counting it as a partial answer.

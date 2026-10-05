# heldout18: priors-reading evaluation set (32 items)

## How it was written

A subagent wrote this set on its own, using only the task brief: the list of registered workflows, the label schema, the coverage rules and the list of scenarios to avoid. It did not read, list or search any repository file. It did not run the assistant or call any model API. Every label comes from the author's own scientific judgement about each request. Before the file was written, a throwaway validation script (in the session scratchpad, not committed) checked the following:

- the JSON parses;
- `prompt` equals `data_sentence + " " + purpose_sentence`;
- every enum value and workflow name is on the allowed lists;
- `recommended_subset` is a subset of `acceptable_candidates`, has at most three entries, and is empty for causal, prediction and none purposes;
- `data_question` is "priors" only when `priors_stated` is "unstated";
- prompts are 29-45 words, name no workflow (whole-word match, any case) and contain no paths;
- families share their data sentence word for word and share `priors_stated`;
- no motif or PPI workflow is acceptable when priors are ruled out, or when priors are unstated and `data_question` is "none";
- the PUMA family appears only when miRNA data are stated, and the DRAGON family only on the one same-sample two-layer item;
- the coverage rules hold: 2 families each of stated, ruled_out and unstated priors; one ruled_out family with no negation word or "only"; at least 2 paired families, at least 2 two-group families and 1 single collection; and the T1-T8 constraints.

The checks passed on the first run. Prompts run from 33 to 43 words.

## Families (4 items each: group, individual, control, TF-level)

| Family | Data | Design | Priors | How the priors are worded |
|---|---|---|---|---|
| A | Synovial fluid leukocytes, 24 gout patients, flare vs remission | paired | stated | "promoter scans of transcription factor binding sites and a map of factor-factor protein contacts" (never says motif, prior or PPI) |
| B | Thyroid tissue, 28 Hashimoto's thyroiditis vs 24 nodular goitre | groups | stated | "JASPAR-derived regulator-to-target pairings and a STRING list of interacting protein partners" (database names, no method words) |
| C | Cassava leaves, 18 brown-streak-infected vs 18 healthy | groups | ruled_out | "we hold nothing on transcription factor binding or protein contacts for this crop": the prior names appear, but negated |
| D | Rosacea facial skin, 10 patients before/after 12 weeks of ivermectin | paired | ruled_out | "these expression counts are everything we have": no negation word, no "only" |
| E | Beef cattle pituitary glands, 64 animals at slaughter, sex and age recorded | single collection (E1 brings in heifers vs steers) | unstated | sequencing described as "poly(A)-selected Illumina libraries" |
| F | Varicose vs healthy saphenous vein segments from 26 patients | paired (matched tissues) | unstated | sequencing described as "full-length cDNA read on a nanopore flow cell, counted reads per gene" |

Family E is the "unstated, but the question does not depend on priors" case. E3 explicitly asks for co-expression ("which genes rise and fall together"), so its `data_question` is "none". In Family F every item depends on the priors, the one-network control F3 included.

## Standalone items

- **T1**: equine asthma BAL cells vs healthy horses, 3-prime tag sequencing. Asks which TFs shift regulatory activity. Priors unstated, so ask about priors.
- **T2**: juvenile dermatomyositis blood on Affymetrix arrays, diagnosis vs one year. Asks which TFs gain or lose targets. Priors unstated, so ask about priors.
- **T3**: Pacific oyster mantle, heatwave vs ambient. "Expression counts are the full extent of our data" rules the priors out without no, not, none, without, only, never or nothing. TF-level question, so nothing is acceptable.
- **T4**: aplastic anaemia marrow before/after immunosuppression. Says "we did not profile microRNAs, but we do have a JASPAR motif prior and a STRING protein network", so the negation is about miRNA and the priors are stated. Individual question.
- **T5**: nine children with glycogen storage disease Ia. Asks for each child's network with a confidence value for every edge. BONOBO only.
- **T6**: mycosis fungoides lesions vs normal skin, mRNA plus small RNA, with TargetScan targets, JASPAR and STRING. Asks which microRNAs change influence.
- **T7**: depression blood at SSRI baseline, with priors stated. Asks for a model predicting remission (prediction).
- **T8**: testicular germ cell tumours: RNA-seq on 44 tumours, methylation arrays on 38 *different* tumours. Wants a joint two-layer network. A careless adviser would offer DRAGON, but the layers do not come from the same samples.

## Labelling rules applied

**Inputs**

- The motif/PPI workflows are PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER and GIRAFFE. They are acceptable when priors are stated, or when priors are unstated and `data_question` is "priors".
- Expression-only workflows (LIONESS-COEXPRESSION, BONOBO) are always input-feasible.
- COBRA is feasible whenever the request has a group, time point or recorded covariate to put in a design matrix.
- CONDOR and SAMBAR never fit, because no request gives an existing bipartite network or mutation calls.

**Group difference**

- With priors, acceptable = PANDA and OTTER (one per group), LIONESS-PANDA, GIRAFFE, COBRA, LIONESS-COEXPRESSION and BONOBO. Co-expression counts as a gene network even when the purpose says "regulatory".
- Recommended:
  - [LIONESS-PANDA, PANDA];
  - [LIONESS-PANDA, COBRA] when the request names covariates to adjust for.
- Expression only: acceptable = COBRA, LIONESS-COEXPRESSION, BONOBO. Recommended = [COBRA], the workflow whose output is the cohort-level answer.

**Individual change**

- With priors, acceptable = LIONESS-PANDA, GIRAFFE, LIONESS-COEXPRESSION, BONOBO. Recommended = [LIONESS-PANDA].
- Expression only, acceptable = LIONESS-COEXPRESSION and BONOBO. Recommended is empty because nothing but cohort size separates them, and size does not narrow the recommendation.

**Regulator change**

The output must contain regulators as regulators, meaning a TF or miRNA layer or TF activity.

- With priors and a comparison: acceptable = PANDA, LIONESS-PANDA, OTTER, GIRAFFE.
- With priors and variation across a single collection: acceptable = LIONESS-PANDA, GIRAFFE.
- Recommended depends on the wording:
  - "activity": [GIRAFFE];
  - "targets": [LIONESS-PANDA, PANDA];
  - generic: [GIRAFFE, LIONESS-PANDA].
- Co-expression workflows are never acceptable here, so a TF-level question with priors ruled out has no acceptable candidates.
- For miRNA regulators (T6): acceptable = PUMA, LIONESS-PUMA, DRAGON and LIONESS-DRAGON (mRNA and small RNA come from the same samples). Recommended = [LIONESS-PUMA, PUMA].

**Controls**

- "One regulatory network" with priors: acceptable = PANDA, OTTER, GIRAFFE. Per-sample LIONESS output is excluded as more than was asked for.
- "A network per sample" or "genes that co-vary" with expression only: acceptable = LIONESS-COEXPRESSION, BONOBO.
- Recommended is always empty.

**Priors-dependent items**

When `data_question` is "priors", `recommended_subset` is the union of the first choice in each branch. For example, [LIONESS-PANDA, COBRA] for a group question.

**Prediction and causal**

None of the workflows delivers a predictor or a causal estimate, so acceptable is empty (T7).

**Other fields**

- `size_preferred` = [BONOBO] when the stated cohort has fewer than about 12 individuals and BONOBO is acceptable (D1-D3, T5). Otherwise it is empty, since nothing else in the brief prefers a workflow by sample count.
- `comparison_design` describes the whole prompt. A control item in a two-group or paired family keeps that family's design. In the single-collection family, only E1 is "groups", because its purpose brings in the heifer/steer split.
- `is_negation_trap` is true when the priors status turns on an explicit or implicit negation or exclusivity statement, or when a nearby negation about something else could be misapplied. That covers C1-C4, D1-D4, T3 and T4.
- `is_precision_trap` is true when a plausible-looking recommendation falls outside the acceptable set. That covers C4, D4, E3, T3, T4, T5, T6, T7 and T8.

## Judgement calls I was unsure about

1. **No proxies for TF-level questions.** C4, D4 and T3 have empty acceptable sets. I counted co-expression of TF genes as not answering "which TFs change their influence/targets". A reply that offers LIONESS-COEXPRESSION as an explicit proxy would be marked imprecise. A more lenient grader could reasonably accept it. Public motif priors (for example from JASPAR) could also be built, but the brief makes motif workflows unacceptable once priors are ruled out.
2. **T7 prediction has an empty acceptable set.** For consistency with call 1, I did not treat per-sample networks as acceptable even though they could supply features. The must_include line lets the reply *mention* them as candidate features. A grader that counts any mention as a recommendation would mark that reply imprecise.
3. **Co-expression is acceptable for group and individual questions worded "regulatory network" or "gene regulation"** (A1, A2, B1, B2, E1, E2, F1, F2, T4). This keeps COBRA and the per-sample co-expression workflows acceptable, and it is why the unstated families have a no-priors branch. A stricter reading would drop them when priors are stated.
4. **GIRAFFE in group and individual acceptable sets.** Its per-sample TF activity can be tested between groups or tracked per individual, but it is not a per-sample network. I included it generously and never recommended it for network-level questions.
5. **"One network" controls exclude LIONESS-PANDA** (A3, B3, F3) even though it also outputs the aggregate. Recommending per-sample networks here felt like adding work that was not asked for, but it is arguable.
6. **DRAGON family in T6.** mRNA and small RNA from the same lesions form two omics layers. The partial-correlation network has miRNAs as their own nodes, so I counted it as able to show which miRNAs' links change, though it is not directional. I recommended only the PUMA pair.
7. **Recommendations for priors-dependent items** are the union of the first choice in each branch, such as [LIONESS-PANDA, COBRA]. Another reasonable convention would list only the with-priors branch.
8. **C wording.** "We hold nothing on transcription factor binding or protein contacts" names the prior types inside a negation. It is a deliberate keyword trap, but it is a more ordinary negation than D's.
9. **D wording.** "These expression counts are everything we have" could be read as being about measured data only, leaving open whether public priors could be downloaded. I labelled it ruled_out, following the brief's "it has only expression data, in any words". T3's "the full extent of our data" raises the same question.
10. **Data-question calls.** E3 is "none" because the user asks explicitly for co-expression, and T5 is "none" because only BONOBO gives per-edge confidence. In both cases the priors could not change the answer. F3, the one-regulatory-network control, is "priors" because a TF-gene network needs them. Controls have no recommended subset, so these calls only test whether the assistant asks.
11. **T5 excludes LIONESS-COEXPRESSION** because it gives no per-edge confidence, not because of the small cohort. Someone could argue it partly answers "how each child's network differs".
12. **T8 acceptable is empty.** Analysing each layer separately is sensible advice, but the purpose explicitly asks for one joint two-layer network, which no workflow can give from unmatched samples.
13. **Size threshold.** I treated 10 patients (D) and 9 children (T5) as small, and 22-27 individuals per arm as not small. Any cutoff between about 12 and 20 is defensible.
14. **Comparison design for controls.** A3, B3, C3, D3 and F3 keep their family's data design ("paired" or "groups") even though the purpose asks for no comparison. If the grader expects "none" for purposes with no comparison, these five labels will disagree.
15. **Species with sparse public priors.** Cassava, oyster, horse and cattle may have thin motif or PPI resources. That does not change any label, because labels follow what the request says it has. It could make the unstated horse and cattle items (T1, E-family) harder for an assistant that knows the resource landscape.

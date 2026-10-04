# Held-out set 4 (comparison design focus)

## How it was written

A subagent wrote this set from the task brief alone. It did not open, list or search any project file, witness list, rule, earlier held-out set or agent output, and it did not run the agent or call a model. A scratchpad script built `heldout.json` and checked it before the file was written here. The checks were:

- the JSON parses;
- every `prompt` equals `data_sentence + " " + purpose_sentence`;
- the ids and labels use the allowed vocabulary, and every candidate is a registered tool;
- all coverage rules hold;
- each prompt is 32-41 words long;
- no prompt names a tool.

The set has 32 prompts:

- 6 minimal-pair families (K1-K6) of 4 prompts each. The data sentence is shared word for word within a family, so the design label is the same for all 4 prompts. Only the purpose sentence changes, and with it the claim label.
- 8 standalone traps: T1-T3 are negation traps and T4-T8 are precision traps.

Coverage:

- Family designs: 3 paired, 2 groups and 1 none.
- Family claims: each non-`none` kind appears 3-4 times, plus 6 controls.
- Whole set: 13 paired, 10 groups and 9 none.

Each family states its design in a different way. The phrasings are a crossover, dose levels, repeated visits, sample-sheet column names, a registry and split samples.

## Family themes

- K1 (paired): a diet crossover in human blood. Adults ate a high-salt and a low-salt diet "in random order", and the word "crossover" never appears. Expression only.
- K2 (groups): rice roots at four cadmium concentrations ("six plants per level"). TF motif and PPI priors.
- K3 (paired): blood from pregnant women taken "once in each trimester", run on microarrays. TF motif, PPI and miRNA-target priors.
- K4 (groups): a Treg count matrix whose design appears only in column names (WT_1.., Ezh2cKO_1..) plus "one mouse each". TF motif and PPI priors.
- K5 (none): 480 lymphoma biopsies from a national registry with no comparison stated. TF motif and PPI priors.
- K6 (paired): donor liver slices, each split into a TGF-beta half and a medium half. TF motif and PPI priors.

## Trap themes

- T1 (negation, prediction): lupus patients vs healthy donors. The purpose opens by declining a diagnostic classifier.
- T2 (negation, comparison): tuberculosis blood. The data sentence says there is no control group and nobody was resampled.
- T3 (negation, causal): symptomatic vs asymptomatic carotid plaques. The purpose ends by disclaiming causation.
- T4 (precision, design): "paired-end" and "read pairs" in a single-group tumor cohort.
- T5 (precision, design): biopsies taken "before" neoadjuvant therapy, but only that one time point exists.
- T6 (precision, design): "compare the networks" means comparing two motif priors on one cohort, not comparing groups of samples.
- T7 (precision, design): mouse pups from nine litters. Litter is a blocking factor here, not a comparison.
- T8 (precision, claim): "predict the target genes" means network inference, not outcome prediction. The design is really paired: the same macaques are sampled over a time course.

## Judgement calls to review

1. **COBRA in K1.** No covariate table is supplied, but the crossover fully defines the covariates (diet and subject). I counted COBRA as acceptable because that table can be built from the design.
2. **Causal labels on experimental designs (K1-c, K4-b, K6-d).** A randomized crossover, a knockout and a split-sample treatment can each support a causal statement about the intervention's effect on expression. I still labelled these `causal`, because the user wants to establish causation. `must_include` asks for that nuance instead of a flat refusal. K4-b ("directly") and K6-d ("through specific transcription factors") ask for mechanism, which networks cannot show.
3. **K2 dose levels.** I labelled them `groups` (separate plants at each level), not a continuous design. K2-a ("as cadmium concentration rises") is labelled `regulator_change`.
4. **K3 three time points.** I labelled the design `paired`: the same women are measured under more than two conditions.
5. **Prediction prompts without stated outcomes (K3-d preeclampsia, K5-b survival).** The outcome labels are not in the data sentence. A good answer should say they are needed.
6. **K4 sample sheet.** "One mouse each" is the only thing that rules out pairing WT_n with Ezh2cKO_n. Without it, the design could be read either way.
7. **T7 litters.** I labelled the design `none` because nothing is compared across litters. Litter is a grouping structure, though, and in other wordings (for example knockout vs wild-type littermates) it would define groups.
8. **T8.** The design is `paired` (the same nine animals over five days), and the claim is `none` despite the word "predict".
9. **T2 and T5.** Both are `none` designs; T2 is also labelled `individual_change` and T5 is labelled `none` for its claim. T5's "before ... began" mimics a before/after design, but no post-treatment sample exists.
10. **Candidate lists.**
    - I included GIRAFFE (per-sample TF activity) as acceptable for individual-level and prediction purposes.
    - K6-a (one network per sample) accepts only LIONESS-PANDA.
    - K3-c (one combined TF + miRNA network) accepts only PUMA. K3-a (which miRNAs change) excludes the TF-only tools.

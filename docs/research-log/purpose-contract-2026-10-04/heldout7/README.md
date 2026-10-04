# heldout7: purpose-contract held-out set

## How it was written

A subagent wrote this set from the task brief alone. It did not open, list or search any project file, run the agent or call a model API. The only files it touched were these two outputs. It wrote the prompts the way users write requests (papers, grant aims, sample sheets, lab emails), without any knowledge of how the component parses them. A generator script in the subagent's scratchpad, outside the repo, built `heldout.json` and checked the following before writing it:
- the JSON parses;
- every `prompt` equals `data_sentence + " " + purpose_sentence`;
- every prompt is 25-40 words;
- labels use only the given vocabulary;
- candidates use only registered tool names;
- no tool name appears in any prompt;
- every family shares one data sentence and has a `none` control;
- the coverage requirements hold (family designs: 2 paired, 3 groups, 1 none; family claim counts: none 6, individual_change 4, causal 4, prediction 4, group_difference 3, regulator_change 3; 3 negation traps; 5 precision traps).

32 prompts: 6 minimal-pair families x 4 (Q1-Q6) + 8 traps (T1-T8).

## Families (one data sentence each, 4 purposes)

- Q1 (paired, before/after): lavaged alveolar macrophages, 14 volunteers, baseline vs 6 h after inhaled endotoxin. RNA-seq + motif + PPI.
- Q2 (groups, cases vs controls): whole blood from Kawasaki disease vs febrile-control children (n=100). RNA-seq, expression only.
- Q3 (paired, split-sample): monocytes from 9 donors, each split into high- vs normal-glucose culture. mRNA + small RNA + motif/PPI/miRNA-target priors.
- Q4 (groups, behavioural role): nurse vs forager honeybee brains (n=60). RNA-seq + bisulfite methylation on the same brains (second omics layer).
- Q5 (no comparison): 210 Ewing sarcoma tumours at diagnosis. Expression arrays + motif + PPI.
- Q6 (groups, dose groups via a sample sheet): rat lungs at four diesel-exhaust doses, 8 rats each. RNA-seq + motif + PPI.

## Traps

- T1 (negation, explicit, at the start of the purpose): myelodysplastic marrow. Prediction and causality are ruled out; the true claim is individual_change.
- T2 (negation of a comparison, indirect, in the data sentence): long-COVID blood. Matched controls exist but were not sequenced, so the design is none; the goal is subtyping (none).
- T3 (negation of causality, indirect, at the end): bleached vs unbleached corals. Causality is deferred to later experiments; the true claim is group_difference.
- T4 (precision, the word "predicted"): azoospermia testis. "Predicted miRNA targets" and "predicted regulatory influence" appear, but the true claim is regulator_change between groups.
- T5 (precision, causal background fact): matched HPV cervical tumour/normal. "Known to cause" is background; the true claim is regulator_change with a paired design.
- T6 (precision, a time word plus a method comparison): mouse lungs all harvested 21 days after influenza. "TMM versus quantile normalisation" is a robustness check, so design none and claim none.
- T7 (precision, nuisance covariates): systemic sclerosis fibroblasts from two hospitals over three years. Site and year are effects to remove, not groups to compare; the word "effects" is not causal.
- T8 (precision, "paired-end"): Scn9a-knockout vs wild-type dorsal root ganglia. The sequencing term is not a paired design; the true labels are groups and group_difference.

## Labelling judgement calls (please review)

1. Controls inside paired or groups families keep the family's design label (e.g., Q1-d is `paired`), because the design is stated in the shared data sentence, even when the purpose does not use it.
2. Q4: methylation and RNA-seq were measured on the same brain. That is input matching for the two-omics tools, not a comparison design, so the label is `groups` (nurse vs forager). A reader could argue for `paired`.
3. Q5-b, "compared with the rest of the cohort": labelled design `none` and claim `individual_change`. Contrasting one sample with the rest of its cohort is not a sample-relation design.
4. T1, "whose marrow networks stand out most": labelled `individual_change` even though nothing changes over time. The vocabulary says "differ or change the most".
5. T5: "already known to cause these cancers; what we want is..." could also count as a negation trap. It is flagged as a precision trap because the causal statement is background, not a goal being ruled out.
6. T8: comparing a knockout with wild-type could be read as a causal intent. It is labelled `group_difference` because the purpose only asks whether the networks differ.
7. Q6: ordered dose levels on different rats are labelled `groups`. Q6-a ("as dose increases") is `regulator_change`, not `group_difference`.
8. Q2-a and Q5-a rely on an outcome (coronary damage, relapse) that the data sentence does not supply. They are labelled by the purpose sentence (`causal`, `prediction`), and `must_include` asks the answer to flag the missing outcome data.
9. Candidates for `causal` and `prediction` items are not empty. They list tools a good answer may propose as an associative step or a feature generator; `must_include` requires the answer to say that the causal or predictive step lies outside the suite.
10. COBRA is accepted for group_difference items (Q1-a, Q2-c, T3, T8) and for T7. In each case the stated design or nuisance factors can be written as a covariate table, even though only T7 mentions such a table explicitly.
11. BONOBO is listed for some cohorts of 40-100 samples (Q2, T2, T3) as acceptable rather than preferred. It is left out of the 210-tumour cohort (Q5).

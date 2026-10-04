# Held-out set 9 (32 prompts)

## How it was written

An isolated subagent wrote this set from the task brief alone. It did not read any project file, run the agent or call a model. Scenarios were picked to avoid the earlier sets listed in the brief. Each family shares one data sentence word for word, and its four purpose sentences vary the claim kind. Every family has one control (`claim_kind: none`). The standalone items T1-T8 each have their own data sentence. A script checked the JSON before the copy: it parses; `prompt` equals data + " " + purpose; labels and tool names are valid; recommended is a subset of acceptable; no prompt names a tool; prompts are 29-45 words; and the coverage rules hold.

Labelling rules used throughout:
- `acceptable_candidates` lists the tools that fit the stated inputs and do not contradict the purpose. No motif/PPI tools appear when only expression is stated. No PUMA family without miRNA data. When two omics layers are the point, the DRAGON family is used.
- `recommended_subset` is non-empty only when the question favours some of the tools that fit the data over others. It can equal `acceptable_candidates` when the purpose already rules out the other data-fitting tools, so those are not listed as acceptable (S1-a, S3-c, S4-b, T3). It is empty for causal, prediction and none purposes, and when the question does not separate the tools.

## Family themes

- S1: thigh muscle before/after a ketogenic diet; expression only, stated explicitly; paired.
- S2: lupus nephritis vs minimal change disease kidney biopsies; expression + TF motif + PPI; groups.
- S3: matched hepatocellular carcinoma vs adjacent liver; mRNA + miRNA with motif, PPI and miRNA-target priors; paired.
- S4: adipose from gestational-diabetes vs normoglycaemic women; RNA-seq + DNA methylation on the same samples; groups.
- S5: CD4 T cells before/after yellow fever vaccination; expression + TF motif + PPI; paired.
- S6: sarcoidosis lymph nodes, nine patients; expression only, implied by listing only RNA-seq; no comparison.

Standalone items:
- T1: vitiligo, five patients, paired.
- T2: myelodysplastic marrow vs donors, signed effects.
- T3: islets, RNA-seq + proteomics, negation trap: the cross-omic link is ruled out.
- T4: cystic fibrosis nasal brushings, non-separating.
- T5: pre-eclamptic placentas with miRNA, non-separating.
- T6: synovium, RNA-seq + proteomics, non-separating.
- T7: tendinopathy with age/sex covariates.
- T8: neuroblastoma miRNAs, negation trap: per-patient networks are ruled out.

## Judgement calls I was unsure about

1. **Design on controls.** `comparison_design` follows the shared data sentence for all four prompts in a family, including controls that say "before comparing" or use only baseline samples (S5-b). One could argue those should be `none`.
2. **Paired wording.** When a paired question says "within each person" or "against their own baseline", I favoured the per-sample tools (S3-b, S5-a, S5-c). S1-b (expression only, cohort-level wording) was left empty instead, because COBRA with volunteer as a covariate and per-sample co-expression networks can both use the pairing.
3. **GIRAFFE vs LIONESS-PANDA.** GIRAFFE is recommended where the question asks for per-sample TF activity or activation/repression (S5-c, T2). It is not recommended where the question asks for per-individual *networks* (S2-c, S5-a), though its TF-by-sample activity matrix could arguably answer S2-c too.
4. **S1-d (TF question, expression only).** Acceptable lists co-expression tools as a caveated proxy, and recommended is empty. A stricter reading would leave acceptable empty.
5. **T5.** The user has miRNA data but asks a generic "does regulation differ" question, so I labelled it non-separating. One could argue the PUMA family should be preferred because it uses all the user's data.
6. **BONOBO vs LIONESS-COEXPRESSION on sample size.** With 9-10 samples (S6-b, T1), only BONOBO is recommended; both items also ask about confidence in each edge. With 24-40 samples (S1-a, T3), both are recommended.
7. **T7 COBRA.** I treated it as favoured because the user asks to attribute co-expression to a covariate while adjusting for others. Per-sample co-expression networks plus an external regression could also do it.
8. **T8.** LIONESS-PUMA stays acceptable as a secondary option, even though the user said per-patient networks are not needed. Recommending it first is a red flag.
9. **COBRA in S1-b.** COBRA counts as acceptable without an explicit covariate table, because the diet/volunteer labels act as the design.

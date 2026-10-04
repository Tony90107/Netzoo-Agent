# Held-out set 5: comparison design and claim kind

## How it was written

A subagent wrote this set using only the task brief: the label vocabulary, the registered tool list with each tool's inputs, and the list of scenarios to exclude. It did not open the agent's code, prompts, rules, earlier held-out sets or research logs, and it did not run the agent or call any model. It also did not look at how the component reads the requests. The prompts were written to sound like lab emails, sample sheets, grant aims and methods notes.

- 32 prompts: 6 minimal-pair families of 4 prompts each (M1-M6) and 8 standalone traps (T1-T8).
- Each family keeps one data sentence word for word and changes only the purpose sentence. Every family has one control whose claim_kind is `none`. Controls sit in different positions across the families (M1-b, M2-c, M3-a, M4-d, M5-c, M6-b).
- Family designs: 3 `paired` (M1, M4, M6), 2 `groups` (M2, M5), 1 `none` (M3).
- Claim kinds across the 24 family prompts: group_difference 4, individual_change 4, regulator_change 4, causal 3, prediction 3, none 6.
- Each prompt is one paragraph of 26-39 words and names no tool, package or file. A script checked that the JSON parses, that every `prompt` equals `data_sentence + " " + purpose_sentence`, and that the coverage counts, label values and candidate names are valid.
- Inputs vary across the set: RNA-seq or microarray; expression only (M3, M5, T2); expression with motif and PPI priors; mRNA plus small-RNA with a miRNA-target prior (M4, T5); paired RNA-seq and methylation (T4); a somatic mutation table (T6).

## Family themes

- M1 (paired): whole-blood RNA-seq from marathon runners, sampled before the race and 24 h after; motif and PPI priors.
- M2 (groups): prefrontal cortex RNA-seq from Shank3-mutant mice and wild-type littermates; motif and PPI priors.
- M3 (none): microarrays of one biobank cohort of high-grade serous ovarian tumours; expression only.
- M4 (paired): matched primary colorectal tumours and liver metastases from the same patients; mRNA, small-RNA, motif, PPI and miRNA priors.
- M5 (groups): rat kidney cortex RNA-seq across saline and three cisplatin dose groups; expression only.
- M6 (paired): colonic organoids from each donor, split into an IL-22 well and a vehicle well; motif and PPI priors.

## Trap themes

- T1 (negation, causal ruled out at the end): Antarctic crew blood drawn on arrival and at midwinter. The real question is a crew-level shift (paired / group_difference).
- T2 (negation, prediction ruled out at the start): medulloblastoma tumours at diagnosis. The real question is which tumours are most atypical (none / individual_change).
- T3 (negation, comparison ruled out inside the data sentence): tendon samples from two hospitals that the user says they will not compare. The real request is a single network (none / none).
- T4 (precision, "paired" omics): "paired RNA-seq and methylation from the same tumours" describes two data layers from one condition, not a two-condition design.
- T5 (precision, "predicted"): "predicted binding sites / targets / predicted to regulate" refers to prior evidence, not to an outcome prediction.
- T6 (precision, "driver" and "impact"): pathway-level mutation scoring and subtyping, worded in terms that sound causal.
- T7 (precision, "longitudinal"): one sample per newborn taken from a longitudinal birth cohort, so there are no repeated measures.
- T8 (precision, "matched"): patients against age- and sex-matched controls. These are different people, so the design is `groups`, not `paired`.

## Judgement calls I was unsure about

1. **Controls in paired or groups families.** A control keeps the family's design label (for example M1-b is `paired` / `none`) because the data sentence still states that structure. The purpose sentence simply does not use it. If the rule is that the design label should only be read when the purpose needs it, these labels would change.
2. **T3.** Two hospitals are named but the user explicitly rules out comparing them, so I labelled the design `none`. Labelling it `groups` with a nuisance batch would also be defensible.
3. **T8.** I labelled age- and sex-matched case-control as `groups`, following the vocabulary's "same individuals" test for `paired`. An analyst could still use a matched-pairs analysis.
4. **M3-a.** "Grouped into regulatory subtypes" is labelled claim `none` (subtype discovery), not `group_difference`. The design stays `none`.
5. **M6-b.** "Which TFs regulate the mucin genes" is labelled `none`. It names regulators but asks for no change or difference.
6. **M5-c.** "A co-expression network for each animal to explore later" is labelled `none`, not `individual_change`. It asks for per-sample networks but not for a ranking.
7. **Causal labels on experiments.** M2-b (a knockout) and M5-a (dosing) are interventional designs. I still labelled them `causal` because the user wants to *demonstrate* a mechanism or rule out a confounder. The must-include notes accept that the experimental design, not the network, carries the causal weight.
8. **M4-c.** The prediction label is kept even though every patient in the cohort already has metastases, so there is no negative class. The must-include line asks for that problem to be pointed out.
9. **T6.** "Mutational impact on pathways" is labelled `none`. It is a pathway-scoring and subtyping request, even though "impact" and "driver" sound causal.
10. **Acceptable candidates.**
    - COBRA (EXPR+COV) is listed whenever the request states the design variables (time point, genotype, dose, treatment). I assumed the covariate table follows from what the request states.
    - BONOBO is listed for per-sample co-expression even in large cohorts (M3, T7), where it is valid but not its best fit.
    - For causal and prediction prompts, the candidates are descriptive first steps only. Every such item's must-include says that the causal test or the classifier lies outside the suite.
    - M3-d lists only LIONESS-COEXPRESSION, because no motif prior is stated for a PAX8-centred TF network. An empty list would also be defensible.

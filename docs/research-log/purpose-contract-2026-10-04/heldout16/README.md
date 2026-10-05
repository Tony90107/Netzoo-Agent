# heldout16: reading TF priors in any wording

32 English research requests for the NetZoo workflow adviser, with labels. The set checks three things. Does the assistant read correctly, whatever the wording, whether the user has a TF motif prior and a PPI network? Does it recommend what fits the question? Does it ask about the priors only when the answer depends on them?

## How it was written

- I wrote it in isolation from the coordinator's brief alone. I read no repository files, did not run the assistant and called no model API. Every label is my own scientific judgement under the rules below.
- I built the items with a throwaway script in the session scratchpad. A separate validation script then checked them: the JSON parses; prompt = data + " " + purpose; every label value and workflow name comes from the allowed lists; recommended is a subset of acceptable and is empty for causal, prediction and none; `data_question` is "priors" only when the priors are unstated; prompts are 29-45 words long (actual range 34-44); no prompt names a workflow; each family shares its data sentence and `priors_stated`; and the coverage rules hold. It flagged one item, T5 (see judgement call 9). I narrowed that one heuristic check and re-ran; everything passed.
- Words are counted by splitting on whitespace, so hyphenated terms count as one word.

## Families (one shared data sentence, four purposes: group / individual / control / TF-level)

| Family | Data | Priors | Design |
|---|---|---|---|
| F1 | Palm skin, chronic hand eczema, 14 adults before and after 12 weeks of alitretinoin; "curated TF–promoter binding annotations and a protein contact map" | stated | paired before/after |
| F2 | Palatine tonsils, 26 recurrent tonsillitis vs 22 sleep apnoea children; "scanned promoters with JASPAR matrices and downloaded STRING interactions" | stated | two groups |
| F3 | Brains of 20 cave vs 20 surface Mexican tetras; "nothing is catalogued about where this fish's transcription factors bind or which proteins they partner with" | ruled_out (explicit) | two groups |
| F4 | Whole blood, 28 peanut-allergic children before and after a year of oral immunotherapy; "the resulting gene count table is the whole of our data" | ruled_out (implicit) | paired before/after |
| F5 | Hearts of 45 wild house mice from European farms, "3′ tag sequencing, one transcript-count profile per animal" | unstated | single collection; the group item brings in male vs female |
| F6 | Lung squamous carcinoma and matched normal lung from 30 patients, "poly-A RNA libraries and a mass-spectrometry proteome" on every piece | unstated | paired matched tissue, two omics layers on the same samples |

Item letters are the same in every family: a = group/cohort comparison, b = individual, c = control (claim_kind "none"), d = TF/regulator-level.

## Standalone items

- **T1**: Grapevine berries, leafroll-infected vs healthy, "total RNA sequencing". TF-level question, priors unstated.
- **T2**: Skin punch biopsies in diabetic neuropathy, at diagnosis and two years later, "hybridised to expression microarrays". TF-level question, priors unstated.
- **T3**: Wasting vs healthy ochre sea stars. Priors are ruled out by "the read-count matrix is everything we hold … binding preferences remain uncharacterised", which uses none of the words no / not / only. TF-level question.
- **T4**: ANCA vasculitis kidney biopsies, relapsed vs "24 who did not", plus a stated motif prior and PPI network. The negation is about relapse, not the priors. Group question.
- **T5**: Nine women with lymphangioleiomyomatosis ("just nine"). Wants a network per woman with a confidence value on every edge. Priors unstated.
- **T6**: Pulmonary arterial hypertension lungs vs unused donor lungs, mRNA and small-RNA sequencing, with JASPAR, STRING and TargetScan. Asks which microRNAs change.
- **T7**: Alpha-1 antitrypsin deficiency liver with stated priors. Causal request ("prove that falling FOXA2 activity … causes their liver scarring").
- **T8**: Uterine leiomyosarcomas with RNA-seq and stated priors. The methylation arrays come from 27 *different* tumours from another biobank, yet the question asks to consider methylation alongside expression. This traps an adviser who reaches for the two-layer workflows.

## Labelling rules I applied

1. **Acceptable sets by purpose** (for expression-only data):
   - *Group/cohort comparison.* With priors: PANDA, OTTER, LIONESS-PANDA, GIRAFFE, COBRA, LIONESS-COEXPRESSION, BONOBO. Without priors: COBRA, LIONESS-COEXPRESSION, BONOBO.
   - *Individual.* Only per-sample workflows: LIONESS-PANDA, GIRAFFE (with priors), LIONESS-COEXPRESSION, BONOBO. PANDA, OTTER and COBRA give one result per cohort or group, so they are never acceptable here.
   - *Control asking for a TF–gene network.* PANDA, OTTER, LIONESS-PANDA, GIRAFFE.
   - *Control asking for per-sample networks without priors.* LIONESS-COEXPRESSION, BONOBO.
   - *TF-level with a comparison.* GIRAFFE, LIONESS-PANDA, PANDA, OTTER, plus the co-expression workflows as an explicitly caveated proxy (TF genes' change in connectivity). With priors ruled out, only that proxy remains.
   - *TF-level variation within a single collection.* Per-sample workflows only.
2. **COBRA** is acceptable whenever groups or time points are stated. The group or time labels, plus the individual ID for paired designs, form its design matrix.
3. **Two-layer workflows** (DRAGON, LIONESS-DRAGON) appear only in F6 and T6, where the layers come from the same samples. They never appear in T8. **PUMA** and **LIONESS-PUMA** appear only in T6.
4. **Recommended:**
   - With priors: paired cohort comparison → LIONESS-PANDA; two-group comparison → PANDA + LIONESS-PANDA; individual → LIONESS-PANDA; TF-level → GIRAFFE + LIONESS-PANDA.
   - Priors ruled out: cohort comparison → COBRA. Individual and TF-level → empty, because LIONESS-COEXPRESSION and BONOBO tie and cohort size may not break the tie.
   - Empty for every control and for T7.
5. **Unstated priors with `data_question` "priors":** acceptable is judged as if the priors exist. Recommended lists the first pick under each branch (with priors / without), but only where that branch has a favoured pick. That gives F5a [PANDA, LIONESS-PANDA, COBRA] but F5b [LIONESS-PANDA].
6. **`data_question` "priors"** applies to F5 (all four), F6d, T1 and T2. It is "none" for F6a-c, where the two-layer route does not need priors, and for T5, where only BONOBO gives per-edge confidence.
7. **`comparison_design`** follows the sample design the prompt describes, even for controls and individual items. F2c is "groups"; F6c is "paired". F5a is "groups" because its purpose sentence brings in the sexes.
8. **`is_negation_trap`** is applied mechanically. It is true when a negation word (no / not / never / none / nothing / without / neither / nor / cannot / lack / n't) appears while the priors are stated or unstated, or when the priors are ruled out with no negation word at all. Items flagged: F2c, F4a-d, T3, T4.
9. **`is_precision_trap`** is true when a cue looks like an input the user does not have: the F6 proteome (not a PPI network) and T8's methylation (not from the same samples). Items flagged: F6a-d, T8.
10. **`size_preferred`:** BONOBO when the stated number of individuals is under 12, which is only T5. Every family has 14 or more individuals.

## Judgement calls I was unsure about

1. **Co-expression proxies for TF-level questions.** I counted LIONESS-COEXPRESSION, BONOBO and COBRA as acceptable for TF-level questions in every prior state, because they can rank TF genes by change in co-expression. They do not measure regulatory activity. A stricter labeller would leave them out, which would make the ruled-out TF items (F3d, F4d, T3) have *no* acceptable workflow. I chose leniency so that a careful "only a proxy is possible" reply is not penalised. The cost is that the acceptable sets for stated-prior TF items are broad.
2. **COBRA without a covariate table.** COBRA counts as acceptable with no table mentioned, because group or time labels are always implied when groups are stated. If the reply rules require an explicitly stated covariate table, COBRA should come out of F1-F5, T1-T4 and T6.
3. **F6a-c `data_question` "none".** These items are unstated-prior, so under the brief's rule the motif workflows are not acceptable there. A reply that adds "if you also have a motif prior, LIONESS-PANDA" would fall outside the acceptable set. I think the two-layer workflow is clearly the first pick, but F6a ("are tumour networks different") is the weakest case: one could argue the answer does depend on priors.
4. **Cohort comparison without priors → COBRA alone** (F3a, F4a). This is because COBRA gives one cohort-level, covariate-adjusted result. For the paired F4a, per-sample co-expression with paired tests is equally defensible.
5. **Literal "empty when nothing favours".** Ruled-out individual and TF items have empty recommended sets because LIONESS-COEXPRESSION and BONOBO tie. A reader could just as well expect both listed.
6. **GIRAFFE as acceptable for TF–gene network controls and group comparisons.** It yields signed TF–gene effects, though its headline output is TF activity.
7. **PANDA and OTTER as acceptable for paired comparisons** (F1a, F1d, F6d, T2). Aggregates per time point answer the cohort question but ignore pairing, so they are acceptable without being recommended.
8. **Branch picks in recommended for unstated priors.** Listing both the "with priors" and "without priors" first picks (F5a includes COBRA) is my convention. If recommended should mean the with-priors branch only, drop COBRA from F5a.
9. **T5 has acceptable = recommended = [BONOBO].** Only BONOBO gives per-edge confidence. My validator's "recommended equals acceptable means nothing is favoured" heuristic flagged this; I limited that check to items with more than one acceptable workflow.
10. **T6 counts mRNA + small-RNA sequencing as two omics layers.** That made DRAGON and LIONESS-DRAGON acceptable proxies for the miRNA question. Leave them out if small RNA counts as part of the same transcriptome layer.
11. **T7 (causal) has acceptable = [].** No workflow can deliver causation. A reply offering GIRAFFE as associational support with a clear caveat would then score outside the acceptable set. A prediction item would have raised the same question.
12. **T8 accepts RNA-only per-tumour workflows** even though the purpose asks for methylation, which cannot be delivered tumour by tumour. Strictly, acceptable could be [].
13. **F4 is human blood** with priors ruled out by "the whole of our data". Public human motif priors exist, so a careful adviser might offer to obtain them. Per the brief, motif workflows are not acceptable. A reply that suggests downloading priors is not a red flag; one that treats them as already in hand is.
14. **F3 Mexican tetra** has a sequenced genome, so vertebrate JASPAR motifs could in principle be mapped. I followed the user's statement that nothing is catalogued.
15. **F5c (control) `data_question` "priors".** I set it although recommended must be empty, because a TF-to-gene map is only possible with a motif prior.
16. **"Vary most from one mouse to the next" (F5d) labelled regulator_change.** There is no comparison, only variation across individuals; it could also be read as individual_change.
17. **Negation and precision trap definitions are mine** (rules 8-9). Under my rule F2c's "No test is planned" counts as a negation trap, and so do all four F4 items (implicit ruled-out wording).
18. **T4's "relapsed … who did not"** invites a careless prediction reading. I flagged it only as a negation trap, not a precision trap.

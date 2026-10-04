# Held-out set 3: comparison design and claim kind

32 prompts in `heldout.json`: 6 minimal-pair families of 4 prompts (H1-H6) and 8 standalone traps (T1-T8).

## How it was written

- An isolated subagent wrote the set from the task brief alone. It did not open, list or search any repository file, did not run the agent and did not call any model. It never saw the witness lists, the rule code or earlier held-out sets, and it did not try to guess how the rules work.
- Each family shares one data sentence word for word and pairs it with four different purpose sentences. Every family has at least one control (claim `none`, `is_control: true`).
- `comparison_design` follows what the request states about the samples, which in this set is always the data sentence. `claim_kind` follows the purpose sentence. If the data sentence states a design and the purpose sentence wants a plain description, the design label stays (for example H2-d, H4-d, T4).
- Phrasing is deliberately varied and avoids any single template: questions, "we want to test whether", grant-aim style ("Aim 2 asks whether"), lab-email style ("could you help me"), hedged goals ("down the line", "we hope to prove").
- `acceptable_candidates` follow the inputs each prompt states. Tools that need a motif or PPI prior are left out wherever no prior is mentioned. miRNA tools appear only in H3 and T6, the two prompts with miRNA data. DRAGON-family tools appear only where two matched omics are stated.
- Prompts are 27-40 words each. The script checks that the JSON parses, that each `prompt` equals `data_sentence + " " + purpose_sentence`, that no prompt names a registered tool, and that every coverage rule holds: at least 2 paired, 2 groups and 1 none family, and every claim kind at least twice across the families (counts: group_difference 4, individual_change 4, regulator_change 3, causal 3, prediction 3, none 7).

## Families (design · data)

- H1: paired · psoriasis, lesional and non-lesional skin from the same patients · microarrays with motif and PPI priors
- H2: groups · rheumatoid arthritis vs osteoarthritis synovial biopsies · RNA-seq, expression only
- H3: paired, three visits · COPD sputum when stable, during exacerbation and after recovery · mRNA and small-RNA-seq with motif, PPI and miRNA-target priors
- H4: groups · dairy cows with subclinical mastitis vs healthy herd-mates · milk-cell RNA-seq with bovine motif and PPI priors
- H5: none · primary neuroblastomas with matched expression and methylation arrays (two omics, no comparison)
- H6: groups, four dose arms · zebrafish larval pools, vehicle plus three bisphenol S concentrations · few samples, expression only

## Traps

- T1 negation: causation ruled out in mid-sentence ("describe, not causally explain"). Thyroid carcinomas split by BRAF vs RAS mutation. True labels: groups / group_difference.
- T2 negation: prediction and a classifier ruled out at the start. Piglet jejunum from one farm. True labels: none / individual_change.
- T3 negation: a diet comparison ruled out at the end ("without a chow-fed group"). Outbred mouse liver on a single diet. True labels: none / none.
- T4 precision: "paired-end" sequencing, where "paired" is a technical term. iPSC microglia from carriers and non-carriers. True labels: groups / none.
- T5 precision: "age- and BMI-matched" donors who are different people. Diabetic vs non-diabetic islets. True labels: groups / regulator_change.
- T6 precision: "computationally predicted miRNA targets", where "predicted" describes an input and not a goal. Term placentas. True labels: none / none.
- T7 precision: "sort the tumours into groups", which means unsupervised clustering and not a stated design. Canine osteosarcomas. True labels: none / none.
- T8 precision: "cause of death" in a covariate table and "remove the effect of RNA integrity", which is a technical adjustment. Postmortem hypothalami. True labels: none / none.

## Labelling judgement calls the author should check

1. H5 says "matched expression and methylation arrays": two omics from the same tumours. I labelled it `none`, not `paired`, because no conditions or time points are compared. A reader who treats "matched" as a pairing cue would disagree.
2. T5 has age- and BMI-matched cases and controls. I labelled it `groups` because the vocabulary reserves `paired` for the same individuals or donors. A matched case-control design could justify a matched analysis, but the samples come from different people.
3. T4 has a carrier vs non-carrier split, so I labelled the design `groups` even though the purpose is only descriptive. If the study wants traps whose true design is `none`, change the data sentence instead.
4. T3 mentions two sample sets (high-fat vs chow) only to say there is no chow group. I labelled it `none`.
5. H6-a asks a dose-trend question ("progressively more disrupted as the concentration rises"). I labelled it `group_difference` (change across conditions at the cohort level). An ordered-dose reading could be seen as a different kind of claim.
6. H6-b ("prove that bisphenol S disrupts development by acting through estrogen-receptor signalling") is labelled `causal` even though the exposure was set by the experiment. The claim is about the mechanism, which these data cannot establish.
7. H4-c and H5-c are labelled `prediction`, but neither data sentence includes outcome data (future mastitis, survival). The expected answer flags that gap.
8. H1-c ranks patients by the change from their own uninvolved skin. I labelled it `individual_change` (which individuals change most), not `group_difference`.
9. H2-d and T7 (modules or clusters across all samples) and H5-d (subtyping) are labelled `none`, following the brief's examples.
10. COBRA is listed as acceptable wherever group labels, dose or a donor table is stated (H2, H6, T8), on the reading that a stated group or dose implies a covariate table. If the study requires the covariate table to be stated explicitly, remove COBRA from H2-a, H2-d, H6-a and H6-b.
11. Where only expression and priors are given, aggregate-network requests list PANDA, OTTER and GIRAFFE together. Expression-only per-sample tools (LIONESS-COEXPRESSION, BONOBO) are also listed for H1-c, because a prior was stated but is not strictly required to rank individuals.
12. H6-d lists only BONOBO, because the user stresses "so few replicates" and wants a trustworthy per-pool network. LIONESS-COEXPRESSION could be argued as acceptable with a caveat.

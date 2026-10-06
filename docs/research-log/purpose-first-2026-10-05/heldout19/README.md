# Held-out set 19: purpose minimal pairs

`heldout.json` has 32 labelled requests: 7 minimal-pair families (A-G, 4 items each) and 4 standalone traps (T1-T4).

## How it was written

- An isolated subagent wrote the set on 2026-10-06, working only from the task brief: the registered workflow list with their inputs, the label schema, the labelling rules and the coverage rules.
- It did not read, list or search any repository file, earlier held-out set, research log or assistant code. It did not use git, run the assistant or call any model API.
- The only files it wrote are this README and `heldout.json`. A throwaway build and validation script ran outside the repository, in `/private/tmp/claude-501/heldout19-scratch/`.
- All labels are the author's own scientific judgement, applied within the brief's input rules.

## Families

In every family the data sentence is identical word for word. Only the purpose sentence changes.

| Family | Data (organism / tissue) | Design | Priors | Priors wording | miRNA | Claims (items 2-4) |
|---|---|---|---|---|---|---|
| A | Human skeletal muscle, 22 adults with type 2 diabetes, before and after 12 weeks of exercise | paired | stated | "a TF motif prior and a protein-protein interaction network" | no | individual_change, regulator_change, causal |
| B | Human lung, 35 IPF patients and 35 donor lungs | groups | stated | "JASPAR transcription-factor binding-site scans of gene promoters and the STRING interaction database for human proteins" (avoids motif / prior / PPI / protein-protein) | no | group_difference, regulator_change, individual_change |
| C | Human placenta, 60 term pregnancies with birth weight recorded | none (single cohort, continuous covariate) | stated | "a ChIP-seq-derived TF binding prior, a PPI network" | yes ("TargetScan predictions for placental miRNAs") | regulator_change, individual_change, prediction |
| D | Leaves of a wild millet species, 6 drought-stressed and 6 well-watered plants | groups (expression alone, small) | ruled_out | "there are no TF motif or protein interaction resources for it" | no | group_difference, individual_change, prediction |
| E | Whole blood, 10 endurance horses before and after a 120-km race | paired (expression alone, small) | ruled_out | "TF binding-site and protein-interaction resources are unavailable for horses, so expression is our sole input" (none of no / not / none / without / only / never / nothing appears anywhere in the family's prompts) | no | group_difference, individual_change, causal |
| F | Nasal epithelial brushings, 40 children with asthma and 40 healthy children | groups | unstated | (no mention) | no | group_difference, regulator_change, prediction |
| G | Liver RNA-seq and lipidomics on the same 48 biopsies, 24 steatohepatitis and 24 simple steatosis | groups (two layers on the same samples) | unstated | (no mention) | no | group_difference, individual_change, causal |

Item 1 of every family is the control (`claim_kind: none`, `is_control: true`). It asks for one summary result with no comparison, so its `recommended_subset` is empty.

Recommended subsets by family (non-control items, in item order):

| Family | Item 2 | Item 3 | Item 4 |
|---|---|---|---|
| A | LIONESS-PANDA | GIRAFFE | (causal: none) |
| B | PANDA, OTTER | GIRAFFE | LIONESS-PANDA |
| C | GIRAFFE | LIONESS-PUMA | (prediction: none) |
| D | COBRA, BONOBO | BONOBO | (prediction: none) |
| E | BONOBO | BONOBO | (causal: none) |
| F | COBRA, LIONESS-COEXPRESSION | (none: priors unstated) | (prediction: none) |
| G | DRAGON | LIONESS-DRAGON | (causal: none) |

In 5 families (A, B, C, D, G), two non-control items have different non-empty recommendations. E and F are deliberate exceptions, explained below.

## Standalone traps

| Item | Trap | Labels |
|---|---|---|
| T1 | Mouse hippocampus, aged and young. One sentence states a TF motif prior and a PPI network and also says there is "no miRNA target data". The purpose asks which TFs change their *targeting* with age. | priors stated, miRNA false. Recommended: LIONESS-PANDA, PANDA. Acceptable also includes OTTER. A miRNA-aware tool, or any claim that the motif prior is missing, is a red flag. |
| T2 | Kidney transplant biopsies with a TF motif prior and PPI. The user's supervisor said to "build one network for the whole cohort", but the user needs each recipient's network. | individual_change. Recommended: LIONESS-PANDA. The same run also gives the aggregate the supervisor asked for. Offering only the single cohort network is the trap. |
| T3 | PCOS vs control adipose, priors stated: "We are testing the hypothesis that regulatory edges ... differ significantly". | group_difference in the statistical sense. Recommended: LIONESS-PANDA (per-sample edges plus a between-group test). Reading "testing" as a trial or preview run is a red flag. |
| T4 | ALS muscle RNA-seq and plasma metabolomics from separate cohorts. The purpose asks for gene-metabolite associations that differ by disease. | The DRAGON tools are not acceptable because the layers are not on the same samples. Recommended is empty. Acceptable lists only within-RNA group-difference tools (COBRA, LIONESS-COEXPRESSION, BONOBO), and only as fallbacks that the reply labels as within-layer. |

## Labelling notes (judgement calls)

1. **`comparison_design` describes the data sentence, not the purpose.** It is therefore constant within each family, and the control keeps its family's design. (A1 is still "paired", even though it asks for no comparison.)
2. **Acceptable vs recommended for causal, prediction and T4.**
   - `recommended_subset` is empty, because no registered workflow answers these purposes.
   - `acceptable_candidates` lists the tools a careful adviser may still offer as associational evidence (causal), as per-sample feature generators for an external model (prediction), or as within-layer analysis (T4). The reply must state that limit.
   - Recommending one of these tools as if it proved cause or made predictions is a red flag.
3. **Network vs activity.**
   - When the purpose asks about each person's *network* or *wiring*/*targeting*, only per-sample or aggregate network tools are acceptable (A2, B4, T1, T2), and GIRAFFE is excluded.
   - When the purpose asks which TFs are *more active* or *change in activity*, GIRAFFE comes first (A3, B3, C2). LIONESS-PANDA targeting scores are acceptable as a proxy.
4. **Regulatory vs co-expression.** When priors are stated and the purpose asks for a regulatory network (A, B, C, T1-T3), co-expression-only tools are not listed. They are input-feasible, but they do not answer a TF-to-gene question.
5. **Group-level vs testable group difference.**
   - B2 ("compare ... group against group") asks for a group-level answer, so one aggregate network per group comes first (PANDA, OTTER), with LIONESS-PANDA acceptable.
   - T3 ("differ significantly") and D2/F2 ("test whether") need a statistical comparison, so they get per-sample networks plus a test, or COBRA with the group label.
   - G2 follows B2: one DRAGON network per group first, with LIONESS-DRAGON acceptable.
6. **Pairing and COBRA.** COBRA's design matrix holds covariates, not individual identities. It cannot respect the pairing in E2, so it is excluded there. It is also excluded from every individual-level item. For E2 and E3, per-sample networks followed by within-horse differences are the right evidence.
7. **Small cohorts.** D has 6 plants per group and E has 10 horses. BONOBO is recommended over LIONESS-COEXPRESSION, which stays acceptable, because BONOBO is suited to small cohorts and gives per-edge confidence.
8. **Family E repeats a recommendation on purpose.** E2 (paired group difference) and E3 (each horse's change) both route to BONOBO. With expression alone and a paired design, the right evidence for both purposes is per-sample co-expression networks. The family therefore checks that the adviser does not invent a difference where purpose does not change the tool.
9. **Family F (priors unstated).**
   - Under the brief, unstated priors are treated as unavailable. F3 (which TFs are more active) therefore has no acceptable workflow, and a good reply asks whether TF binding and PPI data exist.
   - F1's "gene network" control likewise expects that question before any regulatory network is offered.
10. **Co-expression controls (D1, E1, F1).**
    - COBRA is the only registered workflow whose output is one cohort-level co-expression result. Its baseline component summarises shared co-expression, and a group or time label is present in each of these families.
    - The per-sample co-expression tools give more than these controls ask for, so they are not listed.
11. **Aggregate controls with priors.** The controls list only aggregate tools: PANDA and OTTER in A1 and B1, PUMA in C1 (which keeps the miRNA regulators the purpose names). The LIONESS variants also output an aggregate, but they are not what a single-summary purpose calls for.
12. **Family C.** Recording birth weight makes COBRA input-feasible, but no C purpose calls for co-expression, so COBRA is not listed. C3 names miRNA regulators, so LIONESS-PUMA comes first and LIONESS-PANDA is acceptable. C2 asks only about TFs, so GIRAFFE comes first.
13. **Family G.** Priors are unstated and irrelevant, because the two-layer tools need none. RNA-only tools are excluded because every G purpose concerns gene-lipid links.

## Validation

A throwaway script (outside the repository) checked the following, and all checks passed:

- JSON parses; `prompt == data_sentence + " " + purpose_sentence`; enums are valid; workflow names are valid.
- `recommended_subset` is a subset of `acceptable_candidates`, has at most 3 entries, and is empty for causal, prediction and none.
- Data sentences, priors, miRNA and design are identical within each family; each family has one control and three distinct claims.
- Prompts are 38-49 words and contain no workflow names, banned topics or paths.
- Input-feasibility rules hold (prior, miRNA, DRAGON, COBRA, CONDOR/SAMBAR).
- Every coverage count is met. Claims: group_difference 7, individual_change 7, regulator_change 5, causal 3, prediction 3, none 7.

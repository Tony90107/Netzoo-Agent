# heldout11: does the reply notice what each workflow can actually deliver?

32 English research requests, labelled from scientific judgement only. A subagent wrote them in isolation: it read no repository file, never ran the assistant and called no model API. The only input was the brief: the workflow list, the label definitions, the coverage rules and the list of scenarios to avoid.

## How it was written

1. I designed six families of four items and eight standalone items to fit the coverage rules. Then I wrote the data and purpose sentences in plain researcher voice. No prompt names a workflow or contains a file path.
2. I wrote every item into a scratch build script (`build_heldout11.py` in the session scratchpad) and validated it before writing anything here. The script checks:
   - the JSON parses and round-trips;
   - `prompt == data_sentence + " " + purpose_sentence`;
   - every label value and workflow name comes from the allowed lists;
   - prompts are 29-45 words and pure ASCII;
   - no prompt contains a workflow name (a word-boundary regex that also catches `LIONESS`), and none contains a keyword from the earlier-scenario list;
   - the four items of each family share their data sentence word for word and share `samples_per_individual`;
   - `is_control` is true exactly when `claim_kind` is `"none"`;
   - each family has one control, at least one individual item and at least one group item, and its fourth item is a regulator question, an indirect individual question or a negation;
   - there are three "many" and three "one" families, and the data and design types required by the brief all occur;
   - the T1-T8 constraints hold;
   - the candidate rules hold: expression-only items list only expression-only workflows; the PUMA family needs miRNA data; the DRAGON family appears only where two layers are the point; no aggregate workflow is listed for an individual or per-patient question when there is one sample per individual; CONDOR and SAMBAR never appear.

   A mutation test (a workflow name injected into a prompt, PANDA injected into an expression-only item) confirmed that these checks fire. The first full run passed with no errors.

## Family themes

| Family | Data (shared sentence) | Samples per individual | How "many" or "one" is signalled | Data type |
|---|---|---|---|---|
| F1 | Uterine fibroids: 8 hysterectomy patients, 15-20 separate fibroids each | many | count per individual | expression + TF motif + PPI |
| F2 | 6 women, fingerprick blood every morning across two menstrual cycles; cycle day logged | many | frequency (about 56 draws each, never stated as a number) | expression only, said outright ("only RNA-seq counts") |
| F3 | Multiple sclerosis white matter: 300 postmortem blocks (lesion and normal-appearing) from 15 donors | many | total count plus number of individuals (about 20 each, implied) | two layers on the same samples (RNA-seq + DNA methylation) |
| F4 | 22 heart failure patients, left ventricle at assist-device implantation and at transplant | one (one per time point) | paired before/after | mRNA + miRNA with TF motif, miRNA-target priors and PPI |
| F5 | Mouse spleen: 16 *Plasmodium chabaudi*-infected and 16 uninfected mice, one spleen each | one | two-group design | expression + TF motif + PPI |
| F6 | Liver from 160 wild Atlantic cod, one fish per sample; sex, length and catch site recorded | one | single collection, no designed comparison | expression only, implied (no priors mentioned) |

In each family:

| Family | Individual item | Cohort or group item | Control | Fourth item |
|---|---|---|---|---|
| F1 | F1a, per-woman networks | F1b, 4 premenopausal vs 4 postmenopausal women | F1c | F1d, regulator: TF activity apart from mRNA, between women |
| F2 | F2a, which woman shifts most between phases | F2b, phase effect across women | F2c, map each woman's network, no comparison | F2d, indirect individual: "wired differently" |
| F3 | F3a, per-donor two-layer networks | F3b, lesion vs normal-appearing, paired within donors | F3c | F3d, negation: "nothing per donor", progressive vs relapsing onset |
| F4 | F4a, which patients remodelled most | F4b, cohort change | F4c, combined TF + miRNA network | F4d, regulator: which miRNAs change targeting |
| F5 | F5a, which infected mice deviate | F5b, group-level rewiring | F5c, reference network | F5d, negation + regulator: "individual mice do not interest us" |
| F6 | F6a, which fish are unusual | F6b, males vs females, adjusted for covariates | F6c | F6d, indirect individual: suspected other stock |

## Standalone items

- **T1** (borderline): myeloma bone marrow, 10 patients × 5 time points, motif + PPI. Asks how each patient's network evolves. Labelled `one`.
- **T2** (borderline): Wilms tumours, 6-8 regions from each of 14, expression only. Asks which tumours vary most between regions. Labelled `one`.
- **T3**: "Each of 40 patients" with IPF contributed one lung biopsy. The number counts patients, not samples per patient. Individual question.
- **T4**: one healthy volunteer, weekly blood for three years (150 draws), motif + PPI. Asks for this person's network and which TFs shift targeting between winter and summer.
- **T5**: familial adenomatous polyposis, 11 patients × 20-30 adenomas plus 5 normal mucosa samples. Cohort-level question: do adenomas differ from mucosa?
- **T6**: 8 laying hens × about 30 ovarian follicles, expression only plus follicle diameter. Negation ("not interested in hen-to-hen differences"), then small vs large follicles.
- **T7**: prediction. IgA nephropathy kidney biopsies from 130 patients with five-year follow-up; predict who progresses from each patient's regulatory features.
- **T8** (trap): 4 tissues across 80 rats, but each rat gave only one tissue. A careless reader assumes multi-tissue rats.

## Labelling rules I applied

- **`samples_per_individual`.** I labelled `many` when one individual's own samples could support a gene-level network estimate on their own. In practice that meant at least about 15 biological samples (fibroids 15-20, blocks about 20, daily draws about 56, weekly draws about 150). A handful (5 time points, 6-8 regions) is `one`, as the brief says ("only a few time points per individual"). Technical structure (tissue type, region) never makes an individual `many` unless the samples come from the same individual.
- **`comparison_design`.**
  - `paired`: the same individuals appear under two or more conditions or time points, or as matched tissue types. This includes F3b (lesion vs normal-appearing blocks within donors), T5 (adenoma vs mucosa within patients), T6 (small vs large follicles within hens) and T4 (one person, winter vs summer).
  - `groups`: different individuals split into groups.
  - `none`: questions that compare individuals to one another without designed groups (F1a, F1d, F2d, F3a, F6a, F6d, T2, T3, T8), controls, and the prediction item T7.
- **`claim_kind`.**
  - `individual_change`: the question asks which individuals or samples change or stand out.
  - `regulator_change`: the question asks which TFs or miRNAs change most. This applies even when the comparison is between women (F1d) or between seasons in one person (T4).
  - `group_difference`: a cohort-level difference between conditions, time points or groups. This includes F6b (sex, adjusted for covariates) and T6 (follicle size, within hens).
- **`acceptable_candidates`.** A workflow is listed only if the stated inputs support it and its output answers the purpose.
  - **Inputs:** expression-only items allow only LIONESS-COEXPRESSION, BONOBO and COBRA (COBRA only where a covariate is stated). The PUMA family needs the miRNA layer. The DRAGON family is used where methylation-expression coupling is the point (F3), and only there.
  - **One sample per individual:** an individual question or per-patient prediction excludes every aggregate workflow (PANDA, PUMA, OTTER, COBRA, DRAGON).
  - **Many samples per individual:** an aggregate workflow run on each individual's own samples is accepted for individual questions (F1a: PANDA and OTTER per woman; F2: COBRA per woman; F3a: DRAGON per donor; T4: PANDA and OTTER per season within the one person).
  - **GIRAFFE** is accepted when an aggregate run gives what is needed (a network for each group, individual or condition) or when per-sample TF activity is the deliverable (F1d, F4b, T7). It is not accepted when the purpose asks for a network for each sample (F4a, F5a, T1, T3, T8), because its per-sample output is TF activity, not a network.
  - **Controls that ask for one network** accept the aggregate workflow plus its LIONESS counterpart, because LIONESS computes the aggregate as part of its procedure. BONOBO is not accepted for a cohort-wide description (F6c), because it gives only per-sample networks.
  - **miRNA questions** (F4c, F4d) exclude the TF-only workflows.
- **Traps.**
  - `is_negation_trap`: the purpose explicitly rules out per-individual results (F3d, F5d, T6).
  - `is_precision_trap`: a surface cue pushes toward the wrong label and only a careful reading rejects it.
    - "each woman" in a control (F2c);
    - "five samples each" or "six to eight regions of each", which look like `many` (T1, T2);
    - "each of 40 patients" (T3);
    - many adenomas per patient in a cohort-level question (T5);
    - four tissues across 80 rats when each rat gave one tissue (T8).
- **`must_include` and `red_flags`** focus on three things: the replicate unit (individual vs sample), whether the chosen workflow can deliver the requested level (individual, group, regulator), and staying within the stated data.

## Judgement calls I was unsure about

1. **F1's "many" threshold.** 15-20 fibroids per woman is at the low end for a per-woman PANDA, OTTER or GIRAFFE run. These methods lean on the priors, so I judged it adequate. A stricter reader could argue for `one`, which would remove PANDA, OTTER and GIRAFFE from F1a.
2. **T1 and T2 labelled `one`.** Five time points (T1) and six to eight regions (T2) seemed too few for an individual's own gene-by-gene network. BONOBO is built for small samples, but it is per-sample, so it does not change the per-individual verdict. A reader with a lower threshold might call T2 `many`.
3. **COBRA as a per-woman aggregate in F2.** The brief lists COBRA among the aggregate workflows that can run on one individual's samples. I accepted COBRA run per woman, with cycle day or phase as the covariate, for F2a, F2c and F2d. Reading the intercept or phase component as "her co-expression network" is my interpretation of COBRA's output, not something the brief states.
4. **GIRAFFE's boundary.** I accept it for per-individual or per-group networks from aggregate runs and for per-sample activity features. I reject it for per-sample networks (F4a, F5a, T1, T3, T8). Someone could reasonably accept GIRAFFE wherever outlying samples can be detected from TF activity alone.
5. **F1d accepts only GIRAFFE.** "Activity independent of their own mRNA levels" matches GIRAFFE's output, and PANDA or OTTER targeting is not activity. This is the strictest candidate list in the set and may be harsher than the reply rules.
6. **DRAGON excluded from F4.** mRNA and miRNA sequencing on the same tissue are technically two omics layers. I excluded DRAGON because the miRNA-target priors are stated and the purposes concern prior-based regulation. A reviewer could accept DRAGON or LIONESS-DRAGON at least for F4b.
7. **The PANDA family accepted in F4a and F4b despite the miRNA data.** These purposes say "cardiac regulatory networks" and "gene regulation", not miRNA, so TF-only workflows were judged able to answer them. Only F4c and F4d require the PUMA family.
8. **LIONESS counterparts accepted in single-network controls** (F1c, F3c, F4c, F5c, F6c). The brief says outright that LIONESS-PANDA returns the aggregate. I extended that to LIONESS-DRAGON, LIONESS-PUMA and LIONESS-COEXPRESSION. A stricter set would list only the aggregate workflow.
9. **Expression-only controls.** There is no dedicated aggregate co-expression workflow, so I accepted COBRA and LIONESS-COEXPRESSION for F6c and also BONOBO for F2c, because there the deliverable is each woman's network.
10. **BONOBO for 160 cod** (F6a, F6b, F6d). It is "suited to small cohorts", but nothing says it fails on large ones, so I kept it.
11. **`comparison_design: "none"` for between-individual questions.** "How each woman differs from the others" has no designed groups, but one could argue each individual is its own group (`groups`).
12. **T7's design.** Progressors vs non-progressors are different people, so `groups` is defensible. I chose `none` because prediction is not a group comparison.
13. **T4's labels.** I labelled one person in two seasons `paired` and `regulator_change`. The paired definition talks about "individuals", and here n = 1.
14. **T6's design.** Follicle size is continuous (diameter), but the question dichotomises it within each hen, so I labelled it `paired`. A covariate reading would also fit COBRA.
15. **F3d.** The user rules out per-donor results, but a valid progressive vs relapsing test still uses the donor as the replicate. I did not penalise per-donor networks used as a hidden intermediate step, only per-donor results delivered as the answer.
16. **F3a must_include.** I required noting that each donor's lesion/normal block mix can confound donor differences. That may be more than the reply rules expect.
17. **F5c.** A "reference spleen network" from all 32 mice pools infected and uninfected states. I did not require the reply to flag this; a careful reply might suggest using only uninfected mice.
18. **T5's normal mucosa.** Only five normal samples per patient would make per-patient normal networks weak. The adenomas (20-30 each) carry the `many` label. I did not encode this asymmetry in the labels.

# heldout10: can-it-answer-the-purpose set (32 items)

This set tests one question: does the reply notice when a candidate workflow cannot give what the purpose asks for, without ever claiming that when the workflow can?

## How it was written

- An isolated subagent wrote it using only the brief. The brief contained the 13 registered workflows with one-line descriptions, the label definitions, the coverage rules and the list of earlier scenarios to avoid. It did not read any repository file, reply rule, earlier held-out set or model output. It did not run the assistant or call any model API.
- All labels are the author's own scientific judgement.
- A Python script in the session scratchpad built the set and checked it. These checks all passed:
  - the JSON parses;
  - `prompt == data_sentence + " " + purpose_sentence`;
  - every label value and workflow name comes from the allowed lists;
  - every prompt is 29-45 words (actual range 35-43);
  - no prompt contains a workflow name (case-insensitive, including "LIONESS"), a slash or a file extension;
  - each family shares one data sentence word for word and has 4 different purpose sentences;
  - each family has an individual item, a cohort/group item and exactly one control;
  - the families have the required data and design mix;
  - T1-T8 fill their roles;
  - every acceptable list fits the stated inputs, and no individual or prediction item accepts an aggregate workflow unless it is a precision trap.
- Item letters inside a family are shuffled, so a letter does not tell you the item's role. The tables below give the roles.
- Every scenario was checked against the list of earlier scenarios to avoid. None reuses a tissue, condition and design combination from that list.

## Families (shared data sentence, the purpose varies)

| Family | Data | Stated inputs | Design | Items |
|---|---|---|---|---|
| F1 | Liver biopsies from 22 bariatric patients, taken at surgery and one year later | Expression only, said outright ("only ... nothing else") | paired | a cohort-level · b per-person score set against weight loss (individual, without "which patients") · c which patients rewire most (individual) · d control (per-biopsy structure) |
| F2 | Root tips of 40 bread wheat lines under salt, 20 tolerant vs 20 sensitive | Expression only, implied | groups | a control (network per line) · b lines out of place for their class (individual) · c which TFs differ in activity (regulator; the inputs cannot answer it) · d group-level |
| F3 | Melanoma biopsies from 28 patients, before and three weeks into anti-PD-1 | Expression + TF motif + PPI | paired | a which patients' TF regulation changes most (individual) · b control (pre-treatment TF-to-gene network) · c cohort-level shift · d negation + regulator ("not after single patients; which TFs change most") |
| F4 | Duodenal biopsies, 40 active coeliac vs 30 controls | Expression + TF motif + PPI | groups | a TFs differently active beyond their own expression (regulator) · b group-level · c control (single network, comparisons later) · d which patients stand out (individual) |
| F5 | 130 primary prostate tumours, matched mRNA + miRNA; Gleason grade recorded | mRNA + miRNA + TF motif, miRNA-target and PPI priors | none (only F5a uses grade) | a high vs lower grade (group) · b which tumours stand out (individual) · c which miRNAs vary most from tumour to tumour (regulator that needs per-sample output) · d control (one network) |
| F6 | Clear-cell renal tumour + adjacent normal kidney from 30 nephrectomy patients; RNA-seq + methylation on the same piece | Two omics on the same samples | paired (matched tissues) | a control (joint network of the tumours) · b "find those" tumours that kept near-normal coupling (individual, indirect wording) · c which patients change most (individual) · d cohort-level coupling difference |

## Standalone items

| Id | Scenario | Role | Acceptable |
|---|---|---|---|
| T1 | 6 organ donors × ~40 tissues each; motif + PPI; "how does each donor's regulatory network differ" | Precision trap: many samples per individual | PANDA, OTTER, LIONESS-PANDA, GIRAFFE |
| T2 | 3 adults with type 1 diabetes, weekly draws for a year; RNA-seq + proteomics of the same PBMC sample | Precision trap: many samples per individual, two omics | DRAGON, LIONESS-DRAGON |
| T3 | Atopic dermatitis lesional skin, 36 patients before/after an anti-IL-13 antibody; RNA-seq and nothing else; "we don't care which patients responded" | Negation trap, cohort-level | COBRA, LIONESS-COEXPRESSION, BONOBO |
| T4 | Ground squirrel hearts, 20 in torpor vs 20 in summer; mRNA + small RNA + all priors; "not looking at single animals" | Negation trap, group-level | PUMA, LIONESS-PUMA |
| T5 | Blood from 30 wild bottlenose dolphins, no comparison group; "whose network looks least like the others'" | Indirect individual question, no groups | LIONESS-COEXPRESSION, BONOBO |
| T6 | Matched primary breast tumours and brain metastases from 22 patients; motif + PPI; "within each patient, which TFs change most" | Regulator question per individual | GIRAFFE, LIONESS-PANDA |
| T7 | Baseline ileal biopsies from 90 Crohn's patients starting anti-TNF, week-14 response; motif + PPI | Prediction | LIONESS-PANDA, GIRAFFE |
| T8 | Cochlea of 25 noise-exposed vs 25 unexposed mice; motif + PPI; "each individual transcription factor in turn" | Careless-reader trap: "individual" refers to TFs, not mice | PANDA, OTTER, LIONESS-PANDA, GIRAFFE |

## Labelling rules applied

1. **Acceptable = fits the stated inputs AND can deliver what the purpose asks.**
   - Expression only, stated or implied: only LIONESS-COEXPRESSION, BONOBO and COBRA. No motif or PPI workflow, even when public priors exist for the species.
   - Expression + motif + PPI: PANDA, OTTER, LIONESS-PANDA and GIRAFFE. Every purpose in these items names TF regulation or a regulatory network, so the co-expression workflows were not accepted there.
   - miRNA layer + priors: PUMA family only, because every purpose in those items names miRNAs.
   - Two omics on the same samples: DRAGON family only, because every purpose names the cross-layer link.
2. **Individual questions** (which samples change or stand out, a per-person score, a prediction for patients) accept only per-sample outputs: LIONESS-\*, BONOBO, and GIRAFFE's TF-by-sample activity. Aggregate workflows (PANDA, PUMA, OTTER, DRAGON, COBRA) are excluded. The one exception is when each individual contributes enough samples to run an aggregate workflow on that individual alone (T1, T2). With two samples per patient (F3a, F6c, T6), an aggregate network per patient is a red flag.
3. **Cohort or group questions** accept both kinds of workflow. An aggregate workflow can be run once per group or time point. Per-sample outputs can go into a group or paired test. Refusing either would punish a correct reply. Each such item has a red flag for the reverse error: claiming that one of these workflows cannot answer.
4. **Regulator questions** need workflows with TF or miRNA nodes. When the regulator ranking must vary across samples (F5c tumour to tumour; T6 within each patient), only per-sample workflows are accepted.
5. **Controls** accept whatever produces the requested artifact without forcing a comparison. "One network" means an aggregate workflow. LIONESS-PANDA is also accepted there because the brief says it returns the aggregate as well. LIONESS-PUMA and LIONESS-DRAGON are not, because the brief lists only per-sample output for them.
6. **comparison_design** follows the study design stated in the prompt, including for controls and for purposes that use only part of the data. The exception is F5a: its grade split comes from the purpose, so it is labelled `groups`.
7. **is_negation_trap** marks purposes that rule out interest in individuals (F3d, T3, T4). Negations about the data ("nothing else", "no comparison group") are not counted.
8. **is_precision_trap** marks items where a rule like "individual wording → per-sample only" would wrongly exclude valid workflows (T1, T2, T8).
9. **must_include and red_flags** focus on whether the reply judges correctly what each workflow can and cannot answer. Red flags cover both directions: offering a workflow that cannot answer, and saying a workflow cannot answer when it can.

## Judgement calls I was unsure about

1. **F2c has an empty acceptable list.** It asks which TFs differ in regulatory activity, using wheat RNA only. The expression-only workflows give co-expression, not TF activity. The motif workflows need a prior that was not stated. A scorer that expects at least one acceptable workflow will need a special case here. A lenient reader could accept COBRA or LIONESS-COEXPRESSION as a proxy (co-expression change of TF genes), but only if the reply flags the gap.
2. **Per-sample workflows are accepted for every cohort or group question** (F1a, F2d, F3c, F4b, F5a, F6d, T3, T4). I think that is right: per-sample networks followed by a test is the standard use. A stricter "one answer for the cohort" reading would drop them.
3. **Aggregate workflows run once per time point are accepted in paired designs** (F3c, F3d, F6d), even though they ignore the pairing. The must_include for those items asks for the pairing to be mentioned. That is a quality point, not a reason to reject the workflow.
4. **GIRAFFE is accepted in several places:** for "TF regulation" individual questions (F3a, F4d), via its per-sample TF activity; for controls that ask for a single TF-to-gene network (F3b, F4c), via its signed regulatory effects; and per donor in T1. A stricter reader would drop it from F3b, F4c and T1, where a network rather than an activity matrix was asked for.
5. **Co-expression workflows are excluded throughout the motif/PPI families and T1, T6, T7, T8**, because every purpose there names TF regulation. For F3a and F4d ("which patients ...") one could argue LIONESS-COEXPRESSION or BONOBO still names the patients. I treated them as not delivering TF regulation.
6. **LIONESS-PANDA is accepted in "one network" controls but LIONESS-PUMA (F5d) and LIONESS-DRAGON (F6a) are not.** This follows the brief's descriptions literally. In practice all three compute the aggregate on the way.
7. **T1 and T2 accept aggregate workflows run per individual.** In T1, each donor's network pools ~40 different tissues, so tissue programmes will dominate it. It is still exactly "that donor's network". must_include asks the reply to say donors should be compared on matched tissues. In T2, weekly draws are autocorrelated, so each person's network describes co-variation over time, and with three people the result is descriptive only. I judged both acceptable. Someone could argue T1 should accept only LIONESS-PANDA or GIRAFFE, compared within each tissue.
8. **T1 and T2 are labelled `paired`** (the same individuals across matched tissues or repeated time points), even though the question compares individuals rather than conditions. `none` is also defensible.
9. **T8 is marked as a precision trap** in addition to the T1 and T2 the brief asked for, because its trap works the same way: wording that suggests individuals, while aggregate workflows are correct.
10. **F5 is counted as the "no comparison" family** even though its data sentence records Gleason grade. F5a turns grade into groups and is labelled `groups`. A scorer that takes the design from the family will see F5a as the exception.
11. **F5c is labelled `regulator_change` with design `none`.** I read "change" as variation from tumour to tumour, since there are no conditions.
12. **F1b mentions weight loss**, which the data sentence does not list. I assumed it is available in a bariatric cohort. The item is labelled `individual_change` (a per-person score), not `prediction` or `causal`.
13. **T7 (prediction) accepts LIONESS-PANDA and GIRAFFE** as sources of per-patient features. No registered workflow predicts by itself, and must_include says so. You could argue the acceptable list should be empty.
14. **BONOBO is accepted for cohorts of 30-72 samples**, although the brief says it suits small cohorts. It still works at these sizes.
15. **F4a ("beyond any change in their own expression") accepts PANDA, OTTER and LIONESS-PANDA as well as GIRAFFE.** Differential TF targeting does not come from the TF's own mRNA level. A stricter reading would make GIRAFFE the only acceptable workflow.
16. **Expression-only items exclude motif workflows** (F1, F2, T3, T5), following the brief's rule, even where public priors exist (human, and partly wheat). A reply that offers adding priors as an extra step should not be penalised. Only a reply that assumes the priors are already in hand should be.
17. **CONDOR and SAMBAR appear in no item.** No scenario has a bipartite network or mutation calls, so this set does not test them.

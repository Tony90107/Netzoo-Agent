# Held-out set 14: tie recommendations and the TF-prior question

32 English research requests with labels, in `heldout.json`. Written by a subagent working in isolation: it read, listed and searched no repository file, did not run the assistant and called no model API. The labels come only from the brief (the 13 registered workflows, the label definitions and the coverage rules) and from the author's own scientific judgement.

The set asks three things. When several workflows fit, does the reply recommend the one that suits the stated question and data? Does it ask about a TF motif prior and PPI network only when the answer depends on them? Does it avoid guessing what data the user has?

## How it was written

1. Six families were designed first. Each has one shared data sentence and four purpose sentences: a cohort/group question, an individual question, a control (`claim_kind: none`) and a TF/regulator question. Eight standalone items (T1-T8) followed, each written to the brief's T-slot description.
2. Scenarios were checked against the brief's long list of earlier scenarios, so no tissue/condition/design combination is reused. They cover human, mouse, tomato, cheetah and tardigrade samples.
3. `build.py` in the session scratchpad generated the items, so every `prompt` is exactly `data_sentence + " " + purpose_sentence`. `validate.py` then checked:
   - the JSON parses and every required field is present;
   - every label value and workflow name comes from the allowed lists;
   - each `recommended_subset` is part of `acceptable_candidates`, and it is empty for causal, prediction and none purposes;
   - `data_question` is consistent with what the data sentence states;
   - every prompt is 29-45 words and names no workflow;
   - each family shares one data sentence and has one item of each kind;
   - the data-kind, design and T-slot coverage rules hold, and a few earlier scenarios are spot-checked by keyword.

   A deliberately broken copy confirmed that the validator catches errors. The final file passed every check.

Counts:
- **Claim kinds:** 6 group_difference, 9 individual_change, 10 regulator_change, 6 none, 1 causal.
- **Designs:** 9 paired, 18 groups, 5 none.
- **data_question:** "priors" on 6 items (A4, B3, B4, F4, T1, T2).
- **Negation traps:** B3, C3, C4, D3, T3.
- **Precision traps:** B1, D4, E4, T5, T8.

## Family themes

| Family | Data (shared sentence, paraphrased) | Priors | Design |
|---|---|---|---|
| A | Whole blood from 30 adults with chronic hepatitis B, before antiviral therapy and after 24 weeks | not mentioned | paired before/after |
| B | Postmortem caudate nucleus, 26 Huntington's disease vs 24 neurologically normal donors | not mentioned | two groups |
| C | Ripe tomato fruit, 20 ripening-inhibitor mutants vs 20 wild type; "RNA-seq counts, nothing else" | ruled out | two groups |
| D | Liver from 24 alcohol-related hepatitis patients, biopsied at admission and after a month of abstinence | TF motif + PPI stated | paired before/after |
| E | Normal breast tissue from 180 reduction-surgery women, age and parity recorded | TF motif + PPI stated | single collection |
| F | 34 diabetic kidney disease biopsies + 30 living-donor kidneys, RNA-seq and DNA methylation on the same cores | not mentioned | two groups, two omics layers |

Purpose pattern inside each family:
- **1** is the cohort/group question.
- **2** is the individual question.
- **3** is the control.
- **4** is the TF/regulator question.

In family E, item E1 makes a parous vs nulliparous split of the single collection. E2-E4 make no comparison.

## Standalone items

- **T1:** Tracheal aspirates from preterm infants who did or did not develop bronchopulmonary dysplasia. Asks which TFs are most differently active. Only "bulk RNA-seq" is described, so the item needs a priors question.
- **T2:** Lesional and non-lesional oral mucosa from each of 25 oral lichen planus patients. Asks for TF targeting differences. Only "poly-A transcriptomes" are described, so again a priors question. The design is paired.
- **T3:** Tardigrade pools, desiccated vs hydrated. Priors are ruled out in unusual wording ("Nobody has catalogued what this tardigrade's transcription factors bind or which of its proteins interact"). It is a TF-level question.
- **T4:** EAE mouse spinal cord, a separate set of mice at each of four stages. Asks which mice are outliers. Only expression is described, and expression-only workflows answer it.
- **T5:** Eight captive cheetahs. Asks for each animal's network with confidence on every edge (BONOBO; `size_preferred` BONOBO).
- **T6:** Knee cartilage with mRNA and microRNA sequencing, plus TF, PPI and miRNA-target priors. Asks about miRNA regulators (PUMA / LIONESS-PUMA).
- **T7:** Calcified vs non-calcified aortic valves with priors. A causal claim about RUNX2.
- **T8:** Gallbladder cancer exome mutation calls only, with a request for "disrupted pathway networks" and subtypes. A careless adviser assumes RNA-seq; the answer is SAMBAR.

## Labelling rules applied

- **Input fit.** A motif/PPI workflow (PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER, GIRAFFE) is acceptable only in two cases: the request states the priors, or the priors are unstated and `data_question` is "priors". It is never acceptable when the priors are ruled out (family C, T3). The PUMA family is acceptable only where miRNA data and a miRNA-target prior are stated (T6). The DRAGON family is acceptable where the question concerns the two layers (F1-F3, and T6 as a non-recommended option).
- **Network type follows the wording.** Purposes worded as gene-gene or co-expression accept the co-expression workflows. Purposes worded as TF-to-gene, regulatory network or TF activity do not accept COBRA, LIONESS-COEXPRESSION or BONOBO.
- **`data_question`** is "priors" only when the priors are unstated and the purpose needs TF-level inference: a TF-level question, or a TF-to-gene map. Gene-gene, individual-network and two-layer questions over unstated priors get "none", because expression-only workflows (or DRAGON) answer them.
- **Group differences.** A co-expression question gets COBRA, because it gives one cohort-level, covariate-adjusted answer. A paired TF-to-gene question gets LIONESS-PANDA, because per-sample edges allow within-patient tests. So does a TF-to-gene question with a confounder that must be adjusted (E1). An unpaired TF-to-gene question gets PANDA per group plus LIONESS-PANDA.
- **Individual questions.** These get per-sample workflows only, never COBRA or a single aggregate network.
- **Regulator questions.** "Activity" points to GIRAFFE, alone or with LIONESS-PANDA. "Activity apart from own expression" and "activating vs repressing" point to GIRAFFE alone. "Targeting" points to PANDA and/or LIONESS-PANDA, and to LIONESS-PANDA alone when the design is paired.
- **Empty `recommended_subset`.** It is left empty when nothing in the request separates the acceptable workflows. That includes the case where the acceptable set has two or more workflows and the request favours all of them equally (validator rule). With a single acceptable workflow, that workflow is recommended.
- **Cohort size.** It never narrows `acceptable_candidates` or `recommended_subset`. It appears only in `size_preferred`, which is set only on T5 (eight animals).
- **`comparison_design`** describes the sampling design the prompt states, even when the purpose asks for no comparison. That is why controls A3 and D3 are "paired" and B3, C3 and F3 are "groups". In the single-collection family it is "none", except E1, where the purpose itself defines two groups of different women.
- **Causal and prediction items.** `acceptable_candidates` lists workflows that fit the inputs and could supply supporting, descriptive evidence. `recommended_subset` is empty.

## Judgement calls I was unsure about

1. **A1 recommends only COBRA for a paired co-expression question.** Per-sample co-expression networks with paired tests (LIONESS-COEXPRESSION/BONOBO) are a reasonable first choice too. I leaned to COBRA because the question asks for one cohort-level answer, and pairing can go in its design matrix. A reviewer could argue for `[COBRA, LIONESS-COEXPRESSION, BONOBO]`, which would make the subset empty.
2. **Unpaired TF-targeting questions (B4, F4) recommend PANDA and LIONESS-PANDA, but the paired and confounded ones (D1, E1, T2) recommend LIONESS-PANDA alone.** This depends on a view that per-group PANDA cannot respect pairing or adjust for a covariate. It is defensible, but it is a modelling preference.
3. **F1 has an empty `recommended_subset`.** DRAGON per group and LIONESS-DRAGON with a group test both deliver a group-level two-layer contrast, and the request does not separate them. If the evaluation expects LIONESS-DRAGON as the "testable" choice, this label is too lenient.
4. **Expression-only individual questions (A2, B2, C2, T4) have empty `recommended_subset`.** Nothing in them separates LIONESS-COEXPRESSION from BONOBO.
5. **Non-TF questions over unstated priors are labelled `data_question: none`** (A1, A2, A3, B1, B2, F1, F2, F3). Some are worded generically ("gene networks"). A reply that offers LIONESS-PANDA "if you also have priors" is arguably helpful, not wrong. I scored only *asking before answering* as the red flag.
6. **B3 is a control with `data_question: priors`.** A TF-to-gene map cannot be built without priors, even though nothing is recommended for a control.
7. **C4 and T3 accept co-expression workflows (including COBRA) for a TF question with priors ruled out.** C4 asks about TF genes' "co-expression partners", which co-expression delivers. T3 asks about TFs' "network role", which co-expression only approximates. Arguably T3's acceptable set should be empty. The subset is empty in both.
8. **Family C's "RNA-seq counts, nothing else"** is read as ruling out priors but not the genotype labels that COBRA needs as a design matrix.
9. **GIRAFFE is acceptable for TF-to-gene maps and wiring comparisons** (B3, B4, D1, D3, E1, E3, F4) because it outputs signed regulatory effects. It is recommended only when activity or sign is asked.
10. **D4 accepts only GIRAFFE.** LIONESS-PANDA could show which TFs change, but not activation vs repression, which is the point of the question.
11. **E4 excludes PANDA and OTTER.** With a continuous age effect, per-group aggregates need arbitrary age bins. I judged them unable to deliver the purpose, rather than merely weaker.
12. **D2 and E2 exclude co-expression per-sample workflows** because the purpose says "regulatory networks". A lenient reader might accept them.
13. **T5 excludes LIONESS-COEXPRESSION** because it gives no edge confidence. Also, `size_preferred` BONOBO is a label only. Under the brief, the assistant may not call eight animals "few", so no must_include item requires a cohort-size statement.
14. **T6 accepts DRAGON and LIONESS-DRAGON** for miRNA-mRNA associations measured on the same samples. A stricter reading would accept only the PUMA family.
15. **T7 (causal) lists four motif/PPI workflows as acceptable "supporting evidence".** A strict reading of "can deliver what the purpose asks" would make the acceptable set empty.
16. **T8 is labelled `individual_change`.** The subtyping half is closer to a description (`none`). SAMBAR is the only fit either way.
17. **T1 says the infants "went on to develop" bronchopulmonary dysplasia.** I labelled it a retrospective `regulator_change` group comparison, not prediction. A reply that drifts into prediction is a red flag.
18. **Pooled controls are not flagged.** D3 (one network pooling both time points) and B3 (one map pooling patients and controls) pool their samples. A careful reply might mention this, but it is not in must_include.
19. **Precision and negation trap flags are a narrow reading.** I flagged only details that change the right workflow or answer. F4 (the methylation layer tempts DRAGON for a TF question) and T4 (separate mice per stage) carry trap-like details but are not flagged.

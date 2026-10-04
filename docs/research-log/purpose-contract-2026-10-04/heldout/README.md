# Held-out purpose-contract set (2026-10-04)

## How it was written

A subagent wrote this set from the brief alone. It did not open, list or search any project file, ran no agent and called no model API. It never saw the witness lists, the development prompts or the agent's code. The only project content it used was the two development data sentences quoted in the brief, which it was told not to reuse.

- There are 6 minimal-pair families with 4 prompts each, plus 2 standalone negation traps, for 26 prompts in total.
- Within a family, every prompt starts with the same data sentence, copied word for word. Only the closing purpose sentence differs, and each family has at least one control whose `claim_kind` is `none`.
- Each prompt is a single paragraph of 34-39 words and names no tool, package or file.
- The phrasing for each intent was varied by hand. One example is "pin ... on" for causal against "demonstrate ... causes", and another is "flag ... in a new cohort" against "predict" or "forecast".
- A build script checked the following before the file was written:
  - each `prompt` equals `data_sentence + " " + purpose_sentence`
  - the ids, label values and tool names are valid
  - word counts are within range
  - the family structure is correct and the coverage requirements are met
  - the development sentences are not reused

Coverage by `claim_kind`: group_difference 5, individual_change 5, regulator_change 3, causal 3, prediction 4, none 6. Coverage by data sentence: paired 4 (F1, F5, F6, N2), groups 3 (F2, F4, N1), none 1 (F3).

## Families

- **F1** (paired; expression + motif + PPI): human whole-blood microarrays from 18 kidney transplant recipients, taken before surgery and at 3 months.
- **F2** (groups; expression only): RNA-seq of postmortem prefrontal cortex from 40 schizophrenia donors and 40 age-matched controls.
- **F3** (none; expression + motif + PPI + miRNA): RNA-seq and small-RNA-seq from 120 hepatocellular carcinoma tumors, with no comparison stated.
- **F4** (groups; expression + motif + PPI): lung RNA-seq from 12 wild-type and 12 Nrf2-knockout mice after cigarette smoke exposure.
- **F5** (paired; expression only, very small n): thigh muscle RNA-seq from 6 volunteers before and after 10 days of bed rest.
- **F6** (paired; two omics): matched RNA-seq and DNA methylation from colon biopsies of 20 ulcerative colitis patients, before and after anti-TNF therapy.
- **N1** (trap, groups): adipose microarrays from lean and obese women plus priors. The user rules out causation, so the item is labelled group_difference.
- **N2** (trap, paired): blood RNA-seq from septic shock patients at ICU admission and on day 5, expression only. The user rules out a classifier, so the item is labelled individual_change.

## Judgement calls I was unsure about

1. **F2 "age-matched controls" is labelled `groups`.** The controls are matched but they are different people. A reader might mistake matching for pairing, so this item partly tests that confusion.
2. **F3-b is labelled `regulator_change` under design `none`.** The request asks which regulators vary most from tumor to tumor, not which change between conditions. You could argue for `none` instead.
3. **F4-a is labelled `causal` even though a knockout is a real intervention.** The must_include items say that the knockout design supports linking expression differences to genotype, but network inference cannot establish the rewiring mechanism. Reviewers may disagree about how far an answer has to hedge here.
4. **F1-c has a confound that is only implied.** Every recipient had surgery and immunosuppression, so a good answer should notice that there is no comparison group without the drug. I made that a must_include, which may be stricter than intended.
5. **COBRA is listed even though no covariate table is named.** It appears for F2-a, F5-b and F5-d because the data sentence makes a design table obvious (the diagnosis labels, or time point plus subject). If a reviewer reads "COV" strictly, it should be removed.
6. **Expression-only tools are left out of the candidate lists when priors are available.** LIONESS-COEXPRESSION, BONOBO and COBRA are not listed for F1, F4 or N1, which keeps the lists narrow. An answer that offers one of them as a secondary alternative is arguably not wrong.
7. **TF-only per-sample tools follow the wording of the F3 purpose.** LIONESS-PANDA and GIRAFFE are acceptable in F3-c and F3-d, where the purpose does not mention miRNAs. They are not acceptable in F3-a or F3-b, which ask about TFs and miRNAs together.
8. **DRAGON is not listed for F3, although it could be argued.** The mRNA and small-RNA matrices could count as "two paired omics". For F6, expression-only tools are not listed because they ignore the methylation data.
9. **F6-d lists only DRAGON.** The pre and post biopsies pooled into one map are repeated measures from the same patients. I did not make this a red flag.
10. **Prediction items do not state any outcome data.** In F3-c, F5-c and F6-c the outcome is not given, so the comparison design stays the one in the data sentence. The must_include items expect the answer to point out that outcome labels are needed.
11. **Each causal and prediction item lists tools that describe or feed the analysis, with a caveat.** These candidates do not mean the tool achieves the causal or predictive goal.

# heldout23: data-needs held-out set

32 prompts that test whether the methods adviser works out three things: what data the question needs, what data the user has for these samples, and so what it should ask and say.

## How it was written

- An isolated subagent wrote the set on 2026-10-06, working only from the task brief and its own scientific judgement.
- It did not read, list or search any repository file, prompt, log, earlier held-out set or code. It did not use git, run the adviser or call any model.
- The only files it created are `heldout.json` and this README. A throwaway validator lived in the scratch directory outside the repository.
- The validator checks:
  - the JSON parses;
  - `prompt == data_sentence + " " + purpose_sentence`;
  - every enum and workflow name is valid;
  - `recommended_subset ⊆ acceptable_candidates`, has at most 3 entries, and is empty for causal and prediction items;
  - acceptable, conditional and inapplicable candidates are disjoint;
  - the `data_question` rule holds exactly;
  - within a family, data sentences and labels are identical;
  - every prompt is 30-60 words and names no workflow;
  - all coverage counts are met.
- Everything passes.

## Families

The data sentence is identical within a family; only the purpose sentence changes.

| Family | Setting | How the data are worded | priors | miRNA | Items (purpose_kind → data_question) |
|---|---|---|---|---|---|
| A | 54 human corneal endothelium donors with ages | Plain words: "a table of which transcription factors target each gene's promoter and a list of which proteins physically interact" (avoids motif / prior / PPI / protein-protein / binding) | stated | unstated | A1 tf_network → none; A2 coexpression (age) → none; A3 mirna → **mirna**; A4 prediction → none |
| B | 72 gastric biopsies by H. pylori status | Resource names only: JASPAR motif scans, STRING interactions, TargetScan miRNA predictions "prepared for these samples" | stated | stated | B1 mirna+tf_group_difference; B2 tf_per_sample; B3 coexpression; B4 tf_group_difference+causal (all → none) |
| C | 40 brown trout livers, warm vs cold streams | Explicit negation: "we do not have transcription factor binding data, a protein interaction network or any microRNA data" | ruled_out | ruled_out | C1 tf_group_difference; C2 mirna; C3 coexpression group + per-sample; C4 prediction (all → none) |
| D | 36 iPSC cardiomyocyte cultures, doxorubicin dose + batch | Exhaustive, with no negation word and no "only": "Our dataset consists of RNA-seq counts plus a sample sheet ... and that is everything we have." | ruled_out | ruled_out | D1 tf_per_sample ("regulatory program"); D2 coexpression_per_sample; D3 causal; D4 coexpression + regulators (all → none) |
| E | 26 bladder wall biopsies | Expression assay only, no design | unstated | unstated | E1 tf_network → **priors**; E2 coexpression_per_sample → none; E3 prediction → none; E4 tf_per_sample+prediction → **priors** |
| F | 64 rice panicles, 2 cultivars × heat/control, batch | Expression assay plus design (groups, batch) | unstated | unstated | F1 tf_group_difference → **priors**; F2 coexpression (batch-adjusted) → none; F3 causal → none; F4 mirna → **priors** |
| G | 44 prostate biopsies by Gleason grade | Mentioned only: "a collaborator says a proper analysis would need transcription factor binding data and a protein interaction network" | unstated | unstated | G1 regulatory network → **priors**; G2 coexpression → none; G3 prediction → none; G4 causal (TF wording) → none |

## Standalone traps

- **T1 (mouse spleens, malaria).** The only TF wording is inside the PI's quoted email ("Find the transcription factors behind this response."). The user's own question is about co-expression, so `question_needs` is none and nothing should be asked. Asking for a motif prior or PPI network is a red flag.
- **T2 (granulosa cells, IVF).** One sentence says the user built the motif prior and PPI network for these samples "on our bioinformatician's advice". That is **stated**, even though the sentence also reports someone else's advice. The question is a TF group difference with no data question.
- **T3 (Drosophila wing discs).** The lab "plans to build" a motif prior and an interaction network next year, so the priors are **unstated**, not stated and not ruled out. The TF question gets data_question **priors**.
- **T4 (mesenchymal stem cells, bone).** The motif prior and PPI network are stated, but no miRNA data are. The question asks whether transcription factors or microRNAs are the main regulators, so data_question is **mirna**.

## Coverage (checked by the validator)

- 7 families × 4 items plus 4 traps = 32 items.
- 11 purposes are statements; the rest are questions.
- Prediction:
  - 5 items mention prediction.
  - 4 of them are pure prediction: A4, C4, E3, G3.
  - E4 is two-part.
- Causal:
  - 4 items mention causation.
  - 3 of them are pure causal: D3, F3, G4.
  - B4 is two-part.
- 5 of the causal or prediction items are in families where priors are unstated or only mentioned: E3, E4, F3, G3, G4.
- 5 two-part purposes: B1, B4, C3, D4, E4.
- 5 TF-type items use regulator wording with no "transcription factor" or "TF": B4, D1, D4, E4, G1.
- 3 co-expression items sit in families whose data sentence mentions transcription factors or binding data: A2, C3, G2. T1 is a fourth, via the quoted email.
- miRNA coverage:
  - data_question "mirna" (priors stated, miRNA unstated): A3, T4.
  - miRNA question with miRNA ruled out: C2.
  - miRNA question with priors unstated: F4, which asks about priors.

## Labelling notes and judgement calls

1. **miRNA question with priors unstated (F4) → data_question "priors".** A miRNA question needs both the TF priors and the miRNA data. The rule gives "priors" whenever the question needs TF priors and they are unstated, so F4 is "priors". `must_include` still expects the adviser to ask about the miRNA-target predictions too, and a red flag fires if it asks only about miRNA.
2. **A miRNA-plus-TF question with priors stated and miRNA unstated (A3, T4).** The TF methods go in `acceptable_candidates` because the TF half is answerable now. The miRNA workflows go in `conditional_candidates`. PANDA is the first recommendation only for the TF half, alongside asking for miRNA data.
3. **Ruled-out TF questions (C1, D1) have empty acceptable and recommended lists.** No registered workflow answers a TF question without priors. A co-expression method mentioned as a clearly labelled substitute is neither required nor a red flag. Offering it as *the* answer to the TF question would be wrong. D4 is different: its co-expression half is answerable, so COBRA is acceptable and recommended there.
4. **Ruled-out miRNA (C2) lists only the miRNA workflows as inapplicable.** The TF-only workflows don't fit a question that asks only about microRNAs.
5. **The exhaustive wording (D) rules out miRNA as well as priors.** "That is everything we have" closes the data list, so both labels are ruled_out.
6. **Causal and prediction purposes that use TF wording (G4) need nothing.** The question can't be answered by any network method, so asking for priors there is a red flag, even though priors are unstated in G.
7. **Two-part purposes take the stricter need.** If either part needs TF priors (B4, D4, E4), `question_needs` is tf_priors. The causal or prediction half is flagged in `must_include`: no registered workflow establishes causation or builds a predictor.
8. **Regulator wording maps to tf_priors**, even in family B where miRNA data are stated. In B4, "regulators" could cover microRNAs, so PUMA and LIONESS-PUMA are acceptable alongside the TF-only methods.
9. **Group labels and covariates.** COBRA is listed as acceptable only where the data or purpose sentence gives the grouping or covariate: age (A), infection status (B), stream (C), dose and batch (D), heat and batch (F), grade (G), infection (T1). Family E has no design, so its co-expression item is per-sample (BONOBO / LIONESS-COEXPRESSION), and with 26 biopsies BONOBO is recommended first.
10. **Mentioned versus stated.**
    - G (collaborator says data "would need") and T3 (planned) are unstated.
    - T2 (built on someone's advice, for these samples) is stated.
    - T1's quote changes neither the labels nor the question's needs.
11. **Family A wording** describes the motif prior and the PPI network only by what they contain. The validator confirms that none of motif / prior / PPI / protein-protein / binding appears in that data sentence.
12. **No DRAGON / LIONESS-DRAGON items.** No family measures two omics layers on the same samples. Family B's TargetScan predictions are a prior, not measured miRNA expression.

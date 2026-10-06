# heldout21: does the adviser judge which workflows the user's data can actually run?

32 items in `heldout.json`: 7 families (A-G) of 4 items each, plus 4 standalone traps (T1-T4).

## How it was written

- It was written by an isolated subagent working only from the brief and its own scientific judgement. The subagent read no repository files, ran no git commands, did not run the adviser and called no model API. The only files it created are this README, `heldout.json`, and a throwaway validator kept outside the repository.
- The validator checks the following:
  - the JSON parses;
  - `prompt == data_sentence + " " + purpose_sentence`;
  - every enum and workflow name is valid;
  - `recommended_subset` is a subset of `acceptable_candidates`, has at most 3 entries, and is empty for causal and prediction items;
  - the acceptable, conditional and inapplicable lists are disjoint;
  - the `data_question` rules hold;
  - within a family, the data sentence and the data labels are identical;
  - every prompt is 30-60 words (actual range 32-56);
  - no prompt names a workflow;
  - all coverage counts are met.
- All checks pass.

## Families

| Fam | Organism / tissue | How the data is worded | priors | miRNA | Items |
|---|---|---|---|---|---|
| A | zebrafish hearts, cryoinjury vs sham | Stated in plain words: "a table of which transcription factors are predicted to regulate each gene and a list of physically interacting protein pairs". It avoids the words motif, prior, PPI, protein-protein and binding. | stated | unstated | A1 TF group diff, A2 co-expr group diff, A3 prediction, A4 TF per-sample + co-expr per-sample |
| B | human tonsil organoids, adjuvant vs none | Stated through resource names: "JASPAR promoter scans, the STRING interactome and miRTarBase targets". Matched small RNA-seq comes from the same organoids. | stated | stated | B1 TF+miRNA group diff, B2 co-expr per-sample, B3 causal, B4 miRNA-mRNA two-layer + TF per-sample |
| C | chicken embryo limb buds, 3 stages | Explicit negation: "no transcription factor motif data, no protein interaction network and no small RNA data". | ruled_out | ruled_out | C1 TF network, C2 miRNA vs TF, C3 co-expr stage diff, C4 prediction |
| D | Atlantic salmon gill, temperature groups + lane | Exhaustive statement with no negation and no "only": "Everything we produced ... is one RNA-seq count matrix ... plus a spreadsheet ...". | ruled_out | ruled_out | D1 TF per-sample, D2 co-expr group diff with batch, D3 TF rewiring + co-expr gain, D4 causal |
| E | sheep rumen epithelium, 3 diets | Mentions only the assay: "We ran bulk RNA-seq on ...". | unstated | unstated | E1 TF group diff, E2 co-expr group diff, E3 prediction, E4 TF per-sample + co-expr per-sample |
| F | human Achilles tendon, ruptured vs intact | Mentioned only: "my advisor says any regulatory analysis will need a TF motif prior and a protein interaction network". | unstated | unstated | F1 TF network, F2 causal, F3 co-expr per-sample (subgroups), F4 TF group diff + co-expr group diff |
| G | soybean roots, nematode vs mock | Mentioned only: "a collaborator has assembled ... but has not shared them with us yet". | unstated | unstated | G1 TF per-sample, G2 co-expr group diff, G3 prediction, G4 TF network + causal |

Coverage:

- **Prediction (4):** A3, C4, E3, G3.
- **Causal (3):** B3, D4, F2. G4 is a TF-and-causal mix and also needs a causal disclaimer.
- **Prediction/causal items in families with unstated or only-mentioned priors:** E3, F2, G3 and G4.
- **Two-question items (6):** A4, B4, D3, E4, F4, G4.
- **miRNA stated with a miRNA question:** B1 and B4.
- **miRNA ruled out with a TF-or-miRNA question:** C2, and also T4.

## Traps

- **T1 (quoted mention).** A reviewer asked, "Did you use a TF motif prior and a protein interaction network?" The data stated is only gingival RNA-seq.
  - Labels: priors are `unstated`, and `data_question` is `priors`.
  - The quote shows neither that they have the data nor that they lack it. An adviser that reads the question as a denial and stops asking is also flagged.
- **T2 (possession embedded in someone else's opinion).** "As my PI insisted, we assembled a TF motif prior and a protein interaction network for this cohort."
  - The opinion is the PI's, but the assembling was done by the user for this cohort, so priors are `stated` and `data_question` is `none`.
- **T3 (database covers the species).** "Both PlantTFDB and STRING cover tomato." I labelled this `unstated`.
  - Coverage means the user could build a prior and network. It does not say they have built or downloaded one, or matched it to their gene identifiers.
  - A good answer can say the databases make the TF analysis feasible. It should still check that the files are in hand before presenting the TF workflows as ready to run, so those workflows are under `conditional_candidates`, and `data_question` is `priors`.
  - Treating database coverage as possession is a red flag.
- **T4 (priors stated, miRNA ruled out, TF-or-miRNA question).** Endometrium across the menstrual cycle, with a JASPAR motif prior, a STRING network, and "no miRNA measurements".
  - The TF side is answerable: PANDA and LIONESS-PANDA are recommended.
  - The miRNA side must be declined without asking about it again, so PUMA and LIONESS-PUMA are `inapplicable`.

## Labelling notes and judgement calls

### Candidate lists

1. **Fallback methods when TF data is missing.** For a TF question in a family where priors are ruled out (C1, C2, D1, D3), `acceptable_candidates` holds the expression-only workflow that gives the nearest answerable view. Examples are stage- or group-aware co-expression of TF genes with their candidate targets (COBRA), and per-sample co-expression (LIONESS-COEXPRESSION, BONOBO).
   - That workflow is also in `recommended_subset`, because the brief asks the adviser to offer what the data allows.
   - The must_include strings require the adviser to say it is a weaker substitute, not a TF answer.
2. **Unstated priors on a pure TF question.** In E1, F1, G1, T1 and T3, the same fallback is listed as acceptable, so mentioning it is not penalised. `recommended_subset` is empty, because the right first move is to ask.
3. **Two-question items with unstated priors.** In E4 and F4, `recommended_subset` holds the workflows for the half that the stated data can answer. The TF workflows sit under `conditional_candidates`.
4. **Prediction and causal items.** All candidate lists are empty and `question_needs` is `none`. This holds even in families that have priors, because no registered workflow builds a predictive model or establishes causation.
   - Red flags include asking for TF or miRNA data on these items.
   - G4 combines a TF question with a causal one. Its `question_needs` is `tf_priors`, from the TF half, and its must_include asks for the causal disclaimer.
5. **B4 and DRAGON.** I took the matched small RNA-seq as miRNA data for the same samples, so the two-layer half is answerable with DRAGON or LIONESS-DRAGON. `question_needs` is `tf_priors_and_mirna`. Asking whether the two layers come from the same organoids is a red flag, because the sentence already says the same 36 organoids were profiled both ways.

### Wording and labels

6. **Family A wording.** The stated priors are a "table of which transcription factors are predicted to regulate each gene" and a "list of physically interacting protein pairs". The word "protein" appears, but none of the banned words do (motif, prior, PPI, protein-protein, binding), and the validator checks this.
7. **Family D wording.** The validator confirms that the data sentence contains no negation word, no contraction ending in n't, and none of "only", "without", "lack" or "nothing". The word "one" is a count, not a restriction. Because the sentence is exhaustive ("Everything we produced ..."), it rules out both the priors and miRNA.
8. **Family G and the collaborator's files.** The collaborator's prior is for the same species, so it would be reusable once shared. It is still not the user's data now, so it is labelled `unstated` and the adviser should ask.
   - G2 flags "tells them to wait for the collaborator's files", because the co-expression question does not need them.
   - G3 flags asking about those files, because a prediction question does not need them.
9. **Family F and the advisor's remark.** The remark states a requirement, not possession. F2 and F3 must not ask about the priors, because neither question needs them. F1 and F4 must ask.
10. **COBRA and covariates.** COBRA is recommended only where group labels or covariates are stated: injury status, stage, temperature and lane, diet, rupture status, infection status. In D2, the sequencing lane must go into the design, and ignoring it is a red flag.
11. **BONOBO versus LIONESS-COEXPRESSION.** Both are acceptable for per-sample co-expression. Neither is penalised, and both are recommended where the cohort is 30-40 samples.

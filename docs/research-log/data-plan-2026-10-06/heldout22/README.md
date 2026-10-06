# heldout22: data-needs held-out set (2026-10-06)

32 English prompts (7 families x 4 + 4 standalone traps) that test whether the adviser works out
(1) what data the question needs, (2) what data the user actually has for these samples, and
therefore (3) whether to ask about missing data, say that ruled-out data blocks a method, or ask nothing.

## How it was written

- Written by an isolated subagent (Claude Opus 5.5) from the task brief and its own scientific
  judgement only. No repository file, earlier held-out set, prompt, log or code was read, listed or
  searched; git was not used; the assistant and model APIs were not run.
- Items were drafted by hand, written to `heldout.json`, and checked with a throwaway script (kept
  outside the repository) for: JSON parse; `prompt == data_sentence + " " + purpose_sentence`; enum
  values; workflow names; `recommended_subset` within `acceptable_candidates`, at most 3, empty for
  `causal`/`prediction`; acceptable / conditional / inapplicable disjoint; `data_question` derived
  exactly from the rule below; identical data sentence and shared labels within each family; 30-60
  words; no workflow name in any prompt; all coverage counts. All checks pass.

`data_question` rule used by the validator:
`priors` if the question needs `tf_priors` or `tf_priors_and_mirna` and `priors_label` is `unstated`;
`mirna` if it needs `tf_priors_and_mirna`, priors are `stated` and `mirna_label` is `unstated`;
otherwise `none`.

## Families

| Family | Setting | Data wording (how priors / miRNA appear) | priors | miRNA | Items |
|---|---|---|---|---|---|
| A | human dorsal root ganglia, pain vs no pain (32) | Plain words: "our own table of which transcription factors recognise which gene promoters and a list of which factors physically interact" (no motif/prior/PPI/protein-protein/binding) | stated | unstated | A1 TF + co-expression (two-part), A2 co-expression difference, A3 miRNA (asks mirna), A4 prediction |
| B | knee cartilage at joint replacement (48), mRNA-seq + small RNA-seq | Resource names: JASPAR scans, STRING interactions, TargetScan predictions for detected microRNAs | stated | stated | B1 TF+miRNA cohort network, B2 per-patient co-expression, B3 causal (names TFs and miRNAs), B4 per-patient TF + prediction |
| C | Duchenne muscle, 26 vs 20 | Explicit negation: "no transcription factor binding data, no protein interaction network and no microRNA measurements" | ruled_out | ruled_out | C1 regulator network (regulators wording), C2 co-expression difference, C3 miRNA (ruled out), C4 per-sample co-expression + prediction |
| D | keloid vs normal skin, 12 vs 10 | Exhaustive, no negation word, no "only": "Our complete dataset is RNA-seq counts ... that matrix is everything we have" | ruled_out | ruled_out | D1 regulatory network (regulators wording), D2 per-sample co-expression with edge confidence, D3 co-expression difference, D4 TF + co-expression |
| E | rheumatoid synovium vs joint-trauma controls (30/25), age, sex, batch | Expression assay plus design only | unstated | unstated | E1 regulatory program (regulators wording, asks priors), E2 covariate-adjusted co-expression, E3 prediction, E4 causal |
| F | postmortem human cerebellum (64), no design | Expression assay only | unstated | unstated | F1 per-sample regulator activity (asks priors), F2 per-donor co-expression, F3 prediction, F4 causal (regulators wording, needs none) |
| G | mouse islets, high-fat vs chow (20/20) | Mentioned only: a reviewer "insisted that any regulatory analysis must use transcription factor motif and protein-protein interaction data" | unstated | unstated | G1 TF difference (asks priors), G2 co-expression difference, G3 prediction, G4 regulators + causal (asks priors) |

## Standalone traps

| Id | Setting | Trap | Labels |
|---|---|---|---|
| T1 | bat wing membrane, white-nose syndrome vs healthy | The only TF wording is inside the supervisor's quoted note; the user's own question is co-expression | priors unstated, needs none, data_question none |
| T2 | Xenopus tail regeneration, six stages | Priors stated for these genes in a sentence that also reports the bioinformatician's advice | priors stated, data_question none |
| T3 | human aortic endothelial cells, laminar vs disturbed flow | "we are about to download JASPAR and STRING" (planned, not in hand) with a TF question | priors unstated, data_question priors |
| T4 | psoriatic vs healthy skin | Motif prior and PPI stated, miRNA unstated; TF-versus-miRNA regulator question | data_question mirna |

## Coverage (validator counts)

- Statements (purpose not ending in "?"): 12 (A1, A4, B1, C2, D1, D3, E2, E4, F1, G1, G3, T1).
- Prediction-only: 4 (A4, E3, F3, G3). Causal-only: 3 (B3, E4, F4). Of these, 5 are in E/F/G.
- Two-part purposes: 5 (A1, B4, C4, D4, G4).
- TF items worded with "regulators" / "regulatory network" / "regulatory program" and no TF words in the purpose: 5 (C1, D1, E1, F1, G4); D1, E1 and F1 have no TF words anywhere in the prompt.
- Co-expression items in families whose data sentence mentions transcription factors or binding: A1, A2, C2, C4, G2 (plus T1).
- `data_question = mirna`: A3, T4. miRNA question with miRNA ruled out: C3.
- `data_question` totals: priors 5 (E1, F1, G1, G4, T3), mirna 2, none 25.

## Labelling notes and judgement calls

- **Prediction and causal items** have empty candidate lists and `question_needs: none` even when the
  sentence names transcription factors, microRNAs or regulators (B3, F4). The adviser should say no
  registered workflow answers them and should not ask about data. F4 is the deliberate pair to F1: same
  data, "regulators" wording, but a causation-only question.
- **Two-part purposes** take the stronger data need (A1, D4, G4 → `tf_priors`; B4 → `tf_priors`;
  C4 → `none`). The non-network half (prediction, causation) is listed in `must_include` as something to
  flag, not as a candidate. `recommended_subset` is allowed for two-part items that include prediction or
  causation (B4, C4) because the network half is answerable.
- **Ruled-out priors with a TF question** (C1, D1, D4): TF methods go under `inapplicable`; acceptable is
  empty for TF-only questions. I did not list co-expression methods as acceptable for a TF-only question,
  even though an adviser may mention them as a lesser alternative; for D4 they are acceptable because
  the second half asks about co-expression.
- **Family D** reads as ruling out miRNA as well as priors, because "that matrix is everything we have"
  is an exhaustive statement; same for family C via explicit "no microRNA measurements".
- **Family A** wording: "a table of which transcription factors recognise which gene promoters" and "a
  list of which factors physically interact" are treated as a motif prior and a PPI network. "our own"
  marks them as the user's data for this project.
- **Family B**: JASPAR / STRING / TargetScan are named as already obtained ("we have ... plus"), so all
  three are stated; contrast with T3 where JASPAR and STRING are only planned. B1 lists only the
  aggregate miRNA-aware workflow as acceptable because the user asks for one cohort-level network; the
  per-sample variant is acceptable in B4 only for its per-patient TF half.
- **Family G**: the reviewer's sentence names exactly the right data types but says nothing about the
  user having them, so priors are `unstated` (ask), not `stated` and not `ruled_out`. Red flags cover
  both errors.
- **T2**: "as our bioinformatician advised, we have already assembled ..." is labelled `stated`; the
  advice clause is the distractor.
- **T4**: TF-only workflows are `acceptable` (the TF half can run on the stated priors) while the
  miRNA-aware workflows are `conditional`. `recommended_subset` is left empty because the question is a
  TF-versus-miRNA comparison that cannot be answered until the miRNA data question is settled; a reply
  that mentions the TF half can run now is fine. A3, by contrast, is miRNA-only, so its acceptable list
  is empty.
- **Per-sample co-expression**: BONOBO is recommended first only where the cohort is small or per-edge
  confidence is asked for (D2, D3); elsewhere the per-sample co-expression workflow is recommended and
  BONOBO is acceptable.
- **Two-omics family B**: DRAGON-type analyses would be possible (mRNA and small RNA on the same
  samples), but no B purpose asks a cross-omics question, so DRAGON / LIONESS-DRAGON appear nowhere.
- Word counts use whitespace splitting (hyphenated words count once); all prompts are 35-56 words.

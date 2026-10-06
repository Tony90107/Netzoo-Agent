# heldout20: data-applicability evaluation set

32 prompts (7 families x 4, plus 4 standalone traps). They test whether the methods adviser judges each workflow against the data the user actually has, not just against compatible file formats.

## How it was written

- An independent subagent wrote it on 2026-10-06, working only from the task brief and its own scientific judgement.
- It did not read, list or search any repository file, earlier evaluation set, assistant code or log. It did not use git, run the assistant or call a model API.
- One throwaway script in `/private/tmp/claude-501/heldout20-scratch/` validated the set. It checked:
  - the JSON parses;
  - `prompt == data_sentence + " " + purpose_sentence`;
  - the enums and workflow names are valid;
  - `recommended_subset` is a subset of `acceptable_candidates`, has at most 3 entries, and is empty for causal and prediction items;
  - the three candidate lists do not overlap;
  - `data_question` is consistent with the labels, in both directions;
  - within a family, the data sentence and labels are identical;
  - every prompt is 30-55 words and names no workflow;
  - the coverage counts match the brief.

  All checks pass.
- Prompts are 31-49 words.

## Families

| Family | Data sentence (shared by its 4 items) | priors | miRNA | Purposes (1-4) |
|---|---|---|---|---|
| A | Human airway cultures, rhinovirus vs mock, plus "maps of where transcription factors bind … and of which proteins physically contact each other" (plain words, no motif/prior/PPI/protein-protein) | stated | unstated | TF network · co-expression group difference · miRNA (ask) · causal |
| B | Mouse retinas, light damage vs sham: RNA-seq **and small-RNA-seq on the same samples**, plus JASPAR, STRING, TargetScan | stated | stated | TF group difference · miRNA (+TF) · per-sample co-expression · prediction |
| C | Honeybee brains, foragers vs nurses; "we have **no** binding-site, protein-interaction or microRNA data" | ruled_out | ruled_out (explicit) | TF group difference · co-expression modules by group · miRNA · per-bee network |
| D | Arabidopsis seedling pools, 22 vs 28 degrees, dawn/dusk; "We **only** have RNA-seq counts" | ruled_out | ruled_out (implied) | per-sample TF activity · co-expression by temperature · prediction · causal |
| E | Axolotl blastemas vs intact limbs; "that table is the **entirety** of what we produced" (no negation word, no "only") | ruled_out | ruled_out (implied) | TF network · per-limb co-expression · causal · prediction |
| F | Ulcerative colitis colon biopsies, active vs remission; expression assay only | unstated | unstated | TF group difference (ask) · co-expression by state · per-biopsy TF activity (ask) · prediction |
| G | Grapevine berries across ripening, two vineyards; expression assay only | unstated | unstated | TF group difference (ask) · per-berry co-expression, small n · causal · co-expression by vineyard adjusted for stage |

### Coverage

- 4 causal items: A4, D4, E3, G3.
- 4 prediction items: B4, D3, E4, F4.
- 6 items where a good answer must ask about data:
  - priors: F1, F3, G1, T1, T2;
  - miRNA: A3.

  The other 26 must not ask.
- Every family has at least one TF item and at least one gene co-expression item.
- I added one field outside the brief's schema, `purpose_kind`, so the validator could tell causal and prediction items from co-expression items. Scorers can ignore it.

## Standalone traps

| Id | Trap | Labels | Expected behaviour |
|---|---|---|---|
| T1 | "My supervisor says we need a motif prior"; the user's own data is mouse-lung RNA-seq only | priors unstated, ask | Ask whether they actually have a motif prior and a PPI network. Mentioning the prior is not having it. |
| T2 | "Last year we used JASPAR motifs and a STRING network on a different pig cohort"; this year: piglet jejunum RNA-seq | priors unstated, ask | Ask whether those resources are available for this dataset (they could be reused or rebuilt). Do not assume they are. |
| T3 | One sentence states CIS-BP motifs and a BioGRID network but "no microRNA measurements or target predictions"; the question asks about TFs **or** miRNAs | priors stated, miRNA ruled_out | Run the TF part without asking. Say the miRNA part is impossible. Do not ask about miRNA. The miRNA-aware workflows are inapplicable. |
| T4 | Dog osteosarcoma RNA-seq with JASPAR and STRING "both downloaded for human" | priors stated (judgement call) | Proceed with TF networks, but say that TFs and genes must be mapped to dog orthologs first. |

## Labelling notes and judgement calls

1. **miRNA questions need `tf_priors_and_mirna`.** Under the brief, the only miRNA-capable workflows (PUMA, LIONESS-PUMA) need the motif prior and PPI as well as miRNA data.
   - A3: priors stated, miRNA unstated. The ask is `mirna` only. Re-asking about the stated binding maps is a red flag.
   - C3: both ruled out, so nothing is asked and the miRNA workflows are `inapplicable`.
   - No item has both priors and miRNA unstated together with a miRNA question. That would need two asks, which the single-valued `data_question` field cannot hold.
2. **Expression-only families rule out miRNA by implication.** D ("only RNA-seq counts") and E ("the entirety of what we produced") rule out downloadable miRNA-target predictions for the same reason the brief says they rule out downloadable motif and PPI priors. Both are labelled miRNA `ruled_out`.
   - C is the one family that rules out miRNA explicitly in its data sentence.
   - No D or E item asks a miRNA question, so this choice never changes an expected ask.
3. **Fallback for a TF question when the priors are ruled out** (C1, D1, E1). The brief requires the adviser to offer "what their data does allow". I therefore put an expression-only fallback in `acceptable_candidates` and `recommended_subset`:
   - COBRA for group-level questions (C1, E1);
   - LIONESS-COEXPRESSION for the per-sample question (D1).

   The TF workflows are listed as `inapplicable`. `must_include` requires the adviser to frame the fallback as gene-level, not as an answer about TFs.
4. **Fallback for a TF question when the priors are unstated** (F1, F3, G1, T1, T2). Here `acceptable_candidates` and `recommended_subset` are deliberately empty and the TF workflows are `conditional_candidates`. The adviser should ask first; recommending a co-expression method first would dodge the question. Mentioning a fallback after asking is fine.
5. **Causal and prediction items** have `question_needs: none` and every candidate list empty. No registered workflow answers them, so asking about priors for them is a red flag. This matters most in the unstated families (F4, G3), where an adviser might ask about priors reflexively.
6. **Gene co-expression questions when the priors are stated** (A2, B3). The trap is offering a TF or miRNA network because the files are there, which is format compatibility rather than applicability. COBRA is recommended when the question compares groups or adjusts for covariates. LIONESS-COEXPRESSION and BONOBO are recommended for per-sample networks. BONOBO is preferred where the cohort is small (G2 says "so few", n = 22; E2 has 18 per group).
7. **B2 accepts DRAGON** as a secondary option. The small-RNA and RNA-seq layers were measured on the same retinas, so DRAGON can give associative miRNA-to-gene edges. PUMA is the recommendation because the question also asks about TFs.
8. **C4** ("a separate network for each bee") does not name a network type. With priors ruled out, the per-sample TF workflows (LIONESS-PANDA, GIRAFFE) fit the wording but are `inapplicable`. The expected answer is per-sample co-expression (BONOBO, LIONESS-COEXPRESSION), so `question_needs` is `none`.
9. **Why T4 counts as stated.**
   - TF DNA-binding domains and their motifs are strongly conserved across placental mammals.
   - Most dog genes have one-to-one human orthologs.
   - Mapping human JASPAR and STRING resources through orthologs is standard practice for species without curated resources.

   So the adviser should treat the priors as present, with a mapping caveat, and not ask for them as if they were absent. I would label this differently for a distant species, for example human priors for a fish, an insect or a plant. There the priors would not stand in for the sample species, and the right move would be to ask about species-appropriate resources.
10. **T2 is labelled unstated**, even though the user clearly can get JASPAR and STRING. The user stated the resources for a past cohort, not for this dataset, so a one-line check is expected rather than an assumption.
11. **Wording constraints held:**
    - Family A avoids "motif", "prior", "PPI" and "protein-protein" in all four prompts.
    - Family E's data sentence contains no negation word and no "only" or "just".
    - No prompt names a workflow; the animals that share a workflow's name are avoided too.
    - No topic from the brief's avoid list is used.

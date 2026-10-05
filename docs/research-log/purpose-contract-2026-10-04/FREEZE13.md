# Log 370 freeze: a tie led by what fits the stated question, every candidate kept

**Superseded before the held-out set was read (2026-10-05):** the user asked that the lines not explain the
algorithms, only why each workflow is recommended for the question. The live freeze is now `q_frozen.patch`,
sha256 `d1e48608078c`: the "Method: ..." part of each line is removed (the unused `how_it_works` with it); a
recommended line is "- **X** — <its cell>" and a later one "- **X** — <reason>.". Nothing else changed.
Seen data unchanged except length: 107,485 vs 232,046 characters on the 98 fired trials. The earlier
`p_frozen.patch` is kept for the record.

Frozen before anyone on the implementing side read the thirteenth held-out set (`heldout13/`),
which an isolated subagent writes after this freeze.

- Frozen change: `p_frozen.patch` (the whole working-tree diff of `scripts/` and `tests/` against HEAD
  `6be7632`, the new `interpretation/intent_shortlist.py` included), sha256 `ef08bab59bdf`.
  Reply and card only; no contract, prompt, model call or decision change.
- `ClaimSupport` gains `answers` ("test" / "describe" / "other"), `limit` (a few words for why a cell comes
  later) and `quantity_axis`. Aggregate cells for group difference, paired comparison and regulator change
  and DRAGON's group cells are "describe"; GIRAFFE's cells are "other" (TF activity, not wiring) unless the
  question names activity (the `tf_activity_vs_expression` axis witness on the verified quote).
- `intent_shortlist` (only an `outcome_clarification` tie, one reading, a verified question, no causal or
  prediction claim): rank direct 5 > test 4 > describe 3 > other 2 > undeclared 1 > one result for individuals 0;
  not recommended: a workflow needing an input the request's own words never name that the others do not
  need, a one-layer workflow when two omics layers are named, a miRNA workflow when miRNAs are not mentioned.
  Recommended: the best (up to three), plus its aggregate base when one is best; only when the best at least
  describes the answer and the list is shorter than the candidates.
- Reply: "For your question (...), these fit best, and here is why:" then per recommended workflow "Method:
  <mechanism tags, SELECTION_TAG_GLOSSARY>. For your question: <its cell>", its caveats, then "The other
  registered options, and why they come later:" one line each (reason, then method), a question naming the
  recommended, and the original assumption and closing paragraphs. Every candidate is named.
- Card: the method card lists the recommended first with "Recommended" (none added or removed), its
  ordering line says so, and a first point names them; "Nothing you said favours one method yet" is dropped.
- Seen data (s7-s12 candidate arms, 480 trials; live/seen-intent-analysis.txt): fired 98; recommended within
  acceptable 98/98; against recommended_subset (heldout9, 12 labelled) exact 9, overlap 3, disjoint 0; on
  controls/causal/prediction 0; candidates missing from the reply 0; replies changed without a shortlist 0;
  cards that lost or gained an option 0; reply length on fired trials 143,769 vs 232,046 characters.
  Known limit: S6-b (nine patients, "how confident can I be in each edge") recommends LIONESS-COEXPRESSION and
  BONOBO where the label names BONOBO only; stated conditions such as per-edge confidence are not used.
- Suite: 3280 passed / 35 skipped (base 3275; 5 new; 4 pinned tie tests updated to the new layout);
  fingerprints legacy e920bf3b5d57, claims 743b2dd0d73a -- unchanged.

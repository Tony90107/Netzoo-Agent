# "What result do you want?" offers a fixed menu of result families (2026-11-01, user: "Yes, write it")

## Why

clarify-options (`clarify-options-2026-11-01/RESULTS-OFFLINE.md`): Jev's suggested results reached a gold workflow on
2 of 40 gold-CLARIFY-then-DO turns -- its read of a vague request is peaked (one result, or "none"), so it cannot
supply alternatives. The CLARIFY question asks what kind of result the user wants; the registry's results fall into a
few families, and a fixed menu of them covers every answer by construction, with no model.

## Change (code only after this file is committed)

Branch `clarify-menu` from main fc3c7753. Flag `NETZOO_CLARIFY_MENU`: off (default) / on. Only the CLARIFY card changes
(the call, the routing and every check are untouched).

1. `interpretation/result_families.py`: eight families, each a fixed sentence in the user's terms and the capability
   sheet's produce entries it covers (every produce entry in exactly one family -- checked by a test):
   1. one regulatory network (TF/miRNA to gene) from all samples -- PANDA, PUMA, OTTER, GIRAFFE's signed matrix,
      COBRA's adjusted regulation;
   2. a regulatory network for each sample -- LIONESS-PANDA, LIONESS-PUMA;
   3. a gene-gene co-expression network for each sample -- LIONESS-COEXPRESSION, BONOBO;
   4. how covariates (group, batch, age ...) change gene co-expression -- COBRA;
   5. each transcription factor's activity in each sample -- GIRAFFE;
   6. a network linking two kinds of omics data (e.g. RNA and methylation) -- DRAGON, LIONESS-DRAGON;
   7. modules / communities in a regulator-gene network -- CONDOR;
   8. patient subtypes from somatic mutations -- SAMBAR.
   Each family's comparison and test entries (condition comparison, association tests, enrichment, clinical
   comparison) belong to the family of the result they test.
2. The `clarify_goal` card gets one button per family (label: the sentence with its workflows; the click sends "I
   want <sentence>.") and the row for the user's own words. Nothing is bound in code; the follow-up turn reads the
   request with the reply, as every follow-up is read.

## Gates

### Offline (pure code)

- **R1 (hard)**: every produce entry of the sheet in exactly one family; at most 8 families (the card's limit); every
  gold workflow of the 40 recorded gold-CLARIFY-then-DO turns (clarify-options' targets) is in a family (100%).
- **R2 (hard, build)**: unit tests; flags-off replay byte-identical to `sa-off.json`; clean-env suite no new failures;
  with the flag on, every card other than `clarify_goal` identical.

### Live (after R1-R2 and the user's go-ahead; 12 conversations, about US$0.07, cap US$0.12)

The j9 and j10 gold-CLARIFY items whose gold after the reply is DO and whose recorded turn 1 was CLARIFY (A07, A29,
A36, B28, B29, B36), 2 runs each, flag on with the app's other flags. When turn 1 is a CLARIFY with the menu, the
scripted user clicks the family holding the item's gold workflow (fixed in advance in `CLICKS.json`); otherwise the
item's recorded reply rule.
- **L1 (hard)**: no conversation ends worse than its recorded current-system run (same item, typed `reply_result`).
- **L2 (target)**: >= 70% of the clicked conversations end at the gold call.

**Stop rule.** R1, R2 or L1 fails -> withdrawn, code reverted. L2 fails with the rest passing -> no claim; the user
decides. Merging needs the user; the flag stays off by default.

# Step 1′ — typed data checks (declared 2026-10-27, before any call)

The user approved a redesign after step 1 (prose lines, CONDITIONS.md) failed: Jev misread numeric comparisons and
alternatives inside one contract. Here Jev answers only closed questions about the user's data. Code compares the
answers with typed contract fields. Numbers are not judged here (min_samples, features>samples, max_values and
kmax<=samples stay with the existing code checks).

## Typed questions (one Jev call per DO call)

1. `data` (always): "Which kind of data does the user say the analysis should be built from?" Options = the
   registry's `input_artifacts` vocabulary, each with a one-line description: expression_matrix, coexpression_network,
   mutation_matrix, regulatory_network, measurement_dataset, plus `several` and `not_stated`.
2. `same_samples` (only when the call includes DRAGON or LIONESS-DRAGON, whose contract says "Layer 2 is reordered to
   layer 1 only after exact sample-ID set equality is proven."): "Does the user say the two data layers were
   measured on the same samples?" Options: yes / no / not_stated.

## Code rule

A workflow of the call is ruled out when:
- `data` (confidence >= 0.7) is in its `incompatible_input_artifacts`; or
- its input_checks has `refuses_input:coexpression_matrix` and `data` = coexpression_network; or
- it is DRAGON / LIONESS-DRAGON and `same_samples` = no (confidence >= 0.7).

Flag only when every workflow of the call is ruled out. Then the breaking sentence is picked by the same second call
as step 1. A flag plus a sentence gives a confirm ASK `jev_condition` quoting the sentence and the typed contract
field or line; step 3 reads the answer.

## Offline test

Same data (conditions-data.json, 124 DO calls) and the **same gates as step 1, not loosened**: C1 gold-DO flags
<= 4 of 79 and DRAGON controls <= 1; C2 gold-DECLINE flags >= 6 of 16; C3 fixes >= 2 x gold-DO flags.

Reported beside them: how many of the 16 targets are about the data type or sample matching at all (in-scope
recall). The `same_samples` question was designed after seeing J11, so a pass would still need a fresh confirmation
set before any live use.

## Result (CONDITIONS-OFFLINE-TYPED.txt, US$0.0031) — NOT PASSED (C2 by one)

- C1 **pass**: 0 of 79 gold-DO calls flagged; DRAGON controls 0 of 6.
- C2 **fail**: 5 of 16 gold-DECLINE flagged (>= 6): M46 (COBRA matrix into LIONESS-PANDA), C27 and W18 (expression into
  SAMBAR), J11 (different patients), J24 (mutation matrix into LIONESS). Every flag had its sentence.
- C3 pass: 5 fixes, 0 needless asks.

The 11 misses: 8 are settings or limits (M25, C30 SAMBAR k range; J44 OTTER gpu/precision; H18 lambda_inter; H40,
L21 GIRAFFE optimizer; C14 OTTER L1 penalty; W20 BONOBO), 2 ask for a result no workflow gives (J15 miRNA activity,
C47 survival model), 1 is a data type (C18: CONDOR on an expression table). In-scope recall: 5 of 6.

## Post hoc (CONDITIONS-TYPED-POSTHOC.txt; not a gate)

Also ruling a workflow out when the read data is a single kind outside its `input_artifacts` catches C18 too: 6 of 16,
still 0 of 79 false. Not adoptable from this data: that rule and `same_samples` were both shaped after seeing these
cases. A declared round on a fresh set would be needed before any live use.

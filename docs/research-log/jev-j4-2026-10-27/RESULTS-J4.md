# j4 two-arm run (PLAN-J4.md): NOT PASSED (O1, C1)

Frozen code ce8be114 (main, with all three Jev layers); j4 sealed (items.json d075b479…). Arm F has all three flags
off; arm G has all three on. gpt-4o-mini, up to 3 turns, 48 conversations each. Spent US$0.495 for both arms
(F 0.227, G 0.268; cap 1.30), and the runtime code was unchanged in both. Raw: RESULTS-J4.txt, gates-j4.json, live/.

| | final right | FA | FR | MA | extra q | UNCHECKED |
|---|---|---|---|---|---|---|
| F (all off) | 36/48 | 4 | 6 | 2 | 0 | 0 |
| G (all on) | **38/48** | **2** | **3** | **0** | 2 | 2 |

| gate | result |
|---|---|
| O1 G >= F + 4 | 38 vs 36 **fail** |
| O2 FA/FR/MA not up | 4->2, 6->3, 2->0 **PASS** |
| O3 no Jev-made decline on a non-DECLINE gold | none **PASS** (3 jev_answer declines, all on T items, all right) |
| O4 form reasons not asked for | F 6 (S10 S12 S22 S27 S32 S39) -> G 0 **PASS** |
| C1 11 controls DECLINE, never asked a form question | never asked: 11/11; DECLINE: 10/11 (S22 ends DO) **fail** |
| C2 form traps wrong in F, right or waiting in G | 6 wrong in F; G right S02 S12 S39, waiting S05 (4/6) **PASS** |
| S0 J-ask false alarms on gold-DO | 0 **PASS** |
| S1 step 1'' on T DO calls / TC | 3/3 confirmed (S17 S21 S42, all then declined right); TC 0 **PASS** |
| S4 V links | 0 **PASS** |

As declared: the merged system shows no fresh-set gain at the +4 bar, and C1 is reported against the forms layer for
the user to decide.

## Post hoc (labelled; not gates)

- **C1, S22** (a DRAGON metabolite-protein network given to CONDOR): in arm G, gpt-4o-mini typed
  `input_network=none` and credited CONDOR, so the row was available and the call DO. No Jev layer acted. The forms
  read only checks a typed value that refuses, so a misread in the permissive direction (`none` / `not_stated` for a
  network that is not regulator-gene) is never read. Arm F's reading of the same item refused it.
- **S05** (FN): the network question was asked three times. The reply in natural words ("The sources are all
  transcription factors and the targets are the genes they're predicted to regulate") never bound in code, because
  binding needs an option's words, and each re-read typed `gene_gene` again. The item ended waiting (C2 counts it
  apart).
- **S32** (T, expression matrix to SAMBAR): turn 1 typed several_groups, overlap was doubted, and the group
  question came before the data-type refusal. Turn 2 listed the same group question twice, once per quote. The
  item's confirm reply did not bind, and turn 3 ended at the round cap with no call. A question about a form does not
  wait for the data check that would refuse anyway, and duplicate form questions are not merged.
- **S10** (V, reply asks protein-metabolite communities): overlap was doubted rightly, but the real blocker (the
  network kind) was typed `not_stated`. The system kept asking the group question, and the final is ASK, not DECLINE.
- Other G misses: S18, S27 (credited to nothing, or another blocker; the wrong reason is no longer said), S45
  (refused in both arms), S43 (FA in both arms), S03, S35 (UNCHECKED).
- Per item: 7 improved (S02 S12 S17 S21 S26 S39 S42), 5 regressed (S03 S10 S18 S22 S32); exact sign test p = 0.77. The regressions are reading
  variance (S18, S22) and the form question path (S10, S32, plus S03 UNCHECKED).

j4 is now seen.

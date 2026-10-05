# heldout12 — individual-vs-cohort scope set (32 items)

## How it was written

- Written by a subagent working in isolation. It did not read, list or search any repository file, did not run the assistant and did not call any model API. The only input was the brief: the 13 registered workflows, the label definitions, the coverage rules and the avoid-list of earlier scenarios.
- Every label is the author's own scientific judgement of the request, using only the brief.
- The items were built and checked in a throwaway script (scratchpad, not committed), then written here. The script checked that:
  - the JSON parses;
  - `prompt == data_sentence + " " + purpose_sentence`;
  - all enum values and workflow names come from the brief, and there are 2-3 `must_include` and 2-3 `red_flags`;
  - every prompt is 29-45 words (actual range 35-44) and contains no workflow name and no path;
  - each family shares its data sentence word for word and keeps `samples_per_individual` constant;
  - families split 4 "one" / 2 "many", data types and designs are covered, and `is_control == (claim_kind == "none")`;
  - the T1-T8 constraints hold, including that T1 and T2 avoid "whose", "find the ones that", "a score for each" and "rank them";
  - no motif-based candidate appears without a stated motif prior, no PUMA-family candidate without miRNA data, and only DRAGON-family candidates appear on two-layer items;
  - no aggregate-only workflow is accepted for an individual question when each individual gave one sample;
  - none of about 130 keywords from the avoid-list appears.
- The question this set asks: when a request asks about individuals, does the reply say clearly what a one-result-for-all-samples workflow can and cannot give? And does it stay quiet about that when the request asks about the cohort, a group comparison or regulators, or only wants a network?

## Families (4 items each; a = individual, b = cohort/group, c = control, d = extra)

| Family | Data (shared sentence) | Inputs | Per individual | Design | d item |
|---|---|---|---|---|---|
| F1 | Chronic migraine whole blood, one draw before and one after 3 months on a CGRP antibody (38 adults) | expression only, **said outright** ("only have RNA-seq expression") | one | paired before/after | negation that rules out patients, then a group question about modules |
| F2 | Canine mitral valves, 22 dogs with myxomatous valve disease vs 18 without | expression only, **implied** ("sequenced RNA", no priors mentioned) | one | two groups | indirect individual question (which dogs belong to a suspected subtype) |
| F3 | Lymphoblastoid cell lines, 160 unrelated donors, one line each | expression + TF motif + PPI | one | single collection, no comparison | regulator question (TF activity variability line to line) |
| F4 | Acute stroke blood at admission, day 3 and day 90 (34 patients) | mRNA + miRNA + TF motif, PPI, miRNA-target priors | one (three time points) | paired, 3 time points | regulator question (which miRNAs change targeting) |
| F5 | Recurrent bacterial vaginosis, 8 women, self-collected swabs twice weekly for 4 months (~30 each, stated) | expression + TF motif + PPI | **many** | dense series; b adds relapse groups | indirect individual question (did any woman reorganise, and when) |
| F6 | 60-day head-down bed rest, 9 volunteers, blood every other day with RNA-seq + DNA methylation on each draw (~30 each, left for the reader to work out) | two omics layers, same samples | **many** | dense series; b/d add time contrasts | negation that rules out volunteers, then a group time-trend question |

## Standalone items

| Id | Scenario | What it tests |
|---|---|---|
| T1 | Duchenne muscular dystrophy muscle, mRNA + miRNA with priors, one biopsy per boy | individual question without the usual words ("Does any boy stand apart…") |
| T2 | Grey seal pup blood at weaning and after the post-weaning fast | individual question without the usual words ("Do some pups rewire … far more than others do?") |
| T3 | Angiotensin-II aneurysm mouse aortas vs saline controls, motif + PPI | cohort question with "Across all 50 aneurysm mice" in passing (precision trap) |
| T4 | Zebrafish tail fin, intact vs regenerating, same fish | cohort paired question with "In every fish, on average" (precision trap) |
| T5 | Sickle cell disease blood, frequent crises vs none, motif + PPI | "We don't need anything patient by patient" followed by a regulator question (negation trap) |
| T6 | Aged mice, 30 laser-captured colonic crypts per mouse, motif + PPI | individual question where each mouse has many samples, so an aggregate workflow run per mouse is acceptable |
| T7 | Dairy calf blood at one week, later respiratory disease, motif + PPI | prediction request |
| T8 | Infant thymus, Down syndrome vs not, motif + PPI | "a score for each transcription factor": individual-sounding words on a regulator question (precision trap) |

## Labelling rules applied

1. **claim_kind** follows what the purpose sentence wants to conclude, not the words it uses. "Which TFs…" is `regulator_change` even when phrased as "a score for each" (T8) or "from line to line" (F3d). "Across all 50 mice" and "in every fish, on average" are `group_difference`.
2. **comparison_design** is read from the whole prompt:
   - When the data sentence names conditions or groups (before/after, admission/day 3/day 90, affected vs healthy), every item in that family takes that design, controls included.
   - When the data is a single collection or a dense series with no named contrast, the design is `none` unless the purpose adds one: sex groups in F3b, relapse groups in F5b, early vs late or a time trend in F6b/F6d.
   - T7's outcome groups (ill vs healthy calves) are counted as `groups`.
3. **samples_per_individual**:
   - "many" = about 30 samples per individual (F5, F6, T6).
   - "one" = one sample per individual or per time point, and also F4's three time points per patient, following the brief's "only a few time points".
4. **Expression-only items** accept only LIONESS-COEXPRESSION and BONOBO. COBRA is added when the purpose is a cohort-level or group-level question with a covariate or pairing factor (F1b, F1d, F2b, T4).
5. **PUMA family** only where miRNA data and a miRNA-target prior are stated. **DRAGON family** only, and always, on the two-layer family.
6. **Aggregate workflows (PANDA, PUMA, OTTER, DRAGON)**:
   - Accepted for individual questions only when each individual has many samples (F5a, F6a, T6). They are then run once per individual.
   - Not accepted when the question needs *when* or *which sample* inside an individual (F5d).
7. **GIRAFFE** is accepted when per-sample TF-level estimates or regulator-level answers suffice (F3a, F3d, F5b, F5d, T5, T6, T7). It is not accepted when the purpose asks for TF-to-gene edges, targeting or a network as such (F3b, F3c, F5a, F5c, T3, T8).
8. **Aggregate-only controls** accept LIONESS-PANDA, because the brief says it also returns the aggregate. They do not accept LIONESS-PUMA or LIONESS-DRAGON, because the brief describes those only as per-sample (F4c, F6c).
9. **Trap flags**:
   - `is_negation_trap` marks items that explicitly rule individuals out (F1d, F6d, T5).
   - `is_precision_trap` marks items that use individual-sounding wording in passing for a non-individual claim (F3d, T3, T4, T8).
   - The two flags never overlap.
10. **must_include / red_flags**:
    - For individual items with one sample each: the reply should say that a single pooled network cannot answer, and that each individual's change is one unreplicated difference.
    - For individual items with many samples: the reply should say an aggregate workflow per individual works, and a red flag is claiming it cannot.
    - For cohort, regulator and control items: one red flag is always an individual-level caveat nobody asked for.

## Judgement calls I was unsure about

1. **Controls in the expression-only families (F1c, F2c) ask for per-sample networks, not one pooled network.** Under the brief, no expression-only workflow cleanly gives one aggregate co-expression network. COBRA with an intercept-only design arguably does, but that seemed too much of a stretch to label. As a result these two controls naturally lead to per-sample workflows. They still test that the reply draws no conclusion and adds no caveat about individuals.
2. **The design label of controls over paired or grouped data** (F1c, F2c, F4c are `paired`/`groups`). Another labeller could reasonably mark them `none`, since the control does not ask for a comparison.
3. **F3b brings in a sex comparison** inside the "single collection, no comparison" family. The data sentence has no contrast, but a cohort-level claim needs something to compare, and a continuous covariate such as age fits none of the claim definitions cleanly.
4. **F3d is marked as a precision trap.** Ranking TFs by variability across lines really does need per-sample estimates, so a reply that says "a single aggregate network cannot show this" is correct. The trap is only in turning the answer into a list of standout donors. Graders should not penalise the per-sample point here.
5. **F4 counts as "one" per individual with three time points.** That follows the brief. Some readers might still expect the reply to mention that three samples per patient cannot support a per-patient network.
6. **F6 leaves the per-volunteer sample count implicit** (60 days, every other day, so about 30 draws). About 30 samples for a gene × CpG partial-correlation network is modest. I labelled it "many" because DRAGON-style shrinkage is designed for this regime, but a cautious reply may warn about power, and that should not count as a red flag.
7. **F5b has only 8 women, roughly 4 per relapse group.** The group question is legitimate, but statistical power is very low. I put "the woman is the unit of replication" in must_include, rather than "too few to test", which a good reply might also say.
8. **GIRAFFE is in or out depending on wording** ("TF regulation" in, "TF-to-gene network/edges/targeting" out). This is a fine line. GIRAFFE also returns signed TF-gene effects, so a reviewer could reasonably accept it on F3b, F5a and T8.
9. **T5 accepts PANDA and OTTER.** I accepted them for "regulatory influence" (differential targeting between two group networks), alongside GIRAFFE for activity. A stricter reading of "activity" would accept only GIRAFFE and LIONESS-PANDA.
10. **T2 may be read as a cohort-level heterogeneity question** ("is there variation in response?") rather than an individual one. I labelled it `individual_change` because answering it needs per-pup estimates and naming the pups that change more.
11. **T3's "Across all 50 aneurysm mice"** could be read as "consistently in each mouse". I dropped "taken together" to keep the trap sharp, which makes this item the most ambiguous of the precision traps.
12. **COBRA is accepted for paired designs** (F1b, F1d, T4), with patient or fish identity in the design matrix. With 38 patients that adds many covariates; a reply that prefers per-sample networks plus a paired test is equally fine.
13. **BONOBO is accepted on moderate cohorts** (40-76 samples), although the brief says it suits small ones. I treated "suited to small" as a strength, not a requirement.
14. **T6 treats single laser-captured crypts as separate samples from one animal.** The point is the many-samples-per-individual reading. Technical concerns about very low-input libraries are out of scope.
15. **T7 is labelled `groups`.** The outcome defines two groups of calves, but the request is a prediction, so `none` would also be defensible.
16. **Avoid-list proximity.**
    - T7 was moved from piglets to calves to stay away from "piglet jejunum".
    - T2 (seal pups) and F6 (bed-rest blood) are close in spirit to "wild dolphin blood" and "Antarctic expedition"/isolation studies, but differ in species, condition and design.
    - T1 (Duchenne muscle) is a different disease from inclusion-body myositis.

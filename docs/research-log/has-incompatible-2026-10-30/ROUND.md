# The has-read rules a workflow out only through its explicit incompatible inputs (2026-10-30, user "開新一輪")

## Basis (data-has-2026-10-29, withdrawn at D4)

The second Jev question "Which kind of data does the user say they have?" caught j2 Q18 (expression_matrix 0.80;
10/10 stable at 0.73-0.81) with 0 false rule-outs on 158 gold-DO items, but the chain control j5 W17 (PANDA -> CONDOR
from expression) crossed 0.70 once in ten and was ruled out through the guard's broadest branch, "a single kind
outside the workflow's declared input_artifacts". Q18 is ruled out through SAMBAR's explicit
`incompatible_input_artifacts: expression_matrix`.

## Change

The has-read is applied only through the explicit field: a workflow is ruled out by it only when the read kind
(>= 0.7) is in that workflow's `incompatible_input_artifacts`. The guard's own data read keeps every branch it has
today. The confirm names the kind that ruled the workflow out (`ruled_by`), its contract line unchanged. Behind a flag
`NETZOO_JEV_DATA_HAS` (off by default). The guard still only asks its data confirm, never declines from a read.

## Gates (declared before computing anything; E1-E3 reuse data-has's recorded reads, no new call)

- **E1 precision (hard)**: on data-has's 158 gold DO / PARTIAL items, existing OR restricted-has rules out a gold
  workflow in 0 items.
- **E2 recall**: j2 Q18 ruled out (SAMBAR); data-type gold-DECLINE items caught >= 17 (the existing read's count).
- **E3 stability (hard)**: in data-has's 10x reads, Q18 is ruled out >= 8/10; W17 and Z14 (CONDOR, no incompatible
  list) 0/10 by construction, checked in code.
- **E4** build: unit tests (restricted rule, `ruled_by`, the confirm names the right kind, flag off = no extra call);
  flags-off replay byte-identical; clean-env tests no new failures. jev-guard session agrees to the edit first.
- **E5 live** (after the user agrees): Q18, S32, S42 and the chain controls W17, Z14 plus 3 gold-DO data items, app
  settings + the flag; hard: no control ends in a confirm-then-decline; Q18 ends DECLINE with the incompatible line.

Stop rule: a failed hard gate -> withdraw. No gate is changed after the run.

## E5 controls, declared before the live run

The 3 gold-DO data controls: the first three (by set, id) gold-DO items whose recorded has-read is one kind at >= 0.9
and whose gold workflow has a non-empty incompatible list (the ones the restricted rule could touch): j2 Q37 (SAMBAR,
mutations), j4 S08 (LIONESS-COEXPRESSION, expression), j5 W36 (SAMBAR, mutations). Run hi1: code bf2835c6, app
settings + NETZOO_JEV_DATA_HAS=on, up to 3 turns, 1 rep; targets j2 Q18, j4 S32, j4 S42; chain controls j5 W17,
j8 Z14. Cap US$0.15.

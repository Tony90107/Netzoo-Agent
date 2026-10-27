# Jev answer binding for form questions (2026-10-27) — declared before any run

User decision (2026-10-27): when a user answers a form question (group_membership, time_model, spatial,
input_network) in natural words, Jev reads the answer with the same closed menu and code binds the value. Duplicate
form questions are merged. Declare gates, measure offline, then ask the user. Branch `jev-answers` from main ce8be114,
worktree `.worktrees/netzoo-j4`.

## Problem (j4 RESULTS-J4.md, post hoc)

`bind_answers` binds a reply only when it contains an option's value or label words. Natural answers never bind, so
the next turn re-reads the request and can type the same misread again:
- j4g S05: the network question was asked three times. The answer "The sources are all transcription factors and the
  targets are the genes they're predicted to regulate" never bound.
- j4g S32: the same group question was listed twice (once per quote), and the run ended at the round cap.
- j3g R12, R18, R31, R34 and j4g S02, S39: natural "one group each" / "TF to gene" answers, all unbound. Some
  reached the right call anyway, through the re-read.

## Cases

- `cases.json`: every recorded turn (j4g, j3g, jo1, jf1, jfsmoke) whose call asked a form question, with the next
  turn's answer (the text after "User follow-up:"). There are 19 answers:
  - 8 natural answers that did not bind: S02 (network: regulator_gene), S05 t1 and t2 (regulator_gene), S39, R12,
    R18, R31, R34 (group: one_group).
  - 2 non-answers: S10 (a restatement) and S32 (a restatement). Neither states the form.
  - 9 option-label answers that bound in code: jo1 x6, jf1 x2, jfsmoke x1.
- `synthetic.json`: 14 answers I wrote before any run.
  - 8 state the ruling value: G1 G2 several_groups; T1 T2 dynamic; P1 P2 uses_neighbors; N1 gene_gene; N2 a
    protein-metabolite network (gene_gene or nothing).
  - 2 state the other value: T3 not_dynamic; P3 not_spatial.
  - 4 are non-answers: X1-X4, "I'm not sure yet; what would you recommend?".

## Change (flag `NETZOO_JEV_FORMS`; off = no read, nothing changes)

1. After `bind_answers`, each asked form question the reply left unbound is read by Jev: the attribute's frozen
   question and criteria (`jev_forms.QUESTIONS`; `jev_overlap` for group_membership), on the state in
   `answer_q.py` (the question asked and the user's answer). A value is bound when Jev's probability on the options
   meaning it is >= 0.7 and the value is one of the question's options. The binding is recorded like a code binding,
   with the answer quoted. Code binding goes first, and Jev never overrides it.
2. Merge: form questions on the same dimension in one call become one question. A bound form answer then settles
   every row waiting on that dimension (`answered_check`), whatever words each row quotes.

## Gates (offline; then ask the user)

- B0, off = no change: flags off, harness replay 0 of 1388 calls changed vs `replay-frozen.json`; the test suite (clean
  environment) has no new failures beyond the known env-dependent one.
- B1, recall: >= 6 of the 8 unbound natural answers bind the right value. T3 and P3 are reported.
- B2, precision (hard): 0 wrong bindings. That means no binding for S10, S32 and X1-X4. For G1, G2, T1, T2, P1, P2,
  N1 and N2, there is never a binding to the value the answer contradicts.
- B3, code first: the 9 option-label answers bind exactly as before, and Jev is not read for them.
- B4, merge: the rebuilt questions of j4g S32 t2, S39 t1 and j3g R18 t2 have one question per dimension. A unit test
  shows one bound answer settling two waiting rows that quote different words. The flags-on harness replay changes
  0 calls vs main's flags-on replay.

Stop rule: if B2 fails, the round is withdrawn as declared; the frozen state and mapping are not reworded.

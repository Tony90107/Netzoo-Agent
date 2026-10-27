# Jev answer binding — live check (2026-10-27)

User decision (2026-10-27): small live check on the conversations whose natural answers never bound. Code 49a84df1
(branch jev-answers), `run_live.py` (smoke jasmoke: S05; run ja1: 8 items), 1 rep, up to 3 turns, gpt-4o-mini, all
three Jev flags on. Answers are the items' own natural words. Spent US$0.051 + smoke US$0.009. Raw: `live/ja1/`,
`live/jasmoke/`, `score-ja1.json`, `live-ja1.log`. All items are seen; this is no generalization claim.

| item | before (j4g / j3g) | ja1 calls by turn | final |
|---|---|---|---|
| S05 | network question asked 3x, never bound, ended waiting | network question -> natural answer bound by Jev (regulator_gene) -> DO | right (smoke the same) |
| S02 | asked once, unbound; DO through the re-read | network question -> bound by Jev -> DO | right |
| R31, R34 | group question unbound | group question -> bound by Jev (one_group) -> DO | right |
| R18 | group question twice per turn, unbound | CLARIFY -> one group question -> bound by Jev -> DO | right |
| R12 | group question unbound | ASK jev_link -> DO (no form question this run) | right |
| S39 | two group questions, unbound | DO at turn 1 (no form question this run) | right |
| S32 | two group questions, unbound, round cap | CLARIFY -> one group question -> "Yes, it's TPM expression from RNA-seq." not bound (Jev: not_stated 0.99) -> round cap, no call | wrong (gold DECLINE) |

- Form questions asked in 6 of 8 conversations: 5 answers bound by Jev, 0 by code (no answer used an option's words),
  1 non-answer left unbound (S32, right not to bind).
- No form question was asked again in a later turn (S05 was asked 3 times before); no duplicate questions in a turn.
- Final right: 7 of 8.

## Left as it was

S32: the group question comes before the data-type refusal (SAMBAR takes no expression matrix). After a non-answer
the round cap ends the conversation with no call. Binding is not the problem here: the problem is the order. The form
question should not be asked while a data check would refuse the request anyway (the j4 post-hoc finding).

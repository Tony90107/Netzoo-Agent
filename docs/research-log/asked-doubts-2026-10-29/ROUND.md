# A doubt any question already asked is never revived; feature-sized layer counts are feature counts (2026-10-29)

User: "撤回並開新輪" after layer-count-features (withdrawn, L4a not passed).

## Trace (lc1, j6 X22)

t1: the feature-sized `omics_layers` doubt read as a feature count -> ASK/count_fact "150 or 400?" (right). t2: "400"
bound, the row not available with the verified limit (31,960,000 values) -> DECLINE (right) -- then `agreed_fact_core`
revived a fact-agent proposal on the same sentence ("Did the core use the 400-metabolite panel?"), because
`agent_doubts` (jev-agent-once) only holds `source: agent` questions and this doubt was asked by a `count` question.
t3: DO (wrong).

## Change (two parts, one round)

1. Carried unchanged from layer-count-features (a5884601): an `omics_layers` choices doubt whose smallest candidate is
   >= 10 is a `feature_count` candidate fact judged in code.
2. `jev_guard_call`: the sentences `agreed_fact_core` never revives are the user words of every question the task
   asked or the user answered, whatever its source (agent, count, dimension, goal); renamed `asked_doubts`.

## Gates (declared before the code)

- **D1** unit tests: a pending or answered count / dimension / agent question on the sentence -> `already_asked`;
  none -> unchanged; the layer-count tests of layer-count-features pass.
- **D2** recorded lc1 X22 t2 rebuilt -> `already_asked` (stays DECLINE); recorded j6 X02 t2 still `already_asked`;
  ra2 W40 / J46 t1 still `ask`.
- **D3** flags-off harness replay: 0 right -> wrong; clean-env tests no new failures.
- **D4 live** (after the user agrees): X22 up to 3 turns -> final DECLINE; X02 up to 3 turns -> final DO; W40 t1
  shows the somatic question. About US$0.06, cap US$0.10.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

## Amendment (before any live run; jev-guard's review)

A CLARIFY's pending item (source `goal`) carries the goal quote, often most of the request; with `_overlaps` matching
substrings both ways it could block a genuine later revival of a sentence inside it (DO instead of ASK, the less
cautious direction). `asked_doubts` leaves out source `goal`. Added to D1: a goal quote holding the doubt sentence
does not block it. D1-D3 are rerun on the amended code before D4.

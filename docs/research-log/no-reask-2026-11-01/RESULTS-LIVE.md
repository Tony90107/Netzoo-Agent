# no-reask live (2026-11-01): M1 pass as declared (fact-agent path), M2 pass

Code 758595d0 (+ runner), the app `.env` plus NETZOO_ANSWER_BUTTONS, NETZOO_COUNT_ANSWERS and NETZOO_NO_REASK on;
P3 and P4 x 4 (2 below, 2 meets), clicks as count-answers. US$0.071 (cap US$0.08). Score `LIVE.md`.

| gate | result |
|---|---|
| M1 (hard) no fact-agent re-ask of an answered doubt | **pass**: 0. The rule fired 5 times (P3 r1, r2; P4 r1, r2, r3) and each blocked a fact-agent question on a doubt just answered. |
| M2 (hard) no run worse than count-answers' same prompt and click | **pass**: 0 |

**Disclosed: my scorer checked more than the gate.** `score_live.py` flags any question on an answered doubt, whatever
asked it, and reports P4 r3 as FAIL: after "Yes" to "Will you have at least three matched samples?", the fact agent's
repeat was blocked (`core.no_reask`), and the turn then asked the check's own **count question** "Which of these is
right: 2 or 5?" (basis `count_fact`). ROUND.md's M1 is the fact-agent path, and the count question was named there as
outside this round (the recorded "count question 1"). By the gate as written, M1 passes; the scorer's FAIL line stays
in `LIVE.md` as it was generated.

## Against count-answers (same prompts, before this change)

- P3 r2: count-answers asked "at least three tumour samples?" after the count was answered 2; now not asked, refused
  directly (count rule, "LIONESS-COEXPRESSION needs at least 3 samples; the request has 2").
- P4 r2: count-answers asked "2 or 5?" after "No"; now "No" ends in the count-answers refusal at once.
- P4 r1: count-answers ended CLARIFY after "2"; this run got the yes/no form, "No" -> refused (`count_answer`). Not
  attributable: a different first question.
- P4 r4 (meets): "Yes" -> CLARIFY "goal unclear" (the rule did not fire); count-answers' meets run ended DO. Not
  counted as worse by M2 (not refused for the count), but a weaker end; P4's CLARIFY after an answer was seen before
  (count-answers P4 r1).

## Left for later

- The check's count question re-asking a doubt a yes/no answer settled (P4 r3; the recorded count case).
- Jev's re-asks (9 recorded): the jev-guard session's module.
- P4's CLARIFY after an answered count doubt.

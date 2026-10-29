# agent-answer-anchor -- offline results (2026-10-29): G0-G4 PASS

`measure.py` -> `MEASURE.txt`, `measure.json`: the 45 DO answer turns of `population.json` through the anchor, the
guard's `judge_answer` (real Jev; R01's cache reused for identical inputs, the rest read once) and `answered_core`.

| Gate | Result |
|---|---|
| G0 flag off | flags-off replay byte-identical to main's (1388 readings, right 609); clean-env tests 5174 passed, only the 2 known unrelated failures; unit tests `tests/test_agent_answer_anchor.py` 3/3. |
| G1 precision (hard) | **0 of 35** gold-DO answer turns became DECLINE (22 of them anchored and read by Jev). |
| G2 recall | **6 of 6** anchored `fails` turns became DECLINE: j1 J09, j3 R01 x2, j5 W16, j7 Y14 x2. |
| G3 shape | all 6 are DO -> DECLINE `jev_answer`, each line quoting the reply and the anchored contract clause verbatim. |
| G4 anchor | j4 S15 (both, the `lambda1` line that sank R01) not anchored; every count-rule line ("Require at least ... samples", genes-vs-samples) not anchored. |

Not reached, by design: j5 W26 (its quoted line is a count rule; the real reason is a count) and j7 Y22 (its answer
turn was CLARIFY, not DO).

Close call, reported: p5 M03-D ("Transcription factors only." vs LIONESS-PUMA's input line) read `fails` 0.69, just
under the 0.7 threshold -- the jev-guard session has seen `judge_answer` confidence vary between runs on one input, so
this row is the precision risk to watch live. X22 (gold DECLINE by a count rule) read `meets` and stays DO here; the
count path decides it.

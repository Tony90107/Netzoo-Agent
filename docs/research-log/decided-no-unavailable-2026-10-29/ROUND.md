# A decided call is never shown as "Semantic routing unavailable" (2026-10-29, user: "修這個")

## Trace

ac1 j6 X22 turn 2: the core call is DECLINE/full_gap with the code-verified limit ("800 features and 100 samples give
31,960,000"), yet the reply also shows "! Semantic routing unavailable" and ends "Retry this request when semantic
routing is available ... No workflow is ready to start." `guidance_interaction` returns its `routing_unavailable`
interaction whenever the decision is a fallback with no matched or recommended action -- true for a decided refusal
too. jev-guard's review: it tells the user to retry something already decided.

Recorded replies with the notice: 104 -- 44 on a core DECLINE (the contradiction), 60 on UNCHECKED (the reading really
could not be validated; the notice is right there).

## Change

`guidance_interaction` returns no `routing_unavailable` interaction when the decision's core call is DO or DECLINE (a
decided call); the reply is the decided call's own. UNCHECKED and every other branch are unchanged.

## Gates (declared before the code)

- **U1** unit tests: a fallback decision with a DECLINE core -> no interaction; the same with an UNCHECKED core -> the
  `routing_unavailable` interaction as before; the other branches unchanged.
- **U2** recorded ac1 X22 t2 decision re-rendered offline (`replay_sessions` style, no model call): the reply keeps
  the DECLINE line with both numbers and has no "Semantic routing unavailable" / "Retry this request".
- **U3** clean-env tests no new failures; flags-off replay 0 of 1388.
- No live run (rendering only).

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

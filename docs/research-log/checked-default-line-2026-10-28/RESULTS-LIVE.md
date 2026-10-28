# Checked default line -- live (2026-10-28, user "跑 live"): E1 PASS -> KEPT

Run cd1: code 94f9c378 (with granularity-unknown), app settings, gpt-4o-mini, turn 1, 1 rep. Spent **US$0.015**
(cap 0.05). Raw: `live/cd1/`.

| item | call | default line | `routing.default_line_checked` |
|---|---|---|---|
| C04 ("For each of our 25 ... patients ... that patient's own network") | DO LIONESS-PANDA | **"If none of these applies: LIONESS-PANDA."** (recorded before: "PANDA, LIONESS-PANDA") | fired |
| j5 W01 ("... rather than any per-sample networks") | DO PANDA, PUMA, OTTER, GIRAFFE | none: this run's reply had no method-tie question | not reached |

- **E1 pass**: W01's reply names no LIONESS-PANDA in a default line; C04 keeps LIONESS-PANDA and names no PANDA.

Post hoc, not gated:
- W01 this time ended with "Should the result be aggregate or sample-specific?" (the unstated-scale question). With
  its granularity left `unknown` (granularity-unknown-2026-10-28) the turn treats the scale as unstated, although the
  request says "built from all tumour samples together ... rather than any per-sample networks". A needless question,
  not a wrong claim; it comes from the code witness missing "rather than" and the aggregate phrasing, not from this
  round. gu1's W01 run took the tie-question path instead (reading variance).
- C04's question offers OTTER and GIRAFFE (aggregate methods) to a per-sample request; options were out of scope here.

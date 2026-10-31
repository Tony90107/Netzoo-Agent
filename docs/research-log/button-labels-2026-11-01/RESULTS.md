# button-labels results (2026-11-01): G1, G2 pass

- G1: the real-card check (`answer-buttons-2026-10-31/offline2.py`, run on this code; output copied here as
  `G1-C1.md`, `g1-c1.json`): 225 recorded ASKs, 210 rendered with buttons, 0 failures; no button label is a bare
  number (count buttons now read e.g. "25 samples" / "30 samples"; the click still sends "25" / "30").
- G2: `tests/test_answer_buttons.py` 7 tests (one new: "2 samples" / "5 samples" bind 2 / 5); flags-off replay
  byte-identical to `sa-off.json`; clean-env suite 5202 passed, 1 failed = the known `explicit_panda`.

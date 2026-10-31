# Number buttons say what the number counts (2026-11-01, user: "Yes, fix the labels")

## Why

The user's app test: on "Which of these is right: 2 or 5?" the card listed the buttons as 1 "2", 2 "5", 3 "Type your
own answer", with keys 1-3 to choose. The user meant two biopsies and chose item 2 -- the button "5"; all three of
their biopsy sessions (0d1c326d, bd7f7bca, d1c6d325) sent "5". The system was right for 5; the card's numbering and
the option's own number collided.

## Change (code only after this file is committed)

Branch `button-labels` from main a9836c05. Under the same flag `NETZOO_ANSWER_BUTTONS` (on in the user's app):
`engine/answer_buttons.buttons` labels an option whose words are only a number with what it counts --
`sample_count` -> "2 samples", `feature_count` -> "350 features", `omics_layers` -> "2 layers", any other -> "Value 2".
What a click sends (`answer`) stays the bare number, so binding is unchanged.

## Gates (offline; no model call)

- **G1 (hard)**: the round-1/2 real-card check (`answer-buttons-2026-10-31/offline2.py`) on this code: every rendered
  button still binds exactly its option (0 failures, the same 210 turns), and no button label is a bare number.
- **G2 (hard, build)**: unit tests updated; flags-off replay byte-identical to `sa-off.json`; clean-env suite no new
  failures.
- No live round: the change is a label; the user checks it in the app.

Pass -> fast-forward to `netzoo-agent/main` and the app folder (the user asked for the fix in the app).

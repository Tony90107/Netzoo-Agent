# Phase 1 bench freeze (2026-10-18)

Written before the one bench measurement (spec section 6: the 56 items are read once, never used to tune).

- Code: this commit's parent tree -- reader shape **v7** (`READER_SHAPE`), the focused re-read (`menu_focus`,
  `MAX_FOCUS` 6, skipped while the result is open), `decide_menu` as of the v6 commit (an unsure control waits before
  combination checks; phase 0 gate still 56/56).
- Model: `openai/gpt-4o-mini` through OpenRouter, temperature 0, 8,000 output tokens, strict function calling.
- Run: `bench.py read p1` -- 56 items x 2 reads, each followed by its focused re-read; then `bench.py score p1`.
- Scorer checked offline before the run: gold readings fed as reads give 550/550 fields, 154/154 limits, 32/32 doubts,
  56/56 calls.
- Gates the task set (spec section 6, phase 1): kind agreement >= 90%; vague declined <= 1; dont declined right no
  fewer than today (p5r 10/13; p4b, p4c 11/13). Field accuracy and limit/doubt recall are reported, not gated.
- Dev rounds behind this shape: d1-d7 on 85 dev items (heldout11-19, accept24, m3; `dev_items.json`).

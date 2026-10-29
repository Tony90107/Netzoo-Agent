# Jev-first linking, phase A: a shadow measurement, no change to the system (2026-10-29, user "我們試著讓jev先跑跑看")

## Why

The remaining errors are mostly in the reading, and most of those are linking: which registered result a sentence
asks for (X10/W20 linked to LIONESS, h5's errors mostly registry linking). gpt-4o did not beat mini (41/56 x2), and
the same items stay wrong read after read (h5: 41/46 agree, 8 stably wrong). Jev is a closed-menu classifier with
probabilities; linking is a closed-menu choice. Phase A asks one question only: on the same recorded asks, does Jev
link better than the reading did? Nothing in the app changes.

## What earlier rounds already showed (not repeated)

- LINKS step 2 (withdrawn): on DECLINE calls Jev picked a workflow for 40/66 correct refusals -- it picks what the
  request is ABOUT, not whether it can run. So here Jev only links; code still judges every condition, as today.
- LINKS step 4 / jev-menu (kept): workflow-level pick on CLARIFY calls only; the menu now lists produced artifacts.
- jev-permissive (withdrawn): a Jev read can be wrong with high confidence (PPI prior -> other 0.82): calibration is
  measured here, not assumed.

## Design

- Population: every recorded first-turn reading (t1, `routing.capability_checked` with a proposal) of a session whose
  item has a gold call and gold workflows: j1-j6 (`items.json`: `expected_call`, `workflows`, `also_acceptable`), plus
  h7/h8 if recorded. All seen sets -- this is a feasibility measurement, not an adoption test.
- Asks: mini's own sentence roles and ask quotes are kept (phase A isolates linking). For each ask, Jev reads the
  request and the ask's quote and picks ONE entry from a closed menu: the capability sheet's 31 produces entries
  ("WORKFLOW: result text") plus "none of these gives it". Question text frozen in `jev_link_menu.py` before any run.
- Arms, each rebuilt with this checkout's pure-code `build_capability_check` (no model calls; condition-check and
  second-opinion answers are not replayed, the same for every arm):
  - **M** mini's recorded `delivered_by`;
  - **J** Jev's pick (none -> []);
  - **H** Jev's pick when its confidence >= 0.7, else mini's.
- Score per reading, from the rebuilt check: the workflows of the available/with_step/partial rows ("credited").
  - gold DO: right when credited is non-empty and within gold `workflows` + `also_acceptable`;
  - gold DECLINE: "check-level false accept" when anything is credited;
  - gold ASK/CLARIFY: reported only.

## Gates (declared before any Jev call)

- **A1** (worth building): on gold-DO readings, J or H right >= M right + 5, AND for that arm the paired
  wrong->right >= 2 x right->wrong.
- **A2** (safety): on gold-DECLINE readings, the same arm's check-level false accepts <= M's + 2.
- **A3** (calibration): Jev's picks with confidence >= 0.7 on gold-DO readings are right >= 90%.
- Cost cap US$0.30 (Jev ~US$0.00003 a call; reads cached in this folder, so nothing is read twice).

All three pass -> propose phase B (Jev-first typed fields, then a live/fresh test). Any fails -> report what failed and
stop; nothing to withdraw since nothing changes in the system. No gate is changed after the run.

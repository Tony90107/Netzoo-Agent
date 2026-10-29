# Jev-first typed fields, phase B: a shadow measurement, no change to the system (2026-10-29, user "開始 B 階段")

## Why (phase A, `jev-first-links-2026-10-29`)

Arm H (Jev's link when confidence >= 0.7, else mini's) raised gold-DO check-level right 101 -> 120 of 168. Of H's 48
remaining wrong, 39 have Jev linking a gold workflow that code then rules out through mini's typed fields.
`diag.py` (there) neutralised one field at a time on those 39: group_membership 20 (all `several_groups`),
input_network 6 (all `gene_gene`), needs_sign 3 and needs_sign+scale 3, scale 3, regulator_kinds 2 (`other`), counts
2, still nothing 4.

## Design

- Same population, asks, rebuild and scoring as phase A (433 readings of j1-j6; check level only; seen sets).
- One Jev call per ask (the same 367 distinct request+quote pairs), five closed questions at once, frozen in
  `jev_field_questions.py` before any run:
  - group_membership: the live overlap question (`jev_overlap.INSTRUCTIONS/CRITERIA`, frozen 10-27), applied only
    where mini typed a grouping value (one_group / several_groups / not_stated) -- the question presumes groups;
  - input_network: the live forms question (`jev_forms.QUESTIONS["input_network"]`);
  - scale, needs_sign, regulator_kinds: new questions (per_sample / per_group / whole_cohort / not_stated;
    signed / not_signed / not_stated; tf / tf_and_mirna / other_regulators / not_about_regulators / not_stated).
  - A field takes Jev's value only at confidence >= 0.7; else mini's stays. not_stated maps to the schema's own
    not-stated value (scale unstated, needs_sign false, regulator_kinds []).
- Arms: **H** (phase A) and **HB** = H + all five Jev fields; plus five ablations H + one field each (attribution).

## Gates (declared before any Jev call)

- **B1** (worth building): HB gold-DO right >= H's (120) + 5, AND vs H wrong->right >= 2 x right->wrong.
- **B2** (safety): HB gold-DECLINE check-level false accepts <= H's (42) + 2.
- **B3** (per field): a field whose one-field ablation adds >= 3 right->wrong or >= 3 false accepts over H is
  named "harmful" and excluded from any phase C proposal (B1/B2 are judged on all five as declared).
- Cost cap US$0.30; reads cached in this folder.

All pass -> propose phase C: build Jev-first link + fields behind a flag and test live on a fresh set. Otherwise
report and stop. No gate is changed after the run.

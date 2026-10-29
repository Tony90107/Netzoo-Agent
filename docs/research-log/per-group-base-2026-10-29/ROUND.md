# A result per group is credited to the base method's network, not its per-sample extension (2026-10-29, user "還是先修 X10、W20")

## Trace (live pg1, code d2025245)

X10 ("one TF-to-gene regulatory network per tissue, each built from all 30 samples of that tissue, not a network per
animal"; gold PANDA/OTTER) and W20 ("one two-layer partial-correlation network per time point, each using all 15
samples from that visit"; gold DRAGON) are now read `scale: per_group`, but the reading links `delivered_by` only to
`lioness_panda.per_sample_networks` / `lioness_dragon.per_sample_networks`. Those entries carry
`{aggregate, sample_specific}` (they also write the aggregate network), so `_fitting` keeps them and the call is
DO LIONESS-PANDA / LIONESS-DRAGON -- the same as j6a/j5a before per_group existed.

## Earlier round this must respect

aggregate-base-2026-10-28 (withdrawn): dropping the extension for `whole_cohort` contradicted Log 397 ("LIONESS-DRAGON
writes the aggregate network too, so a cohort-level ask fits both") and moved J29 CLARIFY -> DO. This round leaves
`whole_cohort` exactly as it is; it acts only on `per_group`, which no recorded reading carries.

## Change (contract shape: the sheet + the typed scale -> entry mapping in code)

- The capability sheet gains `aggregate_entry` on the three LIONESS network entries: the base entry whose result is
  the aggregate network the LIONESS run writes (lioness_panda.per_sample_networks -> panda.tf_gene_network,
  lioness_puma.per_sample_networks -> puma.regulator_gene_network, lioness_dragon.per_sample_networks ->
  dragon.two_layer_network). Validated at load: it names a produces entry with granularity aggregate only.
- `_fitting`, for `scale: per_group` only: an entry with an `aggregate_entry` is replaced by that entry (one result
  per group is the base method run once per group; the per-sample networks were not asked). Every other scale and
  every entry without the field are unchanged.

## Gates (declared before the code)

- **Q1** unit tests: per_group on each of the three LIONESS network entries -> its base entry; per_sample and
  whole_cohort unchanged (Log 397 test still passes); an entry without `aggregate_entry` (association tests) kept;
  the sheet validation rejects a bad `aggregate_entry`.
- **Q2** rebuild of the recorded pg1 X10 and W20 t1 readings: credited panda.tf_gene_network and
  dragon.two_layer_network, available, no full gap.
- **Q3** flags-off harness replay: 0 changed calls (no recorded reading says per_group); clean-env tests: no new
  failures (module size included).
- **Q4 live** (after the user agrees), turn 1, 1 rep: targets X10 (gold PANDA/OTTER), W20 (DRAGON); kept X30, W30
  (OTTER); controls X14, W13, W35 and j4 S16 (per-sample BONOBO networks "so I can compare network features between
  the days" -- groups named, per-sample result; jev-guard's request). Hard: no control and neither kept item changes
  workflow or kind. About US$0.03.

Checked before the round (jev-guard note): the pg1 X30 DO reply quotes "one TF-to-gene network per stage" and never
says one network for all samples.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

# per-group-scale -- live P4 (2026-10-29, user "跑 live"): PASS

Code d2025245, app settings, gpt-4o-mini, turn 1, 1 rep. Run pg1 (`run_live.py`) started 5 items; its reserve guard
(US$0.012 held for each running turn against the US$0.05 cap) stopped before X14 and W30, which run pg2
(`run_live_pg2.py`) started alone. Nothing was rerun. Spent US$0.025 + US$0.007 = US$0.032.

| item | role | gold | scale read (before: j5a/j6a) | credited | call |
|---|---|---|---|---|---|
| X30 | target | DO OTTER | **per_group** (per_sample) | otter.tf_gene_network | **DO OTTER** (was DECLINE full gap) |
| W30 | target | DO OTTER | per_group | otter.tf_gene_network | DO OTTER |
| X10 | target | DO PANDA/OTTER | per_group (per_sample) | lioness_panda.per_sample_networks | DO LIONESS-PANDA (same as j6a) |
| W20 | target | DO DRAGON | per_group (per_sample) | lioness_dragon.per_sample_networks | DO LIONESS-DRAGON (same as j5a) |
| X14 | control | DO LIONESS-PUMA | per_sample | lioness_puma.per_sample_networks | DO LIONESS-PUMA |
| W13 | control | DO LIONESS-PUMA | per_sample | lioness_puma.per_sample_networks | DO LIONESS-PUMA |
| W35 | control | DO BONOBO | per_sample | bonobo.per_sample_networks | DO BONOBO |

- **Hard gate pass:** no control was typed per_group or credited only aggregate workflows (3/3 per_sample, right
  workflow).
- **Targets:** per_group read 4/4 (before: X10, W20, X30 all per_sample). X30 is fixed (DECLINE -> DO OTTER).
- **Not fixed, unchanged from before:** X10 and W20 still name the LIONESS entry. The reading itself links
  `delivered_by` to the LIONESS entry, not PANDA/DRAGON, and the LIONESS entries also carry `aggregate` (they write
  the cohort network too), so per_group keeps them. The kind (DO) is right, the workflow is the per-sample one. This is
  a linking miss of the reading, the same in j5a/j6a, not caused by this change.

# per-group-base -- live Q4 (2026-10-29, user "跑 live"): PASS, 8/8

Run pb1 (`run_live.py`): code 1d88cd64, app settings, gpt-4o-mini, turn 1, 1 rep, all 8 started. Spent US$0.036
(cap raised to US$0.08 so the per-turn reserve would not stop items early, as in pg1; not a gate).

| item | role | gold | scale | credited | call | before (pg1/pg2) |
|---|---|---|---|---|---|---|
| X10 | target | PANDA/OTTER | per_group | panda.tf_gene_network | **DO PANDA** | DO LIONESS-PANDA |
| W20 | target | DRAGON | per_group | dragon.two_layer_network | **DO DRAGON** | DO LIONESS-DRAGON |
| X30 | kept | OTTER | per_group | otter.tf_gene_network | DO OTTER | DO OTTER |
| W30 | kept | OTTER | per_group | otter.tf_gene_network | DO OTTER | DO OTTER |
| X14 | control | LIONESS-PUMA | per_sample | lioness_puma.per_sample_networks | DO LIONESS-PUMA | same |
| W13 | control | LIONESS-PUMA | per_sample | lioness_puma.per_sample_networks | DO LIONESS-PUMA | same |
| W35 | control | BONOBO | per_sample | bonobo.per_sample_networks | DO BONOBO | same |
| S16 | grouped per-sample control (jev-guard) | BONOBO | per_sample | bonobo.per_sample_networks | DO BONOBO | (new) |

- **Hard gate pass:** no control and neither kept item changed kind or workflow; S16 (days named, per-sample result)
  stayed per_sample.
- **Targets fixed:** X10 -> PANDA, W20 -> DRAGON; the reply quotes the per-tissue / per-visit sentence and names the
  base workflow.
- Per-group counts (jev-guard's open item): every per_group row was checked on the per-group number (X10 30, W20 15,
  X30 12, W30 20). The total-only case stays open (RESULTS.md).

# SPONGE integration

SPONGE (kuijjerlab/sponge, `netzoopy-sponge`) builds a human TF motif prior and a TF PPI prior: it selects TF motifs
from JASPAR (with NCBI homologs for non-human vertebrate motifs), keeps their binding sites inside Ensembl promoter
windows, aggregates transcripts to genes, and asks STRING for the physical interactions between the selected TFs.
The two files are the motif and PPI priors PANDA, PUMA, LIONESS-PANDA/PUMA, OTTER, GIRAFFE and SCORPION read.

The image installs `netzoopy-sponge==2.2.2` into an environment of its own, `netzoo-sponge` (Python 3.12 with pybbi,
bioframe and pyjaspar), so the agent's packages never move. A run needs internet access to JASPAR, Ensembl, NCBI,
UniProt and STRING.

## Where it sits

SPONGE is a preparation step (`build_priors`), like normalization and the STRING download: it produces inputs, not
a result, so it is never a menu workflow and its result is not checked against the capability sheet.

```
(nothing) ──SPONGE──▶ motif_prior.tsv + ppi_prior.tsv ──▶ PANDA / LIONESS-PANDA / OTTER / GIRAFFE / SCORPION ...
```

## When it is used (`netzoo_agent_core/prior_request.py`)

Read from the request's own words before workflow matching, with no model call:

- SPONGE named, or building/generating a motif, PPI or prior network named ("Build the motif and PPI priors for
  SOX2 and MYC", "幫我用 SPONGE 建立 motif 先驗"), as a command, not a question or a negation;
- "..., then run PANDA on expr.tsv": the one workflow named after a sequence word is recorded as `then_action` when it
  reads a motif prior. After the priors are built the follow-up offers it with `motif_file` and `ppi_file` set to
  the two new files (`cli/follow_up.py`), and with the inputs the first request named.
- A workflow named without "then" ("Run PANDA with my motif prior") is left to routing; "PANDA priors" names the
  priors' consumer, not a run.

When the user says they have no motif prior, a workflow that needs one stays unavailable as asked, and the reason now
says "SPONGE (registered) can build a human motif prior and PPI network first -- ask to build the priors with SPONGE"
instead of "no registered workflow or tool provides it" (`interpretation/ruled_out.py`).

## Settings (each from explicit words only; none is guessed)

| Setting | Default | Read from |
| --- | --- | --- |
| `sponge_tf_names` | every vertebrate JASPAR CORE motif | "for the TFs SOX2, MYC and FOXF2", `tf_names=SOX2,MYC` |
| `jaspar_release` | the newest (JASPAR2026) | "JASPAR 2024" |
| `genome_assembly` | hg38 | hg38/GRCh38, hg19/GRCh37, T2T/CHM13/hs1 |
| `promoter_upstream`, `promoter_downstream` | 750, 250 bp | "-1000/+500 bp", "+/-1 kb", "1000 bp upstream" |
| `motif_score_threshold`, `ppi_score_threshold` | 400, 400 | SPONGE's 0-1000 scales |
| `n_cores` | 1 | SPONGE's filtering processes |

Binding sites are always downloaded one TF at a time (`on_the_fly_processing`), never the >100 GB genome-wide
bigBed. Each selected TF's genome-wide track is downloaded once per run (FOXF2's was 77 MB), so the plan says what the
run downloads: with a TF list, one track per TF; without one, one per motif for the 1,019 vertebrate JASPAR2026 CORE
motifs, which takes hours. The run waits for `/execute` (`build_priors` is a deferred operation, like a transform).
A request naming another organism is refused before anything runs: SPONGE builds human priors only.

## Outputs (`scripts/run_sponge.py`)

| File | Orientation |
| --- | --- |
| `motif_prior.tsv` | no header; TF symbol, target gene symbol, 1 |
| `ppi_prior.tsv` | no header; TF, TF, STRING combined score / 1000 (physical) |
| `sponge_provenance/` | SPONGE's `fingerprint.yaml` (JASPAR, Ensembl, NCBI and STRING versions) and `last_user_config.yaml` |
| `manifest.json` | Parameters and counts, including requested TFs that got no motif edge |

The default output folder is `<project output>/sponge_priors`.

## Verified (2026-11-08)

- SOX2, FOXF2 and MYC on chr19 promoters: 1,634 TF-gene edges and 4 PPI rows in 1 min 46 s.
- SOX2 and MYC (plus a made-up NOTATF) on all promoters: 21,855 motif edges over 20,041 genes, 3 PPI rows; NOTATF is
  listed under `requested_tfs_without_motif_edges`.
- Unit and routing tests: `tests/test_sponge_priors.py`.

#!/usr/bin/env python3
"""Build a human TF motif prior and a TF PPI prior with SPONGE (kuijjerlab/sponge) and publish typed artifacts.

Runs in the image's own `netzoo-sponge` environment (SPONGE's pybbi/bioframe/pyjaspar stack is kept apart from the
agent's environment). Needs internet access: SPONGE reads JASPAR, Ensembl, NCBI, UniProt and STRING while it runs.

Binding sites are downloaded one transcription factor at a time (SPONGE `on_the_fly_processing`), never the
>100 GB genome-wide JASPAR bigBed file. Each selected TF's genome-wide track is downloaded once per run, so a TF list
keeps a run short; without one SPONGE selects every vertebrate JASPAR CORE motif.

Outputs (written to output_dir):
  motif_prior.tsv     TF, target gene, 1 (no header) -- the three-column motif prior PANDA, OTTER and SCORPION read
  ppi_prior.tsv       TF, TF, STRING combined score / 1000 (no header) -- the three-column PPI prior
  sponge_provenance/  SPONGE's own fingerprint.yaml (database versions) and last_user_config.yaml
  manifest.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

MOTIF, PPI = "motif_prior.tsv", "ppi_prior.tsv"
ASSEMBLIES = ("hg38", "hg19", "hs1")
DEFAULTS = {
    "genome_assembly": "hg38", "promoter_upstream": 750, "promoter_downstream": 250,
    "motif_score_threshold": 400, "ppi_score_threshold": 400, "n_processes": 1,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build motif and PPI priors with SPONGE (human).")
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--tf-names", default="", help="comma-separated TF symbols; empty selects every vertebrate TF")
    parser.add_argument("--jaspar-release", default="", help="e.g. JASPAR2024; empty takes the newest")
    parser.add_argument("--genome-assembly", default=DEFAULTS["genome_assembly"], choices=ASSEMBLIES)
    parser.add_argument("--promoter-upstream", type=int, default=DEFAULTS["promoter_upstream"])
    parser.add_argument("--promoter-downstream", type=int, default=DEFAULTS["promoter_downstream"])
    parser.add_argument("--motif-score-threshold", type=int, default=DEFAULTS["motif_score_threshold"])
    parser.add_argument("--ppi-score-threshold", type=int, default=DEFAULTS["ppi_score_threshold"])
    parser.add_argument("--n-processes", type=int, default=DEFAULTS["n_processes"])
    return parser


def _errors(args) -> list[str]:
    errors = []
    if args.promoter_upstream < 0 or args.promoter_downstream < 0:
        errors.append("promoter_upstream and promoter_downstream are distances in bp and must be non-negative")
    if args.promoter_upstream + args.promoter_downstream == 0:
        errors.append("the promoter window is empty")
    if not 0 <= args.motif_score_threshold <= 1000 or not 0 <= args.ppi_score_threshold <= 1000:
        errors.append("score thresholds are on SPONGE's 0-1000 scale")
    if args.n_processes < 1:
        errors.append("n_processes must be at least 1")
    if args.jaspar_release and not (args.jaspar_release.startswith("JASPAR") and args.jaspar_release[6:].isdigit()):
        errors.append("jaspar_release looks like JASPAR2024")
    return errors


def _skip_empty_tracks() -> list[str]:
    """Let a TF whose binding-site track has no site at the score threshold give no edges instead of ending the run.

    SPONGE 2.2.2 `process_motif` concatenates one table per chromosome; a track with no site at or above the
    threshold has no chromosome, and `pd.concat([])` raised "No objects to concatenate", so MYC, MAX and SOX2 all
    failed because of MAX (MA0058.4, 2026-11-10). The TF is listed in the manifest with the reason instead.
    """
    import pandas as pd
    from sponge.modules.utils import tfbs_filtering

    original, skipped = tfbs_filtering.process_motif, []

    def process_motif(motif_df, bed_df, n_processes=1):
        if motif_df.empty:
            skipped.append("track had no binding site at or above motif_score_threshold")
            print("No binding site at or above the score threshold in this TF's track; it gets no motif edges.")
            return pd.DataFrame({"score": pd.Series(dtype=float), "transcript": pd.Series(dtype=object)})
        return original(motif_df, bed_df, n_processes)

    tfbs_filtering.process_motif = process_motif
    return skipped


def _table(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8") as handle:
        return [line.rstrip("\n").split("\t") for line in handle if line.strip()]


def main() -> int:
    args = _parser().parse_args()
    tf_names = [name.strip() for name in args.tf_names.split(",") if name.strip()]
    if errors := _errors(args):
        raise SystemExit("SPONGE input validation failed:\n  " + "\n  ".join(errors))
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    from sponge.sponge import Sponge  # imported late so --help works without the package

    without_sites = _skip_empty_tracks()

    config = {
        "default_workflow": True,
        "on_the_fly_processing": True,
        "genome_assembly": args.genome_assembly,
        "motif": {"tf_names": tf_names or None, "jaspar_release": args.jaspar_release or None},
        "region": {"tss_offset": [-args.promoter_upstream, args.promoter_downstream]},
        "filter": {"n_processes": args.n_processes, "score_threshold": args.motif_score_threshold},
        "ppi": {"score_threshold": args.ppi_score_threshold},
    }
    with tempfile.TemporaryDirectory(prefix="sponge-", dir=output_dir) as temporary:
        staging = Path(temporary)
        cache = staging / "sponge_temp"
        config["motif_output"] = {"file_name": str(staging / MOTIF)}
        config["ppi_output"] = {"file_name": str(staging / PPI)}
        cwd = os.getcwd()
        os.chdir(staging)
        try:
            Sponge(temp_folder=str(cache) + "/", config=config)
        finally:
            os.chdir(cwd)
        missing = [name for name in (MOTIF, PPI) if not (staging / name).is_file()]
        if missing:
            raise SystemExit("SPONGE did not create: " + ", ".join(missing))
        motif, ppi = _table(staging / MOTIF), _table(staging / PPI)
        if not motif or any(len(row) != 3 for row in motif):
            raise SystemExit("SPONGE motif prior is empty or not three columns")
        if any(len(row) != 3 for row in ppi):
            raise SystemExit("SPONGE PPI prior is not three columns")
        provenance = output_dir / "sponge_provenance"
        provenance.mkdir(exist_ok=True)
        for name in ("fingerprint.yaml", "last_user_config.yaml"):
            if (cache / name).is_file():
                shutil.copy2(cache / name, provenance / name)
        for name in (MOTIF, PPI):
            shutil.move(str(staging / name), output_dir / name)

    motif_tfs = sorted({row[0] for row in motif})
    manifest = {
        "method": "SPONGE",
        "package": {"name": "netzoopy-sponge", "repository": "kuijjerlab/sponge", "version": version("netzoopy-sponge")},
        "parameters": {
            "tf_names": tf_names, "jaspar_release": args.jaspar_release or "newest",
            "genome_assembly": args.genome_assembly,
            "promoter_window_bp": [-args.promoter_upstream, args.promoter_downstream],
            "motif_score_threshold": args.motif_score_threshold, "ppi_score_threshold": args.ppi_score_threshold,
            "on_the_fly_processing": True, "n_processes": args.n_processes,
        },
        "summary": {
            "motif_edges": len(motif), "motif_tfs": len(motif_tfs), "target_genes": len({row[1] for row in motif}),
            "ppi_edges": len(ppi), "ppi_proteins": len({name for row in ppi for name in row[:2]}),
            "requested_tfs_without_motif_edges": sorted(set(tf_names) - set(motif_tfs)),
            # Requested TFs above whose track had no site at the score threshold (the rest found none in a promoter).
            "tracks_without_sites_at_threshold": len(without_sites),
        },
        "artifacts": [MOTIF, PPI, "sponge_provenance/fingerprint.yaml"],
        "orientation": {
            MOTIF: "no header; columns TF symbol, target gene symbol, 1 (a binding site in the gene's promoter window)",
            PPI: "no header; columns TF, TF, STRING combined score / 1000 (physical interactions)",
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for name in (MOTIF, PPI, "manifest.json"):
        print(f"Wrote {output_dir / name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

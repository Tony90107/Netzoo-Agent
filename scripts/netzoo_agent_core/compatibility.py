"""Historical direct-call tools retained outside the execution allowlist."""

from __future__ import annotations

from .contracts import tool
from .execution import run_panda, run_puma
from .validation import inspect_netzoo_inputs

__all__ = ["TOOLS", "explain_panda_puma_io"]


@tool
def explain_panda_puma_io(topic: str = "overview") -> str:
    """Explain PANDA/PUMA input and output formats without running a workflow."""
    return f"""
PANDA needs:
- expression file: rows are genes, columns are samples, values are processed gene expression.
- motif file: TF, target gene, weight. Example: MYC<TAB>CCND1<TAB>1
- PPI file: TF1, TF2, weight. Example: MYC<TAB>MAX<TAB>1
- output: TF, Gene, Motif, Force. Force is the PANDA edge score.

PUMA needs everything PANDA needs plus:
- miRNA file: miRNA, target gene, weight. Example: hsa-miR-21<TAB>PTEN<TAB>1
- output: regulator-to-gene network. Regulators can be TFs or miRNAs.

Important preprocessing point:
Raw sequencing reads are not expression data yet. In a real RNA-seq workflow, FASTQ reads usually go through QC, trimming, alignment or pseudoalignment, quantification, gene ID mapping, filtering, and normalization before becoming the expression matrix used by PANDA/PUMA.

Requested topic: {topic}
""".strip()


TOOLS = [explain_panda_puma_io, inspect_netzoo_inputs, run_panda, run_puma]

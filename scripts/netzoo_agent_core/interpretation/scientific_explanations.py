"""Capability-gated scientific explanations, independent of workflow names.

Facts describe declared transformations, never select workflows or alter goals.
Mutation normalization/pathway aggregation reference:
https://www.nature.com/articles/s41416-018-0109-7 (Methods, equations 1–2).
"""
from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class Explanation:
    required_transformations: frozenset[str]
    concern_pattern: str
    text: str


EXPLANATIONS = (
    Explanation(frozenset({"gene_length_normalization"}),
                r"gene.{0,12}length|longer.{0,12}gene|基因長度|較長.{0,8}基因",
                "Gene length normalization addresses the greater opportunity for mutations in longer genes; "
                "gene/exon sizes are therefore required, not just the mutation matrix."),
    Explanation(frozenset({"patient_mutation_burden_normalization"}),
                r"mutation.{0,12}burden|\btmb\b|突變負荷|負荷量",
                "Patient mutation burden normalization rescales each patient's mutation scores relative to their "
                "overall mutation burden, so total burden does not dominate the comparison. This is a relative "
                "score normalization, not a clinical TMB estimate or a correction for every sequencing bias."),
    Explanation(frozenset({
                    "gene_length_normalization",
                    "patient_mutation_burden_normalization",
                    "pathway_aggregation",
                }),
                r"spars|99%|充滿.{0,5}0|稀疏",
                "Gene-length normalization scales each gene's non-silent mutation count by its exon length. "
                "Patient-burden normalization then rescales those gene scores by the patient-specific "
                "cancer-associated mutation rate, reducing domination by globally hypermutated samples. "
                "Pathway aggregation next corrects for pathway size and for genes annotated to multiple "
                "pathways, compressing sparse, heterogeneous gene events into comparable pathway-by-sample "
                "scores. Patients with mutations in different genes within the same biological pathway can "
                "therefore share a functional signal that gene-by-gene comparison would miss. These corrections "
                "require gene/exon lengths, a cancer-gene set, and pathway annotations in addition to the mutation "
                "matrix. This compression does not guarantee meaningful clusters; residual mutation burden, "
                "gene-set coverage, batch effects, and cluster stability still require validation."),
    Explanation(frozenset({"pathway_aggregation"}),
                r"spars|99%|充滿.{0,5}0|稀疏",
                "The sparse mutation matrix motivates pathway aggregation: patients may have mutations in "
                "different genes within the same biological pathway. Comparing pathway mutation scores can "
                "recover shared functional patterns that gene-by-gene comparisons miss. It does not guarantee "
                "biologically meaningful clusters; gene-set coverage and cluster stability still need validation."),
    Explanation(frozenset({"pathway_aggregation", "sample_distance", "sample_clustering"}),
                r"pathway|途徑|距離|distance|subtyp|分群|亞型",
                "Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances "
                "are then calculated from those profiles, and clustering assigns sample labels. These are separate "
                "artifacts, not patient-specific mutation networks."),
)


def scientific_explanations(task: str, capabilities: list[dict], rejected: list[dict]) -> list[str]:
    text = unicodedata.normalize("NFKC", task).casefold()
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    available = [set(item.get("transformations", [])) for item in capabilities]
    matched = [
        entry for entry in EXPLANATIONS
        if any(entry.required_transformations <= transforms for transforms in available)
        and re.search(entry.concern_pattern, text)
    ]
    # When the same concern has both a compact explanation and a richer one,
    # retain the strict transformation superset. The compact entry still serves
    # workflows that declare only the smaller capability.
    matched = [
        entry for entry in matched
        if not any(
            entry.concern_pattern == other.concern_pattern
            and entry.required_transformations < other.required_transformations
            for other in matched
        )
    ]
    explanations = [entry.text for entry in matched]
    if rejected:
        explanations.insert(0, "Method suitability depends on the current input and the requested result, "
                            "not on using the same tool as a previous analysis. Changing a file's format does "
                            "not change its scientific modality; a patient-indexed score matrix is not an "
                            "individually inferred network. Use the compatible pathway for the current goal.")
    return explanations

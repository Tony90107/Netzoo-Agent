"""The registry's results in a few families, for "which result do you want?" (docs/research-log/clarify-menu-2026-11-01).

clarify-options showed Jev cannot list alternatives for a vague request (its read is one result or none). The question
asks what kind of result the user wants, so the card offers every kind there is: each family is a fixed sentence in
the user's terms and the capability sheet's produce entries it covers -- every produce entry in exactly one family
(a test checks it), a comparison or test entry in the family of the result it tests. No model is involved.
"""
from __future__ import annotations

from functools import lru_cache

__all__ = ["FAMILIES", "families", "family_of"]

FAMILIES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("regulatory_all", "one regulatory network (TF or miRNA to gene) built from all the samples together",
     ("panda.tf_gene_network", "panda.targeting_scores", "panda.condition_comparison", "puma.regulator_gene_network",
      "puma.targeting_scores", "otter.tf_gene_network", "otter.targeting_scores", "giraffe.signed_regulation",
      "cobra.adjusted_input_to_regulation")),
    ("regulatory_per_sample", "a separate regulatory network (TF or miRNA to gene) for each sample",
     ("lioness_panda.per_sample_networks", "lioness_panda.per_sample_targeting", "lioness_panda.association_tests",
      "lioness_puma.per_sample_networks", "lioness_puma.per_sample_targeting", "lioness_puma.association_tests")),
    ("coexpression_per_sample", "a separate gene-gene co-expression network for each sample",
     ("lioness_coexpression.per_sample_networks", "lioness_coexpression.comparisons", "bonobo.per_sample_networks")),
    ("covariate_coexpression", "how covariates such as group, batch or age change gene co-expression",
     ("cobra.covariate_components",)),
    ("tf_activity", "each transcription factor's activity in each sample",
     ("giraffe.tf_activity", "giraffe.activity_tests")),
    ("two_layer", "a network linking two kinds of omics data, such as RNA and methylation",
     ("dragon.two_layer_network", "dragon.edge_pvalues", "dragon.group_comparison",
      "lioness_dragon.per_sample_networks", "lioness_dragon.association_tests")),
    ("communities", "modules or communities in a regulator-gene network",
     ("condor.communities", "condor.core_scores", "condor.enrichment")),
    ("subtypes", "patient subtypes from somatic mutations",
     ("sambar.subtypes", "sambar.clinical_comparison")),
)


@lru_cache(maxsize=1)
def families() -> list[dict]:
    """[{key, text, entries, workflows}] in menu order."""
    from ..capability_sheet import sheet_entries

    entries = sheet_entries()
    return [{"key": key, "text": text, "entries": list(ids),
             "workflows": sorted(dict.fromkeys(entries[i].workflow for i in ids))} for key, text, ids in FAMILIES]


def family_of(entry_id: str) -> str | None:
    return next((key for key, _text, ids in FAMILIES if entry_id in ids), None)

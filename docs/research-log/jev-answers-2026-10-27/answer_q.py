"""The Jev answer read (frozen before any run): the same closed menu each form question uses, applied to the user's
answer to the question. Bound when Jev's probability on the options meaning one value is >= BIND."""
BIND = 0.7
# Jev option -> the dimension value it means (options absent here bind nothing: not_stated, other, none).
VALUES = {
    "group_membership": {"overlapping": "several_groups", "one_each": "one_group"},
    "time_model": {"dynamic": "dynamic", "separate": "not_dynamic"},
    "spatial": {"uses_neighbors": "uses_neighbors", "independent": "not_spatial"},
    "input_network": {"regulator_gene": "regulator_gene", "gene_gene": "gene_gene"},
}


def state(question: str, answer: str) -> str:
    return f"The assistant asked the user:\n{question}\n\nThe user's answer:\n{answer}"

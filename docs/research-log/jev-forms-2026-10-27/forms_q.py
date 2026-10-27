"""The Jev questions of the forms round (frozen before any run; never reworded after one).

Each asks only about the user's words, on a closed menu. `RULES_OUT` names, per attribute, the options under which
the typed value is what the user said; a row is doubted when Jev's probability on those options is <= 0.3.
"""
QUESTIONS = {
    "time_model": {
        "instructions": ("The user's samples may come from several time points or stages. Does the request say the "
                         "wanted result must model how the system changes from one time point to the next (time "
                         "lags, transitions, trajectories, a dynamic model)?"),
        "criteria": {
            "dynamic": "Yes: the result must model change from one time point to the next.",
            "separate": "No: the request wants results for samples or time points that are not linked into a model "
                        "of change (they may still be compared).",
            "not_stated": "The request does not say.",
        },
        "part": "The part that asks for the result",
    },
    "spatial": {
        "instructions": ("Does the request say the wanted result must use where samples sit in space, or which "
                         "samples are neighbours (spatial neighbourhoods, contiguous tissue regions)?"),
        "criteria": {
            "uses_neighbors": "Yes: the result must use positions in space or neighbouring samples.",
            "independent": "No: each sample is treated on its own.",
            "not_stated": "The request does not say.",
        },
        "part": "The part that asks for the result",
    },
    "input_network": {
        "instructions": ("The wanted result may be computed from a network the user already has. What kind of "
                         "network does the user say it is computed from?"),
        "criteria": {
            "regulator_gene": "Links from regulators such as transcription factors to target genes (for example a "
                              "PANDA or OTTER network, or a TF-to-gene edge list).",
            "gene_gene": "Links among genes or other features of one kind, such as a co-expression or "
                         "partial-correlation network (for example from DRAGON).",
            "other": "Another kind of network, such as protein-protein interactions.",
            "none": "The user has no such network, or the result is not computed from one.",
            "not_stated": "The request does not say.",
        },
        "part": "The part that asks for the result",
    },
}
# The options that mean the typed value is what the user said (input_network: filled per row from the credited entries).
RULES_OUT = {"time_model": ("dynamic",), "spatial": ("uses_neighbors",)}


def state(attr: str, request: str, quote: str) -> str:
    return f"User request:\n{request}\n\n{QUESTIONS[attr]['part']}:\n{quote}"

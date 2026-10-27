"""The overlap question asked of Jev (declared before any run)."""
INSTRUCTIONS = ("The user asks for groups (communities, modules, subtypes or clusters). Does the request say that one "
                "item (a gene, regulator or sample) may belong to more than one group at the same time?")
CRITERIA = {
    "overlapping": "Yes: the request says an item may belong to several groups at once, or asks for a membership "
                   "strength or degree in each group.",
    "one_each": "No: the request says each item belongs to exactly one group.",
    "not_stated": "The request does not say whether an item can belong to more than one group.",
}
def state(request, quote):
    return f"User request:\n{request}\n\nThe part that asks for groups:\n{quote}"

"""jev-first-fields phase B: the frozen Jev questions and the value maps (ROUND.md). Never reworded after a run."""
from __future__ import annotations

from netzoo_agent_core.interpretation import jev_forms, jev_overlap

QUESTIONS = {
    "group_membership": {"instructions": jev_overlap.INSTRUCTIONS, "criteria": jev_overlap.CRITERIA},
    "input_network": {key: jev_forms.QUESTIONS["input_network"][key] for key in ("instructions", "criteria")},
    "scale": {
        "instructions": "How many of the asked-for results does the quoted part want?",
        "criteria": {
            "per_sample": "One result for each sample, patient or individual.",
            "per_group": "One result for each group, condition, stage or time point, built from all that group's "
                         "samples together.",
            "whole_cohort": "One result for all the samples together.",
            "not_stated": "The request does not say.",
        },
    },
    "needs_sign": {
        "instructions": "Does the quoted part need the result to say whether a regulator activates or represses its "
                        "targets (a signed effect)?",
        "criteria": {
            "signed": "Yes: it needs activation versus repression, or the direction of each regulatory effect.",
            "not_signed": "No: link strengths or scores are enough.",
            "not_stated": "The request does not say.",
        },
    },
    "regulator_kinds": {
        "instructions": "Which kinds of regulators must the asked-for result contain?",
        "criteria": {
            "tf": "Transcription factors only.",
            "tf_and_mirna": "Transcription factors and miRNAs.",
            "other_regulators": "Other regulators, such as lncRNAs, as regulators in their own right.",
            "not_about_regulators": "The result is not about regulators (for example co-expression or groups).",
            "not_stated": "The request does not say.",
        },
    },
}

VALUES = {
    "group_membership": {"overlapping": "several_groups", "one_each": "one_group", "not_stated": "not_stated"},
    "input_network": {value: value for value in jev_forms.QUESTIONS["input_network"]["criteria"]},
    "scale": {"per_sample": "per_sample", "per_group": "per_group", "whole_cohort": "whole_cohort",
              "not_stated": "unstated"},
    "needs_sign": {"signed": True, "not_signed": False, "not_stated": False},
    "regulator_kinds": {"tf": ["tf"], "tf_and_mirna": ["tf", "mirna"], "other_regulators": ["other"],
                        "not_about_regulators": [], "not_stated": []},
}
GROUPING = ("one_group", "several_groups", "not_stated")
"""group_membership is taken from Jev only where mini typed one of these (the question presumes groups)."""

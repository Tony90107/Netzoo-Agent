"""Explain a qualified method in scientific prose, reserving API detail for requests."""

from __future__ import annotations

import re

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS
from ..settings import INPUT_ROLE_FIELDS
from .extraction import INPUT_LABELS
from .inspected_answers import with_inspection_footer
from .method_philosophy import method_philosophies_for

_CONCEPT = re.compile(
    r"\b(?:why|assumptions?|principles?|mechanisms?|explain)\b|為什麼|为什么|假設|假设|原理|機制|机制",
    re.I,
)
_TECHNICAL = re.compile(
    r"\b(?:API|schema|parameters?|arguments?|defaults?|script|code)\b|參數|参数|欄位|字段|規格|规格|程式|脚本",
    re.I,
)
_FAILURE = re.compile(
    r"\b(?:fail\w*|collapse\w*|hubs?|giant|wrong)\b|失敗|失败|崩潰|崩溃|巨型|超級|超级|慘",
    re.I,
)


def base_not_first(action, policy):
    """A per-sample extension writes its base's cohort network too, so the base is not a separate run.

    The heading used to read "**PUMA → LIONESS-PUMA**", which suggests running
    PUMA first, while the composition reply for the same pair says the
    opposite (Test 2, 2026-10-02).
    """
    cap = policy.workflows[action].output_capability
    bases = [policy.workflows[a].workflow for a in cap.guidance_predecessors if a in policy.workflows]
    if not bases or not {"aggregate", "sample_specific"} <= set(cap.granularities):
        return ""
    return (
        f"{policy.workflows[action].workflow} also writes the cohort network, "
        f"so {' and '.join(bases)} need not run first."
    )


def method_paragraphs(action, policy, *, task=""):
    spec = policy.workflows[action]
    cap = spec.output_capability
    if "bipartite_community_detection" in cap.selection_tags and _FAILURE.search(task):
        # Explain a possible structural mismatch, not a diagnosis of unseen data.
        # https://arxiv.org/abs/0707.1616 and the official CONDOR vignette.
        return [
            "The first thing to check is whether the analysis preserved the two node types: "
            "regulators and targets. In a bipartite representation, edges run between those "
            "types. A method whose null model allows within-type edges is comparing the data "
            "with a different kind of network. If you first projected onto targets, a shared "
            "hub can also create many target-to-target links and make a broad group look dense.",
            "**"
            + spec.workflow
            + "** fits this structural question because it optimizes "
            "bipartite modularity. Its null model keeps the two partitions and accounts for "
            "node degree, or strength in the weighted case. The question becomes: are these "
            "regulators and targets more strongly connected than expected given how connected "
            "each node already is? BRIM alternates updates between the two partitions to seek "
            "a better community assignment.",
            "A giant community alone does not establish why the previous method failed. "
            "Ordinary modularity can already account for degree; resolution limits, graph "
            "projection and weight handling also matter. A bipartite method addresses the "
            "structural assumption, but biological meaning still needs enrichment or other validation.",
            "To try this, preserve regulator and target identities when converting the weight "
            "matrix to a regulator–target edge list. The result is community membership for "
            "both node types. Check the meaning and sign of the weights before fitting; "
            "do not silently drop signs or take absolute values.",
        ]
    paragraphs = [
        "**"
        + spec.workflow
        + "**. "
        + " ".join(method_philosophies_for(cap.selection_tags) or (spec.description,))
    ]
    fields = [f for f in spec.required_inputs if f in INPUT_ROLE_FIELDS]
    requirements = [INPUT_LABELS.get(f, f.replace("_", " ")) for f in fields]
    for group in spec.required_input_groups:
        labels = [
            INPUT_LABELS.get(f, f.replace("_", " "))
            for f in group
            if f in INPUT_ROLE_FIELDS
        ]
        if labels:
            requirements.append("either " + " or ".join(labels))
    artifacts = sorted(cap.produced_artifacts or {cap.artifact_type})
    results = [
        ARTIFACT_SEMANTICS[a].description for a in artifacts if a in ARTIFACT_SEMANTICS
    ]
    if requirements:
        paragraphs.append(
            "You would need "
            + ", ".join(requirements)
            + ". "
            + "The analysis would provide "
            + "; ".join(r[0].lower() + r[1:] for r in results)
            + "."
            + (f" {base}" if (base := base_not_first(action, policy)) else "")
        )
    return paragraphs


def render_scientific_guidance(decision, policy, *, task):
    """A conceptual question with one qualified candidate needs an explanation."""
    actions = list(dict.fromkeys(decision.matched_actions))
    if (
        decision.action != "no_tool"
        or decision.should_execute
        or decision.capability_match_status not in {"exact", "fallback"}
        or len(actions) != 1
        or actions[0] not in policy.workflows
        or decision.rejected_methods
        or decision.clarification_question
        or not _CONCEPT.search(task)
        or _TECHNICAL.search(task)
    ):
        return None
    paragraphs = method_paragraphs(actions[0], policy, task=task)
    if decision.capability_match_status == "fallback":
        paragraphs.append(
            "This is conditional guidance, not an exact semantic match; the full method-to-data fit still needs checking."
        )
    paragraphs.append("No files were inspected and no analysis ran.")
    if "bipartite_community_detection" in policy.workflows[
        actions[0]
    ].output_capability.selection_tags and _FAILURE.search(task):
        paragraphs.append(
            "Which community method did you try, and did you use the original bipartite network or a projection? Are the weights signed or nonnegative?"
        )
    return with_inspection_footer(
        "\n\n".join(paragraphs), decision.inspected_directories
    )

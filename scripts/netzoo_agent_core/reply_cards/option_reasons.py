"""What an option means for this request, next to the other options on its card.

Option lines used to describe each method on its own ("Widely used baseline:
message passing over motif, PPI and co-expression evidence"), identical for
every request. Someone choosing between them needs what each one gives them
and how it differs from the others listed (2026-10-02, the user's feedback on
Test 1's card). So a line says what you get, what it adds or costs against the
other options here, and the card says once what they all share.

Everything is computed from the typed request and the registry entries of the
listed workflows. The request's wording is read only by `_COOPERATION`, and
only to decide whether a shared note is worth saying; nothing here orders,
selects or recommends an option.
"""

from __future__ import annotations

import re

from workflow_registry import OUTPUT_CAPABILITIES, REQUIRED_INPUTS

from .method_notes import gives
from .phrases import join_names, workflow_name

__all__ = ["option_parts", "per_sample_use", "scale_split", "shared_points"]

# The use of a per-sample network that the registry's downstream notes name
# (DOWNSTREAM_ANALYSES, LIONESS targeting scores related to survival).
_PER_SAMPLE_USE = "Lets you compare samples, or relate them to outcomes such as survival"
_NETWORKS = frozenset({
    "regulatory_network", "signed_regulatory_effect_network", "coexpression_network", "multi_omic_network",
})
# A request that mentions TFs working together. Display only: it decides
# whether to say that every listed method models them through the PPI
# network. "Complex" alone is not enough ("complex disease").
_COOPERATION = re.compile(
    r"\bcooperat\w*|\bcomplexes\b|\b(?:TFs?|proteins?|transcription[- ]factors?)\s+complex\w*|"
    r"協同|複合體|复合体",
    re.I,
)


def _signature(action: str):
    capability = OUTPUT_CAPABILITIES[action]
    return (capability.artifact_type, frozenset(capability.produced_artifacts or {capability.artifact_type}),
            capability.granularities, capability.regulator_types)


def _per_sample(action: str) -> bool:
    capability = OUTPUT_CAPABILITIES.get(action)
    return capability is not None and "sample_specific" in capability.granularities


def _splits_by_sample(action: str, candidates: list[str], outcome) -> bool:
    """A per-sample option beside a cohort-only one, for a request not asking for one cohort network."""
    granularity = outcome.granularity if outcome is not None else "unknown"
    return (granularity != "aggregate" and _per_sample(action)
            and any(not _per_sample(other) for other in candidates if other in OUTPUT_CAPABILITIES))


def _base(action: str, policy) -> str | None:
    capability = OUTPUT_CAPABILITIES.get(action)
    bases = [a for a in (capability.guidance_predecessors if capability else ()) if a in policy.workflows]
    return bases[0] if bases else None


def per_sample_use(action: str, policy) -> list[str]:
    """What one network per sample lets you do, and what it costs."""
    base = _base(action, policy)
    return [_PER_SAMPLE_USE, *([f"Slower: it reruns {workflow_name(policy, base)} once per sample"] if base else [])]


def option_parts(action: str, candidates: list[str], outcome, policy, *, before: list[str]) -> tuple[list[str], list[str]]:
    """(what you get, what it adds or costs) for one option, against the options listed before it.

    A workflow with the same registered output as an earlier option says so
    instead of repeating that option's line: OTTER beside PANDA is the same
    kind of network from a different algorithm, and what separates them is
    the condition under which each is preferred.
    """
    if action not in OUTPUT_CAPABILITIES:
        return [gives(action)], []
    twin = next((other for other in before
                 if other in OUTPUT_CAPABILITIES and _signature(other) == _signature(action)), None)
    if twin is not None:
        noun = "network" if OUTPUT_CAPABILITIES[action].artifact_type in _NETWORKS else "result"
        got = [f"The same kind of {noun} as {workflow_name(policy, twin)}, from a different algorithm"]
    else:
        got = [gives(action)]
    return got, (per_sample_use(action, policy) if _splits_by_sample(action, candidates, outcome) else [])


def scale_split(candidates: list[str], outcome) -> bool:
    """Some options give one result per sample and others only a cohort result, for a request of untyped scale."""
    known = [a for a in candidates if a in OUTPUT_CAPABILITIES]
    granularity = outcome.granularity if outcome is not None else "unknown"
    per_sample = [a for a in known if _per_sample(a)]
    return granularity not in {"aggregate", "sample_specific"} and 0 < len(per_sample) < len(known)


def shared_points(candidates: list[str], outcome, task: str, policy) -> list[str]:
    """What the card says once about every option: which give one result per sample, and a shared mechanism."""
    known = [a for a in candidates if a in OUTPUT_CAPABILITIES]
    points = []
    if scale_split(known, outcome):
        # Said of the options only: an untyped scale is not proof the request
        # never stated one ("For each individual ... their own network").
        per_sample = [a for a in known if _per_sample(a)]
        noun = "network" if all(OUTPUT_CAPABILITIES[a].artifact_type in _NETWORKS for a in known) else "result"
        cohort = [a for a in known if a not in per_sample]
        sample_names = join_names([workflow_name(policy, a) for a in per_sample], "and")
        cohort_names = join_names([workflow_name(policy, a) for a in cohort], "and")
        points.append(f"{'Only ' + sample_names + ' gives' if len(per_sample) == 1 else sample_names + ' give'} "
                      f"one {noun} per sample; {cohort_names} {'gives' if len(cohort) == 1 else 'give'} "
                      "one across all samples.")
    if len(known) > 1 and all("ppi_file" in REQUIRED_INPUTS.get(a, ()) for a in known) and _COOPERATION.search(task):
        every = _EVERY.get(len(known), "all of them")
        points.append(f"As for TFs that cooperate in complexes, {every} model this through the PPI network.")
    return points


_EVERY = {2: "both", 3: "all three", 4: "all four", 5: "all five", 6: "all six"}

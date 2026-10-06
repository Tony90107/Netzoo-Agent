"""Whether each listed workflow can be applied to the request's data (plan item 4, Log 380).

The registry says what each workflow needs; until now the request's side was
read by word lists, which failed both ways: "no transcription factor motifs"
counted as having them (Log 373) and "no other data" still drew "Do you also
have a motif prior and a PPI network?" (Log 378 B3-1). The data-facts call
(Logs 376, 380) reads TF priors and miRNA with quotes; where it has read a
kind, its reading replaces the wording for that kind everywhere the reply
judges inputs. Where it has not, nothing changes.

A workflow is applicable when every input it needs is stated, not applicable
when one is ruled out, and short of information when one is unstated. Only
the reply and card read this: nothing here selects, ranks or removes a
workflow, and no execution depends on it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from workflow_registry import RUN_ACTIONS

from ..contracts.applicability import CandidateApplicability, DataFact

__all__ = [
    "PresentInputs", "assess_applicability", "conditioned_lead", "data_condition", "facts_artifacts",
    "merge_inputs", "needs_data_facts",
]

# The input roles the data-facts call reads, as the reply's input ontology names them.
_FACT_ARTIFACTS = {"tf_priors": ("motif_prior", "ppi_prior"), "mirna": ("mirna_prior",)}
_FACT_FIELDS = {"tf_priors": ("motif_file", "ppi_file"), "mirna": ("mirna_file",)}


class PresentInputs(frozenset):
    """The input artifacts a request states, with the ones a model reading has judged.

    ``judged``: artifacts whose presence the data-facts call decided, so no
    word list may overrule it. ``absent``: the judged ones the request rules out.
    """

    judged: frozenset[str]
    absent: frozenset[str]
    quotes: Mapping[str, str]

    def __new__(cls, present: Iterable[str], judged: Iterable[str] = (), absent: Iterable[str] = (),
                quotes: Mapping[str, str] | None = None):
        instance = super().__new__(cls, present)
        instance.judged = frozenset(judged)
        instance.absent = frozenset(absent)
        instance.quotes = dict(quotes or {})
        return instance


def facts_artifacts(facts: Mapping[str, Any] | None) -> tuple[set[str], set[str], set[str], dict[str, str]]:
    """(stated, ruled out, judged, quote by artifact) from a verified data-facts entry."""
    stated, ruled_out, judged, quotes = set(), set(), set(), {}
    for kind, artifacts in _FACT_ARTIFACTS.items():
        state = (facts or {}).get("priors" if kind == "tf_priors" else kind)
        if state not in {"stated", "ruled_out", "unstated"}:
            continue
        judged.update(artifacts)
        quote = (facts or {}).get(("priors" if kind == "tf_priors" else kind) + "_quote") or ""
        for artifact in artifacts:
            quotes[artifact] = quote
        if state == "stated":
            stated.update(artifacts)
        elif state == "ruled_out":
            ruled_out.update(artifacts)
    return stated, ruled_out, judged, quotes


def merge_inputs(present: Iterable[str], facts: Mapping[str, Any] | None) -> PresentInputs:
    """The wording's present inputs, with every kind the data-facts call judged replaced by its reading."""
    stated, ruled_out, judged, quotes = facts_artifacts(facts)
    return PresentInputs((set(present) - judged) | stated, judged=judged, absent=ruled_out, quotes=quotes)


def needs_data_facts(actions: Iterable[str], bound: Iterable[str]) -> bool:
    """Whether a listed workflow needs TF priors or miRNA data the request does not bind as files."""
    from workflow_registry import REQUIRED_INPUTS

    bound = set(bound)
    for action in actions:
        needed = set(REQUIRED_INPUTS.get(action, ()))
        for fields in _FACT_FIELDS.values():
            if needed & set(fields) and not set(fields) <= bound:
                return True
    return False


def assess_applicability(actions: Iterable[str], present: PresentInputs, task: str) -> list[CandidateApplicability]:
    """Each listed run workflow's status against the request's data, with the basis for each kind."""
    from ..reply_cards.method_notes import input_fields, missing_input_labels

    assessed = []
    for action in dict.fromkeys(actions):
        if action not in RUN_ACTIONS:
            continue
        required, _groups = input_fields(action)
        basis = []
        for kind, fields in _FACT_FIELDS.items():
            if not set(fields) & set(required):
                continue
            artifacts = _FACT_ARTIFACTS[kind]
            source = "model" if set(artifacts) <= present.judged else "words"
            if set(artifacts) & present.absent:
                state = "ruled_out"
            else:
                state = "stated" if set(artifacts) <= present else "unstated"
            basis.append(DataFact(kind=kind, state=state, quote=present.quotes.get(artifacts[0], ""), source=source))
        if any(fact.state == "ruled_out" for fact in basis):
            status = "not_applicable"
        elif missing_input_labels(action, present, task) or any(fact.state == "unstated" for fact in basis):
            status = "insufficient_information"
        else:
            status = "applicable"
        assessed.append(CandidateApplicability(action=action, status=status, basis=basis))
    return assessed


_KIND_LABELS = {"tf_priors": "a motif prior and a PPI network", "mirna": "a miRNA list"}


def data_condition(decision, action: str) -> tuple[str, str] | None:
    """("ruled_out" | "unstated", what it needs) when the reading judged *action* short of data.

    Only kinds the data-facts call read count: a workflow is never called
    unusable on the wording alone. The reply and card then present it under
    that condition instead of as the selected answer (plan item 4: a workflow
    is not chosen just because the inputs it reads are compatible).
    """
    item = next((entry for entry in decision.applicability if entry.action == action), None)
    if item is None:
        return None
    for state in ("ruled_out", "unstated"):
        kinds = [fact.kind for fact in item.basis if fact.state == state and fact.source == "model"]
        if kinds:
            text = " and ".join(_KIND_LABELS[kind] for kind in kinds)
            return state, text
    return None


def conditioned_lead(decision, action: str, names: str) -> str | None:
    """The reply's first line for a workflow the reading judged short of data, else None."""
    condition = data_condition(decision, action)
    if condition is None:
        return None
    state, needs = condition
    if state == "ruled_out":
        return f"**{names}** fits the result you describe, but it needs {needs}, which you said you do not have."
    return f"**{names}** fits the result you describe if you have {needs}."

"""The turn's data-needs plan (plan item 5, Log 383).

Log 382 traced the user-visible failures of Logs 379-381 to shared causes.
Two of them are here:
- Whether to ask about data was decided by each renderer under its own
  preconditions: network results only, a reply-kind whitelist, an
  alternative must exist, no listed workflow may run on the stated data. In
  the current system that accounted for 46 of 89 failures, and each round's
  fix moved them to the next unguarded path.
- What data the question needs was inferred from the workflows routing
  listed, so a routing miss carried straight into the reply (16 of 89).

The plan reads the need from the question itself: the study purpose's quoted
questions, and the routing reading only when no question was quoted. It
reads the possession from the data-facts reading (Logs 376, 380, 381), or the
request's words when nothing read it. It decides once what the reply asks and
says. Every reply renders the plan; `with_data_plan` adds whatever a
renderer left out.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from workflow_registry import UNSUPPORTED_CLAIMS

from ..contracts.data_plan import DataNeed, DataPlan

__all__ = [
    "KIND_FIELDS", "KIND_LABELS", "build_data_plan", "plan_needs", "render_plan_block", "with_data_plan",
    "with_data_plan_reply",
]

# A question about regulators needs the regulator prior: every TF workflow needs a
# motif prior and a PPI network, and every miRNA workflow needs them too (PUMA).
_TF_ROLE = re.compile(r"transcription[- ]factors?|\bTFs?\b|\bregulators?\b|\bregulatory\b", re.I)
_MIRNA_ROLE = re.compile(r"\bmi(?:cro)?[- ]?RNAs?\b|\bmiRs?\b", re.I)
_TF_ARTIFACTS = frozenset({"tf_activity_matrix", "signed_regulatory_effect_network"})
KIND_LABELS = {"tf_priors": "a motif prior and a PPI network", "mirna": "a miRNA list"}
_FACT_KEYS = {"tf_priors": "priors", "mirna": "mirna"}
_WORD_ARTIFACTS = {"tf_priors": ("motif_prior", "ppi_prior"), "mirna": ("mirna_prior",)}


_QUOTED = re.compile(r'"[^"]*"|“[^”]*”')


def _questions(task: str) -> list[str]:
    """The request's own questions: sentences ending in "?", quoted text left out."""
    unquoted = _QUOTED.sub(" ", task or "")
    return [part.strip() for part in re.split(r"(?<=[.?!])\s+", unquoted) if part.strip().endswith("?")]


def plan_needs(claims, decision, task: str = "") -> tuple[bool, str, tuple[str, ...]]:
    """(answerable, basis, kinds) for the question this turn asks.

    *claims*: the study purpose's (claim, quote) pairs. A claim no registered
    workflow supports (prediction, causation) asks for nothing; with only such
    claims nothing is needed. Otherwise the quoted questions, and the request's
    own questions, name the regulators they are about -- never the sentences that
    describe the data ("maps of where transcription factors bind" is not a TF
    question). Only when neither exists do the routing reading's regulator roles.
    """
    claims = [(claim, quote) for claim, quote in claims or ()]
    asked = [quote for claim, quote in claims if claim not in UNSUPPORTED_CLAIMS]
    if claims and not asked:
        return False, "unanswerable", ()
    text = " ".join([*asked, *_questions(task)])
    if text:
        tf, mirna = bool(_TF_ROLE.search(text)), bool(_MIRNA_ROLE.search(text))
        basis = "claims" if asked else "question"
    else:
        readings = [item.outcome for item in decision.outcome_hypotheses]
        tf = any("tf" in outcome.regulator_types or outcome.artifact_type in _TF_ARTIFACTS for outcome in readings)
        mirna = any("mirna" in outcome.regulator_types for outcome in readings)
        basis = "reading" if readings else "none"
    kinds = (("tf_priors",) if tf or mirna else ()) + (("mirna",) if mirna else ())
    return True, basis, kinds


KIND_FIELDS = {"tf_priors": ("motif_file", "ppi_file"), "mirna": ("mirna_file",)}


def build_data_plan(claims, decision, facts: Mapping[str, Any] | None, words: set[str], task: str = "",
                    bound: set[str] = frozenset()) -> DataPlan:
    """The plan for this turn: each needed kind's state, and the reply's action for it.

    *bound*: the input fields the request binds as files; *words*: the input
    artifacts its wording names, used only when no reading exists.
    """
    answerable, basis, kinds = plan_needs(claims, decision, task)
    needs = []
    for kind in kinds:
        state = (facts or {}).get(_FACT_KEYS[kind])
        if set(KIND_FIELDS[kind]) <= set(bound):
            state, source, quote = "stated", "binding", ""
        elif state in {"stated", "ruled_out", "unstated"}:
            source, quote = "model", (facts or {}).get(f"{_FACT_KEYS[kind]}_quote") or ""
        else:
            # Nothing read the request (no data-facts reading this turn): only words decide. Log 403
            # replay: 25 replies said "Your question needs a motif prior and a PPI network, which your
            # request does not mention" to "We have expression, motifs and PPI" -- the reading was
            # budget-blocked and the input words missed "motifs". A request that names the kind is
            # never told it does not mention it; each part of the kind must be named ("plus TF motifs"
            # names no PPI network).
            source, quote = "words", ""
            named = set(_WORD_ARTIFACTS[kind]) <= words or all(
                pattern.search(task or "") for pattern in _PART_WORDS[kind])
            state = "stated" if named else "unstated"
        action = {"stated": "none", "ruled_out": "say_ruled_out", "unstated": "ask"}[state]
        if kind == "mirna" and action == "ask" and any(need.state == "ruled_out" for need in needs):
            # Every miRNA workflow also needs the TF priors the request rules out:
            # a miRNA list cannot make one runnable (Log 380's rule, s20 C3).
            action = "none"
        needs.append(DataNeed(kind=kind, state=state, source=source, quote=quote if state != "unstated" else "",
                              action=action))
    return DataPlan(answerable=answerable, basis=basis, needs=needs)


def _labels(kinds) -> str:
    parts = [KIND_LABELS[kind] for kind in kinds]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]).replace(" and ", ", ") + " and " + parts[-1]


_POSSESSION = re.compile(r"\bdo you (?:also |already )?have\b", re.I)
_KIND_WORDS = {"tf_priors": re.compile(r"motif|\bPPI\b|protein[- ]protein|protein interaction", re.I),
               "mirna": re.compile(r"\bmi(?:cro)?[- ]?RNA", re.I)}
# Each part of a kind, named in the request's words (the words fallback, Log 403).
_PART_WORDS = {"tf_priors": (re.compile(r"motif", re.I),
                             re.compile(r"\bPPI\b|protein[- ]protein|protein interaction", re.I)),
               "mirna": (_KIND_WORDS["mirna"],)}


def _asks(text: str, kind: str) -> bool:
    return any(_POSSESSION.search(part) and _KIND_WORDS[kind].search(part)
               for part in re.split(r"(?<=[.?!])\s+|\n+", text) if part.rstrip('")\'*').endswith("?"))


def _says_ruled_out(text: str, kind: str) -> bool:
    return any("which you said you do not have" in part and _KIND_WORDS[kind].search(part)
               for part in re.split(r"(?<=[.?!])\s+|\n+", text))


def render_plan_block(plan: DataPlan, text: str) -> str | None:
    """What the reply still lacks from the plan, as one paragraph, or None."""
    missing_says = [need for need in plan.ruled_out() if not _says_ruled_out(text, need.kind)]
    missing_asks = [kind for kind in plan.asks() if not _asks(text, kind)]
    if not missing_says and not missing_asks:
        return None
    parts = ["**Data your question needs.**"]
    for need in missing_says:
        said = f' ("{need.quote}")' if need.quote else ""
        parts.append(f"A {('TF-level' if need.kind == 'tf_priors' else 'miRNA-level')} answer needs "
                     f"{KIND_LABELS[need.kind]}, which you said you do not have{said}.")
    if missing_asks:
        parts.append(f"Your question needs {_labels(missing_asks)}, which your request does not mention. "
                     f"Do you have {_labels(missing_asks)}?")
    return " ".join(parts)


def with_data_plan(text: str, plan: DataPlan | None) -> str:
    """The reply with the plan's missing asks and statements above its closing line."""
    from .inspected_answers import above_closing

    if plan is None or not text:
        return text
    block = render_plan_block(plan, text)
    return text if block is None else above_closing(text, block)


def with_data_plan_reply(result: dict, state, reply) -> dict:
    """`respond()`'s last step: every guidance reply shows the plan's questions and statements.

    Guidance replies (the outside-step kinds, which include the per-reading
    replies) and the routing-failure reply. A routing failure still has a
    question: the study purpose names what it needs even when no workflow was
    validated (Log 382: 7 of 10 such sessions).
    """
    from ..contracts import TaskDecision
    from .outside_steps import _REPLY_KINDS

    kind = result.get("reply_kind")
    if kind not in _REPLY_KINDS | {"unresolved"}:
        return result
    plan = TaskDecision.model_validate(state["decision"]).data_plan
    text = str(result["messages"][-1].content)
    updated = with_data_plan(text, plan)
    return result if updated == text else reply(updated, kind)

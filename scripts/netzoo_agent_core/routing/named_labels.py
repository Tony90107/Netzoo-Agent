"""Resolving a registered label the requester wrote out by name.

Separated from the matcher because it answers a different question. The matcher
asks which capability produces the requested scientific result; this asks which
registered label the request actually contains, which is a lookup against the
registry rather than an inference about meaning.
"""

from __future__ import annotations

import re

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS, RecommendedAction
from ..interpretation.request_integrity import _scoped_clauses


def _workflow_name_pattern(action: str) -> str:
    words = re.split(r"[-_\s]+", ACTION_DEFINITIONS[action].workflow.casefold())
    return (
        r"(?<![a-z0-9])"
        + r"[\s_-]*".join(re.escape(word) for word in words)
        + r"(?![a-z0-9])"
    )


def _current_scope_text(task: str) -> str:
    """Return the request minus its historical clauses.

    A workflow the user reports having already run is not the workflow being
    asked about. `_match_semantic_request` already refuses to let a historical
    mention override a compatible typed outcome, but that guard needs an outcome
    to protect; after semantic validation fails there is none, and a live round
    recommended a forbidden PANDA to a request whose only mention of it was
    "Previously I used PANDA" and which said it did not want inferred networks.

    The clause scoping is the same deterministic pass `input_mentions` uses, so
    history is recognised here exactly as it is for input artifacts.
    """
    return " ".join(
        clause for clause, scope in _scoped_clauses(task) if scope != "historical"
    )


def named_workflow_action(task: str) -> RecommendedAction | None:
    """Resolve a currently written registered workflow name, longest first."""
    candidates = sorted(
        RUN_ACTIONS,
        key=lambda action: len(ACTION_DEFINITIONS[action].workflow),
        reverse=True,
    )
    current = _current_scope_text(task).casefold()
    for action in candidates:
        if re.search(_workflow_name_pattern(action), current):
            return action
    return None


def solely_named_run_action(task: str) -> RecommendedAction | None:
    """The one runnable capability the current request writes out by name.

    `named_workflow_action` answers "which label is in here", taking the longest
    on a tie. That is the wrong answer when the requester named two: a request
    mentioning both PANDA and PUMA has asked a question, not stated a fact, and
    silently taking the longer label would answer it for them.

    Counting has to be over every registered label, not only the runnable ones.
    "Search the web with WEB-SEARCH for current PANDA references" names two, and
    counting runnable labels alone would see one and run PANDA -- turning a topic
    the requester wanted read about into a job. Two labels named, whatever their
    kind, means nothing here is the only fact.

    Overlaps are not two. `LIONESS-PANDA` contains `PANDA` between two
    non-alphanumeric characters, so both labels match the same span; the inner
    one is an artefact of the outer and is dropped. Labels count separately only
    when they occupy separate spans.
    """
    spans: list[tuple[int, int, RecommendedAction]] = []
    current = _current_scope_text(task).casefold()
    for action, definition in ACTION_DEFINITIONS.items():
        # The same eligibility rule `named_registered_action` uses: a one-word
        # label counts only for an action the router can recommend, because
        # `inspect_inputs` is labelled with the bare English word `inputs`.
        if action == "no_tool" or (
            definition.output_capability is None
            and len(re.split(r"[-_\s]+", definition.workflow.strip())) == 1
        ):
            continue
        found = re.search(_workflow_name_pattern(action), current)
        if found is not None:
            spans.append((found.start(), found.end(), action))
    distinct = [
        item for item in spans
        if not any(
            other is not item and other[0] <= item[0] and item[1] <= other[1]
            for other in spans
        )
    ]
    if len(distinct) != 1:
        return None
    action = distinct[0][2]
    return action if action in RUN_ACTIONS else None


def named_registered_action(task: str):
    """Resolve an explicitly written registry workflow label, longest first.

    A label must be distinctive enough to be a deliberate reference. Method
    names are (PANDA, SAMBAR), and so are multi-word step labels a requester
    would have to type on purpose (WEB-SEARCH, "bonobo inputs"). One label was
    neither: `inspect_inputs` is labelled with the bare English word `inputs`,
    so "the standard integration of those three inputs" was read as explicitly
    naming a validation step and reported as an exact match on a workflow name.
    A live round recommended that non-workflow to a user.

    So a single-word label is only eligible when the action is one the router can
    actually recommend. Excluding every supporting action instead would have
    broken naming WEB-SEARCH deliberately, which is legitimate.
    """
    candidates = sorted(
        (
            (action, definition)
            for action, definition in ACTION_DEFINITIONS.items()
            if action != "no_tool"
            and (
                definition.output_capability is not None
                or len(re.split(r"[-_\s]+", definition.workflow.strip())) > 1
            )
        ),
        key=lambda item: len(item[1].workflow),
        reverse=True,
    )
    for action, definition in candidates:
        words = re.split(r"[-_\s]+", definition.workflow.casefold())
        pattern = (
            r"(?<![a-z0-9])"
            + r"[\s_-]*".join(re.escape(word) for word in words)
            + r"(?![a-z0-9])"
        )
        if re.search(pattern, task.casefold()):
            return action
    return None


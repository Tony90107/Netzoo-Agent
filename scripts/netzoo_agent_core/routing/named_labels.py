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
from .path_tokens import without_path_tokens


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
    history is recognised here exactly as it is for input artifacts. Path tokens
    are locations, not names, and are blanked out (Log 191).
    """
    return without_path_tokens(" ".join(
        clause for clause, scope in _scoped_clauses(task) if scope != "historical"
    ))


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
    distinct = _named_spans(task)
    if len(distinct) != 1:
        return None
    action = distinct[0][2]
    return action if action in RUN_ACTIONS else None


def _named_spans(task: str) -> list[tuple[int, int, RecommendedAction]]:
    """Every registered label the current request names, one per separate span (inner overlaps dropped)."""
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
    return [
        item for item in spans
        if not any(
            other is not item and other[0] <= item[0] and item[1] <= other[1]
            for other in spans
        )
    ]


_RUN_VERB_BEFORE = re.compile(r"\b(?:run|execute|launch|plan)\s+(?:the\s+)?$")


def run_target_with_named_inputs(task: str) -> RecommendedAction | None:
    """The workflow a "run X on <Y's output>" request runs, when the other labels only name its input.

    "Run PORCUPINE on the LIONESS-PANDA networks ..." names two labels, so `solely_named_run_action` refuses it.
    Here the label right after the run verb is the target, and every other label must be a workflow whose
    registered output artifact (and, where the target restricts it, granularity) the target registers as an
    input. Anything else -- two run targets, a label that is not an input producer -- returns None.
    """
    distinct = _named_spans(task)
    current = _current_scope_text(task).casefold()
    if len(distinct) < 2 or "?" in task or "？" in task:  # a question about running it is not a run request
        return None
    targets = [item for item in distinct if _RUN_VERB_BEFORE.search(current[:item[0]])]
    if len(targets) != 1 or targets[0][2] not in RUN_ACTIONS:
        return None
    target = ACTION_DEFINITIONS[targets[0][2]].output_capability
    if target is None:
        return None
    for _, _, other in distinct:
        if other == targets[0][2]:
            continue
        produced = ACTION_DEFINITIONS[other].output_capability
        if produced is None or produced.artifact_type not in target.input_artifacts:
            return None
        wanted = target.accepted_input_granularities
        if wanted and not set(produced.granularities) & set(wanted):
            return None
    return targets[0][2]


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
    # A folder called `bonobo-toy` does not name BONOBO (Log 191).
    written = without_path_tokens(task).casefold()
    for action, definition in candidates:
        words = re.split(r"[-_\s]+", definition.workflow.casefold())
        pattern = (
            r"(?<![a-z0-9])"
            + r"[\s_-]*".join(re.escape(word) for word in words)
            + r"(?![a-z0-9])"
        )
        if re.search(pattern, written):
            return action
    return None


def named_input_artifacts(task: str, action: str) -> set[str]:
    """The registered output artifacts of the workflows the request names as the producers of *action*'s input.

    "Run PORCUPINE on the LIONESS-PANDA networks" names LIONESS-PANDA, whose registered output is a
    regulatory_network that PORCUPINE accepts: the data's type is the registry's, not a reading of the words.
    Only producers whose output *action* registers as an input (and, where it restricts it, granularity) count.
    """
    target = ACTION_DEFINITIONS[action].output_capability if action in ACTION_DEFINITIONS else None
    if target is None:
        return set()
    found = set()
    for _, _, other in _named_spans(task):
        produced = ACTION_DEFINITIONS[other].output_capability
        if other == action or produced is None or produced.artifact_type not in target.input_artifacts:
            continue
        wanted = target.accepted_input_granularities
        if not wanted or set(produced.granularities) & set(wanted):
            found.add(produced.artifact_type)
    return found

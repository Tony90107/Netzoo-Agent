"""What the user can do next, derived from the machine's own next prompt.

The next prompt already decides what the conversation accepts; these options
are only the common answers to it, written out. Each one submits text the
machine already understands (`/execute`, `new`, a workflow the prompt itself
names), so choosing an option is never a shortcut around a confirmation.
"""

from __future__ import annotations

from ..contracts.state import NextTurnPrompt
from .contracts import ReplyOption
from .phrases import workflow_name

__all__ = ["NEW_TASK", "next_steps", "plan_step"]

NEW_TASK = ReplyOption(
    key="new-task",
    label="Start a new task",
    description="Clear this goal and describe a different one.",
    answer="new",
    resolution="command",
)


def _execute() -> ReplyOption:
    return ReplyOption(
        key="execute",
        label="Execute this plan",
        description="Asks you to confirm once more, then runs this validated plan one time.",
        answer="/execute",
        resolution="command",
    )


def plan_step(policy, action: str) -> ReplyOption:
    name = workflow_name(policy, action)
    return ReplyOption(
        key=f"plan-{action}",
        label=f"Plan {name} with my data",
        description=(
            "Finds matching input files and shows a preview with the command; "
            "nothing runs until you approve it."
        ),
        answer=f"Start planning {name}",
        action=action,
        resolution="plan_workflow",
    )


def _confirm(policy, action: str, label: str) -> ReplyOption:
    name = workflow_name(policy, action)
    return ReplyOption(
        key=f"confirm-{action}",
        label=label.format(name=name),
        description="Explains that workflow for this goal and what it needs; runs nothing.",
        answer=label.format(name=name),
        action=action,
        resolution="confirm_workflow",
    )


def next_steps(prompt: NextTurnPrompt, policy, *, outputs: list[str], has_choices: bool) -> list[ReplyOption]:
    steps: list[ReplyOption] = []
    kind = prompt.kind
    if kind == "dry_run":
        steps.append(_execute())
    elif kind == "recommended_workflow" and prompt.continuation_action in policy.workflows:
        steps.append(plan_step(policy, prompt.continuation_action))
    elif kind == "alternative_outcome" and prompt.alternative_action in policy.workflows:
        steps.append(_confirm(policy, prompt.alternative_action, "Yes, use {name}"))
    elif kind == "failed":
        steps.append(ReplyOption(
            key="doctor",
            label="Check the environment",
            description="Checks the container, NetZoo installation and paths; runs no analysis.",
            answer="/doctor",
            resolution="command",
        ))
    elif kind == "unsupported":
        steps.append(ReplyOption(
            key="capabilities",
            label="Show what NetZoo can do here",
            description="Lists the registered workflows and what each produces.",
            answer="Which analyses can the registered NetZoo workflows run, and what does each produce?",
            resolution="follow_up",
        ))
    if outputs:
        steps.insert(0, ReplyOption(
            key="outputs",
            label="Open the outputs",
            description=f"{len(outputs)} file{'s' if len(outputs) != 1 else ''} from this run.",
            answer="",
            resolution="open_outputs",
            paths=outputs[:20],
        ))
    if kind != "initial" and (steps or has_choices or kind in {"completed", "clarify_outcome", "retrieval"}):
        steps.append(NEW_TASK)
    return steps

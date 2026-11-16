"""The adapter: a stream of envelopes becomes one answer.

A worker reports a turn as a sequence -- notices, progress lines, the reply,
usage, and finally the next question. A window draws each as it arrives. An
MCP client makes one call and reads one result, so this collects the sequence
until the worker asks for input again.

Nothing here talks to a worker or a client. ``TurnCollector`` is fed envelopes
and asked for a ``TurnResult``, which keeps the rules below testable from
fixed sequences:

* The turn ends at a ``view`` (the machine wants input) or at ``stopped``.
  ``turn_finished`` does not end it: the machine can run several turns in a
  row before it has a question.
* A ``running`` result hands over what has been collected so far and forgets
  it, so the result that follows carries only what came after. Every message
  a worker sends is therefore delivered exactly once.
* ``trace`` events are not collected. They are the reasoning timeline, which
  the desktop window shows for the same session.
"""

from __future__ import annotations

from .contracts import (
    ErrorView,
    EvidenceView,
    OptionView,
    OutputRef,
    PlanSummary,
    StepView,
    TurnResult,
)

__all__ = ["PROGRESS_LIMIT", "TurnCollector", "view_fields"]

PROGRESS_LIMIT = 20

# The worker refused the action but kept its question open; the supervisor
# publishes that question again right after, and that view ends the turn.
_RETRYABLE_ERRORS = frozenset(
    {
        "InvalidMessage",
        "UnexpectedMessage",
        "ExecutionApprovalRequired",
        "NoPreviewedPlan",
        "StalePlanHash",
    }
)
# Refused before it reached the worker. No question is guaranteed to follow,
# so the collection ends here rather than wait for one.
_REFUSED_ERRORS = frozenset({"StalePromptSeq"})

_MODE_COMMANDS = frozenset({"/test", "/planning"})


def _via(option: dict) -> str:
    if not option.get("available", True) or option.get("resolution") == "none":
        return "none"
    if option.get("resolution") == "open_outputs":
        return "netzoo_list_outputs"
    answer = str(option.get("answer") or "").strip().casefold()
    if answer == "/execute":
        return "netzoo_execute"
    if answer in _MODE_COMMANDS:
        return "netzoo_set_mode"
    return "netzoo_ask"


def _option(option: dict) -> OptionView:
    return OptionView(
        label=str(option.get("label") or ""),
        description=str(option.get("description") or ""),
        answer=str(option.get("answer") or ""),
        recommended=bool(option.get("recommended")),
        available=bool(option.get("available", True)),
        reason=str(option.get("reason") or ""),
        via=_via(option),
        paths=[str(path) for path in option.get("paths") or []],
    )


def _card_options(card: dict | None) -> list[OptionView]:
    if not card:
        return []
    choices = card.get("choices") or {}
    rows = [
        *(choices.get("options") or []),
        *(card.get("next_steps") or []),
        *(card.get("unavailable") or []),
    ]
    return [_option(row) for row in rows if isinstance(row, dict)]


def _plan_summary(plan: dict | None) -> PlanSummary | None:
    if not plan:
        return None
    return PlanSummary(
        workflow=str(plan.get("workflow") or ""),
        objective=str(plan.get("objective") or ""),
        status=str(plan.get("status") or ""),
        question=plan.get("question"),
        missing_inputs=[str(item) for item in plan.get("missing_inputs") or []],
        evidence=[
            EvidenceView(
                field=str(row.get("field") or ""),
                status=str(row.get("status") or ""),
                value=row.get("value"),
                reason=str(row.get("reason") or ""),
            )
            for row in plan.get("evidence") or []
        ],
        steps=[
            StepView(
                action=str(row.get("action") or ""),
                purpose=str(row.get("purpose") or ""),
                arguments=dict(row.get("arguments") or {}),
            )
            for row in plan.get("steps") or []
        ],
        input_bundles=[dict(row) for row in plan.get("input_bundle_options") or []],
    )


def _previewed(view: dict) -> bool:
    """Whether ``/execute`` would be accepted here: the machine's own condition."""
    next_prompt = view.get("next_prompt") or {}
    return (
        view.get("prompt_kind") == "main"
        and next_prompt.get("kind") == "dry_run"
        and bool(view.get("plan_hash"))
    )


def view_fields(view: dict | None, *, execute_enabled: bool, to_host=None) -> dict:
    """The ``TurnResult`` fields that describe the open question."""
    if not view:
        return {"execute_enabled": execute_enabled}
    options = _card_options(view.get("card"))
    paths: list[str] = []
    for option in options:
        if option.via == "netzoo_list_outputs":
            paths.extend(path for path in option.paths if path not in paths)
    return {
        "mode": view.get("mode") or "",
        "prompt_kind": view.get("prompt_kind"),
        "question": view.get("text"),
        "target_field": view.get("target_field"),
        "choosing_bundle": bool(view.get("choosing_bundle")),
        "preflight_correction": bool(view.get("preflight_correction")),
        "options": options,
        "plan": _plan_summary(view.get("plan")),
        "plan_hash": view.get("plan_hash"),
        "previewed": _previewed(view),
        "can_execute": execute_enabled and _previewed(view),
        "execute_enabled": execute_enabled,
        "outputs": [
            OutputRef(path=path, host_path=to_host(path) if to_host else path)
            for path in paths
        ],
    }


class TurnCollector:
    """Collect one turn's envelopes; hand them over as results."""

    def __init__(self, session_id: str, *, execute_enabled: bool = False, to_host=None, mode: str = ""):
        self.session_id = session_id
        self.done = False
        self._execute_enabled = execute_enabled
        self._to_host = to_host
        self._mode = mode
        self._status = "running"
        self._messages: list[str] = []
        self._notices: list[str] = []
        self._progress: list[str] = []
        self._errors: list[ErrorView] = []
        self._usage: dict | None = None
        self._view: dict | None = None

    @property
    def view(self) -> dict | None:
        """The question that ended the turn, once it has ended at one."""
        return self._view

    def carry(self, *, messages=(), notices=()) -> None:
        """Start with text an earlier step collected but did not return."""
        self._messages[:0] = list(messages)
        self._notices[:0] = list(notices)

    def feed(self, envelope) -> bool:
        """Take one envelope. True once the turn has ended."""
        if self.done:
            raise RuntimeError("this turn has already ended")
        kind, payload = envelope.type, envelope.payload
        text = str(payload.get("text") or "")
        if kind == "message":
            if text:
                self._messages.append(text)
        elif kind == "notice":
            if text.strip():
                self._notices.append(text)
        elif kind == "progress":
            if text.strip():
                self._progress.append(text)
                del self._progress[:-PROGRESS_LIMIT]
        elif kind == "usage":
            # The per-call list grows with every model call; the totals are what a reader needs.
            self._usage = {key: value for key, value in payload.items() if key != "calls"}
        elif kind == "error":
            error_type = str(payload.get("error_type") or "Error")
            self._errors.append(
                ErrorView(error_type=error_type, message=str(payload.get("message") or ""))
            )
            if error_type in _REFUSED_ERRORS:
                self._finish("error")
            elif error_type not in _RETRYABLE_ERRORS:
                # A failure of the worker itself. ``stopped`` normally follows,
                # and it keeps this status.
                self._status = "error"
        elif kind == "view":
            self._view = dict(payload)
            self._mode = str(payload.get("mode") or self._mode)
            self._finish("waiting_for_user")
        elif kind == "stopped":
            self._finish("error" if self._status == "error" else "stopped")
        # ready, turn_started, turn_finished, trace, pong: nothing to collect.
        return self.done

    def close(self) -> None:
        """The session went away before the turn ended."""
        if not self.done:
            self._finish("error" if self._status == "error" else "stopped")

    def _finish(self, status: str) -> None:
        self._status = status
        self.done = True

    def result(self) -> TurnResult:
        """What has been collected since the last result; it is not returned twice."""
        fields = view_fields(
            self._view if self.done else None,
            execute_enabled=self._execute_enabled,
            to_host=self._to_host,
        )
        fields.setdefault("mode", self._mode)
        result = TurnResult(
            session_id=self.session_id,
            status=self._status if self.done else "running",
            reply="\n\n".join(self._messages),
            notices=list(self._notices),
            progress=list(self._progress),
            usage=self._usage,
            errors=list(self._errors),
            **fields,
        )
        self._messages.clear()
        self._notices.clear()
        self._progress.clear()
        self._errors.clear()
        return result

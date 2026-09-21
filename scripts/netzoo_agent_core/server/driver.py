"""The second driver for the conversation engine.

Where ``cli.conversation`` gives the machine a terminal, this gives it a
socket.  The transitions are the machine's; this module only decides how a
question is published and how an answer is accepted.

Execution is the one place the two drivers differ, and deliberately so.  The
terminal asks ``[y/N]`` and trusts whatever the user types next.  A UI client
is several seconds and one network hop away from the plan it is looking at, so
it must name the plan it means: ``approve_execution`` carries the hash of the
plan shown on screen, and a stale hash is refused rather than run.  Both
drivers still require the same two separate acts — request a preview, then
approve it.
"""

from __future__ import annotations

from ..cli.slash_commands import current_mode_label
from ..engine import ConversationMachine, Event, Stop, Turn
from .channel import Channel, ClosedChannel
from .protocol import ClientMessage, Envelope, plan_hash

__all__ = ["ProgressWriter", "WorkerDriver"]

_EVENT_TYPES = {"notice": "notice", "message": "message", "blank": "notice"}


class ProgressWriter:
    """Turn the presentation layer's direct prints into progress envelopes.

    ``_trace`` and ``_clear_transient_trace`` write to stdout because a
    terminal is their native output.  Rather than reorder them through the
    event stream, a worker redirects stdout into this.

    Installing it is the *process's* job, not the driver's: ``sys.stdout`` is
    process-wide, so a driver that redirected it would also silence anything
    else running in the same interpreter.
    """

    def __init__(self, emit):
        self._emit = emit
        self._buffer = ""

    def write(self, text: str) -> int:
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self._emit(line)
        return len(text)

    def flush(self) -> None:
        if self._buffer.strip():
            self._emit(self._buffer)
        self._buffer = ""

    def isatty(self) -> bool:
        return False


class WorkerDriver:
    """Drive one ``ConversationMachine`` over a channel until it stops."""

    def __init__(
        self,
        machine: ConversationMachine,
        channel: Channel,
        *,
        session_id: str,
        progress: ProgressWriter | None = None,
    ):
        self.machine = machine
        self.channel = channel
        self.session_id = session_id
        self.progress = progress

    # -- outbound ----------------------------------------------------------

    def _send(self, message_type: str, payload: dict | None = None) -> None:
        self.channel.send(
            Envelope(
                type=message_type,
                session_id=self.session_id,
                payload=payload or {},
            )
        )

    def _emit_events(self, events: list[Event]) -> None:
        for event in events:
            self._send(_EVENT_TYPES[event.kind], {"text": event.text})

    def _current_plan(self, prompt):
        if prompt.plan is not None:
            return prompt.plan
        preview = self.machine.state.preview
        return preview.plan if preview is not None else None

    def _send_view(self, prompt) -> None:
        plan = self._current_plan(prompt)
        self._send(
            "view",
            {
                "prompt_kind": prompt.kind,
                "text": prompt.text,
                "menu_enabled": prompt.menu_enabled,
                "mode": current_mode_label(),
                "plan": plan.model_dump(mode="json") if plan is not None else None,
                "plan_hash": plan_hash(plan),
                "next_prompt": (
                    prompt.next_prompt.model_dump(mode="json")
                    if prompt.next_prompt is not None
                    else None
                ),
            },
        )

    # -- inbound -----------------------------------------------------------

    def _read_answer(self, prompt) -> str | None:
        """Block until a client sends something that answers this prompt."""
        while True:
            envelope = self.channel.receive()
            if envelope is None:
                continue
            try:
                message = ClientMessage.from_envelope(envelope)
            except Exception as error:
                self._send(
                    "error",
                    {"error_type": "InvalidMessage", "message": str(error)},
                )
                continue
            if message.type == "cancel":
                self.machine.stop(0)
                return None
            if prompt.kind == "execution_confirmation":
                answer = self._answer_execution_prompt(message)
            else:
                answer = self._answer_ordinary_prompt(message)
            if answer is not None:
                return answer

    def _answer_ordinary_prompt(self, message: ClientMessage) -> str | None:
        if message.type == "answer":
            return message.text
        self._send(
            "error",
            {
                "error_type": "UnexpectedMessage",
                "message": (
                    f"'{message.type}' is only valid at an execution confirmation "
                    "prompt."
                ),
            },
        )
        return None

    def _answer_execution_prompt(self, message: ClientMessage) -> str | None:
        if message.type == "decline_execution":
            return "n"
        if message.type != "approve_execution":
            self._send(
                "error",
                {
                    "error_type": "ExecutionApprovalRequired",
                    "message": (
                        "This prompt only accepts approve_execution or "
                        "decline_execution."
                    ),
                },
            )
            return None
        preview = self.machine.state.preview
        expected = plan_hash(preview.plan) if preview is not None else None
        if expected is None:
            self._send(
                "error",
                {
                    "error_type": "NoPreviewedPlan",
                    "message": "There is no previewed plan to approve.",
                },
            )
            return None
        if message.plan_hash != expected:
            self._send(
                "error",
                {
                    "error_type": "StalePlanHash",
                    "message": (
                        "The approved plan is not the plan this session is "
                        "holding. Re-read the current plan and approve again."
                    ),
                    "expected_plan_hash": expected,
                },
            )
            return None
        return "y"

    # -- loop --------------------------------------------------------------

    def _flush_progress(self) -> None:
        if self.progress is not None:
            self.progress.flush()

    def run(self) -> int:
        try:
            return self._loop()
        except ClosedChannel:
            return 0

    def _loop(self) -> int:
        opening = self.machine.opening_notice()
        self._send("ready", {"session_id": self.session_id})
        if opening is not None:
            self._emit_events([opening])
        while True:
            action = self.machine.next_action()
            if isinstance(action, Stop):
                self._flush_progress()
                self._send("stopped", {"exit_code": action.exit_code})
                return action.exit_code
            if isinstance(action, Turn):
                self._send(
                    "turn_started",
                    {"task": action.task, "execute_once": action.execute_once},
                )
                events = self.machine.run_turn()
                self._flush_progress()
                self._emit_events(events)
                self._send_usage()
                self._send("turn_finished", {})
                continue
            self._flush_progress()
            self._send_view(action)
            answer = self._read_answer(action)
            if answer is None:
                continue
            self._emit_events(self.machine.submit(answer))

    def _send_usage(self) -> None:
        usage = self.machine.state.active_usage
        if usage:
            self._send("usage", dict(usage))

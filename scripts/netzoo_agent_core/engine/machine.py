"""Driver-independent conversation state machine.

This is ``cli.conversation.run_conversation`` with the terminal taken out of
it.  The transitions, the order of every message, and the exact prompt strings
are unchanged; what moved is the reading of input and the printing of output,
which now belong to whichever driver is attached.

The machine is used as::

    machine = ConversationMachine(args, runtime)
    while True:
        action = machine.next_action()
        if isinstance(action, Stop):
            return action.exit_code
        if isinstance(action, Turn):
            render(machine.run_turn())
            continue
        answer = read(action)                    # driver's business
        render(machine.submit(answer))

``_trace`` and ``_clear_transient_trace`` are still called directly rather than
returned as events.  They are progress rendering owned by the presentation
layer, and routing them through the event stream would reorder terminal output.
A non-terminal driver redirects them instead.
"""

from __future__ import annotations

from workflow_registry import RUN_ACTIONS

from .. import settings
from ..contracts.interaction import MethodComparison, WorkflowContinuation
from ..contracts.planning import WorkflowPlan
from ..contracts.state import (
    AgentTurnInterrupted,
    ClarificationInputError,
    LLMUsage,
    NextTurnPrompt,
)
from ..framework_compat import HumanMessage
from ..planning_audit import write_planning_audit
from ..presentation import _clear_transient_trace, _trace, _ui_text
from ..session import (
    _is_auto_session_id,
    compact_conversation,
    delete_session,
    save_session,
)
from ..session_outputs import session_output_scope
from ..settings import INPUT_ROLE_FIELDS, OUTPUT_ROLE_FIELDS, ROUTER_CONTEXT_MAX_CHARS
from ..cli.clarification import (
    bundle_clarification_continuation,
    clarification_continuation,
    clarification_prompt,
    custom_clarification_prompt,
    input_confirmation_continuation,
    input_confirmation_prompt,
    parse_clarification_assignments,
    preference_confirmation_prompt,
    preference_continuation,
    resolve_clarification,
)
from ..cli.follow_up import (
    build_follow_up_context,
    build_next_turn_prompt,
    build_workflow_continuation,
    follow_up_returns_to_main,
    initial_next_turn_prompt,
    render_next_turn_prompt,
    resolve_next_turn_input,
)
from ..cli.slash_commands import handle_slash_command, render_mode_prompt
from .choices import (
    accepted,
    chosen_option,
    confirmed_outcome_task,
    follow_up_task,
    trusted_actions,
)
from .state import ConversationState, PreviewState
from .view import Event, Prompt, Stop, Turn

__all__ = ["ConversationMachine"]

_PATH_ANSWER_FIELDS = INPUT_ROLE_FIELDS | OUTPUT_ROLE_FIELDS
_EXIT_WORDS = {"exit", "quit", "q", "離開", "結束"}


def _notice(text: str) -> Event:
    return Event("notice", _ui_text(text))


class ConversationMachine:
    """One interactive conversation, independent of how it is presented."""

    def __init__(self, args, runtime, *, initial_prompt_factory=None):
        self.args = args
        self.runtime = runtime
        # The CLI adapter passes its own module-level ``initial_next_turn_prompt``
        # so that patching it on the adapter keeps working.
        self._initial_prompt_factory = (
            initial_prompt_factory or initial_next_turn_prompt
        )
        self.state = ConversationState(
            session_id=runtime.session_id,
            conversation=runtime.conversation,
            pending_plan=runtime.pending_plan,
            active_usage=runtime.active_usage,
            run_id=runtime.run_id,
            next_prompt=self._initial_prompt_factory(),
            one_shot=bool(args.task) and not runtime.resume_id,
            queued_task=args.task,
        )
        self._stopped = False
        self._exit_code = 0
        self._awaiting: Prompt | None = None

    # -- lifecycle ---------------------------------------------------------

    def opening_notice(self) -> Event | None:
        """The banner the CLI prints before the first prompt."""
        if self.args.task:
            return None
        return _notice(
            "NetZoo agent started in Planning mode. "
            "Enter /help for controls, or exit or quit to stop."
        )

    def stop(self, exit_code: int = 0) -> None:
        self._stopped = True
        self._exit_code = exit_code

    def next_action(self) -> Prompt | Turn | Stop:
        """Decide whether to ask something, run a turn, or finish."""
        while True:
            if self._stopped:
                return Stop(self._exit_code)
            state = self.state
            if state.pending_task is not None:
                self._awaiting = None
                return Turn(
                    task=state.pending_task,
                    execute_once=state.pending_execute_once,
                )
            if state.execution_confirmation_task is not None:
                return self._remember(self._execution_confirmation_prompt())
            if state.queued_task is not None:
                task = state.queued_task.strip()
                state.queued_task = None
                self._accept_task(task)
                continue
            if state.pending_plan is not None:
                return self._remember(self._pending_plan_prompt())
            if state.one_shot:
                self.stop(0)
                continue
            return self._remember(self._main_prompt())

    def _remember(self, prompt: Prompt) -> Prompt:
        self._awaiting = prompt
        return prompt

    # -- prompt construction ----------------------------------------------

    def _execution_confirmation_prompt(self) -> Prompt:
        workflow = self.state.preview.workflow if self.state.preview else None
        return Prompt(
            kind="execution_confirmation",
            text=render_mode_prompt(
                "\nRun the validated "
                f"{workflow or 'NetZoo'} workflow now? [y/N] "
            ),
            menu_enabled=False,
        )

    def _pending_plan_prompt(self) -> Prompt:
        state = self.state
        plan = state.pending_plan
        if plan.status == "needs_confirmation":
            if not plan.preference_proposals:
                body = input_confirmation_prompt(
                    plan,
                    correction=state.input_confirmation_correction,
                )
                kind = "input_confirmation"
            else:
                body = preference_confirmation_prompt(plan)
                kind = "preference_confirmation"
            noninteractive = "\n" + (
                input_confirmation_prompt(
                    plan,
                    correction=state.input_confirmation_correction,
                )
                if not plan.preference_proposals
                else preference_confirmation_prompt(plan)
            )
        else:
            body = (
                custom_clarification_prompt(plan, state.clarification_selections)
                if state.custom_input_selection
                else clarification_prompt(plan, state.clarification_selections)
            )
            kind = "clarification"
            noninteractive = "\n" + clarification_prompt(plan)
        preflight_correction, choosing_bundle, target_field = (
            self._clarification_context()
            if kind == "clarification"
            else (False, False, None)
        )
        return Prompt(
            kind=kind,
            text=render_mode_prompt("\n" + body),
            menu_enabled=False,
            plan=plan,
            noninteractive_text=noninteractive,
            target_field=target_field,
            choosing_bundle=choosing_bundle,
            preflight_correction=preflight_correction,
        )

    def _main_prompt(self) -> Prompt:
        next_prompt = self.state.next_prompt
        return Prompt(
            kind="main",
            text=f"\n{render_mode_prompt(render_next_turn_prompt(next_prompt))}\n> ",
            # Keep the prompt-toolkit adapter for ordinary tasks so a
            # bracketed multi-line paste stays one submission. Path
            # prompts remain plain input to avoid slash/path ambiguity.
            menu_enabled=next_prompt.expected_field not in _PATH_ANSWER_FIELDS,
            next_prompt=next_prompt,
            card=self.state.reply_card if next_prompt.kind != "initial" else None,
        )

    # -- answer handling ---------------------------------------------------

    def submit(self, raw_answer: str) -> list[Event]:
        prompt = self._awaiting
        if prompt is None:
            raise RuntimeError("submit() called without a pending prompt")
        answer = raw_answer.strip()
        if prompt.kind == "execution_confirmation":
            return self._submit_execution_confirmation(answer)
        if prompt.kind == "input_confirmation":
            return self._submit_input_confirmation(answer)
        if prompt.kind == "preference_confirmation":
            return self._submit_preference_confirmation(answer)
        if prompt.kind == "clarification":
            return self._submit_clarification(answer)
        return self._submit_main(answer)

    def _interactive_control(self, answer: str, **options) -> list[Event] | None:
        result = handle_slash_command(answer, **options)
        if not result.handled:
            return None
        return [_notice(result.message)]

    def _submit_execution_confirmation(self, answer: str) -> list[Event]:
        state = self.state
        if (events := self._interactive_control(answer)) is not None:
            return events
        if answer.casefold() in _EXIT_WORDS:
            self.stop(0)
            return []
        if answer.casefold() not in {"y", "yes"}:
            state.execution_confirmation_task = None
            return [_notice("Execution cancelled; the command preview is unchanged.")]
        task = state.execution_confirmation_task
        state.execution_confirmation_task = None
        state.pending_execute_once = True
        if state.preview is not None:
            action = state.preview.plan.decision["action"]
            if action in RUN_ACTIONS:
                state.pending_continuation = WorkflowContinuation(
                    action=action, task=task[-ROUTER_CONTEXT_MAX_CHARS:]
                )
        return self._accept_task(task)

    def _submit_input_confirmation(self, answer: str) -> list[Event]:
        state = self.state
        plan = state.pending_plan
        if (
            events := self._interactive_control(
                answer,
                current_plan=plan,
                execution_block_reason=(
                    "This workflow still requires input confirmation. "
                    "Confirm the displayed files or provide corrected paths."
                ),
            )
        ) is not None:
            return events
        if answer.casefold() in _EXIT_WORDS:
            self.stop(0)
            return []
        if not state.input_confirmation_correction:
            if answer.casefold() in {"y", "yes"}:
                task = input_confirmation_continuation(plan, answer, approved=True)
            elif answer.casefold() in {"n", "no", ""}:
                state.input_confirmation_correction = True
                return [
                    Event(
                        "notice",
                        "\n" + input_confirmation_prompt(plan, correction=True),
                    )
                ]
            else:
                try:
                    task = input_confirmation_continuation(plan, answer, approved=False)
                except ClarificationInputError as error:
                    state.input_confirmation_correction = True
                    return [
                        Event(
                            "notice",
                            "\n" + _ui_text("Input not accepted: ") + str(error),
                        )
                    ]
            state.input_confirmation_correction = False
        else:
            try:
                task = input_confirmation_continuation(plan, answer, approved=False)
            except ClarificationInputError as error:
                return [
                    Event(
                        "notice",
                        "\n" + _ui_text("Input not accepted: ") + str(error),
                    )
                ]
            state.input_confirmation_correction = False
        return self._accept_task(task)

    def _submit_preference_confirmation(self, answer: str) -> list[Event]:
        state = self.state
        plan = state.pending_plan
        if (events := self._interactive_control(answer)) is not None:
            return events
        if answer.casefold() in _EXIT_WORDS:
            self.stop(0)
            return []
        approved = answer.casefold() in {"y", "yes"}
        events: list[Event] = []
        if approved:
            profile_id = self.runtime.memory.profile_id
            self.runtime.memory.profile_store.confirm(
                profile_id,
                plan.preference_proposals,
            )
            events.append(
                Event(
                    "notice",
                    _ui_text("Saved confirmed preferences to profile ")
                    + f"'{profile_id}'.",
                )
            )
        else:
            events.append(_notice("Preference changes were not saved."))
        task = preference_continuation(plan, approved)
        return events + self._accept_task(task)

    def _clarification_context(self) -> tuple[bool, bool, str | None]:
        state = self.state
        plan = state.pending_plan
        preflight_correction = (
            plan.status == "needs_input" and not plan.missing_inputs
        )
        choosing_complete_bundle = bool(
            plan.input_bundle_options
        ) and not state.custom_input_selection
        unresolved_fields = [
            item.field
            for item in plan.evidence
            if item.status == "missing"
            and item.field not in state.clarification_selections
        ]
        target_field = unresolved_fields[0] if unresolved_fields else None
        return preflight_correction, choosing_complete_bundle, target_field

    def _submit_clarification(self, answer: str) -> list[Event]:
        state = self.state
        plan = state.pending_plan
        (
            preflight_correction,
            choosing_complete_bundle,
            target_field,
        ) = self._clarification_context()
        missing_labels = ", ".join(plan.missing_inputs)
        if (
            events := self._interactive_control(
                answer,
                current_plan=plan,
                allow_path_answer=(
                    preflight_correction
                    or (
                        not choosing_complete_bundle
                        and target_field in _PATH_ANSWER_FIELDS
                    )
                ),
                execution_block_reason=(
                    "Input preflight failed. Provide corrected input paths "
                    "as field=path assignments."
                    if preflight_correction
                    else (
                        "This workflow plan is not ready to execute. It still needs: "
                        f"{missing_labels}. Continue the input wizard or provide the "
                        "required paths."
                    )
                ),
            )
        ) is not None:
            return events
        if answer.casefold() in _EXIT_WORDS:
            self.stop(0)
            return []
        if not answer:
            return []
        try:
            if preflight_correction:
                task = input_confirmation_continuation(plan, answer, approved=False)
            elif choosing_complete_bundle:
                if answer.casefold() == "custom":
                    state.custom_input_selection = True
                    state.clarification_selections = {}
                    return []
                task = bundle_clarification_continuation(plan, answer)
                state.custom_input_selection = False
                state.clarification_selections = {}
            elif "lioness_mode" in plan.missing_inputs:
                task = resolve_clarification(plan, answer)
            else:
                state.clarification_selections = parse_clarification_assignments(
                    plan,
                    answer,
                    selected=state.clarification_selections,
                    target_field=target_field,
                )
                still_missing = [
                    field_name
                    for field_name in plan.missing_inputs
                    if field_name not in state.clarification_selections
                ]
                if still_missing:
                    return []
                task = clarification_continuation(plan, state.clarification_selections)
                state.clarification_selections = {}
        except ClarificationInputError as error:
            return [
                Event(
                    "notice",
                    "\n" + _ui_text("Selection not accepted: ") + str(error),
                )
            ]
        return self._accept_task(task)

    def _submit_main(self, answer: str) -> list[Event]:
        # An answer that picks one of the last reply's options resolves
        # without the reply classifier; anything else is handled as before.
        if (option := chosen_option(self.state.reply_card, answer)) is not None:
            return self._submit_option(option)
        return self._submit_main_text(answer)

    def _submit_option(self, option: dict) -> list[Event]:
        state = self.state
        resolution = option.get("resolution")
        if resolution == "command":
            return self._submit_main_text(option["answer"])
        if resolution == "open_outputs":
            paths = option.get("paths") or []
            return [Event("notice", _ui_text("Outputs from this run:") + "\n"
                          + "\n".join(f"  {path}" for path in paths))]
        action = option.get("action")
        if resolution in {"confirm_workflow", "plan_workflow"}:
            if action not in trusted_actions(state.reply_card, state.next_prompt, state.follow_up_context):
                return [_notice("That option no longer matches this conversation. Describe what you want instead.")]
        if resolution == "confirm_workflow":
            task = confirmed_outcome_task(action, option.get("granularity"))
            state.reply_card = None
            return self._accept_task(task)
        if resolution == "plan_workflow":
            decision = accepted(action)
            task = resolve_next_turn_input(state.next_prompt, decision, option["answer"])
            if not task:
                return [_notice("That option no longer matches this conversation. Describe what you want instead.")]
            state.pending_continuation = build_workflow_continuation(
                state.next_prompt, state.follow_up_context, decision, task
            )
            state.reply_card = None
            return self._accept_task(task)
        task = follow_up_task(state.follow_up_context, option["answer"])
        if resolution == "compare_workflows":
            # The answer text is what the transcript shows; which workflows are
            # compared travels as typed state (Log 302). An invalid list is an
            # ordinary follow-up, as before.
            try:
                state.pending_comparison = MethodComparison(
                    actions=list(option.get("compare_actions") or []),
                    task=task[-ROUTER_CONTEXT_MAX_CHARS:],
                )
            except ValueError:
                state.pending_comparison = None
        state.reply_card = None
        return self._accept_task(task)

    def _submit_main_text(self, answer: str) -> list[Event]:
        state = self.state
        next_prompt = state.next_prompt
        if (
            answer.casefold() == "/execute"
            and next_prompt.kind == "dry_run"
            and state.preview is not None
        ):
            command_result = handle_slash_command(
                answer,
                current_plan=state.preview.plan,
                current_plan_evaluation=state.preview.plan_evaluation,
            )
            if command_result.execute_once:
                state.execution_confirmation_task = state.preview.task
            return [_notice(command_result.message)]
        if (
            events := self._interactive_control(
                answer,
                allow_path_answer=next_prompt.expected_field in _PATH_ANSWER_FIELDS,
            )
        ) is not None:
            return events
        if follow_up_returns_to_main(next_prompt, answer):
            state.next_prompt = self._initial_prompt_factory()
            state.follow_up_context = None
            state.reply_card = None
            return []
        if not answer:
            return []
        if answer.casefold() in _EXIT_WORDS:
            self.stop(0)
            return []
        if next_prompt.kind != "initial" and state.follow_up_context is not None:
            return self._resolve_follow_up(answer)
        return self._accept_task(answer)

    def _resolve_follow_up(self, answer: str) -> list[Event]:
        state = self.state
        if state.run_id is None:
            state.run_id = str(
                self.runtime.recorder.start_run(
                    session_id=state.session_id,
                    profile_id=self.runtime.memory.profile_id,
                )
            )
            self.runtime.ensure_trace_sync(state.run_id)
        reply_result = self.runtime.reply_resolver.resolve(
            state.follow_up_context,
            answer,
            state.active_usage,
            state.run_id,
        )
        state.active_usage = reply_result.usage.model_dump()
        resolution = reply_result.resolution
        if resolution.kind == "needs_detail":
            retry_question = _ui_text(
                "Please enter a concrete follow-up question, provide the "
                "requested input path, or describe another NetZoo goal."
            )
            state.next_prompt = state.next_prompt.model_copy(
                update={"question": retry_question}
            )
            state.follow_up_context = state.follow_up_context.model_copy(
                update={
                    "prompt_kind": state.next_prompt.kind,
                    "prompt_question": retry_question,
                }
            )
            self._finish_interaction_run("needs_detail")
            return []
        if resolution.kind == "navigation":
            self._finish_interaction_run("navigation")
            state.next_prompt = self._initial_prompt_factory()
            state.follow_up_context = None
            state.reply_card = None
            return []
        task = resolve_next_turn_input(state.next_prompt, resolution, answer)
        if not task:
            self._finish_interaction_run("needs_detail")
            return [
                _notice(
                    "Please enter a concrete follow-up question, provide the "
                    "requested input path, or describe another NetZoo goal."
                )
            ]
        state.pending_continuation = build_workflow_continuation(
            state.next_prompt, state.follow_up_context, resolution, task
        )
        return self._accept_task(task)

    def _finish_interaction_run(self, interaction_status: str) -> None:
        state = self.state
        self.runtime.recorder.finish_run(
            state.run_id,
            "completed",
            {
                "interaction_status": interaction_status,
                "token_usage": state.active_usage,
            },
        )
        state.run_id = None
        state.active_usage = None

    def _accept_task(self, task: str) -> list[Event]:
        """The shared tail every input branch runs before a turn starts."""
        state = self.state
        if task.casefold() in _EXIT_WORDS:
            self.stop(0)
            return []
        if not task:
            return []
        if state.pending_plan is not None:
            action = state.pending_plan.decision["action"]
            if action in RUN_ACTIONS:
                state.pending_continuation = WorkflowContinuation(
                    action=action, task=task[-ROUTER_CONTEXT_MAX_CHARS:]
                )
        state.pending_task = task
        return []

    # -- the turn ----------------------------------------------------------

    def run_turn(self) -> list[Event]:
        state = self.state
        task = state.pending_task
        execute_once = state.pending_execute_once
        workflow_continuation = state.pending_continuation
        method_comparison = state.pending_comparison
        state.clear_pending_turn()

        if state.run_id is None:
            state.run_id = str(
                self.runtime.recorder.start_run(
                    session_id=state.session_id,
                    profile_id=self.runtime.memory.profile_id,
                )
            )
            self.runtime.ensure_trace_sync(state.run_id)
        elif state.run_paused:
            self.runtime.recorder.append(
                state.run_id,
                "run.resumed",
                "cli",
                {"session_id": state.session_id},
            )
            state.run_paused = False
        try:
            if execute_once:
                # Execution authority is scoped to this single graph turn. The
                # next prompt always returns to Planning mode.
                from ..runtime import configure_runtime

                configure_runtime(EXECUTE_TOOLS=True)
            invocation = {
                "messages": [*state.conversation, HumanMessage(content=task)],
                "session_id": state.session_id,
                "run_id": state.run_id,
                "workflow_continuation": (
                    workflow_continuation.model_dump()
                    if workflow_continuation
                    else None
                ),
                "method_comparison": (
                    method_comparison.model_dump() if method_comparison else None
                ),
            }
            if state.active_usage is not None:
                invocation["token_usage"] = state.active_usage
            # Outputs without an explicit path go to this session's own folder.
            with session_output_scope(state.session_id):
                result = self.runtime.invoke_graph_turn_func(self.runtime.app, invocation)
        except AgentTurnInterrupted:
            return self._turn_interrupted(task)
        except Exception as error:
            return self._turn_failed(task, error)
        finally:
            if execute_once:
                from ..runtime import configure_runtime

                configure_runtime(EXECUTE_TOOLS=False)
        return self._turn_finished(task, result, execute_once)

    def _turn_interrupted(self, task: str) -> list[Event]:
        state = self.state
        self.runtime.recorder.append(
            state.run_id,
            "run.interrupted",
            "cli",
            {"reason": "keyboard_interrupt"},
        )
        self._write_planning_audit_if_needed(state.run_id, task)
        _clear_transient_trace()
        self.stop(130)
        return [
            Event("blank"),
            _notice(
                "The current request was interrupted. No unfinished local "
                "analysis command will be reported as completed."
            ),
        ]

    def _turn_failed(self, task: str, error: Exception) -> list[Event]:
        state = self.state
        self.runtime.recorder.append(
            state.run_id,
            "error.recorded",
            "cli",
            {"error_type": type(error).__name__, "message": str(error)},
        )
        self._write_planning_audit_if_needed(state.run_id, task)
        _clear_transient_trace()
        events = [
            _notice(
                "The agent could not finish this request. No unfinished provider "
                "or local-tool step will be reported as completed."
            ),
            Event("notice", _ui_text("Error type: ") + type(error).__name__),
        ]
        state.reply_card = None
        if state.one_shot:
            self.stop(1)
            return events
        state.next_prompt = NextTurnPrompt(
            kind="failed",
            question=_ui_text(
                "Would you like to retry with a clearer request, describe a "
                "different NetZoo goal, or enter exit?"
            ),
        )
        return events

    def _turn_finished(self, task: str, result: dict, execute_once: bool) -> list[Event]:
        state = self.state
        events: list[Event] = []
        state.conversation = compact_conversation(result["messages"])
        state.active_usage = result.get("token_usage")
        save_session(
            state.session_id,
            state.conversation,
            result,
            profile_id=self.runtime.memory.profile_id,
        )
        plan = WorkflowPlan.model_validate(result["plan"])
        state.pending_plan = (
            plan if plan.status in {"needs_input", "needs_confirmation"} else None
        )
        state.clarification_selections = {}
        state.custom_input_selection = False
        state.input_confirmation_correction = False
        if state.active_usage:
            usage = LLMUsage.model_validate(state.active_usage)
            _trace(
                "done",
                (
                    f"LLM tokens: input={usage.input_tokens}, "
                    f"output={usage.output_tokens}, total={usage.total_tokens}, "
                    f"budget={usage.budget_tokens}"
                ),
                "estimated calls are marked in the saved token_usage records",
            )
        _clear_transient_trace()
        state.reply_card = None
        if state.pending_plan is None:
            state.next_prompt = build_next_turn_prompt(result)
            state.follow_up_context = build_follow_up_context(
                result, state.next_prompt, task
            )
            state.reply_card = self._reply_card(result, task)
            events.append(Event("message", result["messages"][-1].content, card=state.reply_card))
            if state.next_prompt.kind == "dry_run":
                state.preview = PreviewState(
                    task=task,
                    workflow=plan.workflow,
                    plan=plan,
                    plan_evaluation=result.get("plan_evaluation"),
                )
            elif state.next_prompt.kind == "completed":
                state.clear_preview()
        self._remember_turn(result, task)
        if state.pending_plan is not None:
            self.runtime.recorder.pause_run(
                state.run_id,
                {"reason": state.pending_plan.status},
            )
            self._write_planning_audit_if_needed(state.run_id, task, result)
            state.run_paused = True
            return events
        evaluation_status = (result.get("evaluation") or {}).get("status")
        terminal_status = "failed" if evaluation_status == "failed" else "completed"
        self.runtime.recorder.finish_run(
            state.run_id,
            terminal_status,
            {
                "evaluation_status": evaluation_status,
                "token_usage": state.active_usage or {},
            },
        )
        self._write_planning_audit_if_needed(
            state.run_id,
            task,
            result,
            execution_turn=execute_once,
        )
        state.run_id = None
        state.active_usage = None
        if state.one_shot:
            if (
                _is_auto_session_id(state.session_id)
                and not self.args.keep_session
                and evaluation_status != "failed"
            ):
                delete_session(state.session_id)
                _trace("done", "Removed the successful ephemeral session checkpoint")
            self.stop(0)
        return events

    def _remember_turn(self, result: dict, task: str = "") -> None:
        """Record the session's models, output folder and brief reply beside its checkpoint.

        Only a runtime built by ``bootstrap_runtime`` knows its models; one
        assembled by hand (a test, a harness) keeps no sidecar.
        """
        if not getattr(self.runtime, "session_models", None):
            return
        try:
            from .. import session as session_store
            from ..session_meta import remember_turn
            from ..session_outputs import session_output_path

            messages = result.get("messages") or []
            finished = self.state.pending_plan is None
            remember_turn(
                self.state.session_id,
                models=getattr(self.runtime, "session_models", None),
                content=str(messages[-1].content) if messages and self.state.reply_card else None,
                card=self.state.reply_card,
                output_dir=session_output_path(self.state.session_id),
                # A paused run carries its usage into the turn that finishes it,
                # so a run is counted once, when it finishes.
                tokens=int(((result.get("token_usage") or {}).get("total_tokens") or 0)) if finished else 0,
                request=task,
                sessions_root=session_store.SESSION_ROOT,
            )
        except Exception:  # noqa: BLE001 - bookkeeping must not break a turn
            return

    def _card_task(self, result: dict, task: str) -> str:
        """The request a card should read: a picked option's marker carries no data.

        After an option is picked the turn's task is a machine marker such as
        ``CONFIRMED_OUTCOME_ACTION=run_condor``; what the user said about their
        data is in the last request they wrote, which the card reads as well.
        """
        if not task.startswith(("CONFIRMED_OUTCOME_ACTION=", "PREVIOUS_ACTION=")):
            return task
        for message in reversed(result.get("messages") or []):
            content = str(getattr(message, "content", ""))
            if getattr(message, "type", "") == "human" and content and not content.startswith(
                ("CONFIRMED_OUTCOME_ACTION=", "PREVIOUS_ACTION=")
            ):
                return content + "\n" + task
        return task

    def _reply_card(self, result: dict, task: str) -> dict | None:
        """The brief form of this turn's reply, or None; never fails the turn."""
        try:
            from ..reply_cards import build_reply_card

            card = build_reply_card(
                result,
                self.state.next_prompt,
                getattr(self.runtime, "project_policy", None),
                task=self._card_task(result, task),
            )
        except Exception as error:  # noqa: BLE001 - presentation must not break a turn
            _trace("done", "The reply card was skipped", type(error).__name__)
            return None
        return card.model_dump(mode="json") if card is not None else None

    def _write_planning_audit_if_needed(
        self,
        run_id: str,
        task: str,
        result: dict | None = None,
        *,
        execution_turn: bool = False,
    ) -> None:
        """Persist only planning-mode audit Markdown; execute logging is untouched."""
        if settings.EXECUTE_TOOLS or execution_turn:
            return
        try:
            write_planning_audit(
                run_id,
                self.runtime.trace_store,
                task=task,
                result=result,
            )
        except Exception:
            # Observability must never change the outcome of a planning or
            # execute turn.
            return

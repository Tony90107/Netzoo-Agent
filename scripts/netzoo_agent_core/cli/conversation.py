"""One-shot, interactive, clarification, and resume conversation lifecycle."""

from __future__ import annotations

import sys

from workflow_registry import RUN_ACTIONS

from .. import settings
from ..contracts.planning import WorkflowPlan
from ..contracts.state import (
    AgentTurnInterrupted,
    ClarificationInputError,
    LLMUsage,
    NextTurnPrompt,
)
from ..contracts import FollowUpContext
from ..contracts.interaction import WorkflowContinuation
from ..framework_compat import HumanMessage
from ..presentation import _clear_transient_trace, _trace, _ui_text
from ..planning_audit import write_planning_audit
from ..settings import INPUT_ROLE_FIELDS, OUTPUT_ROLE_FIELDS, ROUTER_CONTEXT_MAX_CHARS
from ..session import (
    _is_auto_session_id,
    compact_conversation,
    delete_session,
    save_session,
)
from .bootstrap import CliRuntime
from .clarification import (
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
from .follow_up import (
    build_follow_up_context,
    build_next_turn_prompt,
    build_workflow_continuation,
    follow_up_returns_to_main,
    initial_next_turn_prompt,
    render_next_turn_prompt,
    resolve_next_turn_input,
)
from .slash_commands import handle_slash_command, render_mode_prompt
from .terminal_input import TerminalInputReader

__all__: list[str] = []

_PATH_ANSWER_FIELDS = INPUT_ROLE_FIELDS | OUTPUT_ROLE_FIELDS


def _handle_interactive_control(
    answer: str,
    *,
    allow_path_answer: bool = False,
    execution_ready: bool = False,
    execution_block_reason: str = "",
    current_plan: WorkflowPlan | None = None,
    current_plan_evaluation: dict | None = None,
) -> bool:
    result = handle_slash_command(
        answer,
        allow_path_answer=allow_path_answer,
        execution_ready=execution_ready,
        execution_block_reason=execution_block_reason,
        current_plan=current_plan,
        current_plan_evaluation=current_plan_evaluation,
    )
    if not result.handled:
        return False
    print(_ui_text(result.message))
    return True


def _write_planning_audit_if_needed(
    runtime: CliRuntime,
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
            runtime.trace_store,
            task=task,
            result=result,
        )
    except Exception:
        # Observability must never change the outcome of a planning or execute turn.
        return


def run_conversation(args, runtime: CliRuntime) -> int:
    profile_id = runtime.memory.profile_id
    profile_store = runtime.memory.profile_store
    session_id = runtime.session_id
    conversation = runtime.conversation
    pending_plan = runtime.pending_plan
    active_usage = runtime.active_usage
    run_id = runtime.run_id
    recorder = runtime.recorder
    ensure_trace_sync = runtime.ensure_trace_sync
    input_func = runtime.input_func
    reader = TerminalInputReader(
        input_func,
        is_tty=sys.stdin.isatty,
        notice=lambda message: print(_ui_text(message)),
    )
    invoke_graph_turn_func = runtime.invoke_graph_turn_func
    reply_resolver = runtime.reply_resolver

    clarification_selections: dict[str, str] = {}
    custom_input_selection = False
    preview_task: str | None = None
    preview_workflow: str | None = None
    preview_plan: WorkflowPlan | None = None
    preview_plan_evaluation: dict | None = None
    execution_confirmation_task: str | None = None
    input_confirmation_correction = False
    run_paused = False
    queued_task = args.task
    one_shot = bool(args.task) and not runtime.resume_id
    next_prompt = initial_next_turn_prompt()
    follow_up_context: FollowUpContext | None = None
    if not args.task:
        print(
            _ui_text(
                "NetZoo agent started in Planning mode. "
                "Enter /help for controls, or exit or quit to stop."
            )
        )

    while True:
        execute_once = False
        workflow_continuation = None
        if execution_confirmation_task is not None:
            try:
                raw_answer = reader.read(
                    render_mode_prompt(
                        "\nRun the validated "
                        f"{preview_workflow or 'NetZoo'} workflow now? [y/N] "
                    ),
                    menu_enabled=False,
                )
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if raw_answer is None:
                continue
            answer = raw_answer.strip()
            if _handle_interactive_control(answer):
                continue
            if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                break
            if answer.casefold() not in {"y", "yes"}:
                execution_confirmation_task = None
                print(_ui_text("Execution cancelled; the command preview is unchanged."))
                continue
            task = execution_confirmation_task
            execution_confirmation_task = None
            execute_once = True
            if preview_plan is not None:
                action = preview_plan.decision["action"]
                if action in RUN_ACTIONS:
                    workflow_continuation = WorkflowContinuation(
                        action=action, task=task[-ROUTER_CONTEXT_MAX_CHARS:]
                    )
        elif queued_task is not None:
            task = queued_task.strip()
            queued_task = None
        elif pending_plan is not None:
            if not sys.stdin.isatty() and input_func is input:
                _clear_transient_trace()
                if pending_plan.status == "needs_confirmation":
                    print(
                        "\n"
                        + (
                            input_confirmation_prompt(
                                pending_plan,
                                correction=input_confirmation_correction,
                            )
                            if not pending_plan.preference_proposals
                            else preference_confirmation_prompt(pending_plan)
                        )
                    )
                else:
                    print("\n" + clarification_prompt(pending_plan))
                print(
                    _ui_text("Run the command again with --resume ")
                    + f"{session_id}"
                    + _ui_text(" after preparing the answer.")
                )
                return 2
            if pending_plan.status == "needs_confirmation":
                if not pending_plan.preference_proposals:
                    try:
                        raw_answer = reader.read(
                            render_mode_prompt(
                                "\n"
                                + input_confirmation_prompt(
                                    pending_plan,
                                    correction=input_confirmation_correction,
                                )
                            ),
                            menu_enabled=False,
                        )
                    except (EOFError, KeyboardInterrupt):
                        print()
                        break
                    if raw_answer is None:
                        continue
                    answer = raw_answer.strip()
                    if _handle_interactive_control(
                        answer,
                        current_plan=pending_plan,
                        execution_block_reason=(
                            "This workflow still requires input confirmation. "
                            "Confirm the displayed files or provide corrected paths."
                        ),
                    ):
                        continue
                    if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                        break
                    if not input_confirmation_correction:
                        if answer.casefold() in {"y", "yes"}:
                            task = input_confirmation_continuation(
                                pending_plan,
                                answer,
                                approved=True,
                            )
                            input_confirmation_correction = False
                        elif answer.casefold() in {"n", "no", ""}:
                            input_confirmation_correction = True
                            print(
                                "\n"
                                + input_confirmation_prompt(
                                    pending_plan,
                                    correction=True,
                                )
                            )
                            continue
                        else:
                            try:
                                task = input_confirmation_continuation(
                                    pending_plan,
                                    answer,
                                    approved=False,
                                )
                            except ClarificationInputError as error:
                                print(
                                    "\n"
                                    + _ui_text("Input not accepted: ")
                                    + str(error)
                                )
                                input_confirmation_correction = True
                                continue
                        input_confirmation_correction = False
                    else:
                        try:
                            task = input_confirmation_continuation(
                                pending_plan,
                                answer,
                                approved=False,
                            )
                        except ClarificationInputError as error:
                            print(
                                "\n"
                                + _ui_text("Input not accepted: ")
                                + str(error)
                            )
                            continue
                        input_confirmation_correction = False
                else:
                    try:
                        raw_answer = reader.read(
                            render_mode_prompt(
                                "\n" + preference_confirmation_prompt(pending_plan)
                            ),
                            menu_enabled=False,
                        )
                    except (EOFError, KeyboardInterrupt):
                        print()
                        break
                    if raw_answer is None:
                        continue
                    answer = raw_answer.strip()
                    if _handle_interactive_control(answer):
                        continue
                    if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                        break
                    approved = answer.casefold() in {"y", "yes"}
                    if approved:
                        profile_store.confirm(
                            profile_id,
                            pending_plan.preference_proposals,
                        )
                        print(
                            _ui_text("Saved confirmed preferences to profile ")
                            + f"'{profile_id}'."
                        )
                    else:
                        print(_ui_text("Preference changes were not saved."))
                    task = preference_continuation(pending_plan, approved)
            else:
                choosing_complete_bundle = bool(
                    pending_plan.input_bundle_options
                ) and not custom_input_selection
                unresolved_fields = [
                    item.field
                    for item in pending_plan.evidence
                    if item.status == "missing"
                    and item.field not in clarification_selections
                ]
                target_field = unresolved_fields[0] if unresolved_fields else None
                try:
                    raw_answer = reader.read(
                        render_mode_prompt(
                            "\n"
                            + (
                                custom_clarification_prompt(
                                    pending_plan,
                                    clarification_selections,
                                )
                                if custom_input_selection
                                else clarification_prompt(
                                    pending_plan,
                                    clarification_selections,
                                )
                            )
                        ),
                        menu_enabled=False,
                    )
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if raw_answer is None:
                    continue
                answer = raw_answer.strip()
                missing_labels = ", ".join(pending_plan.missing_inputs)
                if _handle_interactive_control(
                    answer,
                    current_plan=pending_plan,
                    allow_path_answer=(
                        not choosing_complete_bundle
                        and target_field in _PATH_ANSWER_FIELDS
                    ),
                    execution_block_reason=(
                        "This workflow plan is not ready to execute. It still needs: "
                        f"{missing_labels}. Continue the input wizard or provide the "
                        "required paths."
                    ),
                ):
                    continue
                if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                    break
                if not answer:
                    continue
                try:
                    if choosing_complete_bundle:
                        if answer.casefold() == "custom":
                            custom_input_selection = True
                            clarification_selections = {}
                            continue
                        task = bundle_clarification_continuation(
                            pending_plan,
                            answer,
                        )
                        custom_input_selection = False
                        clarification_selections = {}
                    elif "lioness_mode" in pending_plan.missing_inputs:
                        task = resolve_clarification(pending_plan, answer)
                    else:
                        clarification_selections = parse_clarification_assignments(
                            pending_plan,
                            answer,
                            selected=clarification_selections,
                            target_field=target_field,
                        )
                        still_missing = [
                            field_name
                            for field_name in pending_plan.missing_inputs
                            if field_name not in clarification_selections
                        ]
                        if still_missing:
                            continue
                        task = clarification_continuation(
                            pending_plan,
                            clarification_selections,
                        )
                        clarification_selections = {}
                except ClarificationInputError as error:
                    print("\n" + _ui_text("Selection not accepted: ") + str(error))
                    continue
        else:
            if one_shot:
                break
            try:
                raw_answer = reader.read(
                    f"\n{render_mode_prompt(render_next_turn_prompt(next_prompt))}\n> ",
                    # Keep the prompt-toolkit adapter for ordinary tasks so a
                    # bracketed multi-line paste stays one submission. Path
                    # prompts remain plain input to avoid slash/path ambiguity.
                    menu_enabled=next_prompt.expected_field not in _PATH_ANSWER_FIELDS,
                )
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if raw_answer is None:
                continue
            answer = raw_answer.strip()
            if (
                answer.casefold() == "/execute"
                and next_prompt.kind == "dry_run"
                and preview_task is not None
            ):
                command_result = handle_slash_command(
                    answer,
                    current_plan=preview_plan,
                    current_plan_evaluation=preview_plan_evaluation,
                )
                print(_ui_text(command_result.message))
                if command_result.execute_once:
                    execution_confirmation_task = preview_task
                continue
            if _handle_interactive_control(
                answer,
                allow_path_answer=next_prompt.expected_field in _PATH_ANSWER_FIELDS,
            ):
                continue
            if follow_up_returns_to_main(next_prompt, answer):
                next_prompt = initial_next_turn_prompt()
                follow_up_context = None
                continue
            if not answer:
                continue
            if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                break
            if next_prompt.kind != "initial" and follow_up_context is not None:
                if run_id is None:
                    run_id = str(
                        recorder.start_run(
                            session_id=session_id,
                            profile_id=profile_id,
                        )
                    )
                    ensure_trace_sync(run_id)
                reply_result = reply_resolver.resolve(
                    follow_up_context,
                    answer,
                    active_usage,
                    run_id,
                )
                active_usage = reply_result.usage.model_dump()
                resolution = reply_result.resolution
                if resolution.kind == "needs_detail":
                    retry_question = _ui_text(
                        "Please enter a concrete follow-up question, provide the "
                        "requested input path, or describe another NetZoo goal."
                    )
                    next_prompt = next_prompt.model_copy(
                        update={"question": retry_question}
                    )
                    follow_up_context = follow_up_context.model_copy(
                        update={
                            "prompt_kind": next_prompt.kind,
                            "prompt_question": retry_question,
                        }
                    )
                    recorder.finish_run(
                        run_id,
                        "completed",
                        {
                            "interaction_status": "needs_detail",
                            "token_usage": active_usage,
                        },
                    )
                    run_id = None
                    active_usage = None
                    continue
                if resolution.kind == "navigation":
                    recorder.finish_run(
                        run_id,
                        "completed",
                        {
                            "interaction_status": "navigation",
                            "token_usage": active_usage,
                        },
                    )
                    run_id = None
                    active_usage = None
                    next_prompt = initial_next_turn_prompt()
                    follow_up_context = None
                    continue
                task = resolve_next_turn_input(next_prompt, resolution, answer)
                if not task:
                    print(
                        _ui_text(
                            "Please enter a concrete follow-up question, provide the "
                            "requested input path, or describe another NetZoo goal."
                        )
                    )
                    recorder.finish_run(
                        run_id,
                        "completed",
                        {
                            "interaction_status": "needs_detail",
                            "token_usage": active_usage,
                        },
                    )
                    run_id = None
                    active_usage = None
                    continue
                workflow_continuation = build_workflow_continuation(
                    next_prompt, follow_up_context, resolution, task
                )
            else:
                task = answer
        if task.casefold() in {"exit", "quit", "q", "離開", "結束"}:
            break
        if not task:
            continue
        if pending_plan is not None:
            action = pending_plan.decision["action"]
            if action in RUN_ACTIONS:
                workflow_continuation = WorkflowContinuation(
                    action=action, task=task[-ROUTER_CONTEXT_MAX_CHARS:]
                )
        if run_id is None:
            run_id = str(
                recorder.start_run(session_id=session_id, profile_id=profile_id)
            )
            ensure_trace_sync(run_id)
        elif run_paused:
            recorder.append(
                run_id,
                "run.resumed",
                "cli",
                {"session_id": session_id},
            )
            run_paused = False
        try:
            if execute_once:
                # Execution authority is scoped to this single graph turn. The
                # next prompt always returns to Planning mode.
                from ..runtime import configure_runtime

                configure_runtime(EXECUTE_TOOLS=True)
            invocation = {
                "messages": [*conversation, HumanMessage(content=task)],
                "session_id": session_id,
                "run_id": run_id,
                "workflow_continuation": (
                    workflow_continuation.model_dump() if workflow_continuation else None
                ),
            }
            if active_usage is not None:
                invocation["token_usage"] = active_usage
            result = invoke_graph_turn_func(runtime.app, invocation)
        except AgentTurnInterrupted:
            recorder.append(
                run_id,
                "run.interrupted",
                "cli",
                {"reason": "keyboard_interrupt"},
            )
            _write_planning_audit_if_needed(runtime, run_id, task)
            _clear_transient_trace()
            print()
            print(
                _ui_text(
                    "The current request was interrupted. No unfinished local "
                    "analysis command will be reported as completed."
                )
            )
            return 130
        except Exception as error:
            recorder.append(
                run_id,
                "error.recorded",
                "cli",
                {"error_type": type(error).__name__, "message": str(error)},
            )
            _write_planning_audit_if_needed(runtime, run_id, task)
            _clear_transient_trace()
            print(
                _ui_text(
                    "The agent could not finish this request. No unfinished provider "
                    "or local-tool step will be reported as completed."
                )
            )
            print(_ui_text("Error type: ") + type(error).__name__)
            if one_shot:
                return 1
            next_prompt = NextTurnPrompt(
                kind="failed",
                question=_ui_text(
                    "Would you like to retry with a clearer request, describe a "
                    "different NetZoo goal, or enter exit?"
                ),
            )
            continue
        finally:
            if execute_once:
                from ..runtime import configure_runtime

                configure_runtime(EXECUTE_TOOLS=False)
        conversation = compact_conversation(result["messages"])
        active_usage = result.get("token_usage")
        save_session(session_id, conversation, result, profile_id=profile_id)
        plan = WorkflowPlan.model_validate(result["plan"])
        pending_plan = (
            plan if plan.status in {"needs_input", "needs_confirmation"} else None
        )
        clarification_selections = {}
        custom_input_selection = False
        input_confirmation_correction = False
        if active_usage:
            usage = LLMUsage.model_validate(active_usage)
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
        if pending_plan is None:
            print(result["messages"][-1].content)
            next_prompt = build_next_turn_prompt(result)
            follow_up_context = build_follow_up_context(result, next_prompt, task)
            if next_prompt.kind == "dry_run":
                preview_task = task
                preview_workflow = plan.workflow
                preview_plan = plan
                preview_plan_evaluation = result.get("plan_evaluation")
            elif next_prompt.kind == "completed":
                preview_task = None
                preview_workflow = None
                preview_plan = None
                preview_plan_evaluation = None
        if pending_plan is not None:
            recorder.pause_run(
                run_id,
                {"reason": pending_plan.status},
            )
            _write_planning_audit_if_needed(runtime, run_id, task, result)
            run_paused = True
            continue
        evaluation_status = (result.get("evaluation") or {}).get("status")
        terminal_status = "failed" if evaluation_status == "failed" else "completed"
        recorder.finish_run(
            run_id,
            terminal_status,
            {
                "evaluation_status": evaluation_status,
                "token_usage": active_usage or {},
            },
        )
        _write_planning_audit_if_needed(
            runtime,
            run_id,
            task,
            result,
            execution_turn=execute_once,
        )
        run_id = None
        active_usage = None
        if one_shot:
            if (
                _is_auto_session_id(session_id)
                and not args.keep_session
                and evaluation_status != "failed"
            ):
                delete_session(session_id)
                _trace("done", "Removed the successful ephemeral session checkpoint")
            break
    return 0

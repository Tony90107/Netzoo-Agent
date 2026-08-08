"""One-shot, interactive, clarification, and resume conversation lifecycle."""

from __future__ import annotations

import sys

from ..contracts.planning import WorkflowPlan
from ..contracts.state import (
    AgentTurnInterrupted,
    ClarificationInputError,
    LLMUsage,
    NextTurnPrompt,
)
from ..framework_compat import HumanMessage
from ..presentation import _clear_transient_trace, _trace, _ui_text
from ..settings import INPUT_ROLE_FIELDS, OUTPUT_ROLE_FIELDS
from ..session import (
    _is_auto_session_id,
    compact_conversation,
    delete_session,
    save_session,
)
from .bootstrap import CliRuntime
from .clarification import (
    clarification_continuation,
    clarification_prompt,
    parse_clarification_assignments,
    preference_confirmation_prompt,
    preference_continuation,
    resolve_clarification,
)
from .follow_up import (
    build_next_turn_prompt,
    follow_up_declined,
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
) -> bool:
    result = handle_slash_command(
        answer,
        allow_path_answer=allow_path_answer,
    )
    if not result.handled:
        return False
    print(_ui_text(result.message))
    return True


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

    clarification_selections: dict[str, str] = {}
    run_paused = False
    queued_task = args.task
    one_shot = bool(args.task) and not runtime.resume_id
    next_prompt = initial_next_turn_prompt()
    if not args.task:
        print(
            _ui_text(
                "NetZoo agent started. Current mode: TEST. "
                "Enter /help for controls, or exit or quit to stop."
            )
        )

    while True:
        if queued_task is not None:
            task = queued_task.strip()
            queued_task = None
        elif pending_plan is not None:
            if not sys.stdin.isatty() and input_func is input:
                _clear_transient_trace()
                if pending_plan.status == "needs_confirmation":
                    print("\n" + preference_confirmation_prompt(pending_plan))
                else:
                    print("\n" + clarification_prompt(pending_plan, batch=True))
                print(
                    _ui_text("Run the command again with --resume ")
                    + f"{session_id}"
                    + _ui_text(" after preparing the answer.")
                )
                return 2
            if pending_plan.status == "needs_confirmation":
                try:
                    answer = reader.read(
                        render_mode_prompt(
                            "\n" + preference_confirmation_prompt(pending_plan)
                        ),
                        menu_enabled=True,
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
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
                unresolved_fields = [
                    item.field
                    for item in pending_plan.evidence
                    if item.status == "missing"
                    and item.field not in clarification_selections
                ]
                target_field = unresolved_fields[0] if unresolved_fields else None
                try:
                    answer = reader.read(
                        render_mode_prompt(
                            "\n"
                            + clarification_prompt(
                                pending_plan,
                                clarification_selections,
                            )
                        ),
                        menu_enabled=target_field not in _PATH_ANSWER_FIELDS,
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if _handle_interactive_control(
                    answer,
                    allow_path_answer=target_field in _PATH_ANSWER_FIELDS,
                ):
                    continue
                if answer.casefold() in {"exit", "quit", "q", "離開", "結束"}:
                    break
                if not answer:
                    continue
                try:
                    mode_pending = "lioness_mode" in pending_plan.missing_inputs
                    if mode_pending:
                        task = resolve_clarification(pending_plan, answer)
                    else:
                        clarification_selections = parse_clarification_assignments(
                            pending_plan,
                            answer,
                            selected=clarification_selections,
                            target_field=target_field,
                            require_all=False,
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
                answer = reader.read(
                    f"\n{render_mode_prompt(render_next_turn_prompt(next_prompt))}\n> ",
                    menu_enabled=next_prompt.expected_field not in _PATH_ANSWER_FIELDS,
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if _handle_interactive_control(
                answer,
                allow_path_answer=next_prompt.expected_field in _PATH_ANSWER_FIELDS,
            ):
                continue
            if follow_up_returns_to_main(next_prompt, answer):
                next_prompt = initial_next_turn_prompt()
                continue
            if not answer:
                continue
            if next_prompt.kind == "recommended_workflow" and follow_up_declined(
                answer
            ):
                next_prompt = initial_next_turn_prompt()
                continue
            task = resolve_next_turn_input(next_prompt, answer)
        if task.casefold() in {"exit", "quit", "q", "離開", "結束"}:
            break
        if not task:
            continue
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
            invocation = {
                "messages": [*conversation, HumanMessage(content=task)],
                "session_id": session_id,
                "run_id": run_id,
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
        conversation = compact_conversation(result["messages"])
        active_usage = result.get("token_usage")
        save_session(session_id, conversation, result, profile_id=profile_id)
        plan = WorkflowPlan.model_validate(result["plan"])
        pending_plan = (
            plan if plan.status in {"needs_input", "needs_confirmation"} else None
        )
        clarification_selections = {}
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
        if pending_plan is not None:
            recorder.pause_run(
                run_id,
                {"reason": pending_plan.status},
            )
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

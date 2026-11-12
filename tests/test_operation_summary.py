"""The plain-English run description (`operation.summary`) states only what the turn recorded."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.framework_compat import AIMessage, HumanMessage
from netzoo_agent_core.operation_summary import action_label, build_operation_summary


def _state(**overrides):
    state = {
        "messages": [HumanMessage(content="earlier"), AIMessage(content="ok"),
                     HumanMessage(content="Run PANDA on data/toy/expr.tsv with the motif prior")],
        "decision": {"action": "run_panda", "reason": "The request names PANDA.", "candidate_actions": ["run_panda"],
                     "core": {"kind": "DO", "workflows": ["PANDA"], "partial": False, "declined": []}},
        "plan": {"workflow": "PANDA", "objective": "Build one network", "status": "ready",
                 "steps": [{"action": "inspect_inputs", "purpose": "Validate inputs."},
                           {"action": "run_panda", "purpose": "Execute the requested NetZoo workflow."}],
                 "evidence": [{"field": "expression_file", "value": "data/toy/expr.tsv", "status": "provided"}],
                 "missing_inputs": []},
        "tool_results": [
            {"action": "inspect_inputs", "status": "success", "summary": "Inputs passed.", "artifacts": []},
            {"action": "run_panda", "status": "success", "summary": "Passed checks.",
             "artifacts": ["/work/outputs/panda.tsv", "/work/outputs/panda.tsv"], "warnings": ["Small sample"]},
        ],
        "evaluation": {"status": "completed", "reason": "All planned steps completed successfully."},
        "token_usage": {"total_tokens": 900, "calls": [{"cost_micro_usd": 500, "model": "openai/gpt-4o-mini"},
                                                       {"cost_micro_usd": None, "model": "openai/gpt-4o-mini"}]},
    }
    state.update(overrides)
    return state


def test_an_executed_run_names_request_method_steps_outputs_and_next_step():
    summary = build_operation_summary(_state(), {"messages": [AIMessage(content="PANDA finished.")], "reply_kind": "x"})
    assert summary["outcome"] == "executed"
    assert summary["headline"] == "PANDA ran and finished; 1 output file recorded."
    assert summary["request"] == "Run PANDA on data/toy/expr.tsv with the motif prior"
    assert summary["narrative"][0].startswith("You asked:")
    assert "Selected method: PANDA." in summary["narrative"][1]
    assert summary["method"]["steps"][1]["label"] == "Run PANDA"
    assert summary["inputs"][0]["source"] == "given in the request"
    assert summary["outputs"] == ["/work/outputs/panda.tsv"]
    assert summary["warnings"] == ["Small sample"]
    assert summary["reply_excerpt"] == "PANDA finished."
    assert summary["usage"] == {"llm_calls": 2, "total_tokens": 900, "cost_usd": 0.0005, "cost_complete": False,
                                "models": ["openai/gpt-4o-mini"]}
    assert summary["next_step"].startswith("Open the recorded outputs")


def test_a_dry_run_is_a_preview_and_never_claims_outputs():
    tools = [{"action": "run_panda", "status": "dry_run", "summary": "The dry run completed.",
              "artifacts": ["/work/outputs/planned.tsv"]}]
    summary = build_operation_summary(_state(tool_results=tools))
    assert summary["outcome"] == "preview"
    assert "has not run yet" in summary["headline"]
    assert summary["outputs"] == [] and summary["planned_outputs"] == ["/work/outputs/planned.tsv"]
    assert "previewed (dry run, not executed)" in " ".join(summary["narrative"])
    assert summary["next_step"].startswith("Approve the checked plan to run PANDA")


def test_a_failed_step_is_the_conclusion_and_its_error_is_kept():
    tools = [{"action": "run_panda", "status": "failed", "summary": "Failed.", "errors": ["FileNotFoundError: expr.tsv"]},
             {"action": "run_panda", "status": "success", "superseded": True}]
    summary = build_operation_summary(_state(tool_results=tools, evaluation={"status": "failed", "reason": "Step failed."}))
    assert summary["outcome"] == "failed"
    assert summary["errors"] == ["FileNotFoundError: expr.tsv"]
    assert "1 earlier attempt was replaced" in " ".join(summary["narrative"])


def test_missing_inputs_and_a_question_are_the_next_step():
    plan = {"workflow": "PANDA", "status": "needs_input", "missing_inputs": ["motif_file"],
            "question": "Which motif prior should PANDA use?", "steps": []}
    summary = build_operation_summary(_state(plan=plan, tool_results=[], evaluation={}))
    assert summary["outcome"] == "needs_input"
    assert summary["headline"].endswith("(motif_file).")
    assert summary["questions"] == ["Which motif prior should PANDA use?"]
    assert summary["next_step"] == "Give the missing inputs in the conversation."


def test_a_declined_request_names_no_method_and_quotes_what_was_not_done():
    decision = {"action": "no_tool", "core": {"kind": "DECLINE", "workflows": [], "declined": [
        {"quote": "predict drug response", "reasons": ["no workflow produces drug response"]}]}}
    plan = {"workflow": "none", "status": "respond_only", "steps": []}
    summary = build_operation_summary(_state(decision=decision, plan=plan, tool_results=[], evaluation={}))
    assert summary["outcome"] == "declined"
    assert summary["method"]["workflow"] is None
    assert "Selected method" not in " ".join(summary["narrative"])
    assert "“predict drug response” (no workflow produces drug response)" in " ".join(summary["narrative"])


def test_a_conversation_only_turn_says_no_workflow_ran():
    summary = build_operation_summary({"messages": [HumanMessage(content="What does PANDA do?")]})
    assert summary["outcome"] == "answered"
    assert summary["narrative"][1] == "The agent handled this in the conversation and did not select a workflow."
    assert summary["tools"] == [] and summary["usage"] == {}


def test_action_labels_match_the_desktop_reading():
    assert action_label("inspect_inputs") == "Inspect input data"
    assert action_label("inspect_scorpion_inputs") == "Inspect SCORPION inputs"
    assert action_label("run_lioness_panda") == "Run LIONESS-PANDA"


def test_a_question_turn_names_the_question_and_does_not_call_the_method_selected():
    decision = {"action": "run_panda", "candidate_actions": ["run_panda", "no_tool"], "core": {"kind": "ASK", "workflows": ["PANDA"],
                                                "facts": [{"question": "Did you mean PANDA's result?"}]}}
    plan = {"workflow": "PANDA", "status": "respond_only", "steps": []}
    summary = build_operation_summary(_state(decision=decision, plan=plan, tool_results=[], evaluation={}))
    assert summary["outcome"] == "asked"
    assert "Method being considered: PANDA." in summary["narrative"][1]
    assert summary["questions"] == ["Did you mean PANDA's result?"]
    assert summary["next_step"] == "Answer the agent's question in the conversation."
    assert summary["decision"]["candidates"] == ["Run PANDA", "No workflow (answer in the conversation)"]


def test_a_follow_up_turn_shows_the_request_and_the_reply_apart():
    task = "Previous NetZoo goal: Run PANDA on the toy data\nUser follow-up: Yes, I mean PANDA's result."
    summary = build_operation_summary(_state(messages=[HumanMessage(content=task)]))
    assert summary["request"] == "Run PANDA on the toy data"
    assert summary["follow_up"] == "Yes, I mean PANDA's result."
    assert summary["narrative"][0] == "You asked: “Run PANDA on the toy data” Then you replied: “Yes, I mean PANDA's result.”"


def test_a_confirmed_choice_is_described_with_the_original_request():
    messages = [
        HumanMessage(content="Previous NetZoo goal: Run PANDA on the toy data\nUser follow-up: Yes."),
        AIMessage(content="Are these the files you want to use?"),
        HumanMessage(content="DATA_CONFIRMATION_APPROVED. PREVIOUS_ACTION=run_panda. Continue the previous PANDA task; "
                             "CONFIRMED_INPUT_expression_file=data/toy/expr.tsv;"),
    ]
    summary = build_operation_summary(_state(messages=messages))
    assert summary["request"] == "Run PANDA on the toy data"
    assert summary["follow_up"] == "You confirmed the input files the agent found."
    assert summary["narrative"][0] == "You asked: “Run PANDA on the toy data” You confirmed the input files the agent found."
    assert summary["inputs"][0]["source"] == "confirmed by you"
    assert "PREVIOUS_ACTION" not in str(summary)


def test_a_tie_between_methods_is_a_choice_not_an_answer():
    decision = {"action": "no_tool", "core": {"kind": "DO", "workflows": ["LIONESS-PANDA", "LIONESS-PUMA"]}}
    plan = {"workflow": "none", "status": "respond_only", "steps": []}
    summary = build_operation_summary(_state(decision=decision, plan=plan, tool_results=[], evaluation={}),
                                      {"reply_kind": "outcome_clarification"})
    assert summary["outcome"] == "choice"
    assert summary["headline"] == ("More than one method fits (LIONESS-PANDA and LIONESS-PUMA); "
                                   "the agent asked you to choose. Nothing was run.")
    assert "Methods that fit: LIONESS-PANDA and LIONESS-PUMA." in summary["narrative"][1]
    assert summary["next_step"].startswith("Pick one of the offered options")


def test_a_held_run_never_reads_as_selected():
    decision = {"action": "run_dragon", "core": {"kind": "UNCHECKED", "workflows": ["DRAGON"]}}
    plan = {"workflow": "none", "status": "respond_only", "steps": []}
    summary = build_operation_summary(_state(decision=decision, plan=plan, tool_results=[], evaluation={}),
                                      {"reply_kind": "run_held"})
    assert summary["outcome"] == "held"
    assert "Method being considered: DRAGON." in summary["narrative"][1]


def test_a_declined_part_keeps_its_recorded_line():
    line = '"predict drug response" -- not available here: no registered workflow produces this.'
    decision = {"action": "no_tool", "core": {"kind": "DECLINE", "declined": [{"quote": "predict drug response", "line": line}]}}
    plan = {"workflow": "none", "status": "respond_only", "steps": []}
    summary = build_operation_summary(_state(decision=decision, plan=plan, tool_results=[], evaluation={}))
    assert "Not done: " + line in summary["narrative"]

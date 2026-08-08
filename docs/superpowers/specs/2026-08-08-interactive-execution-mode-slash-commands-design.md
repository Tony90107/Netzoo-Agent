# Interactive Execution Mode Slash Commands

**Date:** 2026-08-08

## Goal

Let an interactive `./netzoo-chat` user choose between preview-only testing and
real command execution without restarting the container. Replace the startup
`--execute` flag with explicit slash commands handled entirely by the CLI.

## User Experience

`./netzoo-chat` always starts in test mode. The startup message and interactive
prompt show the current mode so that execution authority remains visible.

The interactive session supports these exact commands:

| Command | Effect |
|---|---|
| `/test` | Keep future workflow tasks in validation and command-preview mode. |
| `/execute` | Allow future workflow tasks to run validated local commands. |
| `/status` | Display the current `TEST` or `EXECUTE` mode. |
| `/help` | Display the available slash commands and their meanings. |

The selected mode persists for the rest of the session or until another mode
command changes it. A successful mode change leaves the user at the same prompt
and preserves the current conversation, pending plan, clarification selections,
and session checkpoint.

The CLI accepts only exact slash commands. A command with trailing arguments,
such as `/execute run PANDA`, is rejected with usage guidance. Unknown slash
commands are not treated as natural-language tasks; the CLI reports the unknown
command and points to `/help`.

## Safety Boundary

Slash commands are intercepted before task routing. They never reach the Router
or response model, never become a NetZoo task, and never start a task trace.

Entering `/execute` is the explicit authorization boundary for subsequent
validated workflow tasks in that interactive process. Entering `/test` revokes
that authority for subsequent tasks. Existing Planner, Plan Evaluator, input
validation, action allowlists, output safety, and tool timeouts remain mandatory
in both modes.

The legacy `--execute` argument is removed rather than deprecated. Argparse will
reject it as an unsupported option. Non-interactive `--task` invocations remain
test-only because they do not provide an interactive opportunity to enter
`/execute`.

## Architecture

A dedicated `netzoo_agent_core.cli.slash_commands` module owns slash-command
parsing, mode changes, status rendering, help rendering, and user-facing errors.
It exposes a small result contract that tells the conversation coordinator
whether input was handled and supplies the message to print.

`conversation.run_conversation` checks interactive input with this handler at
every input boundary:

- the initial or outcome-aware main prompt;
- missing-input clarification prompts;
- preference-confirmation prompts.

If the handler consumes the input, the loop prints its result and returns to the
same prompt without changing task state. Otherwise, existing exit handling,
clarification parsing, follow-up resolution, and graph invocation continue
unchanged.

Mode changes use the existing `configure_runtime` compatibility bridge to set
`EXECUTE_TOOLS` coherently in every loaded NetZoo implementation module. The
slash-command module reads the effective runtime setting when it renders mode
status, rather than copying mode into a second independent source of truth.

The argparse `--execute` declaration is deleted. CLI startup configures
`EXECUTE_TOOLS=False` unconditionally. Existing launcher forwarding remains
available for unrelated supported options.

## Presentation

The startup output includes `Current mode: TEST`. Interactive prompts include a
short `[TEST]` or `[EXECUTE]` marker. Mode changes print a direct confirmation:

- `Execution mode enabled. Future workflow tasks will run commands.`
- `Test mode enabled. Future workflow tasks will only create previews.`

After a dry run, the outcome-aware follow-up tells the user to enter `/execute`
to enable real execution in the current session. It no longer tells the user to
restart with `--execute`.

All user-visible agent output remains English, matching project policy.

## Documentation Changes

Update `AGENTS.md`, `README.md`, `AGENT_USAGE.md`, and other directly affected
guides or messages so they describe the interactive execution boundary. Remove
instructions that recommend starting the CLI with `--execute`.

## Error Handling

- Unknown slash commands display a concise error and suggest `/help`.
- Slash commands with arguments display the command's exact supported form.
- Repeating the active mode command is idempotent and reports the resulting mode.
- A slash command entered during clarification or preference confirmation does
  not count as an answer and does not discard collected state.
- Existing EOF, keyboard interrupt, provider failure, and graph interruption
  behavior remains unchanged.

## Testing

Add focused tests that prove:

1. `/test`, `/execute`, `/status`, and `/help` are recognized and rendered.
2. The mode persists across tasks and can switch `TEST -> EXECUTE -> TEST`.
3. Slash commands work at the main, clarification, and preference prompts without
   losing pending state.
4. Handled slash commands do not invoke the graph or start a trace.
5. Unknown commands and commands with trailing arguments never reach the LLM.
6. Argparse no longer accepts `--execute`.
7. Dry-run follow-up guidance uses `/execute` rather than restart instructions.
8. Existing lifecycle, launcher, agent-gate, and full-suite behavior remains
   passing after the change.

## Out of Scope

- One-shot syntax such as `/execute <task>`.
- Persisting execution mode across process restarts or resumed containers.
- Bypassing validation, planning, evaluation, or action allowlists in execute
  mode.
- Adding slash commands to non-interactive `--task` invocations.

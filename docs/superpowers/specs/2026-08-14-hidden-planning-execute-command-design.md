# Hidden Planning and Execute Command Design

## Goal

Replace the interactive CLI's visible `TEST`/`EXECUTE` toggle with a hidden
Planning default and an explicit `/execute` command. Planning remains the
safe preview-only state, but its label is not shown in the main prompt.

## User experience

- A new interactive Agent session starts in Planning mode with execution
  disabled.
- The ordinary prompt is exactly `What would you like to accomplish with
  NetZoo?`; it has no `[Planning]` or `[TEST]` prefix.
- Entering `/` at an empty ordinary prompt opens an inline slash-command input
  containing `/execute`. The `execute` portion is muted and selected as the
  default completion.
- Pressing Enter submits `/execute`. Typing replaces the selected completion,
  allowing the user to enter any supported slash command, including
  `/planning`, `/status`, and `/help`.
- Entering `/execute` enables execution for the remainder of the current
  interactive Agent session and reports that execution is enabled.
- Once enabled, the ordinary prompt is `[Execute] What would you like to
  accomplish with NetZoo?`.
- Ending the Agent session resets the next session to hidden Planning mode.

## Command surface

- `/planning` returns the current session to Planning.
- `/execute` grants execution authority and `/planning` revokes it for future
  workflow tasks in the current session.
- `/status` reports `Planning` before execution is enabled and `Execute`
  afterward.
- `/help` describes `/execute`, `/planning`, `/status`, and `/help`; it explains
  that `/planning` returns the session to preview-only Planning.
- Unknown commands, absolute-path answers, and commands with arguments retain
  their current parsing and error behavior.

## Runtime and safety

The internal execution flag continues to be false at CLI startup, becomes true
after an exact `/execute` command, and becomes false again after an exact
`/planning` command in the current interactive session.
All existing plan-evaluator and executor gates remain unchanged. Therefore
Planning still produces command previews without executing analysis tools.
`/planning` only changes authority for later workflow tasks: it cannot interrupt an
analysis tool that is already running, because the interactive prompt is not
available while that work is in progress. `Ctrl+C` remains the mechanism for
interrupting the current CLI process.

## Implementation boundaries

The CLI slash-command module owns naming, prompt rendering, help, status, and
mode transitions. The lifecycle bootstrap remains responsible for resetting
execution at each CLI start. Conversation and terminal-input code continue to
route slash commands without invoking the graph.

## Tests

Update slash-command unit tests and interactive lifecycle tests to prove:

1. A new session begins with the unprefixed prompt and execution disabled.
2. `/execute` persists through subsequent prompts in that session and renders
   `[Execute]`.
3. `/status` uses Planning or Execute terminology.
4. `/planning` revokes authority, restores the unprefixed prompt, and reports
   Planning mode.
5. The empty-`/` input selects a muted `execute` completion, Enter submits
   `/execute`, and typed slash commands replace the completion.
6. Starting a separate CLI session resets execution to Planning.

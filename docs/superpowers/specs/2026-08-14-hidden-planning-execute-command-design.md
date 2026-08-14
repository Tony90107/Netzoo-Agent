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
- Entering `/` at an empty ordinary prompt opens the existing slash-command
  input affordance. The available execution command is `/execute`.
- Entering `/execute` enables execution for the remainder of the current
  interactive Agent session and reports that execution is enabled.
- Once enabled, the ordinary prompt is `[Execute] What would you like to
  accomplish with NetZoo?`.
- Ending the Agent session resets the next session to hidden Planning mode.

## Command surface

- Remove `/test`; it is no longer a supported command, help entry, or menu
  choice.
- `/execute` is the only command that changes execution authority.
- `/status` reports `Planning` before execution is enabled and `Execute`
  afterward.
- `/help` describes only `/execute`, `/status`, and `/help`; it must not
  mention Test, switching back, or choosing between modes.
- Unknown commands, absolute-path answers, and commands with arguments retain
  their current parsing and error behavior.

## Runtime and safety

The internal execution flag continues to be false at CLI startup and true
only after an exact `/execute` command in the current interactive session.
All existing plan-evaluator and executor gates remain unchanged. Therefore
Planning still produces command previews without executing analysis tools.
The CLI must not offer a way to revoke execution authority within a session.

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
4. `/test` is rejected as an unknown command and does not alter authority.
5. Help exposes no Test or toggle wording.
6. Starting a separate CLI session resets execution to Planning.

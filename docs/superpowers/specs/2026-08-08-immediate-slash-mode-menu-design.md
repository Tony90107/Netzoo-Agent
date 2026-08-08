# Immediate Slash Mode Menu Design

**Date:** 2026-08-08

## Goal

Make NetZoo's execution-mode selection discoverable in interactive terminals:
when the active task prompt is empty, pressing `/` immediately opens an
arrow-key menu for choosing test or execute mode. Users should not need to
remember or type the mode command.

## User Experience

At a mode-menu-enabled prompt, an empty input buffer reacts to `/` without
requiring Enter:

```text
[TEST] What would you like to accomplish with NetZoo?
> /
```

The terminal presents this menu:

```text
Select NetZoo mode
❯ Test mode — preview commands only
  Execute mode — run validated commands

↑/↓ move · Enter select · Esc cancel
```

The selection initially highlights the current mode. Up and down move the
selection. Enter applies the selected mode and returns to the same prompt.
Escape or Ctrl-C closes the menu without changing the mode, creating a task,
or creating a trace.

After a selection, the existing mode confirmation remains the source of
user-visible authority feedback:

```text
Execution mode enabled. Future workflow tasks will run commands.

[EXECUTE] What would you like to accomplish with NetZoo?
>
```

Existing `/test`, `/execute`, `/status`, and `/help` text commands remain
supported. `/help` explains that `/` opens the mode menu.

## Prompt Scope and Path Safety

The immediate `/` key binding is enabled at the initial prompt, ordinary
outcome-aware prompts, and preference-confirmation prompts when they are not
expecting a path. It is disabled for:

- missing-input clarification prompts whose current field is an input or output
  path role;
- recommended-workflow prompts whose expected field is a path role;
- non-interactive `--task` invocations and non-TTY input.

This preserves direct entry of absolute paths such as `/tmp`, `/output`, and
`/work/data/expression.tsv`. In path prompts, users can continue to type the
existing textual slash commands and submit them with Enter when they need to
change execution mode.

Opening the menu during preference confirmation changes only execution mode; it
does not answer the pending yes/no confirmation.

## Architecture

Add `prompt_toolkit` to the container's Python environment. A focused CLI input
adapter owns terminal-specific behavior:

- it creates the key binding only for an interactive real TTY;
- it opens a two-item modal selector when `/` is pressed at an empty eligible
  buffer;
- it returns the synthetic command `/test` or `/execute` after Enter, or an
  empty no-op result after cancellation;
- it returns ordinary typed text unchanged in every other case.

The adapter does not change runtime settings directly. The existing
`handle_slash_command()` remains the single authority boundary and receives the
synthetic command through the existing conversation control path. This avoids
duplicating execution-mode state transitions.

Tests inject a deterministic adapter or selection result rather than relying on
a real terminal. The existing injected `input_func` path remains available for
unit tests and non-TTY fallback.

## Fallback and Error Handling

If `prompt_toolkit` cannot be imported or initialized in a real TTY, NetZoo
prints one concise English notice and falls back to the current line-based
input. The agent remains usable through `/test` and `/execute` text commands.

Menu cancellation is not an error. It leaves the input prompt active and does
not call the graph, start a trace, modify a pending plan, or alter the current
mode. An already-selected mode is idempotent.

## Testing

Add deterministic tests for:

1. menu options, ordering, labels, and selected default mode;
2. mapping Enter choices to `/test` and `/execute`;
3. Escape and Ctrl-C cancellation with no mode change;
4. menu activation only for empty, eligible interactive prompts;
5. disabled menu binding at path-role clarification and follow-up prompts;
6. unchanged absolute-path handling in disabled prompts;
7. non-TTY and unavailable-TUI fallback to current text input;
8. synthetic menu commands using the existing slash-command handler, without
   graph invocation or trace creation;
9. Docker environment availability and current full-suite regression coverage.

## Documentation

Update current user-facing guides to show `/` as the primary interactive mode
selector, while documenting `/test` and `/execute` as text alternatives.

## Out of Scope

- A graphical desktop dropdown or browser UI.
- A general slash-command picker for every command.
- Menu activation inside path-value prompts.
- Persisting mode selection across process restarts.

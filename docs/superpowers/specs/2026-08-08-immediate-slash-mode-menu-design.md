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

The terminal expands an inline menu directly below the active input prompt. It
does not clear the current terminal content or open a separate screen:

```text
>
  /test      Test mode — preview commands only
▸ /execute   Execute mode — run validated commands
```

The selection initially highlights the current mode. Up, down, or Tab moves
the selection. Enter applies the selected mode and returns to the same prompt.
Escape or Ctrl-C collapses the inline menu without changing the mode, creating
a task, or creating a trace; the same input buffer remains active so the user
can continue typing immediately.

After a selection, the existing mode confirmation remains the source of
user-visible authority feedback:

```text
Execution mode enabled. Future workflow tasks will run commands.

[EXECUTE] What would you like to accomplish with NetZoo?
>
```

Existing `/test`, `/execute`, `/status`, and `/help` text commands remain
supported. At an empty menu-enabled prompt, Ctrl-V inserts a literal `/` so a
user can then type `help`, `status`, `test`, or `execute` and press Enter. A `/`
typed after other text remains literal. `/help` explains both the immediate menu
and this explicit text-command pass-through.

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
- it keeps the prompt and menu in one non-full-screen `prompt_toolkit`
  application, expanding a two-item selector below the input when `/` is
  pressed at an empty eligible buffer;
- it returns the synthetic command `/test` or `/execute` after Enter while
  keeping a cancelled selector in the active input application;
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

Menu cancellation is not an error. It collapses in place, leaves the input
prompt active, and does not call the graph, start a trace, modify a pending
plan, or alter the current mode. An already-selected mode is idempotent.

## Testing

Add deterministic tests for:

1. inline menu options, ordering, labels, selected default mode, and the
   absence of a full-screen dialog;
2. mapping Enter choices to `/test` and `/execute`;
3. real key dispatch for arrow movement plus Enter in both mode directions;
4. Escape and Ctrl-C collapse with no mode, pending-state, graph, trace, or
   preference-confirmation change, followed by ordinary text input in the same
   prompt;
5. menu activation only for empty, eligible interactive prompts;
6. literal `/` preservation after nonempty text and Ctrl-V literal pass-through
   for `/test`, `/execute`, `/status`, and `/help` at an empty prompt;
7. disabled menu binding at path-role clarification and follow-up prompts;
8. unchanged absolute-path handling in disabled prompts;
9. non-TTY and unavailable-TUI fallback to current text input;
10. synthetic menu commands using the existing slash-command handler, without
   graph invocation or trace creation;
11. Docker environment availability and current full-suite regression coverage.

## Documentation

Update current user-facing guides to show `/` as the primary interactive mode
selector, while documenting `/test` and `/execute` as text alternatives.

## Out of Scope

- A graphical desktop dropdown or browser UI.
- A general slash-command picker for every command.
- Menu activation inside path-value prompts.
- Persisting mode selection across process restarts.

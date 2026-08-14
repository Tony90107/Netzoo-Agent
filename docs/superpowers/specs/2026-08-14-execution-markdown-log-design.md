# Execution Markdown Log Design

## Goal

Create a durable Markdown audit record for every workflow that actually runs
after the user grants authority with `/execute`.

## User experience

- Planning command previews do not create execution logs.
- Each Execute-mode workflow creates one independent file in its `output_dir`:
  `<workflow-lowercase>-execution-YYYYMMDD-HHMMSS.md`.
- The file is written even when the workflow command fails, so users can
  inspect the attempted command and preparation work.
- Logs never overwrite input files, output artifacts, or earlier logs.

## Log content

Each document contains the local start and finish timestamps, workflow and
action, the exact executed command, preparation and input-validation reports,
execution status, errors or warnings, and generated artifact paths. Command
text is rendered as a fenced code block; reports are preserved as readable
Markdown sections.

## Architecture

The execution boundary owns log lifecycle: it creates a log context before the
workflow adapter runs, accumulates preparation and command details from the
adapter result, and writes the document in a `finally` path. The writer takes
only structured, already-sanitized execution facts and resolves its destination
inside the validated workflow output directory.

## Safety and tests

- Only Execute-mode runs write logs; dry runs write none.
- Log filenames contain a filesystem-safe timestamp and use exclusive creation
  to avoid accidental overwrite.
- Tests cover a successful prepared workflow, a command failure, dry-run
  suppression, and the generated filename and Markdown sections.

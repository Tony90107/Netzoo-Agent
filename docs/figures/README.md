# Desktop UI screenshots

Captured from the running `NetZoo Agent.app` (macOS, Retina 2x, PNG). Each image
is an intermediate state of one real PANDA run, not a mock-up.

Capture conditions:

| Item | Value |
|---|---|
| Data | the official netZooPy toy data in `data/official-toy/` |
| Model | `openai/gpt-4o-mini` (same model for response, router, and semantic roles) |
| Mode | Synthetic Test (the toy data contains retired gene symbols, which the strict-mode gate rejects) |
| Output | `outputs/demo/ToyExpressionData-panda.tsv`, 3,113,777 bytes |

| File | Screen | What it shows |
|---|---|---|
| `ui-01-startup.png` | empty state after launch | the four-pane information architecture; the sessions list and token counter |
| `ui-02-synthetic-test-mode.png` | switched to Synthetic Test mode | mode switching is a UI control, not a typed command; the mode itself states that results are for software testing only and are not biological evidence |
| `ui-03-plan-evidence-timeline.png` | plan ready | the Plan pane's evidence table (each input labeled with its source, "you gave it"); the Timeline with 68 events, per-node durations and token counts |
| `ui-04-dry-run-and-outputs.png` | dry run and output browsing | pre-execution validation figures: expression 1000 genes x 50 samples, motif targets vs. expression genes 913/913, motif TFs vs. PPI TFs 87/87; the Outputs pane navigated into `outputs / demo` |
| `ui-05-output-preview.png` | output file preview | file contents viewed without loading the whole file; the host-side absolute path is shown |

## Missing screenshot

There is no native-window screenshot of the **two-step approval card** ("Run the
validated PANDA workflow now? / Execute this plan / Cancel"). The screen exists
and works (it was verified against the same daemon driven from a browser), but
capturing it automatically requires sending text input to the window, and
synthetic keyboard events go to whichever application is frontmost. The fastest
way to add it is manually: submit a request, press "Review and execute this
plan" once the plan is ready, then take the screenshot.

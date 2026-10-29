# Answers to agent questions, applied only when code anchors the quoted contract line (2026-10-29, user "照你的這個說法去實作")

## Problem (fresh j7, now seen; same family as W16 / R01)

j7 Y14: the call asked "Has anyone in the group put together a TF-TF protein interaction table for sheep?" (OTTER,
quoting its `ppi_file` line); the user answered "I asked around and there is no TF-TF protein interaction table for
sheep in the group." Nothing bound it (agent yes/no binds only on a first word yes/no) and nothing applies agent
answers, so turn 2 was DO OTTER (gold DECLINE: a required input is missing). Y22 is the same shape for BONOBO's
log-transform declaration (its answer turn was CLARIFY, so this step cannot reach it).

## Why R01 was withdrawn and what is different

R01 (`jev-agent-answers-2026-10-28`) had Jev judge the reply against whatever contract line the question quoted; on
j4 S15 the line was `lambda1`'s setting text, unrelated to "We'll keep 300 genes", judged `fails` 0.72 -> a wrong
DECLINE. The line is the model's choice. Here **code first decides whether the line can decide anything**:

- **Anchor (code, `interpretation/answer_anchor.py`)**, per workflow the question names: the line is verbatim (case and
  spaces folded) in that workflow's contract, is not one of its count rules (a `validation_steps` line or an
  `input_checks` text with a `limit`: counts are judged by code), and names either
  (R) one of its required inputs (`required_inputs` / `required_input_groups`, not outputs) by the input's identifier
  or the identifier's stem (`ppi_file` -> "ppi"; derived from the identifier, never a phrase list), or
  (D) a boolean control that a capability-sheet expectation ties to a value (BONOBO `log_transformed`, `centered`), by
  its name or its description.
- **Jev** reads the reply against the anchored line with the guard's frozen `judge_answer` (meets / fails / unclear) --
  no first-word binding is trusted, so "No idea" cannot count as no.
- **Code decides** with the guard's `answered_core`: only a DO becomes DECLINE `jev_answer`, only on `fails` >= 0.7,
  its line the user's reply and the contract clause, both verbatim. Anything else leaves the call.

Plumbing: `task_updates._pending` keeps an agent question's contract line and workflow as labels (as Jev's own
questions already do; binding unchanged). New step after the data-first step in `routing_planning`, flag
`NETZOO_AGENT_ANSWERS` off (default) / shadow / on. `jev_guard_call.py` is called, not edited.

## Population (`scan.py` -> `population.json`, no model calls)

97 recorded answer turns after an ASK (fact_agent or jev_agent) whose questions quote a contract line; 45 are DO (the
only calls the step can change). Labels: R01's own, else the item file's gold for the scripted reply sent.

## Gates (declared before any code or Jev call)

- **G0** flag off: flags-off harness replay byte-identical to main's; clean-env tests no new failures.
- **G1 precision (hard)**: 0 of the gold-DO answer turns (labels meets / meets_or_none, and the unlabelled X02 / R21
  rows, gold DO by their items) become DECLINE.
- **G2 recall**: of the anchored `fails` DO turns, >= all but one become DECLINE, Y14 included.
- **G3 shape**: every change is DO -> DECLINE `jev_answer` whose line quotes the reply and the contract clause.
- **G4 anchor**: S15 (both) and every count-rule line are not anchored. Reported: every anchored / unanchored row.
- Jev cost cap US$0.05 (R01's cache reused where the inputs are identical).

Stop rule: a failed hard gate -> withdraw. Live only after the user agrees. No gate is changed after the run.

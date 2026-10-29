# A reply already bound to a form or count answer is not a new condition for the model to judge (2026-10-29, "修 X06")

## Trace (j6 X06, gold DO CONDOR; ended DECLINE full_gap -- a false refusal)

t1 group_membership asked (reading typed several_groups; Jev overlap: not stated). t2 the reply "Every TF and every
gene should end up in exactly one module, no sharing between modules." bound in code (`one_group`); input_network asked
(reading typed gene_gene, Jev read regulator_gene 1.0). t3 the same reply was sent again; the reading now credits
CONDOR (`available`), but `stated_requirements` took the reply as a stated condition, the model condition check
(`capability_condition_check`) answered "violates" for CONDOR -- although one group each is exactly what CONDOR gives
-- and the turn became DECLINE full_gap ("I couldn't match this ...").

## Change

`task_answers.settled_quotes(task_state)`: the reply words of every known form or count answer (`source` dimension or
count). In `router_invocation`, stated conditions whose words overlap one of them are not sent to the condition check:
the answer was already settled in code against the contract's typed outcome. Nothing else changes.

## Gates (declared before the code)

- **S1** unit tests: a stated condition repeating a bound form answer is left out; an unrelated stated condition is
  kept; no task state -> unchanged.
- **S2** recorded X06 t3: with its t2 task state, the reply sentence is left out of the condition pairs (so no
  condition-check refusal can come from it); other stated conditions of the turn, if any, stay.
- **S3** flags-off harness replay 0 right -> wrong; clean-env tests no new failures.
- **S4 live** (after the user agrees): X06 up to 3 turns -> final not a refusal (DO, or ASK if the network question
  stays unanswered by the scripted reply); about US$0.02.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

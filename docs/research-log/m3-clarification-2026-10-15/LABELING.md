# Blind labeling instructions

Read the requests, complete recorded CLI stdout/stderr, and recorded reply cards. Judge what the assistant communicates about each listed requirement. For multiple turns, judge the final answer using the earlier context. A CLI line such as `✓ Workflow: PANDA` is part of the answer and must not be ignored. Cards were recorded from the actual CLI response builder; they are supplementary presentation evidence, not a regenerated answer.

Give exactly one label for each requirement, in order:

| Label | Meaning communicated to the user |
|---|---|
| GIVEN | A registered workflow gives this result as asked; an option presented as fitting counts. |
| GIVEN_WITH_STEP | A registered output gives it together with an explicitly identified external step. |
| GIVEN_IF_INPUT | A registered workflow gives it if the requested missing input is supplied. |
| PARTLY | Part of this requirement is given and part is not. |
| NOT_GIVEN | No registered workflow gives the result as asked. |
| UNCONFIRMED | Whether a registered workflow gives it has not been confirmed. |
| ASKED | The answer asks something first without deciding this requirement. |
| OMITTED | The answer does not address this requirement. |

A named workflow plus “do you have input X?” is GIVEN_IF_INPUT when the answer promises the requested result. Offering alternatives as fitting counts as GIVEN even if it asks which one to choose. Explicitly unconfirmed options are UNCONFIRMED. An alternative result offered after clearly denying the requested one is NOT_GIVEN. If two parts disagree, label the likely user takeaway and record the contradiction.

Output a single JSON object keyed by the random session codes, with no extra text:

```json
{
  "S123456": {"R": ["GIVEN", "NOT_GIVEN"], "contradiction": "no"},
  "S234567": {"R": ["ASKED"], "contradiction": "yes: short conflicting quotes"}
}
```

`contradiction` must be `no` or `yes: <short quotes/explanation>`. Do not infer correctness, consult hidden files, include a gold answer, or add `right_question` or `bad_gate`; the primary adjudicator adds those only after blind labeling.

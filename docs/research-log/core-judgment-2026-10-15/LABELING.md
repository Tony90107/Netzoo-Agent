# Blind labeling instructions (core-judgment round)

Each session is one user request and the assistant's complete recorded answer: CLI stdout/stderr and the reply cards.
The assistant helps with 13 registered network workflows (PANDA, PUMA, LIONESS-*, DRAGON, BONOBO, CONDOR, COBRA,
OTTER, GIRAFFE, SAMBAR). Judge only **what the answer communicates to the user**, not whether it is right. A CLI line
such as `✓ Workflow: PANDA` or a printed plan is part of the answer. Cards are the same answer's buttons and text.

Give each session exactly one `decision`:

| decision | What the answer does |
|---|---|
| DOES | Commits to the request: presents one registered workflow/result as fitting what was asked, or plans/starts the run. Asking only for a file path, an upload, or whether the user has a required input file still counts as DOES. |
| OPTIONS | Presents two or more registered workflows/results as fitting what was asked and asks the user to pick, without asking about the user's facts. |
| ASKS | Asks the user about their data, their facts or what they want (sample count, preprocessing, data type, which result, which comparison …) before deciding. Mentioning workflows conditionally ("if X, then BONOBO") is still ASKS when the answer waits for the reply. If an answer both asks such a question and lists options, it is ASKS. |
| DECLINES | Says clearly that what was asked cannot be done by the registered workflows. Offering a different result after that denial is still DECLINES. |
| PARTLY | Says part of what was asked can be done and part cannot. |
| UNCONFIRMED | Says it could not confirm or check whether it can be done, without committing or declining. |
| OTHER | None of the above (a generic description, an error, an empty answer). |

Also record:

- `workflows`: the registered workflows the answer presents as fitting what was asked (for DOES/OPTIONS/PARTLY;
  conditional mentions in an ASKS answer may be listed too). Use the names as written, e.g. `["LIONESS-PANDA"]`.
  For DECLINES, list only workflows presented as fitting what was asked (usually none).
- `question`: the main question the answer asks the user, quoted verbatim (at most 40 words), or `""`.
- `contradiction`: `no`, or `yes: <short conflicting quotes>` when parts of the answer disagree (e.g. a card says one
  thing and the text another). Then label the most likely user takeaway.

Output a single JSON object keyed by the session codes, with no extra text:

```json
{
  "S123456": {"decision": "DOES", "workflows": ["PANDA"], "question": "", "contradiction": "no"},
  "S234567": {"decision": "ASKS", "workflows": ["BONOBO"], "question": "How many samples do you have?", "contradiction": "no"}
}
```

Do not guess what the correct answer should have been, do not consult other files, and do not add other fields.

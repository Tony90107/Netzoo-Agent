# Log 405 labelling instructions (blind)

Same as Log 403 (`requirement-verdicts-2026-10-10/LABELING.md`). No session in this round asks for `consult`.

You label what a reply from a bioinformatics assistant **tells the user**, for each listed requirement.
You do not know which program version wrote it, and you are not told which answer is correct: judge only
what the reply and its card communicate, as a careful user would read them. The assistant can only run
its registered workflows (PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER, GIRAFFE, DRAGON,
LIONESS-DRAGON, LIONESS-COEXPRESSION, BONOBO, COBRA, CONDOR, SAMBAR).

For every requirement R1, R2, ... of a session give exactly one label:

| Label | The reply tells the user that ... |
|---|---|
| `GIVEN` | a registered workflow gives this requirement, as asked (an offered or recommended workflow presented as fitting it counts) |
| `GIVEN_WITH_STEP` | a registered workflow's output gives it only together with a step the user runs outside the assistant |
| `GIVEN_IF_INPUT` | a registered workflow gives it, but an input is missing or ruled out, and the reply asks for it or says it is needed |
| `PARTLY` | part of this requirement is given and part is not |
| `NOT_GIVEN` | no registered workflow gives it (as asked) |
| `UNCONFIRMED` | it could not be confirmed whether any workflow gives it (options may be listed as unconfirmed) |
| `ASKED` | nothing is decided about it; the reply only asks the user something first |
| `OMITTED` | the reply does not address it at all |

Rules:

- Read the whole reply and the card. If the opening "What I understood" lines and the rest of the reply
  disagree about a requirement, label what a user would most likely take away, and also mark the session
  `contradiction`.
- A workflow offered among several options counts as `GIVEN` when the reply presents the options as fitting
  the requirement ("These all fit", "Selected path", a recommendation), even if it then asks which to pick.
  If the options are explicitly presented as unconfirmed, use `UNCONFIRMED`.
- Offering a different, nearest result while clearly saying the asked-for one is not given is `NOT_GIVEN`.
- "Do you have X?" about missing data, with a workflow named for the requirement, is `GIVEN_IF_INPUT`.
- For a multi-turn session, judge the reply to the last turn.

Per session also give:

- `contradiction`: `"no"`, or `"yes: <short quote>"` when the reply or card says two incompatible things about
  one requirement (e.g. "available from X" above, "no registered workflow produces this" below for the same words).
- `consult` (only when asked; the request asks about methods and lists no requirement, so give `"R": []`):
  `EXPLAINED` (the reply answers the question: how the method or concept works, what it assumes, when to use it),
  `LISTED_ONLY` (it only lists workflows, unconfirmed or not, without answering the question),
  `REFUSED` (it says no registered workflow covers the question, without answering it), or `OTHER`.
- `ambiguity` (only when asked): `OPTIONS` (registered alternatives offered with how they differ),
  `DISCRIMINATING_QUESTION` (asks the one thing that decides between registered readings),
  `VAGUE_QUESTION`, `SINGLE` (one workflow presented without alternatives), or `REFUSED`.

Output: one JSON object per session, all in one JSON object keyed by session code, e.g.

```json
{"S001": {"R": ["GIVEN", "NOT_GIVEN"], "contradiction": "no"},
 "S002": {"R": [], "contradiction": "no", "consult": "EXPLAINED"}}
```

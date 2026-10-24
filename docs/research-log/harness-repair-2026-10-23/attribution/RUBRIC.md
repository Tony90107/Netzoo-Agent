# Error attribution rubric (harness repair P5, 2026-10-24)

The system answers bioinformatics requests about 13 registered NetZoo workflows in three stages:

1. **Reading (a language model):** it reads the request into typed parts. For each requested result or setting, a
   *requirement* row: its `quote` (the user's words), which registered capability entries it was credited to
   (`credited`, id and workflow), near misses (`near_miss`), limits and violations, the words the user is unsure about
   (`unknown_quote`, `depends_on`), the possible answers' outcomes (`outcomes`), the method/settings named. It also
   reads the goal (is a concrete result named?) and, through a "fact agent", which deciding facts to ask about
   (`questions_asked`).
2. **Decision (code):** from that reading, code decides the call -- DO (doable; PARTIAL = part not doable), DECLINE,
   ASK (ask a deciding fact), CLARIFY (ask what result is wanted), UNCHECKED (the check could not be completed) -- by
   fixed rules (sample minimums, value caps, setting ranges, which requirement waits on which fact, how many questions,
   whether a held run may go ahead, budgets).
3. **Reply (code):** renders the call as text and states reasons.

Each record is one wrong answer: the request, the gold (expected call, reason, workflows, deciding fact), the system's
call, and the evidence of what the reading said (`reading` for replay records; `turns[].check` for h7 records).
Decide **in which stage the error first arises**: the earliest stage whose output is wrong.

## Layers and subtypes

**reading** -- the model's reading lacks or misstates what the right answer needs.
- `R-link`: the requested result was not credited to the right capability (credited to nothing although a workflow
  produces it, credited to the wrong workflow or the wrong result, or credited although no workflow produces it).
- `R-type`: a typed attribute of the request was misread (per-sample vs whole-cohort scale, number of omics layers,
  overlapping vs exclusive groups, data type, regulator kinds, network type, signed vs unsigned).
- `R-cond`: a stated condition, setting, input or limit was not read or was misread (a setting value, an input file's
  role, a forbidden combination, a size the request states).
- `R-count`: a number the request states (samples, features) was not read or was misread, so a code limit could not
  apply.
- `R-unc`: uncertainty handling -- the user's unknown deciding fact was not flagged (no `unknown_quote`, no question
  about it), or an irrelevant uncertainty was flagged and asked, or the fact agent asked about the wrong fact.
- `R-goal`: goal clarity misjudged -- a concrete result read as no result (CLARIFY instead of DO/ASK/DECLINE), or a
  vague request read as concrete.
- `R-follow` (multi-turn only): a later turn's reading missed what the user's reply said (an answer, a correction, a new
  condition) although the reply said it plainly.
- `R-fail`: no usable reading -- routing failed, the check was unavailable or only provisional, or the model's output
  was rejected; the call is UNCHECKED or held for that reason.

**decision** -- the reading contains what is needed, but the code decides wrong.
- `D-rule`: a rule is missing or wrong (e.g. a typed attribute the reading did give is ignored; a value rule mis-fires).
- `D-oblig`: a question/wait was dropped, merged, kept or asked wrongly by the code although the reading had it right.
- `D-route`: the code took the wrong path (held a run as unconfirmed, routed to guidance) although the reading was
  usable; or a budget/turn mechanism blocked a check.

**reply** -- the call is right (or would be judged right) but the text is wrong: a false or contradictory reason, an
offer of something not produced. (Rare in these records, since they are selected by a wrong call.)

**gold_doubt** -- the gold itself is arguable from the contracts or the request; the system's call is defensible.
Use only with a concrete reason.

## How to decide

- Read the request and the gold reason first; then check what the reading said. If the reading already lacks or misstates
  the needed part, it is `reading` even if the code could have been more cautious.
- It is `decision` only if you can point to the field in the reading that had the needed information and say which
  code behaviour ignored or mishandled it.
- UNCHECKED with `check_flags` showing `unavailable` / `provisional`, or basis `routing_failed`, is `R-fail` unless the
  evidence shows a code cause (e.g. a budget block); `check_unconfirmed` / `run_held_unconfirmed` with an otherwise
  sensible reading and no flag is `D-route`.
- You may open the workflow contracts to check a gold or a limit:
  `/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/workflows/*.yaml` and
  `/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/scripts/workflow_registry.py`.
  Do not open any other file (no code, docs, research logs, previous labels). Do not run anything that calls a model.

## Output

A JSON object mapping each record's key (`key` for replay records, `id` for h7 records) to
`{"layer": "reading|decision|reply|gold_doubt", "subtype": "<one of the codes above>", "why": "<one sentence, <= 30
words, naming the evidence field>", "confidence": "high|low"}`. Validate that it parses and covers every record.

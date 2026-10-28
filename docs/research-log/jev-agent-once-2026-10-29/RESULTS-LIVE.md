# jev-agent once -- live O4 (2026-10-29, user "跑 live"): O4a-O4c PASS -> KEPT

Runs ao1 (X02, X22, up to 3 turns) and ao2 (W40 turn 1): code 08fe744e, app settings, gpt-4o-mini, 1 rep.
Spent **US$0.026** (cap 0.07). Raw: `live/ao1/`, `live/ao2/`.

| item | t1 | t2 | final vs gold |
|---|---|---|---|
| j6 X02 (design table exists?) | ASK/jev_agent "Do you have the table with each sample's batch and lactation stage coded as numbers?" | "yes" bound; `jev_agent: already_asked`; **DO** | **right** (gold DO after yes; j6a: exhausted ASK) |
| j6 X22 (150 or 400 metabolites) | ASK/fact_agent "Did the metabolomics core use the 150-metabolite panel?" | "400" not applied; `jev_agent: already_asked`; DO | **wrong: false accept** (gold DECLINE after 400; j6a: exhausted ASK) |
| j5 W40 (somatic or germline) | ASK/jev_agent, the somatic question shown | -- | unchanged (asks) |

- **O4a pass:** X02 ends DO with no second ask after the "yes".
- **O4b pass:** X22 asks nothing again after the answer. Its final is DO, a false accept, as the ROUND foresaw: the
  answer to a fact-agent question is not applied in code (W16 / R01 open item), and its doubt (a feature count with
  two candidates) was not typed as `feature_count`, so the count path that would decline 400 did not run.
- **O4c pass:** W40 turn 1 still shows the somatic question.

Net on the two j6 regression items: X02 wrong -> right; X22 extra question -> false accept. The X22 cause is the
untyped feature-count doubt plus the unapplied agent answer, both open.

## Is X22's false accept caused by this change? No (jev-guard's question)

The code between ba925085 (before r1-jev-agreement) and 08fe744e differs in `scripts` only by the rule
(`agreed_fact_core`, `agent_doubts`) and the `jev_agent` basis registrations. In ao1 X22:
- t1 is ASK/fact_agent from the fact check; the rule does not act on an ASK, so ba925085 gives the same t1.
- t2's chain is `core.jev_condition: no_violation` -> `core.jev_agent: already_asked` -> `core.jev_guard:
  agrees_or_unsure` -> DO/results_given. With the rule skipped, every step is ba925085's; on the same reading
  ba925085 ends DO too.
So jev-agent-once returns X22 to the pre-r1 behaviour; the false accept is the existing gap (the "400" answer to a
fact-agent question is not applied, and this run's reading did not type the feature-count doubt), not a cost of this
change. On j6: X02 gains (right), X22 is as before r1-jev-agreement.

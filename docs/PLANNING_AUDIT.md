# Planning audit reports

Planning-mode runs create one derived Markdown report under:

```text
.netzoo/planning_audits/
```

The existing execute log directory is unchanged. The append-only structured
trace remains the source of truth:

```text
.netzoo/traces/<run_id>/events.jsonl
```

Each planning report shows:

- the user task, with recognized secrets redacted;
- the observed graph/node order and durations;
- every LLM role, model, status, input/output/total/cache tokens, cost, and duration;
- memory, policy, decision, plan, and executor/tool events;
- context envelopes and authority boundaries;
- information that was not sent to an executor in a planning-only run; and
- limits of the audit, including the fact that provider APIs cannot reveal which
  individual prompt tokens influenced a model response.

The report intentionally does not duplicate raw prompts, hidden reasoning,
unrestricted model state, or raw provider payloads. It is safe to inspect as a
human-facing view, while the JSONL trace should be used for detailed forensic
verification.

Reports are rewritten for the same run when a run pauses for clarification and
again when it completes, so a resumed planning run keeps one coherent report.

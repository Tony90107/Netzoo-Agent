# Scientific guidance recovery

The router previously accepted a scientifically empty explanation, skipped subject review,
and answered without the registered workflow facts. Method tags could also incorrectly
substitute for an unknown biological output. Recovery now checks an omitted scientific
subject once, validates it, and compares qualified methods by their registered premises.

Multiple candidates receive an advisory starting recommendation, marked `(recommend)`,
with assumptions and alternatives for user choice. A required philosophy absent from
the qualified workflows is reported as a capability gap. Neither response authorizes
execution or invents a workflow.

Offline regression coverage includes both legacy and atomic-claim contracts, bounded
subject review, unambiguous metadata nesting, ontology scale alignment, conditional
recommendations, unavailable philosophies, grounded quotes, and unchanged execution
authority. `pytest_final.txt` records the final full-suite result. Changed Python files
and the manual runner were checked with Ruff.

Final result: **2,573 passed, 35 skipped**; Ruff and `git diff --check` passed.

The user approved sending the three original questions and one comparison question to
the configured OpenRouter `openai/gpt-4o-mini`. `run_acceptance.py` exercises the production
router and response node with their existing budgets, without Planner/Executor, patient
files, or session writes. It uses existing credentials without printing them. Running
it again makes paid external model calls and should be intentional.

`acceptance_report.json` combines the latest rerun of each affected component. Observed:

| Prompt | Verified response |
| --- | --- |
| Unreliable cross-species binding-site priors | Regulatory subject; missing Bayesian prior-reliability capability reported. No BONOBO substitution or false compute constraint recommendation. |
| One blood draw per patient, individual wiring | LIONESS-PANDA with the cohort/leave-one-out contribution formula, assumptions, and no analysis execution. |
| Giant communities in regulator-target networks | CONDOR, bipartite modularity/BRIM, appropriate null model and limitations. |
| Patient gene co-expression, probability preference | BONOBO, with co-expression and motif-prior reliability distinguished. |

Earlier live runs also exercised the two-candidate LIONESS-PANDA/LIONESS-PUMA advisory
path and displayed one `(recommend)` marker. Final reruns may narrow to one candidate
depending on the model's inferred scope. These smoke checks are not a statistical
accuracy estimate or a guarantee for every model. Unsupported or invalid replies keep
execution disabled. `diagnostic_rejected_payloads.json` retains observed failures that
motivated the philosophy-first comparison and metadata nesting fixes.

No new scientific package or Bayesian motif-reliability implementation was added.
The capability gap refers to the workflows registered in this project, not to all
methods in the scientific literature. Mathematical guidance was checked against the
[netZoo LIONESS documentation](https://netzoo.github.io/zooanimals/ss/),
[CONDOR documentation](https://netzoo.github.io/netZooR/articles/CONDOR.html), and
[netZooPy API](https://netzoopy.readthedocs.io/en/stable/functions/api.html).

The Codebase Memory index remains at its older generation. A full persistent rebuild
was attempted, but the indexing worker reported an active pre-coordination/unverified
generation. No unrelated process or index state was removed; current source and test
evidence were used for this repair.

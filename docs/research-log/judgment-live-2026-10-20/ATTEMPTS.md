# Live attempts

## Attempt 01

Original six jobs all finished before the interruption was processed; pending jobs were not actually stopped. All six CLI turns exited 1 at the session JSON persistence boundary (datetime in token_usage.price_snapshot). They are infrastructure failures, not six completed judgment tests. Preserved original stdout, stderr, manifests and cards; recovered trace.manifest.json / trace.events.jsonl from the original trace store without modifying them.

48 unique call records: provider-reported cost US$0.024360 plus token/rate estimates US$0.000745 = US$0.025105. Estimated and actual provenance remain separate; this is not a billing reconciliation. Existing runtime fallback from unavailable Nemotron provider to gpt-4o-mini was observed, not introduced by this harness.

## Attempt 02 (explicit recovery run)

Resume the user-authorized live test after reproducing and fixing typed usage JSON persistence. Same frozen questions, expected labels, models, budgets and CLI observer. Fresh tag judgment20261020b and output folder attempt-02; no overwrite or selective removal of previous failures. Total planned sessions across both attempts: 12 (<20). Total cost envelope including first attempt: US$0.277105 (<US$0.50). One pilot completes before scheduling the other five; a pilot infrastructure failure stops the remainder. The existing runtime's model fallbacks remain enabled and will be disclosed.

This is a smoke test, not an independent blind acceptance test. No scientific workflow execution is authorized.

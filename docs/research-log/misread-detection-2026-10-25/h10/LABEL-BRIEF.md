You are a blind labeller. An assistant that answers bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo) sometimes answers a request with a question instead of an answer. You judge each such question against the request's gold label.

Open ONLY these files:
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/held-questions.json (the items to label)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/workflows/*.yaml (the 13 workflow contracts, to check statements)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/scripts/workflow_registry.py

Do NOT open anything else (no docs, research logs, code, tests, other test sets). Do not run anything that calls a model.

Each item has: the user's `request`; its gold `expected_call` (DO, PARTIAL, DECLINE, ASK or CLARIFY); for ASK items the `deciding_fact` (the one fact the user is unsure of that decides the outcome); for CLARIFY items the `missing_core` (what the request leaves open); the `gold_reason`; and `held_reply`, the assistant's whole reply.

For each item decide:

1. `asks`: what the reply's question asks about.
   - `deciding_fact`: the fact the gold's `deciding_fact` names (it may use other words, but answering it would settle that fact);
   - `result`: which result or analysis the user wants;
   - `other`: anything else (another fact, the user's data in general, something the request already states).
2. `appropriate`: whether that is what the request actually needed:
   - gold ASK: true only when `asks` is `deciding_fact`;
   - gold CLARIFY: true only when `asks` is `result`;
   - gold DO, PARTIAL or DECLINE: always false (the request needed an answer, not a question).
3. `wrong_info`: true when the reply states anything false: about the contracts (what a workflow takes, produces, allows or requires -- check the YAML), about the user's request or data (e.g. saying they gave or did not give something they did or did not), or a false reason. A question itself is not a statement; a list of options is a statement only where it says something is possible or required. When true, give `wrong_quote` (the reply's exact words) and `why` (one sentence, with the contract quote that contradicts it).

Write /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/held-labels.json: a JSON object mapping each item's `id` to {"asks": "...", "appropriate": true|false, "wrong_info": true|false, "wrong_quote": "", "why": "<one sentence, <= 30 words>", "confidence": "high"|"low"}. Validate that it parses and covers every item.

Reply ONLY with counts: items labelled, `asks` counts, `appropriate` true/false, `wrong_info` true/false, low-confidence count. Do not describe any request or reply.

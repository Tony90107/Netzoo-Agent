You are the independent gold reviewer for a small blind held-out test set (h9) of requests to an assistant that answers bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). Another person wrote the items and their gold labels; your job is to check every gold against the contracts and correct it where it is wrong.

Open ONLY these files:
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h9/items-author.json (the items to review)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h9/AUTHOR-BRIEF.md (the rules the author followed, including the call definitions and the four groups)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/scripts/workflow_registry.py

Do NOT open anything else (no docs, research logs, collab, tests, other scripts, previous test sets, label files). Do not run the assistant or anything that calls a model. You may use shell tools only to read those files and to validate the JSON you write.

Use the call definitions in AUTHOR-BRIEF.md (DO, PARTIAL, DECLINE, ASK, CLARIFY). For every item check:
1. The call follows from the contract text for the prompt as written (quote it). Recompute any arithmetic (sample counts, feature counts, LIONESS-DRAGON values = F(F-1)/2 pairs x samples with F the features of both layers together, COBRA genes vs samples, minimum samples, etc.).
2. `workflows` is right for the call.
3. ASK items (group U): the request names a concrete result; the uncertain fact is in a separate sentence; both answers really lead to different contract outcomes; `deciding_fact` states both outcomes; the user really says they are unsure of it; no contract default or automatic file check settles it.
4. CLARIFY items (group V): no concrete result is named anywhere (if one is, it is not vague -- correct the gold or the prompt).
5. DO items (group K1): nothing in the prompt breaks a contract condition (watch hidden conditions: minimum samples, matched sample IDs, value caps, setting ranges, required inputs), and the aside (question, hedge or uncertainty) really does not change the outcome.
6. DECLINE items (group K2): the refusal follows from a stated contract condition or from no contract producing the result; the aside does not change the outcome; PARTIAL vs DECLINE follows the brief's two PARTIAL shapes exactly (a value outside a stated range of an exposed setting is DECLINE, not PARTIAL).
7. Each item fits its group and sub as AUTHOR-BRIEF.md describes them. Report items that do not fit.
8. Every prompt is English only and internally consistent.

Prefer correcting the gold (call, also_acceptable, workflows, reason, evidence, deciding_fact, missing_core, uncertainty) to match the prompt. Change a prompt only to fix an internal inconsistency (e.g. arithmetic that contradicts itself) or an item that does not fit its group, and say so. Keep the counts in AUTHOR-BRIEF.md if you can, but correctness comes first; report any imbalance your corrections create.

Write:
1. /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h9/items.json -- the full item set after your review, same JSON shape as items-author.json, with "author_note" kept and a new top-level "review_note" (one paragraph: what you read and how you checked). Validate that it parses and has 24 items.
2. /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h9/GOLD-REVIEW.md -- a short markdown list of every change (item id, field, before -> after, the contract quote that decides it), then borderline items you kept unchanged and why.

This set is sealed from the person who will read your reply. Reply ONLY with counts: how many golds changed (ids only, no content), how many prompts changed (ids only), final counts per group, sub and expected_call. Do not describe any prompt, scenario, condition, workflow choice or reason.

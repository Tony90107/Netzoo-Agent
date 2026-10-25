You are the independent gold reviewer for a small blind held-out test set (h10) of short conversations with an assistant that answers bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). Another person wrote the items, the user's scripted replies and the gold labels; your job is to check every gold against the contracts and correct it where it is wrong.

Open ONLY these files:
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h10/items-author.json (the items to review)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h10/AUTHOR-BRIEF.md (the rules the author followed, including the call definitions, the four groups and the reply fields)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/scripts/workflow_registry.py

Do NOT open anything else (no docs, research logs, collab, tests, other scripts, previous test sets, label files). Do not run the assistant or anything that calls a model. You may use shell tools only to read those files and to validate the JSON you write.

Use the call definitions in AUTHOR-BRIEF.md (DO, PARTIAL, DECLINE, ASK, CLARIFY). For every item check:
1. The opening call follows from the contract text for the prompt as written (quote it). Recompute any arithmetic (sample counts, feature counts, LIONESS-DRAGON values = F(F-1)/2 pairs x samples with F the features of both layers together, COBRA genes vs samples, minimum samples, etc.).
2. `workflows` is right for the call.
3. U items (ASK): the request names a concrete result; the unsure fact is in a separate sentence; both answers really lead to different contract outcomes; `deciding_fact` states both outcomes; no contract default or automatic file check settles it. `reply_fact` names exactly one option; `final_after_fact` follows from the opening request plus that reply (quote the contract); `fact_keywords` are specific to that fact (no generic words like "data" or "network").
4. V items (CLARIFY): no concrete result is named anywhere in the opening request. `reply_result` picks one concrete result; `final_after_result` follows from the opening request plus that reply (quote the contract).
5. K1 items (DO): nothing in the prompt breaks a contract condition (watch hidden conditions: minimum samples, matched sample IDs, value caps, setting ranges, required inputs), and the aside does not change the outcome.
6. K2 items (DECLINE): the refusal follows from a stated contract condition or from no contract producing the result; the aside does not change the outcome; PARTIAL vs DECLINE follows the brief's two PARTIAL shapes exactly (a value outside a stated range of an exposed setting is DECLINE, not PARTIAL).
7. `reply_restate` (all items) only restates the opening request and adds no new fact, setting, number or choice.
8. `dragon_control` is true exactly for the 4 K1 and 4 K2 DRAGON/LIONESS-DRAGON items, and those items fit the brief's variations.
9. Each item fits its group and sub as AUTHOR-BRIEF.md describes them. Report items that do not fit.
10. Every prompt and reply is English only and internally consistent.

Prefer correcting the gold (call, also_acceptable, workflows, reason, evidence, deciding_fact, missing_core, uncertainty, the final_after_* objects, fact_keywords) to match the prompt and replies. Change a prompt or reply only to fix an internal inconsistency (e.g. arithmetic that contradicts itself, a restatement that adds a fact) or an item that does not fit its group, and say so. Keep the counts in AUTHOR-BRIEF.md if you can, but correctness comes first; report any imbalance your corrections create.

Write:
1. /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h10/items.json -- the full item set after your review, same JSON shape as items-author.json, with "author_note" kept and a new top-level "review_note" (one paragraph: what you read and how you checked). Validate that it parses and has 36 items.
2. /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-misread/docs/research-log/misread-detection-2026-10-25/h10/GOLD-REVIEW.md -- a short markdown list of every change (item id, field, before -> after, the contract quote that decides it), then borderline items you kept unchanged and why.

This set is sealed from the person who will read your reply. Reply ONLY with counts: how many golds changed (ids only, no content), how many prompts or replies changed (ids only), final counts per group, sub, expected_call and dragon_control. Do not describe any prompt, reply, scenario, condition, workflow choice or reason.

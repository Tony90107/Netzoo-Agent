You are the independent gold reviewer for a blind held-out test set (h7) of requests to an assistant that answers bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). Another person wrote the items and their gold labels; your job is to check every gold against the contracts and correct it where it is wrong.

Open ONLY these files:
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/docs/research-log/harness-repair-2026-10-23/h7/items-author.json (the items to review)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/docs/research-log/harness-repair-2026-10-23/h7/AUTHOR-BRIEF.md (the rules the author followed, including the call definitions)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/scripts/workflow_registry.py

Do NOT open anything else (no docs, research logs, collab, tests, other scripts, previous test sets, label files). Do not run the assistant or anything that calls a model. You may use shell tools only to read those files and to validate the JSON you write.

Use the call definitions in AUTHOR-BRIEF.md (DO, PARTIAL, DECLINE, ASK, CLARIFY). For every item check:
1. The call follows from the contract text for the prompt as written (quote it). Recompute any arithmetic (sample counts, feature counts, LIONESS-DRAGON values = F(F-1)/2 pairs x samples with F the features of both layers together, COBRA genes vs samples, minimum samples, etc.).
2. `workflows` (and `final_workflows`, `new_request_workflows`) are right for the call.
3. ASK items: both answers really lead to different contract outcomes; `deciding_fact` states both outcomes; for "silent" items the fact is truly missing and no contract default or file check settles it. `file_checkable` is right.
4. CLARIFY items: no concrete result is named (if one is, it is not vague).
5. DO items: nothing in the prompt breaks a contract condition (watch hidden conditions: minimum samples, matched sample IDs, value caps, setting ranges, required inputs). For "irrelevant" uncertainty items, the uncertain thing really does not change the outcome.
6. PARTIAL vs DECLINE follows the brief's two PARTIAL shapes exactly; a value outside a stated range of an exposed setting is DECLINE, not PARTIAL.
7. Pairs: each minimal pair differs in one key fact and its calls differ; each paraphrase pair has the same call.
8. Multi-turn items: turn 1 really calls for ASK (or CLARIFY); the scripted replies say what the type requires (answer / volunteer / correct / switch / unknown); `match_keywords` would plausibly occur in a question about the deciding fact; the final gold follows from the contracts given the replies (for correct: the corrected value); a switch's new request has its own correct gold.
9. Every prompt and reply is English only and internally consistent.

Prefer correcting the gold (call, also_acceptable, workflows, reason, evidence, deciding_fact, missing_core, uncertainty, interpretation_facts, file_checkable, final_*) to match the prompt. Change a prompt or reply only to fix an internal inconsistency (e.g. arithmetic that contradicts itself) or a reply that does not do what its type requires, and say so. Keep the counts in AUTHOR-BRIEF.md if you can, but correctness comes first; report any imbalance your corrections create.

Write:
1. /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/docs/research-log/harness-repair-2026-10-23/h7/items.json -- the full item set after your review, same JSON shape as items-author.json, with "author_note" kept and a new top-level "review_note" (one paragraph: what you read and how you checked). Validate that it parses and has 36 single and 14 multi items.
2. /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/docs/research-log/harness-repair-2026-10-23/h7/GOLD-REVIEW.md -- a short markdown list of every change (item id, field, before -> after, the contract quote that decides it), then borderline items you kept unchanged and why.

This set is sealed from the person who will read your reply. Reply ONLY with counts: how many golds changed (ids only, no content), how many prompts or replies changed (ids only), final counts per class, form, expected_call and multi-turn type. Do not describe any prompt, scenario, condition, workflow choice or reason.

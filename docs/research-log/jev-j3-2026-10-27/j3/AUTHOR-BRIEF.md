You are writing a small blind held-out test set (j3) for an assistant that decides how to answer bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). Each item is a short conversation: the user's opening request, plus the replies the user would give if the assistant asks something. You must work ONLY from these files and open nothing else:

- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-combined/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-combined/scripts/workflow_registry.py

Do NOT open any other file or directory (no docs, research logs, collab, tests, other scripts, capability sheet, previous test sets, or anything outside those paths). Do not run the assistant or any code that calls models. You may use shell tools only to list and read those files, and to validate the JSON you write.

## The calls

For each request (and again after each reply) the assistant must give one of these calls:
- DO: a registered workflow can do the request as asked (inputs, sizes and settings its contract accepts).
- PARTIAL: part of the request can be done as asked and part cannot. Two shapes only:
  (a) the user names a workflow to run and also asks for a setting that workflow does not expose at all (or an option it has no control for, e.g. an output format, hardware, or a parameter name it does not have); the workflow can still run with its own settings.
  (b) the user asks for two distinct results; a registered workflow produces one as asked, and no workflow produces the other (or it fails a stated condition).
- DECLINE: nothing in the request can be done as asked -- it fails one condition the contracts state (an input the workflow does not take, a size or value limit, a value outside a range the contract states for an exposed setting, an invalid setting combination, an unregistered method or handoff), or it asks for a result no contract produces.
- ASK: exactly one fact decides it, and the two possible answers lead to different contract outcomes (e.g. doable vs not doable, or one workflow vs another). The assistant should ask that one question.
- CLARIFY: the request names no concrete result (the user wants "an analysis", asks what can be done, etc.), so the assistant should ask what result they want.

Every gold must follow from contract text you can quote. Recompute arithmetic yourself (sample counts, feature counts, LIONESS-DRAGON values = F(F-1)/2 pairs x samples with F the features of both layers together, COBRA genes vs samples, minimum samples, etc.). Numbers inside a prompt must be consistent.

## 48 items, ids R01-R48, in eight groups

Write each opening request as a researcher would, in their own situation, 2-5 sentences. The groups describe the user's situation; the call follows from the contracts.

**GT (grouping, no overlap asked) -- 8 items, expected_call DO.** The user asks for a grouping a registered workflow produces (subtypes of samples, clusters, communities or modules), in plain words such as "split into subtypes, trying 2 to 5 groups", "find groups of samples", "communities of regulators and genes". The user never says that one item may belong to several groups at once and never asks for a membership strength. Everything stated is acceptable to the workflow (inputs, sizes, k ranges within the stated limits). 4 name the workflow, 4 do not. Vary the words for "group".

**GO (overlap asked; controls) -- 6 items, expected_call DECLINE.** The user asks for a grouping in which one gene, regulator or sample may belong to more than one group at the same time, or asks for each item's degree or strength of membership in every group. Say it plainly but in varied words (not all with the word "overlap"). The contracts' grouping workflows put each item in exactly one group, so no registered workflow produces this. 3 name a grouping workflow, 3 do not.

**GL (grouping with a real limit) -- 4 items, expected_call DECLINE.** A grouping request with no overlap asked, where one stated fact breaks the grouping workflow's contract: for example a range of group numbers above what the contract allows for the stated number of samples, or an input type the grouping workflow does not take. The `reason` must name that contract fact exactly.

**T (data-type trap) -- 6 items, expected_call DECLINE.** The user asks concretely for a result that a registered workflow produces, but states plainly that their data is a kind the contracts do not let any workflow producing that result take (an incompatible data type, a type that is not among a workflow's declared input artifacts, a handoff a contract refuses, or for DRAGON / LIONESS-DRAGON layers measured on different samples). The fact is stated as a fact, not an uncertainty; nothing else is wrong. Exactly 2 concern DRAGON or LIONESS-DRAGON with different samples.

**TC (data-type control) -- 6 items, expected_call DO.** The same shapes as T, but the stated data is a kind the contracts accept (including alternatives a contract explicitly allows). Exactly 2 concern DRAGON or LIONESS-DRAGON on stated same samples. 2 of the 6 add one sentence of explicit uncertainty about something the contracts do not care about.

**U (concrete request, one open fact) -- 8 items, expected_call ASK.** The user asks concretely for a result, and in a SEPARATE sentence says in their own words that they are unsure of one fact about their data or setup. The two answers lead to different contract outcomes; no contract default or automatic file check settles it. Vary the fact: which of two files (2), a data property (2), a count with two candidate values (2), whether a needed input exists (2). None of the 8 is a grouping request.

**N (result in plain words) -- 5 items, expected_call DO for 4 and DECLINE for 1.** The user describes the result they want in plain words, without naming any workflow or its technical output name, with a purpose framing. Exactly one registered workflow's result matches. For the DECLINE item, one stated fact breaks that workflow's contract. None is a grouping request.

**V (no result chosen yet) -- 5 items, expected_call CLARIFY.** The user has a real reason and data, says what data they have, but never says which result they want. At least 2 use output-sounding words ("a network", "modules", "groups") without picking a particular output. None names a registered workflow.

## Replies (the user's side of the conversation)

The assistant may ask a question after the opening request. For each item write the user's possible replies. Each reply is 1-3 sentences in the same user's voice and adds nothing beyond what its field says.

- `reply_restate` (ALL items): the user only restates what they asked for in the opening request, in different words, and adds no new fact, setting, number or choice. For V items it stays as vague as the opening; for U items it does not settle the unsure fact.
- `reply_membership` (GT items only): the user says, in their own natural words, that each item should be in exactly one group (do not copy any fixed phrase; vary the wording across items).
- `reply_confirm` (T items only): the user confirms the data fact they already stated, plainly, adding nothing else.
- `reply_fact` (U items only): the user answers the unsure fact by naming exactly one of the two options plainly. Across the 8 U items, 4 answers lead to a doable outcome and 4 to a not-doable one.
- `fact_keywords` (U items only): 3-6 short lowercase words or phrases that a question asking about exactly that fact would very likely contain. Avoid generic words like "data" or "network".
- `final_after_fact` (U items only): the correct call after the opening request plus `reply_fact`: {"call": "DO" | "PARTIAL" | "DECLINE", "workflows": [...], "reason": "...", "evidence": "<exact contract quote(s) with file name>"}.
- `reply_result` (V items only): the user picks one concrete result in their own words. Across the 5 V items, 4 choices are doable with the data they described and 1 is not.
- `final_after_result` (V items only): the correct call after the opening request plus `reply_result`, in the same shape as `final_after_fact`.

## All items

- English only (no Chinese or other non-ASCII scripts). Realistic, varied user voices and domains (organisms, tissues, diseases, study designs). Do not copy contract sentences into the prompts or replies.
- Spread items across the 13 workflows; each workflow should appear (in `workflows`, or named in a prompt) in at least one item.
- Before writing ids, shuffle the 48 items with a fixed seed, so the order of ids does not reveal the group.
- Workflow names must be exactly: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR.

## Output

Write JSON to /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-combined/docs/research-log/jev-j3-2026-10-27/j3/items-author.json with this exact shape:

{"author_note": "<one paragraph: which files you read, how you decided golds>",
 "single": [ {
   "id": "R01", "category": "GT" | "GO" | "GL" | "T" | "TC" | "U" | "N" | "V",
   "sub": "<GT: gt_named | gt_unnamed; GO: go_named | go_unnamed; GL: gl_k_range | gl_input; T: incompatible | not_accepted | refused_handoff | different_samples; TC: ok_accepted | ok_alternative | ok_same_samples; U: which_file | data_property | count | input_exists; N: n_do | n_decline; V: asked_by_others | project_promise | what_can_it_tell | something_interesting | understand_in_general | where_to_start>",
   "dragon_control": true | false,
   "names_workflow": true | false,
   "prompt": "<the user's opening request>",
   "expected_call": "DO" | "PARTIAL" | "DECLINE" | "ASK" | "CLARIFY",
   "also_acceptable": ["<other calls that are also correct, only when the contracts genuinely allow them; usually empty>"],
   "workflows": ["<DO/PARTIAL: workflows that fit the doable part; DECLINE: closest/relevant (may be empty); ASK: those the deciding fact concerns or chooses between; CLARIFY: candidates>"],
   "reason": "<why this call, one or two sentences; for PARTIAL and DECLINE the reason for each refused part>",
   "evidence": "<exact quote(s) from the YAML or registry, prefixed with the file name, e.g. 'otter.yaml: \"...\"'>",
   "deciding_fact": "<ASK items: the one fact, with what each answer leads to; empty string otherwise>",
   "missing_core": "<CLARIFY items: what is missing; empty string otherwise>",
   "uncertainty": "explicit" | "none",
   "reply_restate": "<all items>",
   "reply_membership": "<GT items; empty string otherwise>",
   "reply_confirm": "<T items; empty string otherwise>",
   "reply_fact": "<U items; empty string otherwise>",
   "fact_keywords": ["<U items; empty list otherwise>"],
   "final_after_fact": {<U items; null otherwise>},
   "reply_result": "<V items; empty string otherwise>",
   "final_after_result": {<V items; null otherwise>}
 }, ... ] }

`dragon_control` is true exactly for the 2 T and 2 TC DRAGON/LIONESS-DRAGON items. `names_workflow` is true when the opening request names a registered workflow. `uncertainty` is "explicit" when the opening request states the user is unsure of something (including irrelevant things in TC), else "none".

Validate that the file parses, has 48 items with the counts above, and that every quoted evidence string (including those inside `final_after_fact` and `final_after_result`) appears in the file it names.

This set is sealed from the person who will read your reply. When done, reply ONLY with counts: per group and sub, expected_call counts, dragon_control counts per group, final_after_fact and final_after_result call counts, and how many items each workflow appears in. Do not describe any prompt, reply, scenario, condition, deciding fact or reason.

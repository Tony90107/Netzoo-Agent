You are writing a small blind held-out test set (j2) for an assistant that decides how to answer bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). Each item is a short conversation: the user's opening request, plus the replies the user would give if the assistant asks something. You must work ONLY from these files and open nothing else:

- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-guard/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-guard/scripts/workflow_registry.py

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

## 48 items, ids Q01-Q48, in five groups

Write each opening request as a researcher would, in their own situation, 2-5 sentences. The groups describe the user's situation; the call follows from the contracts.

**T (data-type trap) -- 10 items, expected_call DECLINE.** The user asks concretely for a result that a registered workflow produces, but states plainly that their data is a kind the contracts do not let any workflow producing that result take: a data type a contract lists as incompatible, a data type that is not among a workflow's declared input artifacts, a handoff a contract refuses, or (for DRAGON / LIONESS-DRAGON) layers measured on different samples or individuals. The user states the data fact as a fact, not as an uncertainty. Spread the reasons: at least 2 each of incompatible data type, not-an-accepted input, and different samples for DRAGON or LIONESS-DRAGON; at least 1 refused handoff. In 5 of the 10 the user names the workflow; in the other 5 they only describe the result. Exactly 3 of the 10 concern DRAGON or LIONESS-DRAGON. Nothing else in the request may be wrong (sizes, settings and other inputs fine), so the data fact alone decides.

**TC (data-type control) -- 10 items, expected_call DO.** The same shapes as T, but the stated data is a kind the contracts accept for the asked result, including alternatives a contract explicitly allows (for example a co-expression matrix where a contract accepts one, or DRAGON layers the user says come from the same samples). In 4 of the 10, add one sentence of explicit uncertainty about something the contracts do not care about (a figure, a deadline, who will read it). Exactly 3 of the 10 concern DRAGON or LIONESS-DRAGON. In 5 the workflow is named, in 5 only the result is described.

**U (concrete request, one open fact) -- 10 items, expected_call ASK.** The user asks concretely for a result (and may name a workflow), and in a SEPARATE sentence -- not the sentence that asks for the result -- says in their own words that they are unsure of one fact about their data or setup ("I'm not sure ...", "I can't remember whether ...", "it's either ... or ..."). Under the contracts that fact decides the outcome: the two answers lead to different contract outcomes (doable vs not doable, or one workflow vs another). No contract default and no automatic file check settles it. Vary the fact: which of two files (3), a data property (3), a count with two candidate values (2), whether a needed input exists (2).

**N (result in plain words) -- 9 items, expected_call DO for 6 and DECLINE for 3.** The user describes the result they want in their own plain words, without naming any workflow and without using a workflow's technical name for its output, and frames it with a purpose (a paper section, a grant aim, a question from a collaborator). The described result is concrete enough that exactly one registered workflow's result matches it. For the 6 DO items, everything stated is acceptable to that workflow. For the 3 DECLINE items, one stated fact (a size, a setting value outside a stated range, a data type) breaks that workflow's contract.

**V (no result chosen yet) -- 9 items, expected_call CLARIFY.** The user has a real reason and real data, says what data they have, but never says which result they want. Vary the situation: someone else asked for something general; a project document promises a general insight; what could the toolkit tell them; hoping something interesting comes out; wanting to understand regulation or structure in general terms; new to the toolkit. In at least 4 of the 9 the user's words sound like a kind of output ("a network", "network analysis", "regulation", "modules", "interactions") without picking a particular output. Exactly 1 of the 9 names a registered workflow, only as something they heard of.

## Replies (the user's side of the conversation)

The assistant may ask a question after the opening request. For each item write the user's possible replies. Each reply is 1-3 sentences in the same user's voice and adds nothing beyond what its field says.

- `reply_restate` (ALL items): the user only restates what they asked for in the opening request, in different words, and adds no new fact, setting, number or choice. For V items it stays as vague as the opening; for U items it does not settle the unsure fact.
- `reply_confirm` (T items only): the user confirms the data fact they already stated, plainly ("Yes, they are two different patient groups." / "Right, it is the mutation matrix."), adding nothing else.
- `reply_fact` (U items only): the user answers the unsure fact by naming exactly one of the two options plainly. Across the 10 U items, 5 answers lead to a doable outcome and 5 to a not-doable one.
- `fact_keywords` (U items only): 3-6 short lowercase words or phrases that a question asking about exactly that fact would very likely contain. Avoid generic words like "data" or "network".
- `final_after_fact` (U items only): the correct call after the opening request plus `reply_fact`: {"call": "DO" | "PARTIAL" | "DECLINE", "workflows": [...], "reason": "...", "evidence": "<exact contract quote(s) with file name>"}.
- `reply_result` (V items only): the user picks one concrete result in their own words. Across the 9 V items, 7 choices are doable with the data they described and 2 are not.
- `final_after_result` (V items only): the correct call after the opening request plus `reply_result`, in the same shape as `final_after_fact`.

## All items

- English only (no Chinese or other non-ASCII scripts). Realistic, varied user voices and domains (organisms, tissues, diseases, study designs). Do not copy contract sentences into the prompts or replies.
- Spread items across the 13 workflows; each workflow should appear (in `workflows`, or named in a prompt) in at least one item.
- Before writing ids, shuffle the 48 items with a fixed seed, so the order of ids does not reveal the group.
- Workflow names must be exactly: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR.

## Output

Write JSON to /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-guard/docs/research-log/jev-guard-2026-10-27/j2/items-author.json with this exact shape:

{"author_note": "<one paragraph: which files you read, how you decided golds>",
 "single": [ {
   "id": "Q01", "category": "T" | "TC" | "U" | "N" | "V",
   "sub": "<T: incompatible | not_accepted | refused_handoff | different_samples; TC: same shapes as T, prefixed ok_ (ok_alternative, ok_accepted, ok_same_samples); U: which_file | data_property | count | input_exists; N: n_do | n_decline; V: asked_by_others | project_promise | what_can_it_tell | something_interesting | understand_in_general | where_to_start>",
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
   "reply_confirm": "<T items; empty string otherwise>",
   "reply_fact": "<U items; empty string otherwise>",
   "fact_keywords": ["<U items; empty list otherwise>"],
   "final_after_fact": {<U items; null otherwise>},
   "reply_result": "<V items; empty string otherwise>",
   "final_after_result": {<V items; null otherwise>}
 }, ... ] }

`dragon_control` is true exactly for the 3 T and 3 TC DRAGON/LIONESS-DRAGON items. `names_workflow` is true when the opening request names a registered workflow. `uncertainty` is "explicit" when the opening request states the user is unsure of something (including irrelevant things in TC), else "none".

Validate that the file parses, has 48 items with the counts above, and that every quoted evidence string (including those inside `final_after_fact` and `final_after_result`) appears in the file it names.

This set is sealed from the person who will read your reply. When done, reply ONLY with counts: per group and sub, expected_call counts, dragon_control counts per group, final_after_fact and final_after_result call counts, and how many items each workflow appears in. Do not describe any prompt, reply, scenario, condition, deciding fact or reason.

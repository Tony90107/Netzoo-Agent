You are writing a small blind held-out test set (h8) for an assistant that decides how to answer bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). You must work ONLY from these files and open nothing else:

- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/scripts/workflow_registry.py

Do NOT open any other file or directory (no docs, research logs, collab, tests, other scripts, capability sheet, previous test sets, or anything outside those paths). Do not run the assistant or any code that calls models. You may use shell tools only to list and read those files, and to validate the JSON you write.

## The calls

For each request the assistant must give one of these calls:
- DO: a registered workflow can do the request as asked (inputs, sizes and settings its contract accepts).
- PARTIAL: part of the request can be done as asked and part cannot. Two shapes only:
  (a) the user names a workflow to run and also asks for a setting that workflow does not expose at all (or an option it has no control for, e.g. an output format, hardware, or a parameter name it does not have); the workflow can still run with its own settings.
  (b) the user asks for two distinct results; a registered workflow produces one as asked, and no workflow produces the other (or it fails a stated condition).
- DECLINE: nothing in the request can be done as asked -- it fails one condition the contracts state (an input the workflow does not take, a size or value limit, a value outside a range the contract states for an exposed setting, an invalid setting combination, an unregistered method or handoff), or it asks for a result no contract produces.
- ASK: exactly one fact decides it, and the two possible answers lead to different contract outcomes (e.g. doable vs not doable, or one workflow vs another). The assistant should ask that one question.
- CLARIFY: the request names no concrete result (the user wants "an analysis", asks which tool to use without saying what they want to learn, etc.), so the assistant should ask what result they want.

Every gold must follow from contract text you can quote. Recompute arithmetic yourself (sample counts, feature counts, LIONESS-DRAGON values = F(F-1)/2 pairs x samples with F the features of both layers together, COBRA genes vs samples, minimum samples, etc.). Numbers inside a prompt must be consistent.

## 24 single-turn items, ids Y01-Y24, in four categories of 6

Write each request as a researcher would, in their own situation. The categories describe the user's situation; the call follows from the contracts.

**R (run, named) -- 6 items.** The user names exactly one registered workflow and asks for it to be run. The request takes 2-4 sentences, and the sentence that names the workflow is NOT the sentence that says what they want to get out of it: a later (or earlier) sentence says what result they want, where to save it, or what it is for (for example a closing sentence about the network or scores they need, or the file to write).
- 4 items are doable as asked (DO).
- 2 items are not doable as asked: one DECLINE and one PARTIAL (either shape), each because of something stated in the request that a contract rules out.
- In exactly 1 of the 4 doable items, a second registered workflow is mentioned only as where one input came from (for example a matrix an earlier run of another workflow wrote); the user still wants only the named workflow run.

**F (purpose first, one open fact) -- 6 items.** The user opens with why they need something (a figure, a reviewer, a grant, a lab meeting, a collaborator) and then describes, concretely, the result they want. In their own words they say they are unsure of one fact, and that fact decides the outcome: the two answers lead to different contract outcomes (expected_call ASK). Vary the fact:
- 2 items: a number (samples, genes, features, layers, or a setting value) where one candidate value meets a contract condition and the other does not;
- 2 items: which of two results they are supposed to deliver -- both named in the user's own words, and the contracts treat them differently (one workflow vs another, or one doable and one not);
- 2 items: whether they need one result for the whole cohort or one per sample, where the contracts give different answers for the two.
At most 2 of the 6 name a workflow.

**C (choosing between named workflows) -- 6 items.** The user names two (or three) registered workflows as alternatives and asks which one to use.
- 4 items: the user does not say what result they want from it (expected_call CLARIFY). Vary how the alternatives are offered, one each: "X or Y"; "X, or maybe Y"; "either X or Y"; "X versus Y" (or "vs"). Across these 4, one item puts the two alternatives in two separate sentences, and one item names three workflows.
- 2 items: the user does say concretely what result they want, and the contracts decide the answer (for example only one of the named workflows produces it as asked -> DO with that workflow; or neither does -> DECLINE; or one fact decides -> ASK). At least one of the 2 is DO.

**K (controls) -- 6 items.**
- 3 items: vague requests that name no workflow and no concrete result and give no fact they are unsure of (expected_call CLARIFY).
- 3 items: one sentence that names one registered workflow, its inputs, and the result wanted, all in that same sentence; doable as asked (DO).

## Both parts

- English only (no Chinese or other non-ASCII scripts). Realistic, varied user voices and domains (organisms, tissues, diseases, study designs). Do not copy contract sentences into the prompts.
- Spread items across the 13 workflows; each workflow should appear (in `workflows`, or named in a prompt) in at least one item.
- Before writing ids, shuffle the 24 items with a fixed seed, so the order of ids does not reveal the category.
- Workflow names must be exactly: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR.

## Output

Write JSON to /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/docs/research-log/harness-repair-2026-10-23/h8/items-author.json with this exact shape:

{"author_note": "<one paragraph: which files you read, how you decided golds>",
 "single": [ {
   "id": "Y01", "category": "R" | "F" | "C" | "K",
   "sub": "<R: doable | not_doable | input_source; F: number | deliverable | scale; C: or | or_maybe | either | versus (add '+two_sentences' or '+three' where it applies) | stated_result; K: vague | one_sentence>",
   "prompt": "<the user's request>",
   "expected_call": "DO" | "PARTIAL" | "DECLINE" | "ASK" | "CLARIFY",
   "also_acceptable": ["<other calls that are also correct, only when the contracts genuinely allow them; usually empty>"],
   "workflows": ["<DO/PARTIAL: workflows that fit the doable part; DECLINE: closest/relevant (may be empty); ASK: those the deciding fact concerns or chooses between; CLARIFY: candidates>"],
   "reason": "<why this call, one or two sentences; for PARTIAL and DECLINE the reason for each refused part>",
   "evidence": "<exact quote(s) from the YAML or registry, prefixed with the file name, e.g. 'otter.yaml: \"...\"'>",
   "deciding_fact": "<ASK items: the one fact, with what each answer leads to; empty string otherwise>",
   "missing_core": "<CLARIFY items: what is missing; empty string otherwise>",
   "uncertainty": "explicit" | "none"
 }, ... ] }

Validate that the file parses, has 24 items with the counts above, and that every quoted evidence string appears in the file it names.

This set is sealed from the person who will read your reply. When done, reply ONLY with counts: per category and sub, expected_call counts, and how many items each workflow appears in. Do not describe any prompt, scenario, condition, deciding fact or reason.

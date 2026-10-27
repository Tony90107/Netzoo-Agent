You are writing a small blind held-out test set (j1) for an assistant that decides how to answer bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). Each item is a short conversation: the user's opening request, plus the replies the user would give if the assistant asks something. You must work ONLY from these files and open nothing else:

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

## 48 items, ids J01-J48, in four groups

Write each opening request as a researcher would, in their own situation, 2-5 sentences. The groups describe the user's situation; the call follows from the contracts.

**V (no result chosen yet) -- 8 items, expected_call CLARIFY.** The user has a real reason and real data, and says what data they have, but never says which result they want. Vary the situation: at least one each of the following, and two more of any of them:
- someone else (a reviewer, a PI, a collaborator, a funder) asked them for something in general words, and the user says they do not know what exactly is expected;
- a project document or plan promises a general kind of insight, and they need to turn it into an analysis;
- they ask what the toolkit could tell them about their data;
- they hope something interesting comes out of their data and ask to "run something";
- they want to "understand" or "look at" regulation, interactions or structure in their samples in general terms;
- they are new to the toolkit and ask where to start with their data.
In at least 4 of the 8, the user's words should sound like a kind of output ("a network", "network analysis", "regulation", "modules", "signatures", "interactions") without picking a particular output. At most 1 of the 8 names a registered workflow, and only as something they heard of, not as the result they want.

**U (concrete request, one open fact) -- 12 items, expected_call ASK.** The user asks concretely for a result (and may name a workflow), and in a SEPARATE sentence -- not the sentence that asks for the result -- says in their own words that they are unsure of one fact about their data or setup ("I'm not sure ...", "I can't remember whether ...", "it's either ... or ..."). Under the contracts that fact decides the outcome: the two answers lead to different contract outcomes (doable vs not doable, or one workflow vs another). No contract default and no automatic file check settles it. Vary the fact, 3 items each:
- which of two files, exports or tables they actually have;
- whether their data has a property a contract requires or rules out (for example how values were transformed, continuous vs binary values, whether two data types come from the same samples, the origin of mutation calls);
- a count (samples, features, layers) with two candidate values, one meeting a contract limit and one not;
- whether an input the result needs exists or was ever made.
Exactly 2 of the 12 concern DRAGON or LIONESS-DRAGON.

**K1 (doable, with an aside) -- 14 items, expected_call DO.** A request that a registered workflow can do as asked. Each contains one sentence that is a question, a hedge or an uncertainty that does NOT change the outcome under the contracts, for example: a polite question form ("Could you ...?", "Would it be possible to ...?"); asking how long it will take; being unsure about something the contracts do not care about (where they will present it, which colleague will read it, a figure's colours, a deadline); a remark about the project's history. In exactly 5 of the 14 the aside is an explicit statement of uncertainty ("I'm not sure ...", "I don't know yet ...") about something irrelevant to the contracts.
- **Exactly 5 of the 14 are DRAGON or LIONESS-DRAGON requests that are doable as asked.** Vary how the result is asked for: one names "a DRAGON network"; one only describes the result in their own words (a network of partial correlations between two kinds of measurements, without the name); one is per-sample (LIONESS-DRAGON) within its limits; one gives sizes and settings DRAGON accepts; the fifth any of these with a different data type.
- The other 9 spread over other workflows; at least 4 of the 14 name the workflow, and at least 4 describe the result without naming it.

**K2 (not doable, with an aside) -- 14 items, expected_call DECLINE.** A request that no registered workflow can do as asked, for a reason the contracts state clearly (a result no contract produces, an input a contract excludes, a size or value limit, an out-of-range setting, an unregistered method). Each also contains one question, hedge or irrelevant uncertainty that does not change the outcome, as in K1; in exactly 5 of the 14 it is an explicit irrelevant uncertainty.
- **Exactly 5 of the 14 are DRAGON or LIONESS-DRAGON requests that are not doable as asked**, at least 4 for different stated reasons (for example: more than two layers in one model, a per-sample value count over the stated limit, layers not measured on the same samples, a setting value outside its range).
- At least 3 of the other 9 ask for a clearly out-of-scope result in plain words.

## Replies (the user's side of the conversation)

The assistant may ask a question after the opening request. For each item write the user's possible replies. Each reply is 1-3 sentences in the same user's voice and adds nothing beyond what its field says.

- `reply_restate` (ALL items): the user only restates what they asked for in the opening request, in different words, and adds no new fact, setting, number or choice. (For V items it stays as vague as the opening; for U items it does not settle the unsure fact.)
- `reply_fact` (U items only): the user answers the unsure fact by naming exactly one of the two options plainly ("It's the filtered export." / "Yes, they were log-transformed."). Across the 12 U items, 6 answers lead to a doable outcome and 6 to a not-doable one.
- `fact_keywords` (U items only): 3-6 short lowercase words or phrases that a question asking about exactly that fact would very likely contain (for example "which file", "filtered", "log-transformed", "somatic", "germline", "same samples"). Avoid generic words like "data" or "network".
- `final_after_fact` (U items only): the correct call after the opening request plus `reply_fact`: {"call": "DO" | "PARTIAL" | "DECLINE", "workflows": [...], "reason": "...", "evidence": "<exact contract quote(s) with file name>"}.
- `reply_result` (V items only): the user picks one concrete result in their own words (what they want to get out of the data). Across the 8 V items, 6 choices are doable with the data they described and 2 are not.
- `final_after_result` (V items only): the correct call after the opening request plus `reply_result`, in the same shape as `final_after_fact`.

## All items

- English only (no Chinese or other non-ASCII scripts). Realistic, varied user voices and domains (organisms, tissues, diseases, study designs). Do not copy contract sentences into the prompts or replies.
- Spread items across the 13 workflows; each workflow should appear (in `workflows`, or named in a prompt) in at least one item.
- Before writing ids, shuffle the 48 items with a fixed seed, so the order of ids does not reveal the group.
- Workflow names must be exactly: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR.

## Output

Write JSON to /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-jev-guard/docs/research-log/jev-guard-2026-10-27/j1/items-author.json with this exact shape:

{"author_note": "<one paragraph: which files you read, how you decided golds>",
 "single": [ {
   "id": "J01", "category": "V" | "U" | "K1" | "K2",
   "sub": "<V: asked_by_others | project_promise | what_can_it_tell | something_interesting | understand_in_general | where_to_start; U: which_file | data_property | count | input_exists; K1: polite_question | runtime_question | irrelevant_uncertainty | history_remark; K2: out_of_scope | broken_condition>",
   "dragon_control": true | false,
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
   "reply_fact": "<U items; empty string otherwise>",
   "fact_keywords": ["<U items; empty list otherwise>"],
   "final_after_fact": {<U items; null otherwise>},
   "reply_result": "<V items; empty string otherwise>",
   "final_after_result": {<V items; null otherwise>}
 }, ... ] }

`dragon_control` is true only for the 5 K1 and 5 K2 DRAGON/LIONESS-DRAGON items. `uncertainty` is "explicit" when the opening request states the user is unsure of something (including irrelevant things in K1/K2), else "none".

Validate that the file parses, has 48 items with the counts above, and that every quoted evidence string (including those inside `final_after_fact` and `final_after_result`) appears in the file it names.

This set is sealed from the person who will read your reply. When done, reply ONLY with counts: per group and sub, expected_call counts, dragon_control counts per group, final_after_fact and final_after_result call counts, and how many items each workflow appears in. Do not describe any prompt, reply, scenario, condition, deciding fact or reason.

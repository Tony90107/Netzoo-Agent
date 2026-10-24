You are writing a blind held-out test set for an assistant that decides how to answer bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). You must work ONLY from these files and open nothing else:

- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/scripts/workflow_registry.py

Do NOT open any other file or directory (no docs, research logs, collab, tests, other scripts, capability sheet, previous test sets, or anything outside those paths). Do not run the assistant or any code that calls models. You may use shell tools only to list and read those files, and to validate the JSON you write.

## The calls

For each request the assistant must give one of these calls:
- DO: a registered workflow can do the request as asked (inputs, sizes and settings its contract accepts).
- PARTIAL: part of the request can be done as asked and part cannot. Two shapes only:
  (a) the user names a workflow to run and also asks for a setting that workflow does not expose at all (or an option it has no control for, e.g. an output format, hardware, or a parameter name it does not have); the workflow can still run with its own settings. The right answer says so, refuses the setting with its reason, and does not start the run by itself.
  (b) the user asks for two distinct results; a registered workflow produces one as asked, and no workflow produces the other (or it fails a stated condition). The right answer offers the doable one, refuses the other with its reason, and runs nothing by itself.
- DECLINE: nothing in the request can be done as asked -- it fails one condition the contracts state (an input the workflow does not take, a size or value limit, a value outside a range the contract states for an exposed setting, an invalid setting combination, an unregistered method or handoff), or it asks for a result no contract produces.
- ASK: exactly one fact decides it, and the two possible answers lead to different contract outcomes (e.g. doable vs not doable, or one workflow vs another). The assistant should ask that one question.
- CLARIFY: the request names no concrete result (the user wants "an analysis", asks which tool to use without saying what they want to learn, etc.), so the assistant should ask what result they want.

Every gold must follow from contract text you can quote. Recompute arithmetic yourself (sample counts, feature counts, LIONESS-DRAGON values = F(F-1)/2 pairs x samples with F the features of both layers together, COBRA genes vs samples, minimum samples, etc.). Numbers inside a prompt must be consistent.

## Part 1: 36 single-turn items, ids S01-S36

Classes: do, dont, ask, vague -- 9 each; within each class 3 of each form:
- named: the user names a specific workflow;
- goal: the user describes what they want without naming a workflow;
- run: the user asks the assistant to run/launch something now, usually naming input files.

`expected_call` by class: do -> DO; dont -> PARTIAL or DECLINE; ask -> ASK; vague -> CLARIFY.

Required within the 36:
- dont: at least 3 items whose expected_call is PARTIAL (use both shapes) and at least 5 whose expected_call is DECLINE; vary which kind of condition fails.
- do: at least 2 items where the user voices uncertainty about something that does NOT change the outcome (asking about it would be needless).
- ask: at least 2 items where the user does NOT say they are unsure, but simply leaves out the one fact that decides the outcome, and no contract default or file check settles it. The rest make the uncertainty explicit in the user's own words.
- 3 minimal pairs (6 items): the same scenario written twice with exactly one key fact changed, so the call changes (e.g. DO vs DECLINE). Give both items of a pair the same `group` (e.g. "P1").
- 2 paraphrase pairs (4 items): the same request written twice in different words and sentence order, same call. Same `group` (e.g. "Q1").
- Every other item has `group` equal to its own id. Apart from these pairs, do not reuse a scenario.

## Part 2: 14 multi-turn items, ids M01-M14

Each is a conversation that starts with a turn-1 request whose right call is ASK (or CLARIFY where stated), followed by scripted user replies. The test runner sends the replies; you write them now. Types and counts:

| type | count | turns | what the user does after turn 1 |
|---|---|---|---|
| answer | 4 | 2 | answers the deciding fact. 2 items answer with the option words themselves (e.g. "They are somatic mutations."), 2 answer in natural words that imply one side without the option words |
| volunteer | 2 | 2 | answers the deciding fact AND adds one new condition in the same reply that changes the final outcome (e.g. the answer makes it doable but the new condition makes one part not doable, or switches the workflow) |
| correct | 3 | 3 | turn 2 answers the deciding fact; turn 3 corrects it to the other side ("Sorry, I checked again: ...") |
| switch | 2 | 2 | turn 2 drops the request and asks for something unrelated (a new, complete request with its own gold) |
| unknown | 3 | 3 | turns 2 and 3 both say, in different words, that they do not know and cannot find out the deciding fact (or, for a CLARIFY start, what result they want) |

The runner answers by what the assistant asked: when the assistant's question is about the deciding fact, it sends your `answer` (or the scripted reply for that turn); when it asks about something else, it replies "I'm not sure about that."; when turn 1 does not ask at all, the conversation stops. So write `match_keywords`: 3-8 lowercase words or short phrases that a question about the deciding fact would very likely contain (e.g. "somatic", "germline", "tumour", "normal"). For unknown, switch and CLARIFY starts, the replies are sent regardless.

For each multi-turn item give the final gold:
- answer / volunteer / correct: `final_call` (DO, PARTIAL or DECLINE) and `final_workflows` after the replies (for correct: after the correction), with the reason and evidence.
- switch: `new_request_call` and `new_request_workflows` for the new request; the old request's facts must not be carried into it.
- unknown: no final call; the right behaviour is that the assistant does not guess the fact, does not decline or run, asks at most twice in total, and on the third turn says what is still missing without asking again.

## Both parts

- English only (no Chinese or other non-ASCII scripts). Realistic, varied user voices and domains (organisms, tissues, diseases, study designs). 1-4 sentences per message. Do not copy contract sentences into the prompts; write as a researcher would.
- Spread items across all 13 workflows; each workflow should appear in at least 2 items.
- Before writing ids, shuffle the items within each part with a fixed seed, so the order of ids does not reveal the class or type.
- Workflow names must be exactly: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR.

## Output

Write JSON to /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-harness-repair/docs/research-log/harness-repair-2026-10-23/h7/items-author.json with this exact shape:

{"author_note": "<one paragraph: which files you read, how you decided golds>",
 "single": [ {
   "id": "S01", "class": "do" | "dont" | "ask" | "vague", "form": "named" | "goal" | "run", "group": "S01" | "P1" | "Q1" ...,
   "prompt": "<the user's request>",
   "expected_call": "DO" | "PARTIAL" | "DECLINE" | "ASK" | "CLARIFY",
   "also_acceptable": ["<other calls that are also correct, only when the contracts genuinely allow them; usually empty>"],
   "workflows": ["<do/PARTIAL: workflows that fit the doable part; DECLINE: closest/relevant (may be empty); ask: those the deciding fact concerns or chooses between; vague: candidates>"],
   "reason": "<why this call, one or two sentences; for PARTIAL and DECLINE the reason for each refused part>",
   "evidence": "<exact quote(s) from the YAML or registry, prefixed with the file name, e.g. 'otter.yaml: \"...\"'>",
   "deciding_fact": "<ask items: the one fact, with what each answer leads to; empty string otherwise>",
   "missing_core": "<vague items: what is missing; empty string otherwise>",
   "uncertainty": "explicit" | "silent" | "irrelevant" | "none",
   "interpretation_facts": ["<facts in the request that matter for interpreting it correctly>"],
   "file_checkable": <ask items: true if the deciding fact could be verified from the named input files before running; false otherwise>
 }, ... ],
 "multi": [ {
   "id": "M01", "type": "answer" | "volunteer" | "correct" | "switch" | "unknown",
   "prompt": "<turn 1>",
   "t1_call": "ASK" | "CLARIFY",
   "workflows": ["..."], "reason": "...", "evidence": "...",
   "deciding_fact": {"what": "<the fact, with what each answer leads to>", "match_keywords": ["..."],
                     "answer": "<turn-2 reply when asked (answer, volunteer, correct)>",
                     "answer_form": "option_words" | "natural" | ""},
   "correction": "<correct only: the turn-3 reply>",
   "new_condition": "<volunteer only: the condition added in the answer, quoted from it>",
   "new_request": "<switch only: the turn-2 reply>",
   "unknown_replies": ["<unknown only: turn-2 reply>", "<turn-3 reply>"],
   "final_call": "DO" | "PARTIAL" | "DECLINE" | "",
   "final_workflows": ["..."],
   "final_reason": "<why, with the contract quote>",
   "new_request_call": "<switch only>", "new_request_workflows": ["<switch only>"]
 }, ... ] }

Validate that the file parses, has 36 single and 14 multi items with the counts above, and that every quoted evidence string appears in the file it names.

This set is sealed from the person who will read your reply. When done, reply ONLY with counts: per class and form, expected_call counts, the count of each required feature (partial shapes, irrelevant/silent uncertainty, pairs), multi-turn counts per type, and how many items each workflow appears in. Do not describe any prompt, scenario, condition, deciding fact or reason.

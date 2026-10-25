You are writing a blind held-out test set (h10) for an assistant that decides how to answer bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). You must work ONLY from these files and open nothing else:

- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/scripts/workflow_registry.py

Do NOT open any other file or directory (no docs, research logs, collab, tests, other scripts, capability sheet, previous test sets, or anything outside those paths). Do not run the assistant or any code that calls models. You may use shell tools only to list and read those files, and to validate the JSON you write.

## The calls

For each request the assistant must give one of these calls:
- DO: a registered workflow can do the request as asked (inputs, sizes and settings its contract accepts).
- PARTIAL: part of the request can be done as asked and part cannot. Two shapes only:
  (a) the user names a workflow to run and also asks for a setting that workflow does not expose at all (or an option it has no control for, e.g. an output format, hardware, or a parameter it does not have); the workflow can still run with its own settings.
  (b) the user asks for two distinct results; a registered workflow produces one as asked, and no workflow produces the other (or it fails a stated condition).
- DECLINE: nothing in the request can be done as asked -- it fails one condition the contracts state (an input the workflow does not take, a size or value limit, a value outside a range the contract states for an exposed setting, an invalid setting combination, an unregistered method or handoff), or it asks for a result no contract produces.
- ASK: exactly one fact decides it, and the two possible answers lead to different contract outcomes (e.g. doable vs not doable, or one workflow vs another). The assistant should ask that one question.
- CLARIFY: the request names no concrete result (the user wants "an analysis", asks what can be done, etc.), so the assistant should ask what result they want.

Every gold must follow from contract text you can quote. Recompute arithmetic yourself (sample counts, feature counts, LIONESS-DRAGON values = F(F-1)/2 pairs x samples with F the features of both layers together, COBRA genes vs samples, minimum samples, etc.). Numbers inside a prompt must be consistent.

## 48 single-turn items, ids Y01-Y48, in five groups

Write each request as a researcher would, in their own situation, 2-5 sentences. The groups describe the user's situation; the call follows from the contracts.

**S (a setting described by what it does) -- 10 items.** The user asks for a concrete result (naming the workflow in at least 6 of the 10) and also wants something about how it is run that, under the contracts, is a setting of that workflow. Describe the setting ONLY by its effect or purpose in the user's own words -- never use the setting's name, its parameter spelling, or a contract sentence about it (e.g. not "sparsify", "lambda1", "kmin"). Calls: 5 DO (the described choice is allowed), 3 DECLINE (the described choice, as stated with its value or combination, breaks a range or rule the contract states for that exposed setting), 2 PARTIAL shape (a) (the described effect is something that workflow has no setting for at all). Spread over at least 4 workflows that expose settings.

**D (an input that is the product of earlier work) -- 10 items.** The user's main input is not raw measurement data but something already computed: a gene-by-gene co-expression or correlation matrix, an adjusted co-expression matrix, a regulatory or other network, per-sample networks, scores, etc. In at least 5 items the prompt says which tool or workflow made it (a NetZoo workflow by name in at least 3; another tool or a collaborator in others). Calls: 4 DO (a contract accepts that input for the asked result), 4 DECLINE (the asked workflow does not take that kind of input, or the handoff is not registered, and nothing else gives the result from it), 2 PARTIAL or DECLINE as the contracts decide (your choice of situation). The kind of the input must be clear from the words.

**U (unsure what an input is or where it came from) -- 8 items, expected_call ASK.** The user asks concretely for a result, and in a SEPARATE sentence -- not the sentence that asks for the result -- says in their own words that they are unsure what one of their files contains or how it was made ("I'm not sure if it's ... or ...", "I can't remember whether that matrix came from ...", "it might be the raw table or the correlation matrix"). Under the contracts that fact decides the outcome: the two answers lead to different contract outcomes (doable vs not doable, or one workflow vs another). No contract default and no automatic file check settles it.

**T (traps and controls) -- 8 items.** 4 items expected DO: a doable request that also mentions data the result does not use, or says where a needed input came from in a way the contracts do not care about. 4 items expected DO: a doable request with an explicit uncertainty ("I'm not sure ...", "I don't remember ...") about an input's origin or preparation that does NOT change the outcome under the contracts (the workflow accepts either answer). At least 4 of the 8 name the workflow.

**G (general) -- 12 items.** Ordinary requests of every kind, not built around settings or derived inputs: 3 DO, 3 DECLINE (at least 1 asks for a clearly out-of-scope result in plain words; at least 1 breaks a stated size or sample condition), 2 ASK (one open fact of any other kind: a count, whether two data types share samples, how values were transformed, ...; stated in a separate sentence as uncertainty), 4 CLARIFY (real data and a real reason, but no concrete result chosen; at least 2 use words that sound like an output -- "a network", "regulation", "modules" -- without picking one).

## All groups

- English only (no Chinese or other non-ASCII scripts). Realistic, varied user voices and domains (organisms, tissues, diseases, study designs). Do not copy contract sentences into the prompts.
- Spread items across the 13 workflows; each workflow should appear (in `workflows`, or named in a prompt) in at least two items.
- Before writing ids, shuffle the 48 items with a fixed seed, so the order of ids does not reveal the group.
- Workflow names must be exactly: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR.

## Output

Write JSON to /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/docs/research-log/round27-phase0-2026-10-25/h10/items-author.json with this exact shape:

{"author_note": "<one paragraph: which files you read, how you decided golds>",
 "single": [ {
   "id": "Y01", "category": "S" | "D" | "U" | "T" | "G",
   "sub": "<S: allowed | breaks_rule | no_such_setting; D: accepted | not_accepted | other; U: content | origin; T: unused_data | irrelevant_origin | irrelevant_uncertainty; G: do | decline | ask | clarify>",
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

`uncertainty` is "explicit" when the prompt states the user is unsure of something, else "none".

Validate that the file parses, has 48 items with the counts above, and that every quoted evidence string appears in the file it names.

This set is sealed from the person who will read your reply. When done, reply ONLY with counts: per group and sub, expected_call counts, and how many items each workflow appears in. Do not describe any prompt, scenario, condition, setting, input kind, deciding fact or reason.

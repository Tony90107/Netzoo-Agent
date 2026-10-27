You are writing a small blind held-out test set (j4) for an assistant that decides how to answer bioinformatics requests about a fixed registry of 13 network-analysis workflows (NetZoo). Each item is a short conversation: the user's opening request, plus the replies the user would give if the assistant asks something. You must work ONLY from these files and open nothing else:

- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-j4/workflows/*.yaml (the 13 workflow contracts)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-j4/scripts/workflow_registry.py

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

## 48 items, ids S01-S48, in thirteen groups

Write each opening request as a researcher would, in their own situation, 2-5 sentences. The groups describe the user's situation; the call follows from the contracts. Several groups are about the *form* of the wanted result (whether items may sit in several groups, whether change over time must be modelled, whether spatial neighbours must be used, what kind of existing network a result starts from). In the "trap" groups the user's words must NOT ask for the excluded form; in the "control" groups they must ask for it plainly.

**GT (grouping, no overlap asked) -- 5 items, expected_call DO.** The user asks for a grouping a registered workflow produces (subtypes, clusters, communities, modules) in plain words, e.g. "split into subtypes, trying 2 to 4 groups", "communities of regulators and genes". Never says an item may sit in several groups and never asks for a membership strength. Everything stated is acceptable. 2-3 name the workflow. Vary the words for "group".

**GO (overlap asked; controls) -- 4 items, expected_call DECLINE.** The user asks that one gene, regulator or sample may belong to more than one group at the same time, or for each item's degree or strength of membership in every group. Plain but varied words. 2 name a grouping workflow, 2 do not.

**FT (several time points, no dynamics asked) -- 4 items, expected_call DO.** The samples come from several time points, stages or a time course (say so plainly, e.g. "time-course samples", "collected at baseline, week 4 and week 12"), and the user asks for a result a registered workflow produces per sample or per group that does NOT model change from one time point to the next (e.g. one network per sample, per-sample activity, a comparison of stages). Never ask for lags, transitions, trajectories or a dynamic model. All stated facts acceptable.

**FD (dynamics asked; controls) -- 3 items, expected_call DECLINE.** The user asks for a model of how the system changes from one time point to the next (time-lagged regulation, a dynamic or state-transition model, a trajectory, regulation at one time predicting the next). Varied words.

**FSN (spatial data, no neighbours asked) -- 2 items, expected_call DO.** The samples are spatial (e.g. spots or regions from tissue sections), but the user asks for a result computed for each sample or the cohort on its own terms, never using positions or neighbours. All stated facts acceptable.

**FS (neighbours asked; controls) -- 2 items, expected_call DECLINE.** The user asks for a result that must use where samples sit in space or which samples are neighbours (smoothing over neighbouring spots, spatially contiguous modules, neighbourhood-aware networks).

**FN (existing regulator-gene network; communities) -- 4 items, expected_call DO.** The user already has a regulator-to-gene network (e.g. from PANDA, LIONESS-PANDA, OTTER or PUMA) saved in a form the community workflow's contract accepts, and asks for communities or modules of regulators and genes. State the network's provenance and form in the user's own words, which must make clear that the links run from regulators (TFs) to target genes. Everything else acceptable (check the contract's input conditions). 2 name CONDOR, 2 do not.

**FG (existing network of another kind; controls) -- 2 items, expected_call DECLINE.** The same request for communities, but the user's existing network links features of one kind (e.g. a co-expression or partial-correlation network, gene-gene or metabolite-protein) and the community workflow's contract does not take it.

**T (data-type trap) -- 5 items, expected_call DECLINE.** The user asks concretely for a result a registered workflow produces, but states plainly that their data is a kind the contracts do not let any workflow producing that result take (an incompatible data type, a type that is not among a workflow's declared input artifacts, a handoff a contract refuses, or for DRAGON / LIONESS-DRAGON layers measured on different samples). Stated as a fact, not an uncertainty; nothing else wrong. Exactly 1 concerns DRAGON or LIONESS-DRAGON with different samples. None is a community request.

**TC (data-type control) -- 4 items, expected_call DO.** Same shapes as T, but the stated data is a kind the contracts accept (including alternatives a contract explicitly allows). Exactly 1 concerns DRAGON or LIONESS-DRAGON on stated same samples. 1 adds one sentence of explicit uncertainty about something the contracts do not care about.

**U (concrete request, one open fact) -- 6 items, expected_call ASK.** The user asks concretely for a result and, in a SEPARATE sentence, says in their own words they are unsure of one fact about their data or setup. The two answers lead to different contract outcomes; no contract default or automatic file check settles it. Facts: which of two files (1), a data property (2), a count with two candidate values (2), whether a needed input exists (1). None is a grouping request.

**N (result in plain words) -- 4 items, expected_call DO for 3 and DECLINE for 1.** The user describes the result in plain words, without naming any workflow or its technical output name, with a purpose framing. Exactly one registered workflow's result matches. For the DECLINE item one stated fact breaks that workflow's contract. None is a grouping request.

**V (no result chosen yet) -- 3 items, expected_call CLARIFY.** The user has a real reason and data, says what data they have, but never says which result they want. At least 1 uses output-sounding words ("a network", "modules") without picking an output. None names a registered workflow.

## Replies (the user's side of the conversation)

Each reply is 1-3 sentences in the same user's voice and adds nothing beyond what its field says.

- `reply_restate` (ALL items): the user only restates what they asked for, in different words, and adds no new fact, setting, number or choice. For V items it stays as vague as the opening; for U items it does not settle the unsure fact.
- `reply_form` (GT, FT, FSN, FN items only; empty string otherwise): if asked about the form of the result, the user answers in their own natural words with what the opening request already implies -- GT: each item belongs to exactly one group; FT: results per time point or sample, compared, not a model of change; FSN: each sample on its own, positions not used; FN: the network links regulators (TFs) to their target genes. Do not copy a fixed phrase; vary the wording across items.
- `reply_confirm` (T items only): the user confirms the data fact they already stated, plainly, adding nothing else.
- `reply_fact` (U items only): the user answers the unsure fact by naming exactly one of the two options plainly. Across the 6 U items, 3 answers lead to a doable outcome and 3 to a not-doable one.
- `fact_keywords` (U items only): 3-6 short lowercase words or phrases a question about exactly that fact would very likely contain. Avoid generic words like "data" or "network".
- `final_after_fact` (U items only): the correct call after the opening request plus `reply_fact`: {"call": "DO" | "PARTIAL" | "DECLINE", "workflows": [...], "reason": "...", "evidence": "<exact contract quote(s) with file name>"}.
- `reply_result` (V items only): the user picks one concrete result in their own words. Across the 3 V items, 2 are doable with the described data and 1 is not.
- `final_after_result` (V items only): the correct call after the opening request plus `reply_result`, same shape as `final_after_fact`.

## All items

- English only. Realistic, varied user voices and domains (organisms, tissues, diseases, study designs). Do not copy contract sentences into the prompts or replies.
- Spread items across the 13 workflows; each workflow should appear (in `workflows`, or named in a prompt) in at least one item.
- Before writing ids, shuffle the 48 items with a fixed seed, so the order of ids does not reveal the group.
- Workflow names must be exactly: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR.

## Output

Write JSON to /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-j4/docs/research-log/jev-j4-2026-10-27/j4/items-author.json with this exact shape:

{"author_note": "<one paragraph: which files you read, how you decided golds>",
 "single": [ {
   "id": "S01", "category": "GT" | "GO" | "FT" | "FD" | "FSN" | "FS" | "FN" | "FG" | "T" | "TC" | "U" | "N" | "V",
   "sub": "<GT: gt_named | gt_unnamed; GO: go_named | go_unnamed; FT: ft; FD: fd; FSN: fsn; FS: fs; FN: fn_named | fn_unnamed; FG: fg; T: incompatible | not_accepted | refused_handoff | different_samples; TC: ok_accepted | ok_alternative | ok_same_samples; U: which_file | data_property | count | input_exists; N: n_do | n_decline; V: asked_by_others | project_promise | what_can_it_tell | something_interesting | understand_in_general | where_to_start>",
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
   "reply_form": "<GT, FT, FSN, FN items; empty string otherwise>",
   "reply_confirm": "<T items; empty string otherwise>",
   "reply_fact": "<U items; empty string otherwise>",
   "fact_keywords": ["<U items; empty list otherwise>"],
   "final_after_fact": {<U items; null otherwise>},
   "reply_result": "<V items; empty string otherwise>",
   "final_after_result": {<V items; null otherwise>}
 }, ... ] }

`dragon_control` is true exactly for the 1 T and 1 TC DRAGON/LIONESS-DRAGON items. `names_workflow` is true when the opening request names a registered workflow. `uncertainty` is "explicit" when the opening request states the user is unsure of something (including irrelevant things in TC), else "none".

Validate that the file parses, has 48 items with the counts above, and that every quoted evidence string (including those inside `final_after_fact` and `final_after_result`) appears in the file it names. You may run `python3 /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-j4/docs/research-log/jev-j4-2026-10-27/j4/check_format.py items-author.json` for counts and quote checks (it reads only the contracts and your file).

This set is sealed from the person who will read your reply. When done, reply ONLY with counts: per group and sub, expected_call counts, dragon_control counts per group, final_after_fact and final_after_result call counts, and how many items each workflow appears in. Do not describe any prompt, reply, scenario, condition, deciding fact or reason.

You are labelling, blind, the field-level gold of a sealed test set (h10): which words of each request link to which registry entries of a fixed registry of 13 network-analysis workflows (NetZoo).

Open ONLY:
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/docs/research-log/round27-phase0-2026-10-25/h10/items.json -- read ONLY each item's `id` and `prompt`; do not read any other field (calls, workflows, reasons, evidence) and do not let them guide you
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/docs/research-log/field-gold-2026-10-22/vocabulary.md (registry vocabulary: settings, PRODUCES entries, near-miss entries)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/docs/research-log/round27-phase0-2026-10-25/CONTENT-BRIEF.md -- ONLY its "What to label" section, for the `content`, `made_by` and `certainty` of each `has` unit (ignore its file paths and output section)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/workflows/*.yaml and /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/scripts/workflow_registry.py

Open nothing else. Do not run anything that calls a model. Shell tools only to read those files (to read items.json, extract id and prompt with a one-line script) and to write/validate your JSON.

## Fields, per request

- `results`: each phrase that names a result the user wants. `quote` = exact contiguous words; `produces` = every PRODUCES id (vocabulary.md) that gives the result as asked -- an acceptable set, respecting per-sample vs whole-cohort, regulator kinds and sign; empty when none does. `near_miss` = near-miss ids that describe it; `registry_wide` = true-ish note ids only if needed (usually empty). A request that only names a method to run ("run PANDA on ...") gets no result unit for the method name; words like "the network" that point back to a named method get only that method's id.
- `settings`: each phrase that sets or declares something a workflow exposes as a setting (vocabulary.md "Settings"), including data-state declarations (e.g. log-transformed, centered). `setting` = `WORKFLOW.setting`, `value` = the stated value as a string ("true", "0.4", "edge_list", ...), or "" when the words choose it without a value. Phrases describing a setting's effect without its name still count when the effect is unmistakably that setting. A choice no workflow exposes is not a setting unit (note it in `notes`).
- `has`: each piece of data the user says they have. `slot` = the input slot it would fill (`expression_file`, `motif_file`, `ppi_file`, `mirna_file`, `coexpression_file`, `network_file`, `mutation_file`, `design_file`, `omics_layer_1`, `omics_layer_2`, `pathway_file`, `cancer_gene_file`, `exon_size_file`) or `none` when no slot takes it; plus `content`, `made_by`, `certainty` as defined in CONTENT-BRIEF.md "What to label".
- `lacks`: each input the user says they do not have, with its `slot`.
- `source`: for each result, which `has` data it must be computed from when the words say so (`result_quote`, `quote`, `slot`).
- Every entry has a short `why`. `notes` per request for anything else.

## Output

Write /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/docs/research-log/round27-phase0-2026-10-25/h10/fields.json:

{"set": "h10", "labeller_note": "<one paragraph: what you read, conventions>",
 "items": [ {"id": "Y01", "results": [...], "settings": [...], "has": [...], "lacks": [...], "source": [...], "notes": ""}, ... ] }

Result entry: {"quote", "produces", "near_miss", "registry_wide", "why"}. Setting entry: {"quote", "setting", "value", "why"}. Has entry: {"quote", "slot", "content", "made_by", "certainty", "why"}. Lacks entry: {"quote", "slot", "why"}. Source entry: {"result_quote", "quote", "slot", "why"}.

Validate: 48 items with ids matching items.json; every quote appears verbatim in its prompt; every id/setting/content/made_by value is from the vocabularies.

This set is sealed from the person who will read your reply. Reply ONLY with counts: number of results, settings, has, lacks and source units, and has-unit counts per content and per certainty. Do not describe any prompt, phrase or label.

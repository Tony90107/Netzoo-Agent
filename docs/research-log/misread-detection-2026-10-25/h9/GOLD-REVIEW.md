# h9 gold review

Reviewer read only REVIEW-BRIEF.md, AUTHOR-BRIEF.md, items-author.json, the 13 `workflows/*.yaml` contracts and
`scripts/workflow_registry.py`. No model was run. Evidence quotes were checked verbatim with python (24/24 items, 0 missing),
and all prompts are ASCII.

## Changes

None. No gold field (call, also_acceptable, workflows, reason, evidence, deciding_fact, missing_core, uncertainty) and no
prompt was changed. `items.json` = `items-author.json` + `review_note`.

Arithmetic I recomputed:
- Z06 LIONESS-DRAGON: 400 proteins + 200 metabolites, F = 600, 600*599/2 = 179,700 pairs x 100 = 17,970,000 (<= 20,000,000);
  500 + 200, F = 700, 700*699/2 = 244,650 x 100 = 24,465,000 (> 20,000,000). lioness-dragon.yaml: "runs above 20,000,000
  values are refused before they start".
- Z09 COBRA: 96 genes < 240 samples, fails cobra.yaml: "Expression must be a labeled gene-by-sample matrix with more genes
  than samples."; Z13 COBRA: 12,000 > 60, passes.
- Z07 SAMBAR 2 <= 2 <= 5 <= 58 and Z24 2 <= 2 <= 6 <= 140, both pass sambar.yaml: "cluster=true requires 2 <= kmin <= kmax
  <= number of mutation samples."
- Z17: 2 profiles < 3, fails lioness-coexpression.yaml: "Require at least three samples" (BONOBO too: "at least three total
  samples"); Z04 (14), Z19 (9), Z16 (70), Z22 (52) all meet their minimums.

## Borderline items kept unchanged

- **Z06 (ASK, count)**: inspecting the proteomics file would show the protein count. Kept because the contract scopes the limit
  to the request, not to a file check: lioness-dragon.yaml input_checks lists "runs above 20,000,000 values are refused before
  they start" with `scope: request`, `limit: "max_values"`. The only file-scope check there is sample-ID equality. This is the
  count shape AUTHOR-BRIEF.md asks for.
- **Z22 (ASK, which_file)**: someone could argue that inspecting the file would show a square gene-by-gene matrix. Kept because the
  contract says this refusal is request-level: lioness-panda.yaml "An aggregate COBRA adjusted co-expression artifact is not
  a direct LIONESS handoff" (`scope: request`, `refuses_input:coexpression_matrix`, commented "no file inspection settles
  it").
- **Z21 (ASK, which_file)**: a DRAGON edge list has source/target columns, so CONDOR's only file check ("Require source and
  target columns and accept an optional numeric weight column.") would not reject it. Which run produced the file decides the
  outcome, and dragon.yaml: "Direct handoffs to PANDA, PUMA, LIONESS, CONDOR, BONOBO, and OTTER are illegal".
- **Z04 (ASK, data_property)**: log status is something the user declares, not something a file check finds: bonobo.yaml
  "The agent requires the caller to declare log_transformed=true and centered=true". The `log_transformed` default is null.
- **Z16 (ASK, input_exists)**: if the miRNA list was never made, a required input is missing and the TF+miRNA per-sample
  result cannot be built as asked (lioness-puma.yaml required_inputs includes `mirna_file`; "a validated one-ID-per-line miRNA
  list"). LIONESS-PANDA would drop the requested miRNA regulators, so it does not count as doing the request as asked.
- **Z08 (DECLINE, out_of_scope)**: the sub could also be read as broken_condition, because OTTER is named and otter.yaml says it
  is "aggregate only". I kept out_of_scope: the requested per-sample OTTER result comes from an unregistered method
  (workflow_registry.py: LIONESS-OTTER "netZooPy, not registered in this agent"), and the K2 minimums (>= 2 each) hold
  either way. I rejected PARTIAL (a): running aggregate OTTER with its own settings does not give "each tumour its own"
  network, so no part of the result is delivered.
- **Z14 (DECLINE)**: I rejected PARTIAL because only one result is asked for (one model over three layers). dragon.yaml: "DRAGON
  consumes exactly two paired sample-by-feature continuous omics tables"; no three-layer argument.
- **Z19 (DO)**: bonobo.yaml delta: "With sparsify it must be above 0 and below 1/3". The user sets no delta, so the
  request asks for no value outside a range. sparsify with confidence 0.01 (range [0, 1]) and `.csv` are exposed settings.
- **Z10, Z18 (CLARIFY) candidate lists**: these include PANDA/LIONESS-PANDA (Z18 states no PPI) and SAMBAR (Z10 states no
  gene-length/cancer-gene/GMT files). They are kept as candidates for the clarifying question. They do not affect the call.

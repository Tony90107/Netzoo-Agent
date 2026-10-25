You are labelling, blind, what each piece of a user's data is, in requests to an assistant that runs a fixed registry of 13 network-analysis workflows (NetZoo).

Open ONLY:
- the batch file named in your task (requests, and for each request the quotes of data the user has, each with the input slot an earlier labeller assigned)
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/workflows/*.yaml
- /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-r27/scripts/workflow_registry.py

Open nothing else (no docs, research logs, collab, tests, other label files, other scripts). Do not run anything that calls a model. Shell tools only to read those files and to write/validate your JSON.

## What to label

For every `has` unit (a quote of something the user has), give three fields, judged from the WHOLE request's words (not from the slot alone -- the slot is a hint and may be wrong):

`content` -- what the data contains:
- `expression`: a gene-by-sample (or gene-by-cell) expression measurement table -- RNA-seq, microarray, counts, TPM; raw, normalized or transformed.
- `other_omics`: another per-sample continuous omics measurement table -- proteomics, methylation, metabolomics, copy-number values, chromatin accessibility, etc.
- `coexpression_matrix`: a gene-by-gene correlation or co-expression matrix (aggregate or per-sample, adjusted or not), whatever produced it.
- `tf_gene_prior`: prior TF-to-gene edges (a motif scan, ChIP-derived or curated TF-target prior).
- `mirna_prior`: prior miRNA-to-gene target edges.
- `protein_interactions`: a protein-protein or TF-TF interaction network.
- `regulator_gene_network`: an already-inferred regulator-to-target network, or another two-sided (bipartite) network given as edges or a matrix, e.g. a PANDA output, a GRN, SNP-gene eQTL edges.
- `gene_gene_network`: a gene-gene network that is not a co-expression or correlation matrix (e.g. a pathway graph).
- `somatic_mutation`: per-sample mutation calls or a mutation matrix.
- `sample_annotation`: clinical variables, a design or covariate matrix, group labels, survival, sample sheets.
- `gene_annotation`: gene lists, pathway sets (e.g. GMT), gene lengths or exon sizes.
- `other`: data whose kind the words state, but none of the above fits.
- `not_stated`: the words do not say what it contains (e.g. "my file", "the data from the core", "the output").

`made_by` -- what produced it, as the request states it:
- one of the 13 workflow names (PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, DRAGON, BONOBO, CONDOR, COBRA, OTTER, GIRAFFE, SAMBAR) when the request says that workflow produced it;
- `outside` when the request says or plainly implies it is measured data, a public resource, or the output of a non-NetZoo tool or person (a sequencing core, a consortium, WGCNA, a batch-correction tool, a collaborator's script);
- `not_stated` when the request does not say.

`certainty` -- `unsure` when the user says they are not sure, do not remember, or give alternatives for what this data contains or where it came from; otherwise `stated`.

Label only what the words say. Do not infer content from what a workflow would need. When a quote covers two pieces of data, label the main one and say so in `why`.

## Output

Write JSON to the output path named in your task:

{"labeller_note": "<one paragraph: what you read, conventions you used>",
 "units": [ {"id": "<request id>", "n": <unit index as given>, "content": "...", "made_by": "...", "certainty": "stated" | "unsure", "why": "<short; quote the words that decide it>"}, ... ] }

Every unit in the batch must get exactly one entry. Validate that the JSON parses, every (id, n) in the batch appears once, and every value is from the lists above.

Reply ONLY with counts: units labelled, and counts per content, per made_by and per certainty.

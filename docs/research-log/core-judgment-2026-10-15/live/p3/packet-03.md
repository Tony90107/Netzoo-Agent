## S740494

Request: Run OTTER with seed_W_mm.tsv, ppi_tf_mm.tsv and coexp_liver.tsv; I have no expression file, only that co-expression file. I can't remember if coexp_liver.tsv is the full gene-by-gene correlation matrix for the cohort or the edge-by-sample table from our earlier LIONESS co-expression run.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
● Preparing next step…
Before I choose a workflow, please tell me:
- Is coexp_liver.tsv the full gene-by-gene correlation matrix for the cohort?
  If yes: OTTER can do what you asked. If no: no registered workflow does it as you asked. (You wrote: "I can't remember if coexp_liver.tsv is the full gene-by-gene correlation matrix for the cohort or the edge-by-sample table from our earlier LIONESS co-expression run". OTTER's contract: "coexpression_file is an optional precomputed source supported by this agent's adapter, not by the official OTTER CLI/API signature. It must be a labeled symmetric square gene-by-gene matrix with exact row/column order".)

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "One fact decides your request; please tell me first.",
    "points": [
      "Is coexp_liver.tsv the full gene-by-gene correlation matrix for the cohort?"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S142779

Request: Run SAMBAR on mutations_ucec.csv (248 endometrial tumours in rows, genes in columns, non-negative mutation counts) with exon_lengths.csv, cancer_genes.txt and c2.cp.kegg.gmt (MSigDB format), all sharing the same gene symbols, and cluster the tumours into between 2 and 6 subtypes.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.46s)
● Matching registered workflows…
✓ Workflow — SAMBAR
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- SAMBAR inputs: error: mutation_file must be an existing regular file: [CHECKOUT]/mutations_ucec.csv
- SAMBAR inputs: error: exon_size_file must be an existing regular file: [CHECKOUT]/exon_lengths.csv
- SAMBAR inputs: error: cancer_gene_file must be an existing regular file: [CHECKOUT]/cancer_genes.txt
- SAMBAR inputs: error: pathway_file must be an existing regular file: [CHECKOUT]/c2.cp.kegg.gmt

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume [SESSION] after preparing the answer.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[]
````

## S279296

Request: Run PANDA on expr_ipf.tsv with motif_hg38.tsv and ppi_hs.tsv, but use cobra_out/adjusted_coexpression.tsv (COBRA's adjusted gene-by-gene matrix, already checked to have the same gene IDs and order as the expression file) as the co-expression input instead of PANDA's own Pearson correlation.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.55s)
● Matching registered workflows…
✓ Workflow — PANDA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: [CHECKOUT]/expr_ipf.tsv
- PANDA/PUMA inputs: error: motif file does not exist: [CHECKOUT]/motif_hg38.tsv
- PANDA/PUMA inputs: error: PPI file does not exist: [CHECKOUT]/ppi_hs.tsv
- coexpression_file: co-expression matrix could not be read: [Errno 2] No such file or directory: '[CHECKOUT]/cobra_out/adjusted_coexpression.tsv'

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume [SESSION] after preparing the answer.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[]
````

## S237521

Request: Using bulk expression and clinical follow-up for 400 lung adenocarcinoma patients, I need a model that predicts each new patient's overall-survival risk, something like a penalized Cox model that outputs a risk score, which I can then lock and apply to an external validation cohort of 150 patients from another hospital without refitting. Ideally the score would also show which genes drive the risk.

Complete recorded stdout:
````text
● Classifying requested outcome…
! Semantic routing unavailable
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "unresolved",
    "headline": "No registered workflow can do this: predict outcomes for new samples.",
    "points": [
      "No registered workflow builds a predictive model; per-sample results can only be its features."
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“I need a model that predicts each new patient's overall-survival risk…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "The backup check matched no registered workflow to this (not confirmed).",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“the score would also show which genes drive the risk.”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "The backup check matched no registered workflow to this (not confirmed).",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S287189

Request: Run DRAGON on expr_cll_layer.csv and methyl_cll_layer.csv (same 110 patient IDs in rows, no missing cells). One thing I'm unsure about: the methylation file is either the continuous beta values or the binarized methylated/unmethylated calls (0/1) that another group derived, and both versions were saved under that name.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.78s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "Run DRAGON on expr_cll_layer.csv and methyl_cll_layer.csv (same 110 patient IDs in rows, no missing cells)." -- available from DRAGON.
Not checked against the registered workflows: "One thing I'm unsure about: the methylation file is either the continuous beta values or the binarized methylated/unmethylated calls (0/1) that another group derived, and both versions were saved under that name."
The usual capability check could not run this turn, so a backup model read the request; nothing it found is confirmed.

You asked me to run DRAGON, but the capability check could not confirm this turn that DRAGON gives what you asked for. I have not planned the run.

Tell me to run DRAGON anyway, and I will then find your input files and show a preview; nothing runs until you approve it.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "general",
    "headline": "DRAGON was not planned: confirm the run you want first.",
    "points": [],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“One thing I'm unsure about: the methylation file is either the continuous…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "Not checked against the registered workflows.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
    "next_steps": [
      {
        "key": "plan-run_dragon",
        "label": "Plan DRAGON with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning DRAGON",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_dragon",
        "granularity": null,
        "resolution": "plan_workflow",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S287138

Request: Will DRAGON take my paired plasma proteomics and metabolomics tables (both with a header, the same 85 participant IDs in the first column, samples in rows, complete continuous values with no NAs) and write the partial-correlation network as an edge list rather than a matrix?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.36s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "write the partial-correlation network as an edge list rather than a matrix" -- available from DRAGON.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `network_file`: an

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "DRAGON fits your goal: cohort-level multi-omic network.",
    "points": [
      "Method: Partial-correlation network across two omics layers of the same samples.",
      "Needs: omics layer 1, omics layer 2.",
      "Produces: multi-omic network (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_dragon",
        "label": "Plan DRAGON with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning DRAGON",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_dragon",
        "granularity": null,
        "resolution": "plan_workflow",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S383472

Request: Call somatic SNVs and indels from tumour_07.bam against its matched normal_07.bam and give me a filtered VCF.

Complete recorded stdout:
````text
● Classifying requested outcome…
! Semantic routing unavailable
What I understood you are asking for:
1. "give me a filtered VCF" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "capability_gap",
    "headline": "No registered workflow produces what you asked for, so none is offered.",
    "points": [],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“give me a filtered VCF”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "Not matched to any registered workflow.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S904491

Request: Run SAMBAR on mut_pilot.csv (mutation counts for 5 cholangiocarcinomas) with exon_len.csv, cancer_genes.txt and hallmark.gmt, testing every subtype number from 2 through 8.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Workflow — SAMBAR
✓ Guidance prepared
What I understood you are asking for:
1. "testing every subtype number from 2 through 8" -- available from SAMBAR.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

Why this recommendation:

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

**SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Outputs:

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "SAMBAR fits your goal: cohort-level set of sample subtypes.",
    "points": [
      "Method: Pathway-level mutation scores, then patient subtypes by clustering.",
      "Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.",
      "Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_sambar",
        "label": "Plan SAMBAR with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning SAMBAR",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_sambar",
        "granularity": null,
        "resolution": "plan_workflow",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S364927

Request: Is DRAGON able to link fecal metabolomics with colon-biopsy transcriptomics for our IBS study? Both tables are complete and continuous, but the metabolomics came from the 2023 recruitment wave and the biopsies may have been taken from a different group of volunteers; I'm still waiting to hear from the clinic whether they're the same 58 people.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.68s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the biopsies from the same 58 people as the metabolomics samples?
  If yes: DRAGON can do what you asked. If no: no registered workflow does it as you asked. (You wrote: "the biopsies may have been taken from a different group of volunteers; I'm still waiting to hear from the clinic whether they're the same 58 people". DRAGON's contract: "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven".)

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "One fact decides your request; please tell me first.",
    "points": [
      "Are the biopsies from the same 58 people as the metabolomics samples?"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S112073

Request: Please run LIONESS-PUMA on expr_cll.tsv (36 CLL patients), motif_cll.txt, ppi_cll.txt, mir_targets.txt and mir_list.txt (one miRNA ID per line, every one present in the first column of mir_targets.txt) to get a TF/miRNA-to-gene network for every patient.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.13s)
● Matching registered workflows…
✓ Workflow — LIONESS-PUMA
● Preparing next step…
? Clarification needed
  Input required

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.

Select input 1 of 1: MiRNA list (mirna_file)
Enter a candidate number or a full path.
1. mir_targets.txt
2. mir_list.txt
Selection > 
Run the command again with --resume [SESSION] after preparing the answer.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[]
````

## S688980

Request: I need a gene co-expression network for each of our 9 periodontitis gingival biopsies, with a p-value for every edge so I can filter them per sample. The matrix (genes in rows, sample IDs in the header) has been mean-centered per gene, but it came from a collaborator and I can't tell whether the values were log-transformed before centering.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.92s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Were the values log-transformed before centering?
  If yes: BONOBO can do what you asked. If no: no registered workflow does it as you asked. (You wrote: "I can't tell whether the values were log-transformed before centering". BONOBO's contract: "the agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression".)

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "One fact decides your request; please tell me first.",
    "points": [
      "Were the values log-transformed before centering?"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S449311

Request: Can GIRAFFE estimate an activity score for every transcription factor in each of our 30 psoriasis skin samples? I have the gene-by-sample expression table, a TF-by-gene motif prior and a TF-TF PPI matrix with matching identifiers.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.17s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "Can GIRAFFE estimate an activity score for every transcription factor in each of our 30 psoriasis skin samples?" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

**GIRAFFE** — Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "GIRAFFE fits your goal: cohort-level TF activity matrix.",
    "points": [
      "Method: Also estimates per-sample TF activity and signed activating/repressing effects.",
      "Needs: expression matrix, motif prior, PPI network.",
      "Produces: regulatory network and TF activity matrix (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_giraffe",
        "label": "Plan GIRAFFE with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning GIRAFFE",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_giraffe",
        "granularity": null,
        "resolution": "plan_workflow",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S946284

Request: For each of our 40 kidney cancer patients I need one number per transcription factor that captures that TF's regulatory strength in that patient, so we can relate it to survival. We have expression, a motif prior and a TF-TF PPI. I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or how active the TF is; my PI used both phrasings.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Do you want to measure how active the TF is?
  If yes: GIRAFFE can do what you asked. If no: no registered workflow does it as you asked. (You wrote: "I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or how active the TF is; my PI used both phrasings". GIRAFFE's contract: "R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression".)

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "One fact decides your request; please tell me first.",
    "points": [
      "Do you want to measure how active the TF is?"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S795233

Request: Reviewers asked for 'a network analysis' of our placenta study. We have mRNA-seq and small-RNA-seq from 45 preeclampsia and control placentas. Honestly I don't know what kind of network they expect or what it's supposed to show. The two groups are roughly balanced and both libraries come from the same placentas; can you set something up that would satisfy them?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.50s)
● Matching registered workflows…
● Preparing next step…
What I understood you are asking for:
1. "'a network analysis'" -- not matched to any registered workflow.
2. "can you set something up that would satisfy them?" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "capability_gap",
    "headline": "No registered workflow produces what you asked for, so none is offered.",
    "points": [
      "Understood: \"'a network analysis'\"",
      "Understood: \"can you set something up that would satisfy them?\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“'a network analysis'”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "Not matched to any registered workflow.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“can you set something up that would satisfy them?”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "Not matched to any registered workflow.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S948971

Request: Could you help me see how genes are connected in my sorghum heat-stress experiment?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.50s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "see how genes are connected" -- available from LIONESS-COEXPRESSION.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "3 registered workflows fit; one detail about your study decides between them.",
    "points": [
      "Understood goal: a co-expression network."
    ],
    "choices": {
      "header": "Scale",
      "question": "Should the result be aggregate or sample-specific?",
      "options": [
        {
          "key": "granularity-2",
          "label": "One network per sample (plus the cohort network)",
          "description": "Leads to LIONESS-COEXPRESSION · Lets you compare samples, or relate them to outcomes such as survival",
          "answer": "One network per sample (plus the cohort network)",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_coexpression",
          "granularity": "sample_specific",
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "granularity-1",
          "label": "One cohort-wide network",
          "description": "Leads to COBRA",
          "answer": "One cohort-wide network",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_cobra",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "granularity-3",
          "label": "One network per sample",
          "description": "Leads to BONOBO · Lets you compare samples, or relate them to outcomes such as survival",
          "answer": "One network per sample",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_bonobo",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "Each answer lists the workflows it leads to."
    },
    "unavailable": [],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

## S313492

Request: Run the TF network inference on expr_alzheimer.tsv (88 donors: 44 AD, 44 controls), motifs_hg38.txt and ppi_tf.txt. The analysis plan just says 'a network for each AD and control', and I can't tell if that means one network per diagnostic group or one network per donor; the person who wrote it is on leave until next month.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (7.41s)
● Matching registered workflows…
● Preparing next step…
Before I choose a workflow, please tell me:
- Does the analysis plan mean one network per diagnostic group?
  If yes: OTTER can do what you asked. If no: no registered workflow does it as you asked. (You wrote: "The analysis plan just says 'a network for each AD and control', and I can't tell if that means one network per diagnostic group or one network per donor;". OTTER's contract: "OTTER's official reader/merging behavior is otherwise permissive and its README warns that NAs and non-intersection inputs need care".)

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "One fact decides your request; please tell me first.",
    "points": [
      "Does the analysis plan mean one network per diagnostic group?"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "new-task",
        "label": "Start a new task",
        "description": "Clear this goal and describe a different one.",
        "answer": "new",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "command",
        "paths": [],
        "compare_actions": []
      }
    ],
    "ran_nothing": true
  }
]
````

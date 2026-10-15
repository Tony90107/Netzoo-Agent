## S406543

Requirements to judge (user words):
R1: LIONESS-DRAGON process all feature pairs

Request (turn 1): The data management team has not finished the export for this project, and I cannot infer the number of measured features from its working filename. There are two plausible releases: a compact targeted panel and a large untargeted panel. Both releases have the same participants and would otherwise satisfy the paired-table requirements. Our funding milestone requires retaining every pair of features and every participant in a single run. Reducing the panel, dropping people, or splitting the requested output into multiple independent runs has not been approved. I need a capability judgment that waits for the size fact rather than assuming the smaller release. Can LIONESS-DRAGON process all feature pairs for our 100 participants? There are either 100 or 1000 total features across the two layers; the export manifest has not arrived.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.58s)
● Matching registered workflows…
✓ Workflow — DRAGON → LIONESS-DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "I need a capability judgment that waits for the size fact rather than assuming the smaller release." -- the backup check matched no registered workflow to this (not confirmed).
2. "Can LIONESS-DRAGON process all feature pairs for our 100 participants?" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **LIONESS-DRAGON** — produces: One two-layer partial-correlation network per sample, plus the aggregate.
- **DRAGON** — produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "method_choice",
    "headline": "Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.",
    "points": [
      "Compare what each produces with what you asked for; asking again re-runs the check."
    ],
    "choices": {
      "header": "Workflow",
      "question": "Which one do you want to look at?",
      "options": [
        {
          "key": "run_lioness_dragon",
          "label": "LIONESS-DRAGON",
          "description": "Not confirmed. Produces: One two-layer partial-correlation network per sample, plus the aggregate.",
          "answer": "Explain what LIONESS-DRAGON produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_dragon",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_dragon",
          "label": "DRAGON",
          "description": "Not confirmed. Produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted…",
          "answer": "Explain what DRAGON produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_dragon",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "In routing's order; none is confirmed or recommended."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“I need a capability judgment that waits for the size fact rather than…",
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
        "label": "“Can LIONESS-DRAGON process all feature pairs for our 100 participants?”",
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
Judge the final turn using the preceding context.

## S696167

Requirements to judge (user words):
R1: 整批樣本的 TF/miRNA 調控網路

Request (turn 1): 請執行 PUMA，整合珊瑚壓力實驗的 expression.tsv、prior.tsv、ppi.tsv 與 mirna_ids.txt，輸出整批樣本的 TF/miRNA 調控網路到 coral.tsv。各檔案已驗證且識別碼相容。

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.96s)
● Matching registered workflows…
✓ Workflow — PUMA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: [CHECKOUT]/expression.tsv
- PANDA/PUMA inputs: error: motif file does not exist: [CHECKOUT]/prior.tsv
- PANDA/PUMA inputs: error: PPI file does not exist: [CHECKOUT]/ppi.tsv
- PANDA/PUMA inputs: error: miRNA file does not exist: [CHECKOUT]/mirna_ids.txt

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume [SESSION] after preparing the answer.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[]
````
Judge the final turn using the preceding context.

## S248423

Requirements to judge (user words):
R1: PANDA use covariance_bundle.tsv as coexpression_file

Request (turn 1): Can PANDA use covariance_bundle.tsv as coexpression_file alongside our valid expression, motif and PPI files? All gene IDs and dimensions match, but the analyst has not confirmed whether the square matrix is symmetric or asymmetric; no repair is authorized.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.05s)
● Matching registered workflows…
✓ Guidance prepared
PANDA: Infer an aggregate TF-to-gene regulatory network with PANDA.
Registered required inputs: expression_file, motif_file, ppi_file, output_file.
Registered workflow controls: with_header (type=boolean, default=False).
Output: aggregate TF-to-gene regulatory networks.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "general",
    "headline": "",
    "points": [],
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
Judge the final turn using the preceding context.

## S394153

Requirements to judge (user words):
R1: without any miRNA list or miRNA identifiers

Request (turn 1): Can LIONESS-PUMA produce its networks without any miRNA list or miRNA identifiers in the regulator prior, while still claiming miRNA regulation?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.74s)
● Matching registered workflows…
✓ Guidance prepared
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

**Data your question needs.** Your question needs a miRNA list, which your request does not mention. Do you have a miRNA list?

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "method_choice",
    "headline": "4 registered methods can build a regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.",
    "points": [
      "Understood goal: a regulatory network.",
      "Your request names the data I described; the matched workflows also need more inputs."
    ],
    "choices": {
      "header": "Inputs",
      "question": "Do you also have a motif prior and a PPI network?",
      "options": [
        {
          "key": "inputs-named",
          "label": "Only the data I described",
          "description": "Ask what the data you named can give instead",
          "answer": "I only have the data I described.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": null,
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "inputs-more",
          "label": "I also have a motif prior and a PPI network",
          "description": "Continues with the workflows this reply names",
          "answer": "I also have a motif prior and a PPI network.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": null,
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "The option that uses only the data you named comes first."
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
Judge the final turn using the preceding context.

## S506505

Requirements to judge (user words):
R1: RNA expression in place of somatic mutations

Request (turn 1): Can SAMBAR use RNA expression in place of somatic mutations to calculate mutation-burden-normalized pathway scores?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.61s)
● Matching registered workflows…
✓ Workflow — SAMBAR
✓ Guidance prepared
Selected path: **SAMBAR**.

Your question asks for a cohort-level pathway mutation matrix. **SAMBAR** fits that result and scale. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization.

Captured request parameters:

- `mutation_file`: calculate

Why this recommendation:

Patient mutation burden normalization rescales each patient's mutation scores relative to their overall mutation burden, so total burden does not dominate the comparison. This is a relative score normalization, not a clinical TMB estimate or a correction for every sequencing bias.

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

**SAMBAR**: Subtype somatic-mutation samples through pathway mutation scores with SAMBAR.

Routing-level input modality: somatic mutation.

Method premise: derive patient or tumor subtypes; produce pathway-level mutation scores; analyze somatic mutation measurements.

SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

Required workflow inputs:

- `mutation_file`: somatic mutation matrix
- `exon_size_file`: gene/exon-size CSV
- `cancer_gene_file`: cancer-gene list
- `pathway_file`: GMT pathway file

Other declared controls (not matched to this request; defaults apply unless you set them): `norm_patient`=True, `kmin`=2, `kmax`=4, `gmt_msigdb`=True, `subset_cancer_genes`=True, `distance`=binomial, `linkage`=complete, `cluster`=True.

Distinct declared output artifacts (availability depends on workflow options):

- `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
- `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
- `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
- `sample_distance_matrix`: Pairwise sample distances, not cluster labels.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "SAMBAR fits your goal: cohort-level pathway mutation score matrix.",
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
Judge the final turn using the preceding context.

## S113098

Requirements to judge (user words):
R1: user-selected learning rate of 0.07 and exactly 11 optimization iterations

Request (turn 1): Does this agent expose GIRAFFE with a user-selected learning rate of 0.07 and exactly 11 optimization iterations?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.40s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "learning rate of 0.07" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "learning rate of 0.07" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can run this with the setting you asked for (above). This workflow can run it with its own settings instead:
- **GIRAFFE** — for "learning rate of 0.07"; produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Tell me to use it with its own settings, or ask about another setting.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "Your request was not mapped to a result any registered workflow produces, so no workflow is offered.",
    "points": [
      "Understood: \"learning rate of 0.07\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“learning rate of 0.07”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so \"learning rate of 0.07\" cannot be applied.",
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
Judge the final turn using the preceding context.

## S388046

Requirements to judge (user words):
R1: run CONDOR on binding_edges.tsv

Request (turn 1): Please run CONDOR on binding_edges.tsv, a validated source,target,weight bipartite TF-gene edge list with disjoint source and target identifiers, and save the separate memberships under out/beetle/.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.60s)
● Matching registered workflows…
✓ Workflow — CONDOR
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- CONDOR network: error: CONDOR network file does not exist: [CHECKOUT]/binding_edges.tsv

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume [SESSION] after preparing the answer.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[]
````
Judge the final turn using the preceding context.

## S821159

Requirements to judge (user words):
R1: Run LIONESS-DRAGON

Request (turn 1): Run LIONESS-DRAGON on two valid-format layers for the mosquito diapause study. They may contain two or ten paired samples; that count is not yet known.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.10s)
● Matching registered workflows…
✓ Matched workflows — DRAGON, LIONESS-DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "Run LIONESS-DRAGON on two valid-format layers for the mosquito diapause study." -- depends on how many independent samples are available, which you said you do not know ("They may contain two or ten paired samples; that count is not yet known."): if 2 samples: no registered workflow gives this; if 10 samples: LIONESS-DRAGON.
2. "They may contain two or ten paired samples; that count is not yet known." -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Before I choose a workflow, please tell me: How many independent biological samples are available for this result?

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "clarification",
    "headline": "One fact about your data decides which workflow applies.",
    "points": [
      "How many independent biological samples are available for this result?"
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“They may contain two or ten paired samples; that count is not yet known.”",
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
Judge the final turn using the preceding context.

## S586666

Requirements to judge (user words):
R1: signed R and sample-varying TFA
R2: exposed custom optimizer learning rate of 0.009

Request (turn 1): Run GIRAFFE with all validated priors to produce signed R and sample-varying TFA, and use an exposed custom optimizer learning rate of 0.009.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.50s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "signed R" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "exposed custom optimizer learning rate" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.
2. "sample-varying TFA" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "exposed custom optimizer learning rate" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

You asked me to run GIRAFFE, but it cannot run as you asked (above), so the run would not do what you asked. I have not planned it.

Tell me to run GIRAFFE anyway, and I will then find your input files and show a preview; nothing runs until you approve it.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "general",
    "headline": "GIRAFFE was not planned: confirm the run you want first.",
    "points": [],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“signed R”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so \"exposed custom optimizer learning rate\" cannot be applied.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“sample-varying TFA”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so \"exposed custom optimizer learning rate\" cannot be applied.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
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
Judge the final turn using the preceding context.

## S524963

Requirements to judge (user words):
R1: edge list with partial_correlation and precision columns
R2: directly feed this multi-omic graph to PUMA without a conversion

Request (turn 1): Can DRAGON export its aggregate edge list with partial_correlation and precision columns, and directly feed this multi-omic graph to PUMA without a conversion?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.88s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
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
Judge the final turn using the preceding context.

## S366297

Requirements to judge (user words):
R1: COBRA adjusted co-expression matrix in aggregate PANDA

Request (turn 1): The sequencing was performed on several plates over the course of a month. The experimental design includes biological groups on each plate, and the team has already checked that group and plate are not completely confounded. We want the analysis plan to make the adjustment explicit so that the downstream regulatory graph is based on the approved adjusted co-expression artifact. The manuscript will report which artifact is passed between steps, and the collaborator reviewing the plan will independently inspect the gene identifiers. We do not need you to interpret any disease association in this request. Can we use a COBRA adjusted co-expression matrix in aggregate PANDA for a coastal fish cohort? We retain the original expression table and priors and will revalidate filtered gene IDs before the handoff.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.48s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "We want the analysis plan to make the adjustment explicit so that the downstream regulatory graph is based on the approved adjusted co-expression artifact." -- not available here as asked. NetZoo's PANDA does not give this result. COBRA gives this result with its own method instead -- an alternative, not "PANDA".
2. "The manuscript will report which artifact is passed between steps" -- not available here: no registered workflow produces this. Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.

No registered workflow can give these as you asked them (above), so none is offered as asked.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "capability_gap",
    "headline": "No registered workflow produces what you asked for, so none is offered.",
    "points": [
      "Understood: \"We want the analysis plan to make the adjustment explicit so that the downstream regulatory graph is based on the approved adjusted co-expression artifact.\"",
      "Understood: \"The manuscript will report which artifact is passed between steps\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“We want the analysis plan to make the adjustment explicit so that the…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's PANDA does not give this result.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“The manuscript will report which artifact is passed between steps”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
    "next_steps": [
      {
        "key": "capabilities",
        "label": "Show what NetZoo can do here",
        "description": "Lists the registered workflows and what each produces.",
        "answer": "Which analyses can the registered NetZoo workflows run, and what does each produce?",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "follow_up",
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
Judge the final turn using the preceding context.

## S574189

Requirements to judge (user words):
R1: Select sample IDs H2 and H5, save CSV networks

Request (turn 1): Run BONOBO on centered_log.tsv: a validated, labeled, log-transformed and centered gene-by-sample matrix with seven samples. Select sample IDs H2 and H5, save CSV networks, and leave sparsify=false.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.96s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "Run BONOBO on centered_log.tsv: a validated, labeled, log-transformed and centered gene-by-sample matrix with seven samples." -- available from BONOBO.
Not checked against the registered workflows: "Select sample IDs H2 and H5"

You asked me to run BONOBO, but part of your request was not checked against what BONOBO gives (above). I have not planned the run.

Tell me to run BONOBO anyway, and I will then find your input files and show a preview; nothing runs until you approve it.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "general",
    "headline": "BONOBO was not planned: confirm the run you want first.",
    "points": [],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Select sample IDs H2 and H5”",
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
        "key": "plan-run_bonobo",
        "label": "Plan BONOBO with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning BONOBO",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_bonobo",
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
Judge the final turn using the preceding context.

## S672667

Requirements to judge (user words):
R1: aggregate PUMA on COBRA-adjusted co-expression

Request (turn 1): Can I run aggregate PUMA on COBRA-adjusted co-expression after validating the gene axes, while keeping the original expression, combined regulator prior, PPI and miRNA list?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.86s)
● Matching registered workflows…
✓ Workflow — PUMA
✓ Guidance prepared
What I understood you are asking for:
1. "Can I run aggregate PUMA on COBRA-adjusted co-expression after validating the gene axes, while keeping the original expression, combined regulator prior, PPI and miRNA list?" -- available from PUMA.

Selected path: **PUMA**.

**PUMA** — Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "PUMA produces a regulatory network (one cohort-level result).",
    "points": [
      "Method: PANDA's message passing with miRNA regulators added.",
      "Needs: expression matrix, motif prior, PPI network, miRNA list.",
      "Produces: regulatory network (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_puma",
        "label": "Plan PUMA with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning PUMA",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_puma",
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
Judge the final turn using the preceding context.

## S530847

Requirements to judge (user words):
R1: run CONDOR on binding_edges.tsv

Request (turn 1): Please run CONDOR on binding_edges.tsv, a validated source,target,weight bipartite TF-gene edge list with disjoint source and target identifiers, and save the separate memberships under out/beetle/.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.30s)
● Matching registered workflows…
✓ Workflow — CONDOR
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- CONDOR network: error: CONDOR network file does not exist: [CHECKOUT]/binding_edges.tsv

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume [SESSION] after preparing the answer.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[]
````
Judge the final turn using the preceding context.

## S118742

Requirements to judge (user words):
R1: straight into PANDA coexpression_file

Request (turn 1): Feed BONOBO per-sample matrices straight into PANDA coexpression_file without selecting, aggregating, converting or validating them.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.50s)
● Matching registered workflows…
✓ Matched workflows — BONOBO
✓ Guidance prepared
? Clarification needed
  Input required

The requested BONOBO → PANDA handoff is blocked: the registered consumer schema does not explicitly accept BONOBO's sample-specific gene-gene co-expression artifact with the same granularity. No execution is permitted.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume [SESSION] after preparing the answer.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[]
````
Judge the final turn using the preceding context.

## S110200

Requirements to judge (user words):
R1: GIRAFFE meet the requirement for an individual result

Request (turn 1): The study combines several seedling samples and asks for a result that differs between individuals. In discussions, the authors have used the words regulation, activity, and personalized network interchangeably, and that has made the planned deliverable unclear. The expression matrix and both biological priors have already passed the file checks, so requesting another file will not settle the issue. Before recommending an execution path, we need to identify what numerical object the authors intend to compare across the individual samples. Please keep the unresolved scientific endpoint visible rather than silently selecting one interpretation. Can GIRAFFE meet the requirement for an individual result in our beet-root paper? The authors have not decided whether individual means TF activity per sample or a different regulatory wiring matrix per sample.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Matched workflows — GIRAFFE, LIONESS-PANDA
✓ Guidance prepared
What I understood you are asking for:
1. "Can GIRAFFE meet the requirement for an individual result in our beet-root paper?" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

For your question ("result that differs between individuals"):
- **LIONESS-PANDA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "method_choice",
    "headline": "Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.",
    "points": [
      "Compare what each produces with what you asked for; asking again re-runs the check.",
      "Your question: which individuals change or stand out; the reply says what LIONESS-PANDA give toward it and the step after each."
    ],
    "choices": {
      "header": "Workflow",
      "question": "Which one do you want to look at?",
      "options": [
        {
          "key": "run_giraffe",
          "label": "GIRAFFE",
          "description": "Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.",
          "answer": "Explain what GIRAFFE produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_giraffe",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_lioness_panda",
          "label": "LIONESS-PANDA",
          "description": "Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.",
          "answer": "Explain what LIONESS-PANDA produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_panda",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "In routing's order; none is confirmed or recommended."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Can GIRAFFE meet the requirement for an individual result in our beet-root…",
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
Judge the final turn using the preceding context.

## S391035

Requirements to judge (user words):
R1: LIONESS-PUMA for the 36-sample gill response study

Request (turn 1): I need LIONESS-PUMA for the 36-sample gill response study, but the miRNA identifier list is still with my collaborator. Expression, motif and PPI files are ready. Please list the remaining input needed before execution.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Workflow — PUMA → LIONESS-PUMA
✓ Guidance prepared
What I understood you are asking for:
1. "I need LIONESS-PUMA for the 36-sample gill response study" -- available from LIONESS-PUMA.

Selected path: **LIONESS-PUMA**.

**LIONESS-PUMA** — Infer aggregate PUMA and sample-specific LIONESS-PUMA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a miRNA list, and you said you do not know whether your data has it ("the miRNA identifier list is still with my collaborator"). Does it?

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "LIONESS-PUMA produces a regulatory network (cohort-level and per-sample).",
    "points": [
      "Method: One TF + miRNA network per sample, derived leave-one-out from the cohort.",
      "Needs: expression matrix, motif prior, PPI network, miRNA list.",
      "Cost: N samples take N+1 PUMA runs.",
      "Produces: regulatory network (cohort-level and per-sample).",
      "It also writes the cohort network, so PUMA need not run first."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_lioness_puma",
        "label": "Plan LIONESS-PUMA with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning LIONESS-PUMA",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_lioness_puma",
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
Judge the final turn using the preceding context.

## S168988

Requirements to judge (user words):
R1: save full networks plus p-value matrices
R2: already-thresholded networks without postprocessing

Request (turn 1): Can BONOBO save full networks plus p-value matrices with sparsify=true/save_pvals=true and also return already-thresholded networks without postprocessing?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.99s)
● Matching registered workflows…
✓ Guidance prepared
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "method_choice",
    "headline": "6 registered methods can build a regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.",
    "points": [
      "Understood goal: a regulatory network.",
      "LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA, OTTER, GIRAFFE and PUMA give one across all samples.",
      "Nothing you said favours one method yet; each option says when to pick it.",
      "Picking an option explains it for your data and what it needs; nothing runs."
    ],
    "choices": {
      "header": "Method",
      "question": "Which method fits your study?",
      "options": [
        {
          "key": "run_panda",
          "label": "PANDA",
          "description": "One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS",
          "answer": "Use PANDA",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_panda",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_lioness_panda",
          "label": "LIONESS-PANDA",
          "description": "One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample",
          "answer": "Use LIONESS-PANDA",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_panda",
          "granularity": "sample_specific",
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_otter",
          "label": "OTTER",
          "description": "The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern",
          "answer": "Use OTTER",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_otter",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_giraffe",
          "label": "GIRAFFE",
          "description": "One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level",
          "answer": "Use GIRAFFE",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_giraffe",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_puma",
          "label": "PUMA",
          "description": "One TF + miRNA network across all your samples · Pick it if the regulators include miRNAs · Also needs miRNA list",
          "answer": "Use PUMA",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_puma",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_lioness_puma",
          "label": "LIONESS-PUMA",
          "description": "One TF + miRNA network per sample, plus the cohort network · Pick it if the regulators include miRNAs · Also needs miRNA list",
          "answer": "Use LIONESS-PUMA",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_puma",
          "granularity": "sample_specific",
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "Options that match more of what you asked for, and use only data you mentioned, come first."
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
Judge the final turn using the preceding context.

## S824917

Requirements to judge (user words):
R1: aggregate signed regulatory coefficient matrix and TF activities

Request (turn 1): Can GIRAFFE jointly estimate the aggregate signed regulatory coefficient matrix and TF activities for our pancreatic differentiation samples? We will provide gene expression, motif priors and a TF interaction prior.

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.19s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "aggregate signed regulatory coefficient matrix" -- available from GIRAFFE.
2. "TF activities" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level regulatory network with TF activities. **GIRAFFE** fits that result and scale.

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

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "GIRAFFE fits your goal: cohort-level regulatory network with TF activities.",
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
Judge the final turn using the preceding context.

## S496986

Requirements to judge (user words):
R1: labeled TF-by-gene prior matrix and a labeled square symmetric PPI matrix

Request (turn 1): We only need the activity of TFs across samples, together with the shared signed R coefficients. Can GIRAFFE use a labeled TF-by-gene prior matrix and a labeled square symmetric PPI matrix if their IDs match expression exactly?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.82s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "activity of TFs across samples" -- available from GIRAFFE.
2. "shared signed R coefficients" -- available from GIRAFFE.
3. "We only need the" -- available from GIRAFFE.
4. "together with the" -- available from GIRAFFE.

The capability check identified workflows for every result you asked for:
- **GIRAFFE** — for "activity of TFs across samples"; produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Choose a result to discuss with its workflow.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "method_choice",
    "headline": "The capability check identified workflows for every result you asked for.",
    "points": [
      "Understood: \"activity of TFs across samples\"",
      "Understood: \"shared signed R coefficients\"",
      "Understood: \"We only need the\"",
      "Understood: \"together with the\""
    ],
    "choices": {
      "header": "Workflow",
      "question": "Which result do you want to discuss?",
      "options": [
        {
          "key": "run_giraffe",
          "label": "GIRAFFE",
          "description": "For \"activity of TFs across samples\": A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.",
          "answer": "Explain how GIRAFFE addresses this result: activity of TFs across samples. Keep the other requirements separate and do not execute it yet.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_giraffe",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "In the order of the parts of your request."
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
Judge the final turn using the preceding context.

## S355050

Requirements to judge (user words):
R1: population TF-gene network
R2: TF-by-sample activity matrix

Request (turn 1): Can PANDA infer our population TF-gene network and also give a TF-by-sample activity matrix from the same native output?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.27s)
● Matching registered workflows…
✓ Workflow — PANDA
✓ Guidance prepared
What I understood you are asking for:
1. "infer our population TF-gene network" -- available from PANDA.
2. "give a TF-by-sample activity matrix" -- not available here as asked. NetZoo's PANDA does not give this result. GIRAFFE gives this result with its own method instead -- an alternative, not "PANDA".

Selected path: **PANDA**.

**PANDA** — Infer an aggregate TF-to-gene regulatory network with PANDA. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "PANDA produces a regulatory network (one cohort-level result).",
    "points": [
      "Method: Widely used baseline: message passing over motif, PPI and co-expression evidence.",
      "Needs: expression matrix, motif prior, PPI network.",
      "Produces: regulatory network (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“give a TF-by-sample activity matrix”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's PANDA does not give this result.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
    "next_steps": [
      {
        "key": "plan-run_panda",
        "label": "Plan PANDA with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning PANDA",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_panda",
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
Judge the final turn using the preceding context.

## S207062

Requirements to judge (user words):
R1: full per-sample co-expression matrices and matching approximate p-value matrices

Request (turn 1): For a frog regeneration study, can BONOBO save full per-sample co-expression matrices and matching approximate p-value matrices together by using sparsify=true and save_pvals=true?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.15s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "full per-sample co-expression matrices" -- available from BONOBO.
2. "matching approximate p-value matrices" -- available from BONOBO.
3. "can BONOBO save" -- available from BONOBO.

Selected path: **BONOBO**.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

Captured request parameters:

- `sparsify`: true
- `save_pvals`: true

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `sparsify`=False, `bonobo_confidence`=0.05, `save_pvals`=False, `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "BONOBO fits your goal: per-sample co-expression network.",
    "points": [
      "Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.",
      "Needs: expression matrix.",
      "Produces: co-expression network and p-value matrix (one per sample)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_bonobo",
        "label": "Plan BONOBO with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning BONOBO",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_bonobo",
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
Judge the final turn using the preceding context.

## S752648

Requirements to judge (user words):
R1: 用 DRAGON 分析這兩份新生兒資料

Request (turn 1): 能用 DRAGON 分析這兩份新生兒資料嗎？一份是連續數值；另一份是否含缺失值還沒確認，而且本研究禁止補值或刪除觀測。

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.02s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "能用 DRAGON 分析這兩份新生兒資料嗎？" -- available from DRAGON.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "DRAGON produces a multi-omic network (one cohort-level result).",
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
Judge the final turn using the preceding context.

## S491427

Requirements to judge (user words):
R1: networks for each of our 16 paired samples
R2: third independent cross-layer shrinkage knob

Request (turn 1): Can LIONESS-DRAGON make networks for each of our 16 paired samples while exposing a third independent cross-layer shrinkage knob?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.78s)
● Matching registered workflows…
! Fallback recommendation — not an exact semantic match
✓ Guidance prepared
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

**DRAGON** — Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "DRAGON is the closest registered match, but it is not a verified match for your request.",
    "points": [
      "Method: Partial-correlation network across two omics layers of the same samples.",
      "Needs: omics layer 1, omics layer 2.",
      "Produces: multi-omic network (one cohort-level result)."
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
Judge the final turn using the preceding context.

## S623007

Requirements to judge (user words):
R1: Bayesian sample-specific co-expression
R2: TF-by-sample activity matrix

Request (turn 1): For the eight validated expression samples, can BONOBO compute Bayesian sample-specific co-expression, while the same run emits a TF-by-sample activity matrix?

Complete recorded stdout (turn 1):
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.22s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Bayesian sample-specific co-expression" -- available from BONOBO.
2. "TF-by-sample activity matrix" -- not available here as asked. NetZoo's BONOBO does not give this result. GIRAFFE gives this result with its own method instead -- an alternative, not "BONOBO".

Based on what you said — "a TF-by-sample activity matrix" — **GIRAFFE** fits better: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed.

Your question asks for a per-sample co-expression network. **GIRAFFE** produces one result for the whole cohort instead.

**GIRAFFE** (recommend) — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values (one cohort-level result).

Conditional assumptions to confirm:
- This starting choice assumes a regulator scope of transcription factors; confirm this scope before analysis.
- It also needs an expression matrix and TF-motif prior and protein-interaction prior; no file for them is named yet.
- The user is primarily interested in obtaining a TF-by-sample activity matrix alongside co-expression insights.

Other compatible option(s):
- If you need a gene co-expression network instead: **LIONESS-COEXPRESSION**, **BONOBO**.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Should I use GIRAFFE, or does another listed option fit your study better?

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.

````

Complete recorded stderr (turn 1):
````text

````

Recorded reply cards (turn 1; empty means no card generated):
````json
[
  {
    "kind": "method_choice",
    "headline": "3 registered workflows fit your request; they differ in what they produce.",
    "points": [
      "Understood goal: a per-sample co-expression network.",
      "Recommended: GIRAFFE, from what you said.",
      "Picking an option explains it for your data and what it needs; nothing runs."
    ],
    "choices": {
      "header": "Method",
      "question": "Which method fits your study?",
      "options": [
        {
          "key": "run_giraffe",
          "label": "GIRAFFE",
          "description": "Fits what you said: TF activity may differ from its mRNA level · One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Also needs motif prior, PPI network",
          "answer": "Use GIRAFFE",
          "recommended": true,
          "badge": "Recommended",
          "available": true,
          "reason": "",
          "action": "run_giraffe",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_lioness_coexpression",
          "label": "LIONESS-COEXPRESSION",
          "description": "One gene co-expression network per sample, from expression data alone · Lets you compare samples, or relate them to outcomes such as survival",
          "answer": "Use LIONESS-COEXPRESSION",
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
          "key": "run_bonobo",
          "label": "BONOBO",
          "description": "One gene co-expression network per sample, with a p-value for each connection · Lets you compare samples, or relate them to outcomes such as survival · Pick it if you need a p-value for each edge",
          "answer": "Use BONOBO",
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
      "ordering": "Recommended first, from what you said."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“TF-by-sample activity matrix”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's BONOBO does not give this result.",
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
Judge the final turn using the preceding context.

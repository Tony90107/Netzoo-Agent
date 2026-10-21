## S510264

Request: Splitting 210 pancreatic tumours into molecular subtypes from their RNA-seq expression is the goal: summarise genes into pathway scores, then cluster the tumours into three to five groups. Only expression data are available - there are no mutation calls for this cohort.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.60s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Splitting 210 pancreatic tumours into molecular subtypes from their RNA-seq expression is the goal: summarise genes into pathway scores, then cluster the tumours into three to five groups." -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

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
        "label": "“Splitting 210 pancreatic tumours into molecular subtypes from their RNA-seq…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "SAMBAR does not give it: SAMBAR's input is somatic mutations.",
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

## S521774

Request: Proteomics and metabolomics on 50 mouse livers from a high-fat-diet experiment, with both layers measured on every animal: how could network approaches help me make sense of this?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.94s)
● Matching registered workflows…
✓ Guidance prepared
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

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
    "headline": "I need to know which result you want before choosing a workflow.",
    "points": [
      "Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?"
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

## S110203

Request: Execute COBRA on immune_panel_counts.csv - a custom 400-gene panel measured in 620 melanoma biopsies, gene-by-sample with labels - plus design.csv, which codes site and processing batch numerically for each biopsy ID. Results go to cobra_panel/.

Complete recorded stdout:
````text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
✓ Guidance prepared
What I understood you are asking for:
1. "Execute COBRA on" -- not available here as asked. COBRA requires more genes than samples; the request has 400 genes and 620 samples.

No registered workflow can give this as you asked it (above), so none is offered as asked.

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
        "label": "“Execute COBRA on”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "COBRA requires more genes than samples; the request has 400 genes and 620 samples.",
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

## S183684

Request: Time to run LIONESS-PANDA: twins_expr.tsv holds our two monozygotic twin samples (two columns), with motif_hs.txt and ppi_hs.txt as priors. Aggregate network to twins_agg.txt, per-sample networks to lioness_twins/, started today if possible.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.28s)
● Matching registered workflows…
? Clarification needed
Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **DRAGON** — produces: One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.
- **LIONESS-DRAGON** — produces: One two-layer partial-correlation network per sample, plus the aggregate.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
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
        },
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
        }
      ],
      "allow_other": true,
      "ordering": "In routing's order; none is confirmed or recommended."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“two monozygotic twin samples”",
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

## S333127

Request: Launch CONDOR on panda_lung_edges.tsv, please. It is our PANDA TF-to-gene network exported as source, target and weight columns and already thresholded, so every weight is positive and TF and gene IDs do not overlap. Output directory condor_lung/, prefix lung.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.80s)
● Matching registered workflows…
✓ Guidance prepared
What you asked for is not something a registered NetZoo workflow produces.

No registered workflow can give this as you asked, so none is offered as asked.

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
    "headline": "This cannot be done as you asked, so no workflow is offered for it.",
    "points": [],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "confirm-run_panda",
        "label": "Yes, use PANDA",
        "description": "Explains that workflow for this goal and what it needs; runs nothing.",
        "answer": "Yes, use PANDA",
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

## S334943

Request: I want SAMBAR to subtype our cholangiocarcinoma cohort from somatic mutations, trying between 2 and 6 subtypes. The catch: either 5 or 9 tumours passed sequencing QC, and I'm still waiting on the core's report to know which.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.25s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Which of these is right: 5 or 9?
  You wrote: "either 5 or 9 tumours".
  - 5: no registered workflow can do this as asked -- SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled
  - 9: SAMBAR can do this

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
      "Which of these is right: 5 or 9?"
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

## S359020

Request: I'd like DRAGON on liver proteomics (1,100 proteins) and VST RNA-seq (3,000 genes) from our diet study. What I can't tell you is whether the proteomics came from the same 40 mice as the RNA-seq; the core may have used a separate cohort fed the same diets.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.80s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Did the proteomics and RNA-seq come from the same 40 mice?
  You wrote: "whether the proteomics came from the same 40 mice as the RNA-seq". DRAGON's contract: "DRAGON consumes exactly two paired sample-by-feature continuous omics tables and produces one aggregate undirected multi-omic network".
- Was a separate cohort used for the proteomics?
  You wrote: "the core may have used a separate cohort fed the same diets". DRAGON's contract: "DRAGON consumes exactly two paired sample-by-feature continuous omics tables and produces one aggregate undirected multi-omic network".

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
      "Did the proteomics and RNA-seq come from the same 40 mice?",
      "Was a separate cohort used for the proteomics?"
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

## S134087

Request: Go ahead with SAMBAR on uterine_somatic.csv (6 tumours by about 19,000 genes, non-negative somatic mutation counts), exon_sizes.csv, cancer_genes.txt and h.all.v2023.1.Hs.symbols.gmt. Cluster with kmin 2 and kmax 6 - yes, kmax equals our tumour count - and put everything in sambar_uterine/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.50s)
● Matching registered workflows…
✓ Workflow — SAMBAR
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- SAMBAR inputs: error: mutation_file must be an existing regular file: [CHECKOUT]/uterine_somatic.csv
- SAMBAR inputs: error: exon_size_file must be an existing regular file: [CHECKOUT]/exon_sizes.csv
- SAMBAR inputs: error: cancer_gene_file must be an existing regular file: [CHECKOUT]/cancer_genes.txt
- SAMBAR inputs: error: pathway_file must be an existing regular file: [CHECKOUT]/h.all.v2023.1.Hs.symbols.gmt

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

## S933684

Request: Across 140 breast tumours I need an estimate of how active each transcription factor is in every tumour, independent of the TF's own transcript level, together with signed TF-gene effects that separate activation from repression. I have log-normalised gene-by-sample expression, a TF-by-gene motif matrix and a TF-TF protein interaction matrix, all with matching identifiers.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.25s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "estimate of how active each transcription factor is in every tumour, independent of the TF's own transcript level" -- available from GIRAFFE.
2. "signed TF-gene effects that separate activation from repression" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level regulatory network with TF activities. **GIRAFFE** fits that result and scale.

What you asked about:

- "independent of the TF's own transcript level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

## S907774

Request: I'm planning to use OTTER for an aggregate TF-to-gene network from zebrafish fin RNA-seq, with a motif seed and a TF-TF PPI edge list. Honestly, I don't know yet whether we'll have one sample or two - the second library is being re-sequenced after a failed run.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.82s)
● Matching registered workflows…
✓ Matched workflows — OTTER
● Preparing next step…
What I understood you are asking for:
1. "aggregate TF-to-gene network" -- depends on a number you gave candidates for ("one sample or two"): 1: no registered workflow can do this as asked -- NetZoo's OTTER does not give this result; 2: OTTER can do this.

Before I choose a workflow, please tell me: Which of these is right: 1 or 2?

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
    "headline": "One fact about your data decides which workflow applies.",
    "points": [
      "Which of these is right: 1 or 2?"
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

## S593031

Request: Our 230 glioblastoma RNA-seq samples (about 18,000 genes) were collected at four hospitals and sequenced in two batches. The aim is to quantify how much of the gene-gene co-expression is associated with hospital and with batch, and to get an adjusted co-expression matrix out of it. The design sheet codes both covariates numerically, keyed by the same sample IDs as the expression columns.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.49s)
● Matching registered workflows…
✓ Workflow — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "The aim is to quantify how much of the gene-gene co-expression is associated with hospital and with batch, and to get an adjusted co-expression matrix out of it." -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale. COBRA models co-expression as a function of sample covariates through conditional covariance estimation.

Captured request parameters:

- `expression_file`: columns

**COBRA**: Model covariate-associated gene co-expression with COBRA.

Routing-level input modality: expression matrix.

Method premise: remove or adjust technical batch effects; estimate how sample covariates change co-expression; model higher-order covariance or correlation structure; assess or remove hospital or site effects; assess or remove sequencing-batch effects.

COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.

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
    "headline": "COBRA fits your goal: cohort-level co-expression network.",
    "points": [
      "Picked from 2 fitting methods because you wrote “quantify how much of the gene-gene…”; LIONESS-COEXPRESSION also fit.",
      "Method: Separates how covariates (batch, site, condition) reshape co-expression.",
      "Needs: expression matrix, covariate design matrix.",
      "Produces: co-expression network (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "compare-others",
        "label": "Compare with LIONESS-COEXPRESSION",
        "description": "Explains how their assumptions differ and which fits your study; runs nothing.",
        "answer": "Compare COBRA with LIONESS-COEXPRESSION for this goal. How do their assumptions differ, and which fits my study?",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "compare_workflows",
        "paths": [],
        "compare_actions": [
          "run_cobra",
          "run_lioness_coexpression"
        ]
      },
      {
        "key": "plan-run_cobra",
        "label": "Plan COBRA with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning COBRA",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_cobra",
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

## S239208

Request: Can OTTER be switched to computing=gpu for us? The aggregate network covers 22,000 genes and 900 TFs, CPU runs take most of a day, and our cluster has idle A100 cards. Keep every other setting at its default.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.82s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "computing=gpu" -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

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
    "headline": "This cannot be done as you asked, so no workflow is offered for it.",
    "points": [
      "\"computing=gpu\" -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for."
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

## S166046

Request: Kick off SAMBAR with sarcoma_somatic.csv (7 tumours, somatic mutation counts per gene), exon_len.csv, cosmic_cgc.txt and kegg_msigdb.gmt. When clustering, try kmin 3 through kmax 9, and write the outputs to sambar_sarcoma/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (15.48s)
● Matching registered workflows…
? Clarification needed
Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **SAMBAR** — produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
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
          "key": "run_sambar",
          "label": "SAMBAR",
          "description": "Not confirmed. Produces: Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them -- with the scores, the cluster labels and the sample distance matrix.",
          "answer": "Explain what SAMBAR produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_sambar",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "In routing's order; none is confirmed or recommended."
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

## S592328

Request: Run SAMBAR on brca_variant_matrix.csv (310 patients by genes), exon_lengths.csv, cancer_genes.txt and c2.cp.kegg.gmt to get mutation-based subtypes. The matrix came from an old lab pipeline and I can't tell whether those are somatic calls or germline variants.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.77s)
● Matching registered workflows…
? Clarification needed
Before I choose a workflow, please tell me:
- Are the mutations in the brca_variant_matrix.csv somatic?
  You wrote: "I can't tell whether those are somatic calls or germline variants". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

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
      "Are the mutations in the brca_variant_matrix.csv somatic?"
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

## S314508

Request: Do the multi-omic analysis on rna_layer.csv and protein_layer.csv (same 72 patients) right away. There's no specific output in my head - just see what the two layers say together.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.33s)
● Matching registered workflows…
? Clarification needed
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

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
    "headline": "I need to know which result you want before choosing a workflow.",
    "points": [
      "Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?"
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

## S500574

Request: From matched liver transcriptomics and metabolomics in 80 mice, I need to establish which metabolites causally drive the expression of lipid-metabolism genes, including the direction of each effect, for a mechanistic figure in our paper.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.59s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "establish which metabolites causally drive the expression of lipid-metabolism genes, including the direction of each effect" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators. Every registered workflow estimates associations or model coefficients from observational data.

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
        "label": "“establish which metabolites causally drive the expression of lipid-metabolism…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "Registered regulatory workflows contain miRNA and TF regulators; none models other regulators.",
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

## S596980

Request: Set up per-sample networks on hnscc_expr.tsv (52 tumours); hs_motif.tsv and hs_ppi.tsv are in the same folder. My supervisor wrote 'one network per tumour', and it isn't clear to me whether she wants gene-gene co-expression networks or TF-to-gene regulatory networks. I'd like it running today.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.45s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Set up per-sample networks on hnscc_expr.tsv (52 tumours)" -- not matched to any registered workflow.
2. "it isn't clear to me whether she wants gene-gene co-expression networks or TF-to-gene regulatory networks." -- you have not chosen which result you want: if "gene-gene co-expression networks": LIONESS-COEXPRESSION or BONOBO; if "TF-to-gene regulatory networks": LIONESS-PANDA or LIONESS-PUMA.
3. "it isn't clear to me whether she wants gene-gene co-expression networks or TF-to-gene regulatory networks." -- you have not chosen which result you want: if "gene-gene co-expression networks": LIONESS-COEXPRESSION or BONOBO; if "TF-to-gene regulatory networks": LIONESS-PANDA or LIONESS-PUMA.

Before I choose a workflow, please tell me: Which result do you want: "gene-gene co-expression networks" or "TF-to-gene regulatory networks"?

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
    "headline": "One fact about your data decides which workflow applies.",
    "points": [
      "Which result do you want: \"gene-gene co-expression networks\" or \"TF-to-gene regulatory networks\"?"
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Set up per-sample networks on hnscc_expr.tsv (52 tumours)”",
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

## S504545

Request: Our nutrition study has plasma metabolomics (412 features) and VST-transformed RNA-seq (2,000 genes) from the same 96 participants, with no missing values. I'd like DRAGON to fit the two-layer partial-correlation network with lambda1 fixed at 0 and lambda2 fixed at 1 - we are deliberately testing the extremes - and return the result as an edge list.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "I'd like DRAGON to fit the two-layer partial-correlation network with lambda1 fixed at 0 and lambda2 fixed at 1 - we are deliberately testing the extremes - and return the result as an edge list." -- available from DRAGON.

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

## S698975

Request: counts_norm.tsv, motif_prior.tsv and ppi_string.tsv from our 64 colon samples are in the project folder. Fire off something useful on them right now; I'll work out the actual question later.

Complete recorded stdout:
````text
● Classifying requested outcome…
? Clarification needed
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

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
    "headline": "I need to know which result you want before choosing a workflow.",
    "points": [
      "Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?"
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

## S942022

Request: I'm trying to understand the regulatory landscape of Arabidopsis roots under drought - about 36 RNA-seq samples, and I can get motif and protein-interaction priors. What kind of analysis makes sense here?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (6.85s)
● Matching registered workflows…
● Preparing next step…
I can't tell yet which result you want, so I have not chosen a workflow.

With expression data, the registered workflows can give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer?

Nothing was selected and nothing runs before you answer.

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
    "headline": "I need to know which result you want before choosing a workflow.",
    "points": [
      "Which of these results do you want, or what question should the analysis answer?"
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

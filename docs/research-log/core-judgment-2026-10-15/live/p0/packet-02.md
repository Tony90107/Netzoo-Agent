## S751060

Request: Run OTTER on expr_t2d_islets.tsv, seed_W.tsv and ppi_tf.tsv with lam set to 1.5, so co-expression gets even more weight than PPI.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.42s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "Run OTTER on expr_t2d_islets.tsv, seed_W.tsv and ppi_tf.tsv with lam set to 1.5, so co-expression gets even more weight than PPI." -- not available here as asked. OTTER's lam must be between 0 and 1; "1.5" is not. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

You asked me to run OTTER, but it cannot run as you asked (above), so the run would not do what you asked. I have not planned it.

Tell me to run OTTER anyway, and I will then find your input files and show a preview; nothing runs until you approve it.

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
    "headline": "OTTER was not planned: confirm the run you want first.",
    "points": [],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Run OTTER on expr_t2d_islets.tsv, seed_W.tsv and ppi_tf.tsv with lam set to…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "OTTER's lam must be between 0 and 1; \"1.5\" is not.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      }
    ],
    "next_steps": [
      {
        "key": "plan-run_otter",
        "label": "Plan OTTER with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning OTTER",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_otter",
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

## S134377

Request: We measured 180 circulating miRNAs (normalized, continuous qPCR values) and 45 plasma cytokines in the same 64 sepsis patients; both tables have samples in rows, identical patient IDs and no missing values. What I want is a separate network for every patient that links miRNAs and cytokines through partial correlations, within and across the two layers, so I can compare survivors with non-survivors patient by patient afterwards.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.81s)
● Matching registered workflows…
✓ Workflow — LIONESS-DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "a separate network for every patient that links miRNAs and cytokines through partial correlations, within and across the two layers" -- available from LIONESS-DRAGON.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 64 patients, 65 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

For your question ("compare survivors with non-survivors patient by patient afterwards"):
- **DRAGON** — Build one network per time point or condition on the same features and compare the cross-layer edges; this does not use the pairing -- to keep it, use LIONESS-DRAGON and compare each individual's samples.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "composition",
    "headline": "LIONESS-DRAGON gives the per-sample result you asked for; it also writes the cohort network, so DRAGON need not run first.",
    "points": [
      "Method: One two-layer partial-correlation network per sample, derived leave-one-out.",
      "Needs: omics layer 1, omics layer 2.",
      "Cost: N samples take N+1 DRAGON runs (for your 64 patients, 65 DRAGON runs).",
      "Produces: multi-omic network (one per sample).",
      "Your question: whether the groups or time points differ; the reply says what DRAGON and LIONESS-DRAGON give toward it and the step after each."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_lioness_dragon",
        "label": "Plan LIONESS-DRAGON with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning LIONESS-DRAGON",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_lioness_dragon",
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

## S803507

Request: Can GIRAFFE be run with my own optimizer settings? For our 52 rice leaf samples from the drought trial I want a learning rate of 1e-4, 2,000 iterations and a heavier weight on the PPI term in the loss, because in a pilot the package defaults gave a TF activity matrix that looked over-smoothed and I'd like to see whether these settings change that.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.16s)
● Matching registered workflows…
! Fallback recommendation — not an exact semantic match
✓ Guidance prepared
What I understood you are asking for:
1. "For our 52 rice leaf samples from the drought trial I want a learning rate of 1e-4, 2,000 iterations and a heavier weight on the PPI term in the loss, because in a pilot the package defaults gave a TF activity matrix that looked over-smoothed and I'd like to see whether these settings change that." -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "learning rate of 1e-4" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

Fallback candidate: **GIRAFFE**, if you have a motif prior and a PPI network. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** is related to that result and scale. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors.

**GIRAFFE**: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.

Routing-level input modality: expression matrix.

Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix; interpret TF-gene regulatory weights as coefficients in a linear expression model; estimate positive activating and negative inhibitory partial regulatory effects; model gene expression with transcription factor activities as predictors.

GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

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
    "headline": "GIRAFFE is the closest registered match, but it is not a verified match for your request.",
    "points": [
      "Method: Also estimates per-sample TF activity and signed activating/repressing effects.",
      "Needs: expression matrix, motif prior, PPI network.",
      "Also needs expression matrix, motif prior and PPI network; no file for them is named yet.",
      "Produces: regulatory network and TF activity matrix (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“For our 52 rice leaf samples from the drought trial I want a learning rate of…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so \"learning rate of 1e-4\" cannot be applied.",
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

## S858427

Request: We generated quite a lot of omics on a pig model of septic shock: whole-blood transcriptome, plasma proteome and a few hundred metabolites, sampled at baseline and at 24 hours. I'd like a systems-level view of what is going on in these animals. Where should we start?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.47s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "I'd like a systems-level view of what is going on in these animals." -- available from DRAGON.

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

## S668568

Request: I want a transcript-metabolite partial-correlation network for 75 NAFLD liver biopsies in which the transcript layer's shrinkage is fixed at 0.3, as in our previous paper, while the metabolite layer's shrinkage is estimated from the data.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.66s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "a transcript-metabolite partial-correlation network" -- available from DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Selected path: **DRAGON**.

Your question asks for a multi-omic network. **DRAGON** fits that result.

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

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "DRAGON fits your goal: multi-omic network.",
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

## S556288

Request: Our grant renewal promises 'network-based insights' into Crohn's disease, and we have bulk RNA-seq from 150 ileal biopsies plus clinical data (disease activity, treatment, biopsy site). I need to propose a concrete analysis by Friday, but nobody has said what the network part should actually be or what question it should answer. We also have matched serology for most of the patients. What can we do?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.13s)
● Matching registered workflows…
● Preparing next step…
I cannot select a workflow until the requested result is clear. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

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
    "headline": "I need one more detail before choosing a workflow.",
    "points": [
      "I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow."
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

## S341502

Request: Our 96 brain RNA-seq samples (about 20,000 genes) were processed in four extraction batches and I want the batch effect removed. Depending on who you ask in the lab, that means a batch-corrected expression matrix to hand to other people, or batch-adjusted gene co-expression to build the regulatory network on, and I'm not sure which one I'm supposed to deliver. Batch is recorded per sample as numeric indicator columns.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Matched workflows — LIONESS-COEXPRESSION
✓ Guidance prepared
What I understood you are asking for:
1. "a batch-corrected expression matrix to hand to other people or batch-adjusted gene co-expression to build the regulatory network on" -- you have not chosen which result you want: if "a batch-corrected expression matrix to hand to other people": no registered workflow gives this; if "batch-adjusted gene co-expression to build the regulatory network on": COBRA.

Before I choose a workflow, please tell me: Which result do you want: "a batch-corrected expression matrix to hand to other people" or "batch-adjusted gene co-expression to build the regulatory network on"?

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
      "Which result do you want: \"a batch-corrected expression matrix to hand to other people\" or \"batch-adjusted gene co-expression to build the regulatory network on\"?"
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

## S937388

Request: I'd like a network of how about 150 regulators control their target genes across 60 hepatocellular carcinoma samples. I have the expression matrix, a PPI among those regulators, and a regulator-to-target prior from a collaborator's project, but that project studied both RNA-binding proteins and transcription factors, and I'm not sure which of the two lists I was given.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.55s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "I'd like a network of how about 150 regulators control their target genes across 60 hepatocellular carcinoma samples." -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **PUMA** — produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **LIONESS-PUMA** — produces: One TF/miRNA-gene network per sample, plus the aggregate network.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

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
      "Compare what each produces with what you asked for; asking again re-runs the check.",
      "Your request names expression data; the matched workflows also need more inputs, while LIONESS-COEXPRESSION or BONOBO works from it alone."
    ],
    "choices": {
      "header": "Inputs",
      "question": "Do you also have a motif prior and a PPI network?",
      "options": [
        {
          "key": "inputs-named",
          "label": "Only expression data",
          "description": "Leads to LIONESS-COEXPRESSION or BONOBO · A gene-gene co-expression network (genes only, no regulator roles)",
          "answer": "I only have expression data. A gene-gene co-expression network (genes only, no regulator roles) is fine.",
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
          "description": "Leads to PANDA, LIONESS-PANDA, OTTER or GIRAFFE",
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
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“I'd like a network of how about 150 regulators control their target genes…",
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

## S156564

Request: Can I add an L1 (lasso) sparsity penalty to OTTER's objective so that the TF-gene network it returns for my 45 bovine mammary gland samples is sparse, with most edges exactly zero?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.96s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "the TF-gene network it returns" -- available from OTTER.
2. "sparse, with most edges exactly zero" -- not available here as asked. OTTER does not meet "sparse, with most edges exactly zero".

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

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
    "headline": "4 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.",
    "points": [
      "Understood goal: a TF-gene regulatory network.",
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
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“sparse, with most edges exactly zero”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "OTTER does not meet \"sparse, with most edges exactly zero\".",
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

## S129053

Request: Run LIONESS-PANDA on expr_ra_synovium.tsv with motif_hs.txt and ppi_hs.txt to get a TF-to-gene network per column. I'm not sure which export this file is: the per-patient matrix (24 patients) or the version where a student averaged the patients into two columns, RA and control.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.84s)
● Matching registered workflows…
✓ Workflow — LIONESS-PANDA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: [CHECKOUT]/expr_ra_synovium.tsv
- PANDA/PUMA inputs: error: motif file does not exist: [CHECKOUT]/motif_hs.txt
- PANDA/PUMA inputs: error: PPI file does not exist: [CHECKOUT]/ppi_hs.txt

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

## S445919

Request: Can SAMBAR subtype our 210 hepatocellular carcinomas from the RNA-seq expression matrix? We don't have mutation calls for this cohort, only expression.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.04s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Can SAMBAR subtype our 210 hepatocellular carcinomas from the RNA-seq expression matrix?" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

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
        "label": "“Can SAMBAR subtype our 210 hepatocellular carcinomas from the RNA-seq…",
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

## S688998

Request: Use the files in shared/hcc_project/ (expr_mrna.tsv, expr_mirna.tsv, motif_hs.txt and targetscan_pairs.txt) and run whichever NetZoo analysis is appropriate.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.00s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "run whichever NetZoo analysis is appropriate." -- not matched to any registered workflow.

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
        "label": "“run whichever NetZoo analysis is appropriate.”",
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

## S249884

Request: We have somatic mutation calls and RNA-seq for the same 90 bladder tumours. Is SAMBAR the right thing to run, or one of the network methods like PANDA? I'm open to whatever gives the most interesting result.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.31s)
● Matching registered workflows…
● Preparing next step…
What I understood you are asking for:
1. "Is SAMBAR the right thing to run, or one of the network methods like PANDA?" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

No single registered workflow produces this result from all the stated inputs together. Each stated input is listed on its own, with the registered workflows that fit it, their algorithmic premises and inputs:

Result: multi omic network (aggregate), from expression matrix and mutation matrix.
Each stated input on its own:
- From the expression matrix:
  - **Multi omic network — DRAGON**
    - Registered purpose: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.
    - Method premise: infer conditional associations using partial correlation; DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
    - Mathematical interpretation: DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.
    - Required inputs: all of: DRAGON omics layer 1, DRAGON omics layer 2.
    - Declared output: multi omic network (cohort-level aggregate).
- From the mutation matrix:
  No registered workflow produces this result from this input.
  Registered workflows that accept it, and what they produce instead: **SAMBAR** (gene mutation scores, pathway mutation matrix, sample cluster assignment, sample distance matrix).

Which should we start with: the expression matrix (DRAGON), the mutation matrix (no registered workflow)? If you meant a different result for one of the inputs, say which.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "reading_choice",
    "headline": "No single registered workflow takes every stated input together.",
    "points": [],
    "choices": {
      "header": "Reading",
      "question": "Which reading should we start with?",
      "options": [
        {
          "key": "reading-1-expression_matrix",
          "label": "From the expression matrix",
          "description": "DRAGON: a cohort-level multi-omic network · Partial-correlation network across two omics layers of the same samples",
          "answer": "Use the expression matrix only",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_dragon",
          "granularity": null,
          "resolution": "confirm_workflow",
          "paths": [],
          "compare_actions": []
        }
      ],
      "allow_other": true,
      "ordering": "In the order your request states them."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Is SAMBAR the right thing to run, or one of the network methods like PANDA?”",
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
        "key": "reading-1-mutation_matrix",
        "label": "From the mutation matrix",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "No registered workflow produces a cohort-level multi-omic network from the mutation matrix.",
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

## S941490

Request: I've been reading about DRAGON, OTTER and GIRAFFE and they all sound powerful. Our lab has bulk transcriptomics, proteomics and some ATAC-seq peaks for a mouse model of pulmonary fibrosis, roughly 30 animals across three time points. Which of these should we apply, and what would we actually learn from each? We haven't settled on a specific hypothesis yet, and our PI wants something to show at the next lab meeting.

Complete recorded stdout:
````text
● Classifying requested outcome…
! Semantic routing unavailable
What I understood you are asking for:
1. "what would we actually learn from each" -- not matched to any registered workflow.

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
        "label": "“what would we actually learn from each”",
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

## S775856

Request: My PI told me to 'do the NetZoo thing, PANDA or LIONESS or something' on our zebrafish fin-regeneration RNA-seq before lab meeting. Which one should I run?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (6.26s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Which one should I run?" -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

For “do the NetZoo thing”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

For “PANDA or LIONESS”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "reading_choice",
    "headline": "No single registered workflow takes every stated input together.",
    "points": [],
    "choices": {
      "header": "Reading",
      "question": "Which reading should we start with?",
      "options": [
        {
          "key": "reading-1",
          "label": "Reading 1: “do the NetZoo thing, PANDA or LIONESS or something”",
          "description": "PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER or GIRAFFE: a regulatory network",
          "answer": "Start with reading 1: “do the NetZoo thing, PANDA or LIONESS or something”",
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
      "ordering": "In the order your request states them."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Which one should I run?”",
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

## S650010

Request: We ran a 48-gene NanoString inflammation panel on 600 rheumatoid arthritis patients recruited at four hospitals. I want to know how much of the co-expression between those 48 genes is associated with the hospital each sample came from, decomposed per covariate, with hospital coded as numeric indicator columns in a design table whose rows match the sample IDs exactly; each hospital contributed roughly 150 patients.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.25s)
● Matching registered workflows…
✓ Workflow — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "how much of the co-expression between those 48 genes is associated with the hospital each sample came from, decomposed per covariate" -- available from COBRA.
2. "I want to know" -- available from COBRA.

Selected path: **COBRA**.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

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
    "headline": "COBRA produces a co-expression network (one cohort-level result).",
    "points": [
      "Method: Separates how covariates (batch, site, condition) reshape co-expression.",
      "Needs: expression matrix, covariate design matrix.",
      "Produces: co-expression network (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
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

## S890091

Request: Can GIRAFFE give us signed TF-to-gene effects, activation versus repression, for our 40 atopic dermatitis skin biopsies? We have expression, a motif prior and a TF PPI. My supervisor's notes say we need those signed effects for each biopsy separately, but the grant text says one set of signed effects for the whole cohort, and I'm not sure which she actually wants.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Matched workflows — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "signed TF-to-gene effects, activation versus repression" -- available from GIRAFFE.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "GIRAFFE produces a regulatory network and TF activity matrix (one cohort-level result).",
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

## S549145

Request: Please run the network analysis on expr_sle_monocytes.tsv and send me the results.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "send me the results" -- not matched to any registered workflow.

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
        "label": "“send me the results”",
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

## S546619

Request: I've put tumor_expr.tsv, motifs.txt, ppi.txt and clinical.tsv in the folder. Do whatever makes sense with them and give me figures for the paper.

Complete recorded stdout:
````text
● Classifying requested outcome…
! Semantic routing unavailable
What I understood you are asking for:
1. "Do whatever makes sense with them and give me figures for the paper." -- not matched to any registered workflow.

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
        "label": "“Do whatever makes sense with them and give me figures for the paper.”",
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

## S882040

Request: For each of our 25 diffuse large B-cell lymphoma patients I need that patient's own TF-to-gene regulatory network, built from the cohort's expression matrix together with a human motif prior and a TF PPI, so I can later compare each TF's targeting between responders and non-responders.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.00s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "that patient's own TF-to-gene regulatory network" -- available from LIONESS-PANDA.
2. "For each of our 25 diffuse large B-cell lymphoma patients I need" -- available from LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

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
    "headline": "4 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.",
    "points": [
      "Understood goal: a TF-gene regulatory network from expression data, a motif prior and a PPI network.",
      "Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.",
      "Nothing you said favours one method yet; each option says when to pick it.",
      "Picking an option explains it for your data and what it needs; nothing runs.",
      "Your stated concern is answered per method in the full explanation."
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
        }
      ],
      "allow_other": true,
      "ordering": "Nothing you said favours one of them; each line says when to pick it."
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

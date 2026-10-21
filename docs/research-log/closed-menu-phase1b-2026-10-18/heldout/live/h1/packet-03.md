## S775856

Request: Each of our 30 patients needs an individual partial-correlation network spanning 900 plasma transcripts and 600 metabolites measured from the same blood draws. The data are complete and continuous, and I want every within- and cross-layer pair kept.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.61s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Each of our 30 patients needs an individual partial-correlation network spanning 900 plasma transcripts and 600 metabolites measured from the same blood draws." -- not available here as asked. LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 1,500 features and 30 samples give 33,727,500.

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
        "label": "“Each of our 30 patients needs an individual partial-correlation network…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 1,500 features and 30 samples give 33,727,500.",
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

Request: With DRAGON, I'd like three separately tuned penalties on our 110 matched colorectal tumours: lambda1 for the methylation block, lambda2 for the expression block, and a lambda_inter of 0.2 controlling only the cross-layer methylation-expression edges. Can you set it up that way?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.93s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "With DRAGON, I'd like three separately tuned penalties on our 110 matched colorectal tumours: lambda1 for the methylation block, lambda2 for the expression block, and a lambda_inter of 0.2 controlling only the cross-layer methylation-expression edges." -- not available here as asked. NetZoo's DRAGON has no setting for "lambda_inter of 0.2"; the settings it passes are output_format, lambda1 and lambda2. DRAGON itself can still run, with its own settings instead -- an alternative, not the setting you asked for.
2. "Can you set it up that way?" -- available from DRAGON.

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
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“With DRAGON, I'd like three separately tuned penalties on our 110 matched…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's DRAGON has no setting for \"lambda_inter of 0.2\"; the settings it passes are output_format, lambda1 and lambda2.",
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

## S890091

Request: I have bulk RNA-seq from 120 Crohn's disease colon biopsies collected at three hospitals. Where should I start with network analysis, and what would you recommend?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.73s)
● Matching registered workflows…
✓ Guidance prepared
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

## S549145

Request: Start the analysis on ovarian_expr.tsv and batch_design.csv today. I'm not sure yet what I want out of it - whichever network method makes the most sense, I trust you.

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

## S546619

Request: My 12 liver samples are log-transformed and centred, with a labelled header. For BONOBO, please sparsify at confidence 0.05 and fix delta at 0.4 so each sample carries a little more weight in its own covariance estimate. HDF5 output is fine.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.33s)
● Matching registered workflows…
✓ Matched workflows — LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, LIONESS-DRAGON, BONOBO
? Clarification needed
What I understood you are asking for:
1. "For BONOBO, please sparsify at confidence 0.05 and fix delta at 0.4 so each sample carries a little more weight in its own covariance estimate." -- available from BONOBO.

The capability check identified workflows for every result you asked for:
- **BONOBO** — for "For BONOBO, please sparsify at confidence 0.05 and fix delta at 0.4 so each sample carries a little more weight in its own covariance estimate."; produces: One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample.

Choose a result to discuss with its workflow.

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
    "headline": "The capability check identified workflows for every result you asked for.",
    "points": [
      "Understood: \"For BONOBO, please sparsify at confidence 0.05 and fix delta at 0.4 so each sample carries a little more weight in its own covariance estimate.\""
    ],
    "choices": {
      "header": "Workflow",
      "question": "Which result do you want to discuss?",
      "options": [
        {
          "key": "run_bonobo",
          "label": "BONOBO",
          "description": "For \"For BONOBO, please sparsify at confidence 0.05 and fix delta at 0.4 so each sample carries a little more weight in its own covariance estimate.\": One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge…",
          "answer": "Explain how BONOBO addresses this result: For BONOBO, please sparsify at confidence 0.05 and fix delta at 0.4 so each sample carries a little more weight in its own covariance estimate.. Keep the other requirements separate and do not execute it yet.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_bonobo",
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

## S882040

Request: I keep reading about PUMA and OTTER. Which one would you pick for my zebrafish fin-regeneration time course - five time points with four replicates each?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.81s)
● Matching registered workflows…
● Preparing next step…
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

## S740494

Request: Sixty-four lung tumours in our biobank have matched DNA methylation, RNA expression and proteomics. I want one joint partial-correlation model that connects the features of all three layers simultaneously, not pairwise, so I can see methylation-protein links conditional on expression.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.86s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "I want one joint partial-correlation model that connects the features of all three layers simultaneously, not pairwise, so I can see methylation-protein links conditional on expression." -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

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
        "label": "“I want one joint partial-correlation model that connects the features of all…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "DRAGON does not give it: two layers only.",
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

## S142779

Request: In a cohort of 240 participants we measured 250 blood transcripts and 150 serum proteins on the same draws; the data are complete and continuous. What I'm after is an individual partial-correlation network for every participant linking features within and across the two layers, so I can compare them between smokers and non-smokers.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.08s)
● Matching registered workflows…
✓ Workflow — DRAGON → LIONESS-DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "What I'm after is an individual partial-correlation network for every participant linking features within and across the two layers, so I can compare them between smokers and non-smokers." -- available from LIONESS-DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Selected path: **LIONESS-DRAGON**.

Your question asks for a multi-omic network. **LIONESS-DRAGON** fits that result.

**LIONESS-DRAGON** — Infer one sample-specific two-layer multi-omic partial-correlation network per sample with LIONESS-DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample.
- Each sample's network is an undirected partial-correlation graph across both layers; like DRAGON's, it is an association graph, not a causal one.

Ask for the workflow's controls and defaults if you want to set them.

For your question ("compare them between smokers and non-smokers"):
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

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
    "headline": "LIONESS-DRAGON fits your goal: multi-omic network.",
    "points": [
      "Method: One two-layer partial-correlation network per sample, derived leave-one-out.",
      "Needs: omics layer 1, omics layer 2.",
      "Cost: N samples take N+1 DRAGON runs (for your 240 participants, 241 DRAGON runs).",
      "Produces: multi-omic network (one per sample).",
      "Your question: whether the groups or time points differ; the reply says what LIONESS-DRAGON give toward it and the step after each."
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

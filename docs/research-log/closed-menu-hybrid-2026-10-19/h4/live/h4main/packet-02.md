## S733589

Request: Our paired proteomics and phosphoproteomics tables from the same 48 ovarian tumours should go through DRAGON. Rows are tumour IDs, columns are proteins or phosphosites, and there are no missing values. I want manual shrinkage, lambda1 = 0 for the proteome layer and lambda2 = 1 for the phosphoproteome layer, with the edge_list output. One network for the whole cohort is what I'm after.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.19s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "Our paired proteomics and phosphoproteomics tables from the same 48 ovarian tumours should go through DRAGON." -- not matched to any registered workflow.
2. "I want manual shrinkage, lambda1 = 0 for the proteome layer and lambda2 = 1 for the phosphoproteome layer, with the edge_list output." -- available from DRAGON.
3. "One network for the whole cohort is what I'm after." -- available from DRAGON.

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
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Our paired proteomics and phosphoproteomics tables from the same 48 ovarian…",
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

## S460406

Request: We want TF-to-gene networks for 30 ALS and 30 control spinal cord samples, one per group, with the sequencing-center effect removed first. I'm not sure whether every ALS sample went to center A and every control to center B; the old tracking sheet is lost.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.08s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Did every ALS sample go to center A and every control to center B?
  You wrote: "I'm not sure whether every ALS sample went to center A and every control to center B; the old tracking sheet is lost". PANDA's contract: "Preserve biological covariates in the correction design and verify that hospital or sequencing batch is not completely confounded with the phenotype before inference".

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
      "Did every ALS sample go to center A and every control to center B?"
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

## S233702

Request: A reviewer asked us to 'add a regulatory network perspective' to our heart failure paper. We have left-ventricle RNA-seq from 24 failing and 24 non-failing hearts. How should we respond to that comment?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.79s)
● Matching registered workflows…
✓ Guidance prepared
Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **PUMA** — produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **LIONESS-PUMA** — produces: One TF/miRNA-gene network per sample, plus the aggregate network.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

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
          "key": "run_panda",
          "label": "PANDA",
          "description": "Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.",
          "answer": "Explain what PANDA produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_panda",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_puma",
          "label": "PUMA",
          "description": "Not confirmed. Produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.",
          "answer": "Explain what PUMA produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_puma",
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
        },
        {
          "key": "run_lioness_puma",
          "label": "LIONESS-PUMA",
          "description": "Not confirmed. Produces: One TF/miRNA-gene network per sample, plus the aggregate network.",
          "answer": "Explain what LIONESS-PUMA produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_puma",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_otter",
          "label": "OTTER",
          "description": "Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.",
          "answer": "Explain what OTTER produces and check whether it meets my original request; do not assume it does.",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_otter",
          "granularity": null,
          "resolution": "follow_up",
          "paths": [],
          "compare_actions": []
        },
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
        }
      ],
      "allow_other": true,
      "ordering": "In routing's order; none is confirmed or recommended."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“How should we respond to that comment?”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "The check matched no registered workflow to this, but the second check that confirms such a gap could not run (not confirmed).",
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

## S689610

Request: Our lab has somatic mutation calls and RNA-seq for the same 150 endometrial tumours. Making sense of them with network methods appeals to us, but I'm not sure where to start or which output would be most useful.

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

## S544211

Request: We have RNA-seq, ATAC-seq, proteomics and metabolomics on the same 50 mice. Is DRAGON the right tool for this, or would something else be better? We haven't settled on what we want to get out of the integration.

Complete recorded stdout:
````text
● Classifying requested outcome…
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

## S644759

Request: For each of our 90 glioma patients, the goal is that patient's own regulatory network in which both transcription factors and microRNAs regulate target genes. We have bulk RNA-seq for all 90, a combined TF motif and miRNA-target prior, a TF interaction file, and a one-per-line list of the miRNAs that appear in the prior.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.76s)
● Matching registered workflows…
✓ Workflow — LIONESS-PUMA
✓ Guidance prepared
What I understood you are asking for:
1. "that patient's own regulatory network in which both transcription factors and microRNAs regulate target genes." -- available from LIONESS-PUMA.

For the sample-specific output you described, use **LIONESS-PUMA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network
   - `mirna_file`: miRNA list

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PUMA** separately; **LIONESS-PUMA** also produces the aggregate output. Use **PUMA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PUMA once on all samples and once more without each sample, so N samples take N+1 PUMA runs and give N network files (for your 90 patients, 91 PUMA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

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
    "headline": "LIONESS-PUMA gives the per-sample result you asked for; it also writes the cohort network, so PUMA need not run first.",
    "points": [
      "Method: One TF + miRNA network per sample, derived leave-one-out from the cohort.",
      "Needs: expression matrix, motif prior, PPI network, miRNA list.",
      "Cost: N samples take N+1 PUMA runs (for your 90 patients, 91 PUMA runs).",
      "Produces: regulatory network (cohort-level and per-sample)."
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

## S751060

Request: Launch LIONESS-DRAGON with metab_110.csv (110 samples x 250 metabolites) and rna_110.csv (the same 110 sample IDs x 350 genes); both are complete numeric tables with no constant columns. Let it estimate both shrinkage values itself. Aggregate matrix to ld/all_samples.tsv, per-sample edge table to ld/per_sample.tsv. Leave everything else at defaults and start it now.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Workflow — DRAGON → LIONESS-DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "Launch LIONESS-DRAGON with metab_110.csv (110 samples x 250 metabolites) and rna_110.csv (the same 110 sample IDs x 350 genes)" -- not matched to any registered workflow.
2. "Aggregate matrix to ld/all_samples.tsv" -- available from LIONESS-DRAGON.
3. "per-sample edge table to ld/per_sample.tsv" -- available from LIONESS-DRAGON.

Selected path: **LIONESS-DRAGON**.

**LIONESS-DRAGON**: Infer one sample-specific two-layer multi-omic partial-correlation network per sample with LIONESS-DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: derive each sample network from all-sample and leave-one-out networks; infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

Workflow-specific scientific notes:

- LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample.
- Each sample's network is an undirected partial-correlation graph across both layers; like DRAGON's, it is an association graph, not a causal one.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Other declared controls (not matched to this request; defaults apply unless you set them): `lambda1`, `lambda2`.

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
    "headline": "LIONESS-DRAGON produces a multi-omic network (one per sample).",
    "points": [
      "Method: One two-layer partial-correlation network per sample, derived leave-one-out.",
      "Needs: omics layer 1, omics layer 2.",
      "Cost: N samples take N+1 DRAGON runs (for your 110 samples, 111 DRAGON runs).",
      "Produces: multi-omic network (one per sample)."
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Launch LIONESS-DRAGON with metab_110.csv (110 samples x 250 metabolites) and…",
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

## S134377

Request: Fire off LIONESS-PUMA on islet_expr.tsv (48 columns), prior_tf_mir.txt, ppi.txt and mir_ids.txt now; aggregate to lp/aggregate.txt and per-sample networks to lp/samples.txt. One snag: my student says the 48 columns are individual FACS-sorted beta cells, while the sample sheet lists them as 48 bulk islet preparations from different donors.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (7.25s)
● Matching registered workflows…
✓ Workflow — PUMA → LIONESS-PUMA
✓ Guidance prepared
What I understood you are asking for:
1. "aggregate to lp/aggregate.txt" -- available from LIONESS-PUMA.
2. "per-sample networks to lp/samples.txt" -- available from LIONESS-PUMA.

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
    "headline": "LIONESS-PUMA produces a regulatory network (cohort-level and per-sample).",
    "points": [
      "Method: One TF + miRNA network per sample, derived leave-one-out from the cohort.",
      "Needs: expression matrix, motif prior, PPI network, miRNA list.",
      "Cost: N samples take N+1 PUMA runs (for your 48 individual, 49 PUMA runs).",
      "Also needs expression matrix and miRNA list; no file for them is named yet.",
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

## S803507

Request: Across 80 breast tumours I want to estimate how active each transcription factor is in each tumour, separately from the TF's own mRNA level, and also whether each TF tends to activate or repress its target genes. The gene-by-sample expression, a TF-by-gene motif prior and a TF-TF protein interaction matrix with matching identifiers are ready.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.13s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "estimate how active each transcription factor is in each tumour, separately from the TF's own mRNA level" -- available from GIRAFFE.
2. "whether each TF tends to activate or repress its target genes." -- available from GIRAFFE.

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

## S858427

Request: Kick off DRAGON on rna_layer.tsv and mirna_layer.tsv (54 matched samples, identical IDs in both). Set lambda1 to 0.3 by hand but let lambda2 be estimated from the data. Matrix output to dragon/rna_mirna.tsv, please.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.90s)
● Matching registered workflows…
✓ Workflow — DRAGON
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- DRAGON inputs: error: omics_layer_1 is missing or not a regular file: [CHECKOUT]/rna_layer.tsv
- DRAGON inputs: error: omics_layer_2 is missing or not a regular file: [CHECKOUT]/mirna_layer.tsv

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

## S668568

Request: Go ahead and run PUMA with kidney_expr.tsv (gene-by-sample, 52 biopsies), prior_tf_mir.txt (TF motif plus miRNA-target edges), ppi_tf.txt, and mirna_ids.txt, which lists one miRNA per line, every one of them present in the prior's first column. Output goes to results/puma_kidney.txt. A single network for all 52 biopsies is fine.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.66s)
● Matching registered workflows…
✓ Workflow — PUMA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: [CHECKOUT]/kidney_expr.tsv
- PANDA/PUMA inputs: error: motif file does not exist: [CHECKOUT]/plus
- PANDA/PUMA inputs: error: PPI file does not exist: [CHECKOUT]/ppi_tf.txt
- PANDA/PUMA inputs: error: miRNA file does not exist: [CHECKOUT]/mirna_ids.txt

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

## S556288

Request: BONOBO is the plan for 7 placenta samples, one co-expression network per sample. Our collaborator's note says the matrix is log2-transformed and gene-centered, but the file header calls it raw_TPM, and I have no way to tell which statement is true.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.20s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the expression matrix log2-transformed and gene-centered?
  You wrote: "the matrix is log2-transformed and gene-centered, but the file header calls it raw_TPM, and I have no way to tell which statement is true". BONOBO's contract: "the agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression".

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
      "Is the expression matrix log2-transformed and gene-centered?"
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

Request: For each of 85 colorectal tumours I want a patient-specific regulatory network from bulk RNA-seq, and motif, PPI and miRNA-target priors are on hand. Our protocol says 'TF-to-gene regulation only' but the grant says 'include microRNA regulators', and I can't tell which one we actually committed to.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.79s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Did you commit to including microRNA regulators in your analysis?
  You wrote: "Our protocol says 'TF-to-gene regulation only' but the grant says 'include microRNA regulators', and I can't tell which one we actually committed to". LIONESS-PANDA's contract: "LIONESS-PANDA uses the original gene-by-sample expression matrix, motif and PPI priors to internally infer the aggregate PANDA network and derive sample-specific TF-to-gene networks".

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
      "Did you commit to including microRNA regulators in your analysis?"
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

Request: COBRA already gave us adjusted_coexpression.tsv with the sequencing batch removed across our 75 patients. Next, feed that adjusted matrix into LIONESS-PANDA as its co-expression input, so that every patient-specific TF-gene network comes out batch-corrected. The motif and PPI priors are the same ones we used before.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.18s)
● Matching registered workflows…
✓ Workflow — LIONESS-PANDA
● Preparing next step…
? Clarification needed
  Input required

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.

Select input 1 of 2: Motif/prior (motif_file)
Enter a candidate number or a full path.
Give the path of motif_file; your request names its own files, so no other data was searched.
Enter the full path.
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

## S156564

Request: Should I be using BONOBO or LIONESS for my 30 kidney transplant biopsies? I keep reading about both and can't decide which one to run; I have bulk RNA-seq plus some motif and PPI files left over from a previous project.

Complete recorded stdout:
````text
● Classifying requested outcome…
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

## S129053

Request: For every one of our 60 donors I want that donor's own partial-correlation network linking 2,500 CpG methylation features with 1,500 transcripts, from two complete tables measured on the same donors. Please keep all 4,000 features; we explicitly do not want any filtering.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.23s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "that donor's own partial-correlation network linking 2,500 CpG methylation features with 1,500 transcripts" -- not available here as asked. LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 4,000 features and 60 samples give 479,880,000.

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
        "label": "“that donor's own partial-correlation network linking 2,500 CpG methylation…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 4,000 features and 60 samples give 479,880,000.",
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

## S445919

Request: Queue a LIONESS-DRAGON job on rna_85.csv (85 samples x 300 genes) and cpg_85.csv for the same 85 samples, aggregate matrix to ldr/all.tsv and the per-sample table to ldr/edges.tsv. I can't remember whether cpg_85.csv is the filtered 300-probe version or the unfiltered 5,000-probe export.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.09s)
● Matching registered workflows…
✓ Workflow — DRAGON → LIONESS-DRAGON
● Preparing next step…
? Clarification needed
  Input required

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.

Select input 1 of 2: DRAGON omics layer 1 (omics_layer_1)
Enter a candidate number or a full path.
1. rna_85.csv
2. cpg_85.csv
3. ldr/all.tsv
4. ldr/edges.tsv
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

## S688998

Request: We need an OTTER network for our 64 mouse liver RNA-seq samples, pooled into one cohort-wide TF-to-gene network. The motif seed and the TF-TF PPI edge list use the same TF identifiers. Set lam to 1 so the fit relies entirely on co-expression rather than the PPI, with gamma 0.6 and 150 iterations, and write the edge_list format so I can pass it to community detection later.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.88s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "We need an OTTER network for our 64 mouse liver RNA-seq samples, pooled into one cohort-wide TF-to-gene network." -- available from OTTER.
2. "Set lam to 1 so the fit relies entirely on co-expression rather than the PPI, with gamma 0.6 and 150 iterations, and write the edge_list format so I can pass it to community detection later." -- available from OTTER.

Assumptions behind this recommendation (not confirmed facts):

- The user has the necessary input data and parameters for the OTTER network construction.

Selected path: **OTTER**.

Your question asks for a cohort-level regulatory network. **OTTER** fits that result and scale.

**OTTER** — Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

Required workflow inputs:

- `motif_file`: motif/prior
- `ppi_file`: PPI network

Required alternative (provide one):

- `expression_file`: expression matrix
- `coexpression_file`: adjusted co-expression matrix

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Runtime limits:

- `computing`: current runtime unavailable: gpu; use `computing=cpu`.

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
    "headline": "OTTER fits your goal: cohort-level TF-gene regulatory network.",
    "points": [
      "Method: Explicit objective (graph matching), fitted by a fixed number of gradient steps; lighter on memory.",
      "Needs: motif prior, PPI network, expression matrix or adjusted co-expression matrix.",
      "Produces: regulatory network (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
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

## S249884

Request: Two separate TF-to-gene regulatory networks are needed: one from the 12 hypoxia and one from the 12 normoxia HUVEC samples, both built on the same genes and the same motif and PPI priors, so I can compare each transcription factor's targeting between the conditions. Expression, motif and PPI data are prepared.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.67s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "one from the 12 hypoxia" -- available from PANDA.
2. "one from the 12 normoxia HUVEC samples" -- available from PANDA.
3. "Two separate TF-to-gene regulatory networks are needed" -- available from PANDA.
4. "so I can compare each transcription factor's targeting between the conditions" -- available from PANDA's output plus a step you run outside NetZoo: One run per condition on the same genes and priors, then compare; two aggregate networks give no per-sample spread for a test.
Not checked against the registered workflows: "both built on the same genes and the same motif and PPI priors"

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

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
    "headline": "4 registered workflows fit your request; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.",
    "points": [
      "Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.",
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
        }
      ],
      "allow_other": true,
      "ordering": "Nothing you said favours one of them; each line says when to pick it."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“both built on the same genes and the same motif and PPI priors”",
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

Request: Time to run SAMBAR: mut_hnscc.csv, exon_size.csv, cancer_genes.txt and kegg.gmt, trying 2 to 10 subtypes, output to sambar_hnscc/. After the purity filter the matrix has either 8 or 15 tumours, and I'm not sure which version of the file I exported.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.55s)
● Matching registered workflows…
✓ Workflow — SAMBAR
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- SAMBAR inputs: error: mutation_file must be an existing regular file: [CHECKOUT]/mut_hnscc.csv
- SAMBAR inputs: error: exon_size_file must be an existing regular file: [CHECKOUT]/exon_size.csv
- SAMBAR inputs: error: cancer_gene_file must be an existing regular file: [CHECKOUT]/cancer_genes.txt
- SAMBAR inputs: error: pathway_file must be an existing regular file: [CHECKOUT]/kegg.gmt

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

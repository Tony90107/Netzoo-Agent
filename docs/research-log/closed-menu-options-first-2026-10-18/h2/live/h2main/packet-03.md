## S775856

Request: We have 18,000 genes measured in 96 colon samples from three hospitals and two sequencing batches, with a numeric design matrix (one-hot hospital, batch, age) keyed by the same sample IDs. I want to see how much of the gene co-expression is associated with hospital and batch, and get an adjusted co-expression matrix out of it.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.06s)
● Matching registered workflows…
✓ Workflow — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "see how much of the gene co-expression is associated with hospital and batch" -- available from COBRA.
2. "get an adjusted co-expression matrix out of it" -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

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
    "headline": "COBRA fits your goal: cohort-level co-expression network.",
    "points": [
      "Picked from 2 fitting methods because you wrote “how much of the gene co-expression is…”; LIONESS-COEXPRESSION also fit.",
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

## S650010

Request: Our panel has somatic mutation calls and RNA-seq for the same 150 colorectal patients, plus survival data. What could NetZoo do for us with data like this? We're open to anything.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.29s)
● Matching registered workflows…
✓ Guidance prepared
I can't tell yet which result you want, so I have not chosen a workflow.

With expression data and somatic mutations, the registered workflows can give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
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

## S890091

Request: We measured proteomics and metabolomics on the same 90 plasma samples (continuous, log-scaled), and reviewers asked for 'a systems-level angle'. We don't have a specific hypothesis yet. Where would you start?

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

## S549145

Request: Time to rerun OTTER: expr_pbmc.tsv, motif_pbmc.tsv and ppi_pbmc.tsv, output otter_pbmc.tsv as an edge list. This time set computing to gpu and precision to single, because the CPU run took far too long on our 19,000-gene matrix. Start it now.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Workflow — OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "output otter_pbmc.tsv as an edge list." -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.
2. "Time to rerun OTTER: expr_pbmc.tsv, motif_pbmc.tsv and" -- available from OTTER.
Not checked against the registered workflows: "set computing to gpu and precision to single"

You asked me to run OTTER. It covers "Time to rerun OTTER: expr_pbmc.tsv, motif_pbmc.tsv and", but no registered workflow covers "output otter_pbmc.tsv as an edge list.", so the run would do only part of what you asked. I have not planned it.

Tell me to run OTTER for the part it gives, and I will then find your input files and show a preview; nothing runs until you approve it.

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
        "label": "“output otter_pbmc.tsv as an edge list.”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“set computing to gpu and precision to single”",
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

## S546619

Request: I've put calls_30pts.csv, gene_lengths.csv, cancer_genes.txt and kegg.gmt in data/; start SAMBAR into sambar_30/ now. No one documented the old pipeline that made calls_30pts.csv, so it's unclear to me whether it holds somatic mutations or germline variants.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.84s)
● Matching registered workflows…
? Clarification needed
Before I choose a workflow, please tell me:
- Does calls_30pts.csv contain somatic mutations?
  You wrote: "it's unclear to me whether it holds somatic mutations or germline variants". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

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
      "Does calls_30pts.csv contain somatic mutations?"
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

## S882040

Request: Is GIRAFFE worth trying on my melanoma data? I have expression for 70 tumours plus motif and PPI files. I'm hoping something interesting falls out of it.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.30s)
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

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **PUMA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **PUMA** — For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

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
    "headline": "6 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.",
    "points": [
      "Understood goal: a TF-gene regulatory network.",
      "LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA, OTTER, GIRAFFE and PUMA give one across all samples.",
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
        },
        {
          "key": "run_puma",
          "label": "PUMA",
          "description": "One TF + miRNA network across all your samples · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list",
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
          "description": "One TF + miRNA network per sample, plus the cohort network · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list",
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

## S740494

Request: Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and prot_all.csv (the same 60 samples by 500 proteins). Estimate the lambdas automatically, write the all-sample matrix to agg_dragon.tsv and the per-sample table to per_sample_edges.tsv, and start it right away.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
● Preparing next step…
What I understood you are asking for:
1. "Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and prot_all.csv (the same 60 samples by 500 proteins)." -- not available here as asked. NetZoo's LIONESS-DRAGON has no setting for "Estimate the lambdas automatically"; the settings it passes are lambda1 and lambda2. LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 2,500 features and 60 samples give 187,425,000.
2. "write the all-sample matrix to agg_dragon.tsv" -- not available here as asked. NetZoo's LIONESS-DRAGON has no setting for "write the all-sample matrix to agg_dragon.tsv"; the settings it passes are lambda1 and lambda2.
3. "the per-sample table to per_sample_edges.tsv" -- not available here as asked. NetZoo's LIONESS-DRAGON has no setting for "the per-sample table to per_sample_edges.tsv"; the settings it passes are lambda1 and lambda2.
4. "start it right away" -- not available here as asked. NetZoo's LIONESS-DRAGON has no setting for "start it right away"; the settings it passes are lambda1 and lambda2.

No registered workflow can give these as you asked them (above), so none is offered as asked.

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
      "Understood: \"Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and prot_all.csv (the same 60 samples by 500 proteins).\"",
      "Understood: \"write the all-sample matrix to agg_dragon.tsv\"",
      "Understood: \"the per-sample table to per_sample_edges.tsv\"",
      "Understood: \"start it right away\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's LIONESS-DRAGON has no setting for \"Estimate the lambdas automatically\"; the settings it passes are lambda1 and lambda2.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“write the all-sample matrix to agg_dragon.tsv”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's LIONESS-DRAGON has no setting for \"write the all-sample matrix to agg_dragon.tsv\"; the settings it passes are lambda1 and lambda2.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-3",
        "label": "“the per-sample table to per_sample_edges.tsv”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's LIONESS-DRAGON has no setting for \"the per-sample table to per_sample_edges.tsv\"; the settings it passes are lambda1 and lambda2.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-4",
        "label": "“start it right away”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's LIONESS-DRAGON has no setting for \"start it right away\"; the settings it passes are lambda1 and lambda2.",
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

Request: Each of my pig muscle samples should get its own gene-gene co-expression network (log2 CPM, centered per gene). We have three samples, unless the degraded one gets excluded, in which case only two. I won't know until Monday.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.19s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Which of these is right: 2 or 3?
  You wrote: "We have three samples, unless the degraded one gets excluded, in which case only two".
  - 2: no registered workflow can do this as asked -- LIONESS-COEXPRESSION needs at least 3 samples; the request has 2
  - 3: LIONESS-COEXPRESSION or BONOBO can do this

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
      "Which of these is right: 2 or 3?"
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

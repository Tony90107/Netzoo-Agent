## S775856

Request: We have 18,000 genes measured in 96 colon samples from three hospitals and two sequencing batches, with a numeric design matrix (one-hot hospital, batch, age) keyed by the same sample IDs. I want to see how much of the gene co-expression is associated with hospital and batch, and get an adjusted co-expression matrix out of it.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.59s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is this a must for your analysis: "get an adjusted co-expression matrix out of it"? The contract of COBRA does not say it meets it.
  You wrote: "get an adjusted co-expression matrix out of it".

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
      "Is this a must for your analysis: \"get an adjusted co-expression matrix out of it\"? The contract of COBRA does not say it meets it."
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

## S650010

Request: Our panel has somatic mutation calls and RNA-seq for the same 150 colorectal patients, plus survival data. What could NetZoo do for us with data like this? We're open to anything.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.42s)
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
✓ Interpreted requested outcome (2.48s)
● Matching registered workflows…
? Clarification needed — Fallback recommendation is not an exact semantic match
? Clarification needed
What I understood you are asking for:
1. "Time to rerun OTTER: expr_pbmc.tsv, motif_pbmc.tsv and ppi_pbmc.tsv, output otter_pbmc.tsv as an edge list." -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.
2. "Start it now." -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give these as you asked, so none is offered as asked.

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
      "\"Time to rerun OTTER: expr_pbmc.tsv, motif_pbmc.tsv and ppi_pbmc.tsv, output otter_pbmc.tsv as an edge list.\" -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative…",
      "\"Start it now.\" -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for."
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

Request: I've put calls_30pts.csv, gene_lengths.csv, cancer_genes.txt and kegg.gmt in data/; start SAMBAR into sambar_30/ now. No one documented the old pipeline that made calls_30pts.csv, so it's unclear to me whether it holds somatic mutations or germline variants.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Guidance prepared
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
● Matching registered workflows…
✓ Guidance prepared
Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
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
1. "Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and prot_all.csv (the same 60 samples by 500 proteins)." -- not available here as asked. NetZoo's LIONESS-DRAGON has no setting for "lambdas"; the settings it passes are lambda1 and lambda2. LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 2,500 features and 60 samples give 187,425,000.

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
        "label": "“Launch LIONESS-DRAGON on rna_all.csv (60 samples by 2,000 genes) and…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo's LIONESS-DRAGON has no setting for \"lambdas\"; the settings it passes are lambda1 and lambda2.",
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
✓ Interpreted requested outcome (3.75s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Each of my pig muscle samples should get its own gene-gene co-expression network" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

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
    "headline": "2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.",
    "points": [
      "Understood goal: a per-sample co-expression network.",
      "Nothing you said favours one method yet; each option says when to pick it.",
      "Picking an option explains it for your data and what it needs; nothing runs."
    ],
    "choices": {
      "header": "Method",
      "question": "Which method fits your study?",
      "options": [
        {
          "key": "run_lioness_coexpression",
          "label": "LIONESS-COEXPRESSION",
          "description": "One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more",
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
          "description": "One gene co-expression network per sample, with a p-value for each connection · Pick it if you have only a handful of samples or you need a p-value for each edge",
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

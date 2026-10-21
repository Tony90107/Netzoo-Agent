## S733589

Request: Go ahead and run LIONESS-PUMA: expression expr_ovarian.tsv (48 tumours, genes by samples), prior motif_tf_mirna.tsv (TF motifs plus miRNA targets), ppi_string.tsv and mirna_ids.txt with one miRNA per line. Aggregate network to out/puma_aggregate.txt and the per-sample networks to out/lioness_puma/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (6.00s)
● Matching registered workflows…
✓ Workflow — PUMA → LIONESS-PUMA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: [CHECKOUT]/expr_ovarian.tsv
- PANDA/PUMA inputs: error: motif file does not exist: [CHECKOUT]/motif_tf_mirna.tsv
- PANDA/PUMA inputs: error: PPI file does not exist: [CHECKOUT]/ppi_string.tsv
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

## S460406

Request: Can we use DRAGON on our gut study: a host transcriptome table (log CPM) and a metabolite table for the same 58 stool samples? One thing I can't vouch for: the metabolite file may hold actual intensities or just 0/1 detected/not-detected calls.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (6.76s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Does the metabolite file contain only finite continuous numeric measurements?
  You wrote: "the metabolite file may hold actual intensities or just 0/1 detected/not-detected calls". DRAGON's contract: "Values must be finite continuous numeric measurements".

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
      "Does the metabolite file contain only finite continuous numeric measurements?"
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

Request: Across 120 breast tumours I need, for each transcription factor, its activity level in every tumour separately from its own mRNA level, and also whether it activates or represses each target gene. I have RNA-seq expression, a TF-gene motif prior and a TF-TF PPI matrix with matching identifiers.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.67s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "its activity level in every tumour separately from its own mRNA level" -- available from GIRAFFE.
2. "whether it activates or represses each target gene" -- available from GIRAFFE.

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

## S689610

Request: Last time GIRAFFE on our 52 prostate samples didn't seem to converge, so this time please use a learning rate of 0.001, 500 iterations and a stronger weight on the PPI term. Same expression, motif and PPI files as before.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.93s)
● Matching registered workflows…
✓ Matched workflows — PANDA, LIONESS-PANDA, OTTER, GIRAFFE
? Clarification needed
What I understood you are asking for:
1. "please use a learning rate of 0.001, 500 iterations and a stronger weight on the PPI term" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "learning rate of 0.001" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
      "\"please use a learning rate of 0.001, 500 iterations and a stronger weight on the PPI term\" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so \"learning rate of 0.001\" cannot be applied. GIRAFFE itself can still run, with its own settings…"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [],
    "ran_nothing": true
  }
]
````

## S544211

Request: I'd like DRAGON on two tables from the same 85 plasma donors: proteomics (310 proteins, log-intensities) and metabolomics (140 metabolites, log-abundances), samples as rows and features as columns. Please fix lambda1 at 0 and lambda2 at 1 rather than estimating them, and give me the edge_list output so I can sort the cross-layer partial correlations.

Complete recorded stdout:
````text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "I'd like DRAGON on two tables from the same 85 plasma donors: proteomics (310 proteins, log-intensities) and metabolomics (140 metabolites, log-abundances), samples as rows and features as columns." -- available from DRAGON.
2. "Please fix lambda1 at 0 and lambda2 at 1 rather than estimating them, and give me the edge_list output so I can sort the cross-layer partial correlations." -- available from DRAGON.

Selected path: **DRAGON**.

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

## S644759

Request: Our downstream pipeline only reads parquet, so BONOBO should write each per-sample co-expression matrix for our 22 lung fibroblast samples as a .parquet file. The expression is log-transformed and centered, with genes on rows.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.37s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "BONOBO should write each per-sample co-expression matrix for our 22 lung fibroblast samples as a .parquet file." -- not available here as asked. NetZoo's BONOBO has no setting for ".parquet file"; the settings it passes are bonobo_output_format, sample_names, sparsify, bonobo_confidence, save_pvals, precision, keep_in_memory, delta, genes_axis, log_transformed and centered. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
      "\"BONOBO should write each per-sample co-expression matrix for our 22 lung fibroblast samples as a .parquet file.\" -- not available here as asked. NetZoo's BONOBO has no setting for \".parquet file\"; the settings it passes are bonobo_output_format, sample_names, sparsify, bonobo_confidence…"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "confirm-run_lioness_panda",
        "label": "Yes, use LIONESS-PANDA",
        "description": "Explains that workflow for this goal and what it needs; runs nothing.",
        "answer": "Yes, use LIONESS-PANDA",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_lioness_panda",
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

## S751060

Request: My lab keeps telling me to 'do LIONESS' on our 200 TCGA breast tumour RNA-seq profiles. Is that something I should be doing, and what would I get out of it?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.90s)
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

## S134377

Request: Our cervical cancer project (38 samples) needs one regulatory network for the whole cohort, with TFs and a set of small RNAs as regulators of the genes. A collaborator sent the small-RNA list and target predictions, but nobody can tell me whether those small RNAs are miRNAs or piRNAs.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.03s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the small RNAs miRNAs?
  You wrote: "nobody can tell me whether those small RNAs are miRNAs or piRNAs". PUMA's contract: "Require one miRNA identifier per line and require every miRNA in prior column one".

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
      "Are the small RNAs miRNAs?"
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

## S803507

Request: For 40 glioblastoma samples I want one cohort-wide regulatory network in which both transcription factors and miRNAs regulate their target genes. I have the expression matrix, a prior with TF motifs and miRNA target predictions, a PPI file and a list of the miRNAs, one per line. Per-sample networks aren't needed.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.50s)
● Matching registered workflows…
✓ Workflow — PUMA
✓ Guidance prepared
What I understood you are asking for:
1. "For 40 glioblastoma samples I want one cohort-wide regulatory network in which both transcription factors and miRNAs regulate their target genes." -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale.

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

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  {
    "kind": "workflow_guidance",
    "headline": "PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.",
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

## S858427

Request: Run CONDOR now on results/panda_lung_edges.tsv: columns source, target and weight, thresholded from my PANDA lung network so all weights are non-negative. Write everything into /data/projects/lung/condor_results/ and use lung_v1 as the prefix.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Matched workflows — CONDOR, COBRA, SAMBAR
? Clarification needed
What I understood you are asking for:
1. NetZoo cannot run CONDOR for this because needs regulator_gene_network, which the request says is not available.

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
      "NetZoo cannot run CONDOR for this because needs regulator_gene_network, which the request says is not available."
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

## S668568

Request: Execute OTTER on expr_heart.tsv, motif_heart.tsv and ppi_heart.tsv right now and save otter_heart.tsv. My notebook says lam should be 1.5, or maybe 0.15; the decimal point is smudged and I can't check with my supervisor today.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
? Clarification needed
Before I choose a workflow, please tell me:
- Is lam set to a value between 0 and 1?
  You wrote: "lam should be 1.5, or maybe 0.15; the decimal point is smudged". OTTER's contract: "setting lam (number; minimum 0; maximum 1): Weight of gene co-expression versus the TF-TF PPI network in OTTER's fit, as (lam, 1 - lam); not a sparsity penalty".

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
      "Is lam set to a value between 0 and 1?"
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

## S556288

Request: We want to group tumours into 2 to 6 subtypes based on pathway-level somatic mutation scores, with gene lengths, a cancer-gene list and a KEGG GMT in hand. Pathology review is still deciding how many tumours qualify: it will end up as 5 or 9.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.12s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Will the final number of tumours be 5?
  You wrote: "it will end up as 5 or 9". SAMBAR's contract: "cluster=true requires 2 <= kmin <= kmax <= number of mutation samples".

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
      "Will the final number of tumours be 5?"
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

Request: Our seven tumours are in mut_7tumours.csv. Together with exon_lengths.csv, cancer_genes.txt and c2.cp.v7.gmt, please execute SAMBAR now into sambar_out/ with kmin 2 and kmax 10, so we see a wide range of subtype numbers.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.16s)
● Matching registered workflows…
✓ Workflow — SAMBAR
✓ Guidance prepared
What I understood you are asking for:
1. "please execute SAMBAR now into sambar_out/ with kmin 2 and kmax 10, so we see a wide range of subtype numbers." -- not available here as asked. SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled. SAMBAR itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
      "\"please execute SAMBAR now into sambar_out/ with kmin 2 and kmax 10, so we see a wide range of subtype numbers.\" -- not available here as asked. SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled. SAMBAR itself can still run, with its own settings instead -- an…"
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

## S937388

Request: Please run CONDOR directly on expr_tpm_brain.tsv (genes by 40 cortex samples) to find gene communities, and write the output to condor_brain/ today. We don't want any network-building step first.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.12s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "to find gene communities" -- not available here: no registered workflow produces this. CONDOR does not meet "We don't want any network-building step first.".
2. "write the output to condor_brain/ today" -- not available here: no registered workflow produces this. Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.

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
      "Understood: \"to find gene communities\"",
      "Understood: \"write the output to condor_brain/ today\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“to find gene communities”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "CONDOR does not meet \"We don't want any network-building step first.\".",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“write the output to condor_brain/ today”",
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

Request: COBRA seems right for separating sex and batch effects on co-expression in our 640-sample blood cohort; the design matrix is numeric. The README says the filtered expression matrix has 600 genes, but the methods draft says 6,000, and I honestly don't know which is right.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.18s)
● Matching registered workflows…
✓ Matched workflows — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "separating sex and batch effects on co-expression" -- depends on a number you gave candidates for ("The README says the filtered expression matrix has 600 genes, but the methods draft says 6,000"): 600: no registered workflow can do this as asked -- COBRA requires more genes than samples; the request has 600 genes and 640 samples; 6,000: COBRA can do this.

Before I choose a workflow, please tell me: Which of these is right: 600 or 6,000?

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
      "Which of these is right: 600 or 6,000?"
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

Request: Can DRAGON give me a single partial-correlation network across transcriptomics, proteomics and metabolomics together? All three tables come from the same 75 patients, samples as rows. I want all three layers in one model rather than separate pairwise runs.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.12s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Can DRAGON give me a single partial-correlation network across transcriptomics, proteomics and metabolomics together?" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.
2. "I want all three layers in one model rather than separate pairwise runs." -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

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
      "Understood: \"Can DRAGON give me a single partial-correlation network across transcriptomics, proteomics and metabolomics together?\"",
      "Understood: \"I want all three layers in one model rather than separate pairwise runs.\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Can DRAGON give me a single partial-correlation network across…",
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
      },
      {
        "key": "capability-2",
        "label": "“I want all three layers in one model rather than separate pairwise runs.”",
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

## S445919

Request: I want to understand gene regulation during zebrafish fin regeneration: five time points, four replicates each, bulk RNA-seq. Any thoughts on how to approach it?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.10s)
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

## S688998

Request: From matched liver RNA-seq and metabolomics on 70 mice, I need a network that proves which metabolites causally drive which genes, with arrows showing the direction of each effect, to support a mechanistic claim in our paper.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.66s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "I need a network that proves which metabolites causally drive which genes, with arrows showing the direction of each effect" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators.

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
        "label": "“I need a network that proves which metabolites causally drive which genes…",
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

## S249884

Request: Could you set up OTTER for an aggregate TF-gene network of human cardiomyocytes, using my precomputed gene-by-gene co-expression matrix instead of an expression table, plus the motif seed and the TF-TF PPI? Settings: lam = 1, gamma = 0, 150 iterations, single precision on CPU, matrix output.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.67s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "set up OTTER for an aggregate TF-gene network" -- available from OTTER.

Selected path: **OTTER**.

Your question asks for a cohort-level regulatory network. **OTTER** fits that result and scale. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression.

**OTTER**: Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints.

Routing-level input modality: expression matrix, coexpression network.

Method premise: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.

OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

Required workflow inputs:

- `motif_file`: motif/prior
- `ppi_file`: PPI network

Required alternative (provide one):

- `expression_file`: expression matrix
- `coexpression_file`: adjusted co-expression matrix

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `computing`=cpu, `precision`=double, `lam`=0.035, `gamma`=0.335, `iterations`=60, `eta`=1e-05, `bexp`=1.0.

Runtime limits:

- `computing`: current runtime unavailable: gpu; use `computing=cpu`.

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.

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

## S941490

Request: Someone in journal club suggested BONOBO, someone else said COBRA, for our 24 bladder cancer RNA-seq samples with batch information. Which one do I go with?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.58s)
● Matching registered workflows…
✓ Guidance prepared
The capability check could not confirm this turn what a registered workflow gives you, so nothing was selected and nothing runs.

Ask again to re-run the check.

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
    "headline": "I could not judge this request this turn, so nothing was selected.",
    "points": [
      "Asking again re-runs the check; restating the result you want usually helps."
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

## S740494

Request: Run OTTER with seed_W_mm.tsv, ppi_tf_mm.tsv and coexp_liver.tsv; I have no expression file, only that co-expression file. I can't remember if coexp_liver.tsv is the full gene-by-gene correlation matrix for the cohort or the edge-by-sample table from our earlier LIONESS co-expression run.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.44s)
● Matching registered workflows…
✓ Matched workflows — LIONESS-COEXPRESSION, COBRA, BONOBO
? Clarification needed
What I understood you are asking for:
1. "Run OTTER with seed_W_mm.tsv, ppi_tf_mm.tsv and coexp_liver.tsv; I have no expression file, only that co-expression file." -- available from OTTER.

OTTER: Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints.
Registered required inputs: motif_file, ppi_file, output_file.
Registered workflow controls: output_format (type=enum, default='matrix'), computing (type=enum, default='cpu'), precision (type=enum, default='double'), lam (type=number, default=0.035), gamma (type=number, default=0.335), iterations (type=integer, default=60), eta (type=number, default=1e-05), bexp (type=number, default=1.0).
Output: aggregate TF-to-gene regulatory networks.

You asked me to run this, and LIONESS-COEXPRESSION, COBRA and BONOBO all fit it. Tell me which one to run; I will then find your input files and show a preview, and nothing runs until you approve it.

No files were inspected and no analysis ran.

````

Complete recorded stderr:
````text

````

Recorded reply cards (empty means no card generated):
````json
[
  null
]
````

## S142779

Request: Run SAMBAR on mutations_ucec.csv (248 endometrial tumours in rows, genes in columns, non-negative mutation counts) with exon_lengths.csv, cancer_genes.txt and c2.cp.kegg.gmt (MSigDB format), all sharing the same gene symbols, and cluster the tumours into between 2 and 6 subtypes.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.64s)
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
● Matching registered workflows…
✓ Workflow — PANDA
✓ Guidance prepared
What I understood you are asking for:
1. "Run PANDA on expr_ipf.tsv with motif_hg38.tsv and ppi_hs.tsv, but use cobra_out/adjusted_coexpression.tsv (COBRA's adjusted gene-by-gene matrix, already checked to have the same gene IDs and order as the expression file) as the co-expression input instead of PANDA's own Pearson correlation." -- available from PANDA.

Selected path: **PANDA**.

Your question asks for a cohort-level regulatory network. **PANDA** fits that result and scale.

**PANDA** — Infer an aggregate TF-to-gene regulatory network with PANDA. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

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
    "headline": "PANDA fits your goal: cohort-level regulatory network.",
    "points": [
      "Method: Widely used baseline: message passing over motif, PPI and co-expression evidence.",
      "Needs: expression matrix, motif prior, PPI network.",
      "Produces: regulatory network (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
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

## S237521

Request: Using bulk expression and clinical follow-up for 400 lung adenocarcinoma patients, I need a model that predicts each new patient's overall-survival risk, something like a penalized Cox model that outputs a risk score, which I can then lock and apply to an external validation cohort of 150 patients from another hospital without refitting. Ideally the score would also show which genes drive the risk.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.00s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "I need a model that predicts each new patient's overall-survival risk, something like a penalized Cox model that outputs a risk score, which I can then lock and apply to an external validation cohort of 150 patients from another hospital without refitting." -- not available here as asked. NetZoo has no registered method or variant "penalized Cox model". No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
2. "Ideally the score would also show which genes drive the risk." -- available from LIONESS-PANDA or LIONESS-PUMA.

About "a model that predicts each new patient's overall-survival risk": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

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
    "headline": "2 registered workflows fit; one detail about your study decides between them.",
    "points": [
      "Understood goal: a per-sample regulatory network."
    ],
    "choices": {
      "header": "Regulators",
      "question": "Which regulator type should the network model: transcription factors, miRNA regulators, or both?",
      "options": [
        {
          "key": "regulator_type-2",
          "label": "Transcription factors only",
          "description": "Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network",
          "answer": "Transcription factors only",
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
          "key": "regulator_type-1",
          "label": "Both TFs and miRNAs",
          "description": "Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list",
          "answer": "Both TFs and miRNAs",
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
      "ordering": "Each answer lists the workflows it leads to."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“I need a model that predicts each new patient's overall-survival risk…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo has no registered method or variant \"penalized Cox model\".",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "purpose-prediction",
        "label": "Predict outcomes for new samples",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "No registered workflow builds a predictive model; per-sample results can only be its features.",
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
✓ Interpreted requested outcome (4.88s)
● Matching registered workflows…
✓ Matched workflows — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "Run DRAGON on expr_cll_layer.csv and methyl_cll_layer.csv (same 110 patient IDs in rows, no missing cells)." -- available from DRAGON.
2. "continuous beta values" -- you have not chosen which result you want: if "continuous beta values": DRAGON; if "binarized methylated/unmethylated calls (0/1)": no registered workflow gives this.
3. "binarized methylated/unmethylated calls (0/1)" -- you have not chosen which result you want: if "continuous beta values": DRAGON; if "binarized methylated/unmethylated calls (0/1)": no registered workflow gives this.

Before I choose a workflow, please tell me: Which result do you want: "continuous beta values" or "binarized methylated/unmethylated calls (0/1)"?

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
      "Which result do you want: \"continuous beta values\" or \"binarized methylated/unmethylated calls (0/1)\"?"
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

## S287138

Request: Will DRAGON take my paired plasma proteomics and metabolomics tables (both with a header, the same 85 participant IDs in the first column, samples in rows, complete continuous values with no NAs) and write the partial-correlation network as an edge list rather than a matrix?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.95s)
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

## S383472

Request: Call somatic SNVs and indels from tumour_07.bam against its matched normal_07.bam and give me a filtered VCF.

Complete recorded stdout:
````text
● Classifying requested outcome…
! Semantic routing unavailable
What I understood you are asking for:
1. "give me a filtered VCF." -- not matched to any registered workflow.

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
        "label": "“give me a filtered VCF.”",
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
1. "Run SAMBAR on mut_pilot.csv (mutation counts for 5 cholangiocarcinomas) with exon_len.csv, cancer_genes.txt and hallmark.gmt, testing every subtype number from 2 through 8." -- available from SAMBAR.

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
● Matching registered workflows…
● Preparing next step…
No additional response-model call was made because the configured task token budget was reached.

Router decision: no_tool
Reason: The request names no result yet; the goal is asked before any workflow is chosen.

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

## S112073

Request: Please run LIONESS-PUMA on expr_cll.tsv (36 CLL patients), motif_cll.txt, ppi_cll.txt, mir_targets.txt and mir_list.txt (one miRNA ID per line, every one present in the first column of mir_targets.txt) to get a TF/miRNA-to-gene network for every patient.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.18s)
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
✓ Interpreted requested outcome (3.02s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "I need a gene co-expression network for each of our 9 periodontitis gingival biopsies, with a p-value for every edge so I can filter them per sample." -- available from BONOBO.

Selected path: **BONOBO**.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Controls matching this request:

- `sparsify` (type=boolean; default=False) — Compute approximate edge p-values and threshold each sample's co-expression matrix at bonobo_confidence (with save_pvals, the full matrix is kept and the p-values are written).
- `bonobo_confidence` (type=number; default=0.05; range=0.0..1.0) — Significance level at which sparsify thresholds the edges.
- `save_pvals` (type=boolean; default=False) — Write each sample's edge p-value matrix; requires sparsify.

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

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
    "headline": "BONOBO fits your goal: per-sample co-expression network.",
    "points": [
      "Picked from 2 fitting methods because you wrote “with a p-value for every edge so I can…”; LIONESS-COEXPRESSION also fit.",
      "Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.",
      "Needs: expression matrix.",
      "Produces: co-expression network and p-value matrix (one per sample)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "compare-others",
        "label": "Compare with LIONESS-COEXPRESSION",
        "description": "Explains how their assumptions differ and which fits your study; runs nothing.",
        "answer": "Compare BONOBO with LIONESS-COEXPRESSION for this goal. How do their assumptions differ, and which fits my study?",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": null,
        "granularity": null,
        "resolution": "compare_workflows",
        "paths": [],
        "compare_actions": [
          "run_bonobo",
          "run_lioness_coexpression"
        ]
      },
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

## S449311

Request: Can GIRAFFE estimate an activity score for every transcription factor in each of our 30 psoriasis skin samples? I have the gene-by-sample expression table, a TF-by-gene motif prior and a TF-TF PPI matrix with matching identifiers.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.78s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "Can GIRAFFE estimate an activity score for every transcription factor in each of our 30 psoriasis skin samples?" -- available from GIRAFFE.

No single registered workflow produces this result from all the stated inputs together. Each stated input is listed on its own, with the registered workflows that fit it, their algorithmic premises and inputs:

Result: TF activity matrices (aggregate), from expression matrix and tf activity matrix.
Each stated input on its own:
- From the expression matrix:
  - **TF-only signed regulatory-effect network — GIRAFFE**
    - Registered purpose: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.
    - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
    - Mathematical interpretation: GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.
    - Required inputs: all of: expression matrix, motif/prior, PPI network.
    - Declared output: regulatory networks, TF activity matrices (cohort-level aggregate).
- From the tf activity matrix:
  No registered workflow produces this result from this input.

Which should we start with: the expression matrix (GIRAFFE), the tf activity matrix (no registered workflow)? If you meant a different result for one of the inputs, say which.

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
          "description": "GIRAFFE: a cohort-level TF activity matrix · Also estimates per-sample TF activity and signed activating/repressing effects",
          "answer": "Use the expression matrix only",
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
      "ordering": "In the order your request states them."
    },
    "unavailable": [
      {
        "key": "reading-1-tf_activity_matrix",
        "label": "From the tf activity matrix",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "No registered workflow produces a cohort-level TF activity matrix from the tf activity matrix.",
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

## S946284

Request: For each of our 40 kidney cancer patients I need one number per transcription factor that captures that TF's regulatory strength in that patient, so we can relate it to survival. We have expression, a motif prior and a TF-TF PPI. I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or how active the TF is; my PI used both phrasings.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.82s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "one number per transcription factor that captures that TF's regulatory strength in that patient" -- available from GIRAFFE.

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
    "kind": "reading_choice",
    "headline": "Your request can be read 2 ways, and they lead to different workflows.",
    "points": [],
    "choices": {
      "header": "Reading",
      "question": "Which reading should we start with?",
      "options": [
        {
          "key": "reading-1",
          "label": "Reading 1: “one number per transcription factor that captures that…”",
          "description": "GIRAFFE: a cohort-level TF activity matrix · Also estimates per-sample TF activity and signed activating/repressing effects",
          "answer": "Start with reading 1: “one number per transcription factor that captures that TF's regulatory strength in that patient”",
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
          "key": "reading-2",
          "label": "Reading 2: “I'm honestly not sure whether 'regulatory strength'…”",
          "description": "GIRAFFE: a cohort-level regulatory network with TF activities · Also estimates per-sample TF activity and signed activating/repressing effects",
          "answer": "Start with reading 2: “I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or…”",
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
      "ordering": "In the order your request states them."
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

## S795233

Request: Reviewers asked for 'a network analysis' of our placenta study. We have mRNA-seq and small-RNA-seq from 45 preeclampsia and control placentas. Honestly I don't know what kind of network they expect or what it's supposed to show. The two groups are roughly balanced and both libraries come from the same placentas; can you set something up that would satisfy them?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.80s)
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
✓ Interpreted requested outcome (1.41s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Could you help me see how genes are connected in my sorghum heat-stress experiment?" -- available from LIONESS-COEXPRESSION.

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
✓ Interpreted requested outcome (1.89s)
● Matching registered workflows…
✓ Workflow — PANDA → LIONESS-PANDA
✓ Guidance prepared
What I understood you are asking for:
1. "Run the TF network inference on expr_alzheimer.tsv (88 donors: 44 AD, 44 controls), motifs_hg38.txt and ppi_tf.txt." -- available from LIONESS-PANDA, LIONESS-PUMA, OTTER or GIRAFFE.
The usual capability check could not run this turn, so a backup model read the request; nothing it found is confirmed.

You asked me to run LIONESS-PANDA, but the capability check could not confirm this turn that LIONESS-PANDA gives what you asked for. I have not planned the run.

Tell me to run LIONESS-PANDA anyway, and I will then find your input files and show a preview; nothing runs until you approve it.

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
    "headline": "LIONESS-PANDA was not planned: confirm the run you want first.",
    "points": [],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_lioness_panda",
        "label": "Plan LIONESS-PANDA with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning LIONESS-PANDA",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_lioness_panda",
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

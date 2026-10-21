## S359020

Request: Run PANDA on tumour_profiles_v2.tsv with motif_hs.txt and ppi_hs.txt. Heads up: our lab saved two genes-by-tumours matrices under similar names, one with log2 expression and one with binary somatic-mutation calls, and I'm not sure which one this is.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.57s)
● Matching registered workflows…
? Clarification needed
Before I choose a workflow, please tell me:
- Is the file you want to use the gene-by-sample expression matrix with log2 expression?
  You wrote: "I'm not sure which one this is". PANDA's contract: "PANDA consumes a gene-by-sample expression matrix plus motif and PPI priors, or a validated adjusted gene-by-gene co-expression matrix through coexpression_file".

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
      "Is the file you want to use the gene-by-sample expression matrix with log2 expression?"
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

Request: Can CONDOR find communities in network_final.tsv, which a postdoc left behind when he moved on? It's a three-column source/target/weight table, but I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.33s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the network a validated regulator-gene network?
  You wrote: "I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built". CONDOR's contract: "CONDOR consumes a weighted source-target bipartite edge list made from a validated regulator-gene network and returns community assignments with regulator-side and gene-side partitions".

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
      "Is the network a validated regulator-gene network?"
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

## S933684

Request: Should I be using COBRA or CONDOR on our lupus nephritis cohort? I keep seeing both names in NetZoo papers and I'm not sure what either would give me.

Complete recorded stdout:
````text
● Classifying requested outcome…
? Clarification needed
The research comparison could not be validated; no workflow was selected.

The requested result is not specific enough to select a workflow. No workflow has been selected. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

Specify the requested result type and whether it should be aggregate or sample-specific. The workflow will be selected only after the result is clear; the captured inputs will be carried forward, and nothing will run yet.

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
    "headline": "I could not validate an interpretation of this request, so nothing was selected.",
    "points": [
      "This does not mean your question is unclear; restating the result you want usually helps."
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

## S907774

Request: Should I go with BONOBO or LIONESS for my 20 Shank3 knockout and wild-type mouse cortex samples? I'm hoping to learn something about the knockout, but I haven't pinned down what yet.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.67s)
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

## S593031

Request: Can PUMA model the small RNAs from our mouse testis small-RNA-seq as regulators alongside the TFs? I have expression for 24 testes, a motif prior, a PPI and a small-RNA-to-target prior, but the annotation isn't finished: the small RNAs we picked could be miRNAs or piRNAs, and I genuinely don't know which yet.

Complete recorded stdout:
````text
● Classifying requested outcome…
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

## S239208

Request: I already have an aggregate TF-to-gene regulatory network for glioblastoma, exported as an edge list with source, target and weight columns; TF and gene IDs don't overlap and the weights were thresholded to be non-negative. Now I want to split it into communities of TFs and their target genes, with the TF-side and gene-side memberships reported separately.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.75s)
● Matching registered workflows…
✓ Workflow — CONDOR
✓ Guidance prepared
What I understood you are asking for:
1. "Now I want to split it into communities of TFs and their target genes, with the TF-side and gene-side memberships reported separately." -- available from CONDOR.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

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
    "headline": "CONDOR fits your goal: cohort-level set of network communities (modules).",
    "points": [
      "Method: Finds TF-gene communities (modules) in a two-mode network.",
      "Needs: TF-gene (bipartite) network.",
      "Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.",
      "Produces: set of network communities (modules) (one cohort-level result)."
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [
      {
        "key": "plan-run_condor",
        "label": "Plan CONDOR with my data",
        "description": "Finds matching input files and shows a preview with the command; nothing runs until you approve it.",
        "answer": "Start planning CONDOR",
        "recommended": false,
        "badge": "",
        "available": true,
        "reason": "",
        "action": "run_condor",
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

## S166046

Request: Can BONOBO build a co-expression network for each of my 6 rhesus macaque lymph node samples? The data are log2-transformed and centered per gene, with genes in rows and sample IDs in the header, and I'd like the per-sample matrices saved as HDF5 and computed in double precision.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.37s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "Can BONOBO build a co-expression network for each of my 6 rhesus macaque lymph node samples?" -- available from BONOBO.
2. "per-sample matrices saved as HDF5" -- not available here as asked. BONOBO's bonobo_output_format requires one of .h5, .hdf, .txt and .csv; "HDF5" does not identify one allowed choice.

BONOBO: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.
Registered required inputs: expression_file, output_dir.
Registered workflow controls: bonobo_output_format (type=enum, default='.h5'), sample_names (type=string_list, default=[]), sparsify (type=boolean, default=False), bonobo_confidence (type=number, default=0.05), save_pvals (type=boolean, default=False), precision (type=enum, default='single'), keep_in_memory (type=boolean, default=False), delta (type=number, default=None), genes_axis (type=enum, default='auto'), log_transformed (type=boolean, default=None), centered (type=boolean, default=None).
Output: one gene-gene co-expression network per selected sample.
This is a co-expression result, not a regulatory network (TF/miRNA) or a covariance-decomposition artifact.
When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.
When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.
When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

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
    "headline": "BONOBO fits your goal: per-sample co-expression network.",
    "points": [
      "Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.",
      "Needs: expression matrix.",
      "Produces: co-expression network and p-value matrix (one per sample)."
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“per-sample matrices saved as HDF5”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "BONOBO's bonobo_output_format requires one of .h5, .hdf, .txt and .csv; \"HDF5\" does not identify one allowed choice.",
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

## S592328

Request: Is OTTER able to run on CPU in single precision with 150 iterations and a step size (eta) of 1e-4, writing the result as an edge list? Inputs would be expression for 60 breast tumours (header row, gene IDs in the first column), a TF-by-gene seed edge list, and a TF-TF PPI edge list whose TFs are exactly the seed's TFs.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.76s)
● Matching registered workflows…
✓ Guidance prepared
Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.

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
        }
      ],
      "allow_other": true,
      "ordering": "In routing's order; none is confirmed or recommended."
    },
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Is OTTER able to run on CPU in single precision with 150 iterations and a…",
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
        "label": "“Inputs would be expression for 60 breast tumours (header row, gene IDs in the…",
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

## S314508

Request: From our 10x single-cell RNA-seq of differentiating iPSC-derived cardiomyocytes, I'd like to order the cells along a pseudotime trajectory and find the branch point where atrial and ventricular fates split.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.01s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "order the cells along a pseudotime trajectory" -- not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results. Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells.
2. "find the branch point where atrial and ventricular fates split" -- not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results. Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells.

No registered workflow produces these as you asked them, so none is offered for them as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

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
      "Understood: \"order the cells along a pseudotime trajectory\"",
      "Understood: \"find the branch point where atrial and ventricular fates split\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“order the cells along a pseudotime trajectory”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“find the branch point where atrial and ventricular fates split”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results.",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "outside-single_cell",
        "label": "SCORPION (single-cell networks)",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.",
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

## S500574

Request: We'd like a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients, from 300 serum miRNAs and a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs). The catch: I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel, and the files are still on the CRO's server.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.65s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Do you have the proteomics data in the required format for LIONESS-DRAGON?
  You wrote: "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel". LIONESS-DRAGON's contract: "LIONESS-DRAGON consumes exactly two paired sample-by-feature continuous omics tables, DRAGON's inputs, and produces the aggregate DRAGON matrix plus one partial-correlation network per sample".

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
      "Do you have the proteomics data in the required format for LIONESS-DRAGON?"
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

## S596980

Request: Can PANDA build a single TF-to-gene regulatory network for our whole cohort of 48 mouse liver RNA-seq samples? I have the gene-by-sample expression matrix, a JASPAR-based motif prior and a mouse TF-TF PPI from STRING, all using the same gene symbols.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.66s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Can PANDA build a single TF-to-gene regulatory network for our whole cohort of 48 mouse liver RNA-seq samples?" -- available from PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

What artifact should NetZoo produce?

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
    "points": [],
    "choices": {
      "header": "Result",
      "question": "What artifact should NetZoo produce?",
      "options": [
        {
          "key": "artifact_type-1",
          "label": "Regulatory network",
          "description": "Leads to PANDA or OTTER",
          "answer": "Regulatory network",
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
          "key": "artifact_type-2",
          "label": "Regulatory network + TF activity matrix",
          "description": "Leads to GIRAFFE · One signed TF-gene network (activating or repressing), plus each TF's activity in each sample",
          "answer": "Regulatory network + TF activity matrix",
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

## S504545

Request: Can SAMBAR subtype our 160 pediatric medulloblastomas? The sequencing core sent a samples-by-genes variant-count matrix along with gene lengths, a cancer-gene list and a KEGG GMT, but their README doesn't say whether the counts are tumour-only somatic mutations or germline variant calls, and I can't tell from the file itself.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.10s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the counts tumour-only somatic mutations?
  You wrote: "their README doesn't say whether the counts are tumour-only somatic mutations or germline variant calls". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

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
      "Are the counts tumour-only somatic mutations?"
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

## S698975

Request: I uploaded counts_week0.tsv, counts_week4.tsv and counts_week12.tsv from our vaccine trial. Can you run the right workflow on them?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.50s)
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

## S942022

Request: I want the list of genes differentially expressed between 12 drug-treated and 12 vehicle mouse hippocampi, with log2 fold changes and FDR-adjusted p-values like DESeq2 reports.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.35s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "I want the list of genes differentially expressed between 12 drug-treated and 12 vehicle mouse hippocampi, with log2 fold changes and FDR-adjusted p-values like DESeq2 reports." -- not available here as asked. NetZoo has no registered method or variant "DESeq2". COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

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
        "label": "“I want the list of genes differentially expressed between 12 drug-treated and…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo has no registered method or variant \"DESeq2\".",
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

## S733589

Request: Our 140 skeletal-muscle RNA-seq samples (about 18,000 genes after filtering) were sequenced in three runs and come from donors of both sexes. I'd like to see how much of each gene pair's co-expression is associated with sequencing run versus sex, and get an adjusted gene-by-gene co-expression matrix out of it for later network work. Both covariates are already coded as numeric indicator columns in a design table whose rows are exactly the expression sample IDs.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.09s)
● Matching registered workflows…
✓ Workflow — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "see how much of each gene pair's co-expression is associated with sequencing run versus sex" -- available from COBRA.
2. "get an adjusted gene-by-gene co-expression matrix out of it" -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale. COBRA models co-expression as a function of sample covariates through conditional covariance estimation.

Captured request parameters:

- `expression_file`: sample

What you asked about:

- "get an adjusted gene-by-gene co-expression matrix out of it for later network work" — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

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
      "Picked from 2 fitting methods because you wrote “how much of each gene pair's…”; LIONESS-COEXPRESSION also fit.",
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

## S460406

Request: Analyze everything in glioma_bundle/ (expression.tsv, methylation.tsv and mutations.csv for 80 gliomas) and tell me what you find.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.28s)
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

## S233702

Request: I'd like one regulatory network for my 70 colorectal tumours in which both transcription factors and microRNAs act as regulators of their target genes. I have the gene-by-sample expression matrix, a TF motif prior, a TF-TF PPI, a miRNA-target prior and a file listing the miRNAs, one ID per line, all of which appear in the prior. Nothing per-patient is needed; a single cohort-level network is what goes into the paper.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.02s)
● Matching registered workflows…
✓ Workflow — PUMA
✓ Guidance prepared
What I understood you are asking for:
1. "I'd like one regulatory network for my 70 colorectal tumours in which both transcription factors and microRNAs act as regulators of their target genes." -- available from PUMA.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

Captured request parameters:

- `network_file`: for

**PUMA**: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.

Routing-level input modality: gene expression, coexpression.

Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.

Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Workflow-specific scientific notes:

- PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network
- `mirna_file`: miRNA list

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

## S689610

Request: Run BONOBO on expr_ms_lesions.tsv (27 multiple sclerosis lesion samples; log2-transformed and centered per gene; gene IDs in the first column, sample IDs in the header), but only write networks for samples MS_03, MS_11 and MS_19, saved as .csv files.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.42s)
● Matching registered workflows…
✓ Workflow — BONOBO
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- BONOBO inputs: error: BONOBO expression_file does not exist: [CHECKOUT]/expr_ms_lesions.tsv

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

## S544211

Request: Can BONOBO run with sparsify on at a 0.01 confidence level and delta fixed at 0.5 for my 18 log-transformed, centered endometriosis samples?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.47s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "sparsify on at a 0.01 confidence level and delta fixed at 0.5 for my 18 log-transformed, centered" -- not available here as asked. BONOBO: with sparsify, delta must be above 0 and below 1/3, got 0.5. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
      "\"sparsify on at a 0.01 confidence level and delta fixed at 0.5 for my 18 log-transformed, centered\" -- not available here as asked. BONOBO: with sparsify, delta must be above 0 and below 1/3, got 0.5. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you…"
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

Request: Run CONDOR directly on expr_kidney_fibrosis.tsv (gene-by-sample RNA-seq for 64 biopsies) to get gene communities. I don't have any motif or PPI files, just this expression table.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
● Preparing next step…
What I understood you are asking for:
1. "to get gene communities" -- not available here: no registered workflow produces this. CONDOR does not meet "I don't have any motif or PPI files, just this expression table.".

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
        "label": "“to get gene communities”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "CONDOR does not meet \"I don't have any motif or PPI files, just this expression table.\".",
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

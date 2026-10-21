## S510264

Request: Please execute BONOBO on liver_log2_centered.tsv immediately (gene rows, 14 donor columns, log2-transformed and gene-centered). Sparsify at a 0.05 confidence level and fix delta at 0.4 rather than estimating it. HDF5 output into bonobo_liver/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.24s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "Please execute BONOBO on liver_log2_centered.tsv immediately" -- not available here as asked. BONOBO: with sparsify, delta must be above 0 and below 1/3, got 0.4. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
      "\"Please execute BONOBO on liver_log2_centered.tsv immediately\" -- not available here as asked. BONOBO: with sparsify, delta must be above 0 and below 1/3, got 0.4. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you asked for."
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

## S521774

Request: Here are expr_brca_160.tsv, motif_hg38.txt and ppi_string_hs.txt. Please run whatever is appropriate now and put the results in runs/brca/; I'll look at the output tomorrow morning.

Complete recorded stdout:
````text
● Classifying requested outcome…
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

Request: I've uploaded kidney_expr_64.tsv, tf_motif.txt, tf_ppi.txt, mirna_prior.txt and mirna_ids.txt for 64 biopsies. Please launch the standard NetZoo analysis on them now, with all output going to /data/runs/kidney/.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Matched workflows — PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER, GIRAFFE
? Clarification needed
What I understood you are asking for:
1. "Please launch the standard NetZoo analysis on them now, with all output going to /data/runs/kidney/." -- available from PUMA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

You asked me to run this, and PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER and GIRAFFE all fit it. Tell me which one to run; I will then find your input files and show a preview, and nothing runs until you approve it.

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
    "headline": "6 registered methods can build a regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.",
    "points": [
      "Understood goal: a regulatory network.",
      "LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA, PUMA, OTTER and GIRAFFE give one across all samples.",
      "Nothing you said favours one method yet; each option says when to pick it.",
      "Picking an option finds your input files and shows a preview; nothing runs until you approve it."
    ],
    "choices": {
      "header": "Method",
      "question": "Which workflow should I run?",
      "options": [
        {
          "key": "run_panda",
          "label": "PANDA",
          "description": "One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS",
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
          "key": "run_puma",
          "label": "PUMA",
          "description": "One TF + miRNA network across all your samples · Pick it if the regulators include miRNAs",
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
          "key": "run_lioness_panda",
          "label": "LIONESS-PANDA",
          "description": "One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample",
          "answer": "Start planning LIONESS-PANDA",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_panda",
          "granularity": "sample_specific",
          "resolution": "plan_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_lioness_puma",
          "label": "LIONESS-PUMA",
          "description": "One TF + miRNA network per sample, plus the cohort network · Pick it if the regulators include miRNAs",
          "answer": "Start planning LIONESS-PUMA",
          "recommended": false,
          "badge": "",
          "available": true,
          "reason": "",
          "action": "run_lioness_puma",
          "granularity": "sample_specific",
          "resolution": "plan_workflow",
          "paths": [],
          "compare_actions": []
        },
        {
          "key": "run_otter",
          "label": "OTTER",
          "description": "The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern",
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
          "key": "run_giraffe",
          "label": "GIRAFFE",
          "description": "One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level",
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

## S183684

Request: Can COBRA or CONDOR do anything useful with our liver fibrosis RNA-seq? It's 88 patients recruited at three hospitals, with fibrosis stage recorded for each. I'm open to suggestions on what to look at.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (6.33s)
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

## S333127

Request: My Arabidopsis drought experiment has leaf RNA-seq at four time points with six plants each. I'm curious what network approaches could reveal about the response, but I don't really know what to ask for yet.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.53s)
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

## S334943

Request: We profiled 70 patients with RNA-seq, DNA methylation arrays and plasma metabolomics. Please use DRAGON to build a single partial-correlation network spanning all three layers at once, so that the cross-layer edges among methylation, expression and metabolites are estimated jointly in one model.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.18s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Please use DRAGON to build a single partial-correlation network spanning all three layers at once, so that the cross-layer edges among methylation, expression and metabolites are estimated jointly in one model." -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

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
        "label": "“Please use DRAGON to build a single partial-correlation network spanning all…",
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

## S359020

Request: With 120 AML bone-marrow RNA-seq samples and motif and PPI priors, I need one number per transcription factor per patient to correlate with relapse. I'm genuinely unsure whether that number should describe how strongly the TF is wired to its targets in that patient, or how active the TF is regardless of its own mRNA.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.93s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Do you want the number to describe how active the TF is regardless of its own mRNA?
  You wrote: "I'm genuinely unsure whether that number should describe how strongly the TF is wired to its targets in that patient, or how active the TF is regardless of its own mRNA". GIRAFFE's contract: "TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression".

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
      "Do you want the number to describe how active the TF is regardless of its own mRNA?"
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

Request: I already have a cohort-wide TF-to-gene network saved as a source, target, weight edge list; weights were thresholded so all are non-negative, and TF and gene IDs never overlap. What I want now are communities in which groups of TFs and groups of genes cluster together, with separate TF-side and gene-side memberships.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.15s)
● Matching registered workflows…
✓ Workflow — CONDOR
✓ Guidance prepared
What I understood you are asking for:
1. "What I want now are communities in which groups of TFs and groups of genes cluster together, with separate TF-side and gene-side memberships" -- available from CONDOR.

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

## S933684

Request: SAMBAR pathway-based subtypes are what we want for 210 tumours, from a mutation matrix our core facility produced. I honestly don't know whether their calls are somatic (tumour versus matched normal) or germline variants; the README doesn't say and the analyst has left.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.50s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the calls somatic variants?
  You wrote: "I honestly don't know whether their calls are somatic (tumour versus matched normal) or germline variants; the README doesn't say and the analyst has left". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

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
      "Are the calls somatic variants?"
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

Request: Go ahead and start a run on pbmc_bulk_60donors.tsv and write the outputs to out/pbmc/. I just want to see something network-like before Thursday's lab meeting; there's no particular question yet.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.18s)
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

Request: Can you set up BONOBO for 5 endometrial biopsies? The gene-by-sample table is already log2-transformed and mean-centered per gene. I need one co-expression network per biopsy plus a p-value for every edge, so turn on sparsify and save_pvals to keep the full matrices; I'll threshold at 0.01 myself afterwards. CSV files, please.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (21.51s)
● Matching registered workflows…
✓ Workflow — BONOBO
● Preparing next step…
? Clarification needed
  Input required

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.

Select input 1 of 1: Expression matrix (expression_file)
Enter a candidate number or a full path.
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

## S239208

Request: Start COBRA right away on vst_counts.tsv (18,000 genes by 210 samples) with design.csv, whose rows are exactly those 210 sample IDs and whose numeric columns are an intercept, disease status (0/1) and two 0/1 dummy columns for the three recruiting sites. Disease is what we study; site should be adjusted for. Write everything to /scratch/cobra_run1/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Workflow — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "Start COBRA right away" -- available from COBRA.

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

## S166046

Request: What could GIRAFFE tell me about our T-cell exhaustion time course? We have RNA-seq at six time points from four donors, plus human motif and PPI priors, but I'm not sure what question to put to it.

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

## S592328

Request: Set SAMBAR going on mut_pilot.csv (6 tumours x 900 genes, non-negative counts), exon_sizes.csv, cancer_genes.txt and h.all.v2023.gmt, trying anywhere from 2 to 8 subtypes. Results go to sambar_pilot/ and the job can begin straight away.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.00s)
● Matching registered workflows…
✓ Workflow — SAMBAR
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- SAMBAR inputs: error: mutation_file must be an existing regular file: [CHECKOUT]/mut_pilot.csv
- SAMBAR inputs: error: exon_size_file must be an existing regular file: [CHECKOUT]/exon_sizes.csv
- SAMBAR inputs: error: cancer_gene_file must be an existing regular file: [CHECKOUT]/cancer_genes.txt
- SAMBAR inputs: error: pathway_file must be an existing regular file: [CHECKOUT]/h.all.v2023.gmt

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

## S314508

Request: For GIRAFFE on our 36 pancreatic islet samples, I'd like to change the optimizer: learning rate 1e-4, 2,000 iterations, and double the weight on the PPI agreement term. Expression, motif prior and PPI are ready with matching identifiers.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "learning rate 1e-4" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "learning rate 1e-4" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
      "\"learning rate 1e-4\" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so \"learning rate 1e-4\" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for."
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

Request: Run LIONESS-PANDA now: the expression file is pilot_expr.tsv with exactly three mouse retina samples, plus motif_mm10.txt and ppi_mm10.txt. Save the aggregate PANDA network to out/panda_all.txt and the per-sample networks to out/lioness_samples.txt. Three samples is all we will ever have from this pilot, so please don't wait for more.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.15s)
● Matching registered workflows…
✓ Workflow — PANDA → LIONESS-PANDA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: [CHECKOUT]/pilot_expr.tsv
- PANDA/PUMA inputs: error: motif file does not exist: [CHECKOUT]/motif_mm10.txt
- PANDA/PUMA inputs: error: PPI file does not exist: [CHECKOUT]/ppi_mm10.txt

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

## S596980

Request: I want to see how gene co-expression depends on sequencing batch and on disease status across roughly 650 samples, using a numeric design table keyed by sample ID. What I don't know is whether the expression table my analyst exported is the full 19,000-gene transcriptome or the 500-gene filtered panel.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.76s)
● Matching registered workflows…
● Preparing next step…
Before I choose a workflow, please tell me:
- Which of these is right: 500 or 19,000?
  You wrote: "the full 19,000-gene transcriptome or the 500-gene filtered panel".
  - 500: no registered workflow can do this as asked -- COBRA requires more genes than samples; the request has 500 genes and 650 samples
  - 19,000: COBRA can do this

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
      "Which of these is right: 500 or 19,000?"
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

## S504545

Request: Could I get LIONESS co-expression networks, one per sample, for our zebrafish fin-regeneration RNA-seq? The matrix has four libraries right now, but the sequencing core flagged one, possibly two, as failed, and I don't yet know how many will have to be dropped.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.91s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Will at least three samples remain after dropping the failed ones?
  You wrote: "I don't yet know how many will have to be dropped". LIONESS-COEXPRESSION's contract: "Require at least three samples and validate expression inside the execution wrapper".

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
      "Will at least three samples remain after dropping the failed ones?"
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

Request: Process counts_synovium_140.tsv and covariates_140.csv now (batch, age, sex and disease activity score for each of the 140 patients) and put the results in out/ra/. Let me know when it's done.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.35s)
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

## S942022

Request: We want SAMBAR subtypes for 120 lung adenocarcinomas from a somatic mutation matrix (samples by genes, non-negative mutation counts), with exon lengths, a cancer-gene list and an MSigDB-format GMT. Try between 3 and 8 subtypes, use average linkage, and switch off the per-patient mutation-burden normalization. The distance can stay at its default.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (11.13s)
● Matching registered workflows…
✓ Workflow — SAMBAR
✓ Guidance prepared
What I understood you are asking for:
1. "SAMBAR subtypes" -- available from SAMBAR.

Assumptions behind this recommendation (not confirmed facts):

- The somatic mutation matrix is suitable for subtype analysis.
- Exon lengths, cancer-gene list, and MSigDB-format GMT are provided as additional inputs.
- The analysis will utilize average linkage for clustering.
- The user has specified the number of subtypes to try between 3 and 8.
- The user has indicated to switch off per-patient mutation-burden normalization.

Selected path: **SAMBAR**.

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
    "headline": "SAMBAR produces a gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).",
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

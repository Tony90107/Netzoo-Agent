## S775856

Request: Set up BONOBO for 16 log-transformed, gene-centered expression profiles from sorted human microglia: sparsify at bonobo_confidence 0.05, delta fixed at 0.5 so each sample weighs as much as its background, and .h5 output. Genes are on rows and sample IDs form the header.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.27s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Set up BONOBO for 16 log-transformed, gene-centered expression profiles from sorted human microglia: sparsify at bonobo_confidence 0.05, delta fixed at 0.5 so each sample weighs as much as its background, and .h5 output." -- not available here as asked. BONOBO: with sparsify, delta must be above 0 and below 1/3, got 0.5. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
      "\"Set up BONOBO for 16 log-transformed, gene-centered expression profiles from sorted human microglia: sparsify at bonobo_confidence 0.05, delta fixed at 0.5 so each sample weighs as much as its background, and .h5 output.\" -- not available here as asked. BONOBO: with sparsify, delta must be above…"
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

## S650010

Request: I need the per-sample DRAGON networks run today on 60 matched samples: transcripts.tsv and metabolites.tsv (100 metabolites), outputs to ld_out/. For the transcript layer my co-author kept either the top 300 variable genes or all 1,500 that passed filtering, and I have no idea which version she uploaded.

Complete recorded stdout:
````text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Which of these is right: 300 or 1,500?
  You wrote: "either the top 300 variable genes or all 1,500 that passed filtering".
  - 300: LIONESS-DRAGON can do this
  - 1,500: no registered workflow can do this as asked -- LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 1,600 features and 60 samples give 76,752,000

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
      "Which of these is right: 300 or 1,500?"
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

Request: We want a TF-to-gene regulatory network for each one of our 74 high-grade serous ovarian tumors, so that later we can relate each TF's targeting in a tumor to platinum response. Inputs are a gene-by-sample RNA-seq matrix, a human TF motif prior and a STRING-derived TF PPI file; we have no miRNA data at all.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.26s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "We want a TF-to-gene regulatory network for each one of our 74 high-grade serous ovarian tumors" -- available from LIONESS-PANDA.

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

## S549145

Request: Execute COBRA now: expr_panel.tsv is a NanoString panel of 150 genes measured in 400 patients, and design_panel.tsv has the matching patient IDs with numeric columns for site (0/1/2) and age. Save the results under cobra_panel/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Guidance prepared
What I understood you are asking for:
1. "Execute COBRA now:" -- not matched to any registered workflow.
2. "Save the results under cobra_panel/" -- not available here: no registered workflow produces this. Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.

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
      "Understood: \"Execute COBRA now:\"",
      "Understood: \"Save the results under cobra_panel/\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Execute COBRA now:”",
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
        "label": "“Save the results under cobra_panel/”",
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

## S546619

Request: Across 58 human tonsil B-cell samples, I want an activity value for every transcription factor in every sample that isn't simply the TF's own mRNA level, and I also want to know whether each TF activates or represses each of its targets. The expression matrix, a motif prior and a TF-TF PPI matrix with matching IDs are ready.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.58s)
● Matching registered workflows…
✓ Workflow — GIRAFFE
✓ Guidance prepared
What I understood you are asking for:
1. "I want an activity value for every transcription factor in every sample that isn't simply the TF's own mRNA level" -- available from GIRAFFE.
2. "whether each TF activates or represses each of its targets" -- available from GIRAFFE.

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

## S882040

Request: Can OTTER give me one TF-to-gene network per patient? I have 95 glioblastoma RNA-seq samples with a motif seed and a PPI file, and I specifically want OTTER's graph-matching objective rather than PANDA's message passing, applied patient by patient the way LIONESS does it.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.09s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Can OTTER give me one TF-to-gene network per patient?" -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

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
        "label": "“Can OTTER give me one TF-to-gene network per patient?”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "OTTER does not give it: no per-sample OTTER is registered.",
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

## S740494

Request: Go ahead and run it now: TF-plus-miRNA networks for each of our 25 endometrial tumors, from expr_ucec.tsv (genes by samples), motif_prior.tsv (TF and miRNA target edges, regulator in column one), ppi_prior.tsv, and mirna_ids.txt with one miRNA ID per line. Aggregate network to out/puma_all.txt, per-sample networks to out/lioness/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.79s)
● Matching registered workflows…
✓ Workflow — PUMA → LIONESS-PUMA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: [CHECKOUT]/expr_ucec.tsv
- PANDA/PUMA inputs: error: motif file does not exist: [CHECKOUT]/motif_prior.tsv
- PANDA/PUMA inputs: error: PPI file does not exist: [CHECKOUT]/ppi_prior.tsv
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

## S142779

Request: Is BONOBO OK for my 14 Drosophila wing-disc samples? I need one co-expression network per sample. The matrix came from a collaborator as 'normalized values', and I can't tell whether it was log-transformed or centered; the README doesn't say either way.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.01s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the expression data numeric, finite, complete, and gene-by-sample with at least three samples?
  You wrote: "The matrix came from a collaborator as 'normalized values', and I can't tell whether it was log-transformed or centered; the README doesn't say either way". BONOBO's contract: "Expression data must be numeric, finite, complete, gene-by-sample, and have at least three total samples so each leave-one-out background has at least two samples".
- Is the expression log-transformed and centered?
  You wrote: "I can't tell whether it was log-transformed or centered; the README doesn't say either way". BONOBO's contract: "the agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression".

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
      "Is the expression data numeric, finite, complete, and gene-by-sample with at least three samples?",
      "Is the expression log-transformed and centered?"
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

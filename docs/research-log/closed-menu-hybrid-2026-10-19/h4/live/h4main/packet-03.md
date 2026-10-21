## S775856

Request: We have primary tumour RNA-seq and overall survival for 200 pancreatic cancer patients, and we downloaded human motif and PPI priors that we have not used yet. What kind of network analysis would make sense here?

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.46s)
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

## S650010

Request: I have a control and a disease TF-gene network written as one edge table over the same TF-gene pairs. I want each node's differential modularity score, with the control network as the null model, so that I can quantify directly how the disease network's module structure differs from the control's.

Complete recorded stdout:
````text
● Classifying requested outcome…
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "I want each node's differential modularity score, with the control network as the null model, so that I can quantify directly how the disease network's module structure differs from the control's." -- not matched to any registered workflow.

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
        "label": "“I want each node's differential modularity score, with the control network as…",
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

## S890091

Request: Please use DRAGON to relate plasma proteomics to whole-blood RNA-seq for our 40 participants. Both tables label rows P01 to P40, but I've just learned the proteomics may come from a different study cohort that reused the same participant codes, and I can't confirm whether they are the same people.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.92s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the participant codes in the proteomics data the same individuals as in the RNA-seq data?
  You wrote: "the proteomics may come from a different study cohort that reused the same participant codes, and I can't confirm whether they are the same people". DRAGON's contract: "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven".

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
      "Are the participant codes in the proteomics data the same individuals as in the RNA-seq data?"
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

Request: Please run OTTER today on expr_heart.tsv, motif_seed.tsv and ppi_tf.tsv, writing otter_heart.tsv. My notes from the methods meeting say lam = 0.35, but the slide we presented says lam = 3.5, and I don't know which one the group intended. Everything else can stay at defaults.

Complete recorded stdout:
````text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the intended value of lam 0.35?
  You wrote: "lam = 0.35, but the slide we presented says lam = 3.5, and I don't know which one the group intended". OTTER's contract: "setting lam (number; minimum 0; maximum 1): Weight of gene co-expression versus the TF-TF PPI network in OTTER's fit, as (lam, 1 - lam); not a sparsity penalty".

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
      "Is the intended value of lam 0.35?"
    ],
    "choices": null,
    "unavailable": [],
    "next_steps": [],
    "ran_nothing": true
  }
]
````

## S546619

Request: Can you run LIONESS-OTTER on our 40 lupus patients? I want one OTTER-style TF-to-gene network per patient from the expression matrix, motif seed and PPI file, using the relaxed graph-matching objective rather than PANDA's message passing.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.48s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Can you run LIONESS-OTTER on our 40 lupus patients?" -- not available here as asked. NetZoo has no registered method or variant "LIONESS-OTTER".
2. "I want one OTTER-style TF-to-gene network per patient from the expression matrix, motif seed and PPI file, using the relaxed graph-matching objective rather than PANDA's message passing." -- not available here as asked. NetZoo has no registered method or variant "LIONESS-OTTER". OTTER does not give it: no per-sample OTTER is registered.

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
      "Understood: \"Can you run LIONESS-OTTER on our 40 lupus patients?\"",
      "Understood: \"I want one OTTER-style TF-to-gene network per patient from the expression matrix, motif seed and PPI file, using the relaxed graph-matching objective rather than PANDA's message passing.\""
    ],
    "choices": null,
    "unavailable": [
      {
        "key": "capability-1",
        "label": "“Can you run LIONESS-OTTER on our 40 lupus patients?”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo has no registered method or variant \"LIONESS-OTTER\".",
        "action": null,
        "granularity": null,
        "resolution": "none",
        "paths": [],
        "compare_actions": []
      },
      {
        "key": "capability-2",
        "label": "“I want one OTTER-style TF-to-gene network per patient from the expression…",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "NetZoo has no registered method or variant \"LIONESS-OTTER\".",
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

Request: Using matched DNA methylation and RNA-seq from 60 colon biopsies, I need a directed network showing whether each methylation site drives its gene's expression or the other way round, so we can claim causal regulation in the paper rather than mere correlation.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.16s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "a directed network showing whether each methylation site drives its gene's expression or the other way round" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators. Every registered workflow estimates associations or model coefficients from observational data.

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
        "label": "“a directed network showing whether each methylation site drives its gene's…",
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

## S740494

Request: From 140 melanoma patients treated with anti-PD-1, with pre-treatment RNA-seq and responder labels, I want a trained model that predicts whether a new patient will respond, reported with an AUC on held-out patients.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.38s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "a trained model that predicts whether a new patient will respond, reported with an AUC on held-out patients." -- not matched to any registered workflow.

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
        "label": "“a trained model that predicts whether a new patient will respond, reported…",
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

## S142779

Request: I need COBRA run today: expr_panel.tsv is a 400-gene targeted panel across 520 samples, design_520.csv has an intercept plus smoker (0/1) and batch (0/1) columns for exactly those samples, and outputs should go to cobra_panel/.

Complete recorded stdout:
````text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.96s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "across 520 samples" -- not available here as asked. COBRA requires more genes than samples; the request has 400 genes and 520 samples.

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
        "label": "“across 520 samples”",
        "description": "",
        "answer": "",
        "recommended": false,
        "badge": "",
        "available": false,
        "reason": "COBRA requires more genes than samples; the request has 400 genes and 520 samples.",
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

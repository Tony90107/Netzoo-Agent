## S069

Request (turn 1): We have a bipartite TF-gene network from PANDA. Is there a method that lets a TF belong to more than one module at the same time?

Requirements to judge (in the user's words):
R1: "lets a TF belong to more than one module at the same time"

Reply:

````
What I understood you are asking for:
1. "Is there a method that lets a TF belong to more than one module at the same time?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that lets a TF belong to more than one module at the same… — Not matched to any registered workflow.
- next step: Start a new task

## S070

Request (turn 1): We have expression from 100 samples with age recorded. We want the co-expression adjusted for age and a list of genes differentially expressed with age.

Requirements to judge (in the user's words):
R1: "the co-expression adjusted for age"
R2: "a list of genes differentially expressed with age"

Reply:

````
What I understood you are asking for:
1. "the co-expression adjusted for age" -- available from COBRA.
2. "a list of genes differentially expressed with age" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

Assumptions behind this recommendation (not confirmed facts):

- The expression data is suitable for co-expression analysis.
- Age is a significant factor affecting gene expression.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

What you asked about:

- "We want the co-expression adjusted for age and a list of genes differentially expressed with age." — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Picked from 2 fitting methods because you wrote “co-expression adjusted for age”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- not available: “a list of genes differentially expressed with age” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S071

Request (turn 1): We have a bipartite TF-gene network. We want its modules and the pathways enriched in each module.

Requirements to judge (in the user's words):
R1: "its modules"
R2: "the pathways enriched in each module"

Reply:

````
What I understood you are asking for:
1. "its modules" -- available from CONDOR.
2. "the pathways enriched in each module" -- available from CONDOR's output plus a step you run outside NetZoo: A gene-set tool outside NetZoo.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “modules”:

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

For “pathways enriched in each module”:

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

For “pathways enriched in each module”:

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: You described 2 approaches; 3 registered workflows fit them.
- question: Which hypothesis should we start with?
- option: CONDOR — For “modules” · Finds TF-gene communities (modules) in a two-mode network
- option: DRAGON — For “pathways enriched in each module” · Partial-correlation network across two omics layers of the same samples
- option: LIONESS-DRAGON — For “pathways enriched in each module” · One two-layer partial-correlation network per sample, derived leave-one-out
- next step: Start a new task

## S072

Request (turn 1): What does LIONESS assume about the samples when it estimates one network per sample?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S073

Request (turn 1): We have expression, motifs and PPI from 60 patients. Which method estimates each patient's own TF-gene network from how the cohort network changes when that patient is left out?

Requirements to judge (in the user's words):
R1: "estimates each patient's own TF-gene network"

Reply:

````
What I understood you are asking for:
1. "estimates each patient's own TF-gene network from how the cohort network changes when that patient is left out" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 patients, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

For your question ("how the cohort network changes when that patient is left out"):
- **LIONESS-PANDA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 60 patients, 61 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Your question: which individuals change or stand out; the reply says what LIONESS-PANDA give toward it and the step after each.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S074

Request (turn 1): What does LIONESS assume about the samples when it estimates one network per sample?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S075

Request (turn 1): When is a Gaussian graphical model better than plain correlation for linking two omics layers?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
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

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S076

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and, for each community, the TFs that are most central to it.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "for each community, the TFs that are most central to it"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "for each community, the TFs that are most central to it" -- available from CONDOR.

Assumptions behind this recommendation (not confirmed facts):

- The TF-gene network is suitable for community detection analysis.

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

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S077

Request (turn 1): We have spatial transcriptomics of 3,000 spots with motifs and PPI. Which method models how each spot's regulatory network is shaped by the networks of its neighbouring spots?

Requirements to judge (in the user's words):
R1: "models how each spot's regulatory network is shaped by the networks of its neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "Which method models how each spot's regulatory network is shaped by the networks of its neighbouring spots?" -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Which method models how each spot's regulatory network is shaped by the… — OTTER does not give it: no per-sample OTTER is registered.
- next step: Start a new task

## S078

Request (turn 1): We have expression and methylation from 80 patients at two visits. Is there a method that captures how methylation at the first visit drives expression at the second visit?

Requirements to judge (in the user's words):
R1: "captures how methylation at the first visit drives expression at the second visit"

Reply:

````
What I understood you are asking for:
1. "Is there a method that captures how methylation at the first visit drives expression at the second visit?" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that captures how methylation at the first visit drives… — Every registered workflow estimates associations or model coefficients from observational data.
- next step: Start a new task

## S079

Request (turn 1): We have expression, motifs and PPI from 60 tumors. We want each TF's activity per tumor and each TF's protein abundance in each tumor.

Requirements to judge (in the user's words):
R1: "each TF's activity per tumor"
R2: "each TF's protein abundance in each tumor"

Reply:

````
What I understood you are asking for:
1. "each TF's activity per tumor" -- available from GIRAFFE.
2. "each TF's protein abundance in each tumor" -- not available here: no registered workflow produces this. GIRAFFE does not give it: activity is inferred from expression and priors, not measured.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

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

Card shown with the reply:
- headline: GIRAFFE fits your goal: cohort-level TF activity matrix.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- not available: “each TF's protein abundance in each tumor” — GIRAFFE does not give it: activity is inferred from expression and priors, not measured.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S080

Request (turn 1): We have expression and methylation from 90 samples. We want the cross-layer network and the causal direction of each link.

Requirements to judge (in the user's words):
R1: "the cross-layer network"
R2: "the causal direction of each link"

Reply:

````
What I understood you are asking for:
1. "the cross-layer network" -- available from DRAGON.
2. "the causal direction of each link" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "the causal direction of each link": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- not available: “the causal direction of each link” — Every registered workflow estimates associations or model coefficients from observational data.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S081

Request (turn 1): We have expression from 2,000 single cells plus TF motifs and PPI. Is there a method that infers a regulatory network for each individual cell?

Requirements to judge (in the user's words):
R1: "infers a regulatory network for each individual cell"

Reply:

````
What I understood you are asking for:
1. "Is there a method that infers a regulatory network for each individual cell?" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that infers a regulatory network for each individual cell?” — LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S082

Request (turn 1): What is the difference between a per-sample regulatory network and a cohort network?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **LIONESS-PUMA** — produces: One TF/miRNA-gene network per sample, plus the aggregate network.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S083

Request (turn 1): We have expression and methylation from 100 matched samples. Is there a method that captures the direct links between the two layers while conditioning on all the other features?

Requirements to judge (in the user's words):
R1: "captures the direct links between the two layers while conditioning on all the other features"

Reply:

````
What I understood you are asking for:
1. "Is there a method that captures the direct links between the two layers while conditioning on all the other features?" -- available from DRAGON.

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

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S084

Request (turn 1): Why does OTTER need a PPI network as well as expression data?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
OTTER: Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints.
Registered required inputs: motif_file, ppi_file, output_file.
Registered workflow controls: output_format (type=enum, default='matrix'), computing (type=enum, default='cpu'), precision (type=enum, default='double'), lam (type=number, default=0.035), gamma (type=number, default=0.335), iterations (type=integer, default=60), eta (type=number, default=1e-05), bexp (type=number, default=1.0).
Output: aggregate TF-to-gene regulatory networks.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 
- next step: Start a new task

## S085

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and a 3D animation of the communities rotating.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "a 3D animation of the communities rotating"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "a 3D animation of the communities rotating" -- not matched to any registered workflow.

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

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- not available: “a 3D animation of the communities rotating” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S086

Request (turn 1): We have a bipartite TF-gene network from PANDA. Is there a method that lets a TF belong to more than one module at the same time?

Requirements to judge (in the user's words):
R1: "lets a TF belong to more than one module at the same time"

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **CONDOR** — produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- question: Which one do you want to look at?
- option: CONDOR — Not confirmed. Produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.
- next step: Start a new task

## S087

Request (turn 1): We have a TF-gene network from PANDA. Which method groups the TFs and genes into modules by maximizing bipartite modularity?

Requirements to judge (in the user's words):
R1: "groups the TFs and genes into modules by maximizing bipartite modularity"

Reply:

````
What I understood you are asking for:
1. "Which method groups the TFs and genes into modules by maximizing bipartite modularity?" -- available from CONDOR.

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

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S088

Request (turn 1): We have RNA-seq from 70 liver samples plus TF motifs and PPI. Is there a method that weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions?

Requirements to judge (in the user's words):
R1: "weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions"

Reply:

````
What I understood you are asking for:
1. "weighs how strongly each TF regulates each gene by reconciling the motif prior with co-expression and protein interactions" -- available from PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a TF-gene regulatory network from expression data, a motif prior and a PPI network.
- point: Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S089

Request (turn 1): We have a TF-gene network from PANDA. Which method groups the TFs and genes into modules by maximizing bipartite modularity?

Requirements to judge (in the user's words):
R1: "groups the TFs and genes into modules by maximizing bipartite modularity"

Reply:

````
What I understood you are asking for:
1. "Which method groups the TFs and genes into modules by maximizing bipartite modularity?" -- available from CONDOR.

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

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S090

Request (turn 1): We have expression and methylation from 80 patients at two visits. Is there a method that captures how methylation at the first visit drives expression at the second visit?

Requirements to judge (in the user's words):
R1: "captures how methylation at the first visit drives expression at the second visit"

Reply:

````
About "how methylation at the first visit drives expression at the second visit": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `expression_file`: and

**DRAGON**: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.

Routing-level input modality: multi omic continuous.

Method premise: infer conditional associations using partial correlation.

DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

Workflow-specific scientific notes:

- DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
- DRAGON's precision-derived partial correlations estimate within-layer and cross-layer conditional associations after accounting for the other modeled features; this is an undirected association graph, not a causal guarantee or proof that every indirect effect is removed.
- The declared DRAGON API does not expose a separately tunable third cross-layer penalty such as lambda_inter; three independently controlled intra/inter-omics penalties are outside this workflow contract.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Other declared controls (not matched to this request; defaults apply unless you set them): `output_format`=matrix, `lambda1`, `lambda2`.

Distinct declared output artifacts (availability depends on workflow options):

- `multi_omic_network`: Inferred associations between omics features.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S091

Request (turn 1): We have expression, TF motifs and PPI from 70 samples and want a regulatory network.
Request (turn 2): Our regulators also include miRNAs, with predicted target sites.

Requirements to judge (in the user's words):
R1: "Our regulators also include miRNAs"

Reply:

````
I can map this to more than one compatible network result:

- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Should the result be aggregate or sample-specific?

**What your data allows.** Your request names only a miRNA list. PUMA and LIONESS-PUMA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a miRNA-gene regulatory network.
- point: Your request names only a miRNA list; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only a miRNA list — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Start a new task

## S092

Request (turn 1): We have expression and methylation from 80 patients at two visits. Is there a method that captures how methylation at the first visit drives expression at the second visit?

Requirements to judge (in the user's words):
R1: "captures how methylation at the first visit drives expression at the second visit"

Reply:

````
What I understood you are asking for:
1. "Is there a method that captures how methylation at the first visit drives expression at the second visit?" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that captures how methylation at the first visit drives… — Every registered workflow estimates associations or model coefficients from observational data.
- next step: Start a new task

## S093

Request (turn 1): We have expression with batch and sex recorded for 120 samples. Is there a method that separates how much of each gene pair's co-expression comes from each covariate?

Requirements to judge (in the user's words):
R1: "separates how much of each gene pair's co-expression comes from each covariate"

Reply:

````
What I understood you are asking for:
1. "separates how much of each gene pair's co-expression comes from each covariate" -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: co-expression network.
- point: Picked from 3 fitting methods because you wrote “separates how much of each gene pair's…”; LIONESS-COEXPRESSION and BONOBO also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION and BONOBO
- next step: Plan COBRA with my data
- next step: Start a new task

## S094

Request (turn 1): We have spatial transcriptomics of 3,000 spots with motifs and PPI. Which method models how each spot's regulatory network is shaped by the networks of its neighbouring spots?

Requirements to judge (in the user's words):
R1: "models how each spot's regulatory network is shaped by the networks of its neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "Which method models how each spot's regulatory network is shaped by the networks of its neighbouring spots?" -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Which method models how each spot's regulatory network is shaped by the… — OTTER does not give it: no per-sample OTTER is registered.
- next step: Start a new task

## S095

Request (turn 1): We have expression, motifs and PPI from 50 samples and want a TF-gene network.
Request (turn 2): Actually we need it to say whether each TF activates or represses each target, separately in every sample.

Requirements to judge (in the user's words):
R1: "whether each TF activates or represses each target, separately in every sample"

Reply:

````
What I understood you are asking for:
1. "whether each TF activates or represses each target, separately in every sample." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “whether each TF activates or represses each target, separately in every… — Not matched to any registered workflow.
- next step: Start a new task

## S096

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and, for each community, the TFs that are most central to it.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "for each community, the TFs that are most central to it"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "for each community, the TFs that are most central to it" -- available from CONDOR.

Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- next step: Start a new task

## S097

Request (turn 1): How do bipartite community methods decide which genes are core to a module?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
Routing matched these registered workflows to your words, but the capability check found no result in your request to check them against, so none is confirmed to give what you asked for:
- **CONDOR** — produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.

Compare what each produces with what you asked for, or describe the result you want from your data and it is checked against what each workflow produces.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check found no result in your request to check them against.
- point: Compare what each produces with what you asked for; describing the result you want has it checked.
- question: Which one do you want to look at?
- option: CONDOR — Not confirmed. Produces: Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity. Each regulator's and gene's core score -- its share of its community's modularity -- to pick out each community's core nodes.
- next step: Start a new task

## S098

Request (turn 1): What does LIONESS assume about the samples when it estimates one network per sample?

Requirements to judge (in the user's words):
(none: this request asks about methods; give `R: []`)
Judge `consult` for this session.

Reply:

````
I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a per-sample regulatory network.
- question: Which regulator type should the network model: transcription factors, miRNA regulators, or both?
- option: Transcription factors only — Leads to LIONESS-PANDA · One TF-gene network per sample, plus the cohort network
- option: Both TFs and miRNAs — Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus the cohort network · Also needs miRNA list
- next step: Start a new task

## S099

Request (turn 1): We have expression, motifs and PPI from 75 tumors. We want each TF's activity in each tumor and a signed TF-gene regulatory matrix.

Requirements to judge (in the user's words):
R1: "each TF's activity in each tumor"
R2: "a signed TF-gene regulatory matrix"

Reply:

````
What I understood you are asking for:
1. "each TF's activity in each tumor" -- available from GIRAFFE.
2. "a signed TF-gene regulatory matrix" -- available from GIRAFFE.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Your request can be read 2 ways, and they lead to different workflows.
- question: Which reading should we start with?
- option: Reading 1: “We want each TF's activity in each tumor” — GIRAFFE: a cohort-level TF activity matrix · Also estimates per-sample TF activity and signed activating/repressing effects
- option: Reading 2: “a signed TF-gene regulatory matrix” — GIRAFFE: a cohort-level signed regulatory-effect network · Also estimates per-sample TF activity and signed activating/repressing effects
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S100

Request (turn 1): We have expression with batch and sex recorded for 120 samples. Is there a method that separates how much of each gene pair's co-expression comes from each covariate?

Requirements to judge (in the user's words):
R1: "separates how much of each gene pair's co-expression comes from each covariate"

Reply:

````
What I understood you are asking for:
1. "separates how much of each gene pair's co-expression comes from each covariate" -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: co-expression network.
- point: Picked from 3 fitting methods because you wrote “Is there a method that separates how…”; LIONESS-COEXPRESSION and BONOBO also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION and BONOBO
- next step: Plan COBRA with my data
- next step: Start a new task

## S101

Request (turn 1): We have a TF-gene network from PANDA. We want its communities and, for each community, the TFs that are most central to it.

Requirements to judge (in the user's words):
R1: "its communities"
R2: "for each community, the TFs that are most central to it"

Reply:

````
What I understood you are asking for:
1. "its communities" -- available from CONDOR.
2. "the TFs that are most central to it" -- available from CONDOR.

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

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S102

Request (turn 1): We have a bipartite TF-gene network. We want its modules and the pathways enriched in each module.

Requirements to judge (in the user's words):
R1: "its modules"
R2: "the pathways enriched in each module"

Reply:

````
What I understood you are asking for:
1. "its modules" -- available from CONDOR.
2. "the pathways enriched in each module" -- available from CONDOR's output plus a step you run outside NetZoo: A gene-set tool outside NetZoo.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “modules”:

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

For “pathways enriched in each module”:

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

For “pathways enriched in each module”:

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
````

Card shown with the reply:
- headline: You described 2 approaches; 3 registered workflows fit them.
- question: Which hypothesis should we start with?
- option: CONDOR — For “modules” · Finds TF-gene communities (modules) in a two-mode network
- option: DRAGON — For “pathways enriched in each module” · Partial-correlation network across two omics layers of the same samples
- option: LIONESS-DRAGON — For “pathways enriched in each module” · One two-layer partial-correlation network per sample, derived leave-one-out
- next step: Start a new task

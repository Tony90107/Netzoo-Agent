## S026

Request (turn 1): We want batch-adjusted co-expression for 150 samples, and then a list of genes differentially expressed between cases and controls.

Requirements to judge (in the user's words):
R1: "batch-adjusted co-expression"
R2: "a list of genes differentially expressed between cases and controls"

Reply:

````
What I understood you are asking for:
1. "batch-adjusted co-expression" -- available from COBRA.
2. "a list of genes differentially expressed between cases and controls" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

Assumptions behind this recommendation (not confirmed facts):

- The user is interested in a single aggregate co-expression network for the 150 samples.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale. COBRA models co-expression as a function of sample covariates through conditional covariance estimation.

**COBRA**: Model covariate-associated gene co-expression with COBRA.

Routing-level input modality: expression matrix.

Method premise: remove or adjust technical batch effects; estimate how sample covariates change co-expression; model higher-order covariance or correlation structure; assess or remove hospital or site effects; assess or remove sequencing-batch effects.

COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.

For your question ("a list of genes differentially expressed between cases and controls"):
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Picked from 2 fitting methods because you wrote “We want batch-adjusted co-expression…”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- point: Your question: whether the groups or time points differ; the reply says what COBRA give toward it and the step after each.
- not available: “a list of genes differentially expressed between cases and controls” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S027

Request (turn 1): We have motifs, PPI and expression from 50 samples. Is there a method that fits one TF-gene network to agree with both the PPI and the co-expression?

Requirements to judge (in the user's words):
R1: "fits one TF-gene network to agree with both the PPI and the co-expression"

Reply:

````
This turn could not be checked against what the registered workflows produce, so the methods below have not been confirmed to give what you asked for.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- next step: Start a new task

## S028

Request (turn 1): We have microbiome abundances and metabolomics from 100 stool samples. Which method gives conditional associations between taxa and metabolites?

Requirements to judge (in the user's words):
R1: "conditional associations between taxa and metabolites"

Reply:

````
What I understood you are asking for:
1. "conditional associations between taxa and metabolites" -- available from DRAGON.

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

## S029

Request (turn 1): We have expression and metabolomics for 70 matched samples and want each sample's own two-layer network, with a p-value for every edge in every sample.

Requirements to judge (in the user's words):
R1: "each sample's own two-layer network"
R2: "a p-value for every edge in every sample"

Reply:

````
What I understood you are asking for:
1. "each sample's own two-layer network" -- available from LIONESS-DRAGON.
2. "with a p-value for every edge in every sample" -- not available here: no registered workflow produces this. LIONESS-DRAGON does not give it: LIONESS-DRAGON writes per-sample edge weights only; DRAGON's p-values are for the aggregate network.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

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
- headline: DRAGON is the closest registered match, but it is not a verified match for your request.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- not available: “with a p-value for every edge in every sample” — LIONESS-DRAGON does not give it: LIONESS-DRAGON writes per-sample edge weights only; DRAGON's p-values are for the aggregate network.
- next step: Start a new task

## S030

Request (turn 1): We have expression for 95 kidney samples, TF motifs, PPI and predicted miRNA target sites. We want one network of how TFs and miRNAs regulate genes across the cohort.

Requirements to judge (in the user's words):
R1: "one network of how TFs and miRNAs regulate genes across the cohort"

Reply:

````
What I understood you are asking for:
1. "one network of how TFs and miRNAs regulate genes across the cohort" -- available from PUMA.

Assumptions behind this recommendation (not confirmed facts):

- The expression data for 95 kidney samples is sufficient to infer the regulatory network.
- TF motifs and predicted miRNA target sites are relevant for constructing the regulatory relationships.

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

Card shown with the reply:
- headline: PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- next step: Plan PUMA with my data
- next step: Start a new task

## S031

Request (turn 1): We want a TF-gene network from expression, motifs and PPI of 75 samples.
Request (turn 2): We also need to know whether each TF activates or represses its targets.

Requirements to judge (in the user's words):
R1: "whether each TF activates or represses its targets"

Reply:

````
What I understood you are asking for:
1. "We also need to know whether each TF activates or represses its targets." -- available from GIRAFFE.

**GIRAFFE** fits the result you describe if you have a motif prior and a PPI network.

Your question asks for a cohort-level signed regulatory-effect network. **GIRAFFE** fits that result and scale.

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

**What your data allows.** GIRAFFE also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: GIRAFFE fits your goal if you have a motif prior and a PPI network.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S032

Request (turn 1): We have somatic mutations for 250 tumors. We want to know which of the mutations are drivers.

Requirements to judge (in the user's words):
R1: "which of the mutations are drivers"

Reply:

````
What I understood you are asking for:
1. "which of the mutations are drivers" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “which of the mutations are drivers” — SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.
- next step: Start a new task

## S033

Request (turn 1): We have proteomics and RNA-seq from 120 matched plasma samples. We want a partial-correlation network between proteins and transcripts, keeping only edges with adjusted p below 0.05.

Requirements to judge (in the user's words):
R1: "a partial-correlation network between proteins and transcripts, keeping only edges with adjusted p below 0.05"

Reply:

````
What I understood you are asking for:
1. "a partial-correlation network between proteins and transcripts, keeping only edges with adjusted p below 0.05" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a partial-correlation network between proteins and transcripts, keeping only… — Not matched to any registered workflow.
- next step: Start a new task

## S034

Request (turn 1): We have expression, TF motifs, PPI and miRNA target predictions for 60 patients. We want a separate TF and miRNA regulatory network for each patient.

Requirements to judge (in the user's words):
R1: "a separate TF and miRNA regulatory network for each patient"

Reply:

````
What I understood you are asking for:
1. "a separate TF and miRNA regulatory network for each patient" -- available from LIONESS-PUMA.

Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- sample-specific regulatory networks**
Result: regulatory networks (sample-specific), from inputs the request does not state.
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

**Reading 2 -- sample-specific regulatory networks**
Result: regulatory networks (sample-specific), from inputs the request does not state.
- **TF/miRNA regulatory network — PUMA → LIONESS-PUMA**
  - Registered purpose: Infer aggregate PUMA and sample-specific LIONESS-PUMA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

Which reading should we start with: 1 (LIONESS-PANDA), 2 (LIONESS-PUMA)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Your request can be read 2 ways, and they lead to different workflows.
- question: Which reading should we start with?
- option: Reading 1 — LIONESS-PANDA: a per-sample TF-gene regulatory network · One TF-gene network per sample, derived leave-one-out from the cohort
- option: Reading 2 — LIONESS-PUMA: a per-sample miRNA-gene regulatory network · One TF + miRNA network per sample, derived leave-one-out from the cohort
- next step: Plan LIONESS-PUMA with my data
- next step: Start a new task

## S035

Request (turn 1): We have RNA-seq of 300 tumors and no mutation data. We want patient subtypes from the expression profiles.

Requirements to judge (in the user's words):
R1: "patient subtypes from the expression profiles"

Reply:

````
What I understood you are asking for:
1. "patient subtypes" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “patient subtypes” — SAMBAR does not give it: SAMBAR's input is somatic mutations.
- next step: Start a new task

## S036

Request (turn 1): We have expression, motifs and PPI from 80 patients. We want to prove which TFs causally drive the disease state.

Requirements to judge (in the user's words):
R1: "prove which TFs causally drive the disease state"

Reply:

````
What I understood you are asking for:
1. "We want to prove which TFs causally drive the disease state." -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want to prove which TFs causally drive the disease state.” — Every registered workflow estimates associations or model coefficients from observational data.
- next step: Start a new task

## S037

Request (turn 1): We have lncRNA, miRNA and mRNA expression for 110 samples. We want a ceRNA network of lncRNAs sponging miRNAs.

Requirements to judge (in the user's words):
R1: "a ceRNA network of lncRNAs sponging miRNAs"

Reply:

````
What I understood you are asking for:
1. "We want a ceRNA network of lncRNAs sponging miRNAs." -- available from DRAGON or LIONESS-DRAGON.

Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- next step: Start a new task

## S038

Request (turn 1): We have a TF-gene network. We want gene modules in which one gene can belong to several modules at once.

Requirements to judge (in the user's words):
R1: "gene modules in which one gene can belong to several modules at once"

Reply:

````
What I understood you are asking for:
1. "gene modules in which one gene can belong to several modules at once" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “gene modules in which one gene can belong to several modules at once” — Not matched to any registered workflow.
- next step: Start a new task

## S039

Request (turn 1): We want the communities of our TF-gene network from PANDA.
Request (turn 2): We need its community structure compared against our second network, from the treated group.

Requirements to judge (in the user's words):
R1: "its community structure compared against our second network"

Reply:

````
What I understood you are asking for:
1. "We need its community structure compared against our second network, from the treated group." -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We need its community structure compared against our second network, from the… — CONDOR does not give it: one network at a time.
- next step: Start a new task

## S040

Request (turn 1): We have expression from 100 samples. We want a simulation of every gene's expression after knocking out STAT3.

Requirements to judge (in the user's words):
R1: "a simulation of every gene's expression after knocking out STAT3"

Reply:

````
What I understood you are asking for:
1. "a simulation of every gene's expression after knocking out STAT3" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a simulation of every gene's expression after knocking out STAT3” — Not matched to any registered workflow.
- next step: Start a new task

## S041

Request (turn 1): We have expression, motifs and PPI for 60 tumor and 60 normal samples. We want to know which TF-gene edges differ between tumor and normal.

Requirements to judge (in the user's words):
R1: "which TF-gene edges differ between tumor and normal"

Reply:

````
What I understood you are asking for:
1. "which TF-gene edges differ between tumor and normal" -- available from PANDA's output plus a step you run outside NetZoo: One run per condition on the same genes and priors, then compare; two aggregate networks give no per-sample spread for a test.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("which TF-gene edges differ between tumor and normal"):
- **PANDA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a TF-gene regulatory network.
- point: Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- point: Your question: whether the groups or time points differ; the reply says what PANDA, LIONESS-PANDA, OTTER and GIRAFFE give toward it and the step after each.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S042

Request (turn 1): We want one TF-gene network per patient from expression, motifs and PPI of 66 patients, plus a dashboard that updates live as new patients are added.

Requirements to judge (in the user's words):
R1: "one TF-gene network per patient"
R2: "a dashboard that updates live as new patients are added"

Reply:

````
What I understood you are asking for:
1. "one TF-gene network per patient" -- available from LIONESS-PANDA.
2. "a dashboard that updates live as new patients are added" -- not matched to any registered workflow.

About "a dashboard that updates live as new patients are added.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 66 patients, 67 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 66 patients, 67 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- not available: “a dashboard that updates live as new patients are added” — Not matched to any registered workflow.
- not available: Predict outcomes for new samples — No registered workflow builds a predictive model; per-sample results can only be its features.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S043

Request (turn 1): We want batch-adjusted co-expression for 150 samples, and then a list of genes differentially expressed between cases and controls.

Requirements to judge (in the user's words):
R1: "batch-adjusted co-expression"
R2: "a list of genes differentially expressed between cases and controls"

Reply:

````
What I understood you are asking for:
1. "batch-adjusted co-expression" -- available from COBRA.
2. "a list of genes differentially expressed between cases and controls" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

Assumptions behind this recommendation (not confirmed facts):

- The user is interested in a single aggregate co-expression network for the 150 samples.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale. COBRA models co-expression as a function of sample covariates through conditional covariance estimation.

**COBRA**: Model covariate-associated gene co-expression with COBRA.

Routing-level input modality: expression matrix.

Method premise: remove or adjust technical batch effects; estimate how sample covariates change co-expression; model higher-order covariance or correlation structure; assess or remove hospital or site effects; assess or remove sequencing-batch effects.

COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.

For your question ("a list of genes differentially expressed between cases and controls"):
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Picked from 2 fitting methods because you wrote “We want batch-adjusted co-expression…”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- point: Your question: whether the groups or time points differ; the reply says what COBRA give toward it and the step after each.
- not available: “a list of genes differentially expressed between cases and controls” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S044

Request (turn 1): We want a signed TF-gene regulatory matrix from expression, motifs and PPI of 90 samples, and the measured TF protein level in each sample.

Requirements to judge (in the user's words):
R1: "a signed TF-gene regulatory matrix"
R2: "the measured TF protein level in each sample"

Reply:

````
What I understood you are asking for:
1. "a signed TF-gene regulatory matrix from expression, motifs and PPI of 90 samples" -- available from GIRAFFE.
2. "the measured TF protein level in each sample" -- not available here: no registered workflow produces this. GIRAFFE does not give it: activity is inferred from expression and priors, not measured.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level signed regulatory-effect network. **GIRAFFE** fits that result and scale.

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
- headline: GIRAFFE fits your goal: cohort-level signed regulatory-effect network.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- not available: “the measured TF protein level in each sample” — GIRAFFE does not give it: activity is inferred from expression and priors, not measured.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S045

Request (turn 1): We have expression for 95 kidney samples, TF motifs, PPI and predicted miRNA target sites. We want one network of how TFs and miRNAs regulate genes across the cohort.

Requirements to judge (in the user's words):
R1: "one network of how TFs and miRNAs regulate genes across the cohort"

Reply:

````
What I understood you are asking for:
1. "one network of how TFs and miRNAs regulate genes across the cohort" -- available from PUMA.

Assumptions behind this recommendation (not confirmed facts):

- The expression data for 95 kidney samples is sufficient for constructing the regulatory network.
- TF motifs and predicted miRNA target sites are relevant for the regulatory relationships being inferred.

Selected path: **PUMA**.

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

Card shown with the reply:
- headline: PUMA produces a regulatory network (one cohort-level result).
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- next step: Plan PUMA with my data
- next step: Start a new task

## S046

Request (turn 1): We want a TF-gene network from expression, motifs and PPI of 75 samples.
Request (turn 2): We also need to know whether each TF activates or represses its targets.

Requirements to judge (in the user's words):
R1: "whether each TF activates or represses its targets"

Reply:

````
What I understood you are asking for:
1. "whether each TF activates or represses its targets" -- available from GIRAFFE.

**GIRAFFE** fits the result you describe if you have a motif prior and a PPI network.

Your question asks for a cohort-level signed regulatory-effect network. **GIRAFFE** fits that result and scale.

What you asked about:

- "whether each TF activates or represses its targets" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

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

**What your data allows.** GIRAFFE also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: GIRAFFE fits your goal if you have a motif prior and a PPI network.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S047

Request (turn 1): We have expression, motifs and PPI for 70 samples. We want TF-gene edges that are confirmed physical binding events, not predictions.

Requirements to judge (in the user's words):
R1: "TF-gene edges that are confirmed physical binding events"

Reply:

````
What I understood you are asking for:
1. "TF-gene edges that are confirmed physical binding events, not predictions." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene edges that are confirmed physical binding events, not predictions.” — Not matched to any registered workflow.
- next step: Start a new task

## S048

Request (turn 1): We want one TF-gene network per patient from expression, motifs and PPI of 66 patients, plus a dashboard that updates live as new patients are added.

Requirements to judge (in the user's words):
R1: "one TF-gene network per patient"
R2: "a dashboard that updates live as new patients are added"

Reply:

````
What I understood you are asking for:
1. "one TF-gene network per patient from expression, motifs and PPI of 66 patients" -- available from LIONESS-PANDA.
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

About "a dashboard that updates live as new patients are added.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- not available: Predict outcomes for new samples — No registered workflow builds a predictive model; per-sample results can only be its features.
- next step: Start a new task

## S049

Request (turn 1): We have a bipartite TF-gene network. We want a hierarchy of small modules nested inside larger modules.

Requirements to judge (in the user's words):
R1: "a hierarchy of small modules nested inside larger modules"

Reply:

````
What I understood you are asking for:
1. "We want a hierarchy of small modules nested inside larger modules." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a hierarchy of small modules nested inside larger modules.” — Not matched to any registered workflow.
- next step: Start a new task

## S050

Request (turn 1): We have a bipartite TF-gene network. We want a hierarchy of small modules nested inside larger modules.

Requirements to judge (in the user's words):
R1: "a hierarchy of small modules nested inside larger modules"

Reply:

````
What I understood you are asking for:
1. "We want a hierarchy of small modules nested inside larger modules." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a hierarchy of small modules nested inside larger modules.” — Not matched to any registered workflow.
- next step: Start a new task

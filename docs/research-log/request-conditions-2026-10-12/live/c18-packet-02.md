## S026

Request (turn 1): We want a network linking expression and proteomics in 60 samples.
Request (turn 2): The proteomics came from a separate group of 60 donors.

Requirements to judge (in the user's words):
R1: "The proteomics came from a separate group of 60 donors"

Reply:

````
What I understood you are asking for:
1. "a network linking expression and proteomics in 60 samples." -- available from DRAGON.

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

## S027

Request (turn 1): We have expression, motifs and PPI at 4 time points, 20 samples each. We want one network per time point to compare them.

Requirements to judge (in the user's words):
R1: "one network per time point to compare them"

Reply:

````
What I understood you are asking for:
1. "one network per time point" -- available from PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 6 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a TF-gene regulatory network.
- point: LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA, OTTER, GIRAFFE and PUMA give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- option: PUMA — One TF + miRNA network across all your samples · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list
- option: LIONESS-PUMA — One TF + miRNA network per sample, plus the cohort network · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list
- next step: Start a new task

## S028

Request (turn 1): We have expression for 140 samples with a batch covariate. We want the co-expression with the batch part separated.

Requirements to judge (in the user's words):
R1: "the co-expression with the batch part separated"

Reply:

````
What I understood you are asking for:
1. "We want the co-expression with the batch part separated." -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a co-expression network. **COBRA** fits that result.

What you asked about:

- "We want the co-expression with the batch part separated." — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

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
- point: Picked from 3 fitting methods because you wrote “We want the co-expression with the…”; LIONESS-COEXPRESSION and BONOBO also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION and BONOBO
- next step: Plan COBRA with my data
- next step: Start a new task

## S029

Request (turn 1): We have expression for two groups of 50 samples. We want the differentially expressed genes between them.

Requirements to judge (in the user's words):
R1: "the differentially expressed genes between them"

Reply:

````
What I understood you are asking for:
1. "We want the differentially expressed genes between them." -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want the differentially expressed genes between them.” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Start a new task

## S030

Request (turn 1): We have somatic mutations for 150 tumors. A patient may belong to more than one subtype. We want subtypes from pathway mutation scores.

Requirements to judge (in the user's words):
R1: "We want subtypes from pathway mutation scores"

Reply:

````
What I understood you are asking for:
1. "We want subtypes from pathway mutation scores." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want subtypes from pathway mutation scores.” — Not matched to any registered workflow.
- next step: Start a new task

## S031

Request (turn 1): We have a bipartite TF-gene network. Each TF may belong to several modules at once. We want its modules.

Requirements to judge (in the user's words):
R1: "We want its modules"

Reply:

````
What I understood you are asking for:
1. "We want its modules." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want its modules.” — Not matched to any registered workflow.
- next step: Start a new task

## S032

Request (turn 1): We want per-sample TF-gene networks from expression, motifs and PPI of 48 samples.
Request (turn 2): The 48 samples are bulk tumor biopsies.

Requirements to judge (in the user's words):
R1: "The 48 samples are bulk tumor biopsies"

Reply:

````
What I understood you are asking for:
1. "per-sample TF-gene networks" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 48 samples, 49 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** LIONESS-PANDA and PANDA also need a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 48 samples, 49 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Leads to LIONESS-PANDA or PANDA
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S033

Request (turn 1): We want a network linking expression and metabolites in 90 samples.
Request (turn 2): Both layers come from the same 90 samples.

Requirements to judge (in the user's words):
R1: "Both layers come from the same 90 samples"

Reply:

````
What I understood you are asking for:
1. "a network linking expression and metabolites" -- available from DRAGON.

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

## S034

Request (turn 1): We want the communities of our bipartite TF-gene network.
Request (turn 2): Genes should be allowed in several communities at the same time.

Requirements to judge (in the user's words):
R1: "Genes should be allowed in several communities at the same time"

Reply:

````
What I understood you are asking for:
1. "We want the communities of our bipartite TF-gene network." -- available from CONDOR.

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

## S035

Request (turn 1): We want per-sample co-expression networks for 120 spots.
Request (turn 2): The spots are on a tissue slide, and each network should use the neighbouring spots.

Requirements to judge (in the user's words):
R1: "each network should use the neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "per-sample co-expression networks for 120 spots" -- available from LIONESS-COEXPRESSION or BONOBO.

Based on what you said — "each network should use the neighbouring spots" — **BONOBO** fits better: a confidence value (p-value) is needed for each connection in each sample.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale.

**BONOBO** (recommend) — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable. Needs expression matrix. Produces inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result (one result per sample).

Other compatible option(s):
- **LIONESS-COEXPRESSION** — preferred when: dozens of samples or more; no sample covariates need to be separated or adjusted; approach: derive each sample network from all-sample and leave-one-out networks.

Should I use BONOBO, or does another listed option fit your study better?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Recommended: BONOBO, from what you said.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: BONOBO — Fits what you said: you need a p-value for each edge · One gene co-expression network per sample, with a p-value for each connection [Recommended]
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more
- next step: Start a new task

## S036

Request (turn 1): We have expression and methylation from the same 85 tumors. We want a partial-correlation network linking them.

Requirements to judge (in the user's words):
R1: "a partial-correlation network linking them"

Reply:

````
What I understood you are asking for:
1. "a partial-correlation network linking them" -- available from DRAGON.

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

## S037

Request (turn 1): We have Visium data for 4,000 spots with motifs and PPI. Each spot's network has to take its neighbouring spots into account. We want TF-gene networks per spot.

Requirements to judge (in the user's words):
R1: "We want TF-gene networks per spot"

Reply:

````
What I understood you are asking for:
1. "TF-gene networks per spot" -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene networks per spot” — OTTER does not give it: no per-sample OTTER is registered.
- next step: Start a new task

## S038

Request (turn 1): We have expression, motifs and PPI for 110 samples. We want one TF-gene network.

Requirements to judge (in the user's words):
R1: "We want one TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want one TF-gene network." -- available from PANDA, OTTER, GIRAFFE, LIONESS-PANDA or LIONESS-PUMA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S039

Request (turn 1): We have expression, motifs and PPI at 4 time points, 20 samples each. We want one network per time point to compare them.

Requirements to judge (in the user's words):
R1: "one network per time point to compare them"

Reply:

````
What I understood you are asking for:
1. "one network per time point" -- available from PANDA or OTTER.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback candidate: **PUMA**, if you have a miRNA list. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result. PUMA extends PANDA's message passing to miRNA regulators.

Captured request parameters:

- `ppi_file`: 4

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

**What your data allows.** Your request names only a motif prior and a PPI network. PUMA also needs a miRNA list. With a motif prior and a PPI network alone, PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER, GIRAFFE or BONOBO builds a network instead. Do you also have a miRNA list?

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA is the closest registered match, but it is not a verified match for your request.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- point: Your request names only a motif prior and a PPI network; the matched workflows need more inputs, while PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER, GIRAFFE or BONOBO works from it alone.
- question: Do you also have a miRNA list?
- option: Only a motif prior and a PPI network — Leads to PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER, GIRAFFE or BONOBO · A network
- option: I also have a miRNA list — Leads to PUMA
- next step: Start a new task

## S040

Request (turn 1): We want a TF-gene network from expression, motifs and PPI at 9 time points.
Request (turn 2): It has to capture how regulation at one time point drives the next one.

Requirements to judge (in the user's words):
R1: "It has to capture how regulation at one time point drives the next one"

Reply:

````
What I understood you are asking for:
1. "TF-gene network from expression, motifs and PPI at 9 time points" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene network from expression, motifs and PPI at 9 time points” — Not matched to any registered workflow.
- next step: Start a new task

## S041

Request (turn 1): We have expression and methylation from the same 85 tumors. We want a partial-correlation network linking them.

Requirements to judge (in the user's words):
R1: "a partial-correlation network linking them"

Reply:

````
What I understood you are asking for:
1. "We want a partial-correlation network linking them." -- available from DRAGON.

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

## S042

Request (turn 1): We want a network linking expression and metabolites in 90 samples.
Request (turn 2): Both layers come from the same 90 samples.

Requirements to judge (in the user's words):
R1: "Both layers come from the same 90 samples"

Reply:

````
What I understood you are asking for:
1. "We want a network linking expression and metabolites in 90 samples." -- available from DRAGON.

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

## S043

Request (turn 1): We want per-sample co-expression networks for 120 spots.
Request (turn 2): The spots are on a tissue slide, and each network should use the neighbouring spots.

Requirements to judge (in the user's words):
R1: "each network should use the neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "per-sample co-expression networks for 120 spots" -- available from LIONESS-COEXPRESSION or BONOBO.

Based on what you said — "The spots are on a tissue slide, and each network should use the neighbouring spots." — **BONOBO** fits better: a confidence value (p-value) is needed for each connection in each sample.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale.

**BONOBO** (recommend) — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable. Needs expression matrix. Produces inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result (one result per sample).

Other compatible option(s):
- **LIONESS-COEXPRESSION** — preferred when: dozens of samples or more; no sample covariates need to be separated or adjusted; approach: derive each sample network from all-sample and leave-one-out networks.

Should I use BONOBO, or does another listed option fit your study better?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Recommended: BONOBO, from what you said.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: BONOBO — Fits what you said: you need a p-value for each edge · One gene co-expression network per sample, with a p-value for each connection [Recommended]
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more
- next step: Start a new task

## S044

Request (turn 1): We have proteomics for 50 patients and RNA-seq for a different set of 60 patients. We want a partial-correlation network linking proteins and transcripts.

Requirements to judge (in the user's words):
R1: "a partial-correlation network linking proteins and transcripts"

Reply:

````
What I understood you are asking for:
1. "a partial-correlation network linking proteins and transcripts" -- available from DRAGON.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- next step: Plan DRAGON with my data
- next step: Start a new task

## S045

Request (turn 1): We have expression at 8 time points, with motifs and PPI. The model must describe how each time point's regulation leads to the next. We want a TF-gene network.

Requirements to judge (in the user's words):
R1: "We want a TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a TF-gene network.” — Not matched to any registered workflow.
- next step: Start a new task

## S046

Request (turn 1): We have expression, motifs and PPI for 64 profiles. Each profile is one cell from a Smart-seq3 plate. We want a TF-gene network for each profile.

Requirements to judge (in the user's words):
R1: "We want a TF-gene network for each profile"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network for each profile." -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a TF-gene network for each profile.” — OTTER does not give it: no per-sample OTTER is registered.
- next step: Start a new task

## S047

Request (turn 1): We want patient subtypes from somatic mutations of 140 tumors.
Request (turn 2): A patient should be able to belong to two subtypes.

Requirements to judge (in the user's words):
R1: "A patient should be able to belong to two subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from somatic mutations" -- available from SAMBAR.

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

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level set of sample subtypes.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S048

Request (turn 1): We have lncRNA, miRNA and mRNA expression for 90 samples. We want the lncRNAs that sponge miRNAs.

Requirements to judge (in the user's words):
R1: "the lncRNAs that sponge miRNAs"

Reply:

````
What I understood you are asking for:
1. "the lncRNAs that sponge miRNAs" -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “the lncRNAs that sponge miRNAs” — PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.
- next step: Start a new task

## S049

Request (turn 1): We have a bipartite TF-gene network. Each TF may belong to several modules at once. We want its modules.

Requirements to judge (in the user's words):
R1: "We want its modules"

Reply:

````
What I understood you are asking for:
1. "We want its modules." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want its modules.” — Not matched to any registered workflow.
- next step: Start a new task

## S050

Request (turn 1): We want patient subtypes from somatic mutations of 140 tumors.
Request (turn 2): A patient should be able to belong to two subtypes.

Requirements to judge (in the user's words):
R1: "A patient should be able to belong to two subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from somatic mutations" -- available from SAMBAR.

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

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level set of sample subtypes.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

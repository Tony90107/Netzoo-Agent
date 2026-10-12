## S051

Request (turn 1): We have proteomics for 50 patients and RNA-seq for a different set of 60 patients. We want a partial-correlation network linking proteins and transcripts.

Requirements to judge (in the user's words):
R1: "a partial-correlation network linking proteins and transcripts"

Reply:

````
What I understood you are asking for:
1. "We want a partial-correlation network linking proteins and transcripts." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a partial-correlation network linking proteins and transcripts.” — Not matched to any registered workflow.
- next step: Start a new task

## S052

Request (turn 1): We have expression for 300 patients. We want a model that predicts each patient's survival.

Requirements to judge (in the user's words):
R1: "a model that predicts each patient's survival"

Reply:

````
What I understood you are asking for:
1. "a model that predicts each patient's survival" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a model that predicts each patient's survival” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- next step: Start a new task

## S053

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

## S054

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

## S055

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

## S056

Request (turn 1): We have a bipartite TF-gene network. Each gene should belong to exactly one module. We want its modules.

Requirements to judge (in the user's words):
R1: "We want its modules"

Reply:

````
What I understood you are asking for:
1. "We want its modules." -- available from CONDOR.

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

## S057

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

## S058

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

## S059

Request (turn 1): We have single-cell data that we aggregated into pseudo-bulk profiles for 30 samples. We want one co-expression network per sample.

Requirements to judge (in the user's words):
R1: "one co-expression network per sample"

Reply:

````
What I understood you are asking for:
1. "one co-expression network per sample" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "30 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Not on single cells: run it on pseudo-bulk profiles, one per donor and state · Pick it if you have dozens of samples or more
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Not on single cells: run it on pseudo-bulk profiles, one per donor and state
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S060

Request (turn 1): We have expression, motifs and PPI for 64 profiles. Each profile is one cell from a Smart-seq3 plate. We want a TF-gene network for each profile.

Requirements to judge (in the user's words):
R1: "We want a TF-gene network for each profile"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network for each profile." -- the backup check matched no registered workflow to this (not confirmed).
The usual capability check could not run this turn, so a backup model read the request; the lines above are not confirmed, and the methods below were not removed for them.

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
- not available: “We want a TF-gene network for each profile.” — The backup check matched no registered workflow to this (not confirmed).
- next step: Start a new task

## S061

Request (turn 1): Proteomics and RNA-seq were measured on the same 70 patients. We want each patient's two-layer network.

Requirements to judge (in the user's words):
R1: "each patient's two-layer network"

Reply:

````
What I understood you are asking for:
1. "each patient's two-layer network" -- available from LIONESS-DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Selected path: **LIONESS-DRAGON**.

Your question asks for a multi-omic network. **LIONESS-DRAGON** fits that result.

**LIONESS-DRAGON** — Infer one sample-specific two-layer multi-omic partial-correlation network per sample with LIONESS-DRAGON. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

Required workflow inputs:

- `omics_layer_1`: DRAGON omics layer 1
- `omics_layer_2`: DRAGON omics layer 2

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `multi_omic_network`: Inferred associations between omics features.

Workflow-specific scientific notes:

- LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample.
- Each sample's network is an undirected partial-correlation graph across both layers; like DRAGON's, it is an association graph, not a causal one.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-DRAGON fits your goal: multi-omic network.
- point: Method: One two-layer partial-correlation network per sample, derived leave-one-out.
- point: Needs: omics layer 1, omics layer 2.
- point: Cost: N samples take N+1 DRAGON runs (for your 70 patients, 71 DRAGON runs).
- point: Produces: multi-omic network (one per sample).
- next step: Plan LIONESS-DRAGON with my data
- next step: Start a new task

## S062

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

## S063

Request (turn 1): We have expression, motifs and PPI for 110 samples. We want one TF-gene network.

Requirements to judge (in the user's words):
R1: "We want one TF-gene network"

Reply:

````
What I understood you are asking for:
1. "We want one TF-gene network." -- available from PANDA or OTTER.

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

## S064

Request (turn 1): We have single-cell data that we aggregated into pseudo-bulk profiles for 30 samples. We want one co-expression network per sample.

Requirements to judge (in the user's words):
R1: "one co-expression network per sample"

Reply:

````
What I understood you are asking for:
1. "one co-expression network per sample" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "30 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Not on single cells: run it on pseudo-bulk profiles, one per donor and state · Pick it if you have dozens of samples or more
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Not on single cells: run it on pseudo-bulk profiles, one per donor and state
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S065

Request (turn 1): We have expression for 3,000 profiles. All of them are single nuclei from one brain. We want a co-expression network per profile.

Requirements to judge (in the user's words):
R1: "We want a co-expression network per profile"

Reply:

````
What I understood you are asking for:
1. "We want a co-expression network per profile." -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a co-expression network per profile.” — LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S066

Request (turn 1): We have expression for 3,000 profiles. All of them are single nuclei from one brain. We want a co-expression network per profile.

Requirements to judge (in the user's words):
R1: "We want a co-expression network per profile"

Reply:

````
What I understood you are asking for:
1. "We want a co-expression network per profile." -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a co-expression network per profile.” — LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S067

Request (turn 1): We have expression for 3,000 profiles. All of them are single nuclei from one brain. We want a co-expression network per profile.

Requirements to judge (in the user's words):
R1: "We want a co-expression network per profile"

Reply:

````
What I understood you are asking for:
1. "a co-expression network per profile" -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a co-expression network per profile” — LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S068

Request (turn 1): We want a TF-gene network from expression, motifs and PPI at 9 time points.
Request (turn 2): It has to capture how regulation at one time point drives the next one.

Requirements to judge (in the user's words):
R1: "It has to capture how regulation at one time point drives the next one"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network from expression, motifs and PPI at 9 time points." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a TF-gene network from expression, motifs and PPI at 9 time points.” — Not matched to any registered workflow.
- next step: Start a new task

## S069

Request (turn 1): We have single-cell data that we aggregated into pseudo-bulk profiles for 30 samples. We want one co-expression network per sample.

Requirements to judge (in the user's words):
R1: "one co-expression network per sample"

Reply:

````
What I understood you are asking for:
1. "one co-expression network per sample" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "30 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Not on single cells: run it on pseudo-bulk profiles, one per donor and state · Pick it if you have dozens of samples or more
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Not on single cells: run it on pseudo-bulk profiles, one per donor and state
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S070

Request (turn 1): We want a TF-gene network for each of our 70 samples, from expression, motifs and PPI.
Request (turn 2): Those 70 samples are single cells from one patient.

Requirements to judge (in the user's words):
R1: "Those 70 samples are single cells from one patient"

Reply:

````
What I understood you are asking for:
1. "TF-gene network for each of our 70 samples" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 70 samples, 71 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 70 samples, 71 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S071

Request (turn 1): We want patient subtypes from somatic mutations of 140 tumors.
Request (turn 2): A patient should be able to belong to two subtypes.

Requirements to judge (in the user's words):
R1: "A patient should be able to belong to two subtypes"

Reply:

````
What I understood you are asking for:
1. "patient subtypes" -- available from SAMBAR.

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

## S072

Request (turn 1): We have 10x data from 25 donors, already summed into one pseudo-bulk profile per donor. We want a TF-gene network for each donor, with motifs and PPI.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each donor"

Reply:

````
What I understood you are asking for:
1. "a TF-gene network for each donor, with motifs and PPI" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 25 donors, 26 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 25 donors, 26 PANDA runs).
- point: Not mentioned in your request: expression matrix.
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S073

Request (turn 1): We want per-sample co-expression networks for 120 spots.
Request (turn 2): The spots are on a tissue slide, and each network should use the neighbouring spots.

Requirements to judge (in the user's words):
R1: "each network should use the neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "per-sample co-expression networks" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “per-sample co-expression networks” — Not matched to any registered workflow.
- next step: Start a new task

## S074

Request (turn 1): We have expression for 300 patients. We want a model that predicts each patient's survival.

Requirements to judge (in the user's words):
R1: "a model that predicts each patient's survival"

Reply:

````
What I understood you are asking for:
1. "a model that predicts each patient's survival" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a model that predicts each patient's survival” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- next step: Start a new task

## S075

Request (turn 1): We have expression for 3,000 profiles. All of them are single nuclei from one brain. We want a co-expression network per profile.

Requirements to judge (in the user's words):
R1: "We want a co-expression network per profile"

Reply:

````
What I understood you are asking for:
1. "We want a co-expression network per profile." -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a co-expression network per profile.” — LIONESS-COEXPRESSION does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

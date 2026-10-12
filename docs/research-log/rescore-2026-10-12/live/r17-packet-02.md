## S026

Request (turn 1): We want a network linking expression and methylation for 64 samples.
Request (turn 2): Each link also needs a multiple-testing adjusted p-value.

Requirements to judge (in the user's words):
R1: "Each link also needs a multiple-testing adjusted p-value"

Reply:

````
What I understood you are asking for:
1. "We want a network linking expression and methylation for 64 samples." -- available from DRAGON.
2. "Each link also needs a multiple-testing adjusted p-value." -- available from DRAGON.

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

Request (turn 1): We want one TF-gene network for 90 samples from expression, motifs and PPI, with its edges ranked by evolutionary conservation across 30 species.

Requirements to judge (in the user's words):
R1: "one TF-gene network"
R2: "its edges ranked by evolutionary conservation across 30 species"

Reply:

````
What I understood you are asking for:
1. "one TF-gene network for 90 samples from expression, motifs and PPI, with its edges ranked by evolutionary conservation across 30 species" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “one TF-gene network for 90 samples from expression, motifs and PPI, with its… — Not matched to any registered workflow.
- next step: Start a new task

## S028

Request (turn 1): We have a human TF-gene network. We want it aligned to the mouse network through orthologous genes.

Requirements to judge (in the user's words):
R1: "it aligned to the mouse network through orthologous genes"

Reply:

````
What I understood you are asking for:
1. "We want it aligned to the mouse network through orthologous genes." -- the check matched no registered workflow to this, but the second check that confirms such a gap could not run (not confirmed).
The second check that confirms a gap could not run this turn, so the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- not available: “We want it aligned to the mouse network through orthologous genes.” — The check matched no registered workflow to this, but the second check that confirms such a gap could not run (not confirmed).
- next step: Start a new task

## S029

Request (turn 1): We have DNA methylation profiles for 200 tumors and no mutation data. We want patient subtypes from the methylation.

Requirements to judge (in the user's words):
R1: "patient subtypes from the methylation"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from the methylation" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “patient subtypes from the methylation” — SAMBAR does not give it: SAMBAR's input is somatic mutations.
- next step: Start a new task

## S030

Request (turn 1): We have expression and copy number for 150 tumors. We want an expression matrix corrected for copy-number dosage.

Requirements to judge (in the user's words):
R1: "an expression matrix corrected for copy-number dosage"

Reply:

````
What I understood you are asking for:
1. "We want an expression matrix corrected for copy-number dosage." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want an expression matrix corrected for copy-number dosage.” — Not matched to any registered workflow.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S031

Request (turn 1): We want the communities of our bipartite TF-gene network.
Request (turn 2): Regulators must be able to belong to more than one community.

Requirements to judge (in the user's words):
R1: "Regulators must be able to belong to more than one community"

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

## S032

Request (turn 1): We have raw mass-spectrometry spectra from 30 runs. We want peptides identified from them.

Requirements to judge (in the user's words):
R1: "peptides identified from them"

Reply:

````
What I understood you are asking for:
1. "peptides identified from them" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “peptides identified from them” — Not matched to any registered workflow.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S033

Request (turn 1): We have expression, motifs and PPI for 90 samples. We want each TF's binding affinity to its targets in nanomolar.

Requirements to judge (in the user's words):
R1: "each TF's binding affinity to its targets in nanomolar"

Reply:

````
What I understood you are asking for:
1. "each TF's binding affinity to its targets in nanomolar" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “each TF's binding affinity to its targets in nanomolar” — Not matched to any registered workflow.
- next step: Start a new task

## S034

Request (turn 1): We want a partial-correlation network between expression and metabolites in 75 samples.
Request (turn 2): The two layers were not measured on the same samples.

Requirements to judge (in the user's words):
R1: "The two layers were not measured on the same samples"

Reply:

````
What I understood you are asking for:
1. "We want a partial-correlation network between expression and metabolites in 75 samples." -- available from DRAGON.

I can map this to more than one compatible network result:

- **DRAGON** — DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Per-sample version: **LIONESS-DRAGON**. Needs DRAGON omics layer 1 and DRAGON omics layer 2.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a multi-omic network.
- question: Should the result be aggregate or sample-specific?
- option: One cohort-wide network — Leads to DRAGON
- option: One network per sample — Leads to LIONESS-DRAGON · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns DRAGON once per sample
- next step: Start a new task

## S035

Request (turn 1): We want communities in our bipartite TF-gene network and a tree of sub-communities nested inside each.

Requirements to judge (in the user's words):
R1: "communities in our bipartite TF-gene network"
R2: "a tree of sub-communities nested inside each"

Reply:

````
What I understood you are asking for:
1. "communities in our bipartite TF-gene network" -- available from CONDOR.
2. "a tree of sub-communities nested inside each" -- not matched to any registered workflow.

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
- not available: “a tree of sub-communities nested inside each” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S036

Request (turn 1): We want a TF-gene network across our 100 samples from expression, motifs and PPI.
Request (turn 2): We'd rather have one network for every patient.

Requirements to judge (in the user's words):
R1: "one network for every patient"

Reply:

````
What I understood you are asking for:
1. "We'd rather have one network for every patient." -- available from LIONESS-PANDA or LIONESS-PUMA.

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

## S037

Request (turn 1): We have somatic mutation calls for 330 tumors. We want our mutated genes ranked by how likely they are to be cancer drivers.

Requirements to judge (in the user's words):
R1: "our mutated genes ranked by how likely they are to be cancer drivers"

Reply:

````
What I understood you are asking for:
1. "our mutated genes ranked by how likely they are to be cancer drivers" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “our mutated genes ranked by how likely they are to be cancer drivers” — SAMBAR does not give it: SAMBAR summarizes given mutation calls; it does not call or rank driver mutations.
- next step: Start a new task

## S038

Request (turn 1): We have expression at 6 time points after infection, with motifs and PPI. We want the lagged regulatory effect of each TF from one time point on its targets at the next.

Requirements to judge (in the user's words):
R1: "the lagged regulatory effect of each TF from one time point on its targets at the next"

Reply:

````
What I understood you are asking for:
1. "the lagged regulatory effect of each TF from one time point on its targets at the next" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “the lagged regulatory effect of each TF from one time point on its targets at… — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- next step: Start a new task

## S039

Request (turn 1): We have a TF-gene network. We want a soft clustering in which each TF gets a membership weight in every module.

Requirements to judge (in the user's words):
R1: "a soft clustering in which each TF gets a membership weight in every module"

Reply:

````
What I understood you are asking for:
1. "We want a soft clustering in which each TF gets a membership weight in every module." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a soft clustering in which each TF gets a membership weight in every… — Not matched to any registered workflow.
- next step: Start a new task

## S040

Request (turn 1): We have FASTQ files from 24 RNA-seq libraries. We want the reads aligned to the human genome.

Requirements to judge (in the user's words):
R1: "the reads aligned to the human genome"

Reply:

````
What I understood you are asking for:
1. "We want the reads aligned to the human genome." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want the reads aligned to the human genome.” — Not matched to any registered workflow.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S041

Request (turn 1): We have RNA-seq of 75 lung adenocarcinomas plus a motif prior and a PPI network. We want a cohort-wide TF-to-gene network.

Requirements to judge (in the user's words):
R1: "a cohort-wide TF-to-gene network"

Reply:

````
What I understood you are asking for:
1. "a cohort-wide TF-to-gene network" -- available from PANDA or OTTER.

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
- point: Understood goal: a cohort-level TF-gene regulatory network from expression data, a motif prior and a PPI network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S042

Request (turn 1): We have Drop-seq data for 2,400 cells with motifs and PPI. We want a separate TF-gene network for every cell.

Requirements to judge (in the user's words):
R1: "a separate TF-gene network for every cell"

Reply:

````
What I understood you are asking for:
1. "a separate TF-gene network for every cell" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a separate TF-gene network for every cell” — LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- next step: Start a new task

## S043

Request (turn 1): We have raw mass-spectrometry spectra from 30 runs. We want peptides identified from them.

Requirements to judge (in the user's words):
R1: "peptides identified from them"

Reply:

````
What I understood you are asking for:
1. "We want peptides identified from them." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want peptides identified from them.” — Not matched to any registered workflow.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S044

Request (turn 1): We have a thresholded TF-gene network from PANDA. We want its communities by bipartite modularity.

Requirements to judge (in the user's words):
R1: "its communities by bipartite modularity"

Reply:

````
What I understood you are asking for:
1. "We want its communities by bipartite modularity." -- available from CONDOR.

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

## S045

Request (turn 1): We have expression, motifs and PPI for 70 patients. We want to know whether TF activity changes cause the target gene changes or the other way round.

Requirements to judge (in the user's words):
R1: "whether TF activity changes cause the target gene changes or the other way round"

Reply:

````
What I understood you are asking for:
1. "whether TF activity changes cause the target gene changes or the other way round." -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “whether TF activity changes cause the target gene changes or the other way… — Every registered workflow estimates associations or model coefficients from observational data.
- next step: Start a new task

## S046

Request (turn 1): We want the communities of our bipartite TF-gene network and the GO terms enriched in each.

Requirements to judge (in the user's words):
R1: "the communities of our bipartite TF-gene network and the GO terms enriched in each"

Reply:

````
What I understood you are asking for:
1. "communities of our bipartite TF-gene network" -- available from CONDOR.
2. "GO terms enriched in each" -- available from CONDOR's output plus a step you run outside NetZoo: A gene-set tool outside NetZoo.

Selected path: **CONDOR**.

Your question asks for a community assignment. **CONDOR** fits that result.

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
- headline: CONDOR fits your goal: set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- next step: Plan CONDOR with my data
- next step: Start a new task

## S047

Request (turn 1): We have expression, motifs and PPI for 85 samples. We want lncRNAs included as regulators alongside the TFs.

Requirements to judge (in the user's words):
R1: "lncRNAs included as regulators alongside the TFs"

Reply:

````
What I understood you are asking for:
1. "We want lncRNAs included as regulators alongside the TFs." -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want lncRNAs included as regulators alongside the TFs.” — PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.
- next step: Start a new task

## S048

Request (turn 1): We have matched lipidomics and transcriptomics for 130 subjects. We want conditional associations between lipids and genes, with an adjusted p-value for each.

Requirements to judge (in the user's words):
R1: "conditional associations between lipids and genes, with an adjusted p-value for each"

Reply:

````
What I understood you are asking for:
1. "conditional associations between lipids and genes, with an adjusted p-value for each" -- available from DRAGON.

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

## S049

Request (turn 1): We have expression for 120 samples. We want the sequence motifs enriched in the promoters of our co-expressed genes.

Requirements to judge (in the user's words):
R1: "the sequence motifs enriched in the promoters of our co-expressed genes"

Reply:

````
What I understood you are asking for:
1. "the sequence motifs enriched in the promoters of our co-expressed genes" -- not available here: no registered workflow produces this. PANDA does not give it: the motif prior is an input; PANDA never searches sequence.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “the sequence motifs enriched in the promoters of our co-expressed genes” — PANDA does not give it: the motif prior is an input; PANDA never searches sequence.
- next step: Start a new task

## S050

Request (turn 1): We want a partial-correlation network between expression and metabolites in 75 samples.
Request (turn 2): The two layers were not measured on the same samples.

Requirements to judge (in the user's words):
R1: "The two layers were not measured on the same samples"

Reply:

````
What I understood you are asking for:
1. "a partial-correlation network between expression and metabolites" -- available from DRAGON.

I can map this to more than one compatible network result:

- **DRAGON** — DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Per-sample version: **LIONESS-DRAGON**. Needs DRAGON omics layer 1 and DRAGON omics layer 2.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a multi-omic network.
- question: Should the result be aggregate or sample-specific?
- option: One cohort-wide network — Leads to DRAGON
- option: One network per sample — Leads to LIONESS-DRAGON · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns DRAGON once per sample
- next step: Start a new task

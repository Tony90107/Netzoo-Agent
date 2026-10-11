## S076

Request (turn 1): We have methylation and expression for 72 tumors. Is there a method that gives each tumor its own methylation-expression network?

Requirements to judge (in the user's words):
R1: "gives each tumor its own methylation-expression network"

Reply:

````
What I understood you are asking for:
1. "each tumor its own methylation-expression network" -- available from LIONESS-DRAGON.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-DRAGON fits your goal: multi-omic network.
- point: Method: One two-layer partial-correlation network per sample, derived leave-one-out.
- point: Needs: omics layer 1, omics layer 2.
- point: Cost: N samples take N+1 DRAGON runs (for your 72 tumors, 73 DRAGON runs).
- point: Produces: multi-omic network (one per sample).
- next step: Plan LIONESS-DRAGON with my data
- next step: Start a new task

## S077

Request (turn 1): We have expression, motifs and PPI from 88 samples. We want each TF's activity in every sample, estimated apart from the TF's own mRNA level.

Requirements to judge (in the user's words):
R1: "each TF's activity in every sample, estimated apart from the TF's own mRNA level"

Reply:

````
What I understood you are asking for:
1. "each TF's activity in every sample, estimated apart from the TF's own mRNA level." -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "estimated apart from the TF's own mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S078

Request (turn 1): We have expression, motifs, PPI and survival data for 180 patients. We want per-patient TF targeting scores tested against survival.

Requirements to judge (in the user's words):
R1: "per-patient TF targeting scores tested against survival"

Reply:

````
What I understood you are asking for:
1. "per-patient TF targeting scores tested against survival" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "We want per-patient TF targeting scores tested against survival." — The activity matrix holds one value per TF per sample (TF by sample, written as the `.tfa` output). GIRAFFE reports absolute activity, so every value is zero or positive.

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
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S079

Request (turn 1): We have a TF-gene network. We want the shortest regulatory path from TP53 to MYC and how significant it is.

Requirements to judge (in the user's words):
R1: "the shortest regulatory path from TP53 to MYC and how significant it is"

Reply:

````
What I understood you are asking for:
1. "shortest regulatory path from TP53 to MYC" -- not matched to any registered workflow.
2. "how significant it is" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- point: Understood: "shortest regulatory path from TP53 to MYC"
- point: Understood: "how significant it is"
- not available: “shortest regulatory path from TP53 to MYC” — Not matched to any registered workflow.
- not available: “how significant it is” — Not matched to any registered workflow.
- next step: Start a new task

## S080

Request (turn 1): We have proteomics and phosphoproteomics for 75 matched samples. We want a two-layer network of direct associations between them.

Requirements to judge (in the user's words):
R1: "a two-layer network of direct associations between them"

Reply:

````
What I understood you are asking for:
1. "a two-layer network of direct associations between them" -- available from DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- The proteomics and phosphoproteomics data are compatible for network construction.

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

## S081

Request (turn 1): We have a TF-gene network. We want gene modules in which one gene can belong to several modules at once.

Requirements to judge (in the user's words):
R1: "gene modules in which one gene can belong to several modules at once"

Reply:

````
What I understood you are asking for:
1. "We want gene modules in which one gene can belong to several modules at once." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want gene modules in which one gene can belong to several modules at once.” — Not matched to any registered workflow.
- next step: Start a new task

## S082

Request (turn 1): We want one gene co-expression network across our 120 samples.
Request (turn 2): Actually we need one for each sample.

Requirements to judge (in the user's words):
R1: "one for each sample"

Reply:

````
What I understood you are asking for:
1. "one for each sample" -- available from LIONESS-PANDA or LIONESS-PUMA.

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

## S083

Request (turn 1): We have a regulator-gene network from PANDA. We want its modules and the core regulators of each module.

Requirements to judge (in the user's words):
R1: "its modules and the core regulators of each module"

Reply:

````
What I understood you are asking for:
1. "its modules" -- available from CONDOR.
2. "the core regulators of each module" -- available from CONDOR.

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

## S084

Request (turn 1): We have RNA-seq for 60 samples but proteomics for only 40 of them. We want the missing proteomics values imputed from the RNA-seq.

Requirements to judge (in the user's words):
R1: "the missing proteomics values imputed from the RNA-seq"

Reply:

````
What I understood you are asking for:
1. "We want the missing proteomics values imputed from the RNA-seq." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want the missing proteomics values imputed from the RNA-seq.” — Not matched to any registered workflow.
- next step: Start a new task

## S085

Request (turn 1): We have bulk RNA-seq of 90 samples. We want a separate regulatory network for each of the 8 cell types deconvolved from the bulk.

Requirements to judge (in the user's words):
R1: "a separate regulatory network for each of the 8 cell types deconvolved from the bulk"

Reply:

````
What I understood you are asking for:
1. "We want a separate regulatory network for each of the 8 cell types deconvolved from the bulk." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a separate regulatory network for each of the 8 cell types… — Not matched to any registered workflow.
- next step: Start a new task

## S086

Request (turn 1): We have expression from 100 samples. We want a simulation of every gene's expression after knocking out STAT3.

Requirements to judge (in the user's words):
R1: "a simulation of every gene's expression after knocking out STAT3"

Reply:

````
What I understood you are asking for:
1. "We want a simulation of every gene's expression after knocking out STAT3." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a simulation of every gene's expression after knocking out STAT3.” — Not matched to any registered workflow.
- next step: Start a new task

## S087

Request (turn 1): We have matched miRNA and mRNA expression for 80 samples. We want miRNA-gene edges estimated from the anti-correlation of their expression.

Requirements to judge (in the user's words):
R1: "miRNA-gene edges estimated from the anti-correlation of their expression"

Reply:

````
What I understood you are asking for:
1. "miRNA-gene edges estimated from the anti-correlation of their expression" -- not available here: no registered workflow produces this. PUMA does not give it: the miRNA's own expression is not an input.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “miRNA-gene edges estimated from the anti-correlation of their expression” — PUMA does not give it: the miRNA's own expression is not an input.
- next step: Start a new task

## S088

Request (turn 1): We have expression from 80 samples. We want a directed acyclic graph of which genes regulate which other genes.

Requirements to judge (in the user's words):
R1: "a directed acyclic graph of which genes regulate which other genes"

Reply:

````
What I understood you are asking for:
1. "a directed acyclic graph of which genes regulate which other genes" -- not available here: no registered workflow produces this. LIONESS-COEXPRESSION does not give it: co-expression is undirected gene-gene similarity, with no regulator layer.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a directed acyclic graph of which genes regulate which other genes” — LIONESS-COEXPRESSION does not give it: co-expression is undirected gene-gene similarity, with no regulator layer.
- next step: Start a new task

## S089

Request (turn 1): We have proteomics and RNA-seq from 120 matched plasma samples. We want a partial-correlation network between proteins and transcripts, keeping only edges with adjusted p below 0.05.

Requirements to judge (in the user's words):
R1: "a partial-correlation network between proteins and transcripts, keeping only edges with adjusted p below 0.05"

Reply:

````
What I understood you are asking for:
1. "We want a partial-correlation network between proteins and transcripts, keeping only edges with adjusted p below 0.05." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a partial-correlation network between proteins and transcripts… — Not matched to any registered workflow.
- next step: Start a new task

## S090

Request (turn 1): We have Smart-seq2 profiles of 600 single cells, with motifs and PPI. We want a TF-gene network for each cell.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each cell"

Reply:

````
What I understood you are asking for:
1. "TF-gene network for each cell" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene network for each cell” — LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S091

Request (turn 1): We want CRISPR guide RNAs designed to knock out the 20 hub TFs of our network.

Requirements to judge (in the user's words):
R1: "CRISPR guide RNAs designed to knock out the 20 hub TFs"

Reply:

````
What I understood you are asking for:
1. "CRISPR guide RNAs designed to knock out the 20 hub TFs" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “CRISPR guide RNAs designed to knock out the 20 hub TFs” — Not matched to any registered workflow.
- next step: Start a new task

## S092

Request (turn 1): We have expression, motifs, PPI and drug response labels for 200 patients. We want a trained model that predicts each new patient's response, with its accuracy.

Requirements to judge (in the user's words):
R1: "a trained model that predicts each new patient's response, with its accuracy"

Reply:

````
What I understood you are asking for:
1. "a trained model that predicts each new patient's response, with its accuracy" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a trained model that predicts each new patient's response, with its accuracy” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- next step: Start a new task

## S093

Request (turn 1): We have a regulator-gene network from PANDA. We want its modules and the core regulators of each module.

Requirements to judge (in the user's words):
R1: "its modules and the core regulators of each module"

Reply:

````
What I understood you are asking for:
1. "its modules" -- available from CONDOR.
2. "the core regulators of each module" -- available from CONDOR.

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

## S094

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

## S095

Request (turn 1): We have RNA-seq for 60 samples but proteomics for only 40 of them. We want the missing proteomics values imputed from the RNA-seq.

Requirements to judge (in the user's words):
R1: "the missing proteomics values imputed from the RNA-seq"

Reply:

````
What I understood you are asking for:
1. "We want the missing proteomics values imputed from the RNA-seq." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want the missing proteomics values imputed from the RNA-seq.” — Not matched to any registered workflow.
- next step: Start a new task

## S096

Request (turn 1): We have microbiome abundances and metabolomics from 100 stool samples. Which method gives conditional associations between taxa and metabolites?

Requirements to judge (in the user's words):
R1: "conditional associations between taxa and metabolites"

Reply:

````
What I understood you are asking for:
1. "conditional associations between taxa and metabolites" -- available from DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- The analysis aims to explore relationships between microbiome taxa and metabolites in a joint framework.

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

## S097

Request (turn 1): We have bulk RNA-seq of 90 samples. We want a separate regulatory network for each of the 8 cell types deconvolved from the bulk.

Requirements to judge (in the user's words):
R1: "a separate regulatory network for each of the 8 cell types deconvolved from the bulk"

Reply:

````
What I understood you are asking for:
1. "a separate regulatory network for each of the 8 cell types deconvolved from the bulk" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a separate regulatory network for each of the 8 cell types deconvolved from… — Not matched to any registered workflow.
- next step: Start a new task

## S098

Request (turn 1): We have Smart-seq2 profiles of 600 single cells, with motifs and PPI. We want a TF-gene network for each cell.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each cell"

Reply:

````
What I understood you are asking for:
1. "a TF-gene network for each cell" -- not available here: no registered workflow produces this. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a TF-gene network for each cell” — LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S099

Request (turn 1): We have RNA-seq of 300 tumors and no mutation data. We want patient subtypes from the expression profiles.

Requirements to judge (in the user's words):
R1: "patient subtypes from the expression profiles"

Reply:

````
What I understood you are asking for:
1. "patient subtypes from the expression profiles" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “patient subtypes from the expression profiles” — SAMBAR does not give it: SAMBAR's input is somatic mutations.
- next step: Start a new task

## S100

Request (turn 1): We have expression, motifs and PPI from 100 samples. We want the TF-gene network and also the refined TF-TF cooperation network the method estimates along the way.

Requirements to judge (in the user's words):
R1: "the TF-gene network"
R2: "the refined TF-TF cooperation network the method estimates along the way"

Reply:

````
What I understood you are asking for:
1. "TF-gene network" -- available from PANDA.
2. "refined TF-TF cooperation network the method estimates along the way" -- not matched to any registered workflow.

Assumptions behind this recommendation (not confirmed facts):

- The expression, motifs, and PPI data are sufficient to infer the requested networks.

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

Card shown with the reply:
- headline: GIRAFFE fits your goal: cohort-level regulatory network with TF activities.
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- not available: “refined TF-TF cooperation network the method estimates along the way” — Not matched to any registered workflow.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S001

Request (turn 1): We want the communities of our bipartite TF-gene network, and then to fine-map the causal GWAS variants inside each community.

Requirements to judge (in the user's words):
R1: "the communities of our bipartite TF-gene network"
R2: "fine-map the causal GWAS variants inside each community"

Reply:

````
What I understood you are asking for:
1. "the communities of our bipartite TF-gene network" -- available from CONDOR.
2. "to fine-map the causal GWAS variants inside each community" -- not available here: no registered workflow produces this. CONDOR does not give it: CONDOR partitions a given network; it does not test or fine-map variants (its original eQTL use takes eQTL associations as input).

About "to fine-map the causal GWAS variants inside each community.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Assumptions behind this recommendation (not confirmed facts):

- The user has a bipartite TF-gene network available for analysis.

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
- not available: “to fine-map the causal GWAS variants inside each community” — CONDOR does not give it: CONDOR partitions a given network; it does not test or fine-map variants (its original eQTL use takes eQTL associations as input).
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S002

Request (turn 1): We have expression, motifs, PPI and survival data for 180 patients. We want per-patient TF targeting scores tested against survival.

Requirements to judge (in the user's words):
R1: "per-patient TF targeting scores tested against survival"

Reply:

````
What I understood you are asking for:
1. "per-patient TF targeting scores tested against survival" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

Assumptions behind this recommendation (not confirmed facts):

- The analysis will involve correlating TF activity with survival outcomes for each patient.
- Survival data is available and can be correlated with TF targeting scores.

Selected path: **LIONESS-PANDA**.

Your question asks for a cohort-level TF activity matrix. **LIONESS-PANDA** fits that result and scale.

**LIONESS-PANDA** — Infer aggregate PANDA and sample-specific LIONESS-PANDA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA fits your goal: cohort-level TF activity matrix.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 180 patients, 181 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: It also writes the cohort network, so PANDA need not run first.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S003

Request (turn 1): We have ATAC-seq peaks and expression from 40 samples. We want to discover new TF binding motifs de novo.

Requirements to judge (in the user's words):
R1: "discover new TF binding motifs de novo"

Reply:

````
What I understood you are asking for:
1. "discover new TF binding motifs de novo" -- not available here: no registered workflow produces this. PANDA does not give it: the motif prior is an input; PANDA never searches sequence.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “discover new TF binding motifs de novo” — PANDA does not give it: the motif prior is an input; PANDA never searches sequence.
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S004

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

## S005

Request (turn 1): We have expression from 90 treated and 90 control samples. We want differentially expressed genes with fold changes and p-values.

Requirements to judge (in the user's words):
R1: "differentially expressed genes with fold changes and p-values"

Reply:

````
What I understood you are asking for:
1. "differentially expressed genes with fold changes and p-values" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “differentially expressed genes with fold changes and p-values” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Start a new task

## S006

Request (turn 1): We want per-sample TF-gene networks from expression, motifs and PPI of 50 samples.
Request (turn 2): Those samples are 50 spatial spots from one tissue section, and neighbouring spots should share information.

Requirements to judge (in the user's words):
R1: "neighbouring spots should share information"

Reply:

````
Selected path: **SAMBAR**.

Your question asks for a cohort-level sample distance matrix. **SAMBAR** fits that result and scale.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level sample distance matrix.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S007

Request (turn 1): We have a TF-gene network. We want the shortest regulatory path from TP53 to MYC and how significant it is.

Requirements to judge (in the user's words):
R1: "the shortest regulatory path from TP53 to MYC and how significant it is"

Reply:

````
What I understood you are asking for:
1. "the shortest regulatory path from TP53 to MYC" -- not matched to any registered workflow.
2. "how significant it is" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- point: Understood: "the shortest regulatory path from TP53 to MYC"
- point: Understood: "how significant it is"
- not available: “the shortest regulatory path from TP53 to MYC” — Not matched to any registered workflow.
- not available: “how significant it is” — Not matched to any registered workflow.
- next step: Start a new task

## S008

Request (turn 1): We have expression, motifs and PPI for 60 tumor and 60 normal samples. We want to know which TF-gene edges differ between tumor and normal.

Requirements to judge (in the user's words):
R1: "which TF-gene edges differ between tumor and normal"

Reply:

````
What I understood you are asking for:
1. "which TF-gene edges differ between tumor and normal" -- available from PANDA's output plus a step you run outside NetZoo: One run per condition on the same genes and priors, then compare; two aggregate networks give no per-sample spread for a test.

I can map this to more than one compatible network result:

**Gene co-expression network**
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable. Needs expression matrix.

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will compare TF-gene interactions specifically between tumor and normal samples.
- The user has access to the necessary data to perform the analysis.

Which result do you mean: inferred regulator-to-target associations (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE); or p-value matrix paired with a sample-specific gene-gene co-expression result (BONOBO)?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 7 registered workflows fit your request; they differ in scale (one cohort network or one per sample).
- point: Understood goal: a TF-gene regulatory network.
- point: LIONESS-PANDA, BONOBO and LIONESS-PUMA give one network per sample; PANDA, OTTER, GIRAFFE and PUMA give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Produces a co-expression network instead · Pick it if you need a p-value for each edge
- option: PUMA — One TF + miRNA network across all your samples · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list
- option: LIONESS-PUMA — One TF + miRNA network per sample, plus the cohort network · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list
- next step: Start a new task

## S009

Request (turn 1): We have expression from 200 samples processed in 4 batches. We want gene co-expression with the batch-associated part separated out.

Requirements to judge (in the user's words):
R1: "gene co-expression with the batch-associated part separated out"

Reply:

````
What I understood you are asking for:
1. "gene co-expression with the batch-associated part separated out" -- available from COBRA.

Based on what you said — "We want gene co-expression with the batch-associated part separated out." — **COBRA** fits better: co-expression must be separated or adjusted for batch, site or other covariates.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** (recommend) — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern. Needs expression matrix and sample covariate design matrix. Produces inferred gene-to-gene associations (one cohort-level result).

Conditional assumptions to confirm:
- It also needs an expression matrix, which the request does not mention.
- The expression data is in a gene-by-sample matrix format and includes relevant covariate information.

Other compatible option(s):
- **LIONESS-COEXPRESSION** — preferred when: dozens of samples or more; no sample covariates need to be separated or adjusted; approach: derive each sample network from all-sample and leave-one-out networks.

Should I use COBRA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a cohort-level co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level co-expression network.
- point: Recommended: COBRA, from what you said.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: COBRA — Fits what you said: batch, site or covariates must be separated · Co-expression split into the parts your covariates (batch, site, condition) explain and the rest [Recommended]
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if no covariates need adjusting
- next step: Start a new task

## S010

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

## S011

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

## S012

Request (turn 1): We have expression at 10 time points after drug treatment, with motifs and PPI. We want a model that simulates how the regulatory network evolves between time points.

Requirements to judge (in the user's words):
R1: "a model that simulates how the regulatory network evolves between time points"

Reply:

````
What I understood you are asking for:
1. "a model that simulates how the regulatory network evolves between time points" -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a model that simulates how the regulatory network evolves between time points” — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- next step: Start a new task

## S013

Request (turn 1): We have expression from 90 treated and 90 control samples. We want differentially expressed genes with fold changes and p-values.

Requirements to judge (in the user's words):
R1: "differentially expressed genes with fold changes and p-values"

Reply:

````
What I understood you are asking for:
1. "We want differentially expressed genes with fold changes and p-values." -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want differentially expressed genes with fold changes and p-values.” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- next step: Start a new task

## S014

Request (turn 1): We have Visium spatial transcriptomics of 3,000 spots. We want TF-gene networks that borrow information from each spot's neighbouring spots.

Requirements to judge (in the user's words):
R1: "TF-gene networks that borrow information from each spot's neighbouring spots"

Reply:

````
What I understood you are asking for:
1. "TF-gene networks that borrow information from each spot's neighbouring spots" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene networks that borrow information from each spot's neighbouring spots” — Not matched to any registered workflow.
- next step: Start a new task

## S015

Request (turn 1): We have expression, motifs and PPI for 100 samples. We want to know which TFs physically form complexes and in what stoichiometry.

Requirements to judge (in the user's words):
R1: "which TFs physically form complexes and in what stoichiometry"

Reply:

````
What I understood you are asking for:
1. "which TFs physically form complexes" -- not available here: no registered workflow produces this. PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
2. "in what stoichiometry" -- not available here: no registered workflow produces this. PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- point: Understood: "which TFs physically form complexes"
- point: Understood: "in what stoichiometry"
- not available: “which TFs physically form complexes” — PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
- not available: “in what stoichiometry” — PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
- next step: Start a new task

## S016

Request (turn 1): We have expression, methylation and proteomics for 85 matched samples. We want one partial-correlation network that models all three layers jointly.

Requirements to judge (in the user's words):
R1: "one partial-correlation network that models all three layers jointly"

Reply:

````
What I understood you are asking for:
1. "one partial-correlation network that models all three layers jointly" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “one partial-correlation network that models all three layers jointly” — DRAGON does not give it: two layers only.
- next step: Start a new task

## S017

Request (turn 1): We want the communities of our TF-gene network from PANDA.
Request (turn 2): We need its community structure compared against our second network, from the treated group.

Requirements to judge (in the user's words):
R1: "its community structure compared against our second network"

Reply:

````
What I understood you are asking for:
1. "its community structure compared against our second network, from the treated group" -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “its community structure compared against our second network, from the treated… — CONDOR does not give it: one network at a time.
- next step: Start a new task

## S018

Request (turn 1): We have lncRNA, miRNA and mRNA expression for 110 samples. We want a ceRNA network of lncRNAs sponging miRNAs.

Requirements to judge (in the user's words):
R1: "a ceRNA network of lncRNAs sponging miRNAs"

Reply:

````
What I understood you are asking for:
1. "We want a ceRNA network of lncRNAs sponging miRNAs." -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a ceRNA network of lncRNAs sponging miRNAs.” — PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.
- next step: Start a new task

## S019

Request (turn 1): We want a signed TF-gene regulatory matrix from expression, motifs and PPI of 90 samples, and the measured TF protein level in each sample.

Requirements to judge (in the user's words):
R1: "a signed TF-gene regulatory matrix"
R2: "the measured TF protein level in each sample"

Reply:

````
What I understood you are asking for:
1. "signed TF-gene regulatory matrix from expression, motifs and PPI of 90 samples" -- available from GIRAFFE.
2. "measured TF protein level in each sample" -- not available here: no registered workflow produces this. GIRAFFE does not give it: activity is inferred from expression and priors, not measured.

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
- not available: “measured TF protein level in each sample” — GIRAFFE does not give it: activity is inferred from expression and priors, not measured.
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S020

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

## S021

Request (turn 1): We have somatic mutation calls for 310 tumors. We want to group the patients into subtypes using pathway-level mutation scores.

Requirements to judge (in the user's words):
R1: "group the patients into subtypes using pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "group the patients into subtypes using pathway-level mutation scores" -- available from SAMBAR.

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

## S022

Request (turn 1): We have expression and metabolomics for 70 matched samples and want each sample's own two-layer network, with a p-value for every edge in every sample.

Requirements to judge (in the user's words):
R1: "each sample's own two-layer network"
R2: "a p-value for every edge in every sample"

Reply:

````
What I understood you are asking for:
1. "each sample's own two-layer network" -- available from LIONESS-DRAGON.
2. "a p-value for every edge in every sample" -- not available here: no registered workflow produces this. LIONESS-DRAGON does not give it: LIONESS-DRAGON writes per-sample edge weights only; DRAGON's p-values are for the aggregate network.

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
- not available: “a p-value for every edge in every sample” — LIONESS-DRAGON does not give it: LIONESS-DRAGON writes per-sample edge weights only; DRAGON's p-values are for the aggregate network.
- next step: Start a new task

## S023

Request (turn 1): We have expression, methylation and proteomics for 85 matched samples. We want one partial-correlation network that models all three layers jointly.

Requirements to judge (in the user's words):
R1: "one partial-correlation network that models all three layers jointly"

Reply:

````
What I understood you are asking for:
1. "one partial-correlation network that models all three layers jointly" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “one partial-correlation network that models all three layers jointly” — DRAGON does not give it: two layers only.
- next step: Start a new task

## S024

Request (turn 1): We want 3D structures predicted for 12 TF proteins from their amino-acid sequences.

Requirements to judge (in the user's words):
R1: "3D structures predicted for 12 TF proteins"

Reply:

````
What I understood you are asking for:
1. "3D structures predicted for 12 TF proteins from their amino-acid sequences" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “3D structures predicted for 12 TF proteins from their amino-acid sequences” — Not matched to any registered workflow.
- next step: Start a new task

## S025

Request (turn 1): We have expression from 90 samples and want one TF-gene regulatory network for them.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network"

Reply:

````
What I understood you are asking for:
1. "one TF-gene regulatory network" -- available from PANDA, OTTER or LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**What your data allows.** PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network.
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Leads to PANDA, OTTER or GIRAFFE
- next step: Start a new task

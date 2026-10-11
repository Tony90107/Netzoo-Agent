## S211

Request (turn 1): From expression, motifs and PPI of 60 tumors, we want each tumor's TF-gene network, and then a web dashboard where clinicians can browse them interactively.

Requirements to judge (in the user's words):
R1: "each tumor's TF-gene network"
R2: "a web dashboard where clinicians can browse them interactively"

Reply:

````
What I understood you are asking for:
1. "each tumor's TF-gene network" -- available from LIONESS-PANDA.
2. "a web dashboard where clinicians can browse them interactively" -- not matched to any registered workflow.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 60 tumors, 61 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 60 tumors, 61 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- not available: “a web dashboard where clinicians can browse them interactively” — Not matched to any registered workflow.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S212

Request (turn 1): We have expression from 300 patients with drug response labels. We want a model that predicts the response of new patients.

Requirements to judge (in the user's words):
R1: "a model that predicts the response of new patients"

Reply:

````
What I understood you are asking for:
1. "a model that predicts the response of new patients" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a model that predicts the response of new patients” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- next step: Start a new task

## S213

Request (turn 1): We have expression from 140 smokers and non-smokers. We want the co-expression with the smoking effect separated out, and also a differential expression table of smokers versus non-smokers.

Requirements to judge (in the user's words):
R1: "the co-expression with the smoking effect separated out"
R2: "a differential expression table of smokers versus non-smokers"

Reply:

````
What I understood you are asking for:
1. "the co-expression with the smoking effect separated out" -- available from COBRA.
2. "a differential expression table of smokers versus non-smokers" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

For “differential expression table of smokers versus non-smokers”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

For your question ("a differential expression table of smokers versus non-smokers"):
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- point: Your question: whether the groups or time points differ; the reply says what COBRA give toward it and the step after each.
- not available: “a differential expression table of smokers versus non-smokers” — COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.
- not available: “differential expression table of smokers versus non-smokers” — No registered workflow meets this; it needs a clearer measurement or an external method.
- next step: Start a new task

## S214

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. Which method splits it into communities, with each gene in exactly one community, and finds each community's core genes?

Requirements to judge (in the user's words):
R1: "splits it into communities, with each gene in exactly one community"
R2: "finds each community's core genes"

Reply:

````
What I understood you are asking for:
1. "Which method splits it into communities, with each gene in exactly one community, and finds each community's core genes?" -- available from CONDOR.

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

## S215

Request (turn 1): From expression, motifs and PPI of 88 patients with survival follow-up, we want a network for each patient and then a test of which TFs' targeting relates to survival.

Requirements to judge (in the user's words):
R1: "a network for each patient"
R2: "a test of which TFs' targeting relates to survival"

Reply:

````
What I understood you are asking for:
1. "a network for each patient" -- available from LIONESS-PANDA.
2. "a test of which TFs' targeting relates to survival" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: I could not validate an interpretation of this request, so nothing was selected.
- point: This does not mean your question is unclear; restating the result you want usually helps.
- next step: Start a new task

## S216

Request (turn 1): We have expression from 70 colon samples. We want a TF-gene network for each sample.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each sample"

Reply:

````
What I understood you are asking for:
1. "We want a TF-gene network for each sample." -- available from LIONESS-PANDA.

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

**What your data allows.** LIONESS-PANDA and PANDA need a motif prior and a PPI network, which you said you do not have ("We have expression from 70 colon samples.").

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 70 samples, 71 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Needs a motif prior and a PPI network, which you said you do not have.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S217

Request (turn 1): We have ATAC-seq peaks from 30 samples. We want to discover de novo motifs enriched in the peaks.

Requirements to judge (in the user's words):
R1: "discover de novo motifs enriched in the peaks"

Reply:

````
What I understood you are asking for:
1. "discover de novo motifs enriched in the peaks" -- not available here: no registered workflow produces this. PANDA does not give it: the motif prior is an input; PANDA never searches sequence.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “discover de novo motifs enriched in the peaks” — PANDA does not give it: the motif prior is an input; PANDA never searches sequence.
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S218

Request (turn 1): We have RNA-seq from 64 kidney biopsies plus motifs. We want one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene.

Requirements to judge (in the user's words):
R1: "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene"

Reply:

````
What I understood you are asking for:
1. "one regulatory network in which long non-coding RNAs, not TFs, are the regulators of each gene" -- not available here: no registered workflow produces this. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “one regulatory network in which long non-coding RNAs, not TFs, are the… — PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.
- next step: Start a new task

## S219

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. Is there a method that finds overlapping communities, where a gene can belong to several communities at once?

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

Reply:

````
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

## S220

Request (turn 1): Sorry, I meant a separate network for each patient.

Requirements to judge (in the user's words):
R1: "a separate network for each patient"

Reply:

````
What I understood you are asking for:
1. "a separate network for each patient" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** LIONESS-PANDA and PANDA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs.
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S221

Request (turn 1): We have mRNA expression, TF motifs and PPI for 90 samples. Is there a method for one network in which both TFs and miRNAs regulate the genes?

Requirements to judge (in the user's words):
R1: "one network in which both TFs and miRNAs regulate the genes"

Reply:

````
What I understood you are asking for:
1. "one network in which both TFs and miRNAs regulate the genes" -- available from PUMA.

**PUMA** fits the result you describe if you have a miRNA list.

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

**What your data allows.** Your request names only a motif prior and a PPI network. PUMA also needs a miRNA list. With a motif prior and a PPI network alone, PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER or GIRAFFE builds one cohort-level network instead. Do you also have a miRNA list?

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA fits your goal if you have a miRNA list.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- point: Your request names only a motif prior and a PPI network; the matched workflows need more inputs, while PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER or GIRAFFE works from it alone.
- question: Do you also have a miRNA list?
- option: Only a motif prior and a PPI network — Leads to PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER or GIRAFFE · One cohort-level network
- option: I also have a miRNA list — Leads to PUMA
- next step: Plan PUMA with my data
- next step: Start a new task

## S222

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. We want overlapping communities, where a gene can belong to several communities at once.

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

Reply:

````
What I understood you are asking for:
1. "overlapping communities, where a gene can belong to several communities at once." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “overlapping communities, where a gene can belong to several communities at… — Not matched to any registered workflow.
- next step: Start a new task

## S223

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. Is there a method that finds overlapping communities, where a gene can belong to several communities at once?

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

Reply:

````
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

## S224

Request (turn 1): We have ATAC-seq peaks from 30 samples. We want to discover de novo motifs enriched in the peaks.

Requirements to judge (in the user's words):
R1: "discover de novo motifs enriched in the peaks"

Reply:

````
What I understood you are asking for:
1. "discover de novo motifs enriched in the peaks" -- not available here: no registered workflow produces this. PANDA does not give it: the motif prior is an input; PANDA never searches sequence.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “discover de novo motifs enriched in the peaks” — PANDA does not give it: the motif prior is an input; PANDA never searches sequence.
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S225

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. Is there a method that finds overlapping communities, where a gene can belong to several communities at once?

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

Reply:

````
What I understood you are asking for:
1. "Is there a method that finds overlapping communities, where a gene can belong to several communities at once?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Is there a method that finds overlapping communities, where a gene can belong… — Not matched to any registered workflow.
- next step: Start a new task

## S226

Request (turn 1): With expression, motifs and PPI from 72 tumors, we want each TF's activity in each tumor, beyond what its own mRNA level shows.

Requirements to judge (in the user's words):
R1: "each TF's activity in each tumor"

Reply:

````
What I understood you are asking for:
1. "each TF's activity in each tumor, beyond what its own mRNA level shows" -- available from GIRAFFE.

Assumptions behind this recommendation (not confirmed facts):

- The expression data includes mRNA levels for the TFs.
- Motifs and PPI data are relevant for inferring TF activity.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "beyond what its own mRNA level shows" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

## S227

Request (turn 1): Is there a method that finds the communities in our bipartite TF-gene network and then writes a narrative report on their biology automatically?

Requirements to judge (in the user's words):
R1: "finds the communities in our bipartite TF-gene network"
R2: "writes a narrative report on their biology automatically"

Reply:

````
What I understood you are asking for:
1. "finds the communities in our bipartite TF-gene network" -- available from CONDOR.
2. "writes a narrative report on their biology automatically" -- not matched to any registered workflow.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale.

**CONDOR** — Detect communities in a validated bipartite network with CONDOR. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Outputs:

- `community_assignment`: Network-node community memberships, not patient subtype labels.

Ask for the workflow's controls and defaults if you want to set them.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: CONDOR fits your goal: cohort-level set of network communities (modules).
- point: Method: Finds TF-gene communities (modules) in a two-mode network.
- point: Needs: TF-gene (bipartite) network.
- point: Before running: threshold a PANDA or LIONESS network so its edge weights are non-negative; CONDOR then gives each node one community and a core score.
- point: Produces: set of network communities (modules) (one cohort-level result).
- not available: “writes a narrative report on their biology automatically” — Not matched to any registered workflow.
- next step: Plan CONDOR with my data
- next step: Start a new task

## S228

Request (turn 1): We have methylation, expression and proteomics from the same 95 donors. We want one network of direct partial-correlation links among all three layers jointly.

Requirements to judge (in the user's words):
R1: "one network of direct partial-correlation links among all three layers jointly"

Reply:

````
What I understood you are asking for:
1. "one network of direct partial-correlation links among all three layers jointly" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “one network of direct partial-correlation links among all three layers jointly” — DRAGON does not give it: two layers only.
- next step: Start a new task

## S229

Request (turn 1): Which method should we use for a co-expression analysis of our 90 samples?

Requirements to judge (in the user's words):
R1: "a co-expression analysis of our 90 samples"
Also judge `ambiguity` for this session.

Reply:

````
What I understood you are asking for:
1. "Which method should we use for a co-expression analysis of our 90 samples?" -- available from LIONESS-COEXPRESSION, BONOBO or COBRA.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered workflows fit; one detail about your study decides between them.
- point: Understood goal: a co-expression network.
- question: Should the result be aggregate or sample-specific?
- option: One network per sample (plus the cohort network) — Leads to LIONESS-COEXPRESSION · Lets you compare samples, or relate them to outcomes such as survival
- option: One cohort-wide network — Leads to COBRA
- option: One network per sample — Leads to BONOBO · Lets you compare samples, or relate them to outcomes such as survival
- next step: Start a new task

## S230

Request (turn 1): We have expression from 70 colon samples. We want a TF-gene network for each sample.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each sample"

Reply:

````
What I understood you are asking for:
1. "a TF-gene network for each sample" -- available from LIONESS-PANDA.

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

**What your data allows.** LIONESS-PANDA and PANDA need a motif prior and a PPI network, which you said you do not have ("We have expression from 70 colon samples.").

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 70 samples, 71 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Needs a motif prior and a PPI network, which you said you do not have.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S231

Request (turn 1): Which method gives each TF's activity per sample from our expression, motifs and PPI, and also aligns our raw reads to the genome first?

Requirements to judge (in the user's words):
R1: "each TF's activity per sample"
R2: "aligns our raw reads to the genome"

Reply:

````
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
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S232

Request (turn 1): Sorry, I meant a separate network for each patient.

Requirements to judge (in the user's words):
R1: "a separate network for each patient"

Reply:

````
What I understood you are asking for:
1. "a separate network for each patient." -- available from LIONESS-PANDA, LIONESS-PUMA, LIONESS-DRAGON, LIONESS-COEXPRESSION or BONOBO.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**What your data allows.** LIONESS-PANDA and PANDA also need an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs.
- point: Produces: regulatory network (cohort-level and per-sample).
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S233

Request (turn 1): We want gene modules from a TF-gene network, but we have not built the network yet; we only have expression, motifs and PPI from 55 samples.

Requirements to judge (in the user's words):
R1: "gene modules from a TF-gene network"

Reply:

````
What I understood you are asking for:
1. "gene modules from a TF-gene network" -- available from CONDOR.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

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

## S234

Request (turn 1): We built a gene-gene co-expression network from 200 samples. We want its gene modules, found with bipartite modularity.

Requirements to judge (in the user's words):
R1: "its gene modules, found with bipartite modularity"

Reply:

````
What I understood you are asking for:
1. "its gene modules, found with bipartite modularity" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “its gene modules, found with bipartite modularity” — Not matched to any registered workflow.
- next step: Start a new task

## S235

Request (turn 1): We have RNA-seq from 45 heart biopsies but no motif or PPI data at all. We want one TF-gene regulatory network.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network"

Reply:

````
What I understood you are asking for:
1. "one TF-gene regulatory network" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “one TF-gene regulatory network” — Not matched to any registered workflow.
- next step: Start a new task

## S236

Request (turn 1): With methylation and expression from 80 donors, we want the direct links between the two layers, and also the causal direction of each link.

Requirements to judge (in the user's words):
R1: "the direct links between the two layers"
R2: "the causal direction of each link"

Reply:

````
What I understood you are asking for:
1. "direct links between the two layers" -- available from DRAGON.
2. "causal direction of each link" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "the causal direction of each link": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Assumptions behind this recommendation (not confirmed facts):

- The user has access to both methylation and expression data from the 80 donors.
- The analysis aims to identify causal relationships between the two omics layers.
- The user is looking for a comprehensive understanding of the interactions between methylation and expression across the donor cohort.

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
- not available: “causal direction of each link” — Every registered workflow estimates associations or model coefficients from observational data.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S237

Request (turn 1): We have methylation and expression from the same 95 donors. Is there a method that gives a network of direct partial-correlation links within and between the two layers, with a p-value for each edge?

Requirements to judge (in the user's words):
R1: "a network of direct partial-correlation links within and between the two layers, with a p-value for each edge"

Reply:

````
What I understood you are asking for:
1. "Is there a method that gives a network of direct partial-correlation links within and between the two layers, with a p-value for each edge?" -- available from DRAGON or LIONESS-DRAGON.

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

## S238

Request (turn 1): We have RNA-seq from 45 heart biopsies but no motif or PPI data at all. We want one TF-gene regulatory network.

Requirements to judge (in the user's words):
R1: "one TF-gene regulatory network"

Reply:

````
What I understood you are asking for:
1. "We want one TF-gene regulatory network." -- available from PANDA, OTTER or GIRAFFE.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**What your data allows.** Your request names only expression data. PANDA, OTTER and GIRAFFE need a motif prior and a PPI network, which you said you do not have ("no motif or PPI data at all").

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network from expression data.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- point: Needs a motif prior and a PPI network, which you said you do not have.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S239

Request (turn 1): From expression, motifs and PPI of 110 lymphoma samples, which method gives a separate TF-gene network for each sample?

Requirements to judge (in the user's words):
R1: "a separate TF-gene network for each sample"

Reply:

````
What I understood you are asking for:
1. "which method gives a separate TF-gene network for each sample?" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 110 samples, 111 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 110 samples, 111 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S240

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. We want overlapping communities, where a gene can belong to several communities at once.

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

Reply:

````
What I understood you are asking for:
1. "We want overlapping communities, where a gene can belong to several communities at once." -- available from CONDOR.

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

## S241

Request (turn 1): Actually, each gene should be allowed to sit in several communities at once.

Requirements to judge (in the user's words):
R1: "each gene should be allowed to sit in several communities at once"

Reply:

````
What I understood you are asking for:
1. "Actually, each gene should be allowed to sit in several communities at once." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Actually, each gene should be allowed to sit in several communities at once.” — Not matched to any registered workflow.
- next step: Start a new task

## S242

Request (turn 1): We measured expression every 2 hours for 48 hours after heat shock, with motifs and PPI. Is there a method that models how each TF-gene edge at one time point depends on the edges at the previous time point?

Requirements to judge (in the user's words):
R1: "models how each TF-gene edge at one time point depends on the edges at the previous time point"

Reply:

````
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The user has time-series expression data for analysis.
- The user is interested in temporal modeling of regulatory interactions.
- The user is looking for methods applicable to time-series data.
- The analysis involves transcription factors and their regulatory roles.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered workflows fit your request; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S243

Request (turn 1): With expression, motifs and PPI from 72 tumors, which method gives a separate signed network for each tumor, saying for every TF-gene edge whether the TF activates or represses it in that tumor?

Requirements to judge (in the user's words):
R1: "a separate signed network for each tumor"

Reply:

````
What I understood you are asking for:
1. "which method gives a separate signed network for each tumor, saying for every TF-gene edge whether the TF activates or represses it in that tumor?" -- not available here: no registered workflow produces this. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “which method gives a separate signed network for each tumor, saying for every… — OTTER does not give it: no per-sample OTTER is registered.
- next step: Start a new task

## S244

Request (turn 1): We have expression from 300 patients with drug response labels. We want a model that predicts the response of new patients.

Requirements to judge (in the user's words):
R1: "a model that predicts the response of new patients"

Reply:

````
What I understood you are asking for:
1. "We want a model that predicts the response of new patients." -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a model that predicts the response of new patients.” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- next step: Start a new task

## S245

Request (turn 1): We have ATAC-seq peaks from 30 samples. We want to discover de novo motifs enriched in the peaks.

Requirements to judge (in the user's words):
R1: "discover de novo motifs enriched in the peaks"

Reply:

````
What I understood you are asking for:
1. "discover de novo motifs enriched in the peaks" -- not available here: no registered workflow produces this. PANDA does not give it: the motif prior is an input; PANDA never searches sequence.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “discover de novo motifs enriched in the peaks” — PANDA does not give it: the motif prior is an input; PANDA never searches sequence.
- not available: SPIDER (chromatin-filtered prior) — Not registered here; SPIDER is in netZooR and netZooM. The filtered prior can then be used with PANDA or OTTER.
- next step: Start a new task

## S246

Request (turn 1): We have mRNA expression, TF motifs and PPI for 90 samples. Is there a method for one network in which both TFs and miRNAs regulate the genes?

Requirements to judge (in the user's words):
R1: "one network in which both TFs and miRNAs regulate the genes"

Reply:

````
What I understood you are asking for:
1. "Is there a method for one network in which both TFs and miRNAs regulate the genes?" -- available from PUMA.

**PUMA** fits the result you describe if you have a miRNA list.

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

**What your data allows.** Your request names only a motif prior and a PPI network. PUMA also needs a miRNA list. With a motif prior and a PPI network alone, PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER or GIRAFFE builds one cohort-level network instead. Do you also have a miRNA list?

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA fits your goal if you have a miRNA list.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- point: Your request names only a motif prior and a PPI network; the matched workflows need more inputs, while PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER or GIRAFFE works from it alone.
- question: Do you also have a miRNA list?
- option: Only a motif prior and a PPI network — Leads to PANDA, LIONESS-PANDA, LIONESS-COEXPRESSION, OTTER or GIRAFFE · One cohort-level network
- option: I also have a miRNA list — Leads to PUMA
- next step: Plan PUMA with my data
- next step: Start a new task

## S247

Request (turn 1): We have a bipartite TF-gene network from an earlier PANDA run. Is there a method that finds overlapping communities, where a gene can belong to several communities at once?

Requirements to judge (in the user's words):
R1: "overlapping communities, where a gene can belong to several communities at once"

Reply:

````
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

## S248

Request (turn 1): We have Hi-C contact maps from 12 cell lines. We want to call topologically associating domains in each one.

Requirements to judge (in the user's words):
R1: "call topologically associating domains in each one"

Reply:

````
What I understood you are asking for:
1. "call topologically associating domains in each one" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “call topologically associating domains in each one” — Not matched to any registered workflow.
- next step: Start a new task

## S249

Request (turn 1): From expression, motifs and PPI of 110 lymphoma samples, which method gives a separate TF-gene network for each sample?

Requirements to judge (in the user's words):
R1: "a separate TF-gene network for each sample"

Reply:

````
What I understood you are asking for:
1. "which method gives a separate TF-gene network for each sample?" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 110 samples, 111 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 110 samples, 111 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S250

Request (turn 1): With methylation and expression from 80 donors, we want the direct links between the two layers, and also the causal direction of each link.

Requirements to judge (in the user's words):
R1: "the direct links between the two layers"
R2: "the causal direction of each link"

Reply:

````
What I understood you are asking for:
1. "direct links between the two layers" -- available from DRAGON.
2. "causal direction of each link" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "the causal direction of each link": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Assumptions behind this recommendation (not confirmed facts):

- The user has both methylation and expression data from 80 donors available for analysis.
- The user is interested in understanding causal relationships, which implies a need for a sophisticated analysis of the data.

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
- not available: “causal direction of each link” — Every registered workflow estimates associations or model coefficients from observational data.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S251

Request (turn 1): We have somatic mutations for 260 tumors. Which method groups the patients into subtypes from pathway-level mutation scores?

Requirements to judge (in the user's words):
R1: "groups the patients into subtypes from pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "groups the patients into subtypes from pathway-level mutation scores" -- available from SAMBAR.

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

## S252

Request (turn 1): We built a gene-gene co-expression network from 200 samples. We want its gene modules, found with bipartite modularity.

Requirements to judge (in the user's words):
R1: "its gene modules, found with bipartite modularity"

Reply:

````
What I understood you are asking for:
1. "gene modules, found with bipartite modularity" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “gene modules, found with bipartite modularity” — Not matched to any registered workflow.
- next step: Start a new task

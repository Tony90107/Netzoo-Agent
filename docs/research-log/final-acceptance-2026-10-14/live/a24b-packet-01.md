## S001

Request (turn 1): Which method gives me a single TF-to-target-gene regulatory network for 48 bovine mammary samples? I have the expression matrix, a TF motif prior scanned against bosTau9 promoters, and a TF-TF interaction list.

Requirements to judge (in the user's words):
R1: "a single TF-to-target-gene regulatory network for 48 bovine mammary samples"

Reply:

````
What I understood you are asking for:
1. "Which method gives me a single TF-to-target-gene regulatory network for 48 bovine mammary samples?" -- available from PANDA, OTTER, GIRAFFE or LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, GIRAFFE.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network from expression data and a motif prior.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- option: PUMA — One TF + miRNA network across all your samples · Also adds miRNA regulators · Pick it if the regulators include miRNAs · Also needs miRNA list
- next step: Start a new task

## S002

Request (turn 1): Our sequencing partner sent a variant-by-gene count table for 190 patients and I'm not sure whether it holds somatic tumour mutations or germline variants. We'd like pathway mutation scores and patient subgroups from it; gene lengths, the cancer-gene list and a GMT file are ready.

Requirements to judge (in the user's words):
R1: "pathway mutation scores"
R2: "patient subgroups"

Reply:

````
What I understood you are asking for:
1. "pathway mutation scores" -- available from SAMBAR.
2. "patient subgroups" -- available from SAMBAR.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

To use subtypes for chemotherapy resistance or another clinical outcome, you would also need outcome labels matched to the patients. Check cluster stability and confounding, then evaluate prediction on held-out patients. Fit feature selection and cohort-dependent network estimation within the training split to avoid information leakage.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: SAMBAR produces a gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S003

Request (turn 1): We'd like a network in which lncRNAs act as the regulators of protein-coding genes across our 60 prostate tumours.

Requirements to judge (in the user's words):
R1: "a network in which lncRNAs act as the regulators of protein-coding genes"

Reply:

````
What I understood you are asking for:
1. "a network in which lncRNAs act as the regulators of protein-coding genes" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models lncRNA regulators. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a network in which lncRNAs act as the regulators of protein-coding genes” — Registered regulatory workflows contain miRNA and TF regulators; none models lncRNA regulators.
- next step: Start a new task

## S004

Request (turn 1): We'd like a DRAGON network between the proteome and the transcriptome of our 64 matched tumours, and please fold the metabolome from the same tumours into the same model as a third layer.

Requirements to judge (in the user's words):
R1: "a DRAGON network between the proteome and the transcriptome of our 64 matched tumours"
R2: "fold the metabolome from the same tumours into the same model as a third layer"

Reply:

````
What I understood you are asking for:
1. "We'd like a DRAGON network between the proteome and the transcriptome of our 64 matched tumours, and please fold the metabolome from the same tumours into the same model as a third layer." -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We'd like a DRAGON network between the proteome and the transcriptome of our… — DRAGON does not give it: two layers only.
- next step: Start a new task

## S005

Request (turn 1): Using expression from 300 GTEx skeletal muscle samples, we want a directed acyclic Bayesian network showing which genes drive which others.

Requirements to judge (in the user's words):
R1: "a directed acyclic Bayesian network showing which genes drive which others"

Reply:

````
What I understood you are asking for:
1. "a directed acyclic Bayesian network showing which genes drive which others" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a directed acyclic Bayesian network showing which genes drive which others” — Registered regulatory workflows contain miRNA and TF regulators; none models other regulators.
- next step: Start a new task

## S006

Request (turn 1): We want per-sample co-expression networks with LIONESS for our 33 equine tendon samples, and afterwards upload them to Zenodo under our group account.

Requirements to judge (in the user's words):
R1: "per-sample co-expression networks with LIONESS for our 33 equine tendon samples"
R2: "upload them to Zenodo under our group account"

Reply:

````
What I understood you are asking for:
1. "per-sample co-expression networks with LIONESS" -- available from LIONESS-COEXPRESSION.
2. "and afterwards upload them to Zenodo under our group account" -- not available here: no registered workflow produces this. Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.

Based on what you said — "We want per-sample co-expression networks with LIONESS for our 33 equine tendon samples." — **BONOBO** fits better: a confidence value (p-value) is needed for each connection in each sample.

Your question asks for a per-sample co-expression network. **BONOBO** fits that result and scale.

**BONOBO** (recommend) — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable. Needs expression matrix. Produces inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result (one result per sample).

Other compatible option(s):
- **LIONESS-COEXPRESSION** — preferred when: dozens of samples or more; no sample covariates need to be separated or adjusted; approach: derive each sample network from all-sample and leave-one-out networks.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **BONOBO** — Per-sample gene degree or edge weights can be compared across samples or groups; with p-value output, edges can be filtered per sample at a chosen confidence. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. These are co-expression networks, not TF-gene regulation; turning them into regulatory networks needs a separate, validated conversion before PANDA.

Should I use BONOBO, or does another listed option fit your study better?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Recommended: BONOBO, from what you said.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- point: Your stated concern is answered per method in the full explanation.
- question: Which method fits your study?
- option: BONOBO — Fits what you said: you need a p-value for each edge · One gene co-expression network per sample, with a p-value for each connection [Recommended]
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more
- not available: “and afterwards upload them to Zenodo under our group account” — Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.
- next step: Start a new task

## S007

Request (turn 1): Which TFs drive the transition from normal mucosa to adenoma? We want the transition matrix between the two states' networks, as MONSTER computes it.

Requirements to judge (in the user's words):
R1: "the transition matrix between the two states' networks"

Reply:

````
What I understood you are asking for:
1. "Which TFs drive the transition from normal mucosa to adenoma?" -- not matched to any registered workflow.
2. "the transition matrix between the two states' networks, as MONSTER computes it" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- point: Understood: "Which TFs drive the transition from normal mucosa to adenoma?"
- point: Understood: "the transition matrix between the two states' networks, as MONSTER computes it"
- not available: “Which TFs drive the transition from normal mucosa to adenoma?” — Not matched to any registered workflow.
- not available: “the transition matrix between the two states' networks, as MONSTER computes it” — Not matched to any registered workflow.
- next step: Start a new task

## S008

Request (turn 1): Run PANDA on this month's 40 prostate samples with the usual motif and PPI files, and set it to re-run automatically every Monday as new samples arrive.

Requirements to judge (in the user's words):
R1: "Run PANDA on this month's 40 prostate samples"
R2: "re-run automatically every Monday as new samples arrive"

Reply:

````
What I understood you are asking for:
1. "Run PANDA" -- available from PANDA.

No tool was executed because the Planner requires additional input.

Choose one complete input bundle before the workflow continues, or enter custom to select files individually:
1. data/auto-check-invalid/
   - expression.tsv
   - motif.tsv
   - ppi.tsv
2. data/auto-check-valid/
   - expression.tsv
   - motif.tsv
   - ppi.tsv
3. data/blind-neutral/case-1/
   - expression.tsv
   - motif.tsv
   - ppi.tsv
4. data/blind-neutral/case-2/
   - expression.tsv
   - motif.tsv
   - ppi.tsv
5. data/blind-neutral/case-4/
   - expression.tsv
   - motif.tsv
   - ppi.tsv
````

Card shown with the reply:
(no card)

## S009

Request (turn 1): Our 96 pancreatic samples came from two hospitals. With the expression matrix, a 0/1 hospital column in covariates.tsv, the motif prior and the PPI, we'd like a PANDA network built on hospital-adjusted co-expression.

Requirements to judge (in the user's words):
R1: "a PANDA network built on hospital-adjusted co-expression"

Reply:

````
What I understood you are asking for:
1. "a PANDA network built on hospital-adjusted co-expression" -- available from PANDA.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Picked from 2 fitting methods because you wrote “hospital-adjusted co-expression”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S010

Request (turn 1): Our 96 pancreatic samples came from two hospitals. With the expression matrix, a 0/1 hospital column in covariates.tsv, the motif prior and the PPI, we'd like a PANDA network built on hospital-adjusted co-expression.

Requirements to judge (in the user's words):
R1: "a PANDA network built on hospital-adjusted co-expression"

Reply:

````
What I understood you are asking for:
1. "a PANDA network built on hospital-adjusted co-expression" -- available from PANDA.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale.

**COBRA** — Model covariate-associated gene co-expression with COBRA. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Outputs:

- `coexpression_network`: Inferred gene-to-gene associations.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: COBRA fits your goal: cohort-level co-expression network.
- point: Picked from 2 fitting methods because you wrote “hospital-adjusted co-expression”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S011

Request (turn 1): How do we get a separate TF-and-miRNA-to-gene network for each of 75 ovarian cancer patients? Expression, the motif prior with miRNA edges, PPI and the miRNA list are all ready.

Requirements to judge (in the user's words):
R1: "a separate TF-and-miRNA-to-gene network for each of 75 ovarian cancer patients"

Reply:

````
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

Fallback recommendation: **PUMA**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a regulatory network. **PUMA** is related to that result.

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
- headline: PUMA is the closest registered match, but it is not a verified match for your request.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- next step: Start a new task

## S012

Request (turn 1): Run LIONESS-DRAGON on all 20,000 genes and 800 proteins for our 300 patients and keep every per-patient network.

Requirements to judge (in the user's words):
R1: "LIONESS-DRAGON on all 20,000 genes and 800 proteins for our 300 patients"

Reply:

````
What I understood you are asking for:
1. "keep every per-patient network" -- available from LIONESS-DRAGON.

No tool was executed because the Planner requires additional input.

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.
````

Card shown with the reply:
(no card)

## S013

Request (turn 1): For our 58 asthma bronchial brushings (29 severe, 29 mild) we have expression, a motif prior and a PPI. We want individual TF-gene networks for every sample, and then a list of edges that differ significantly between severe and mild.

Requirements to judge (in the user's words):
R1: "individual TF-gene networks for every sample"
R2: "a list of edges that differ significantly between severe and mild"

Reply:

````
What I understood you are asking for:
1. "individual TF-gene networks for every sample" -- available from LIONESS-PANDA.
2. "a list of edges that differ significantly between severe and mild" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

It sounds like you want sample-specific TF-to-gene regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

The only registered workflow compatible with this request is **LIONESS-PANDA**, but it infers a regulatory network from its inputs, while your request reads as asking to analyze an existing result; and your request does not settle the kind of result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA produces a regulatory network (cohort-level and per-sample).
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs.
- point: Produces: regulatory network (cohort-level and per-sample).
- point: It also writes the cohort network, so PANDA need not run first.
- next step: Start a new task

## S014

Request (turn 1): Run DRAGON on methylation_beta.csv and rnaseq_log.csv (the same 140 lung adenocarcinoma patients, patients as rows) and give me the partial-correlation network.

Requirements to judge (in the user's words):
R1: "give me the partial-correlation network"

Reply:

````
No tool was executed because the Planner requires additional input.

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.
````

Card shown with the reply:
(no card)

## S015

Request (turn 1): Run CONDOR on our thresholded OTTER edge list otter_edges.csv (positive weights only) to get TF-gene communities, and allow genes to sit in more than one community.

Requirements to judge (in the user's words):
R1: "Run CONDOR on our thresholded OTTER edge list otter_edges.csv"
R2: "allow genes to sit in more than one community"

Reply:

````
What I understood you are asking for:
1. "TF-gene communities" -- not available here: no registered workflow produces this. Registered grouping puts each item in exactly one group (CONDOR: one community per regulator or gene; SAMBAR: one subtype per sample); none returns overlapping memberships.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “TF-gene communities” — Registered grouping puts each item in exactly one group (CONDOR: one community per regulator or gene; SAMBAR: one subtype per sample); none returns overlapping memberships.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S016

Request (turn 1): Can we turn our bladder cancer somatic mutation table (220 patients x 18,000 genes) into pathway-level mutation scores? We do have a GMT pathway file.

Requirements to judge (in the user's words):
R1: "pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "turn our bladder cancer somatic mutation table (220 patients x 18,000 genes) into pathway-level mutation scores?" -- available from SAMBAR.

Selected path: **SAMBAR**.

Your question asks for a cohort-level pathway mutation matrix. **SAMBAR** fits that result and scale.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: SAMBAR fits your goal: cohort-level pathway mutation score matrix.
- point: Method: Pathway-level mutation scores, then patient subtypes by clustering.
- point: Needs: somatic mutation matrix, gene-length CSV, cancer-gene list, GMT pathway file.
- point: Produces: gene mutation score matrix, pathway mutation score matrix, set of sample subtypes and sample distance matrix (one cohort-level result).
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S017

Request (turn 1): We have 'miRNA data' for 60 gastric samples from an old project, and I'm not sure if it's measured miRNA expression or a table of predicted miRNA targets. We want miRNAs linked to the genes they affect; gene expression for the same samples is ready.

Requirements to judge (in the user's words):
R1: "miRNAs linked to the genes they affect"

Reply:

````
What I understood you are asking for:
1. "miRNAs linked to the genes they affect" -- available from PUMA.
2. "I'm not sure if it's measured miRNA expression or a table of predicted miRNA targets." -- you have not chosen which result you want: if "measured miRNA expression": no registered workflow gives this; if "table of predicted miRNA targets": PUMA.

Before I choose a workflow, please tell me: Which result do you want: "measured miRNA expression" or "table of predicted miRNA targets"?

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: One fact about your data decides which workflow applies.
- point: Which result do you want: "measured miRNA expression" or "table of predicted miRNA targets"?
- point: Your request names the data I described; the matched workflows also need more inputs, while LIONESS-COEXPRESSION or BONOBO works from it alone.
- question: Do you also have a motif prior, a PPI network and a miRNA list?
- option: Only the data I described — Leads to LIONESS-COEXPRESSION or BONOBO · A gene-gene co-expression network (genes only, no regulator roles)
- option: I also have a motif prior, a PPI network and a miRNA list — Leads to PUMA
- next step: Start a new task

## S018

Request (turn 1): We have a 10-time-point series of mouse liver after partial hepatectomy, one sample per time point, plus motif and PPI priors. We haven't decided whether we want one network per time point or the time delays between regulators and their targets.

Requirements to judge (in the user's words):
R1: "one network per time point or the time delays between regulators and their targets"

Reply:

````
What I understood you are asking for:
1. "one network per time point" -- available from LIONESS-PANDA, LIONESS-PUMA, LIONESS-DRAGON, LIONESS-COEXPRESSION or BONOBO.
2. "the time delays between regulators and their targets" -- not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
Not checked against the registered workflows: "plus motif and PPI priors"

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

For “one network per time point”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
````

Card shown with the reply:
- headline: GIRAFFE produces a regulatory network and TF activity matrix (one cohort-level result).
- point: Method: Also estimates per-sample TF activity and signed activating/repressing effects.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Also needs expression matrix; no file for it is named yet.
- point: Produces: regulatory network and TF activity matrix (one cohort-level result).
- not available: “the time delays between regulators and their targets” — No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results.
- not available: “plus motif and PPI priors” — Not checked against the registered workflows.
- not available: “one network per time point” — No registered workflow meets this; it needs a clearer measurement or an external method.
- next step: Start a new task

## S019

Request (turn 1): We need per-sample transcription factor activity estimates for 120 breast tumours, plus the signed TF-gene effects, from the expression matrix, motif prior and PPI we already have.

Requirements to judge (in the user's words):
R1: "per-sample transcription factor activity estimates for 120 breast tumours"
R2: "the signed TF-gene effects"

Reply:

````
What I understood you are asking for:
1. "per-sample transcription factor activity estimates" -- available from GIRAFFE.
2. "signed TF-gene effects" -- available from GIRAFFE.

Selected path: **GIRAFFE**.

Your question asks for a cohort-level regulatory network with TF activities. **GIRAFFE** fits that result and scale.

What you asked about:

- "We need per-sample transcription factor activity estimates for 120 breast tumours" — The activity matrix holds one value per TF per sample (TF by sample, written as the `.tfa` output). GIRAFFE reports absolute activity, so every value is zero or positive.

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
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S020

Request (turn 1): How would I find which gene co-expression patterns are associated with smoking in 180 airway samples? Right now I just have the expression matrix.

Requirements to judge (in the user's words):
R1: "which gene co-expression patterns are associated with smoking"

Reply:

````
What I understood you are asking for:
1. "How would I find which gene co-expression patterns are associated with smoking in 180 airway samples?" -- the check matched no registered workflow to this, but the second check that confirms such a gap could not run (not confirmed).
2. "Right now I just have the expression matrix." -- the check matched no registered workflow to this, but the second check that confirms such a gap could not run (not confirmed).
The second check that confirms a gap could not run this turn, so the lines above are not confirmed, and the methods below were not removed for them.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **LIONESS-COEXPRESSION** — produces: One gene-gene co-expression network per sample, plus the aggregate.
- **COBRA** — produces: The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix.
- **BONOBO** — produces: One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: LIONESS-COEXPRESSION — Not confirmed. Produces: One gene-gene co-expression network per sample, plus the aggregate.
- option: COBRA — Not confirmed. Produces: The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix.
- option: BONOBO — Not confirmed. Produces: One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample.
- not available: “How would I find which gene co-expression patterns are associated with… — The check matched no registered workflow to this, but the second check that confirms such a gap could not run (not confirmed).
- not available: “Right now I just have the expression matrix.” — The check matched no registered workflow to this, but the second check that confirms such a gap could not run (not confirmed).
- next step: Start a new task

## S021

Request (turn 1): We haven't decided whether we'll have four or five omics layers on our 100 donors, but we want all of them in one joint partial-correlation network.

Requirements to judge (in the user's words):
R1: "all of them in one joint partial-correlation network"

Reply:

````
What I understood you are asking for:
1. "we want all of them in one joint partial-correlation network." -- available from DRAGON.

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

## S022

Request (turn 1): Go ahead and map cis-eQTLs from our genotype calls and expression for 400 individuals.

Requirements to judge (in the user's words):
R1: "map cis-eQTLs from our genotype calls and expression for 400 individuals"

Reply:

````
What I understood you are asking for:
1. "map cis-eQTLs" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “map cis-eQTLs” — Registered regulatory workflows contain miRNA and TF regulators; none models other regulators.
- next step: Start a new task

## S023

Request (turn 1): Run it now: build one aggregate PANDA network for our 64 liver biopsies from expr_liver.tsv, motif prior motif_hs.txt and PPI ppi_hs.txt, and call the output liver_panda.txt.

Requirements to judge (in the user's words):
R1: "build one aggregate PANDA network for our 64 liver biopsies"

Reply:

````
No tool was executed because the Planner requires additional input.

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-final-live/expr_liver.tsv
- PANDA/PUMA inputs: error: motif file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-final-live/motif_hs.txt
- PANDA/PUMA inputs: error: PPI file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-final-live/ppi_hs.txt

Please provide corrected files or fix the file contents, then I will re-check them.
````

Card shown with the reply:
(no card)

## S024

Request (turn 1): We haven't decided whether we want per-sample TF activity scores or per-sample TF-gene networks for our 90 psoriasis skin biopsies. Motif prior, PPI and expression are all available, so please get started.

Requirements to judge (in the user's words):
R1: "per-sample TF activity scores or per-sample TF-gene networks"

Reply:

````
What I understood you are asking for:
1. "We haven't decided whether we want" -- you have not chosen which result you want: if "per-sample TF activity scores": GIRAFFE; if "per-sample TF-gene networks": LIONESS-PANDA.

Before I choose a workflow, please tell me: Which result do you want: "per-sample TF activity scores" or "per-sample TF-gene networks"?

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: One fact about your data decides which workflow applies.
- point: Which result do you want: "per-sample TF activity scores" or "per-sample TF-gene networks"?
- next step: Start a new task

## S025

Request (turn 1): We have a proteomics table and an RNA-seq table from the same hospital biobank, but I don't know whether they were measured on the same patients. Can we get one joint network linking proteins and transcripts?

Requirements to judge (in the user's words):
R1: "one joint network linking proteins and transcripts"

Reply:

````
What I understood you are asking for:
1. "Can we get one joint network linking proteins and transcripts?" -- available from DRAGON. You said "but I don't know whether they were measured on the same patients.": before it runs, DRAGON checks that both tables list exactly the same sample IDs and pairs their rows by ID, so their order does not matter; if they are not the same samples, that check stops it and lists the IDs that differ.

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

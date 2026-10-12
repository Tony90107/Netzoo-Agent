## S031

Request (turn 1): We want per-sample TF-gene networks for 40 samples.
Request (turn 2): Another thing: we'd like guide RNAs designed to knock out the strongest hub TFs.

Requirements to judge (in the user's words, from the last turn):
R1: "guide RNAs designed to knock out the strongest hub TFs"

Reply to the last turn:

````
What I understood you are asking for:
1. "guide RNAs designed to knock out the strongest hub TFs" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “guide RNAs designed to knock out the strongest hub TFs” — Not matched to any registered workflow.
- next step: Start a new task

## S032

Request (turn 1): We want a partial-correlation network between transcripts and CpG methylation for 66 matched samples.
Request (turn 2): Our proteomics from the same samples has to be part of that single model too.

Requirements to judge (in the user's words, from the last turn):
R1: "Our proteomics from the same samples has to be part of that single model too"

Reply to the last turn:

````
What I understood you are asking for:
1. "a partial-correlation network between transcripts and CpG methylation" -- available from DRAGON.
2. "has to be part of that single model too" -- not available here: no registered workflow produces this. DRAGON does not give it: two layers only.

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

For your question ("We want a partial-correlation network between transcripts and CpG methylation"):
- **DRAGON** — Build one network per time point or condition on the same features and compare the cross-layer edges; this does not use the pairing -- to keep it, use LIONESS-DRAGON and compare each individual's samples.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: DRAGON fits your goal: cohort-level multi-omic network.
- point: Method: Partial-correlation network across two omics layers of the same samples.
- point: Needs: omics layer 1, omics layer 2.
- point: Produces: multi-omic network (one cohort-level result).
- point: Your question: whether the groups or time points differ; the reply says what DRAGON give toward it and the step after each.
- not available: “has to be part of that single model too” — DRAGON does not give it: two layers only.
- next step: Plan DRAGON with my data
- next step: Start a new task

## S033

Request (turn 1): We want a TF-gene network from expression, motifs and PPI of 77 samples.
Request (turn 2): For each TF we need to see whether it switches its targets on or off.

Requirements to judge (in the user's words, from the last turn):
R1: "whether it switches its targets on or off"

Reply to the last turn:

````
What I understood you are asking for:
1. "We want a TF-gene network from expression, motifs and PPI of 77 samples." -- available from PANDA.
2. "For each TF we need to see whether it switches its targets on or off." -- available from GIRAFFE.

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
- next step: Plan GIRAFFE with my data
- next step: Start a new task

## S034

Request (turn 1): We want a network connecting gene expression with metabolite levels in 92 matched samples.
Request (turn 2): Every edge also needs a Benjamini-Hochberg adjusted p-value.

Requirements to judge (in the user's words, from the last turn):
R1: "Every edge also needs a Benjamini-Hochberg adjusted p-value"

Reply to the last turn:

````
What I understood you are asking for:
1. "We want a network connecting gene expression with metabolite levels in 92 matched samples." -- available from DRAGON.
2. "Every edge also needs a Benjamini-Hochberg adjusted p-value." -- available from DRAGON.

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

## S035

Request (turn 1): We want per-sample TF-gene networks for 52 patients from expression, motifs and PPI.
Request (turn 2): Could those networks then be related to the patients' survival?

Requirements to judge (in the user's words, from the last turn):
R1: "related to the patients' survival"

Reply to the last turn:

````
What I understood you are asking for:
1. "per-sample TF-gene networks" -- available from LIONESS-PANDA.
2. "related to the patients' survival" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

Selected path: **LIONESS-PANDA**.

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
- headline: LIONESS-PANDA produces a regulatory network (cohort-level and per-sample).
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 52 patients, 53 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: It also writes the cohort network, so PANDA need not run first.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S036

Request (turn 1): We want a co-expression network for every one of our 96 samples.
Request (turn 2): These samples are spots on one tissue slide, and each spot's network should draw on the spots next to it.

Requirements to judge (in the user's words, from the last turn):
R1: "each spot's network should draw on the spots next to it"

Reply to the last turn:

````
What I understood you are asking for:
1. "We want a co-expression network for every one of our 96 samples." -- available from LIONESS-COEXPRESSION.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "96 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Pick it if you have only a handful of samples or you need a p-value for each edge
- next step: Start a new task

## S037

Request (turn 1): We want a TF-gene network for 50 samples from expression, motifs and PPI.
Request (turn 2): alright

Requirements to judge (in the user's words, from the last turn):
(none: the second turn asks for nothing; give `R: []`)

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

## S038

Request (turn 1): We want a co-expression network for every one of our 96 samples.
Request (turn 2): These samples are spots on one tissue slide, and each spot's network should draw on the spots next to it.

Requirements to judge (in the user's words, from the last turn):
R1: "each spot's network should draw on the spots next to it"

Reply to the last turn:

````
What I understood you are asking for:
1. "a co-expression network for every one of our 96 samples" -- available from LIONESS-COEXPRESSION.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Both fit; to choose, tell me: (1) About how many samples do you have? (only a handful of samples → BONOBO; dozens of samples or more → LIONESS-COEXPRESSION) (2) Do you need a confidence value for each connection in each sample? (yes → BONOBO)

You mentioned "96 samples". Whether that counts as a handful of samples or as dozens or more is your call for this study design; I do not map a sample count to these categories myself.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 2 registered methods can build a per-sample co-expression network; they differ in their modeling assumptions.
- point: Understood goal: a per-sample co-expression network.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: LIONESS-COEXPRESSION — One gene co-expression network per sample, from expression data alone · Pick it if you have dozens of samples or more
- option: BONOBO — One gene co-expression network per sample, with a p-value for each connection · Pick it if you have only a handful of samples or you need a p-value for each edge
- next step: Start a new task

## S039

Request (turn 1): We want a network of how TFs and miRNAs regulate genes across 58 samples, with motifs, PPI and predicted miRNA targets.
Request (turn 2): The miRNA links should be estimated from negative correlation with the miRNA levels we measured.

Requirements to judge (in the user's words, from the last turn):
R1: "The miRNA links should be estimated from negative correlation with the miRNA levels we measured"

Reply to the last turn:

````
What I understood you are asking for:
1. "a network of how TFs and miRNAs regulate genes" -- available from PUMA.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; PUMA gives one result for the whole cohort; LIONESS-PUMA gives one result for the whole cohort or one result per sample.

**PUMA** fits the result you describe if you have a motif prior and a PPI network.

Your question asks for a regulatory network. **PUMA** fits that result.

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

**What your data allows.** Your request names only a miRNA list. PUMA also needs an expression matrix, a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: PUMA fits your goal if you have a motif prior and a PPI network.
- point: Method: PANDA's message passing with miRNA regulators added.
- point: Needs: expression matrix, motif prior, PPI network, miRNA list.
- point: Produces: regulatory network (one cohort-level result).
- point: Your request names only a miRNA list; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only a miRNA list — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Continues with the workflows this reply names
- next step: Plan PUMA with my data
- next step: Start a new task

## S040

Request (turn 1): We want a TF-gene network across 72 samples from expression, motifs and PPI.
Request (turn 2): The samples form a time course, and the model has to capture how regulation at one time point drives the next.

Requirements to judge (in the user's words, from the last turn):
R1: "the model has to capture how regulation at one time point drives the next"

Reply to the last turn:

````
What I understood you are asking for:
1. "a TF-gene network across 72 samples from expression, motifs and PPI." -- available from PANDA.

About "how regulation at one time point drives the next": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

Yes, in principle, data can weaken an unreliable TF-binding prior and quantify uncertainty about it, but only if the model explicitly represents that uncertainty. A hierarchical Bayesian model can treat binding-site predictions as noisy evidence about latent TF-gene edges, with a source-reliability parameter and an expression-data likelihood. Conflicting evidence can lower posterior edge support; learning the source's reliability itself also requires an identifiable model and informative data, potentially including independent binding evidence or multiple priors. A Bayesian label alone does not supply this model.

No qualified registered workflow fully matches the requested modeling philosophy.

Outside this agent (reference only; it cannot run these):
- **TIGER** (netZooR, R) — Bayesian matrix factorization of expression with a prior TF-gene network and TF activities; sparse edge priors let the data shrink unsupported prior edges, one edge at a time. Chen & Padi 2024, doi:10.1038/s41540-024-00386-w.
- **Werhli & Husmeier (2007)** (published method, no NetZoo implementation) — Bayesian networks that give each prior-knowledge source its own weight, sampled by MCMC, so the data decide how much each prior counts. PMID 17542777.

A registered method with that philosophy estimates a different result:
- **BONOBO** — declared output: co-expression networks and matching p-value matrices (one per sample). BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

If you relax that requirement, these registered approaches can infer the requested network through different assumptions:

PANDA and OTTER tie only on the stated output and scope. This does not show that they are equally robust to a noisy motif prior; neither estimates its reliability as a posterior probability.

1. **PANDA** — Iterative message passing reconciles the motif seed with TF-TF interactions and gene co-expression, repeatedly revising TF-gene edge support across those networks. The edge weights summarize integrated evidence, not a posterior probability that the motif prior is reliable.

2. **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

For the probabilistic reliability estimate you asked for, the hierarchical model above remains the recommendation. If stable network scores would suffice instead, perturb or replace the motif prior and compare inferred edges against independent evidence. Neither algorithm is known from the stated facts to be more robust for your study.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow implements the bayesian approach you asked for.
- point: Understood goal: a TF-gene regulatory network.
- point: The registered alternatives do not fulfil the requested modeling requirement.
- question: Would one of these, without that requirement, work for you?
- option: PANDA — Widely used baseline: message passing over motif, PPI and co-expression evidence
- option: OTTER — Explicit objective (graph matching), fitted by a fixed number of gradient steps; lighter on memory
- not available: TIGER — Not runnable here (netZooR, R); Chen & Padi 2024, doi:10.1038/s41540-024-00386-w.
- not available: Werhli & Husmeier (2007) — Not runnable here (published method, no NetZoo implementation); PMID 17542777.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Start a new task

## S041

Request (turn 1): We want per-sample TF-gene networks for 45 tumors from expression, motifs and PPI.
Request (turn 2): We need to know which direction causality runs along each edge.

Requirements to judge (in the user's words, from the last turn):
R1: "which direction causality runs along each edge"

Reply to the last turn:

````
What I understood you are asking for:
1. "per-sample TF-gene networks" -- available from LIONESS-PANDA.
2. "which direction causality runs along each edge" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "we need to know which direction causality runs along each edge.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Selected path: **LIONESS-PANDA**.

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
- headline: LIONESS-PANDA produces a regulatory network (cohort-level and per-sample).
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 45 tumors, 46 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: It also writes the cohort network, so PANDA need not run first.
- not available: “which direction causality runs along each edge” — Every registered workflow estimates associations or model coefficients from observational data.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S042

Request (turn 1): We want per-sample TF-gene networks for 52 patients from expression, motifs and PPI.
Request (turn 2): Could those networks then be related to the patients' survival?

Requirements to judge (in the user's words, from the last turn):
R1: "related to the patients' survival"

Reply to the last turn:

````
What I understood you are asking for:
1. "per-sample TF-gene networks" -- available from LIONESS-PANDA.
2. "related to the patients' survival" -- available from LIONESS-PANDA's output plus a step you run outside NetZoo: A statistical model outside NetZoo (e.g. limma, Cox), with multiple-testing correction; needs a clinical table keyed by sample ID.

Selected path: **LIONESS-PANDA**.

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
- headline: LIONESS-PANDA produces a regulatory network (cohort-level and per-sample).
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 52 patients, 53 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- point: It also writes the cohort network, so PANDA need not run first.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S043

Request (turn 1): We want a regulatory network linking TFs to genes, from expression, motif and PPI data on 85 samples.
Request (turn 2): Those 85 profiles are single cells captured from one organoid.

Requirements to judge (in the user's words, from the last turn):
R1: "Those 85 profiles are single cells"

Reply to the last turn:

````
What I understood you are asking for:
1. "a regulatory network linking TFs to genes" -- not matched to any registered workflow.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “a regulatory network linking TFs to genes” — Not matched to any registered workflow.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S044

Request (turn 1): We want per-sample TF-gene networks for 45 tumors from expression, motifs and PPI.
Request (turn 2): We need to know which direction causality runs along each edge.

Requirements to judge (in the user's words, from the last turn):
R1: "which direction causality runs along each edge"

Reply to the last turn:

````
What I understood you are asking for:
1. "per-sample TF-gene networks" -- available from LIONESS-PANDA.
2. "which direction causality runs along each edge" -- not available here: no registered workflow produces this. Every registered workflow estimates associations or model coefficients from observational data.

About "we need to know which direction causality runs along each edge.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 45 tumors, 46 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 45 tumors, 46 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- not available: “which direction causality runs along each edge” — Every registered workflow estimates associations or model coefficients from observational data.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S045

Request (turn 1): We want to split our 160 tumors into subtypes.
Request (turn 2): We only have their RNA-seq profiles; no mutation calls exist.

Requirements to judge (in the user's words, from the last turn):
R1: "We only have their RNA-seq profiles; no mutation calls exist"

Reply to the last turn:

````
What I understood you are asking for:
1. "split our 160 tumors into subtypes" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “split our 160 tumors into subtypes” — SAMBAR does not give it: SAMBAR's input is somatic mutations.
- next step: Start a new task

## S046

Request (turn 1): We want gene-gene co-expression for 180 samples.
Request (turn 2): They were sequenced in four batches, and the batch-related part of the co-expression should be pulled apart.

Requirements to judge (in the user's words, from the last turn):
R1: "the batch-related part of the co-expression should be pulled apart"

Reply to the last turn:

````
What I understood you are asking for:
1. "gene-gene co-expression" -- available from LIONESS-COEXPRESSION.
2. "the batch-related part of the co-expression should be pulled apart" -- available from COBRA.

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
- point: Picked from 3 fitting methods because you wrote “We want gene-gene co-expression for…”; LIONESS-COEXPRESSION and BONOBO also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION and BONOBO
- next step: Plan COBRA with my data
- next step: Start a new task

## S047

Request (turn 1): We want a network connecting gene expression with metabolite levels in 92 matched samples.
Request (turn 2): Every edge also needs a Benjamini-Hochberg adjusted p-value.

Requirements to judge (in the user's words, from the last turn):
R1: "Every edge also needs a Benjamini-Hochberg adjusted p-value"

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

## S048

Request (turn 1): We want the modules of our bipartite TF-gene network.
Request (turn 2): Within each module we also want the nodes that are most central to it.

Requirements to judge (in the user's words, from the last turn):
R1: "the nodes that are most central to it"

Reply to the last turn:

````
What I understood you are asking for:
1. "We want the modules of our bipartite TF-gene network." -- available from CONDOR.
2. "Within each module we also want the nodes that are most central to it." -- available from CONDOR.

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

## S049

Request (turn 1): We want gene-gene co-expression for 180 samples.
Request (turn 2): They were sequenced in four batches, and the batch-related part of the co-expression should be pulled apart.

Requirements to judge (in the user's words, from the last turn):
R1: "the batch-related part of the co-expression should be pulled apart"

Reply to the last turn:

````
What I understood you are asking for:
1. "gene-gene co-expression for 180 samples" -- available from LIONESS-COEXPRESSION.
2. "the batch-related part of the co-expression should be pulled apart" -- available from COBRA.

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
- point: Picked from 3 fitting methods because you wrote “We want gene-gene co-expression for…”; LIONESS-COEXPRESSION and BONOBO also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION and BONOBO
- next step: Plan COBRA with my data
- next step: Start a new task

## S050

Request (turn 1): We want a TF-gene network across 72 samples from expression, motifs and PPI.
Request (turn 2): The samples form a time course, and the model has to capture how regulation at one time point drives the next.

Requirements to judge (in the user's words, from the last turn):
R1: "the model has to capture how regulation at one time point drives the next"

Reply to the last turn:

````
What I understood you are asking for:
1. "We want a TF-gene network across 72 samples from expression, motifs and PPI." -- available from PANDA.
2. "The samples form a time course, and the model has to capture how regulation at one time point drives the next." -- not available here: no registered workflow produces this. PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.

About "how regulation at one time point drives the next": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

Only part of your request is supported. These workflows provide the confirmed part; no registered workflow supplies the whole request:
- **PANDA** — for "We want a TF-gene network across 72 samples from expression, motifs and PPI."; produces: One weighted TF-to-gene regulatory network across all the samples given.

Ask about the supported part, or describe a different result for the unavailable part.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Only part of your request maps to a registered workflow; nothing is offered for the rest.
- point: Understood: "We want a TF-gene network across 72 samples from expression, motifs and PPI."
- point: Understood: "The samples form a time course, and the model has to capture how regulation at one time point drives the next."
- question: Which result do you want to discuss?
- option: PANDA — For "We want a TF-gene network across 72 samples from expression, motifs and PPI.": One weighted TF-to-gene regulatory network across all the samples given.
- not available: “The samples form a time course, and the model has to capture how regulation… — PANDA does not give it: one static network per set of samples; time points can only be compared as separate networks.
- not available: Show that one thing causes another — Registered workflows estimate associations; they can describe what changes, not prove its cause.
- next step: Start a new task

## S051

Request (turn 1): We want the modules of our bipartite TF-gene network.
Request (turn 2): Within each module we also want the nodes that are most central to it.

Requirements to judge (in the user's words, from the last turn):
R1: "the nodes that are most central to it"

Reply to the last turn:

````
What I understood you are asking for:
1. "the modules of our bipartite TF-gene network" -- available from CONDOR.
2. "the nodes that are most central to it" -- available from CONDOR.

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

## S052

Request (turn 1): We want a TF-gene network from expression, motifs and PPI of 77 samples.
Request (turn 2): For each TF we need to see whether it switches its targets on or off.

Requirements to judge (in the user's words, from the last turn):
R1: "whether it switches its targets on or off"

Reply to the last turn:

````
This turn could not be checked against what the registered workflows produce, so the methods below have not been confirmed to give what you asked for.

Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- **PANDA** — produces: One weighted TF-to-gene regulatory network across all the samples given.
- **PUMA** — produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **LIONESS-PUMA** — produces: One TF/miRNA-gene network per sample, plus the aggregate network.
- **OTTER** — produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: Not confirmed: routing matched these workflows to your words, but the check did not confirm that any of them gives what you asked for.
- point: Compare what each produces with what you asked for; asking again re-runs the check.
- question: Which one do you want to look at?
- option: GIRAFFE — Not confirmed. Produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.
- option: PANDA — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all the samples given.
- option: PUMA — Not confirmed. Produces: One weighted network of how TFs and miRNAs regulate genes, across all samples.
- option: LIONESS-PANDA — Not confirmed. Produces: One TF-gene network per sample, plus the aggregate network.
- option: LIONESS-PUMA — Not confirmed. Produces: One TF/miRNA-gene network per sample, plus the aggregate network.
- option: OTTER — Not confirmed. Produces: One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.
- next step: Start a new task

## S053

Request (turn 1): We want communities in our bipartite TF-gene network.
Request (turn 2): ok, thank you

Requirements to judge (in the user's words, from the last turn):
(none: the second turn asks for nothing; give `R: []`)

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

## S054

Request (turn 1): We want to split our 160 tumors into subtypes.
Request (turn 2): We only have their RNA-seq profiles; no mutation calls exist.

Requirements to judge (in the user's words, from the last turn):
R1: "We only have their RNA-seq profiles; no mutation calls exist"

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

## S055

Request (turn 1): We want a regulatory network linking TFs to genes, from expression, motif and PPI data on 85 samples.
Request (turn 2): Those 85 profiles are single cells captured from one organoid.

Requirements to judge (in the user's words, from the last turn):
R1: "Those 85 profiles are single cells"

Reply to the last turn:

````
What I understood you are asking for:
1. "We want a regulatory network linking TFs to genes" -- available from PANDA, OTTER or GIRAFFE.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**What your data allows.** PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 4 registered methods can build a TF-gene regulatory network; they differ in scale (one network for all samples or one per sample) and in their modeling assumptions.
- point: Understood goal: a TF-gene regulatory network.
- point: Your request names only the data I described; the matched workflows need more inputs, which the request does not mention.
- question: Do you also have a motif prior and a PPI network?
- option: Only the data I described — Ask what the data you named can give instead
- option: I also have a motif prior and a PPI network — Leads to PANDA, LIONESS-PANDA, OTTER or GIRAFFE
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S056

Request (turn 1): We want a TF-gene network for 50 samples from expression, motifs and PPI.
Request (turn 2): alright

Requirements to judge (in the user's words, from the last turn):
(none: the second turn asks for nothing; give `R: []`)

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

## S057

Request (turn 1): We have a bipartite TF-gene network and would like it split into modules.
Request (turn 2): A gene ought to be able to sit in two or three of those modules.

Requirements to judge (in the user's words, from the last turn):
R1: "A gene ought to be able to sit in two or three of those modules"

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

## S058

Request (turn 1): We want a TF-gene network for 50 samples from expression, motifs and PPI.
Request (turn 2): alright

Requirements to judge (in the user's words, from the last turn):
(none: the second turn asks for nothing; give `R: []`)

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

## S059

Request (turn 1): We want a TF-gene network from expression, motifs and PPI of 77 samples.
Request (turn 2): For each TF we need to see whether it switches its targets on or off.

Requirements to judge (in the user's words, from the last turn):
R1: "whether it switches its targets on or off"

Reply to the last turn:

````
What I understood you are asking for:
1. "a TF-gene network" -- available from PANDA.
2. "whether it switches its targets on or off" -- available from GIRAFFE.

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
- point: Understood goal: a TF-gene regulatory network.
- point: Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and GIRAFFE give one across all samples.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Lets you compare samples, or relate them to outcomes such as survival · Slower: it reruns PANDA once per sample
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S060

Request (turn 1): We want a TF-gene regulatory network from expression, motifs and PPI of 64 samples.
Request (turn 2): miRNAs should be among the regulators as well; we have predicted target sites for them.

Requirements to judge (in the user's words, from the last turn):
R1: "miRNAs should be among the regulators as well"

Reply to the last turn:

````
Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.
````

Card shown with the reply:
(no card)

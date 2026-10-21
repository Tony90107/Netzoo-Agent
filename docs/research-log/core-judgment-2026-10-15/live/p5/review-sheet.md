# Review sheet

## ASK facts to check (facts-checked.json)

- C06 gold: Are the ~150 regulators transcription factors (with a TF-to-gene motif prior) rather than RNA-binding proteins?
  - asked: Do you have a list of transcription factors? (user: "I'm not sure which of the two lists I was given."; contract: "PANDA consumes a gene-by-sample expression matrix plus motif and PPI priors, or a validated adjusted gene-by-gene co-expression matrix through coexpression_file.")
- C11 gold: Do you need one network per donor (88 networks) rather than one network per diagnostic group?
  - asked: Which result do you want: "one network per diagnostic group" or "one network per donor"? (user: "I can't tell if that means one network per diagnostic group or one network per donor"; contract: "")
  - asked: Which result do you want: "one network per diagnostic group" or "one network per donor"? (user: "I can't tell if that means one network per diagnostic group or one network per donor"; contract: "")
- C20 gold: Is tumour_profiles_v2.tsv the log2 expression matrix rather than the binary mutation matrix?
  - asked: Is the file you want to use the gene-by-sample expression matrix with log2 expression? (user: "I'm not sure which one this is."; contract: "PANDA consumes a gene-by-sample expression matrix plus motif and PPI priors, or a validated adjusted gene-by-gene co-expression matrix through coexpression_file.")
- C21 gold: Is network_final.tsv the TF-to-gene (regulator-to-gene) network rather than the gene-gene co-expression network?
  - asked: Is the network_final.tsv a TF-to-gene regulatory network? (user: "I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built."; contract: "CONDOR consumes a weighted source-target bipartite edge list made from a validated regulator-gene network and returns community assignments with regulator-side and gene-side partitions.")
- C31 gold: Is one cohort-wide set of signed TF-to-gene effects what you need, rather than a separate signed matrix for each biopsy?
  - asked: Does your supervisor want signed effects for each biopsy separately? (user: "My supervisor's notes say we need those signed effects for each biopsy separately, but the grant text says one set of signed effects for the whole cohort, and I'm not sure which she actually wants."; contract: "It returns the aggregate TF-by-gene R matrix and a TF-by-sample TFA matrix.")

## Replies to spot-check (faithful-checked.json)

### C04 class=do gold=['LIONESS-PANDA'] core=DO ['LIONESS-PANDA'] basis=results_given views=['outcome_clarification']
Request: For each of our 25 diffuse large B-cell lymphoma patients I need that patient's own TF-to-gene regulatory network, built from the cohort's expression matrix together with a human motif prior and a TF PPI, so I can later compare each TF's targeting between responders and non-responders.
```text
k per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### C06 class=ask gold=['PANDA', 'OTTER', 'GIRAFFE'] core=ASK ['PANDA'] basis=fact_agent views=['ask_facts']
Request: I'd like a network of how about 150 regulators control their target genes across 60 hepatocellular carcinoma samples. I have the expression matrix, a PPI among those regulators, and a regulator-to-target prior from a collaborator's project, but that project studied both RNA-binding proteins and transcription factors, and I'm not sure which of the two lists I was given.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.14s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Do you have a list of transcription factors?
  You wrote: "I'm not sure which of the two lists I was given". PANDA's contract: "PANDA consumes a gene-by-sample expression matrix plus motif and PPI priors, or a validated adjusted gene-by-gene co-expression matrix through coexpression_file".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C07 class=do gold=['LIONESS-DRAGON'] core=DO ['LIONESS-DRAGON'] basis=results_given views=['verified_guidance']
Request: We measured 180 circulating miRNAs (normalized, continuous qPCR values) and 45 plasma cytokines in the same 64 sepsis patients; both tables have samples in rows, identical patient IDs and no missing values. What I want is a separate network for every patient that links miRNAs and cytokines through partial correlations, within and across the two layers, so I can compare survivors with non-survivors patient by patient afterwards.
```text
hical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

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

For your question ("compare survivors with non-survivors patient by patient afterwards"):
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### C08 class=dont gold=['GIRAFFE'] core=DO ['GIRAFFE'] basis=results_given views=['verified_guidance']
Request: Can GIRAFFE be run with my own optimizer settings? For our 52 rice leaf samples from the drought trial I want a learning rate of 1e-4, 2,000 iterations and a heavier weight on the PPI term in the loss, because in a pilot the package defaults gave a TF activity matrix that looked over-smoothed and I'd like to see whether these settings change that.
```text
E** fits the result you describe if you have a motif prior and a PPI network.

What you asked about:

- "I want a learning rate of 1e-4, 2,000 iterations and a heavier weight on the PPI term in the loss" — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

**GIRAFFE**: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.

Routing-level input modality: expression matrix.

Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix; interpret TF-gene regulatory weights as coefficients in a linear expression model; estimate positive activating and negative inhibitory partial regulatory effects; model gene expression with transcription factor activities as predictors.

GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Distinct declared output artifacts (availability depends on workflow options):

- `regulatory_network`: Inferred regulator-to-target associations.
- `tf_activity_matrix`: Inferred transcription-factor-by-sample activity values.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### C09 class=vague gold=['BONOBO', 'LIONESS-COEXPRESSION', 'LIONESS-PANDA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Should I go with BONOBO or LIONESS for my 20 Shank3 knockout and wild-type mouse cortex samples? I'm hoping to learn something about the knockout, but I haven't pinned down what yet.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.73s)
● Matching registered workflows…
● Preparing next step…
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C10 class=vague gold=['COBRA', 'CONDOR'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Should I be using COBRA or CONDOR on our lupus nephritis cohort? I keep seeing both names in NetZoo papers and I'm not sure what either would give me.
```text
● Classifying requested outcome…
? Clarification needed
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C11 class=ask gold=['LIONESS-PANDA'] core=ASK ['PANDA'] basis=needs_fact views=['needs_fact']
Request: Run the TF network inference on expr_alzheimer.tsv (88 donors: 44 AD, 44 controls), motifs_hg38.txt and ppi_tf.txt. The analysis plan just says 'a network for each AD and control', and I can't tell if that means one network per diagnostic group or one network per donor; the person who wrote it is on leave until next month.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.92s)
● Matching registered workflows…
✓ Matched workflows — PANDA
● Preparing next step…
What I understood you are asking for:
1. "Run the TF network inference" -- available from PANDA.
2. "I can't tell if that means one network per diagnostic group or one network per donor" -- you have not chosen which result you want: if "one network per diagnostic group": PANDA; if "one network per donor": no registered workflow gives this.
3. "I can't tell if that means one network per diagnostic group or one network per donor" -- you have not chosen which result you want: if "one network per diagnostic group": PANDA; if "one network per donor": no registered workflow gives this.

Before I choose a workflow, please tell me: Which result do you want: "one network per diagnostic group" or "one network per donor"?

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C12 class=vague gold=['LIONESS-COEXPRESSION', 'BONOBO', 'PANDA', 'COBRA'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Please run the network analysis on expr_sle_monocytes.tsv and send me the results.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.00s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "network analysis" -- not matched to any registered workflow.
2. "send me the results" -- not available here: no registered workflow produces this. Every registered workflow writes result files to the output folder you give; sending, uploading, publishing or showing them is done outside NetZoo.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

### C13 class=dont gold=['OTTER'] core=DECLINE [] basis=full_gap views=['decline']
Request: Run OTTER on expr_t2d_islets.tsv, seed_W.tsv and ppi_tf.tsv with lam set to 1.5, so co-expression gets even more weight than PPI.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.27s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "Run OTTER on expr_t2d_islets.tsv, seed_W.tsv and ppi_tf.tsv with lam set to 1.5, so co-expression gets even more weight than PPI." -- not available here as asked. OTTER's lam must be between 0 and 1; "1.5" is not. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

### C14 class=dont gold=['OTTER'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Can I add an L1 (lasso) sparsity penalty to OTTER's objective so that the TF-gene network it returns for my 45 bovine mammary gland samples is sparse, with most edges exactly zero?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.73s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "the TF-gene network it returns for my 45 bovine mammary gland samples is sparse, with most edges exactly zero" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

### C15 class=vague gold=['DRAGON', 'LIONESS-DRAGON', 'SAMBAR', 'PANDA', 'LIONESS-PANDA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Analyze everything in glioma_bundle/ (expression.tsv, methylation.tsv and mutations.csv for 80 gliomas) and tell me what you find.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.98s)
● Matching registered workflows…
? Clarification needed
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C16 class=dont gold=[] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: From our 10x single-cell RNA-seq of differentiating iPSC-derived cardiomyocytes, I'd like to order the cells along a pseudotime trajectory and find the branch point where atrial and ventricular fates split.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.10s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "order the cells along a pseudotime trajectory" -- not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results. Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells.
2. "find the branch point where atrial and ventricular fates split" -- not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results. Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells.

No registered workflow produces these as you asked them, so none is offered for them as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

### C17 class=dont gold=['DRAGON'] core=DO ['DRAGON'] basis=results_given views=['verified_guidance']
Request: I want a transcript-metabolite partial-correlation network for 75 NAFLD liver biopsies in which the transcript layer's shrinkage is fixed at 0.3, as in our previous paper, while the metabolite layer's shrinkage is estimated from the data.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.13s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "I want a transcript-metabolite partial-correlation network" -- available from DRAGON.

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
```

### C18 class=dont gold=['CONDOR'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Run CONDOR directly on expr_kidney_fibrosis.tsv (gene-by-sample RNA-seq for 64 biopsies) to get gene communities. I don't have any motif or PPI files, just this expression table.
```text
● Classifying requested outcome…
● Matching registered workflows…
● Preparing next step…
What I understood you are asking for:
1. "gene communities" -- not available here as asked. You said "just this expression table"; CONDOR needs a regulator-gene network; every registered route to one (OTTER, PANDA, PUMA) needs an input you do not have: you said "motif"; OTTER needs a TF motif prior and no registered workflow or tool provides it.

No registered workflow can give this as you asked it (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

### C19 class=vague gold=['PUMA', 'LIONESS-PUMA', 'DRAGON', 'LIONESS-DRAGON', 'PANDA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Use the files in shared/hcc_project/ (expr_mrna.tsv, expr_mirna.tsv, motif_hs.txt and targetscan_pairs.txt) and run whichever NetZoo analysis is appropriate.
```text
● Classifying requested outcome…
✓ Guidance prepared
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C20 class=ask gold=['PANDA'] core=ASK ['PANDA'] basis=fact_agent views=['ask_facts']
Request: Run PANDA on tumour_profiles_v2.tsv with motif_hs.txt and ppi_hs.txt. Heads up: our lab saved two genes-by-tumours matrices under similar names, one with log2 expression and one with binary somatic-mutation calls, and I'm not sure which one this is.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.26s)
● Matching registered workflows…
? Clarification needed
Before I choose a workflow, please tell me:
- Is the file you want to use the gene-by-sample expression matrix with log2 expression?
  You wrote: "I'm not sure which one this is". PANDA's contract: "PANDA consumes a gene-by-sample expression matrix plus motif and PPI priors, or a validated adjusted gene-by-gene co-expression matrix through coexpression_file".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C21 class=ask gold=['CONDOR'] core=ASK ['CONDOR'] basis=fact_agent views=['ask_facts']
Request: Can CONDOR find communities in network_final.tsv, which a postdoc left behind when he moved on? It's a three-column source/target/weight table, but I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.28s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the network_final.tsv a TF-to-gene regulatory network?
  You wrote: "I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built". CONDOR's contract: "CONDOR consumes a weighted source-target bipartite edge list made from a validated regulator-gene network and returns community assignments with regulator-side and gene-side partitions".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C22 class=dont gold=[] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Call somatic SNVs and indels from tumour_07.bam against its matched normal_07.bam and give me a filtered VCF.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
What I understood you are asking for:
1. "give me a filtered VCF." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

### C23 class=vague gold=['DRAGON', 'LIONESS-DRAGON', 'PANDA', 'LIONESS-PANDA', 'COBRA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: We generated quite a lot of omics on a pig model of septic shock: whole-blood transcriptome, plasma proteome and a few hundred metabolites, sampled at baseline and at 24 hours. I'd like a systems-level view of what is going on in these animals. Where should we start?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.45s)
● Matching registered workflows…
✓ Guidance prepared
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C24 class=vague gold=['PUMA', 'LIONESS-PUMA', 'DRAGON', 'PANDA', 'LIONESS-COEXPRESSION'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Reviewers asked for 'a network analysis' of our placenta study. We have mRNA-seq and small-RNA-seq from 45 preeclampsia and control placentas. Honestly I don't know what kind of network they expect or what it's supposed to show. The two groups are roughly balanced and both libraries come from the same placentas; can you set something up that would satisfy them?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.56s)
● Matching registered workflows…
● Preparing next step…
What I understood you are asking for:
1. "Reviewers asked for 'a network analysis' of our placenta study." -- not matched to any registered workflow.
2. "can you set something up that would satisfy them?" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

### C25 class=do gold=['PUMA'] core=DO ['PUMA'] basis=results_given views=['verified_guidance']
Request: I'd like one regulatory network for my 70 colorectal tumours in which both transcription factors and microRNAs act as regulators of their target genes. I have the gene-by-sample expression matrix, a TF motif prior, a TF-TF PPI, a miRNA-target prior and a file listing the miRNAs, one ID per line, all of which appear in the prior. Nothing per-patient is needed; a single cohort-level network is what goes into the paper.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.06s)
● Matching registered workflows…
✓ Workflow — PUMA
✓ Guidance prepared
What I understood you are asking for:
1. "I'd like one regulatory network for my 70 colorectal tumours in which" -- available from PUMA.
2. "both transcription factors and microRNAs act as regulators" -- not matched to any registered workflow.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

Captured request parameters:

- `network_file`: for

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### C26 class=vague gold=['SAMBAR', 'PANDA', 'LIONESS-PANDA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: We have somatic mutation calls and RNA-seq for the same 90 bladder tumours. Is SAMBAR the right thing to run, or one of the network methods like PANDA? I'm open to whatever gives the most interesting result.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.54s)
● Matching registered workflows…
✓ Guidance prepared
I can't tell yet which result you want, so I have not chosen a workflow.

The registered workflows give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?

Nothing was selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C27 class=dont gold=['SAMBAR'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Can SAMBAR subtype our 210 hepatocellular carcinomas from the RNA-seq expression matrix? We don't have mutation calls for this cohort, only expression.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.89s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Can SAMBAR subtype our 210 hepatocellular carcinomas from the RNA-seq expression matrix?" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

### C28 class=do gold=['COBRA'] core=DO ['COBRA'] basis=results_given views=['verified_guidance']
Request: Our 140 skeletal-muscle RNA-seq samples (about 18,000 genes after filtering) were sequenced in three runs and come from donors of both sexes. I'd like to see how much of each gene pair's co-expression is associated with sequencing run versus sex, and get an adjusted gene-by-gene co-expression matrix out of it for later network work. Both covariates are already coded as numeric indicator columns in a design table whose rows are exactly the expression sample IDs.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.97s)
● Matching registered workflows…
✓ Workflow — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "see how much of each gene pair's co-expression is associated with sequencing run versus sex" -- available from COBRA.
2. "get an adjusted gene-by-gene co-expression matrix out of it for later network work" -- available from COBRA.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale. COBRA models co-expression as a function of sample covariates through conditional covariance estimation.

Captured request parameters:

- `expression_file`: sample

What you asked about:

- "get an adjusted gene-by-gene co-expression matrix out of it for later network work" — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

**COBRA**: Model covariate-associated gene co-expression with COBRA.

Routing-level input modality: expression matrix.

Method premise: remove or adjust technical batch effects; estimate how sample covariates change co-expression; model higher-order covariance or correlation structure; assess or remove hospital or site effects; assess or remove sequencing-batch effects.

COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

Required workflow inputs:

- `expression_file`: expression matrix
- `design_file`: sample covariate design matrix

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### C29 class=do gold=['CONDOR'] core=DO ['CONDOR'] basis=results_given views=['verified_guidance']
Request: I already have an aggregate TF-to-gene regulatory network for glioblastoma, exported as an edge list with source, target and weight columns; TF and gene IDs don't overlap and the weights were thresholded to be non-negative. Now I want to split it into communities of TFs and their target genes, with the TF-side and gene-side memberships reported separately.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.33s)
● Matching registered workflows…
✓ Workflow — CONDOR
✓ Guidance prepared
What I understood you are asking for:
1. "Now I want to split it into communities of TFs and their target genes, with the TF-side and gene-side memberships reported separately." -- available from CONDOR.

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
```

### C30 class=dont gold=['SAMBAR'] core=DECLINE [] basis=all_results_not_available views=['decline']
Request: Run SAMBAR on mut_pilot.csv (mutation counts for 5 cholangiocarcinomas) with exon_len.csv, cancer_genes.txt and hallmark.gmt, testing every subtype number from 2 through 8.
```text
● Classifying requested outcome…
● Matching registered workflows…
! Interpretation kept, but its quotes could not be matched to your wording
● Preparing next step…
What I understood you are asking for:
1. "Run SAMBAR" -- not available here as asked. SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled. SAMBAR itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

### C31 class=ask gold=['GIRAFFE'] core=ASK ['GIRAFFE'] basis=fact_agent views=['ask_facts']
Request: Can GIRAFFE give us signed TF-to-gene effects, activation versus repression, for our 40 atopic dermatitis skin biopsies? We have expression, a motif prior and a TF PPI. My supervisor's notes say we need those signed effects for each biopsy separately, but the grant text says one set of signed effects for the whole cohort, and I'm not sure which she actually wants.
```text
● Classifying requested outcome…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Does your supervisor want signed effects for each biopsy separately?
  You wrote: "My supervisor's notes say we need those signed effects for each biopsy separately, but the grant text says one set of signed effects for the whole cohort, and I'm not sure which she actually wants". GIRAFFE's contract: "It returns the aggregate TF-by-gene R matrix and a TF-by-sample TFA matrix".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C32 class=do gold=['DRAGON'] core=DO ['DRAGON'] basis=routed views=['verified_guidance']
Request: Will DRAGON take my paired plasma proteomics and metabolomics tables (both with a header, the same 85 participant IDs in the first column, samples in rows, complete continuous values with no NAs) and write the partial-correlation network as an edge list rather than a matrix?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.46s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
Selected path: **DRAGON**.

Your question asks for a cohort-level multi-omic network. **DRAGON** fits that result and scale. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage.

Captured request parameters:

- `network_file`: an

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
```

### C33 class=dont gold=['BONOBO'] core=DECLINE [] basis=all_results_not_available views=['decline']
Request: Can BONOBO run with sparsify on at a 0.01 confidence level and delta fixed at 0.5 for my 18 log-transformed, centered endometriosis samples?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.76s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "sparsify on at a 0.01 confidence level and delta fixed at 0.5 for my 18 log-transformed, centered" -- not available here as asked. BONOBO: with sparsify, delta must be above 0 and below 1/3, got 0.5. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

### C34 class=ask gold=['COBRA'] core=DO ['COBRA'] basis=results_given views=['hypothesis_routes']
Request: Our 96 brain RNA-seq samples (about 20,000 genes) were processed in four extraction batches and I want the batch effect removed. Depending on who you ask in the lab, that means a batch-corrected expression matrix to hand to other people, or batch-adjusted gene co-expression to build the regulatory network on, and I'm not sure which one I'm supposed to deliver. Batch is recorded per sample as numeric indicator columns.
```text
● Classifying requested outcome…
✓ Matched workflows — LIONESS-COEXPRESSION
✓ Guidance prepared
What I understood you are asking for:
1. "I want the batch effect removed." -- not matched to any registered workflow.
2. "a batch-corrected expression matrix to hand to other people" -- not matched to any registered workflow.
3. "batch-adjusted gene co-expression to build the regulatory network on" -- available from COBRA.
Not checked against the registered workflows: "Batch is recorded per sample as numeric indicator columns."
Not checked against the registered workflows: "processed in four extraction batches"

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

For “batch-corrected expression matrix”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

### C35 class=do gold=['SAMBAR'] core=UNCHECKED ['SAMBAR'] basis=run_held_unconfirmed views=['run_held']
Request: Run SAMBAR on mutations_ucec.csv (248 endometrial tumours in rows, genes in columns, non-negative mutation counts) with exon_lengths.csv, cancer_genes.txt and c2.cp.kegg.gmt (MSigDB format), all sharing the same gene symbols, and cluster the tumours into between 2 and 6 subtypes.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.14s)
● Matching registered workflows…
✓ Guidance prepared
You asked me to run SAMBAR, but the capability check could not confirm this turn that SAMBAR gives what you asked for. I have not planned the run.

Tell me to run SAMBAR anyway, and I will then find your input files and show a preview; nothing runs until you approve it.

No files were inspected and no analysis ran.
```

### C36 class=ask gold=['LIONESS-PANDA'] core=UNCHECKED ['LIONESS-PANDA', 'GIRAFFE'] basis=check_unconfirmed views=['capability_unconfirmed']
Request: For each of our 40 kidney cancer patients I need one number per transcription factor that captures that TF's regulatory strength in that patient, so we can relate it to survival. We have expression, a motif prior and a TF-TF PPI. I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or how active the TF is; my PI used both phrasings.
```text
● Classifying requested outcome…
✓ Guidance prepared
Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **LIONESS-PANDA** — produces: One TF-gene network per sample, plus the aggregate network.
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
```

### C37 class=vague gold=['DRAGON', 'LIONESS-DRAGON', 'OTTER', 'GIRAFFE'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: I've been reading about DRAGON, OTTER and GIRAFFE and they all sound powerful. Our lab has bulk transcriptomics, proteomics and some ATAC-seq peaks for a mouse model of pulmonary fibrosis, roughly 30 animals across three time points. Which of these should we apply, and what would we actually learn from each? We haven't settled on a specific hypothesis yet, and our PI wants something to show at the next lab meeting.
```text
● Classifying requested outcome…
? Clarification needed
The research comparison could not be validated; no workflow was selected.

The requested result is not specific enough to select a workflow. No workflow has been selected. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

Specify the requested result type and whether it should be aggregate or sample-specific. The workflow will be selected only after the result is clear; the captured inputs will be carried forward, and nothing will run yet.

No files were inspected and no analysis ran.
```

### C38 class=do gold=['GIRAFFE'] core=UNCHECKED ['GIRAFFE'] basis=check_unconfirmed views=['capability_unconfirmed']
Request: Can GIRAFFE estimate an activity score for every transcription factor in each of our 30 psoriasis skin samples? I have the gene-by-sample expression table, a TF-by-gene motif prior and a TF-TF PPI matrix with matching identifiers.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.43s)
● Matching registered workflows…
✓ Guidance prepared
Routing matched these registered workflows to your words, but the capability check did not confirm that any of them gives what you asked for:
- **GIRAFFE** — produces: A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples. Each TF's activity in each sample, estimated apart from its own mRNA level.

Compare what each produces with what you asked for. Ask again to re-run the check, or say which result you want and from which workflow.

No files were inspected and no analysis ran.
```

### C39 class=ask gold=['PUMA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Can PUMA model the small RNAs from our mouse testis small-RNA-seq as regulators alongside the TFs? I have expression for 24 testes, a motif prior, a PPI and a small-RNA-to-target prior, but the annotation isn't finished: the small RNAs we picked could be miRNAs or piRNAs, and I genuinely don't know which yet.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C40 class=do gold=['BONOBO'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Run BONOBO on expr_ms_lesions.tsv (27 multiple sclerosis lesion samples; log2-transformed and centered per gene; gene IDs in the first column, sample IDs in the header), but only write networks for samples MS_03, MS_11 and MS_19, saved as .csv files.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Input files recognized by filename (role not stated in the request, so it is still to be confirmed):

- `expression_file`: expr_ms_lesions.tsv

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C41 class=vague gold=['PANDA', 'LIONESS-PANDA', 'LIONESS-COEXPRESSION', 'OTTER', 'GIRAFFE', 'BONOBO'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: My PI told me to 'do the NetZoo thing, PANDA or LIONESS or something' on our zebrafish fin-regeneration RNA-seq before lab meeting. Which one should I run?
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C42 class=ask gold=['DRAGON'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Run DRAGON on expr_cll_layer.csv and methyl_cll_layer.csv (same 110 patient IDs in rows, no missing cells). One thing I'm unsure about: the methylation file is either the continuous beta values or the binarized methylated/unmethylated calls (0/1) that another group derived, and both versions were saved under that name.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Input files recognized by filename (role not stated in the request, so it is still to be confirmed):

- `expression_file`: expr_cll_layer.csv

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C43 class=ask gold=['LIONESS-PANDA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Run LIONESS-PANDA on expr_ra_synovium.tsv with motif_hs.txt and ppi_hs.txt to get a TF-to-gene network per column. I'm not sure which export this file is: the per-patient matrix (24 patients) or the version where a student averaged the patients into two columns, RA and control.
```text
● Classifying requested outcome…
! Semantic routing unavailable
The research comparison could not be validated; no workflow was selected.

The system could not validate its interpretation. This is not evidence that your question is unclear.

Input files recognized by filename (role not stated in the request, so it is still to be confirmed):

- `expression_file`: expr_ra_synovium.tsv
- `motif_file`: motif_hs.txt
- `ppi_file`: ppi_hs.txt

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C44 class=ask gold=['OTTER'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Run OTTER with seed_W_mm.tsv, ppi_tf_mm.tsv and coexp_liver.tsv; I have no expression file, only that co-expression file. I can't remember if coexp_liver.tsv is the full gene-by-gene correlation matrix for the cohort or the edge-by-sample table from our earlier LIONESS co-expression run.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Input files recognized by filename (role not stated in the request, so it is still to be confirmed):

- `ppi_file`: ppi_tf_mm.tsv

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C45 class=ask gold=['LIONESS-DRAGON'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: We'd like a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients, from 300 serum miRNAs and a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs). The catch: I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel, and the files are still on the CRO's server.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C46 class=dont gold=[] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: I want the list of genes differentially expressed between 12 drug-treated and 12 vehicle mouse hippocampi, with log2 fold changes and FDR-adjusted p-values like DESeq2 reports.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C47 class=dont gold=[] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Using bulk expression and clinical follow-up for 400 lung adenocarcinoma patients, I need a model that predicts each new patient's overall-survival risk, something like a penalized Cox model that outputs a risk score, which I can then lock and apply to an external validation cohort of 150 patients from another hospital without refitting. Ideally the score would also show which genes drive the risk.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C48 class=ask gold=['DRAGON'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Is DRAGON able to link fecal metabolomics with colon-biopsy transcriptomics for our IBS study? Both tables are complete and continuous, but the metabolomics came from the 2023 recruitment wave and the biopsies may have been taken from a different group of volunteers; I'm still waiting to hear from the clinic whether they're the same 58 people.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C49 class=vague gold=['PANDA', 'LIONESS-PANDA', 'OTTER', 'GIRAFFE'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: I've put tumor_expr.tsv, motifs.txt, ppi.txt and clinical.tsv in the folder. Do whatever makes sense with them and give me figures for the paper.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Input files recognized by filename (role not stated in the request, so it is still to be confirmed):

- `expression_file`: tumor_expr.tsv
- `motif_file`: motifs.txt
- `ppi_file`: ppi.txt

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C50 class=ask gold=['BONOBO'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: I need a gene co-expression network for each of our 9 periodontitis gingival biopsies, with a p-value for every edge so I can filter them per sample. The matrix (genes in rows, sample IDs in the header) has been mean-centered per gene, but it came from a collaborator and I can't tell whether the values were log-transformed before centering.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C51 class=do gold=['OTTER'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Is OTTER able to run on CPU in single precision with 150 iterations and a step size (eta) of 1e-4, writing the result as an edge list? Inputs would be expression for 60 breast tumours (header row, gene IDs in the first column), a TF-by-gene seed edge list, and a TF-TF PPI edge list whose TFs are exactly the seed's TFs.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C52 class=do gold=['BONOBO'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Can BONOBO build a co-expression network for each of my 6 rhesus macaque lymph node samples? The data are log2-transformed and centered per gene, with genes in rows and sample IDs in the header, and I'd like the per-sample matrices saved as HDF5 and computed in double precision.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C53 class=vague gold=['LIONESS-COEXPRESSION', 'BONOBO', 'PANDA', 'OTTER', 'COBRA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Could you help me see how genes are connected in my sorghum heat-stress experiment?
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C54 class=vague gold=['PANDA', 'LIONESS-PANDA', 'LIONESS-COEXPRESSION', 'COBRA', 'GIRAFFE', 'BONOBO'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Our grant renewal promises 'network-based insights' into Crohn's disease, and we have bulk RNA-seq from 150 ileal biopsies plus clinical data (disease activity, treatment, biopsy site). I need to propose a concrete analysis by Friday, but nobody has said what the network part should actually be or what question it should answer. We also have matched serology for most of the patients. What can we do?
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C55 class=do gold=['PANDA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Can PANDA build a single TF-to-gene regulatory network for our whole cohort of 48 mouse liver RNA-seq samples? I have the gene-by-sample expression matrix, a JASPAR-based motif prior and a mouse TF-TF PPI from STRING, all using the same gene symbols.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C56 class=ask gold=['SAMBAR'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Can SAMBAR subtype our 160 pediatric medulloblastomas? The sequencing core sent a samples-by-genes variant-count matrix along with gene lengths, a cancer-gene list and a KEGG GMT, but their README doesn't say whether the counts are tumour-only somatic mutations or germline variant calls, and I can't tell from the file itself.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C57 class=dont gold=['COBRA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: We ran a 48-gene NanoString inflammation panel on 600 rheumatoid arthritis patients recruited at four hospitals. I want to know how much of the co-expression between those 48 genes is associated with the hospital each sample came from, decomposed per covariate, with hospital coded as numeric indicator columns in a design table whose rows match the sample IDs exactly; each hospital contributed roughly 150 patients.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C58 class=do gold=['PANDA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Run PANDA on expr_ipf.tsv with motif_hg38.tsv and ppi_hs.tsv, but use cobra_out/adjusted_coexpression.tsv (COBRA's adjusted gene-by-gene matrix, already checked to have the same gene IDs and order as the expression file) as the co-expression input instead of PANDA's own Pearson correlation.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Input files recognized by filename (role not stated in the request, so it is still to be confirmed):

- `expression_file`: expr_ipf.tsv
- `motif_file`: motif_hg38.tsv
- `ppi_file`: ppi_hs.tsv
- `coexpression_file`: cobra_out/adjusted_coexpression.tsv

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C59 class=do gold=['LIONESS-PUMA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: Please run LIONESS-PUMA on expr_cll.tsv (36 CLL patients), motif_cll.txt, ppi_cll.txt, mir_targets.txt and mir_list.txt (one miRNA ID per line, every one present in the first column of mir_targets.txt) to get a TF/miRNA-to-gene network for every patient.
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Input files recognized by filename (role not stated in the request, so it is still to be confirmed):

- `expression_file`: expr_cll.tsv
- `motif_file`: motif_cll.txt
- `ppi_file`: ppi_cll.txt

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

### C60 class=vague gold=['LIONESS-COEXPRESSION', 'BONOBO', 'PANDA', 'LIONESS-PANDA', 'COBRA'] core=UNCHECKED [] basis=routing_failed views=['unresolved']
Request: I uploaded counts_week0.tsv, counts_week4.tsv and counts_week12.tsv from our vaccine trial. Can you run the right workflow on them?
```text
● Classifying requested outcome…
↻ Router output invalid — using deterministic fallback
! Semantic routing unavailable
The LLM router was unavailable, so no workflow was selected. (OpenAIConnectionError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

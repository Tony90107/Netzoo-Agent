# Review sheet

## ASK facts to check (facts-checked.json)

- C06 gold: Are the ~150 regulators transcription factors (with a TF-to-gene motif prior) rather than RNA-binding proteins?
  - asked: Is the list you have for transcription factors? (user: "I'm not sure which of the two lists I was given."; contract: "Build the source-target-weight edge list from a validated regulator-gene network; CONDOR does not consume the raw expression matrix directly.")
- C20 gold: Is tumour_profiles_v2.tsv the log2 expression matrix rather than the binary mutation matrix?
  - asked: Is the tumour_profiles_v2.tsv file a gene-by-sample expression matrix? (user: "two genes-by-tumours matrices under similar names, one with log2 expression and one with binary somatic-mutation calls, and I'm not sure which one this is."; contract: "PANDA consumes a gene-by-sample expression matrix plus motif and PPI priors, or a validated adjusted gene-by-gene co-expression matrix through coexpression_file.")
- C21 gold: Is network_final.tsv the TF-to-gene (regulator-to-gene) network rather than the gene-gene co-expression network?
  - asked: Is the network a TF-to-gene regulatory network from PANDA runs? (user: "I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built."; contract: "CONDOR consumes a weighted source-target bipartite edge list made from a validated regulator-gene network and returns community assignments with regulator-side and gene-side partitions.")
- C31 gold: Is one cohort-wide set of signed TF-to-gene effects what you need, rather than a separate signed matrix for each biopsy?
  - asked: Does your supervisor want signed effects for each biopsy separately? (user: "we need those signed effects for each biopsy separately, but the grant text says one set of signed effects for the whole cohort, and I'm not sure which she actually wants."; contract: "TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.")
- C34 gold: Do you need batch-adjusted gene-gene co-expression rather than a batch-corrected expression matrix?
  - asked: Do you need to deliver batch-adjusted gene co-expression to build the regulatory network? (user: "Depending on who you ask in the lab, that means a batch-corrected expression matrix to hand to other people, or batch-adjusted gene co-expression to build the regulatory network on, and I'm not sure which one I'm supposed to deliver."; contract: "COBRA consumes a gene-by-sample expression matrix and numeric sample covariates, then produces a covariate-associated covariance decomposition and a labeled adjusted gene-by-gene co-expression artifact.")
- C36 gold: By 'regulatory strength' do you mean how strongly each TF is wired to its targets in each patient, rather than each TF's activity level in each patient?
  - asked: Does 'regulatory strength' mean how active the TF is? (user: "I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or how active the TF is; my PI used both phrasings."; contract: "GIRAFFE: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.")
- C39 gold: Are the small-RNA regulators miRNAs (rather than piRNAs)?
  - asked: Are the small RNAs miRNAs? (user: "the small RNAs we picked could be miRNAs or piRNAs, and I genuinely don't know which yet."; contract: "Require one miRNA identifier per line and require every miRNA in prior column one.")
- C42 gold: Are the methylation values continuous (beta or M-values) rather than binarized 0/1 calls?
  - asked: Are the methylation values continuous beta values? (user: "the methylation file is either the continuous beta values or the binarized methylated/unmethylated calls (0/1)"; contract: "Values must be finite continuous numeric measurements.")
- C43 gold: Does expr_ra_synovium.tsv have one column per patient (24 samples) rather than two group-average columns?
  - said: Is the file a per-patient matrix with 24 patients? (user: "I'm not sure which export this file is: the per-patient matrix (24 patients) or the version where a student averaged the patients into two columns, RA and control."; contract: "Require at least three expression samples before execution.")
- C45 gold: Is the protein layer the 200-protein targeted panel rather than the 2,000-protein discovery panel?
  - asked: Is the proteomics panel the 200-protein targeted panel? (user: "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel"; contract: "LIONESS-DRAGON consumes exactly two paired sample-by-feature continuous omics tables, DRAGON's inputs, and produces the aggregate DRAGON matrix plus one partial-correlation network per sample, written as an edge-by-sample table (source, target, one column per sample) with layer-qualified node IDs.")
- C48 gold: Were both layers measured on the same 58 individuals, so the two tables share exactly the same sample IDs?
  - asked: Are the biopsies from the same 58 people as the metabolomics? (user: "the biopsies may have been taken from a different group of volunteers; I'm still waiting to hear from the clinic whether they're the same 58 people."; contract: "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven.")
- C50 gold: Were the expression values log-transformed before they were centered?
  - asked: Were the expression values log-transformed before centering? (user: "I can't tell whether the values were log-transformed before centering."; contract: "The agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression.")
- C56 gold: Are the counts somatic (tumour-acquired) mutations rather than germline variant calls?
  - asked: Are the counts tumour-only somatic mutations? (user: "whether the counts are tumour-only somatic mutations or germline variant calls"; contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV")

## Replies to spot-check (faithful-checked.json)

### C04 class=do gold=['LIONESS-PANDA'] core=DO ['LIONESS-PANDA'] basis=results_given views=['outcome_clarification']
Request: For each of our 25 diffuse large B-cell lymphoma patients I need that patient's own TF-to-gene regulatory network, built from the cohort's expression matrix together with a human motif prior and a TF PPI, so I can later compare each TF's targeting between responders and non-responders.
```text
FFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The human motif prior and TF PPI are used as additional inputs for the network inference.

For your question ("compare each TF's targeting between responders and non-responders"):
- **PANDA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### C06 class=ask gold=['PANDA', 'OTTER', 'GIRAFFE'] core=ASK ['CONDOR'] basis=fact_agent views=['ask_facts']
Request: I'd like a network of how about 150 regulators control their target genes across 60 hepatocellular carcinoma samples. I have the expression matrix, a PPI among those regulators, and a regulator-to-target prior from a collaborator's project, but that project studied both RNA-binding proteins and transcription factors, and I'm not sure which of the two lists I was given.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.25s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the list you have for transcription factors?
  You wrote: "I'm not sure which of the two lists I was given". CONDOR's contract: "Build the source-target-weight edge list from a validated regulator-gene network; CONDOR does not consume the raw expression matrix directly".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C07 class=do gold=['LIONESS-DRAGON'] core=DO ['LIONESS-DRAGON', 'SAMBAR'] basis=results_given views=['composition']
Request: We measured 180 circulating miRNAs (normalized, continuous qPCR values) and 45 plasma cytokines in the same 64 sepsis patients; both tables have samples in rows, identical patient IDs and no missing values. What I want is a separate network for every patient that links miRNAs and cytokines through partial correlations, within and across the two layers, so I can compare survivors with non-survivors patient by patient afterwards.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.83s)
● Matching registered workflows…
✓ Workflow — LIONESS-DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "a separate network for every patient that links miRNAs and cytokines through partial correlations" -- available from LIONESS-DRAGON or SAMBAR.
2. "within" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators. Every registered workflow estimates associations or model coefficients from observational data.
3. "across the two layers" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators. Every registered workflow estimates associations or model coefficients from observational data.
4. "compare survivors with non-survivors patient by patient afterwards" -- available from LIONESS-DRAGON's output plus a step you run outside NetZoo: A statistical test outside NetZoo.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 64 patients, 65 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

### C08 class=dont gold=['GIRAFFE'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Can GIRAFFE be run with my own optimizer settings? For our 52 rice leaf samples from the drought trial I want a learning rate of 1e-4, 2,000 iterations and a heavier weight on the PPI term in the loss, because in a pilot the package defaults gave a TF activity matrix that looked over-smoothed and I'd like to see whether these settings change that.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.51s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "a TF activity matrix" -- not available here: no registered workflow produces this. PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
2. "a learning rate of 1e-4" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "a learning rate of 1e-4" cannot be applied.
3. "2,000 iterations" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "2,000 iterations" cannot be applied.
4. "a heavier weight on the PPI term in the loss" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "a heavier weight on the PPI term in the loss" cannot be applied.

No registered workflow can give these as you asked them (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

### C09 class=vague gold=['BONOBO', 'LIONESS-COEXPRESSION', 'LIONESS-PANDA'] core=CLARIFY [] basis=result_open views=['clarify_goal']
Request: Should I go with BONOBO or LIONESS for my 20 Shank3 knockout and wild-type mouse cortex samples? I'm hoping to learn something about the knockout, but I haven't pinned down what yet.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.61s)
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

### C10 class=vague gold=['COBRA', 'CONDOR'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Should I be using COBRA or CONDOR on our lupus nephritis cohort? I keep seeing both names in NetZoo papers and I'm not sure what either would give me.
```text
● Classifying requested outcome…
✓ Guidance prepared
What I understood you are asking for:
1. "Should I be using COBRA" -- not matched to any registered workflow.
2. "Should I be using" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

### C11 class=ask gold=['LIONESS-PANDA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Run the TF network inference on expr_alzheimer.tsv (88 donors: 44 AD, 44 controls), motifs_hg38.txt and ppi_tf.txt. The analysis plan just says 'a network for each AD and control', and I can't tell if that means one network per diagnostic group or one network per donor; the person who wrote it is on leave until next month.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.27s)
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

### C12 class=vague gold=['LIONESS-COEXPRESSION', 'BONOBO', 'PANDA', 'COBRA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Please run the network analysis on expr_sle_monocytes.tsv and send me the results.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.96s)
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

### C13 class=dont gold=['OTTER'] core=DECLINE [] basis=full_gap views=['decline']
Request: Run OTTER on expr_t2d_islets.tsv, seed_W.tsv and ppi_tf.tsv with lam set to 1.5, so co-expression gets even more weight than PPI.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.41s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "Run OTTER on expr_t2d_islets.tsv, seed_W.tsv and ppi_tf.tsv with lam set to 1.5, so co-expression gets even more weight than PPI." -- not available here as asked. OTTER's lam must be between 0 and 1; "1.5" is not. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

### C14 class=dont gold=['OTTER'] core=DO ['OTTER'] basis=routed views=['verified_guidance']
Request: Can I add an L1 (lasso) sparsity penalty to OTTER's objective so that the TF-gene network it returns for my 45 bovine mammary gland samples is sparse, with most edges exactly zero?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.07s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
Assumptions behind this recommendation (not confirmed facts):

- The user is considering using an L1 penalty to achieve sparsity in the network.

**OTTER** fits the result you describe, but it needs a motif prior and a PPI network, which you said you do not have.

Your question asks for a cohort-level regulatory network. **OTTER** fits that result and scale.

**OTTER** — Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

Required workflow inputs:

- `motif_file`: motif/prior
- `ppi_file`: PPI network

Required alternative (provide one):

- `expression_file`: expression matrix
- `coexpression_file`: adjusted co-expression matrix

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Runtime limits:

- `computing`: current runtime unavailable: gpu; use `computing=cpu`.

Ask for the workflow's controls and defaults if you want to set them.

**What your data allows.** OTTER also needs an expression matrix or adjusted co-expression matrix. OTTER needs a motif prior and a PPI network, which you said you do not have ("my 45 bovine mammary gland samples").

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### C15 class=vague gold=['DRAGON', 'LIONESS-DRAGON', 'SAMBAR', 'PANDA', 'LIONESS-PANDA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Analyze everything in glioma_bundle/ (expression.tsv, methylation.tsv and mutations.csv for 80 gliomas) and tell me what you find.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.59s)
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

### C16 class=dont gold=[] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: From our 10x single-cell RNA-seq of differentiating iPSC-derived cardiomyocytes, I'd like to order the cells along a pseudotime trajectory and find the branch point where atrial and ventricular fates split.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.01s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "order the cells along a pseudotime trajectory" -- not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results. Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells.
2. "find the branch point where atrial and ventricular fates split" -- not available here: no registered workflow produces this. No registered workflow models how the system changes from one time point to the next; time points can only be compared as separate results. Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells.

No registered workflow produces these as you asked them, so none is offered for them as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

### C17 class=dont gold=['DRAGON'] core=DO ['DRAGON'] basis=results_given views=['outcome_clarification']
Request: I want a transcript-metabolite partial-correlation network for 75 NAFLD liver biopsies in which the transcript layer's shrinkage is fixed at 0.3, as in our previous paper, while the metabolite layer's shrinkage is estimated from the data.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.33s)
● Matching registered workflows…
✓ Matched workflows — DRAGON
? Clarification needed
What I understood you are asking for:
1. "a transcript-metabolite partial-correlation network for 75 NAFLD liver biopsies" -- available from DRAGON.

It sounds like you want aggregate multi omic network.

Registered method and input/output fit:
- **Multi omic network — DRAGON**
  - Registered purpose: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.
  - Method premise: infer conditional associations using partial correlation; DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
  - Mathematical interpretation: DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.
  - Required inputs: all of: DRAGON omics layer 1, DRAGON omics layer 2.
  - Declared output: multi omic network (cohort-level aggregate).

Unconfirmed assumptions in my current interpretation (please correct me if needed):
- The shrinkage parameter for the transcript layer is fixed at 0.3 as per the user's previous paper.
- The shrinkage parameter for the metabolite layer is estimated from the data.

What supported NetZoo result do you want the agent to produce?

No files were inspected and no analysis ran.
```

### C18 class=dont gold=['CONDOR'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Run CONDOR directly on expr_kidney_fibrosis.tsv (gene-by-sample RNA-seq for 64 biopsies) to get gene communities. I don't have any motif or PPI files, just this expression table.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.19s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "get gene communities" -- not available here as asked. You said "just this expression table"; CONDOR needs a regulator-gene network; every registered route to one (OTTER, PANDA, PUMA) needs an input you do not have: you said "I don't have any motif or PPI files"; OTTER needs a TF motif prior and no registered workflow or tool provides it.

No registered workflow can give this as you asked it (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

### C19 class=vague gold=['PUMA', 'LIONESS-PUMA', 'DRAGON', 'LIONESS-DRAGON', 'PANDA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: Use the files in shared/hcc_project/ (expr_mrna.tsv, expr_mirna.tsv, motif_hs.txt and targetscan_pairs.txt) and run whichever NetZoo analysis is appropriate.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.64s)
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

### C20 class=ask gold=['PANDA'] core=ASK ['PANDA'] basis=fact_agent views=['ask_facts']
Request: Run PANDA on tumour_profiles_v2.tsv with motif_hs.txt and ppi_hs.txt. Heads up: our lab saved two genes-by-tumours matrices under similar names, one with log2 expression and one with binary somatic-mutation calls, and I'm not sure which one this is.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.08s)
● Matching registered workflows…
? Clarification needed
Before I choose a workflow, please tell me:
- Is the tumour_profiles_v2.tsv file a gene-by-sample expression matrix?
  You wrote: "two genes-by-tumours matrices under similar names, one with log2 expression and one with binary somatic-mutation calls, and I'm not sure which one this is". PANDA's contract: "PANDA consumes a gene-by-sample expression matrix plus motif and PPI priors, or a validated adjusted gene-by-gene co-expression matrix through coexpression_file".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C21 class=ask gold=['CONDOR'] core=ASK ['CONDOR'] basis=fact_agent views=['ask_facts']
Request: Can CONDOR find communities in network_final.tsv, which a postdoc left behind when he moved on? It's a three-column source/target/weight table, but I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.14s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the network a TF-to-gene regulatory network from PANDA runs?
  You wrote: "I don't know whether it's the TF-to-gene regulatory network from his PANDA runs or the gene-gene co-expression network he also built". CONDOR's contract: "CONDOR consumes a weighted source-target bipartite edge list made from a validated regulator-gene network and returns community assignments with regulator-side and gene-side partitions".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C22 class=dont gold=[] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Call somatic SNVs and indels from tumour_07.bam against its matched normal_07.bam and give me a filtered VCF.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.08s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Call somatic SNVs and indels from tumour_07.bam against its matched normal_07.bam and give me a filtered VCF." -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

### C23 class=vague gold=['DRAGON', 'LIONESS-DRAGON', 'PANDA', 'LIONESS-PANDA', 'COBRA'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: We generated quite a lot of omics on a pig model of septic shock: whole-blood transcriptome, plasma proteome and a few hundred metabolites, sampled at baseline and at 24 hours. I'd like a systems-level view of what is going on in these animals. Where should we start?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.37s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "a systems-level view of what is going on in these animals" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

### C24 class=vague gold=['PUMA', 'LIONESS-PUMA', 'DRAGON', 'PANDA', 'LIONESS-COEXPRESSION'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Reviewers asked for 'a network analysis' of our placenta study. We have mRNA-seq and small-RNA-seq from 45 preeclampsia and control placentas. Honestly I don't know what kind of network they expect or what it's supposed to show. The two groups are roughly balanced and both libraries come from the same placentas; can you set something up that would satisfy them?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.89s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "'a network analysis' of our placenta study" -- not matched to any registered workflow.
2. "can you set something up that would satisfy them?" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

### C26 class=vague gold=['SAMBAR', 'PANDA', 'LIONESS-PANDA'] core=DO ['PANDA', 'OTTER'] basis=results_given views=['hypothesis_routes']
Request: We have somatic mutation calls and RNA-seq for the same 90 bladder tumours. Is SAMBAR the right thing to run, or one of the network methods like PANDA? I'm open to whatever gives the most interesting result.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (6.55s)
● Matching registered workflows…
✓ Matched workflows — PANDA, OTTER
✓ Guidance prepared
What I understood you are asking for:
1. "Is SAMBAR the right thing to run" -- not matched to any registered workflow.
2. "one of the network methods like PANDA" -- available from PANDA.
3. "whatever gives the most interesting result" -- available from PANDA or OTTER.

There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “network methods like PANDA”:

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

For “network methods like PANDA”:

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

For “SAMBAR”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

**What your data allows.** Your request names expression data and mutation data. PANDA and OTTER need a motif prior and a PPI network, which you said you do not have ("We have somatic mutation calls and RNA-seq for the same 90 bladder tumours"). With expression data and mutation data alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

### C27 class=dont gold=['SAMBAR'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Can SAMBAR subtype our 210 hepatocellular carcinomas from the RNA-seq expression matrix? We don't have mutation calls for this cohort, only expression.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.78s)
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
✓ Interpreted requested outcome (2.50s)
● Matching registered workflows…
✓ Workflow — COBRA
✓ Guidance prepared
What I understood you are asking for:
1. "see how much of each gene pair's co-expression is associated with sequencing run versus sex" -- available from COBRA.
2. "get an adjusted gene-by-gene co-expression matrix out of it for later network work" -- available from COBRA's output plus a step you run outside NetZoo: Pass adjusted_coexpression to PANDA, PUMA or OTTER (registered handoff) after identifier checks.

Selected path: **COBRA**.

Your question asks for a cohort-level co-expression network. **COBRA** fits that result and scale. COBRA models co-expression as a function of sample covariates through conditional covariance estimation.

Captured request parameters:

- `expression_file`: sample

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
✓ Interpreted requested outcome (2.82s)
● Matching registered workflows…
✓ Workflow — CONDOR
✓ Guidance prepared
What I understood you are asking for:
1. "split it into communities of TFs and their target genes, with the TF-side and gene-side memberships reported separately" -- available from CONDOR.

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

### C30 class=dont gold=['SAMBAR'] core=DECLINE [] basis=full_gap views=['decline']
Request: Run SAMBAR on mut_pilot.csv (mutation counts for 5 cholangiocarcinomas) with exon_len.csv, cancer_genes.txt and hallmark.gmt, testing every subtype number from 2 through 8.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.97s)
● Matching registered workflows…
✓ Workflow — SAMBAR
✓ Guidance prepared
What I understood you are asking for:
1. "Run SAMBAR on mut_pilot.csv (mutation counts for 5 cholangiocarcinomas) with exon_len.csv, cancer_genes.txt and hallmark.gmt, testing every subtype number from 2 through 8." -- not available here as asked. SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled. SAMBAR itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

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
  You wrote: "we need those signed effects for each biopsy separately, but the grant text says one set of signed effects for the whole cohort, and I'm not sure which she actually wants". GIRAFFE's contract: "TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C32 class=do gold=['DRAGON'] core=DO ['DRAGON'] basis=results_given views=['verified_guidance']
Request: Will DRAGON take my paired plasma proteomics and metabolomics tables (both with a header, the same 85 participant IDs in the first column, samples in rows, complete continuous values with no NAs) and write the partial-correlation network as an edge list rather than a matrix?
```text
quested outcome…
✓ Interpreted requested outcome (2.54s)
● Matching registered workflows…
✓ Workflow — DRAGON
✓ Guidance prepared
What I understood you are asking for:
1. "write the partial-correlation network as an edge list rather than a matrix" -- available from DRAGON.

Assumptions behind this recommendation (not confirmed facts):

- The tool can handle both proteomics and metabolomics data.
- The output format as an edge list is supported.

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
✓ Interpreted requested outcome (5.27s)
● Matching registered workflows…
! Fallback recommendation — not an exact semantic match
✓ Guidance prepared
What I understood you are asking for:
1. "sparsify on at a 0.01 confidence level and delta fixed at 0.5 for my 18 log-transformed, centered endometriosis samples" -- not available here as asked. BONOBO: with sparsify, delta must be above 0 and below 1/3, got 0.5. BONOBO itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

### C34 class=ask gold=['COBRA'] core=ASK ['COBRA'] basis=fact_agent views=['ask_facts']
Request: Our 96 brain RNA-seq samples (about 20,000 genes) were processed in four extraction batches and I want the batch effect removed. Depending on who you ask in the lab, that means a batch-corrected expression matrix to hand to other people, or batch-adjusted gene co-expression to build the regulatory network on, and I'm not sure which one I'm supposed to deliver. Batch is recorded per sample as numeric indicator columns.
```text
● Classifying requested outcome…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Do you need to deliver batch-adjusted gene co-expression to build the regulatory network?
  You wrote: "Depending on who you ask in the lab, that means a batch-corrected expression matrix to hand to other people, or batch-adjusted gene co-expression to build the regulatory network on, and I'm not sure which one I'm supposed to deliver". COBRA's contract: "COBRA consumes a gene-by-sample expression matrix and numeric sample covariates, then produces a covariate-associated covariance decomposition and a labeled adjusted gene-by-gene co-expression artifact".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C35 class=do gold=['SAMBAR'] core=DO ['SAMBAR'] basis=run views=['needs_input']
Request: Run SAMBAR on mutations_ucec.csv (248 endometrial tumours in rows, genes in columns, non-negative mutation counts) with exon_lengths.csv, cancer_genes.txt and c2.cp.kegg.gmt (MSigDB format), all sharing the same gene symbols, and cluster the tumours into between 2 and 6 subtypes.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.65s)
● Matching registered workflows…
✓ Workflow — SAMBAR
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- SAMBAR inputs: error: mutation_file must be an existing regular file: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/mutations_ucec.csv
- SAMBAR inputs: error: exon_size_file must be an existing regular file: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/exon_lengths.csv
- SAMBAR inputs: error: cancer_gene_file must be an existing regular file: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/cancer_genes.txt
- SAMBAR inputs: error: pathway_file must be an existing regular file: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/c2.cp.kegg.gmt

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume cj-g4o2-C35-1 after preparing the answer.
```

### C36 class=ask gold=['LIONESS-PANDA'] core=ASK ['GIRAFFE'] basis=fact_agent views=['ask_facts']
Request: For each of our 40 kidney cancer patients I need one number per transcription factor that captures that TF's regulatory strength in that patient, so we can relate it to survival. We have expression, a motif prior and a TF-TF PPI. I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or how active the TF is; my PI used both phrasings.
```text
● Classifying requested outcome…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Does 'regulatory strength' mean how active the TF is?
  You wrote: "I'm honestly not sure whether 'regulatory strength' here should mean how strongly the TF is wired to its targets or how active the TF is; my PI used both phrasings". GIRAFFE's contract: "GIRAFFE: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C37 class=vague gold=['DRAGON', 'LIONESS-DRAGON', 'OTTER', 'GIRAFFE'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: I've been reading about DRAGON, OTTER and GIRAFFE and they all sound powerful. Our lab has bulk transcriptomics, proteomics and some ATAC-seq peaks for a mouse model of pulmonary fibrosis, roughly 30 animals across three time points. Which of these should we apply, and what would we actually learn from each? We haven't settled on a specific hypothesis yet, and our PI wants something to show at the next lab meeting.
```text
● Classifying requested outcome…
✓ Matched workflows — DRAGON, CONDOR
✓ Guidance prepared
What I understood you are asking for:
1. "DRAGON, OTTER and GIRAFFE" -- not matched to any registered workflow.
2. "bulk transcriptomics, proteomics and some ATAC-seq peaks for a mouse model of pulmonary fibrosis, roughly 30 animals across three time points" -- not matched to any registered workflow.
3. "Which of these should we apply" -- not matched to any registered workflow.
4. "what would we actually learn from each" -- not matched to any registered workflow.
5. "something to show at the next lab meeting" -- not matched to any registered workflow.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

### C39 class=ask gold=['PUMA'] core=ASK ['PUMA'] basis=fact_agent views=['ask_facts']
Request: Can PUMA model the small RNAs from our mouse testis small-RNA-seq as regulators alongside the TFs? I have expression for 24 testes, a motif prior, a PPI and a small-RNA-to-target prior, but the annotation isn't finished: the small RNAs we picked could be miRNAs or piRNAs, and I genuinely don't know which yet.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (4.62s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the small RNAs miRNAs?
  You wrote: "the small RNAs we picked could be miRNAs or piRNAs, and I genuinely don't know which yet". PUMA's contract: "Require one miRNA identifier per line and require every miRNA in prior column one".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C40 class=do gold=['BONOBO'] core=DO ['BONOBO'] basis=run_held views=['run_held']
Request: Run BONOBO on expr_ms_lesions.tsv (27 multiple sclerosis lesion samples; log2-transformed and centered per gene; gene IDs in the first column, sample IDs in the header), but only write networks for samples MS_03, MS_11 and MS_19, saved as .csv files.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.75s)
● Matching registered workflows…
✓ Workflow — BONOBO
✓ Guidance prepared
What I understood you are asking for:
1. "Run BONOBO on expr_ms_lesions.tsv" -- available from BONOBO.
2. "log2-transformed" -- not available here as asked. BONOBO's log_transformed needs an explicit true or false value; "log2-transformed" is unresolved.
3. "centered per gene" -- not available here as asked. BONOBO's centered needs an explicit true or false value; "centered per gene" is unresolved.
4. "gene IDs in the first column, sample IDs in the header" -- not available here as asked. BONOBO's genes_axis requires one of auto, rows and columns; "gene IDs in the first column, sample IDs in the header" does not identify one allowed choice.
5. "but only write networks for samples MS_03, MS_11 and MS_19, saved as .csv files" -- available from BONOBO.
Not checked against the registered workflows: "only write networks for samples MS_03, MS_11 and MS_19"
Not checked against the registered workflows: "but only write networks for samples MS_03, MS_11 and MS_19"

You asked me to run BONOBO. It covers "Run BONOBO on expr_ms_lesions.tsv" and "but only write networks for samples MS_03, MS_11 and MS_19, saved as .csv files", but no registered workflow covers "log2-transformed", "centered per gene" and "gene IDs in the first column, sample IDs in the header", so the run would do only part of what you asked. I have not planned it.

Tell me to run BONOBO for the part it gives, and I will then find your input files and show a preview; nothing runs until you approve it.

No files were inspected and no analysis ran.
```

### C41 class=vague gold=['PANDA', 'LIONESS-PANDA', 'LIONESS-COEXPRESSION', 'OTTER', 'GIRAFFE', 'BONOBO'] core=ASK ['LIONESS-PANDA', 'PANDA'] basis=fact_agent views=['ask_facts']
Request: My PI told me to 'do the NetZoo thing, PANDA or LIONESS or something' on our zebrafish fin-regeneration RNA-seq before lab meeting. Which one should I run?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.45s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Do you want to infer sample-specific networks using LIONESS?
  You wrote: "PANDA or LIONESS". LIONESS-PANDA's contract: "LIONESS-PANDA uses the original gene-by-sample expression matrix, motif and PPI priors to internally infer the aggregate PANDA network and derive sample-specific TF-to-gene networks".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C42 class=ask gold=['DRAGON'] core=ASK ['DRAGON'] basis=fact_agent views=['ask_facts']
Request: Run DRAGON on expr_cll_layer.csv and methyl_cll_layer.csv (same 110 patient IDs in rows, no missing cells). One thing I'm unsure about: the methylation file is either the continuous beta values or the binarized methylated/unmethylated calls (0/1) that another group derived, and both versions were saved under that name.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.62s)
● Matching registered workflows…
? Clarification needed
Before I choose a workflow, please tell me:
- Are the methylation values continuous beta values?
  You wrote: "the methylation file is either the continuous beta values or the binarized methylated/unmethylated calls (0/1)". DRAGON's contract: "Values must be finite continuous numeric measurements".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C43 class=ask gold=['LIONESS-PANDA'] core=DO ['LIONESS-PANDA'] basis=run views=['needs_input']
Request: Run LIONESS-PANDA on expr_ra_synovium.tsv with motif_hs.txt and ppi_hs.txt to get a TF-to-gene network per column. I'm not sure which export this file is: the per-patient matrix (24 patients) or the version where a student averaged the patients into two columns, RA and control.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.80s)
● Matching registered workflows…
✓ Workflow — LIONESS-PANDA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/expr_ra_synovium.tsv
- PANDA/PUMA inputs: error: motif file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/motif_hs.txt
- PANDA/PUMA inputs: error: PPI file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/ppi_hs.txt

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume cj-g4o2-C43-1 after preparing the answer.
```

### C44 class=ask gold=['OTTER'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Run OTTER with seed_W_mm.tsv, ppi_tf_mm.tsv and coexp_liver.tsv; I have no expression file, only that co-expression file. I can't remember if coexp_liver.tsv is the full gene-by-gene correlation matrix for the cohort or the edge-by-sample table from our earlier LIONESS co-expression run.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.86s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "Run OTTER with seed_W_mm.tsv, ppi_tf_mm.tsv and coexp_liver.tsv" -- not available here as asked. You said "I have no expression file, only that co-expression file."; OTTER needs a TF motif prior and no registered workflow or tool provides it. OTTER does not give it: no per-sample OTTER is registered.

No registered workflow can give this as you asked it (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

### C45 class=ask gold=['LIONESS-DRAGON'] core=ASK ['LIONESS-DRAGON'] basis=fact_agent views=['ask_facts']
Request: We'd like a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients, from 300 serum miRNAs and a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs). The catch: I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel, and the files are still on the CRO's server.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.04s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Is the proteomics panel the 200-protein targeted panel?
  You wrote: "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel". LIONESS-DRAGON's contract: "LIONESS-DRAGON consumes exactly two paired sample-by-feature continuous omics tables, DRAGON's inputs, and produces the aggregate DRAGON matrix plus one partial-correlation network per sample, written as an edge-by-sample table (source, target, one column per sample) with layer-qualified node IDs".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C46 class=dont gold=[] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: I want the list of genes differentially expressed between 12 drug-treated and 12 vehicle mouse hippocampi, with log2 fold changes and FDR-adjusted p-values like DESeq2 reports.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.03s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "the list of genes differentially expressed between 12 drug-treated and 12 vehicle mouse hippocampi, with log2 fold changes and FDR-adjusted p-values like DESeq2 reports" -- not available here: no registered workflow produces this. COBRA does not give it: COBRA decomposes gene-pair co-expression; it does not test single genes' expression.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

### C47 class=dont gold=[] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Using bulk expression and clinical follow-up for 400 lung adenocarcinoma patients, I need a model that predicts each new patient's overall-survival risk, something like a penalized Cox model that outputs a risk score, which I can then lock and apply to an external validation cohort of 150 patients from another hospital without refitting. Ideally the score would also show which genes drive the risk.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.63s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "a model that predicts each new patient's overall-survival risk" -- not available here as asked. NetZoo has no registered method or variant "something like a penalized Cox model". No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
2. "the score would also show which genes drive the risk" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

No registered workflow can give these as you asked them (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

### C48 class=ask gold=['DRAGON'] core=ASK ['DRAGON'] basis=fact_agent views=['ask_facts']
Request: Is DRAGON able to link fecal metabolomics with colon-biopsy transcriptomics for our IBS study? Both tables are complete and continuous, but the metabolomics came from the 2023 recruitment wave and the biopsies may have been taken from a different group of volunteers; I'm still waiting to hear from the clinic whether they're the same 58 people.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.97s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the biopsies from the same 58 people as the metabolomics?
  You wrote: "the biopsies may have been taken from a different group of volunteers; I'm still waiting to hear from the clinic whether they're the same 58 people". DRAGON's contract: "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C49 class=vague gold=['PANDA', 'LIONESS-PANDA', 'OTTER', 'GIRAFFE'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: I've put tumor_expr.tsv, motifs.txt, ppi.txt and clinical.tsv in the folder. Do whatever makes sense with them and give me figures for the paper.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.24s)
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

### C50 class=ask gold=['BONOBO'] core=ASK ['BONOBO'] basis=fact_agent views=['ask_facts']
Request: I need a gene co-expression network for each of our 9 periodontitis gingival biopsies, with a p-value for every edge so I can filter them per sample. The matrix (genes in rows, sample IDs in the header) has been mean-centered per gene, but it came from a collaborator and I can't tell whether the values were log-transformed before centering.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.06s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Were the expression values log-transformed before centering?
  You wrote: "I can't tell whether the values were log-transformed before centering". BONOBO's contract: "The agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C51 class=do gold=['OTTER'] core=DO ['OTTER'] basis=routed views=['workflow_contract']
Request: Is OTTER able to run on CPU in single precision with 150 iterations and a step size (eta) of 1e-4, writing the result as an edge list? Inputs would be expression for 60 breast tumours (header row, gene IDs in the first column), a TF-by-gene seed edge list, and a TF-TF PPI edge list whose TFs are exactly the seed's TFs.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.67s)
● Matching registered workflows…
✓ Workflow — OTTER
✓ Guidance prepared
OTTER: Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints.
Registered required inputs: motif_file, ppi_file, output_file.
Registered workflow controls: output_format (type=enum, default='matrix'), computing (type=enum, default='cpu'), precision (type=enum, default='double'), lam (type=number, default=0.035), gamma (type=number, default=0.335), iterations (type=integer, default=60), eta (type=number, default=1e-05), bexp (type=number, default=1.0).
Output: aggregate TF-to-gene regulatory networks.

No files were inspected and no analysis ran.
```

### C52 class=do gold=['BONOBO'] core=DO ['BONOBO'] basis=run views=['needs_input']
Request: Can BONOBO build a co-expression network for each of my 6 rhesus macaque lymph node samples? The data are log2-transformed and centered per gene, with genes in rows and sample IDs in the header, and I'd like the per-sample matrices saved as HDF5 and computed in double precision.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.80s)
● Matching registered workflows…
✓ Workflow — BONOBO
● Preparing next step…
? Clarification needed
  Input required

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.

Select input 1 of 1: Expression matrix (expression_file)
Enter a candidate number or a full path.
Enter the full path.
Selection > 
Run the command again with --resume cj-g4o2-C52-1 after preparing the answer.
```

### C53 class=vague gold=['LIONESS-COEXPRESSION', 'BONOBO', 'PANDA', 'OTTER', 'COBRA'] core=DO ['LIONESS-COEXPRESSION', 'BONOBO'] basis=results_given views=['outcome_clarification']
Request: Could you help me see how genes are connected in my sorghum heat-stress experiment?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.56s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "how genes are connected in my sorghum heat-stress experiment" -- available from LIONESS-COEXPRESSION or BONOBO.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### C54 class=vague gold=['PANDA', 'LIONESS-PANDA', 'LIONESS-COEXPRESSION', 'COBRA', 'GIRAFFE', 'BONOBO'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: Our grant renewal promises 'network-based insights' into Crohn's disease, and we have bulk RNA-seq from 150 ileal biopsies plus clinical data (disease activity, treatment, biopsy site). I need to propose a concrete analysis by Friday, but nobody has said what the network part should actually be or what question it should answer. We also have matched serology for most of the patients. What can we do?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.64s)
● Matching registered workflows…
● Preparing next step…
What I understood you are asking for:
1. "What can we do?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
```

### C55 class=do gold=['PANDA'] core=DO ['PANDA'] basis=results_given views=['verified_guidance']
Request: Can PANDA build a single TF-to-gene regulatory network for our whole cohort of 48 mouse liver RNA-seq samples? I have the gene-by-sample expression matrix, a JASPAR-based motif prior and a mouse TF-TF PPI from STRING, all using the same gene symbols.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.92s)
● Matching registered workflows…
✓ Workflow — PANDA
✓ Guidance prepared
What I understood you are asking for:
1. "Can PANDA build a single TF-to-gene regulatory network for our whole cohort of 48 mouse liver RNA-seq samples?" -- available from PANDA.

Assumptions behind this recommendation (not confirmed facts):

- The provided motif prior and TF-TF PPI are compatible with the expression matrix.

Selected path: **PANDA**.

Your question asks for a cohort-level regulatory network. **PANDA** fits that result and scale.

**PANDA** — Infer an aggregate TF-to-gene regulatory network with PANDA. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

Required workflow inputs:

- `expression_file`: expression matrix
- `motif_file`: motif/prior
- `ppi_file`: PPI network

Outputs:

- `regulatory_network`: Inferred regulator-to-target associations.

Ask for the workflow's controls and defaults if you want to set them.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### C56 class=ask gold=['SAMBAR'] core=ASK ['SAMBAR'] basis=fact_agent views=['ask_facts']
Request: Can SAMBAR subtype our 160 pediatric medulloblastomas? The sequencing core sent a samples-by-genes variant-count matrix along with gene lengths, a cancer-gene list and a KEGG GMT, but their README doesn't say whether the counts are tumour-only somatic mutations or germline variant calls, and I can't tell from the file itself.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (5.91s)
● Matching registered workflows…
✓ Guidance prepared
Before I choose a workflow, please tell me:
- Are the counts tumour-only somatic mutations?
  You wrote: "whether the counts are tumour-only somatic mutations or germline variant calls". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

### C57 class=dont gold=['COBRA'] core=DECLINE [] basis=full_gap views=['capability_check_gap']
Request: We ran a 48-gene NanoString inflammation panel on 600 rheumatoid arthritis patients recruited at four hospitals. I want to know how much of the co-expression between those 48 genes is associated with the hospital each sample came from, decomposed per covariate, with hospital coded as numeric indicator columns in a design table whose rows match the sample IDs exactly; each hospital contributed roughly 150 patients.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (2.90s)
● Matching registered workflows…
✓ Guidance prepared
What I understood you are asking for:
1. "how much of the co-expression between those 48 genes is associated with the hospital each sample came from, decomposed per covariate" -- not available here as asked. COBRA requires more genes than samples; the request has 48 genes and 600 samples. PANDA does not give it: the PPI network is an input of possible TF cooperation. PANDA refines a cooperativity matrix internally, but the executor does not save it, and it is not a measurement of physical complexes or stoichiometry.
2. "rows match the sample IDs exactly" -- not available here as asked. NetZoo runs COBRA with its package defaults and passes no settings to it, so "rows match the sample IDs exactly" cannot be applied.

No registered workflow can give these as you asked them (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

### C58 class=do gold=['PANDA'] core=DO ['PANDA'] basis=run views=['needs_input']
Request: Run PANDA on expr_ipf.tsv with motif_hg38.tsv and ppi_hs.tsv, but use cobra_out/adjusted_coexpression.tsv (COBRA's adjusted gene-by-gene matrix, already checked to have the same gene IDs and order as the expression file) as the co-expression input instead of PANDA's own Pearson correlation.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.60s)
● Matching registered workflows…
✓ Workflow — PANDA
● Preparing next step…
? Clarification needed
  Input required

Input preflight failed, so the Work Plan is not ready:

- PANDA/PUMA inputs: error: expression file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/expr_ipf.tsv
- PANDA/PUMA inputs: error: motif file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/motif_hg38.tsv
- PANDA/PUMA inputs: error: PPI file does not exist: /Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/ppi_hs.tsv
- coexpression_file: co-expression matrix could not be read: [Errno 2] No such file or directory: '/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-core-p0-run/cobra_out/adjusted_coexpression.tsv'

Please provide corrected files or fix the file contents, then I will re-check them.

Please provide corrected paths as field=path assignments (for example expression_file=data/expression.tsv). The files will be inspected again before execution.
Correction > 
Run the command again with --resume cj-g4o2-C58-1 after preparing the answer.
```

### C59 class=do gold=['LIONESS-PUMA'] core=DO ['LIONESS-PUMA'] basis=run views=['needs_input']
Request: Please run LIONESS-PUMA on expr_cll.tsv (36 CLL patients), motif_cll.txt, ppi_cll.txt, mir_targets.txt and mir_list.txt (one miRNA ID per line, every one present in the first column of mir_targets.txt) to get a TF/miRNA-to-gene network for every patient.
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (3.58s)
● Matching registered workflows…
✓ Workflow — LIONESS-PUMA
● Preparing next step…
? Clarification needed
  Input required

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.

Select input 1 of 1: MiRNA list (mirna_file)
Enter a candidate number or a full path.
1. mir_targets.txt
2. mir_list.txt
Selection > 
Run the command again with --resume cj-g4o2-C59-1 after preparing the answer.
```

### C60 class=vague gold=['LIONESS-COEXPRESSION', 'BONOBO', 'PANDA', 'LIONESS-PANDA', 'COBRA'] core=CLARIFY [] basis=goal_unclear views=['clarify_goal']
Request: I uploaded counts_week0.tsv, counts_week4.tsv and counts_week12.tsv from our vaccine trial. Can you run the right workflow on them?
```text
● Classifying requested outcome…
✓ Interpreted requested outcome (1.93s)
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

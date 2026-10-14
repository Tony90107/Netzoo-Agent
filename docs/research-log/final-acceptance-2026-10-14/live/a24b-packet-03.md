## S051

Request (turn 1): We want a network of TFs and miRNAs regulating genes in our 72 hepatoblastoma samples (expression, motif prior with miRNA edges, miRNA list and PPI are ready), with the lncRNAs added as a third regulator class in the same network using our lncRNA-target predictions.

Requirements to judge (in the user's words):
R1: "a network of TFs and miRNAs regulating genes in our 72 hepatoblastoma samples"
R2: "the lncRNAs added as a third regulator class in the same network"

Reply:

````
What I understood you are asking for:
1. "We want a network of TFs and miRNAs regulating genes in our 72 hepatoblastoma samples (expression, motif prior with miRNA edges, miRNA list and PPI are ready), with the lncRNAs added as a third regulator class in the same network using our lncRNA-target predictions." -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models lncRNA regulators. PUMA does not give it: PUMA's non-TF regulators are miRNAs given by a target prior; it has no lncRNA layer and models no sponging.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “We want a network of TFs and miRNAs regulating genes in our 72 hepatoblastoma… — Registered regulatory workflows contain miRNA and TF regulators; none models lncRNA regulators.
- next step: Start a new task

## S052

Request (turn 1): Run SAMBAR on the somatic mutation matrix of our 412 stomach tumours (mut_matrix.csv) with exon lengths esize.csv, cancer genes cgenes.txt and the MSigDB GMT, and give us pathway mutation scores and patient clusters for k from 2 to 6.

Requirements to judge (in the user's words):
R1: "pathway mutation scores"
R2: "patient clusters for k from 2 to 6"

Reply:

````
No tool was executed because the Planner requires additional input.

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.
````

Card shown with the reply:
(no card)

## S053

Request (turn 1): We'd like a TF-gene regulatory network summarising all 30 of our zebrafish fin-regeneration RNA-seq samples. So far we only have the normalised count table.

Requirements to judge (in the user's words):
R1: "a TF-gene regulatory network summarising all 30 of our zebrafish fin-regeneration RNA-seq samples"

Reply:

````
What I understood you are asking for:
1. "a TF-gene regulatory network summarising all 30 of our zebrafish fin-regeneration RNA-seq samples" -- available from PANDA, OTTER or LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: 3 registered methods can build a cohort-level TF-gene regulatory network; they differ in their modeling assumptions.
- point: Understood goal: a cohort-level TF-gene regulatory network from expression data.
- point: Every option also needs motif prior and PPI network; no file for them is named yet.
- point: Nothing you said favours one method yet; each option says when to pick it.
- point: Picking an option explains it for your data and what it needs; nothing runs.
- question: Which method fits your study?
- option: PANDA — One TF-gene network across all your samples · Pick it if you want the standard published method or a base for LIONESS
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- next step: Start a new task

## S054

Request (turn 1): Go ahead: LIONESS-PANDA on the 15 macaque PBMC samples with the motif and PPI priors in /proj/mac/priors, but in the end I only need the network for animal M07 - keep the aggregate separate.

Requirements to judge (in the user's words):
R1: "I only need the network for animal M07"

Reply:

````
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

## S055

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

## S056

Request (turn 1): I inherited a network file from a former student and can't tell whether it holds TF-to-gene edges or gene-gene co-expression edges. Can you find communities in it?

Requirements to judge (in the user's words):
R1: "find communities in it"

Reply:

````
What I understood you are asking for:
1. "Can you find communities in it?" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “Can you find communities in it?” — Not matched to any registered workflow.
- next step: Start a new task

## S057

Request (turn 1): Can you show that methylation at these promoter CpGs causes the expression changes, using a causal network built from our paired methylation and RNA data on 120 patients?

Requirements to judge (in the user's words):
R1: "show that methylation at these promoter CpGs causes the expression changes"

Reply:

````
What I understood you are asking for:
1. "show that methylation at these promoter CpGs causes the expression changes" -- not available here: no registered workflow produces this. Registered regulatory workflows contain miRNA and TF regulators; none models other regulators. Every registered workflow estimates associations or model coefficients from observational data.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “show that methylation at these promoter CpGs causes the expression changes” — Registered regulatory workflows contain miRNA and TF regulators; none models other regulators.
- next step: Start a new task

## S058

Request (turn 1): Run DRAGON on our methylation and expression matrices from the same 88 patients.
Request (turn 2): Please give it to me as an edge list, with fixed lambdas of 0.2 and 0.6.

Requirements to judge (in the user's words):
R1: "give it to me as an edge list, with fixed lambdas of 0.2 and 0.6"

Reply:

````
No tool was executed because the Planner requires additional input.

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.
````

Card shown with the reply:
(no card)

## S059

Request (turn 1): We'd like to subtype 150 breast tumours with SAMBAR using pathway scores computed from their RNA-seq expression values (no mutation data).

Requirements to judge (in the user's words):
R1: "subtype 150 breast tumours with SAMBAR using pathway scores computed from their RNA-seq expression values"

Reply:

````
What I understood you are asking for:
1. "subtype 150 breast tumours with SAMBAR" -- not available here: no registered workflow produces this. SAMBAR does not give it: SAMBAR's input is somatic mutations.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “subtype 150 breast tumours with SAMBAR” — SAMBAR does not give it: SAMBAR's input is somatic mutations.
- next step: Show what NetZoo can do here
- next step: Start a new task

## S060

Request (turn 1): I don't know whether our expression values are TPM or FPKM, but please build the aggregate PANDA network for the 33 tendon samples with our motif prior and PPI.

Requirements to judge (in the user's words):
R1: "build the aggregate PANDA network for the 33 tendon samples"

Reply:

````
What I understood you are asking for:
1. "build the aggregate PANDA network" -- available from PANDA.

Assumptions behind this recommendation (not confirmed facts):

- The user has access to the necessary motif prior and PPI data.

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
````

Card shown with the reply:
- headline: PANDA fits your goal: cohort-level regulatory network.
- point: Method: Widely used baseline: message passing over motif, PPI and co-expression evidence.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Produces: regulatory network (one cohort-level result).
- next step: Plan PANDA with my data
- next step: Start a new task

## S061

Request (turn 1): Can we get one OTTER network per sample, LIONESS-style, for our 50 kidney biopsies?

Requirements to judge (in the user's words):
R1: "one OTTER network per sample, LIONESS-style"

Reply:

````
What I understood you are asking for:
1. "one OTTER network per sample, LIONESS-style" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 50 biopsies, 51 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 50 biopsies, 51 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S062

Request (turn 1): We're still deciding whether to add metabolomics to the methylation and expression data from the same 70 mice. Either way, we want one network across all the layers we end up using.

Requirements to judge (in the user's words):
R1: "one network across all the layers we end up using"

Reply:

````
What I understood you are asking for:
1. "one network across all the layers we end up using" -- depends on how many omics data types you have, which you said you do not know ("We're still deciding whether to add metabolomics to the methylation and expression data"): if two: DRAGON; if three or more: no registered workflow gives this.

Before I choose a workflow, please tell me: How many omics data types do you have?

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: One fact about your data decides which workflow applies.
- point: How many omics data types do you have?
- next step: Start a new task

## S063

Request (turn 1): The core facility sent a matrix with 3,000 columns labelled cells_x_genes, and I'm not sure whether those columns are single cells or pooled bulk samples. We want a TF-gene network for each column; motif and PPI priors are ready.

Requirements to judge (in the user's words):
R1: "a TF-gene network for each column"

Reply:

````
What I understood you are asking for:
1. "TF-gene network for each column" -- available from LIONESS-PANDA.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

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
- option: LIONESS-PANDA — One TF-gene network per sample, plus the cohort network · Not on single cells: run it on pseudo-bulk profiles, one per donor and state
- option: OTTER — The same kind of network as PANDA, from a different algorithm · Pick it if memory or runtime is a concern
- option: GIRAFFE — One signed TF-gene network (activating or repressing), plus each TF's activity in each sample · Pick it if TF activity may differ from its mRNA level
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Start a new task

## S064

Request (turn 1): Go ahead: LIONESS-PANDA on the 15 macaque PBMC samples with the motif and PPI priors in /proj/mac/priors, but in the end I only need the network for animal M07 - keep the aggregate separate.

Requirements to judge (in the user's words):
R1: "I only need the network for animal M07"

Reply:

````
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

## S065

Request (turn 1): Run SAMBAR on our 300 colorectal mutation profiles (mutation matrix, gene lengths, cancer genes and GMT attached) to get subtypes, and then predict which patients will respond to immunotherapy.

Requirements to judge (in the user's words):
R1: "Run SAMBAR on our 300 colorectal mutation profiles"
R2: "predict which patients will respond to immunotherapy"

Reply:

````
What I understood you are asking for:
1. "to get subtypes" -- available from SAMBAR.
2. "predict which patients will respond to immunotherapy" -- not available here: no registered workflow produces this. No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.

You asked me to run SAMBAR. It covers "to get subtypes", but no registered workflow covers "predict which patients will respond to immunotherapy", so the run would do only part of what you asked. I have not planned it.

Tell me to run SAMBAR for the part it gives, and I will then find your input files and show a preview; nothing runs until you approve it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: SAMBAR was not planned: confirm the run you want first.
- not available: “predict which patients will respond to immunotherapy” — No registered workflow fits a predictive or generative model; per-sample results can only be features for one built elsewhere.
- not available: Predict outcomes for new samples — No registered workflow builds a predictive model; per-sample results can only be its features.
- next step: Plan SAMBAR with my data
- next step: Start a new task

## S066

Request (turn 1): Our 310 blood transcriptomes were sequenced at three centres. We want a gene co-expression matrix with the sequencing-centre effect taken out; design.tsv has dummy-coded centre, age and sex for every sample.

Requirements to judge (in the user's words):
R1: "a gene co-expression matrix with the sequencing-centre effect taken out"

Reply:

````
What I understood you are asking for:
1. "We want a gene co-expression matrix with the sequencing-centre effect taken out" -- available from COBRA.

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
- point: Picked from 2 fitting methods because you wrote “with the sequencing-centre effect…”; LIONESS-COEXPRESSION also fit.
- point: Method: Separates how covariates (batch, site, condition) reshape co-expression.
- point: Needs: expression matrix, covariate design matrix.
- point: Produces: co-expression network (one cohort-level result).
- next step: Compare with LIONESS-COEXPRESSION
- next step: Plan COBRA with my data
- next step: Start a new task

## S067

Request (turn 1): Run OTTER on the GPU for our 120 samples; motif prior, PPI and expression are attached.
Request (turn 2): Never mind the GPU - CPU is fine, just use single precision.

Requirements to judge (in the user's words):
R1: "CPU is fine, just use single precision"

Reply:

````
No tool was executed because the Planner requires additional input.

Choose one complete input bundle before the workflow continues, or enter custom to select files individually:
1. data/auto-check-invalid/
   - motif.tsv
   - ppi.tsv
   - expression.tsv
2. data/auto-check-valid/
   - motif.tsv
   - ppi.tsv
   - expression.tsv
3. data/blind-neutral/case-1/
   - motif.tsv
   - ppi.tsv
   - expression.tsv
4. data/blind-neutral/case-2/
   - motif.tsv
   - ppi.tsv
   - expression.tsv
5. data/blind-neutral/case-6/
   - motif.tsv
   - ppi.tsv
   - expression.tsv
````

Card shown with the reply:
(no card)

## S068

Request (turn 1): Can you run DRAGON on our liver proteomics and phosphoproteomics tables?
Request (turn 2): I just checked: the phospho data come from a different set of 25 mice than the proteomics.

Requirements to judge (in the user's words):
R1: "the phospho data come from a different set of 25 mice than the proteomics"

Reply:

````
No tool was executed because the Planner requires additional input.

Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.
````

Card shown with the reply:
(no card)

## S069

Request (turn 1): Please give us a batch-corrected gene expression matrix for our 200 samples from four sequencing runs, ComBat-style, so we can use it for clustering.

Requirements to judge (in the user's words):
R1: "a batch-corrected gene expression matrix"

Reply:

````
What I understood you are asking for:
1. "batch-corrected gene expression matrix" -- not matched to any registered workflow.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “batch-corrected gene expression matrix” — Not matched to any registered workflow.
- next step: Start a new task

## S070

Request (turn 1): Please build per-sample TF-gene networks for our 96 tumour samples; expression, the motif prior and the PPI are in /data/t96.
Request (turn 2): Correction: those 96 columns are single cells from one biopsy, not tumours - we still want a network for each cell.

Requirements to judge (in the user's words):
R1: "we still want a network for each cell"

Reply:

````
What I understood you are asking for:
1. "Please build per-sample TF-gene networks for our 96 tumour samples" -- available from LIONESS-PANDA.
2. "we still want a network for each cell." -- not available here: no registered workflow produces this. Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells. LIONESS-PANDA does not give it: built for bulk samples; per-cell co-expression is dominated by dropout.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 96 samples, 97 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives the per-sample result you asked for; it also writes the cohort network, so PANDA need not run first.
- point: Method: One TF-gene network per sample, derived leave-one-out from the cohort.
- point: Needs: expression matrix, motif prior, PPI network.
- point: Cost: N samples take N+1 PANDA runs (for your 96 samples, 97 PANDA runs).
- point: Produces: regulatory network (cohort-level and per-sample).
- not available: “we still want a network for each cell.” — Every registered workflow takes bulk samples (tissues, patients, cell lines or pseudo-bulk profiles); none models single cells.
- not available: SCORPION (single-cell networks) — Not registered here; SCORPION is an R package (CRAN). Pseudo-bulk per state with PANDA is the registered route.
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

## S071

Request (turn 1): Can we turn our bladder cancer somatic mutation table (220 patients x 18,000 genes) into pathway-level mutation scores? We do have a GMT pathway file.

Requirements to judge (in the user's words):
R1: "pathway-level mutation scores"

Reply:

````
What I understood you are asking for:
1. "Can we turn our bladder cancer somatic mutation table (220 patients x 18,000 genes) into pathway-level mutation scores?" -- available from SAMBAR.

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

## S072

Request (turn 1): How can we quantify, with differential modularity, how the community structure of our control PANDA network is reorganised in the disease network?

Requirements to judge (in the user's words):
R1: "quantify, with differential modularity, how the community structure of our control PANDA network is reorganised in the disease network"

Reply:

````
Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model.

Captured request parameters:

- `network_file`: reorganised

**CONDOR**: Detect communities in a validated bipartite network with CONDOR.

Routing-level input modality: regulatory network.

Method premise: find communities in a two-mode network; return network modules or community membership.

CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Other declared controls (not matched to this request; defaults apply unless you set them): `prefix`=condor.

Distinct declared output artifacts (availability depends on workflow options):

- `community_assignment`: Network-node community memberships, not patient subtype labels.

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

## S073

Request (turn 1): We have only 9 log-transformed, centred RNA-seq profiles from rare paediatric tumours and want a co-expression network for each one, with a p-value per edge so we can keep only confident edges.

Requirements to judge (in the user's words):
R1: "a co-expression network for each one"
R2: "a p-value per edge"

Reply:

````
What I understood you are asking for:
1. "a co-expression network for each one, with a p-value per edge" -- available from BONOBO.

Selected path: **BONOBO**.

Your question asks for a co-expression network. **BONOBO** fits that result. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression.

What you asked about:

- "with a p-value per edge so we can keep only confident edges." — With `sparsify=true` BONOBO computes a p-value for every connection in every sample and keeps those with a two-sided p-value below `bonobo_confidence` (default 0.05), without multiple-testing correction. With `save_pvals=true` as well, the full network is kept and the p-values are saved beside it instead.

**BONOBO**: Infer sample-specific gene-gene co-expression networks with netZooPy BONOBO.

Routing-level input modality: expression matrix.

Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices.

BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

Required workflow inputs:

- `expression_file`: expression matrix

Controls matching this request:

- `sparsify` (type=boolean; default=False)
- `bonobo_confidence` (type=number; default=0.05; range=0.0..1.0)
- `save_pvals` (type=boolean; default=False)

Other declared controls (not matched to this request; defaults apply unless you set them): `bonobo_output_format`=.h5, `sample_names`=[], `precision`=single, `keep_in_memory`=False, `delta`, `genes_axis`=auto, `log_transformed`, `centered`.

When `sparsify=False` and `save_pvals=False`: full sample-specific gene-gene co-expression matrices; no p-value artifact is written.

When `sparsify=True` and `save_pvals=False`: upstream thresholds each sample-specific co-expression matrix; no p-value artifact is written.

When `sparsify=True` and `save_pvals=True`: upstream retains the full co-expression matrix for each selected sample and writes a matching p-value matrix; threshold it from the saved p-value matrix; it does not also emit an already-thresholded network in this mode.

Distinct declared output artifacts (availability depends on workflow options):

- `coexpression_network`: Inferred gene-to-gene associations.
- `pvalue_matrix`: P-value matrix paired with a sample-specific gene-gene co-expression result.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: BONOBO fits your goal: co-expression network.
- point: Picked from 3 fitting methods because you wrote “with a p-value per edge so we can keep…”; LIONESS-COEXPRESSION and COBRA also fit.
- point: Method: Per-sample co-expression with Bayesian shrinkage and a p-value per edge.
- point: Needs: expression matrix.
- point: Produces: co-expression network and p-value matrix (one per sample).
- next step: Compare with LIONESS-COEXPRESSION and COBRA
- next step: Plan BONOBO with my data
- next step: Start a new task

## S074

Request (turn 1): Run CONDOR on net_tf_gene.tsv (TF, gene, weight) to get regulatory modules.
Request (turn 2): One more thing: every gene has to be allowed in several modules at once.

Requirements to judge (in the user's words):
R1: "every gene has to be allowed in several modules at once"

Reply:

````
What I understood you are asking for:
1. "to get regulatory modules" -- not available here: no registered workflow produces this. Registered grouping puts each item in exactly one group (CONDOR: one community per regulator or gene; SAMBAR: one subtype per sample); none returns overlapping memberships.

No registered workflow produces this, so none is offered as the way to get it.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: No registered workflow produces what you asked for, so none is offered.
- not available: “to get regulatory modules” — Registered grouping puts each item in exactly one group (CONDOR: one community per regulator or gene; SAMBAR: one subtype per sample); none returns overlapping memberships.
- next step: Start a new task

## S075

Request (turn 1): Per-sample TF-gene networks for our 45 tumours, please - expression, motif prior and PPI are provided.
Request (turn 2): In the end I only need the networks for tumours T05 and T19.

Requirements to judge (in the user's words):
R1: "I only need the networks for tumours T05 and T19"

Reply:

````
What I understood you are asking for:
1. "Per-sample TF-gene networks for our 45 tumours" -- available from LIONESS-PANDA.
2. "the networks for tumours T05 and T19" -- available from LIONESS-PANDA.

I matched your goal to an aggregate and a sample-specific workflow. They use the same biological inputs:

1. **PANDA**
   - **Inputs**:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network
   - **Output**: Aggregate workflow output (`output_file`).

2. **LIONESS-PANDA**
   - **Inputs**:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network
   - **Outputs**:
     - Aggregate workflow output (`output_file`).
     - Sample-specific LIONESS output (`lioness_output`).

Use PANDA when you only need the aggregate result. Use LIONESS-PANDA directly when you need the sample-specific result; it also produces its aggregate output, so running the aggregate workflow first is unnecessary.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 45 tumours, 46 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
````

Card shown with the reply:
- headline: LIONESS-PANDA gives one network per sample and also the cohort network; PANDA alone gives only the cohort network.
- point: Needs: expression matrix, motif prior, PPI network.
- question: Do you need one network per sample, or only the cohort network?
- option: One network per sample (LIONESS-PANDA) — Lets you compare samples, or relate them to outcomes such as survival · Also writes the cohort network · Slower: it reruns PANDA once per sample
- option: Cohort network only (PANDA) — A single PANDA run, so faster · It will not show how samples differ
- next step: Plan LIONESS-PANDA with my data
- next step: Start a new task

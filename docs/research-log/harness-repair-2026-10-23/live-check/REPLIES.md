# P1/P2 live check: replies

## L21 (hb-h3main-L21-1) -- P2 partial: GIRAFFE optimizer settings

Call: DECLINE/full_gap; run_allowed False; replay expected: DO partial, run held

```
What I understood you are asking for:
1. "Please run GIRAFFE on our 44 psoriasis skin biopsies (expression, motif prior and PPI are ready), but change the optimizer: learning rate 0.0005, 5,000 iterations, and a heavier weight on the PPI term of the loss." -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "learning rate 0.0005" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

## J44 (hb-h2main-J44-1) -- P2 partial: OTTER on GPU

Call: DECLINE/full_gap; run_allowed False; replay expected: DO partial, run held

```
What I understood you are asking for:
1. "output otter_pbmc.tsv as an edge list." -- not available here as asked. OTTER computing=gpu is not enabled by this Docker runtime; use computing=cpu. OTTER itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

## H40 (hb-h1-H40-1) -- P2 partial: GIRAFFE settings

Call: DECLINE/full_gap; run_allowed False; replay expected: DO partial, run held

```
What I understood you are asking for:
1. "I'd like GIRAFFE run on 75 AML samples with a custom learning rate of 0.001, 5,000 iterations and a heavier weight on the PPI term in the loss - with the defaults it seemed to stop before the TF activities stabilised." -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "a custom learning rate of 0.001" cannot be applied. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "5,000 iterations" cannot be applied.

No registered workflow can give this as you asked it (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

## H18 (hb-h1-H18-1) -- control: only a question row is doable

Call: DECLINE/all_results_not_available; run_allowed False; replay expected: DECLINE

```
What I understood you are asking for:
1. "I'd like three separately tuned penalties on our 110 matched colorectal tumours: lambda1 for the methylation block, lambda2 for the expression block, and a lambda_inter of 0.2 controlling only the cross-layer methylation-expression edges." -- not available here as asked. DRAGON: lambda1 and lambda2 must be supplied together. DRAGON itself can still run, with its own settings instead -- an alternative, not the setting you asked for.
2. "Can you set it up that way?" -- not available here as asked. DRAGON: lambda1 and lambda2 must be supplied together.

No registered workflow can give these as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

## C08 (cj-p2-C08-1) -- control: can GIRAFFE take my settings

Call: DECLINE/all_results_not_available; run_allowed False; replay expected: DECLINE

```
What I understood you are asking for:
1. "a learning rate of 1e-4" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "a learning rate of 1e-4" cannot be applied. GIRAFFE itself can still run, with its own settings instead -- an alternative, not the setting you asked for.

No registered workflow can give this as you asked, so none is offered as asked.

No files were inspected and no analysis ran.
```

## L13 (hb-h3main-L13-1) -- control: past LIONESS-DRAGON's size cap

Call: DECLINE/full_gap; run_allowed False; replay expected: DECLINE

```
What I understood you are asking for:
1. "Kick off LIONESS-DRAGON now on rna_2000.csv and prot_500.csv: 120 matched samples, 2,000 transcripts and 500 proteins, sample ID in the first column of both." -- not available here as asked. LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 2,500 features and 120 samples give 374,850,000.

No registered workflow can give this as you asked it (above), so none is offered as asked.

No files were inspected and no analysis ran.
```

## C12 (cj-p0-C12-1) -- layer 2; live R21-A goal read (gold CLARIFY)

Call: CLARIFY/goal_unclear; run_allowed False; replay expected: DECLINE with layer 2 in replay

```
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

## C51 (cj-p2-C51-1) -- once a misjudged gap with a false 'no registered workflow produces this' (gold DO)

Call: DECLINE/full_gap; run_allowed False; replay expected: layer-2 wording if a gap

```
What I understood you are asking for:
1. "Is OTTER able to run on CPU in single precision with 150 iterations and a step size (eta) of 1e-4, writing the result as an edge list?" -- I couldn't match this to anything a registered NetZoo workflow produces or lets you set. OTTER gives: one weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression.

I couldn't match this to a result any registered NetZoo workflow produces, so none is offered.

Registered workflows that take the kind of data you described: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, COBRA, DRAGON, LIONESS-DRAGON, OTTER, GIRAFFE, BONOBO. Tell me if one of them gives what you meant, or which result you need.

No files were inspected and no analysis ran.
```

## C24 (cj-p2-C24-1) -- reasonless gap (gold CLARIFY)

Call: CLARIFY/goal_unclear; run_allowed False; replay expected: DECLINE with layer 2 in replay

```
I can't tell yet which result you want, so I have not chosen a workflow.

With expression data, the registered workflows can give these results:
- One weighted TF-to-gene regulatory network across all the samples given (PANDA)
- One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
- One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
- One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
- One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
- The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
- One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
- One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
- One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
- A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
- One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)

Which of these results do you want, or what question should the analysis answer?

Nothing was selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

## C07 (cj-p2-C07-1) -- near-miss prefix (gold DO)

Call: DO/results_given; run_allowed False; replay expected: DO partial

```
What I understood you are asking for:
1. "a separate network for every patient that links miRNAs and cytokines through partial correlations, within and across the two layers" -- available from LIONESS-DRAGON.
2. "so I can compare survivors with non-survivors patient by patient afterwards" -- available from LIONESS-DRAGON.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 64 patients, 65 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-DRAGON** — Each sample column holds that sample's edge weights; comparing the columns between groups of samples shows which within- and cross-layer associations differ. A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from, not absolute values.

For your question ("compare survivors with non-survivors patient by patient afterwards"):
- **DRAGON** — Build one network per time point or condition on the same features and compare the cross-layer edges; this does not use the pairing -- to keep it, use LIONESS-DRAGON and compare each individual's samples.
- **LIONESS-DRAGON** — Each sample gets its own two-layer network; comparing the samples' edge weights between the groups or conditions (paired when the same individuals give both) shows which within- and cross-layer associations differ.
Note: Partial correlations are conditional on every other feature in both layers, so use the same feature set in every network you compare.
Note: A sample's edges are estimated from how removing it changes the cohort network, so they are relative to the cohort the network was built from.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

## M20 (hb-h4main-M20-1) -- control: truly not doable; layer 2 must not mislead (gold DECLINE)

Call: DECLINE/full_gap; run_allowed False; replay expected: DECLINE with layer 2

```
What I understood you are asking for:
1. "a trained model that predicts whether a new patient will respond, reported with an AUC on held-out patients" -- I couldn't match this to anything a registered NetZoo workflow produces or lets you set.

I couldn't match this to a result any registered NetZoo workflow produces, so none is offered.

Registered workflows that take the kind of data you described: PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, LIONESS-COEXPRESSION, COBRA, DRAGON, LIONESS-DRAGON, OTTER, GIRAFFE, BONOBO. Tell me if one of them gives what you meant, or which result you need.

No files were inspected and no analysis ran.
```

## J19 (hb-h2main-J19-1) -- P1: legacy scale question beside the agent's

Call: ASK/fact_agent; run_allowed False; replay expected: ASK

```
Before I choose a workflow, please tell me:
- Do you want one network per tumour?
  You wrote: "The aims page says one network for the whole cohort, the grant narrative says one per tumour, and I can't tell which my PI meant". LIONESS-DRAGON's contract: "LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

## C56 (cj-p3-C56-1) -- P1: was UNCHECKED (gold ASK)

Call: ASK/fact_agent; run_allowed False; replay expected: ASK

```
Before I choose a workflow, please tell me:
- Do the mutation rows contain unique sample IDs?
  You wrote: "I can't tell from the file itself". SAMBAR's contract: "Mutation rows are unique sample IDs and mutation columns are unique gene IDs with non-negative numeric values".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

## J34 (hb-h2main-J34-1) -- P1: was UNCHECKED, somatic or germline (gold ask)

Call: ASK/fact_agent; run_allowed False; replay expected: ASK

```
Before I choose a workflow, please tell me:
- Does calls_30pts.csv contain somatic mutations?
  You wrote: "it's unclear to me whether it holds somatic mutations or germline variants". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

## M06 (hb-h4main-M06-1) -- P1: legacy wait bound to the agent's same question

Call: ASK/fact_agent; run_allowed False; replay expected: ASK, one question

```
Before I choose a workflow, please tell me:
- Are the calls somatic mutations?
  You wrote: "I honestly don't know whether their calls are somatic (tumour versus matched normal) or germline variants; the README doesn't say and the analyst has left". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

## C11 (cj-p2-C11-1) -- A01 regression: agent asks nothing, legacy wait kept (gold ASK)

Call: ASK/needs_fact; run_allowed False; replay expected: ASK

```
What I understood you are asking for:
1. "Run the TF network inference on expr_alzheimer.tsv (88 donors: 44 AD, 44 controls), motifs_hg38.txt and ppi_tf.txt." -- available from LIONESS-PANDA, LIONESS-PUMA, OTTER or GIRAFFE.
2. "one network per diagnostic group or one network per donor" -- you have not chosen which result you want: if "one network per diagnostic group": LIONESS-PANDA, LIONESS-PUMA, OTTER or GIRAFFE; if "one network per donor": LIONESS-PANDA, LIONESS-PUMA or GIRAFFE.
3. "a network for each AD and control" -- I couldn't match this to anything a registered NetZoo workflow produces or lets you set.

Before I choose a workflow, please tell me: Which result do you want: "one network per diagnostic group" or "one network per donor"?

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

## L05 (hb-h3main-L05-1) -- P1 live path: run request with somatic doubt

Call: ASK/fact_agent; run_allowed False; replay expected: ASK

```
Before I choose a workflow, please tell me:
- Are the variants tumor somatic calls?
  You wrote: "I don't know if these are tumor somatic calls or germline variants, because the pipeline output just says 'variants'". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

## C31 (cj-p2-C31-1) -- P1: per-biopsy scale (gold ASK)

Call: ASK/fact_agent; run_allowed False; replay expected: ASK

```
Before I choose a workflow, please tell me:
- Does your supervisor want the signed effects for each biopsy separately?
  You wrote: "My supervisor's notes say we need those signed effects for each biopsy separately, but the grant text says one set of signed effects for the whole cohort, and I'm not sure which she actually wants". GIRAFFE's contract: "It returns the aggregate TF-by-gene R matrix and a TF-by-sample TFA matrix".

No workflow has been selected and nothing runs before you answer.

No files were inspected and no analysis ran.
```

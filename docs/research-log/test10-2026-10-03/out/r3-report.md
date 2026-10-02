# TEST_PROMPTS local run `r3`

## test1

> We just finished RNA-seq on a batch of lung cancer tissues, and we also have standard transcription factor motif binding data and known protein-protein interaction data. We want to estimate how strongly each transcription factor regulates its target genes across these tissues, while also accounting for TFs that cooperate in complexes. What method should we use to build this network?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended None []
- reason `The user is seeking guidance on methods to estimate transcription factor regulat`; calls 5, tokens 12410, $0.0012

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • As for TFs that cooperate in complexes, all four model this through
    the PPI network.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Nothing you said favours one of them; each line says when to pick it.
  1) PANDA
      One TF-gene network across all your samples · Pick it if you
      want the standard published method or a base for LIONESS
  2) LIONESS-PANDA
      One TF-gene network per sample, plus the cohort network · Lets
      you compare samples, or relate them to outcomes such as survival
      · Slower: it reruns PANDA once per sample
  3) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  4) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  Next: 5) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## test2

> We have microarray expression profiles from 40 heart failure patients with highly heterogeneous clinical presentations. A single population-level network would average away individual differences, but each patient contributed only one tissue biopsy, so a per-patient correlation cannot be computed. How can we reconstruct a separate regulatory network for each patient from this cohort?

- status `ambiguous`, matched [], candidates ['run_lioness_panda', 'run_lioness_puma'], recommended None []
- reason `The user is seeking guidance on reconstructing separate regulatory networks for `; calls 7, tokens 24107, $0.0025

Card:
```
2 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a per-sample regulatory network from expression
    data.
  • Your request names only expression data; the matched workflows need
    more inputs, while LIONESS-COEXPRESSION or BONOBO works from it
    alone.
  • Nothing has run yet.
  Full explanation: /details
[Inputs] Do you also have a motif prior and a PPI network?
  The option that uses only the data you named comes first.
  1) Only expression data
      Leads to LIONESS-COEXPRESSION or BONOBO · One gene-gene co-
      expression network per sample (genes only, no regulator roles)
  2) I also have a motif prior and a PPI network
      Leads to LIONESS-PANDA
  Next: 3) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

**What your data allows.** Your request names only expression data. LIONESS-PANDA also needs a motif prior and a PPI network; LIONESS-PUMA also needs a motif prior, a PPI network and a miRNA list. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds one gene-gene co-expression network per sample (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## test3

> We have finished computing the TF-to-target regulatory edge weights. We now want to partition this network into tightly connected regulatory modules to see which groups of TFs jointly control which sets of target genes. Standard community detection treats all nodes as the same type and ignores that this is a bipartite network. What method properly detects communities across two distinct node types?

- status `exact`, matched ['run_condor'], candidates [], recommended None []
- reason `The user is seeking guidance on a method for community detection in a bipartite `; calls 4, tokens 11883, $0.0011

Card:
```
CONDOR fits your goal: cohort-level set of network communities (modules).
  • Method: Finds TF-gene communities (modules) in a two-mode network.
  • Needs: TF-gene (bipartite) network.
  • Produces: set of network communities (modules) (one cohort-level
    result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Input compatibility has not been assessed because no current input is established.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model.

**CONDOR**: Detect communities in a validated bipartite network with CONDOR.

Routing-level input modality: regulatory network.

Method premise: find communities in a two-mode network; return network modules or community membership.

CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Other declared controls (not matched to this request; defaults apply unless you set them): `prefix`=condor.

Distinct declared output artifacts (availability depends on workflow options):

- `community_assignment`: Network-node community memberships, not patient subtype labels.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## test4

> We have single-cell RNA-seq data from tumor-infiltrating immune cells, annotated into 6 cell states. The matrix is extremely sparse, with heavy dropout and variable library sizes across cells. We want to compare how regulatory networks are rewired across these 6 states, while still being able to examine heterogeneity within rare states. How should we approach this?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended None []
- reason `The user is seeking guidance on how to approach the comparison of regulatory net`; calls 6, tokens 19728, $0.0021

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Your request names only expression data; the matched workflows need
    more inputs, while LIONESS-COEXPRESSION or BONOBO works from it
    alone.
  • Nothing has run yet.
  Full explanation: /details
[Inputs] Do you also have a motif prior and a PPI network?
  The option that uses only the data you named comes first.
  1) Only expression data
      Leads to LIONESS-COEXPRESSION or BONOBO · A gene-gene co-
      expression network (genes only, no regulator roles)
  2) I also have a motif prior and a PPI network
      Leads to PANDA, LIONESS-PANDA, OTTER or GIRAFFE
  Next: 3) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that memory is a limiting factor (for example, an earlier run ran out of memory):
- **OTTER** — `precision=single` keeps OTTER's largest array, the gene-by-gene co-expression matrix, in single precision during the optimization. The loader first computes that matrix in double precision, so peak memory while loading is not reduced, and the optimization and the output network stay in double precision.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network; PUMA and LIONESS-PUMA also need a motif prior, a PPI network and a miRNA list. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## test5

> We have binary (0/1) somatic mutation calls from tumor exome sequencing of 200 patients. The data are extremely sparse with a long tail: thousands of genes are mutated in only one or two patients, and hierarchical clustering or NMF fails to find meaningful subtypes. We want to summarize these scattered gene-level mutations into pathway-level scores for each patient using known pathway annotations, and then subtype patients on those scores. Which approach fits this?

- status `None`, matched [], candidates [], recommended None []
- reason `Semantic routing output failed validation, so no workflow was selected. (ValueEr`; calls 2, tokens 12998, $0.0015

Card:
```
I could not validate an interpretation of this request, so nothing was
selected.
  • This does not mean your question is unclear; restating the result
    you want usually helps.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## test6

> In our study of cell differentiation during development, we sequenced both mRNA and small RNA, so we also have miRNA expression data. Several key genes are regulated by transcription factors at the transcriptional level and by microRNAs post-transcriptionally. A TF-gene network alone misses the post-transcriptional layer. Is there a method that incorporates miRNA target predictions into regulatory network inference?

- status `exact`, matched ['run_giraffe'], candidates ['run_giraffe'], recommended None []
- reason `The user is seeking guidance on methods to integrate miRNA target predictions in`; calls 4, tokens 13697, $0.0014

Card:
```
GIRAFFE fits your goal: cohort-level TF-gene regulatory network with TF
activities.
  • Method: Also estimates per-sample TF activity and signed
    activating/repressing effects.
  • Needs: expression matrix, motif prior, PPI network.
  • Not mentioned in your request: motif prior and PPI network.
  • Produces: regulatory network and TF activity matrix (one cohort-
    level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
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
```

## test7

> Conventional motif scanning yields many false positives because many predicted binding sites fall in closed chromatin. We have matched ATAC-seq peaks and RNA-seq expression data from the same tissues. Before network inference, we want to filter the TF-gene prior so that only binding sites in accessible chromatin are kept. How should this upstream integration be set up?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended None []
- reason `The request is for guidance on setting up upstream integration, which falls unde`; calls 7, tokens 25659, $0.0032

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Every option also needs PPI network, which your request does not
    mention.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your stated concern is answered per method in the full explanation.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Nothing you said favours one of them; each line says when to pick it.
  1) PANDA
      One TF-gene network across all your samples · Pick it if you
      want the standard published method or a base for LIONESS
  2) LIONESS-PANDA
      One TF-gene network per sample, plus the cohort network · Lets
      you compare samples, or relate them to outcomes such as survival
      · Slower: it reruns PANDA once per sample
  3) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  4) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  Next: 5) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup. For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup. OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## test8

> We have built two brain regulatory networks, one for Alzheimer's disease patients and one for healthy controls. Listing which individual TF-gene edges go up or down produces an overwhelming list and little system-level insight. We want to know how module boundaries reorganize in disease: did groups of genes that form one module in controls split apart, or merge into inflammation-related modules? How can we directly quantify this differential modular structure between the two networks?

- status `exact`, matched ['run_condor'], candidates [], recommended None []
- reason `The user is seeking guidance on how to quantify differential modular structure b`; calls 3, tokens 8036, $0.0007

Card:
```
CONDOR fits your goal: cohort-level set of network communities (modules).
  • Method: Finds TF-gene communities (modules) in a two-mode network.
  • Needs: TF-gene (bipartite) network.
  • Produces: set of network communities (modules) (one cohort-level
    result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Input compatibility has not been assessed because no current input is established.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model.

What you asked about:

- "how can we directly quantify this differential modular structure between the two networks?" — Core scores rank each node's contribution to its community's modularity; the top-scoring regulators and genes are candidates for the community's function. Gene communities can be tested for pathway enrichment with standard gene-set tools, which is a separate analysis step.

**CONDOR**: Detect communities in a validated bipartite network with CONDOR.

Routing-level input modality: regulatory network.

Method premise: find communities in a two-mode network; return network modules or community membership.

CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

Required workflow inputs:

- `network_file`: bipartite network

Other declared controls (not matched to this request; defaults apply unless you set them): `prefix`=condor.

Distinct declared output artifacts (availability depends on workflow options):

- `community_assignment`: Network-node community memberships, not patient subtype labels.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## test9

> We want to infer a gene regulatory network for a rare tissue, but only a few microarray samples are available; we also have generic, tissue-agnostic PPI and TF motif data from public databases. We would rather formulate the problem as an optimization with an explicit objective than use an iterative heuristic update scheme, ideally with a convex, globally optimal guarantee. Which tool meets these criteria?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended None []
- reason `The user is seeking guidance on identifying a tool for inferring a gene regulato`; calls 6, tokens 17695, $0.0016

Card:
```
6 registered methods can build a regulatory network; they differ in scale
(one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a regulatory network.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA,
    OTTER, GIRAFFE and PUMA give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Options that match more of what you asked for, and use only data you mentioned, come first.
  1) PANDA
      One TF-gene network across all your samples · Pick it if you
      want the standard published method or a base for LIONESS
  2) LIONESS-PANDA
      One TF-gene network per sample, plus the cohort network · Lets
      you compare samples, or relate them to outcomes such as survival
      · Slower: it reruns PANDA once per sample
  3) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  4) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  5) PUMA
      One TF + miRNA network across all your samples · Pick it if the
      regulators include miRNAs · Also needs miRNA list
  6) LIONESS-PUMA
      One TF + miRNA network per sample, plus the cohort network ·
      Pick it if the regulators include miRNAs · Also needs miRNA list
  Next: 7) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## test10

> We collected liver tissue from 90 patients across three disease stages (cirrhosis, early HCC, and advanced HCC), with one sample per patient and follow-up survival data. We want to find regulatory circuits that become progressively dysregulated with disease severity. Pairwise group comparisons are not enough; we want a network for each patient so we can model associations with disease stage and survival. What workflow would you recommend?

- status `exact`, matched ['run_lioness_panda'], candidates ['run_lioness_panda'], recommended None []
- reason `The user is seeking guidance on a workflow to identify regulatory circuits in li`; calls 4, tokens 11440, $0.0011

Card:
```
LIONESS-PANDA gives the per-sample result you asked for; it also writes the
cohort network, so PANDA need not run first.
  • Method: One TF-gene network per sample, derived leave-one-out from
    the cohort.
  • Needs: expression matrix, motif prior, PPI network.
  • Produces: regulatory network (cohort-level and per-sample).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

# TEST_PROMPTS local run `r12`

## test1

> We just finished RNA-seq on a batch of lung cancer tissues, and we also have standard transcription factor motif binding data and known protein-protein interaction data. We want to estimate how strongly each transcription factor regulates its target genes across these tissues, while also accounting for TFs that cooperate in complexes. What method should we use to build this network?

- status `None`, matched [], candidates [], recommended None []
- reason `Semantic routing output failed validation, so no workflow was selected. (ValueEr`; calls 4, tokens 36528, $0.0000

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
What I understood you are asking for:
1. "estimate how strongly each transcription factor regulates its target genes across these tissues, while also accounting for TFs that cooperate in complexes." -- available from PANDA.

Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## test2

> We have microarray expression profiles from 40 heart failure patients with highly heterogeneous clinical presentations. A single population-level network would average away individual differences, but each patient contributed only one tissue biopsy, so a per-patient correlation cannot be computed. How can we reconstruct a separate regulatory network for each patient from this cohort?

- status `ambiguous`, matched [], candidates ['run_lioness_panda', 'run_lioness_puma', 'run_giraffe', 'run_lioness_coexpression', 'run_bonobo'], recommended None []
- reason `The user seeks guidance on how to reconstruct patient-specific networks from coh`; calls 10, tokens 54778, $0.0000

Card:
```
5 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a per-sample TF-gene regulatory network from
    expression data.
  • Nothing has run yet.
  Full explanation: /details
[Result] What artifact should NetZoo produce?
  Each answer lists the workflows it leads to.
  1) Regulatory network
      Leads to LIONESS-PANDA or LIONESS-PUMA · Also needs motif prior,
      PPI network
  2) Co-expression network
      Leads to LIONESS-COEXPRESSION · One gene co-expression network
      per sample, from expression data alone · Produces a co-
      expression network instead
  3) Co-expression network + p-value matrix
      Leads to BONOBO · One gene co-expression network per sample,
      with a p-value for each connection · Produces a co-expression
      network instead
  4) Regulatory network + TF activity matrix
      Leads to GIRAFFE · Its network covers the whole cohort, not one
      per sample · Also needs motif prior, PPI network
  Next: 5) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**Gene co-expression network**
- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

**TF-only regulatory network**
- **LIONESS-PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that a value is needed for each sample:
- **GIRAFFE** — The activity matrix holds one value per TF per sample (TF by sample, written as the `.tfa` output). GIRAFFE reports absolute activity, so every value is zero or positive.

What artifact should NetZoo produce?

**Data your question needs.** Your question needs a motif prior and a PPI network, which your request does not mention. Do you have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## test3

> We have finished computing the TF-to-target regulatory edge weights. We now want to partition this network into tightly connected regulatory modules to see which groups of TFs jointly control which sets of target genes. Standard community detection treats all nodes as the same type and ignores that this is a bipartite network. What method properly detects communities across two distinct node types?

- status `exact`, matched ['run_condor'], candidates [], recommended None []
- reason `The user is asking for methodological guidance on detecting communities in a bip`; calls 6, tokens 28509, $0.0000

Card:
```
CONDOR fits your goal: cohort-level set of network communities (modules).
  • Method: Finds TF-gene communities (modules) in a two-mode network.
  • Needs: TF-gene (bipartite) network.
  • Before running: threshold a PANDA or LIONESS network so its edge
    weights are non-negative; CONDOR then gives each node one community
    and a core score.
  • Produces: set of network communities (modules) (one cohort-level
    result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "partition this network into tightly connected regulatory modules to see which groups of TFs jointly control which sets of target genes." -- available from CONDOR.

Selected path: **CONDOR**.

Your question asks for a cohort-level community assignment. **CONDOR** fits that result and scale. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model.

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
```

## test4

> We have single-cell RNA-seq data from tumor-infiltrating immune cells, annotated into 6 cell states. The matrix is extremely sparse, with heavy dropout and variable library sizes across cells. We want to compare how regulatory networks are rewired across these 6 states, while still being able to examine heterogeneity within rare states. How should we approach this?

- status `unsupported`, matched [], candidates [], recommended None []
- reason `The user is asking for guidance on how to approach the analysis, not requesting `; calls 9, tokens 51157, $0.0000

Card:
```
No registered workflow produces what you asked for, so none is offered.
  • Understood: "compare how regulatory networks are rewired across
    these 6 states"
  • Understood: "examine heterogeneity within rare states"
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ “compare how regulatory networks are rewired across these 6
      states” — Not matched to any registered workflow.
    ✕ “examine heterogeneity within rare states” — Not matched to any
      registered workflow.
    ✕ SCORPION (single-cell networks) — Not registered here; SCORPION
      is an R package (CRAN). Pseudo-bulk per state with PANDA is the
      registered route.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "compare how regulatory networks are rewired across these 6 states" -- not matched to any registered workflow.
2. "examine heterogeneity within rare states" -- not matched to any registered workflow.

No registered workflow produces these as you asked them, so none is offered for them as asked. The note below describes the closest route.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## test5

> We have binary (0/1) somatic mutation calls from tumor exome sequencing of 200 patients. The data are extremely sparse with a long tail: thousands of genes are mutated in only one or two patients, and hierarchical clustering or NMF fails to find meaningful subtypes. We want to summarize these scattered gene-level mutations into pathway-level scores for each patient using known pathway annotations, and then subtype patients on those scores. Which approach fits this?

- status `fallback`, matched ['run_sambar'], candidates ['run_sambar'], recommended None []
- reason `The user is asking for a methodological recommendation on how to summarize gene-`; calls 6, tokens 34725, $0.0000

Card:
```
SAMBAR is the closest registered match, but it is not a verified match for
your request.
  • Method: Pathway-level mutation scores, then patient subtypes by
    clustering.
  • Needs: somatic mutation matrix, gene-length CSV, cancer-gene list,
    GMT pathway file.
  • Produces: gene mutation score matrix, pathway mutation score matrix,
    set of sample subtypes and sample distance matrix (one cohort-level
    result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "summarize these scattered gene-level mutations into pathway-level scores for each patient using known pathway annotations" -- available from SAMBAR.
2. "subtype patients on those scores" -- available from SAMBAR.

Assumptions behind this recommendation (not confirmed facts):

- Known pathway annotations are available to map genes to pathways.
- Pathway scores can be computed as a simple aggregation (e.g., sum or weighted sum) of mutation status per pathway per patient.
- A clustering algorithm appropriate for the resulting pathway score matrix will reveal meaningful patient groups.

Fallback recommendation: **SAMBAR**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** is related to that result and scale.

Why this recommendation:

Gene-length normalization scales each gene's non-silent mutation count by its exon length. Patient-burden normalization then rescales those gene scores by the patient-specific cancer-associated mutation rate, reducing domination by globally hypermutated samples. Pathway aggregation next corrects for pathway size and for genes annotated to multiple pathways, compressing sparse, heterogeneous gene events into comparable pathway-by-sample scores. Patients with mutations in different genes within the same biological pathway can therefore share a functional signal that gene-by-gene comparison would miss. These corrections require gene/exon lengths, a cancer-gene set, and pathway annotations in addition to the mutation matrix. This compression does not guarantee meaningful clusters; residual mutation burden, gene-set coverage, batch effects, and cluster stability still require validation.

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
```

## test6

> In our study of cell differentiation during development, we sequenced both mRNA and small RNA, so we also have miRNA expression data. Several key genes are regulated by transcription factors at the transcriptional level and by microRNAs post-transcriptionally. A TF-gene network alone misses the post-transcriptional layer. Is there a method that incorporates miRNA target predictions into regulatory network inference?

- status `exact`, matched ['run_puma'], candidates [], recommended None []
- reason `The user is asking for a method recommendation (guidance) to incorporate miRNA t`; calls 7, tokens 36611, $0.0000

Card:
```
PUMA fits your goal if you have a motif prior and a PPI network.
  • Method: PANDA's message passing with miRNA regulators added.
  • Needs: expression matrix, motif prior, PPI network, miRNA list.
  • Produces: regulatory network (one cohort-level result).
  • Your request names only expression data and a miRNA list; the
    matched workflows need more inputs, which the request does not
    mention.
  • Nothing has run yet.
  Full explanation: /details
[Inputs] Do you also have a motif prior and a PPI network?
  The option that uses only the data you named comes first.
  1) Only expression data and a miRNA list
      Ask what the data you named can give instead
  2) I also have a motif prior and a PPI network
      Leads to PUMA
  Next: 3) Start a new task
```

Full reply:

```
**PUMA** fits the result you describe if you have a motif prior and a PPI network.

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

**What your data allows.** Your request names only expression data and a miRNA list. PUMA also needs a motif prior and a PPI network. Do you also have a motif prior and a PPI network?

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## test7

> Conventional motif scanning yields many false positives because many predicted binding sites fall in closed chromatin. We have matched ATAC-seq peaks and RNA-seq expression data from the same tissues. Before network inference, we want to filter the TF-gene prior so that only binding sites in accessible chromatin are kept. How should this upstream integration be set up?

- status `unsupported`, matched [], candidates [], recommended None []
- reason `The user is asking for guidance on how to set up upstream integration to filter `; calls 5, tokens 28490, $0.0000

Card:
```
No registered workflow prepares a TF-gene regulatory network as an input
step.
  • A registered workflow produces a related result; choose it below if
    that is what you meant.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ A TF-gene regulatory network — No registered workflow prepares
      this as an input; the workflows infer networks from your inputs.
    ✕ SPIDER (chromatin-filtered prior) — Not registered here; SPIDER
      is in netZooR and netZooM. The filtered prior can then be used
      with PANDA or OTTER.
  Full explanation: /details
[Instead] Did you mean a supported result?
  The closest supported result first.
  1) Use PANDA instead
      One TF-gene network across all your samples · Can use the prior
      you build as its motif prior · Needs expression matrix, motif
      prior, PPI network
  Next: 2) Start a new task
```

Full reply:

```
This turn could not be checked against what the registered workflows produce, so the methods below have not been confirmed to give what you asked for.

No registered NetZoo workflow prepares TF/gene regulatory networks as an input step, such as a prior built from other data; the workflows infer networks from inputs you supply.

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

PANDA can instead infer aggregate TF-to-gene regulatory networks. Did you mean that supported result?

No files were inspected and no analysis ran.
```

## test8

> We have built two brain regulatory networks, one for Alzheimer's disease patients and one for healthy controls. Listing which individual TF-gene edges go up or down produces an overwhelming list and little system-level insight. We want to know how module boundaries reorganize in disease: did groups of genes that form one module in controls split apart, or merge into inflammation-related modules? How can we directly quantify this differential modular structure between the two networks?

- status `unsupported`, matched [], candidates [], recommended None []
- reason `The user is asking for guidance on how to quantify differential modular structur`; calls 8, tokens 33588, $0.0000

Card:
```
No registered workflow produces what you asked for, so none is offered.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ “how module boundaries reorganize in disease: did groups of
      genes that form… — CONDOR does not give it: one network at a
      time.
    ✕ ALPACA (differential modularity) — Not registered here; ALPACA
      is in netZooR. CONDOR run on each network is only an
      approximation.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "how module boundaries reorganize in disease: did groups of genes that form one module in controls split apart, or merge into inflammation-related modules?" -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.

No registered workflow produces this as you asked it, so none is offered for it as asked. The note below describes the closest route.

**Comparing module structure between two networks.** CONDOR partitions one network at a time. Running it on each network gives two unaligned sets of communities, so a split or a merge can only be judged by matching them afterwards, for example by gene overlap. ALPACA (Padi & Quackenbush 2018; netZooR `pandaToAlpaca`, not registered here) compares the two directly: it uses the control network as the null model for the disease network's modularity (differential modularity) and returns each node's module and its contribution score. It takes both networks as one edge table (TF, target gene, control weight, disease weight), so they must be given over the same TF-gene pairs.

No files were inspected and no analysis ran.
```

## test9

> We want to infer a gene regulatory network for a rare tissue, but only a few microarray samples are available; we also have generic, tissue-agnostic PPI and TF motif data from public databases. We would rather formulate the problem as an optimization with an explicit objective than use an iterative heuristic update scheme, ideally with a convex, globally optimal guarantee. Which tool meets these criteria?

- status `unsupported`, matched [], candidates [], recommended None []
- reason `Semantic routing output failed validation, so no workflow was selected. (ValueEr`; calls 3, tokens 19904, $0.0000

Card:
```
No registered workflow produces what you asked for, so none is offered.
  • Understood: "infer a gene regulatory network for a rare tissue"
  • Understood: "Which tool meets these criteria?"
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ “infer a gene regulatory network for a rare tissue” — OTTER does
      not give it: non-convex objective; netZooPy takes fixed gradient
      steps.
    ✕ “Which tool meets these criteria?” — OTTER does not give it:
      non-convex objective; netZooPy takes fixed gradient steps.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "infer a gene regulatory network for a rare tissue" -- not available here: no registered workflow produces this. OTTER does not give it: non-convex objective; netZooPy takes fixed gradient steps.
2. "Which tool meets these criteria?" -- not available here: no registered workflow produces this. OTTER does not give it: non-convex objective; netZooPy takes fixed gradient steps.

No registered workflow produces these, so none is offered as the way to get them.

No files were inspected and no analysis ran.
```

## test10

> We collected liver tissue from 90 patients across three disease stages (cirrhosis, early HCC, and advanced HCC), with one sample per patient and follow-up survival data. We want to find regulatory circuits that become progressively dysregulated with disease severity. Pairwise group comparisons are not enough; we want a network for each patient so we can model associations with disease stage and survival. What workflow would you recommend?

- status `ambiguous`, matched [], candidates ['run_lioness_panda', 'run_lioness_puma'], recommended None []
- reason `The user is asking for a workflow recommendation (guidance) rather than requesti`; calls 9, tokens 43500, $0.0000

Card:
```
2 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a per-sample regulatory network.
  • Nothing has run yet.
  Full explanation: /details
[Regulators] Which regulator type should the network model: transcription factors, miRNA regulators, or both?
  Each answer lists the workflows it leads to.
  1) Transcription factors only
      Leads to LIONESS-PANDA · One TF-gene network per sample, plus
      the cohort network
  2) Both TFs and miRNAs
      Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus
      the cohort network · Also needs miRNA list
  Next: 3) Start a new task
```

Full reply:

```
What I understood you are asking for:
1. "find regulatory circuits that become progressively dysregulated with disease severity" -- available from LIONESS-PANDA.
2. "a network for each patient" -- available from LIONESS-PANDA.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- Gene expression measurements are available for each patient.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

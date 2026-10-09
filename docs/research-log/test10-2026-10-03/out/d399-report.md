# TEST_PROMPTS local run `d399`

## test1

> We just finished RNA-seq on a batch of lung cancer tissues, and we also have standard transcription factor motif binding data and known protein-protein interaction data. We want to estimate how strongly each transcription factor regulates its target genes across these tissues, while also accounting for TFs that cooperate in complexes. What method should we use to build this network?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended None []
- reason `The user is seeking guidance on methods to estimate transcription factor regulat`; calls 7, tokens 27131, $0.0018

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
What I understood you are asking for:
1. "We want to estimate how strongly each transcription factor regulates its target genes across these tissues, while also accounting for TFs that cooperate in complexes." -- available from PANDA.

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
- reason `The user is seeking guidance on reconstructing regulatory networks, which falls `; calls 7, tokens 29780, $0.0022

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
What I understood you are asking for:
1. "How can we reconstruct a separate regulatory network for each patient from this cohort?" -- available from LIONESS-PANDA.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

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
- reason `The user is seeking guidance on a method for community detection in a bipartite `; calls 6, tokens 26475, $0.0019

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
2. "What method properly detects communities across two distinct node types?" -- available from CONDOR.

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
- reason `The request is for guidance on how to approach comparing regulatory networks acr`; calls 7, tokens 38572, $0.0031

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

- status `exact`, matched ['run_sambar'], candidates [], recommended None []
- reason `The user is seeking guidance on summarizing gene-level mutations into pathway-le`; calls 5, tokens 29061, $0.0017

Card:
```
SAMBAR fits your goal: cohort-level set of sample subtypes.
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
3. "Which approach fits this?" -- available from SAMBAR.

Selected path: **SAMBAR**.

Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.

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

- status `exact`, matched ['run_puma'], candidates ['run_puma'], recommended None []
- reason `The request is for guidance on methods to incorporate miRNA target predictions i`; calls 5, tokens 28604, $0.0016

Card:
```
PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
  • Method: PANDA's message passing with miRNA regulators added.
  • Needs: expression matrix, motif prior, PPI network, miRNA list.
  • Not mentioned in your request: motif prior and PPI network.
  • Produces: regulatory network (one cohort-level result).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "Is there a method that incorporates miRNA target predictions into regulatory network inference?" -- available from PUMA.

About "Is there a method that incorporates miRNA target predictions into regulatory network inference?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Selected path: **PUMA**.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## test7

> Conventional motif scanning yields many false positives because many predicted binding sites fall in closed chromatin. We have matched ATAC-seq peaks and RNA-seq expression data from the same tissues. Before network inference, we want to filter the TF-gene prior so that only binding sites in accessible chromatin are kept. How should this upstream integration be set up?

- status `unsupported`, matched [], candidates [], recommended None []
- reason `The request is for guidance on setting up upstream integration to filter TF-gene`; calls 4, tokens 28406, $0.0014

Card:
```
No registered workflow prepares a TF-gene regulatory network as an input
step.
  • A registered workflow produces a related result; choose it below if
    that is what you meant.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ “filter the TF-gene prior so that only binding sites in
      accessible chromatin… — Not matched to any registered workflow.
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
What I understood you are asking for:
1. "filter the TF-gene prior so that only binding sites in accessible chromatin are kept" -- not matched to any registered workflow.
2. "How should this upstream integration be set up?" -- available from PANDA.

No registered NetZoo workflow prepares TF/gene regulatory networks as an input step, such as a prior built from other data; the workflows infer networks from inputs you supply.

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

PANDA can instead infer aggregate TF-to-gene regulatory networks. Did you mean that supported result?

No files were inspected and no analysis ran.
```

## test8

> We have built two brain regulatory networks, one for Alzheimer's disease patients and one for healthy controls. Listing which individual TF-gene edges go up or down produces an overwhelming list and little system-level insight. We want to know how module boundaries reorganize in disease: did groups of genes that form one module in controls split apart, or merge into inflammation-related modules? How can we directly quantify this differential modular structure between the two networks?

- status `unsupported`, matched [], candidates [], recommended None []
- reason `The request is for guidance on quantifying differential modular structure, which`; calls 6, tokens 24367, $0.0010

Card:
```
No registered workflow produces what you asked for, so none is offered.
  • Understood: "We want to know how module boundaries reorganize in
    disease: did groups of genes that form one module in controls split
    apart, or merge into inflammation-related modules?"
  • Understood: "How can we directly quantify this differential modular
    structure between the two networks?"
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ “We want to know how module boundaries reorganize in disease:
      did groups of… — CONDOR does not give it: one network at a time.
    ✕ “How can we directly quantify this differential modular
      structure between the… — CONDOR does not give it: one network at
      a time.
    ✕ ALPACA (differential modularity) — Not registered here; ALPACA
      is in netZooR. CONDOR run on each network is only an
      approximation.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "We want to know how module boundaries reorganize in disease: did groups of genes that form one module in controls split apart, or merge into inflammation-related modules?" -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.
2. "How can we directly quantify this differential modular structure between the two networks?" -- not available here: no registered workflow produces this. CONDOR does not give it: one network at a time.

No registered workflow produces these as you asked them, so none is offered for them as asked. The note below describes the closest route.

**Comparing module structure between two networks.** CONDOR partitions one network at a time. Running it on each network gives two unaligned sets of communities, so a split or a merge can only be judged by matching them afterwards, for example by gene overlap. ALPACA (Padi & Quackenbush 2018; netZooR `pandaToAlpaca`, not registered here) compares the two directly: it uses the control network as the null model for the disease network's modularity (differential modularity) and returns each node's module and its contribution score. It takes both networks as one edge table (TF, target gene, control weight, disease weight), so they must be given over the same TF-gene pairs.

No files were inspected and no analysis ran.
```

## test9

> We want to infer a gene regulatory network for a rare tissue, but only a few microarray samples are available; we also have generic, tissue-agnostic PPI and TF motif data from public databases. We would rather formulate the problem as an optimization with an explicit objective than use an iterative heuristic update scheme, ideally with a convex, globally optimal guarantee. Which tool meets these criteria?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended run_otter [('selection_tag', 'relaxed_graph_matching')]
- reason `The user is seeking guidance on identifying a tool for inferring a gene regulato`; calls 7, tokens 34530, $0.0027

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; OTTER,
    PANDA, GIRAFFE and PUMA give one across all samples.
  • Recommended: OTTER, from what you said.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ A convex, globally optimal method — No registered workflow
      guarantees a convex, global optimum; OTTER's objective is non-
      convex.
  Full explanation: /details
[Method] Which method fits your study?
  Recommended first, from what you said.
  1) OTTER  (Recommended)
      Fits what you said: you asked for an explicit objective that is
      optimized · One TF-gene network across all your samples
  2) PANDA
      The same kind of network as OTTER, from a different algorithm ·
      Pick it if you want the standard published method or a base for
      LIONESS
  3) LIONESS-PANDA
      One TF-gene network per sample, plus the cohort network · Lets
      you compare samples, or relate them to outcomes such as survival
      · Slower: it reruns PANDA once per sample
  4) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  5) PUMA
      One TF + miRNA network across all your samples · Also adds miRNA
      regulators · Pick it if the regulators include miRNAs · Also
      needs miRNA list
  6) LIONESS-PUMA
      One TF + miRNA network per sample, plus the cohort network ·
      Also adds miRNA regulators · Pick it if the regulators include
      miRNAs · Also needs miRNA list
  Next: 7) Start a new task
```

Full reply:

```
What I understood you are asking for:
1. "We want to infer a gene regulatory network for a rare tissue" -- available from OTTER.
2. "We would rather formulate the problem as an optimization with an explicit objective than use an iterative heuristic update scheme, ideally with a convex, globally optimal guarantee." -- available from OTTER.
3. "Which tool meets these criteria?" -- available from OTTER.

Based on what you said — "We would rather formulate the problem as an optimization with an explicit objective than use an iterative heuristic update scheme, ideally with a convex, globally optimal guarantee." — **OTTER** fits better: you asked for an explicit objective that is optimized.

Your question asks for a regulatory network. **OTTER** fits that result.

**OTTER** (recommend) — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix. Produces inferred regulator-to-target associations (one cohort-level result).

Conditional assumptions to confirm:
- It also needs files for the TF-motif prior and protein-interaction prior you mention; no file is named yet.

Other compatible option(s):
- **PANDA** — preferred when: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis; approach: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

**On a convex, globally optimal guarantee.** None of the registered methods offers one. OTTER is posed as a non-convex optimization (Weighill et al. 2021): the network W is fitted so that W times its transpose matches the PPI and its transpose times W matches co-expression. The paper derives a spectral solution with recovery guarantees under its assumptions, but the netZooPy OTTER registered here takes a fixed number of gradient steps from a motif-based start, which reaches a local solution. PANDA's iterative updates do not minimize a stated objective. OTTER does give the explicit objective you asked for.

Should I use OTTER, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## test10

> We collected liver tissue from 90 patients across three disease stages (cirrhosis, early HCC, and advanced HCC), with one sample per patient and follow-up survival data. We want to find regulatory circuits that become progressively dysregulated with disease severity. Pairwise group comparisons are not enough; we want a network for each patient so we can model associations with disease stage and survival. What workflow would you recommend?

- status `exact`, matched ['run_lioness_panda'], candidates ['run_lioness_panda'], recommended None []
- reason `The user is seeking guidance on a workflow to analyze regulatory circuits in liv`; calls 8, tokens 26864, $0.0031

Card:
```
LIONESS-PANDA gives the per-sample result you asked for; it also writes the
cohort network, so PANDA need not run first.
  • Method: One TF-gene network per sample, derived leave-one-out from
    the cohort.
  • Needs: expression matrix, motif prior, PPI network.
  • Cost: N samples take N+1 PANDA runs (for your 90 patients, 91 PANDA
    runs).
  • Produces: regulatory network (cohort-level and per-sample).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ “find regulatory circuits that become progressively dysregulated
      with disease… — Not matched to any registered workflow.
  Full explanation: /details
```

Full reply:

```
What I understood you are asking for:
1. "find regulatory circuits that become progressively dysregulated with disease severity" -- not matched to any registered workflow.
2. "we want a network for each patient so we can model associations with disease stage and survival" -- available from LIONESS-PANDA.

For the sample-specific output you described, use **LIONESS-PANDA**.

Required inputs:
   - `expression_file`: Expression matrix
   - `motif_file`: Motif/prior
   - `ppi_file`: PPI network

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **PANDA** separately; **LIONESS-PANDA** also produces the aggregate output. Use **PANDA** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 90 patients, 91 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

No files were inspected and no analysis ran.
```

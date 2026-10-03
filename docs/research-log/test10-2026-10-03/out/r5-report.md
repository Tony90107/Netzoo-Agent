# TEST_PROMPTS local run `r5`

## test1

> We just finished RNA-seq on a batch of lung cancer tissues, and we also have standard transcription factor motif binding data and known protein-protein interaction data. We want to estimate how strongly each transcription factor regulates its target genes across these tissues, while also accounting for TFs that cooperate in complexes. What method should we use to build this network?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended None []
- reason `The user is seeking guidance on methods to estimate transcription factor regulat`; calls 5, tokens 12654, $0.0021

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
- reason `The user is seeking guidance on reconstructing separate regulatory networks for `; calls 6, tokens 17056, $0.0027

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
- reason `The user is seeking guidance on a method for community detection in a bipartite `; calls 4, tokens 11875, $0.0015

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
Input compatibility has not been assessed because no current input is established.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## test4

> We have single-cell RNA-seq data from tumor-infiltrating immune cells, annotated into 6 cell states. The matrix is extremely sparse, with heavy dropout and variable library sizes across cells. We want to compare how regulatory networks are rewired across these 6 states, while still being able to examine heterogeneity within rare states. How should we approach this?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe', 'run_sambar'], recommended None []
- reason `The request is for guidance on how to approach comparing regulatory networks acr`; calls 6, tokens 21248, $0.0031

Card:
```
Your request can be read 2 ways, and they lead to different workflows.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Reading 2: “annotated into 6 cell states.” — No registered
      workflow produces this from the stated inputs.
    ✕ SCORPION (single-cell networks) — Not registered here; SCORPION
      is an R package (CRAN). Pseudo-bulk per state with PANDA is the
      registered route.
  Full explanation: /details
[Reading] Which reading should we start with?
  In the order your request states them.
  1) Reading 1: “RNA-seq”
      PANDA, PUMA, LIONESS-PANDA, LIONESS-PUMA, OTTER or GIRAFFE: a
      TF-gene regulatory network
  Next: 2) Start a new task
```

Full reply:

```
Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- "RNA-seq"**
Result: regulatory networks, from expression matrix.
- **TF-only regulatory network — PANDA**
  - Registered purpose: Infer an aggregate TF-to-gene regulatory network with PANDA.
  - Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate).
- **TF/miRNA regulatory network — PUMA**
  - Registered purpose: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.
  - Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow; PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate).
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).
- **TF/miRNA regulatory network — PUMA → LIONESS-PUMA**
  - Registered purpose: Infer aggregate PUMA and sample-specific LIONESS-PUMA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).
- **TF-only regulatory network — OTTER**
  - Registered purpose: Infer an aggregate TF-to-gene regulatory network with OTTER by solving a continuous-relaxation graph-matching optimization with an explicit objective and gamma regularization that balances motif/PPI priors with co-expression constraints.
  - Method premise: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing
  - Mathematical interpretation: OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.
  - Required inputs: all of: motif/prior, PPI network; and one of: expression matrix or adjusted co-expression matrix.
  - Declared output: regulatory networks (cohort-level aggregate).
- **TF-only signed regulatory-effect network — GIRAFFE**
  - Registered purpose: Use biologically informed matrix factorization with netZooPy GIRAFFE to jointly infer R and TFA by fitting Y approximately R times absolute TFA; TFA provides the sample-varying predictors and R contains signed partial regulatory effects interpretable as linear-model coefficients, positive for activation and negative for repression.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Mathematical interpretation: GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks, TF activity matrices (cohort-level aggregate).

**Reading 2 -- "annotated into 6 cell states."**
Result: sample cluster assignment (aggregate), from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE), 2 (no registered workflow)? If a reading should use different data, say which.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.
```

## test5

> We have binary (0/1) somatic mutation calls from tumor exome sequencing of 200 patients. The data are extremely sparse with a long tail: thousands of genes are mutated in only one or two patients, and hierarchical clustering or NMF fails to find meaningful subtypes. We want to summarize these scattered gene-level mutations into pathway-level scores for each patient using known pathway annotations, and then subtype patients on those scores. Which approach fits this?

- status `exact`, matched ['run_sambar'], candidates [], recommended None []
- reason `The user is seeking guidance on summarizing gene-level mutations into pathway-le`; calls 4, tokens 14697, $0.0021

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
- reason `The user is seeking guidance on methods for incorporating miRNA target predictio`; calls 4, tokens 12874, $0.0014

Card:
```
PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
  • Method: PANDA's message passing with miRNA regulators added.
  • Needs: expression matrix, motif prior, PPI network, miRNA list.
  • Produces: regulatory network (one cohort-level result).
  • Your request names only expression data; the matched workflows need
    more inputs, while LIONESS-COEXPRESSION works from it alone.
  • Nothing has run yet.
  Full explanation: /details
[Inputs] Do you also have a motif prior and a PPI network?
  The option that uses only the data you named comes first.
  1) Only expression data
      Leads to LIONESS-COEXPRESSION · One cohort-level gene-gene co-
      expression network (genes only, no regulator roles)
  2) I also have a motif prior and a PPI network
      Leads to PUMA
  Next: 3) Start a new task
```

Full reply:

```
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

This is workflow guidance only; no execution was authorized. **What your data allows.** Your request names only expression data. PUMA also needs a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## test7

> Conventional motif scanning yields many false positives because many predicted binding sites fall in closed chromatin. We have matched ATAC-seq peaks and RNA-seq expression data from the same tissues. Before network inference, we want to filter the TF-gene prior so that only binding sites in accessible chromatin are kept. How should this upstream integration be set up?

- status `unsupported`, matched [], candidates [], recommended None []
- reason `The request is for guidance on setting up upstream integration to filter TF-gene`; calls 3, tokens 12766, $0.0014

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
      Widely used baseline: message passing over motif, PPI and co-
      expression evidence · Needs expression matrix, motif prior, PPI
      network
  2) Use PUMA instead
      PANDA's message passing with miRNA regulators added · Needs
      expression matrix, motif prior, PPI network, miRNA list
  Next: 3) Start a new task
```

Full reply:

```
No registered NetZoo workflow prepares TF/gene regulatory networks as an input step, such as a prior built from other data; the workflows infer networks from inputs you supply.

PANDA can instead infer aggregate TF-to-gene regulatory networks. Did you mean that supported result?

**Building the prior from chromatin accessibility.** Keeping only motif sites in open chromatin is a step before network inference, and no registered workflow performs it. SPIDER (Sonawane et al. 2021; netZooR and netZooM, not registered here) does this and then runs PANDA's message passing. A manual route: scan TF motifs (for example FIMO or HOMER), keep the sites inside your ATAC-seq peaks (for example bedtools intersect), assign the kept sites to genes with a stated promoter window (for example TSS -750/+250 bp or +/-1 kb), and write the TF-gene pairs as a binary motif prior. Then run PANDA or OTTER (registered) with that prior and the expression matrix from the same tissues. A promoter window misses distal enhancers unless enhancer-gene links are added.

No files were inspected and no analysis ran.
```

## test8

> We have built two brain regulatory networks, one for Alzheimer's disease patients and one for healthy controls. Listing which individual TF-gene edges go up or down produces an overwhelming list and little system-level insight. We want to know how module boundaries reorganize in disease: did groups of genes that form one module in controls split apart, or merge into inflammation-related modules? How can we directly quantify this differential modular structure between the two networks?

- status `exact`, matched ['run_condor'], candidates [], recommended None []
- reason `The request is for guidance on quantifying differential modular structure, which`; calls 3, tokens 8043, $0.0008

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
  Related, but not available in this agent:
    ✕ ALPACA (differential modularity) — Not registered here; ALPACA
      is in netZooR. CONDOR run on each network is only an
      approximation.
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

Before CONDOR: a PANDA or LIONESS network is dense and its edge weights can be negative. netZooR's pandaToCondorObject keeps only edges above a threshold (by default midway between the median weights of prior and non-prior edges) before CONDOR; threshold your network the same way, or otherwise make the weights non-negative, before running it here. CONDOR puts each node in one community and gives each node a core score, its share of its community's modularity, which picks out each module's core regulators.

Other declared controls (not matched to this request; defaults apply unless you set them): `prefix`=condor.

Distinct declared output artifacts (availability depends on workflow options):

- `community_assignment`: Network-node community memberships, not patient subtype labels.

**Comparing module structure between two networks.** CONDOR partitions one network at a time. Running it on each network gives two unaligned sets of communities, so a split or a merge can only be judged by matching them afterwards, for example by gene overlap. ALPACA (Padi & Quackenbush 2018; netZooR `pandaToAlpaca`, not registered here) compares the two directly: it uses the control network as the null model for the disease network's modularity (differential modularity) and returns each node's module and its contribution score.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## test9

> We want to infer a gene regulatory network for a rare tissue, but only a few microarray samples are available; we also have generic, tissue-agnostic PPI and TF motif data from public databases. We would rather formulate the problem as an optimization with an explicit objective than use an iterative heuristic update scheme, ideally with a convex, globally optimal guarantee. Which tool meets these criteria?

- status `ambiguous`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended None []
- reason `The user is seeking guidance on identifying a tool for inferring a gene regulato`; calls 6, tokens 17747, $0.0023

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
  Related, but not available in this agent:
    ✕ A convex, globally optimal method — No registered workflow
      guarantees a convex, global optimum; OTTER's objective is non-
      convex.
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

**On a convex, globally optimal guarantee.** None of the registered methods offers one. OTTER is posed as a non-convex optimization (Weighill et al. 2021): the network W is fitted so that W times its transpose matches the PPI and its transpose times W matches co-expression. The paper derives a spectral solution with recovery guarantees under its assumptions, but the netZooPy OTTER registered here takes a fixed number of gradient steps from a motif-based start, which reaches a local solution. PANDA's iterative updates do not minimize a stated objective. OTTER does give the explicit objective you asked for.

No files were inspected and no analysis ran.
```

## test10

> We collected liver tissue from 90 patients across three disease stages (cirrhosis, early HCC, and advanced HCC), with one sample per patient and follow-up survival data. We want to find regulatory circuits that become progressively dysregulated with disease severity. Pairwise group comparisons are not enough; we want a network for each patient so we can model associations with disease stage and survival. What workflow would you recommend?

- status `exact`, matched ['run_lioness_panda'], candidates ['run_lioness_panda'], recommended None []
- reason `The user is seeking guidance on a workflow to model regulatory circuits and asso`; calls 4, tokens 11398, $0.0011

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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 90 patients, 91 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

# Log 342 live `s7`: replies

## Q1-a [paired/group_difference] witness: None/[]

> Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin; we have RNA-seq plus a human motif prior and PPI network. Does the macrophage regulatory network shift, on average, after the challenge?

### base r1

```
Based on what you said — "Does the macrophage regulatory network shift, on average, after the challenge?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### base r2

```
Based on what you said — "Does the macrophage regulatory network shift, on average, after the challenge?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### base r3

```
Based on what you said — "Does the macrophage regulatory network shift, on average, after the challenge?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['group_difference', 'Does the macrophage regulatory network shift, on average, after the challenge?']]})

```
Based on what you said — "Does the macrophage regulatory network shift, on average, after the challenge?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Does the macrophage regulatory network shift, on average, after the challenge?"):
- **PANDA**, **PUMA** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use the per-sample (LIONESS) version and compare each individual's samples.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each individual's networks from the different time points can be compared directly: test the within-individual differences of edge weights or targeting scores, for example with a paired test or a linear model with an individual term.
- **OTTER** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use a per-sample method such as LIONESS-PANDA and compare each individual's samples.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['group_difference', 'Does the macrophage regulatory network shift, on average, after the challenge?']]})

```
Based on what you said — "the macrophage regulatory network shift, on average, after the challenge?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Does the macrophage regulatory network shift, on average, after the challenge?"):
- **PANDA**, **PUMA** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use the per-sample (LIONESS) version and compare each individual's samples.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each individual's networks from the different time points can be compared directly: test the within-individual differences of edge weights or targeting scores, for example with a paired test or a linear model with an individual term.
- **OTTER** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use a per-sample method such as LIONESS-PANDA and compare each individual's samples.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['group_difference', 'Does the macrophage regulatory network shift, on average, after the challenge?']]})

```
Based on what you said — "the macrophage regulatory network shift, on average, after the challenge?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Does the macrophage regulatory network shift, on average, after the challenge?"):
- **PANDA**, **PUMA** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use the per-sample (LIONESS) version and compare each individual's samples.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each individual's networks from the different time points can be compared directly: test the within-individual differences of edge weights or targeting scores, for example with a paired test or a linear model with an individual term.
- **OTTER** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use a per-sample method such as LIONESS-PANDA and compare each individual's samples.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## Q1-b [paired/individual_change] witness: None/['individual_change']

> Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin; we have RNA-seq plus a human motif prior and PPI network. Which volunteers had the most rewired networks post-exposure?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'individual_change', 'quote': 'Which volunteers had the most rewired networks post-exposure?'}]})

```
I can map this to more than one compatible network result:

**Gene co-expression network**
- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which result do you mean: inferred regulator-to-target associations (PANDA or PUMA or LIONESS-PANDA or LIONESS-PUMA or OTTER or GIRAFFE); or inferred gene-to-gene associations (LIONESS-COEXPRESSION or COBRA or BONOBO)?

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'individual_change', 'quote': 'Which volunteers had the most rewired networks post-exposure?'}]})

```
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

For your question ("Which volunteers had the most rewired networks post-exposure?"):
- **LIONESS-PANDA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'individual_change', 'quote': 'Which volunteers had the most rewired networks post-exposure?'}]})

```
Based on what you said — "Which volunteers had the most rewired networks post-exposure?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Which volunteers had the most rewired networks post-exposure?"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['individual_change', 'Which volunteers had the most rewired networks post-exposure?']]})

```
Based on what you said — "Which volunteers had the most rewired networks post-exposure?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Which volunteers had the most rewired networks post-exposure?"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each individual has a network for each time point; the difference between an individual's own networks (or their regulators' targeting scores) measures how much that individual changed, and ranks individuals by it.
- **GIRAFFE** — The difference between an individual's activity profiles at the time points measures how much that individual's TF activity changed.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['individual_change', 'Which volunteers had the most rewired networks post-exposure?']]})

```
Based on what you said — "Which volunteers had the most rewired networks post-exposure?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Which volunteers had the most rewired networks post-exposure?"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each individual has a network for each time point; the difference between an individual's own networks (or their regulators' targeting scores) measures how much that individual changed, and ranks individuals by it.
- **GIRAFFE** — The difference between an individual's activity profiles at the time points measures how much that individual's TF activity changed.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['individual_change', 'Which volunteers had the most rewired networks post-exposure?']]})

```
Based on what you said — "Which volunteers had the most rewired networks post-exposure?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Which volunteers had the most rewired networks post-exposure?"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each individual has a network for each time point; the difference between an individual's own networks (or their regulators' targeting scores) measures how much that individual changed, and ranks individuals by it.
- **GIRAFFE** — The difference between an individual's activity profiles at the time points measures how much that individual's TF activity changed.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## Q1-c [paired/regulator_change] witness: None/['regulator_change']

> Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin; we have RNA-seq plus a human motif prior and PPI network. Which transcription factors gain or lose the most targets after endotoxin?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which transcription factors gain or lose the most targets after endotoxin?'}]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will focus on transcription factors specifically in the context of alveolar macrophages.
- The RNA-seq data will be used to infer changes in regulatory networks.

Which modeling assumption best matches your experiment: biologically informed matrix factorization; derive each sample network from all-sample and leave-one-out networks; iterative message passing?

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which transcription factors gain or lose the most targets after endotoxin?'}]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which transcription factors gain or lose the most targets after endotoxin?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which transcription factors gain or lose the most targets after endotoxin?'}]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which transcription factors gain or lose the most targets after endotoxin?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['regulator_change', 'which transcription factors gain or lose the most targets after endotoxin']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("which transcription factors gain or lose the most targets after endotoxin"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['regulator_change', 'Which transcription factors gain or lose the most targets after endotoxin?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which transcription factors gain or lose the most targets after endotoxin?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': [['regulator_change', 'Which transcription factors gain or lose the most targets after endotoxin?']]})

```
Based on what you said — "Which transcription factors gain or lose the most targets after endotoxin?" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

For your question ("Which transcription factors gain or lose the most targets after endotoxin?"):
- **PANDA**, **PUMA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## Q1-d [paired/none] witness: None/[]

> Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin; we have RNA-seq plus a human motif prior and PPI network. For now, one reference regulatory network for these cells is enough.

### base r1

```
Based on what you said — "one reference regulatory network for these cells is enough" — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### base r2

```
Based on what you said — "For now, one reference regulatory network for these cells is enough." — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### base r3

```
Based on what you said — "For now, one reference regulatory network for these cells is enough." — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': []})

```
Based on what you said — "For now, one reference regulatory network for these cells is enough." — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': []})

```
Based on what you said — "For now, one reference regulatory network for these cells is enough." — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Alveolar macrophages from 14 volunteers were collected by lavage at baseline and 6 h after inhaled endotoxin', 'claims': []})

```
Based on what you said — "one reference regulatory network for these cells is enough." — **PANDA** fits better: results must be comparable with the widely published approach, or serve as a base network for later per-sample analysis.

Your question asks for a regulatory network. **PANDA** fits that result.

**PANDA** (recommend) — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations (one cohort-level result).

Other compatible option(s):
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.
- **LIONESS-PANDA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; approach: derive each sample network from all-sample and leave-one-out networks.
- **OTTER** — preferred when: the network is large and memory or runtime is a concern; approach: continuous relaxed graph-matching; explicit objective/loss, gradient descent, convergence; not heuristic message passing.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PANDA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## Q2-a [groups/causal] witness: None/['causal']

> Whole-blood RNA-seq from 60 children with Kawasaki disease and 40 febrile children with other infections; we only have the expression matrix. Ultimately we want to show that disrupted interferon co-expression causes the coronary artery damage.

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Ultimately we want to show that disrupted interferon co-expression causes the coronary artery damage.'}]})

```
About "Ultimately we want to show that disrupted interferon co-expression causes the coronary artery damage.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared across samples or groups. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
- **COBRA** — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Ultimately we want to show that disrupted interferon co-expression causes the coronary artery damage.'}]})

```
About "Ultimately we want to show that disrupted interferon co-expression causes the coronary artery damage.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared across samples or groups. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
- **LIONESS-COEXPRESSION**, **BONOBO** — Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately.
- **COBRA** — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).
- **BONOBO** — Per-sample gene degree or edge weights can be compared across samples or groups; with p-value output, edges can be filtered per sample at a chosen confidence. These are co-expression networks, not TF-gene regulation; turning them into regulatory networks needs a separate, validated conversion before PANDA.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Ultimately we want to show that disrupted interferon co-expression causes the coronary artery damage.'}]})

```
About "Ultimately we want to show that disrupted interferon co-expression causes the coronary artery damage.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared across samples or groups. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
- **LIONESS-COEXPRESSION**, **BONOBO** — Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately.
- **COBRA** — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).
- **BONOBO** — Per-sample gene degree or edge weights can be compared across samples or groups; with p-value output, edges can be filtered per sample at a chosen confidence. These are co-expression networks, not TF-gene regulation; turning them into regulatory networks needs a separate, validated conversion before PANDA.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['causal', 'show that disrupted interferon co-expression causes the coronary artery damage.']]})

```
About "show that disrupted interferon co-expression causes the coronary artery damage.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared across samples or groups. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
- **LIONESS-COEXPRESSION**, **BONOBO** — Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately.
- **COBRA** — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).
- **BONOBO** — Per-sample gene degree or edge weights can be compared across samples or groups; with p-value output, edges can be filtered per sample at a chosen confidence. These are co-expression networks, not TF-gene regulation; turning them into regulatory networks needs a separate, validated conversion before PANDA.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['causal', 'show that disrupted interferon co-expression causes the coronary artery damage.']]})

```
About "show that disrupted interferon co-expression causes the coronary artery damage.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared across samples or groups. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
- **LIONESS-COEXPRESSION**, **BONOBO** — Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately.
- **COBRA** — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).
- **BONOBO** — Per-sample gene degree or edge weights can be compared across samples or groups; with p-value output, edges can be filtered per sample at a chosen confidence. These are co-expression networks, not TF-gene regulation; turning them into regulatory networks needs a separate, validated conversion before PANDA.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['causal', 'show that disrupted interferon co-expression causes the coronary artery damage.']]})

```
About "show that disrupted interferon co-expression causes the coronary artery damage.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared across samples or groups. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
- **LIONESS-COEXPRESSION**, **BONOBO** — Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately.
- **COBRA** — Each covariate's component is a gene-by-gene co-expression attributable to that covariate; the adjusted co-expression can be passed to PANDA, PUMA or OTTER as coexpression_file after its identifiers and order are revalidated. Interpret each component relative to how the design matrix codes that covariate (for example, which level is the reference).
- **BONOBO** — Per-sample gene degree or edge weights can be compared across samples or groups; with p-value output, edges can be filtered per sample at a chosen confidence. These are co-expression networks, not TF-gene regulation; turning them into regulatory networks needs a separate, validated conversion before PANDA.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## Q2-b [groups/prediction] witness: None/[]

> Whole-blood RNA-seq from 60 children with Kawasaki disease and 40 febrile children with other infections; we only have the expression matrix. We'd like something that tells, at admission, whether a new febrile child has Kawasaki disease.

### base r1

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

### base r2

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

### base r3

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['prediction', "we'd like something that tells, at admission, whether a new febrile child has Kawasaki disease."]]})

```
About "we'd like something that tells, at admission, whether a new febrile child has Kawasaki disease.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '60 children with Kawasaki disease and 40 febrile children with other infections', 'claims': [['prediction', "we'd like something that tells, at admission, whether a new febrile child has Kawasaki disease."]]})

```
About "we'd like something that tells, at admission, whether a new febrile child has Kawasaki disease.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **LIONESS-PANDA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['prediction', "we'd like something that tells, at admission, whether a new febrile child has Kawasaki disease."]]})

```
About "we'd like something that tells, at admission, whether a new febrile child has Kawasaki disease.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

Your request does not say what the network should connect; the options above assume regulator-to-target associations. Every option above also needs a TF-motif prior and a protein-interaction prior. If you meant gene-to-gene associations, **BONOBO** and **LIONESS-COEXPRESSION** need only the input you named.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## Q2-c [groups/group_difference] witness: None/[]

> Whole-blood RNA-seq from 60 children with Kawasaki disease and 40 febrile children with other infections; we only have the expression matrix. Is gene co-expression wired differently in Kawasaki disease than in the other fevers?

### base r1

```
I cannot select a workflow until the requested result is clear. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

No files were inspected and no analysis ran.
```

### base r2

```
I cannot select a workflow until the requested result is clear. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

No files were inspected and no analysis ran.
```

### base r3

```
I cannot select a workflow until the requested result is clear. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '60 children with Kawasaki disease and 40 febrile children with other infections', 'claims': [['group_difference', 'Is gene co-expression wired differently in Kawasaki disease than in the other fevers?']]})

```
I cannot select a workflow until the requested result is clear. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '60 children with Kawasaki disease and 40 febrile children with other infections', 'claims': [['group_difference', 'Is gene co-expression wired differently in Kawasaki disease than in the other fevers?']]})

```
I cannot select a workflow until the requested result is clear. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '60 children with Kawasaki disease and 40 febrile children with other infections', 'claims': [['group_difference', 'Is gene co-expression wired differently in Kawasaki disease than in the other fevers?']]})

```
I cannot select a workflow until the requested result is clear. I could not validate every research alternative. Please state each hypothesis and the result you want from it before selecting a workflow.

No files were inspected and no analysis ran.
```

## Q2-d [groups/none] witness: None/[]

> Whole-blood RNA-seq from 60 children with Kawasaki disease and 40 febrile children with other infections; we only have the expression matrix. First step: one co-expression network per child, to explore.

### base r1

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The expression matrix contains sufficient data to infer co-expression networks for each child.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### base r2

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The expression matrix contains sufficient data to infer co-expression networks for each child.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### base r3

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '60 children with Kawasaki disease and 40 febrile children with other infections', 'claims': []})

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '60 children with Kawasaki disease and 40 febrile children with other infections', 'claims': []})

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '60 children with Kawasaki disease and 40 febrile children with other infections', 'claims': []})

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.
- **BONOBO** — BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. Needs expression matrix.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## Q3-a [paired/regulator_change] witness: None/['regulator_change']

> Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18, plus motif, PPI and miRNA-target priors. Which miRNAs and TFs are most rewired by high glucose?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which miRNAs and TFs are most rewired by high glucose?'}]})

```
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

For your question ("Which miRNAs and TFs are most rewired by high glucose?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which miRNAs and TFs are most rewired by high glucose?'}]})

```
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

For your question ("Which miRNAs and TFs are most rewired by high glucose?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which miRNAs and TFs are most rewired by high glucose?'}]})

```
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

For your question ("Which miRNAs and TFs are most rewired by high glucose?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18', 'claims': [['regulator_change', 'Which miRNAs and TFs are most rewired by high glucose?']]})

```
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

For your question ("Which miRNAs and TFs are most rewired by high glucose?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18', 'claims': [['regulator_change', 'Which miRNAs and TFs are most rewired by high glucose?']]})

```
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

For your question ("Which miRNAs and TFs are most rewired by high glucose?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18', 'claims': [['regulator_change', 'Which miRNAs and TFs are most rewired by high glucose?']]})

```
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

For your question ("Which miRNAs and TFs are most rewired by high glucose?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## Q3-b [paired/causal] witness: None/['causal']

> Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18, plus motif, PPI and miRNA-target priors. Goal: prove that glucose-driven miRNA loss causes the inflammatory switch.

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Goal: prove that glucose-driven miRNA loss causes the inflammatory switch.'}]})

```
About "Goal: prove that glucose-driven miRNA loss causes the inflammatory switch.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**Multi omic network**
- **DRAGON** — DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. Per-sample version: **LIONESS-DRAGON**. Needs DRAGON omics layer 1 and DRAGON omics layer 2.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- Transcription factor activity will provide insights into the inflammatory response.
- Sample-specific analysis is necessary to account for donor variability.
- The multi-omic approach will provide a comprehensive view of the regulatory mechanisms involved.

Which result do you mean: inferred regulator-to-target associations (PUMA or LIONESS-PUMA); or inferred transcription-factor-by-sample activity values (GIRAFFE); or inferred associations between omics features (DRAGON or LIONESS-DRAGON)?

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Goal: prove that glucose-driven miRNA loss causes the inflammatory switch.'}]})

```
About "Goal: prove that glucose-driven miRNA loss causes the inflammatory switch.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- Transcription factors play a role in the inflammatory response influenced by miRNA levels.

Which result do you mean: inferred regulator-to-target associations (PUMA or LIONESS-PUMA); or inferred transcription-factor-by-sample activity values (GIRAFFE)?

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Goal: prove that glucose-driven miRNA loss causes the inflammatory switch.'}]})

```
About "Goal: prove that glucose-driven miRNA loss causes the inflammatory switch.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18', 'claims': [['causal', 'prove that glucose-driven miRNA loss causes the inflammatory switch']]})

```
About "prove that glucose-driven miRNA loss causes the inflammatory switch": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

I can map this to more than one compatible network result:

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which result do you mean: inferred regulator-to-target associations (PUMA or LIONESS-PUMA); or inferred transcription-factor-by-sample activity values (GIRAFFE)?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18', 'claims': [['causal', 'prove that glucose-driven miRNA loss causes the inflammatory switch']]})

```
About "prove that glucose-driven miRNA loss causes the inflammatory switch": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

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
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18', 'claims': [['causal', 'prove that glucose-driven miRNA loss causes the inflammatory switch']]})

```
About "prove that glucose-driven miRNA loss causes the inflammatory switch": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

I can map this to more than one compatible network result:

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which result do you mean: inferred regulator-to-target associations (PUMA or LIONESS-PUMA); or inferred transcription-factor-by-sample activity values (GIRAFFE)?

No files were inspected and no analysis ran.
```

## Q3-c [paired/individual_change] witness: None/[]

> Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18, plus motif, PPI and miRNA-target priors. Whose monocytes respond most strongly to glucose, network-wise?

### base r1

```
Selected path: **PUMA**.

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

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### base r2

```
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
```

### base r3

```
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
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'Whose monocytes respond most strongly to glucose, network-wise?']]})

```
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
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'Whose monocytes respond most strongly to glucose, network-wise?']]})

```
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
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'Whose monocytes respond most strongly to glucose, network-wise?']]})

```
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
```

## Q3-d [paired/none] witness: None/[]

> Monocytes from 9 donors were each split into high- and normal-glucose cultures; we have mRNA and small-RNA sequencing for all 18, plus motif, PPI and miRNA-target priors. We want one combined TF-and-miRNA network as a lab resource.

### base r1

```
Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

Captured request parameters:

- `network_file`: a

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

### base r2

```
Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- aggregate regulatory networks**
Result: regulatory networks (aggregate), from inputs the request does not state.
- **TF/miRNA regulatory network — PUMA**
  - Registered purpose: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.
  - Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow; PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate).

**Reading 2 -- "one combined TF-and-miRNA network"**
Result: multi omic network (aggregate), from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PUMA), 2 (no registered workflow)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
```

### base r3

```
Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- aggregate regulatory networks**
Result: regulatory networks (aggregate), from inputs the request does not state.
- **TF/miRNA regulatory network — PUMA**
  - Registered purpose: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.
  - Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow; PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate).

**Reading 2 -- "one combined TF-and-miRNA network"**
Result: multi omic network (aggregate), from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PUMA), 2 (no registered workflow)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- aggregate regulatory networks**
Result: regulatory networks (aggregate), from inputs the request does not state.
- **TF/miRNA regulatory network — PUMA**
  - Registered purpose: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.
  - Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow; PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate).

**Reading 2 -- "one combined TF-and-miRNA network"**
Result: multi omic network (aggregate), from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PUMA), 2 (no registered workflow)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
Assumptions behind this recommendation (not confirmed facts):

- The user has access to the necessary sequencing data and prior information for the analysis.

Selected path: **PUMA**.

Your question asks for a cohort-level regulatory network. **PUMA** fits that result and scale. PUMA extends PANDA's message passing to miRNA regulators.

Captured request parameters:

- `network_file`: a

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

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
Your request describes more than one scientific reading. Each is listed with the registered workflows that fit it, their algorithmic premises and inputs:

**Reading 1 -- aggregate regulatory networks**
Result: regulatory networks (aggregate), from inputs the request does not state.
- **TF/miRNA regulatory network — PUMA**
  - Registered purpose: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA.
  - Method premise: iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow; PUMA uses message passing to integrate miRNA-target predictions with target-gene co-expression alongside TF motif and PPI evidence.
  - Mathematical interpretation: PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
  - Declared output: regulatory networks (cohort-level aggregate).

**Reading 2 -- "one combined TF-and-miRNA network"**
Result: multi omic network (aggregate), from inputs the request does not state.
No registered workflow produces this result from these inputs.

Which reading should we start with: 1 (PUMA), 2 (no registered workflow)? If a reading should use different data, say which.

No files were inspected and no analysis ran.
```

## Q4-a [groups/group_difference] witness: None/[]

> We profiled brains of 30 nurse and 30 forager honeybees, with RNA-seq and bisulfite methylation measured on each individual brain. Does methylation-expression coupling differ between nurses and foragers?

### base r1

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### base r2

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### base r3

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['group_difference', 'Does methylation-expression coupling differ between nurses and foragers?']]})

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['group_difference', 'Does methylation-expression coupling differ between nurses and foragers?']]})

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['group_difference', 'Does methylation-expression coupling differ between nurses and foragers?']]})

```
Semantic routing output failed validation, so no workflow was selected. (ValueError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## Q4-b [groups/prediction] witness: None/[]

> We profiled brains of 30 nurse and 30 forager honeybees, with RNA-seq and bisulfite methylation measured on each individual brain. Next season we want to classify newly collected bees as nurse or forager from their brain profiles.

### base r1

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### base r2

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### base r3

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['prediction', 'classify newly collected bees as nurse or forager from their brain profiles']]})

```
About "classify newly collected bees as nurse or forager from their brain profiles": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['prediction', 'classify newly collected bees as nurse or forager from their brain profiles']]})

```
About "classify newly collected bees as nurse or forager from their brain profiles": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['prediction', 'classify newly collected bees as nurse or forager from their brain profiles']]})

```
About "classify newly collected bees as nurse or forager from their brain profiles": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

## Q4-c [groups/none] witness: None/[]

> We profiled brains of 30 nurse and 30 forager honeybees, with RNA-seq and bisulfite methylation measured on each individual brain. Mainly we need one joint network linking methylated loci to expressed genes across all 60 brains.

### base r1

```
Assumptions behind this recommendation (not confirmed facts):

- The analysis will integrate both RNA-seq and bisulfite methylation data.
- The user is interested in a population-level network rather than individual-specific networks.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level multi-omic network. **DRAGON** is related to that result and scale.

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
```

### base r2

```
Assumptions behind this recommendation (not confirmed facts):

- The analysis will integrate both RNA-seq and bisulfite methylation data.
- The resulting network will be inferred from the combined data of all 60 brains.

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
```

### base r3

```
Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level multi-omic network. **DRAGON** is related to that result and scale.

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
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': []})

```
Assumptions behind this recommendation (not confirmed facts):

- The methylation and expression data are compatible for joint analysis.
- The analysis will consider all 60 brains as a single cohort.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level multi-omic network. **DRAGON** is related to that result and scale.

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
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': []})

```
Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a cohort-level multi-omic network. **DRAGON** is related to that result and scale.

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
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': []})

```
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
```

## Q4-d [groups/individual_change] witness: None/['individual_change']

> We profiled brains of 30 nurse and 30 forager honeybees, with RNA-seq and bisulfite methylation measured on each individual brain. Which individual bees have the most atypical methylation-expression wiring?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'individual_change', 'quote': 'Which individual bees have the most atypical methylation-expression wiring?'}]})

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'individual_change', 'quote': 'Which individual bees have the most atypical methylation-expression wiring?'}]})

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'individual_change', 'quote': 'Which individual bees have the most atypical methylation-expression wiring?'}]})

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'Which individual bees have the most atypical methylation-expression wiring?']]})

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

For your question ("Which individual bees have the most atypical methylation-expression wiring?"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
- **LIONESS-COEXPRESSION**, **BONOBO** — Comparing each sample's network with the rest of the cohort -- or, with repeated samples, with the same individual's other sample -- shows which individuals change or stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: With p-value output, edges can be filtered per sample at a chosen confidence.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['individual_change', 'Which individual bees have the most atypical methylation-expression wiring?']]})

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

For your question ("Which individual bees have the most atypical methylation-expression wiring?"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
- **LIONESS-COEXPRESSION**, **BONOBO** — Comparing each sample's network with the rest of the cohort -- or, with repeated samples, with the same individual's other sample -- shows which individuals change or stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: With p-value output, edges can be filtered per sample at a chosen confidence.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '30 nurse and 30 forager honeybees', 'claims': [['individual_change', 'Which individual bees have the most atypical methylation-expression wiring?']]})

```
For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## Q5-a [none/prediction] witness: None/['prediction']

> Expression arrays from 210 primary Ewing sarcoma tumours at diagnosis, along with a human TF motif prior and a protein interaction network. The aim is to forecast relapse risk for future patients from their individual networks.

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'prediction', 'quote': 'The aim is to forecast relapse risk for future patients from their individual networks.'}]})

```
About "The aim is to forecast relapse risk for future patients from their individual networks.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

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
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'prediction', 'quote': 'The aim is to forecast relapse risk for future patients from their individual networks.'}]})

```
About "The aim is to forecast relapse risk for future patients from their individual networks.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'prediction', 'quote': 'The aim is to forecast relapse risk for future patients from their individual networks.'}]})

```
About "The aim is to forecast relapse risk for future patients from their individual networks.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['prediction', 'to forecast relapse risk for future patients from their individual networks.']]})

```
About "to forecast relapse risk for future patients from their individual networks.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['prediction', 'to forecast relapse risk for future patients from their individual networks.']]})

```
About "to forecast relapse risk for future patients from their individual networks.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['prediction', 'to forecast relapse risk for future patients from their individual networks']]})

```
About "to forecast relapse risk for future patients from their individual networks": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## Q5-b [none/individual_change] witness: None/[]

> Expression arrays from 210 primary Ewing sarcoma tumours at diagnosis, along with a human TF motif prior and a protein interaction network. Which tumours have the most unusual regulatory wiring compared with the rest of the cohort?

### base r1

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

### base r2

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

### base r3

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

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

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

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'Which tumours have the most unusual regulatory wiring compared with the rest of the cohort?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which tumours have the most unusual regulatory wiring compared with the rest of the cohort?"):
- **LIONESS-PANDA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

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

## Q5-c [none/causal] witness: None/['causal']

> Expression arrays from 210 primary Ewing sarcoma tumours at diagnosis, along with a human TF motif prior and a protein interaction network. We hope to establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours.

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'We hope to establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours.'}]})

```
About "We hope to establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'We hope to establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours.'}]})

```
About "We hope to establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'We hope to establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours.'}]})

```
About "We hope to establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['causal', 'establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours']]})

```
About "establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['causal', 'establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours']]})

```
About "establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['causal', 'establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours']]})

```
About "establish that EWS-FLI1 binding directly causes the proliferation programme in these tumours": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## Q5-d [none/none] witness: None/[]

> Expression arrays from 210 primary Ewing sarcoma tumours at diagnosis, along with a human TF motif prior and a protein interaction network. Aim 1: describe the regulatory landscape and find TF-gene modules.

### base r1

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The expression arrays represent the gene expression profiles of the tumors.
- The human TF motif prior provides relevant information about transcription factors involved in regulation.
- The protein interaction network provides additional context for understanding TF-gene interactions.
- The integration of these datasets will yield insights into the regulatory modules present in Ewing sarcoma.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r2

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will utilize expression arrays from Ewing sarcoma tumors and a human TF motif prior.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### base r3

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

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

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

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

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

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The expression arrays provide the necessary data for constructing a coexpression network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## Q6-a [groups/regulator_change] witness: None/['regulator_change']

> Sample sheet: 32 rat lungs (RNA-seq), dose column 0/0.5/2.5/10 mg/m3 diesel exhaust, 8 rats per dose; rat motif and PPI priors available. Which TFs change their targeting most as dose increases?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which TFs change their targeting most as dose increases?'}]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which TFs change their targeting most as dose increases?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which TFs change their targeting most as dose increases?'}]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which TFs change their targeting most as dose increases?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which TFs change their targeting most as dose increases?'}]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which TFs change their targeting most as dose increases?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['regulator_change', 'Which TFs change their targeting most as dose increases?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which TFs change their targeting most as dose increases?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['regulator_change', 'Which TFs change their targeting most as dose increases?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which TFs change their targeting most as dose increases?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['regulator_change', 'Which TFs change their targeting most as dose increases?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("Which TFs change their targeting most as dose increases?"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## Q6-b [groups/causal] witness: None/['causal']

> Sample sheet: 32 rat lungs (RNA-seq), dose column 0/0.5/2.5/10 mg/m3 diesel exhaust, 8 rats per dose; rat motif and PPI priors available. Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?'}]})

```
About "Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The available rat motif and PPI priors can be utilized to construct the regulatory network.
- The RNA-seq data will provide sufficient information to infer the regulatory relationships.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?'}]})

```
About "Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Based on what you said — "Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?" — **GIRAFFE** fits better: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

**GIRAFFE** (recommend) — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values (one cohort-level result).

Conditional assumptions to confirm:
- It also needs files for the TF-motif prior and protein-interaction prior you mention; no file is named yet.

Other compatible option(s):
- If you need a TF-only regulatory network instead: **PANDA**, **LIONESS-PANDA**, **OTTER**.
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Should I use GIRAFFE, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?'}]})

```
About "Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

For “diesel-induced NF-kB activation”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

For “fibrotic gene switch-on”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['causal', 'show that diesel-induced NF-kB activation causes the fibrotic gene switch-on']]})

```
About "show that diesel-induced NF-kB activation causes the fibrotic gene switch-on": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['causal', 'show that diesel-induced NF-kB activation causes the fibrotic gene switch-on']]})

```
About "show that diesel-induced NF-kB activation causes the fibrotic gene switch-on": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Based on what you said — "Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?" — **GIRAFFE** fits better: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

**GIRAFFE** (recommend) — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values (one cohort-level result).

Conditional assumptions to confirm:
- It also needs files for the TF-motif prior and protein-interaction prior you mention; no file is named yet.

Other compatible option(s):
- If you need a TF-only regulatory network instead: **PANDA**, **LIONESS-PANDA**, **OTTER**.
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Should I use GIRAFFE, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['causal', 'show that diesel-induced NF-kB activation causes the fibrotic gene switch-on']]})

```
About "show that diesel-induced NF-kB activation causes the fibrotic gene switch-on": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Based on what you said — "Can we show that diesel-induced NF-kB activation causes the fibrotic gene switch-on?" — **GIRAFFE** fits better: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed.

Your question asks for a regulatory network. **GIRAFFE** fits that result.

**GIRAFFE** (recommend) — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network. Produces inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values (one cohort-level result).

Conditional assumptions to confirm:
- It also needs files for the TF-motif prior and protein-interaction prior you mention; no file is named yet.

Other compatible option(s):
- If you need a TF-only regulatory network instead: **PANDA**, **LIONESS-PANDA**, **OTTER**.
- If you need a TF/miRNA regulatory network instead: **PUMA**, **LIONESS-PUMA**.

TF activity is how active a TF is in each sample, apart from its own mRNA level. If you mean how strongly each TF is wired to its targets in each sample, the out-degree in LIONESS-PANDA's per-sample networks is the other reading, from the same inputs.

Should I use GIRAFFE, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## Q6-c [groups/prediction] witness: None/['prediction']

> Sample sheet: 32 rat lungs (RNA-seq), dose column 0/0.5/2.5/10 mg/m3 diesel exhaust, 8 rats per dose; rat motif and PPI priors available. Could network signatures predict the exposure level of rats in a future study?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'prediction', 'quote': 'Could network signatures predict the exposure level of rats in a future study?'}]})

```
About "Could network signatures predict the exposure level of rats in a future study?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The analysis will utilize the available rat motif and PPI priors.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'prediction', 'quote': 'Could network signatures predict the exposure level of rats in a future study?'}]})

```
About "Could network signatures predict the exposure level of rats in a future study?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'prediction', 'quote': 'Could network signatures predict the exposure level of rats in a future study?'}]})

```
About "Could network signatures predict the exposure level of rats in a future study?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The regulatory network can be inferred from the RNA-seq data of the rat lungs.
- The available motif and PPI priors can be utilized in the analysis.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['prediction', 'Could network signatures predict the exposure level of rats in a future study?']]})

```
About "Could network signatures predict the exposure level of rats in a future study?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The regulatory network can be inferred from the RNA-seq data of the rat lungs.
- The available motif and PPI priors can be utilized in the analysis.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['prediction', 'Could network signatures predict the exposure level of rats in a future study?']]})

```
About "Could network signatures predict the exposure level of rats in a future study?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The regulatory network can be inferred from the RNA-seq data of the rat lungs.
- The available motif and PPI priors can inform the regulatory network construction.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': [['prediction', 'Could network signatures predict the exposure level of rats in a future study?']]})

```
About "Could network signatures predict the exposure level of rats in a future study?": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The regulatory network can be inferred from the RNA-seq data of the rat lungs.
- The available motif and PPI priors can be utilized in the analysis.

Should the result be aggregate or sample-specific?

No files were inspected and no analysis ran.
```

## Q6-d [groups/none] witness: None/[]

> Sample sheet: 32 rat lungs (RNA-seq), dose column 0/0.5/2.5/10 mg/m3 diesel exhaust, 8 rats per dose; rat motif and PPI priors available. To begin with, I'm just after one regulatory network for rat lung.

### base r1

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

### base r2

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

### base r3

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': []})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': []})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '8 rats per dose; rat motif and PPI priors available.', 'claims': []})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## T1 [none/individual_change] witness: None/['causal', 'prediction']

> Bone-marrow RNA-seq from 45 patients with myelodysplastic syndrome, all sampled at diagnosis, with motif and PPI priors. Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.'}, {'claim': 'prediction', 'quote': 'Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.'}]})

```
About "Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

About "Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can show that one thing causes another or predict outcomes for new samples; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.'}, {'claim': 'prediction', 'quote': 'Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.'}]})

```
About "Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

About "Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can show that one thing causes another or predict outcomes for new samples; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'causal', 'quote': 'Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.'}, {'claim': 'prediction', 'quote': 'Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.'}]})

```
About "Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

About "Predicting progression or proving causality is off the table; we just want to see whose marrow networks stand out most.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can show that one thing causes another or predict outcomes for new samples; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'we just want to see whose marrow networks stand out most.']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("we just want to see whose marrow networks stand out most."):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'we just want to see whose marrow networks stand out most']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("we just want to see whose marrow networks stand out most"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': [['individual_change', 'we just want to see whose marrow networks stand out most']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("we just want to see whose marrow networks stand out most"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## T2 [none/none] witness: groups/[]

> Whole-blood RNA-seq from 52 long-COVID patients; matched healthy controls exist in our biobank but were deliberately not sequenced for this project. We want to sort the patients into molecular subtypes from their co-expression networks.

### base r1 (study purpose: {'source': None, 'design': 'groups', 'design_quote': 'Whole-blood RNA-seq from 52 long-COVID patients; matched healthy controls exist in our biobank but were deliberately not sequenced for this project.', 'claims': []})

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': 'groups', 'design_quote': 'Whole-blood RNA-seq from 52 long-COVID patients; matched healthy controls exist in our biobank but were deliberately not sequenced for this project.', 'claims': []})

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': 'groups', 'design_quote': 'Whole-blood RNA-seq from 52 long-COVID patients; matched healthy controls exist in our biobank but were deliberately not sequenced for this project.', 'claims': []})

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
Here is how registered workflows can reach this result, with their algorithmic premises and inputs:

Result: sample cluster assignment (aggregate), from expression matrix.
No registered workflow assigns samples to clusters from expression. A registered workflow can give each sample a feature profile to cluster on:
- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **LIONESS-PUMA** gives the same out-degree matrix with miRNAs among the regulators (needs a miRNA list).
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Required inputs: all of: expression matrix, motif/prior, PPI network, miRNA list.
- **GIRAFFE** gives its TF-by-sample activity matrix -- how active each TF is apart from its own mRNA level, a different reading from wiring.
  - Method premise: factor gene expression using motif and TF-protein interaction priors; jointly infer a TF-gene regulatory matrix and a TF-by-sample activity matrix
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
- **BONOBO** gives one gene co-expression network per sample; with about genes-squared edges each, summarize them first (for example per-gene degree).
  - Method premise: Bayesian shrinkage estimation of sample-specific co-expression; sparsify sample-specific co-expression and return matching p-value matrices
  - Required inputs: all of: expression matrix.
- **LIONESS-COEXPRESSION** gives one gene co-expression network per sample, summarized the same way.
  - Method premise: derive each sample network from all-sample and leave-one-out networks
  - Required inputs: all of: expression matrix.
Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.
Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, GIRAFFE, BONOBO or LIONESS-COEXPRESSION?

No files were inspected and no analysis ran.
```

## T3 [groups/group_difference] witness: None/[]

> RNA-seq of 24 bleached and 24 unbleached Acropora colonies sampled on the same reef during one heatwave; expression only. We ask whether gene co-expression differs between the two sets, leaving whether it drives bleaching to later transplant experiments.

### base r1

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### base r2

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### base r3

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': '24 bleached and 24 unbleached Acropora colonies sampled on the same reef during one heatwave', 'claims': [['group_difference', 'whether gene co-expression differs between the two sets']]})

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

For your question ("whether gene co-expression differs between the two sets"):
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': '24 bleached and 24 unbleached Acropora colonies sampled on the same reef during one heatwave', 'claims': [['group_difference', 'whether gene co-expression differs between the two sets']]})

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

For your question ("whether gene co-expression differs between the two sets"):
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': '24 bleached and 24 unbleached Acropora colonies sampled on the same reef during one heatwave', 'claims': [['group_difference', 'whether gene co-expression differs between the two sets']]})

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

For your question ("whether gene co-expression differs between the two sets"):
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

## T4 [groups/regulator_change] witness: None/['regulator_change']

> Testis biopsies from 18 men with non-obstructive and 18 with obstructive azoospermia: mRNA and small-RNA sequencing, motif and PPI priors, and predicted miRNA targets. Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?

### base r1 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?'}]})

```
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

For your question ("Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?'}]})

```
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

For your question ("Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': None, 'design_quote': '', 'claims': [{'claim': 'regulator_change', 'quote': 'Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?'}]})

```
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

For your question ("Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '18 men with non-obstructive and 18 with obstructive azoospermia', 'claims': [['regulator_change', 'Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?']]})

```
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

For your question ("Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '18 men with non-obstructive and 18 with obstructive azoospermia', 'claims': [['regulator_change', 'Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?']]})

```
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

For your question ("Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '18 men with non-obstructive and 18 with obstructive azoospermia', 'claims': [['regulator_change', 'Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?']]})

```
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

For your question ("Which miRNAs show the biggest difference in predicted regulatory influence between the two forms?"):
- **PUMA** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## T5 [paired/regulator_change] witness: groups/['causal', 'regulator_change']

> Matched tumour and adjacent normal cervix from 22 women with HPV-positive cervical cancer, RNA-seq, with motif and PPI priors. HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.

### base r1 (study purpose: {'source': None, 'design': 'groups', 'design_quote': 'Matched tumour and adjacent normal cervix from 22 women with HPV-positive cervical cancer, RNA-seq, with motif and PPI priors.', 'claims': [{'claim': 'causal', 'quote': 'HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.'}, {'claim': 'regulator_change', 'quote': 'HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.'}]})

```
About "HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour."):
- **PANDA**, **PUMA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### base r2 (study purpose: {'source': None, 'design': 'groups', 'design_quote': 'Matched tumour and adjacent normal cervix from 22 women with HPV-positive cervical cancer, RNA-seq, with motif and PPI priors.', 'claims': [{'claim': 'causal', 'quote': 'HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.'}, {'claim': 'regulator_change', 'quote': 'HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.'}]})

```
About "HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour."):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### base r3 (study purpose: {'source': None, 'design': 'groups', 'design_quote': 'Matched tumour and adjacent normal cervix from 22 women with HPV-positive cervical cancer, RNA-seq, with motif and PPI priors.', 'claims': [{'claim': 'causal', 'quote': 'HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.'}, {'claim': 'regulator_change', 'quote': 'HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.'}]})

```
About "HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("HPV is already known to cause these cancers; what we want is which transcription factors are most rewired in tumour."):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r1 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Matched tumour and adjacent normal cervix from 22 women with HPV-positive cervical cancer', 'claims': [['regulator_change', 'which transcription factors are most rewired in tumour']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("which transcription factors are most rewired in tumour"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Matched tumour and adjacent normal cervix from 22 women with HPV-positive cervical cancer', 'claims': [['regulator_change', 'which transcription factors are most rewired in tumour']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("which transcription factors are most rewired in tumour"):
- **PANDA**, **PUMA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'paired', 'design_quote': 'Matched tumour and adjacent normal cervix from 22 women with HPV-positive cervical cancer', 'claims': [['regulator_change', 'which transcription factors are most rewired in tumour']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

For your question ("which transcription factors are most rewired in tumour"):
- **PANDA**, **OTTER** — Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance.
- **LIONESS-PANDA** — Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators.
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## T6 [none/none] witness: None/[]

> Lungs from 30 mice, all harvested 21 days after influenza infection, RNA-seq with mouse motif and PPI priors. We want one regulatory network and to check whether TMM versus quantile normalisation changes it much.

### base r1

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **PUMA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **PUMA** — For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### base r2

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **PUMA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **PUMA** — For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The RNA-seq data from the 30 mice is suitable for regulatory network inference.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### base r3

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

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **PUMA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **PUMA** — For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r2

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The RNA-seq data from the 30 mice is suitable for regulatory network inference.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **PANDA**, **PUMA**, **OTTER** — Targeting scores: a regulator's outdegree or a gene's indegree summarizes the network per regulator or per gene; comparing them between networks built separately for each condition shows regulators whose targeting changes. Comparing conditions needs one run per condition on matched inputs (the same genes and the same motif and PPI priors); edge weights are comparable only within that shared setup.
- **PANDA** — For per-sample scores to test against clinical variables, use LIONESS-PANDA instead.
- **PUMA** — For per-sample scores to test against clinical variables, use LIONESS-PUMA instead.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.
- **OTTER** — OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.
- **GIRAFFE** — The TF-by-sample activity matrix (TFA) can serve as predictors in association tests with sample-level variables -- survival, for example, with a Cox model. Relating per-sample results to sample-level variables needs an annotation or clinical table keyed by the same sample IDs, supplied separately. Signs in the regulatory matrix are partial linear effects (positive for activation, negative for repression); read them as model coefficients, not as proof of direct binding.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## T7 [none/none] witness: None/[]

> Skin fibroblast RNA-seq from 140 adults with systemic sclerosis, collected at two hospitals over three years; expression matrix plus a site and year table. We need this cohort's gene co-expression structure with hospital and collection-year effects removed.

### base r1

```
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
```

### base r2

```
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
```

### base r3

```
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
```

### cand r1 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
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
```

### cand r2 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': None, 'design_quote': '', 'claims': []})

```
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
```

## T8 [groups/group_difference] witness: None/[]

> We ran 150-bp paired-end RNA-seq on dorsal root ganglia from 12 wild-type and 12 Scn9a-knockout mice, with mouse motif and PPI priors. Is the overall regulatory network different between genotypes?

### base r1

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

### base r2

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

### base r3

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

### cand r1 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '12 wild-type and 12 Scn9a-knockout mice', 'claims': [['group_difference', 'Is the overall regulatory network different between genotypes?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("Is the overall regulatory network different between genotypes?"):
- **PANDA**, **PUMA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r2 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '12 wild-type and 12 Scn9a-knockout mice', 'claims': [['group_difference', 'Is the overall regulatory network different between genotypes?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("Is the overall regulatory network different between genotypes?"):
- **PANDA**, **PUMA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### cand r3 (study purpose: {'source': 'model', 'design': 'groups', 'design_quote': '12 wild-type and 12 Scn9a-knockout mice', 'claims': [['group_difference', 'Is the overall regulatory network different between genotypes?']]})

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("Is the overall regulatory network different between genotypes?"):
- **PANDA**, **PUMA** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample (LIONESS) version and test between the groups.
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma.
- **OTTER** — Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use a per-sample method such as LIONESS-PANDA and test between the groups.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

# Minimal pairs `b0`

## A0

> We have RNA-seq from 24 patients, each sampled before and after treatment, plus TF motif and protein interaction data. We want a single regulatory network that summarizes all 48 samples.

### A0 r1

- status `ambiguous`, candidates ['run_giraffe', 'run_otter', 'run_panda', 'run_puma'], recommended None
- reason `The user is seeking guidance on how to obtain a regulatory network, which indica`; calls 7, $0.0027

Card:
```
4 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a cohort-level regulatory network from expression
    data.
  • Nothing has run yet.
  Full explanation: /details
[Regulators] Which regulator type should the network model: transcription factors, miRNA regulators, or both?
  Each answer lists the workflows it leads to.
  1) Transcription factors only
      Leads to PANDA, OTTER or GIRAFFE
  2) Both TFs and miRNAs
      Leads to PUMA · One TF + miRNA network across all your samples ·
      Also needs miRNA list
  Next: 3) Start a new task
```

Full reply:

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

### A0 r2

- status `ambiguous`, candidates ['run_giraffe', 'run_otter', 'run_panda', 'run_puma'], recommended None
- reason `The request is for guidance on obtaining a regulatory network, which falls under`; calls 7, $0.0020

Card:
```
4 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a cohort-level regulatory network from expression
    data.
  • Nothing has run yet.
  Full explanation: /details
[Regulators] Which regulator type should the network model: transcription factors, miRNA regulators, or both?
  Each answer lists the workflows it leads to.
  1) Transcription factors only
      Leads to PANDA, OTTER or GIRAFFE
  2) Both TFs and miRNAs
      Leads to PUMA · One TF + miRNA network across all your samples ·
      Also needs miRNA list
  Next: 3) Start a new task
```

Full reply:

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

### A0 r3

- status `ambiguous`, candidates ['run_giraffe', 'run_otter', 'run_panda', 'run_puma'], recommended None
- reason `The request is for guidance on obtaining a regulatory network, which falls under`; calls 7, $0.0019

Card:
```
4 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a cohort-level regulatory network from expression
    data.
  • Nothing has run yet.
  Full explanation: /details
[Regulators] Which regulator type should the network model: transcription factors, miRNA regulators, or both?
  Each answer lists the workflows it leads to.
  1) Transcription factors only
      Leads to PANDA, OTTER or GIRAFFE
  2) Both TFs and miRNAs
      Leads to PUMA · One TF + miRNA network across all your samples ·
      Also needs miRNA list
  Next: 3) Start a new task
```

Full reply:

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

## A1

> We have RNA-seq from 24 patients, each sampled before and after treatment, plus TF motif and protein interaction data. We want to know whether the regulatory network changes after treatment across the cohort.

### A1 r1

- status `ambiguous`, candidates ['run_giraffe', 'run_otter', 'run_panda', 'run_puma'], recommended None
- reason `The request is seeking guidance on how to determine changes in the regulatory ne`; calls 7, $0.0024

Card:
```
4 registered methods can build a cohort-level TF-gene regulatory network;
they differ in their modeling assumptions.
  • Understood goal: a cohort-level TF-gene regulatory network from
    expression data.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your question: whether the groups or time points differ; the reply
    says what PANDA, PUMA, OTTER and GIRAFFE give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Options that match more of what you asked for, and use only data you mentioned, come first.
  1) PANDA
      One TF-gene network across all your samples · Pick it if you
      want the standard published method or a base for LIONESS
  2) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  3) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  4) PUMA
      One TF + miRNA network across all your samples · Also adds miRNA
      regulators · Pick it if the regulators include miRNAs · Also
      needs miRNA list
  Next: 5) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("whether the regulatory network changes after treatment across the cohort"):
- **PANDA**, **PUMA** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use the per-sample (LIONESS) version and compare each individual's samples.
- **OTTER** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use a per-sample method such as LIONESS-PANDA and compare each individual's samples.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### A1 r2

- status `ambiguous`, candidates ['run_giraffe', 'run_otter', 'run_panda', 'run_puma'], recommended None
- reason `The user is seeking guidance on how to determine changes in the regulatory netwo`; calls 7, $0.0022

Card:
```
4 registered methods can build a cohort-level TF-gene regulatory network;
they differ in their modeling assumptions.
  • Understood goal: a cohort-level TF-gene regulatory network from
    expression data.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your question: whether the groups or time points differ; the reply
    says what PANDA, PUMA, OTTER and GIRAFFE give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Options that match more of what you asked for, and use only data you mentioned, come first.
  1) PANDA
      One TF-gene network across all your samples · Pick it if you
      want the standard published method or a base for LIONESS
  2) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  3) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  4) PUMA
      One TF + miRNA network across all your samples · Also adds miRNA
      regulators · Pick it if the regulators include miRNAs · Also
      needs miRNA list
  Next: 5) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("whether the regulatory network changes after treatment across the cohort"):
- **PANDA**, **PUMA** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use the per-sample (LIONESS) version and compare each individual's samples.
- **OTTER** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use a per-sample method such as LIONESS-PANDA and compare each individual's samples.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

### A1 r3

- status `ambiguous`, candidates ['run_giraffe', 'run_otter', 'run_panda', 'run_puma'], recommended None
- reason `The request is seeking guidance on how to determine changes in the regulatory ne`; calls 7, $0.0020

Card:
```
4 registered methods can build a cohort-level TF-gene regulatory network;
they differ in their modeling assumptions.
  • Understood goal: a cohort-level TF-gene regulatory network from
    expression data.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your question: whether the groups or time points differ; the reply
    says what PANDA, PUMA, OTTER and GIRAFFE give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Options that match more of what you asked for, and use only data you mentioned, come first.
  1) PANDA
      One TF-gene network across all your samples · Pick it if you
      want the standard published method or a base for LIONESS
  2) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  3) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  4) PUMA
      One TF + miRNA network across all your samples · Also adds miRNA
      regulators · Pick it if the regulators include miRNAs · Also
      needs miRNA list
  Next: 5) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

For your question ("whether the regulatory network changes after treatment across the cohort"):
- **PANDA**, **PUMA** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use the per-sample (LIONESS) version and compare each individual's samples.
- **OTTER** — Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. This compares the time points across all individuals but does not use the pairing: each individual's samples from the different time points are pooled into separate networks. To keep the pairing, use a per-sample method such as LIONESS-PANDA and compare each individual's samples.
- **GIRAFFE** — The activity matrix compares TF activity, not network wiring, between the conditions; test each TF's activity between them (paired when the same individuals give both).
Note: OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.

These all fit; to choose, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## A2

> We have RNA-seq from 24 patients, each sampled before and after treatment, plus TF motif and protein interaction data. We want to know which patients show the largest change in their own regulatory network after treatment.

### A2 r1

- status `ambiguous`, candidates ['run_lioness_panda', 'run_lioness_puma'], recommended None
- reason `The request is for guidance on identifying patients with changes in their regula`; calls 7, $0.0023

Card:
```
2 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a per-sample TF-gene regulatory network from
    expression data.
  • Your question: which individuals change or stand out; the reply says
    what LIONESS-PANDA and LIONESS-PUMA give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Regulators] Which regulator type should the network model: transcription factors, miRNA regulators, or both?
  Each answer lists the workflows it leads to.
  1) Transcription factors only
      Leads to LIONESS-PANDA · One TF-gene network per sample, plus
      the cohort network
  2) Both TFs and miRNAs
      Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus
      the cohort network · Also adds miRNA regulators · Also needs
      miRNA list
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

For your question ("which patients show the largest change in their own regulatory network after treatment"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each individual has a network for each time point; the difference between an individual's own networks (or their regulators' targeting scores) measures how much that individual changed, and ranks individuals by it.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

### A2 r2

- status `ambiguous`, candidates ['run_lioness_panda'], recommended None
- reason `The request is for guidance on identifying patients with the largest change in t`; calls 4, $0.0013

Card:
```
LIONESS-PANDA fits your goal: per-sample TF-gene regulatory network.
  • Method: One TF-gene network per sample, derived leave-one-out from
    the cohort.
  • Needs: expression matrix, motif prior, PPI network.
  • Cost: N samples take N+1 PANDA runs (for your 24 patients × 2
    samples each = 48 samples, 49 PANDA runs).
  • Produces: regulatory network (cohort-level and per-sample).
  • It also writes the cohort network, so PANDA need not run first.
  • Your question: which individuals change or stand out; the reply says
    what LIONESS-PANDA give toward it and the step after each.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
It sounds like you want sample-specific regulatory networks.

Registered method and input/output fit:
- **TF-only regulatory network — PANDA → LIONESS-PANDA**
  - Registered purpose: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks.
  - Method premise: derive each sample network from all-sample and leave-one-out networks; iteratively exchange information across biological evidence networks; the participating layers depend on the registered workflow
  - Mathematical interpretation: LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.
  - Mathematical interpretation: Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
  - Required inputs: all of: expression matrix, motif/prior, PPI network.
  - Declared output: regulatory networks (cohort-level aggregate; sample-specific, one network per sample).

For your question ("which patients show the largest change in their own regulatory network after treatment"):
- **LIONESS-PANDA** — Each individual has a network for each time point; the difference between an individual's own networks (or their regulators' targeting scores) measures how much that individual changed, and ranks individuals by it.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

The only registered workflow compatible with this request is **LIONESS-PANDA**, but it infers a regulatory network from its inputs, while your request reads as asking to analyze an existing result. Is LIONESS-PANDA the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

### A2 r3

- status `ambiguous`, candidates ['run_lioness_panda', 'run_lioness_puma'], recommended None
- reason `The request is for guidance on identifying patients with changes in their regula`; calls 7, $0.0019

Card:
```
2 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a per-sample TF-gene regulatory network from
    expression data.
  • Your question: which individuals change or stand out; the reply says
    what LIONESS-PANDA and LIONESS-PUMA give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Regulators] Which regulator type should the network model: transcription factors, miRNA regulators, or both?
  Each answer lists the workflows it leads to.
  1) Transcription factors only
      Leads to LIONESS-PANDA · One TF-gene network per sample, plus
      the cohort network
  2) Both TFs and miRNAs
      Leads to LIONESS-PUMA · One TF + miRNA network per sample, plus
      the cohort network · Also adds miRNA regulators · Also needs
      miRNA list
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

For your question ("which patients show the largest change in their own regulatory network after treatment"):
- **LIONESS-PANDA**, **LIONESS-PUMA** — Each individual has a network for each time point; the difference between an individual's own networks (or their regulators' targeting scores) measures how much that individual changed, and ranks individuals by it.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## A3

> We have RNA-seq from 24 patients, each sampled before and after treatment, plus TF motif and protein interaction data. We want to know which transcription factors change their regulatory activity most after treatment.

### A3 r1

- status `exact`, candidates ['run_giraffe'], recommended None
- reason `The request is for guidance on identifying transcription factors with significan`; calls 5, $0.0018

Card:
```
GIRAFFE fits your goal: cohort-level TF activity matrix.
  • Method: Also estimates per-sample TF activity and signed
    activating/repressing effects.
  • Needs: expression matrix, motif prior, PPI network.
  • Produces: regulatory network and TF activity matrix (one cohort-
    level result).
  • Your question: which regulators change most; the reply says what
    GIRAFFE give toward it and the step after each.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

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

For your question ("which transcription factors change their regulatory activity most after treatment"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### A3 r2

- status `exact`, candidates ['run_giraffe'], recommended None
- reason `The request is for guidance on identifying transcription factors with significan`; calls 5, $0.0013

Card:
```
GIRAFFE fits your goal: cohort-level TF activity matrix.
  • Method: Also estimates per-sample TF activity and signed
    activating/repressing effects.
  • Needs: expression matrix, motif prior, PPI network.
  • Produces: regulatory network and TF activity matrix (one cohort-
    level result).
  • Your question: which regulators change most; the reply says what
    GIRAFFE give toward it and the step after each.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

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

For your question ("which transcription factors change their regulatory activity most after treatment"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

### A3 r3

- status `exact`, candidates ['run_giraffe'], recommended None
- reason `Semantic interpretation did not classify this request as explicit execution; no `; calls 5, $0.0013

Card:
```
GIRAFFE fits your goal: cohort-level TF activity matrix.
  • Method: Also estimates per-sample TF activity and signed
    activating/repressing effects.
  • Needs: expression matrix, motif prior, PPI network.
  • Produces: regulatory network and TF activity matrix (one cohort-
    level result).
  • Your question: which regulators change most; the reply says what
    GIRAFFE give toward it and the step after each.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

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

For your question ("which transcription factors change their regulatory activity most after treatment"):
- **GIRAFFE** — GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction.

This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## A4

> We have RNA-seq from 24 patients, each sampled before and after treatment, plus TF motif and protein interaction data. We want to show that the treatment itself causes changes in gene regulation.

### A4 r1

- status `ambiguous`, candidates ['run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'], recommended None
- reason `The request is for guidance on demonstrating treatment effects on gene regulatio`; calls 7, $0.0023

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
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
About "show that the treatment itself causes changes in gene regulation": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### A4 r2

- status `ambiguous`, candidates ['run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'], recommended None
- reason `The request is for guidance on demonstrating treatment effects on gene regulatio`; calls 7, $0.0020

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
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
About "show that the treatment itself causes changes in gene regulation": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

### A4 r3

- status `ambiguous`, candidates ['run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'], recommended None
- reason `The request is for guidance on demonstrating treatment effects on gene regulatio`; calls 7, $0.0019

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
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
About "show that the treatment itself causes changes in gene regulation": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## A5

> We have RNA-seq from 24 patients, each sampled before and after treatment, plus TF motif and protein interaction data. We want to know whether the patients' gene regulation changes after treatment.

### A5 r1

- status `ambiguous`, candidates ['run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'], recommended None
- reason `The request is for guidance on determining changes in gene regulation, which fal`; calls 7, $0.0024

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
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

### A5 r2

- status `ambiguous`, candidates ['run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'], recommended None
- reason `The request is for guidance on determining changes in gene regulation, which fal`; calls 7, $0.0020

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
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

### A5 r3

- status `ambiguous`, candidates ['run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'], recommended None
- reason `The request is for guidance on determining changes in gene regulation, which fal`; calls 7, $0.0020

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
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

## B1

> We have bulk RNA-seq from 60 tumors, 30 from immunotherapy responders and 30 from non-responders, and no other data. We want to know whether gene co-expression differs between responders and non-responders.

### B1 r1

- status `ambiguous`, candidates ['run_cobra', 'run_lioness_coexpression'], recommended None
- reason `The request is for guidance on analyzing gene co-expression differences, which f`; calls 7, $0.0022

Card:
```
2 registered methods can build a cohort-level co-expression network; they
differ in their modeling assumptions.
  • Understood goal: a cohort-level co-expression network from
    expression data.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your question: whether the groups or time points differ; the reply
    says what LIONESS-COEXPRESSION and COBRA give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Nothing you said favours one of them; each line says when to pick it.
  1) LIONESS-COEXPRESSION
      One gene co-expression network per sample, from expression data
      alone · Pick it if no covariates need adjusting
  2) COBRA
      Co-expression split into the parts your covariates (batch, site,
      condition) explain and the rest · Pick it if batch, site or
      covariates must be separated
  Next: 3) Start a new task
```

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

For your question ("whether gene co-expression differs between responders and non-responders"):
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### B1 r2

- status `ambiguous`, candidates ['run_cobra', 'run_lioness_coexpression'], recommended None
- reason `The request is for guidance on analyzing gene co-expression differences, which f`; calls 7, $0.0020

Card:
```
2 registered methods can build a cohort-level co-expression network; they
differ in their modeling assumptions.
  • Understood goal: a cohort-level co-expression network from
    expression data.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your question: whether the groups or time points differ; the reply
    says what LIONESS-COEXPRESSION and COBRA give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Nothing you said favours one of them; each line says when to pick it.
  1) LIONESS-COEXPRESSION
      One gene co-expression network per sample, from expression data
      alone · Pick it if no covariates need adjusting
  2) COBRA
      Co-expression split into the parts your covariates (batch, site,
      condition) explain and the rest · Pick it if batch, site or
      covariates must be separated
  Next: 3) Start a new task
```

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

For your question ("whether gene co-expression differs between responders and non-responders"):
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

### B1 r3

- status `ambiguous`, candidates ['run_cobra', 'run_lioness_coexpression'], recommended None
- reason `The request is for guidance on analyzing gene co-expression differences, which f`; calls 7, $0.0019

Card:
```
2 registered methods can build a cohort-level co-expression network; they
differ in their modeling assumptions.
  • Understood goal: a cohort-level co-expression network from
    expression data.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your question: whether the groups or time points differ; the reply
    says what LIONESS-COEXPRESSION and COBRA give toward it and the step
    after each.
  • Nothing has run yet.
  Full explanation: /details
[Method] Which method fits your study?
  Nothing you said favours one of them; each line says when to pick it.
  1) LIONESS-COEXPRESSION
      One gene co-expression network per sample, from expression data
      alone · Pick it if no covariates need adjusting
  2) COBRA
      Co-expression split into the parts your covariates (batch, site,
      condition) explain and the rest · Pick it if batch, site or
      covariates must be separated
  Next: 3) Start a new task
```

Full reply:

```
Several registered methods fit this result; they differ in their modeling assumptions:

- **LIONESS-COEXPRESSION** — LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. Needs expression matrix.
- **COBRA** — COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Needs expression matrix and sample covariate design matrix.

For your question ("whether gene co-expression differs between responders and non-responders"):
- **LIONESS-COEXPRESSION** — Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both).
- **COBRA** — Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch.
Note: All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.
Note: Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis.

Both fit; to choose, tell me: (1) Do you need to separate or adjust co-expression for batch, site or other sample covariates? (co-expression must be separated or adjusted for batch, site or other covariates → COBRA; no sample covariates need to be separated or adjusted → LIONESS-COEXPRESSION)

No files were inspected and no analysis ran.
```

## B2

> We have bulk RNA-seq from 60 tumors, 30 from immunotherapy responders and 30 from non-responders, and no other data. We want to know whether the non-responders split into distinct subgroups.

### B2 r1

- status `ambiguous`, candidates [], recommended None
- reason `The request is for guidance on how to determine if non-responders can be classif`; calls 5, $0.0016

Card:
```
No single registered workflow takes every stated input together.
  • Nothing has run yet.
  Full explanation: /details
[Reading] Which reading should we start with?
  In the order your request states them.
  1) Reading 1: “We want to know whether the non-responders split into…”
      A per-sample profile from LIONESS-PANDA, LIONESS-PUMA, GIRAFFE,
      BONOBO or LIONESS-COEXPRESSION · Then clustering outside NetZoo
  Next: 2) Start a new task
```

Full reply:

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

### B2 r2

- status `ambiguous`, candidates [], recommended None
- reason `The request is for guidance on determining if non-responders can be classified i`; calls 5, $0.0019

Card:
```
No single registered workflow takes every stated input together.
  • Nothing has run yet.
  Full explanation: /details
[Reading] Which reading should we start with?
  In the order your request states them.
  1) Reading 1: “We want to know whether the non-responders split into…”
      A per-sample profile from LIONESS-PANDA, LIONESS-PUMA, GIRAFFE,
      BONOBO or LIONESS-COEXPRESSION · Then clustering outside NetZoo
  Next: 2) Start a new task
```

Full reply:

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

### B2 r3

- status `ambiguous`, candidates [], recommended None
- reason `The request is for guidance on classifying non-responders into distinct subgroup`; calls 5, $0.0015

Card:
```
No single registered workflow takes every stated input together.
  • Nothing has run yet.
  Full explanation: /details
[Reading] Which reading should we start with?
  In the order your request states them.
  1) Reading 1: “We want to know whether the non-responders split into…”
      A per-sample profile from LIONESS-PANDA, LIONESS-PUMA, GIRAFFE,
      BONOBO or LIONESS-COEXPRESSION · Then clustering outside NetZoo
  Next: 2) Start a new task
```

Full reply:

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

## B3

> We have bulk RNA-seq from 60 tumors, 30 from immunotherapy responders and 30 from non-responders, and no other data. We want a model that predicts whether a new patient will respond.

### B3 r1

- status `ambiguous`, candidates ['run_giraffe', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_panda', 'run_puma'], recommended None
- reason `The request is for guidance on developing a predictive model, which falls under `; calls 7, $0.0025

Card:
```
6 registered methods can build a regulatory network; they differ in scale
(one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a regulatory network from expression data.
  • Your request names only expression data; the matched workflows need
    more inputs, while LIONESS-COEXPRESSION or BONOBO works from it
    alone.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "a model that predicts whether a new patient will respond": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

**What your data allows.** Your request names only expression data. PANDA, LIONESS-PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network; PUMA and LIONESS-PUMA also need a motif prior, a PPI network and a miRNA list. With expression data alone, LIONESS-COEXPRESSION or BONOBO builds a gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

### B3 r2

- status `None`, candidates [], recommended None
- reason `Semantic routing output failed validation, so no workflow was selected. (ValueEr`; calls 3, $0.0019

Card:
```
No registered workflow can do this: predict outcomes for new samples.
  • No registered workflow builds a predictive model; per-sample results
    can only be its features.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
About "a model that predicts whether a new patient will respond": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

### B3 r3

- status `None`, candidates [], recommended None
- reason `Semantic routing output failed validation, so no workflow was selected. (ValueEr`; calls 3, $0.0013

Card:
```
No registered workflow can do this: predict outcomes for new samples.
  • No registered workflow builds a predictive model; per-sample results
    can only be its features.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
About "a model that predicts whether a new patient will respond": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

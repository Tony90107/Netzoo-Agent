# Capability traps `b0`

## ct-b0-U1-1

> We profiled RNA-seq from 60 colorectal tumors, half of which later relapsed. We want to prove which transcription factors causally drive relapse, not merely correlate with it. Which analysis gives that causal answer?

- core: causal proof that specific TFs drive relapse
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Every option also needs motif prior and PPI network, which your
    request does not mention.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA,
    OTTER, GIRAFFE and PUMA give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your stated concern is answered per method in the full explanation.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
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
About "We want to prove which transcription factors causally drive relapse, not merely correlate with it.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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
- The analysis will focus on the relationship between transcription factors and relapse in colorectal tumors.
- Causal inference methods will be applied to establish the directionality of the relationships.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## ct-b0-U1-2

> We profiled RNA-seq from 60 colorectal tumors, half of which later relapsed. We want to prove which transcription factors causally drive relapse, not merely correlate with it. Which analysis gives that causal answer?

- core: causal proof that specific TFs drive relapse
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Every option also needs motif prior and PPI network, which your
    request does not mention.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA,
    OTTER, GIRAFFE and PUMA give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your stated concern is answered per method in the full explanation.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
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
About "We want to prove which transcription factors causally drive relapse, not merely correlate with it.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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
- The analysis should focus on causal relationships rather than mere correlations.
- The data from the RNA-seq profiling is suitable for inferring regulatory networks.
- The data from the RNA-seq profiling is suitable for inferring signed regulatory effects.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## ct-b0-U1-3

> We profiled RNA-seq from 60 colorectal tumors, half of which later relapsed. We want to prove which transcription factors causally drive relapse, not merely correlate with it. Which analysis gives that causal answer?

- core: causal proof that specific TFs drive relapse
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data.
  • Every option also needs motif prior and PPI network, which your
    request does not mention.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA,
    OTTER, GIRAFFE and PUMA give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Your stated concern is answered per method in the full explanation.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
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
About "We want to prove which transcription factors causally drive relapse, not merely correlate with it.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

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
- The analysis will involve causal inference methods to establish the relationship between transcription factors and relapse.
- The analysis will focus on the causal effects of transcription factors on the relapse of colorectal tumors.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## ct-b0-U2-1

> We sampled yeast every ten minutes for four hours after heat shock. We want a dynamical model that forecasts each gene's expression at later time points from its regulators' earlier levels. How should we build it?

- core: a dynamical model forecasting future expression from earlier regulator levels
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "forecasts each gene's expression at later time points from its regulators' earlier levels": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## ct-b0-U2-2

> We sampled yeast every ten minutes for four hours after heat shock. We want a dynamical model that forecasts each gene's expression at later time points from its regulators' earlier levels. How should we build it?

- core: a dynamical model forecasting future expression from earlier regulator levels
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA,
    OTTER, GIRAFFE and PUMA give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "forecasts each gene's expression at later time points from its regulators' earlier levels": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## ct-b0-U2-3

> We sampled yeast every ten minutes for four hours after heat shock. We want a dynamical model that forecasts each gene's expression at later time points from its regulators' earlier levels. How should we build it?

- core: a dynamical model forecasting future expression from earlier regulator levels
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "We want a dynamical model that forecasts each gene's expression at later time points from its regulators' earlier levels.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## ct-b0-U3-1

> We have single-cell RNA-seq of differentiating T cells. We want to order the cells along a pseudotime trajectory and find the branch point where cells commit to helper versus cytotoxic fates.

- core: pseudotime ordering and a fate branch point
- status `ambiguous`, in_scope True, artifact `unknown`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_lioness_coexpression', 'run_cobra', 'run_dragon', 'run_lioness_dragon', 'run_otter', 'run_giraffe', 'run_bonobo'], recommended [], advised None, model-written False

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## ct-b0-U3-2

> We have single-cell RNA-seq of differentiating T cells. We want to order the cells along a pseudotime trajectory and find the branch point where cells commit to helper versus cytotoxic fates.

- core: pseudotime ordering and a fate branch point
- status `ambiguous`, in_scope True, artifact `unknown`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_lioness_coexpression', 'run_cobra', 'run_dragon', 'run_lioness_dragon', 'run_otter', 'run_giraffe', 'run_bonobo'], recommended [], advised None, model-written False

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## ct-b0-U3-3

> We have single-cell RNA-seq of differentiating T cells. We want to order the cells along a pseudotime trajectory and find the branch point where cells commit to helper versus cytotoxic fates.

- core: pseudotime ordering and a fate branch point
- status `ambiguous`, in_scope True, artifact `unknown`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_lioness_coexpression', 'run_cobra', 'run_dragon', 'run_lioness_dragon', 'run_otter', 'run_giraffe', 'run_bonobo'], recommended [], advised None, model-written False

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

**Single-cell data.** The registered workflows are built for bulk samples. Co-expression between individual cells is dominated by dropout, so per-cell LIONESS or BONOBO networks are not advised. A registered route: sum cells into pseudo-bulk profiles per donor and cell state, then run PANDA (or OTTER) once per state with the same genes and the same motif and PPI priors; this needs several donors per state to estimate co-expression. To look within a state, SCORPION (an R package from the Kuijjer lab, not registered here) first aggregates similar cells into metacells and then runs PANDA on them, giving comparable networks per sample or state.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## ct-b0-U4-1

> Using pretreatment tumor expression from 200 melanoma patients with known immunotherapy outcomes, we want to train a classifier that predicts which new patients will respond and report its cross-validated accuracy.

- core: a trained response classifier with cross-validated accuracy
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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

## ct-b0-U4-2

> Using pretreatment tumor expression from 200 melanoma patients with known immunotherapy outcomes, we want to train a classifier that predicts which new patients will respond and report its cross-validated accuracy.

- core: a trained response classifier with cross-validated accuracy
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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

## ct-b0-U4-3

> Using pretreatment tumor expression from 200 melanoma patients with known immunotherapy outcomes, we want to train a classifier that predicts which new patients will respond and report its cross-validated accuracy.

- core: a trained response classifier with cross-validated accuracy
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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

## ct-b0-U5-1

> We have RNA-seq from 30 treated and 30 untreated mouse livers. We need the genes significantly differentially expressed between groups, with fold changes and FDR-adjusted p-values, for a volcano plot.

- core: differentially expressed genes with fold changes and FDR p-values
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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

## ct-b0-U5-2

> We have RNA-seq from 30 treated and 30 untreated mouse livers. We need the genes significantly differentially expressed between groups, with fold changes and FDR-adjusted p-values, for a volcano plot.

- core: differentially expressed genes with fold changes and FDR p-values
- status `ambiguous`, in_scope True, artifact `expression_matrix`, matched [], candidates [], recommended [], advised None, model-written False

Card:
```
I need one more detail before choosing a workflow.
  • Which scientific result do you want NetZoo to produce?
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## ct-b0-U5-3

> We have RNA-seq from 30 treated and 30 untreated mouse livers. We need the genes significantly differentially expressed between groups, with fold changes and FDR-adjusted p-values, for a volcano plot.

- core: differentially expressed genes with fold changes and FDR p-values
- status `ambiguous`, in_scope True, artifact `expression_matrix`, matched [], candidates [], recommended [], advised None, model-written False

Card:
```
I need one more detail before choosing a workflow.
  • Which scientific result do you want NetZoo to produce?
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## ct-b0-U6-1

> We have spatial transcriptomics sections of breast tumors. We want to estimate the cell-type proportions within each spot and map where immune cells infiltrate the tumor margin.

- core: per-spot cell-type proportions (spatial deconvolution)
- status `ambiguous`, in_scope True, artifact `unknown`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_lioness_coexpression', 'run_condor', 'run_cobra', 'run_sambar', 'run_dragon', 'run_lioness_dragon', 'run_otter', 'run_giraffe', 'run_bonobo'], recommended [], advised None, model-written False

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## ct-b0-U6-2

> We have spatial transcriptomics sections of breast tumors. We want to estimate the cell-type proportions within each spot and map where immune cells infiltrate the tumor margin.

- core: per-spot cell-type proportions (spatial deconvolution)
- status `ambiguous`, in_scope True, artifact `unknown`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_lioness_coexpression', 'run_condor', 'run_cobra', 'run_sambar', 'run_dragon', 'run_lioness_dragon', 'run_otter', 'run_giraffe', 'run_bonobo'], recommended [], advised None, model-written False

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## ct-b0-U6-3

> We have spatial transcriptomics sections of breast tumors. We want to estimate the cell-type proportions within each spot and map where immune cells infiltrate the tumor margin.

- core: per-spot cell-type proportions (spatial deconvolution)
- status `ambiguous`, in_scope True, artifact `unknown`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_lioness_coexpression', 'run_condor', 'run_cobra', 'run_sambar', 'run_dragon', 'run_lioness_dragon', 'run_otter', 'run_giraffe', 'run_bonobo'], recommended [], advised None, model-written False

Full reply:

```
There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

**PANDA**. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

**PUMA**. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations.

**LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations. LIONESS-PANDA also writes the cohort network, so PANDA need not run first.

**LIONESS-PUMA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network, miRNA list. The analysis would provide inferred regulator-to-target associations. LIONESS-PUMA also writes the cohort network, so PUMA need not run first.

**LIONESS-COEXPRESSION**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

**COBRA**. COBRA models co-expression as a function of sample covariates through conditional covariance estimation. Correcting gene means alone may leave covariance confounding. Covariate-associated components are not TF-to-gene regulatory edges or proof that a covariate causes the expression pattern.

You would need expression matrix, sample covariate design matrix. The analysis would provide inferred gene-to-gene associations.

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide sample-by-gene mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

**DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**LIONESS-DRAGON**. DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring.

You would need DRAGON omics layer 1, DRAGON omics layer 2. The analysis would provide inferred associations between omics features.

**OTTER**. OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Its lambda balances those two fit terms and gamma regularizes W; a PPI-transformed motif matrix initializes W rather than contributing a motif-fidelity term to that loss. Neither parameter estimates motif-prior reliability, and optimized edge scores are not posterior probabilities.

You would need motif/prior, PPI network, either expression matrix or adjusted co-expression matrix. The analysis would provide inferred regulator-to-target associations.

**GIRAFFE**. GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations; inferred transcription-factor-by-sample activity values.

**BONOBO**. BONOBO applies Bayesian estimation and shrinkage to sample-specific gene-gene co-expression. It does not model uncertain TF-binding/motif priors or return TF-to-gene regulatory edges. A shared probabilistic philosophy does not make these scientific outputs interchangeable.

You would need expression matrix. The analysis would provide inferred gene-to-gene associations; p-value matrix paired with a sample-specific gene-gene co-expression result.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
```

## ct-b0-U7-1

> We have isoform-level quantifications from 80 brain samples. We want to find which splicing factors control inclusion of each alternative exon and build a splicing regulatory map.

- core: which splicing factors control each alternative exon
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • Your request names only the data I described; the matched workflows
    need more inputs, which the request does not mention.
  • Nothing has run yet.
  Full explanation: /details
[Inputs] Do you also have a motif prior and a PPI network?
  The option that uses only the data you named comes first.
  1) Only the data I described
      Ask what the data you named can give instead
  2) I also have a motif prior and a PPI network
      Continues with the workflows this reply names
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

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## ct-b0-U7-2

> We have isoform-level quantifications from 80 brain samples. We want to find which splicing factors control inclusion of each alternative exon and build a splicing regulatory map.

- core: which splicing factors control each alternative exon
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • Your request names only the data I described; the matched workflows
    need more inputs, which the request does not mention.
  • Nothing has run yet.
  Full explanation: /details
[Inputs] Do you also have a motif prior and a PPI network?
  The option that uses only the data you named comes first.
  1) Only the data I described
      Ask what the data you named can give instead
  2) I also have a motif prior and a PPI network
      Continues with the workflows this reply names
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

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## ct-b0-U7-3

> We have isoform-level quantifications from 80 brain samples. We want to find which splicing factors control inclusion of each alternative exon and build a splicing regulatory map.

- core: which splicing factors control each alternative exon
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • Your request names only the data I described; the matched workflows
    need more inputs, which the request does not mention.
  • Nothing has run yet.
  Full explanation: /details
[Inputs] Do you also have a motif prior and a PPI network?
  The option that uses only the data you named comes first.
  1) Only the data I described
      Ask what the data you named can give instead
  2) I also have a motif prior and a PPI network
      Continues with the workflows this reply names
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

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

**What your data allows.** PANDA, LIONESS-PANDA and GIRAFFE also need an expression matrix, a motif prior and a PPI network; OTTER also needs a motif prior, a PPI network and an expression matrix or adjusted co-expression matrix. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## ct-b0-U8-1

> We have proteomics and metabolomics from 50 plasma samples and want to estimate metabolic flux through glycolysis and the TCA cycle for each person. Which approach should we use?

- core: per-person metabolic flux through glycolysis and the TCA cycle
- status `fallback`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates ['run_dragon'], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON is the closest registered match, but it is not a verified match for
your request.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

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

## ct-b0-U8-2

> We have proteomics and metabolomics from 50 plasma samples and want to estimate metabolic flux through glycolysis and the TCA cycle for each person. Which approach should we use?

- core: per-person metabolic flux through glycolysis and the TCA cycle
- status `fallback`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates ['run_dragon'], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON is the closest registered match, but it is not a verified match for
your request.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The user has access to appropriate computational tools for multi-omic analysis.
- The proteomics and metabolomics data are of sufficient quality to support flux estimation.
- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

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

## ct-b0-U8-3

> We have proteomics and metabolomics from 50 plasma samples and want to estimate metabolic flux through glycolysis and the TCA cycle for each person. Which approach should we use?

- core: per-person metabolic flux through glycolysis and the TCA cycle
- status `fallback`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates ['run_dragon'], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON is the closest registered match, but it is not a verified match for
your request.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Assumptions behind this recommendation (not confirmed facts):

- The user has access to appropriate computational tools for multi-omic analysis.
- The metabolic pathways of interest are well-defined and can be modeled using the available data.
- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

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

## ct-b0-N1-1

> With our tumor RNA-seq, motif data and a protein interaction map, we want to identify which transcription factors physically assemble into complexes and estimate the stoichiometry of each complex.

- core: which TFs physically assemble into complexes, and complex stoichiometry
- status `ambiguous`, in_scope True, artifact `multi_omic_network`, matched [], candidates [], recommended [], advised None, model-written False

Card:
```
I need one more detail before choosing a workflow.
  • Which scientific result do you want NetZoo to produce?
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## ct-b0-N1-2

> With our tumor RNA-seq, motif data and a protein interaction map, we want to identify which transcription factors physically assemble into complexes and estimate the stoichiometry of each complex.

- core: which TFs physically assemble into complexes, and complex stoichiometry
- status `ambiguous`, in_scope True, artifact `multi_omic_network`, matched [], candidates [], recommended [], advised None, model-written False

Card:
```
I need one more detail before choosing a workflow.
  • Which scientific result do you want NetZoo to produce?
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
I cannot select a workflow until the requested result is clear. Which scientific result do you want NetZoo to produce?

No files were inspected and no analysis ran.
```

## ct-b0-N1-3

> With our tumor RNA-seq, motif data and a protein interaction map, we want to identify which transcription factors physically assemble into complexes and estimate the stoichiometry of each complex.

- core: which TFs physically assemble into complexes, and complex stoichiometry
- status `ambiguous`, in_scope True, artifact `multi_omic_network`, matched [], candidates ['run_dragon'], recommended [], advised None, model-written False

Card:
```
DRAGON fits your goal: cohort-level multi-omic network.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
It sounds like you want aggregate TF multi omic network.

Registered method and input/output fit:
- **Multi omic network — DRAGON**
  - Registered purpose: Infer an aggregate two-layer multi-omic Gaussian graphical model with DRAGON.
  - Method premise: infer conditional associations using partial correlation; DRAGON uses two layer-specific shrinkage parameters, lambda1 and lambda2, rather than a generic Graphical Lasso penalty matrix.
  - Mathematical interpretation: DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage. Partial correlations describe associations conditional on the other measured features under that model; they are not directed causal effects. The two omics layers must refer to matched samples.
  - Required inputs: all of: DRAGON omics layer 1, DRAGON omics layer 2.
  - Declared output: multi omic network (cohort-level aggregate).

The only registered workflow compatible with this request is **DRAGON**. Is DRAGON the analysis you want? If so, say so and name its inputs; otherwise describe the result you need.

No files were inspected and no analysis ran.
```

## ct-b0-N2-1

> From our liver expression data with motif and protein interaction priors, we want to simulate knocking out one transcription factor and predict how much each target gene's expression would change.

- core: a simulated knockout predicting each target gene's expression change
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data,
    a motif prior and a PPI network.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "predict how much each target gene's expression would change": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## ct-b0-N2-2

> From our liver expression data with motif and protein interaction priors, we want to simulate knocking out one transcription factor and predict how much each target gene's expression would change.

- core: a simulated knockout predicting each target gene's expression change
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data,
    a motif prior and a PPI network.
  • Only LIONESS-PANDA gives one network per sample; PANDA, OTTER and
    GIRAFFE give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "predict how much each target gene's expression would change": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## ct-b0-N2-3

> From our liver expression data with motif and protein interaction priors, we want to simulate knocking out one transcription factor and predict how much each target gene's expression would change.

- core: a simulated knockout predicting each target gene's expression change
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network from expression data,
    a motif prior and a PPI network.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; PANDA,
    OTTER, GIRAFFE and PUMA give one across all samples.
  • Nothing you said favours one method yet; each option says when to
    pick it.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "predict how much each target gene's expression would change": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Per-sample version: **LIONESS-PUMA**. Needs expression matrix, motif/prior, PPI network and miRNA list.

Unconfirmed assumptions in these interpretations (please correct me if needed):
- The expression data includes relevant target genes and their interactions with the transcription factor.
- Motif and protein interaction priors are available to inform the regulatory network inference.

These fit the result you described, but none can predict outcomes for new samples; to choose among them, tell me: (1) Do the regulators include miRNAs, short non-coding RNAs that repress or degrade their target transcripts after transcription? (yes → PUMA, LIONESS-PUMA) (2) Is the network large enough that memory or runtime is a concern? (yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA, GIRAFFE.

No files were inspected and no analysis ran.
```

## ct-b0-N3-1

> We built a TF-gene network from 120 kidney samples. Now we want to determine, for each pair of transcription factors, which one activates the other, giving the causal direction of every TF-TF edge.

- core: the causal direction of every TF-TF edge
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

Card:
```
No registered workflow can do this: show that one thing causes another.
  • Registered workflows estimate associations; they can describe what
    changes, not prove its cause.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
About "which one activates the other, giving the causal direction of every TF-TF edge": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## ct-b0-N3-2

> We built a TF-gene network from 120 kidney samples. Now we want to determine, for each pair of transcription factors, which one activates the other, giving the causal direction of every TF-TF edge.

- core: the causal direction of every TF-TF edge
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

Card:
```
No registered workflow can do this: show that one thing causes another.
  • Registered workflows estimate associations; they can describe what
    changes, not prove its cause.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
About "which one activates the other, giving the causal direction of every TF-TF edge.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## ct-b0-N3-3

> We built a TF-gene network from 120 kidney samples. Now we want to determine, for each pair of transcription factors, which one activates the other, giving the causal direction of every TF-TF edge.

- core: the causal direction of every TF-TF edge
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

Card:
```
No registered workflow can do this: show that one thing causes another.
  • Registered workflows estimate associations; they can describe what
    changes, not prove its cause.
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
About "which one activates the other, giving the causal direction of every TF-TF edge.": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

If you want to describe what differs or changes, say which comparison you mean and the data you have.

No files were inspected and no analysis ran.
```

## ct-b0-N4-1

> We have ChIP-seq peaks for an uncharacterized transcription factor and expression data from the same cells. We want to discover its binding motif de novo and then find its target genes genome-wide.

- core: de novo discovery of the TF's binding motif from ChIP-seq peaks
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
3 registered methods can build a cohort-level TF-gene regulatory network;
they differ in their modeling assumptions.
  • Understood goal: a cohort-level TF-gene regulatory network from
    expression data, a motif prior and a PPI network.
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
  2) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  3) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  Next: 4) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## ct-b0-N4-2

> We have ChIP-seq peaks for an uncharacterized transcription factor and expression data from the same cells. We want to discover its binding motif de novo and then find its target genes genome-wide.

- core: de novo discovery of the TF's binding motif from ChIP-seq peaks
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
3 registered methods can build a cohort-level TF-gene regulatory network;
they differ in their modeling assumptions.
  • Understood goal: a cohort-level TF-gene regulatory network from
    expression data.
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
      Leads to PANDA, OTTER or GIRAFFE
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

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

**What your data allows.** Your request names only expression data. PANDA, OTTER and GIRAFFE also need a motif prior and a PPI network. With expression data alone, LIONESS-COEXPRESSION builds one cohort-level gene-gene co-expression network (genes only, no regulator roles) instead. Do you also have a motif prior and a PPI network?

No files were inspected and no analysis ran.
```

## ct-b0-N4-3

> We have ChIP-seq peaks for an uncharacterized transcription factor and expression data from the same cells. We want to discover its binding motif de novo and then find its target genes genome-wide.

- core: de novo discovery of the TF's binding motif from ChIP-seq peaks
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
3 registered methods can build a cohort-level TF-gene regulatory network;
they differ in their modeling assumptions.
  • Understood goal: a cohort-level TF-gene regulatory network from
    expression data, a motif prior and a PPI network.
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
  2) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  3) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  Next: 4) Start a new task
```

Full reply:

```
I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA.

No files were inspected and no analysis ran.
```

## ct-b0-N5-1

> We have genotypes and liver expression for 300 donors. We want to fine-map which noncoding variants disrupt transcription factor binding sites and thereby cause changes in their target genes' expression.

- core: fine-mapped causal noncoding variants that disrupt TF binding
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_puma', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_giraffe'], recommended [], advised run_puma, model-written False

Card:
```
6 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
  • LIONESS-PANDA and LIONESS-PUMA give one network per sample; PUMA,
    PANDA, OTTER and GIRAFFE give one across all samples.
  • Recommended: PUMA, from what you said.
  • Picking an option explains it for your data and what it needs;
    nothing runs.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
  Full explanation: /details
[Method] Which method fits your study?
  Recommended first, from what you said.
  1) PUMA  (Recommended)
      Fits what you said: the regulators include miRNAs · One TF +
      miRNA network across all your samples · Also adds miRNA
      regulators · Also needs miRNA list
  2) PANDA
      One TF-gene network across all your samples · Pick it if you
      want the standard published method or a base for LIONESS
  3) LIONESS-PANDA
      One TF-gene network per sample, plus the cohort network · Lets
      you compare samples, or relate them to outcomes such as survival
      · Slower: it reruns PANDA once per sample
  4) OTTER
      The same kind of network as PANDA, from a different algorithm ·
      Pick it if memory or runtime is a concern
  5) GIRAFFE
      One signed TF-gene network (activating or repressing), plus each
      TF's activity in each sample · Pick it if TF activity may differ
      from its mRNA level
  6) LIONESS-PUMA
      One TF + miRNA network per sample, plus the cohort network ·
      Also adds miRNA regulators · Pick it if the regulators include
      miRNAs · Also needs miRNA list
  Next: 7) Start a new task
```

Full reply:

```
About "thereby cause changes in their target genes' expression": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

Based on what you said — "We want to fine-map which noncoding variants disrupt transcription factor binding sites and thereby cause changes in their target genes' expression." — **PUMA** fits better: the regulators include miRNAs or similar short non-coding RNAs that repress or degrade target transcripts after transcription.

Your question asks for a regulatory network. **PUMA** fits that result.

**PUMA** (recommend) — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list. Produces inferred regulator-to-target associations (one cohort-level result).

Conditional assumptions to confirm:
- This reads the molecules you describe as miRNAs. Confirm that, and that you have a miRNA-target prior and a list of the miRNAs, before analysis.
- It also needs an expression matrix and TF-motif prior and protein-interaction prior and miRNA list, which the request does not mention.

Other compatible option(s):
- If you need a TF-only regulatory network instead: **PANDA**, **LIONESS-PANDA**, **OTTER**.
- **LIONESS-PUMA** — preferred when: dozens of samples or more; each sample's regulator-to-target wiring (edge weights or targeting scores) is needed; the regulators include miRNAs or similar short non-coding RNAs that repress or degrade target transcripts after transcription; approach: derive each sample network from all-sample and leave-one-out networks.
- **GIRAFFE** — preferred when: a regulator's activity may differ from its own expression, or activating versus repressing effects are needed; each sample's regulator activity level is needed, apart from the regulator's own expression; approach: factor gene expression using motif and TF-protein interaction priors.

Should I use PUMA, or does another listed option fit your study better?

No files were inspected and no analysis ran.
```

## ct-b0-N5-2

> We have genotypes and liver expression for 300 donors. We want to fine-map which noncoding variants disrupt transcription factor binding sites and thereby cause changes in their target genes' expression.

- core: fine-mapped causal noncoding variants that disrupt TF binding
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
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

## ct-b0-N5-3

> We have genotypes and liver expression for 300 donors. We want to fine-map which noncoding variants disrupt transcription factor binding sites and thereby cause changes in their target genes' expression.

- core: fine-mapped causal noncoding variants that disrupt TF binding
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_panda', 'run_lioness_panda', 'run_otter', 'run_giraffe'], recommended [], advised None, model-written False

Card:
```
4 registered methods can build a TF-gene regulatory network; they differ in
scale (one network for all samples or one per sample) and in their modeling
assumptions.
  • Understood goal: a TF-gene regulatory network.
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
About "thereby cause changes in their target genes' expression": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

I can map this to more than one compatible network result:

**TF-only regulatory network**
- **PANDA** — Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Per-sample version: **LIONESS-PANDA**. Needs expression matrix, motif/prior and PPI network.
- **OTTER** — OTTER optimizes a TF-gene matrix W so that W W-transpose matches the TF-TF interaction network and W-transpose W matches gene co-expression. Needs motif/prior, PPI network and either expression matrix or adjusted co-expression matrix.

**TF-only signed regulatory-effect network**
- **GIRAFFE** — GIRAFFE jointly factors expression into a regulatory-effect matrix and sample-varying TF activities using biological priors. Signed effects describe the fitted activation/repression relationship, while activity differs from the TF's own expression. These fitted coefficients do not alone establish causality. Needs expression matrix, motif/prior and PPI network.

These fit the result you described, but none can show that one thing causes another; to choose among them, tell me: (1) Is the network large enough that memory or runtime is a concern? (yes → OTTER) (2) Do you suspect a regulator's activity differs across samples even when its own expression does not, or do you need activating versus repressing effects? (yes → GIRAFFE) If none of these applies: PANDA, LIONESS-PANDA.

No files were inspected and no analysis ran.
```

## ct-b0-N6-1

> We have matched mRNA, lncRNA and microRNA expression from 90 gastric tumors. We want a competing endogenous RNA network showing which lncRNAs sponge microRNAs away from their mRNA targets.

- core: a ceRNA network of lncRNAs sponging microRNAs away from mRNAs
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## ct-b0-N6-2

> We have matched mRNA, lncRNA and microRNA expression from 90 gastric tumors. We want a competing endogenous RNA network showing which lncRNAs sponge microRNAs away from their mRNA targets.

- core: a ceRNA network of lncRNAs sponging microRNAs away from mRNAs
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## ct-b0-N6-3

> We have matched mRNA, lncRNA and microRNA expression from 90 gastric tumors. We want a competing endogenous RNA network showing which lncRNAs sponge microRNAs away from their mRNA targets.

- core: a ceRNA network of lncRNAs sponging microRNAs away from mRNAs
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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
Semantic routing output failed validation, so no workflow was selected. (ValidationError)

The system could not validate its interpretation. This is not evidence that your question is unclear.

Retry this request when semantic routing is available, or ask a follow-up question. No workflow is ready to start.

No files were inspected and no analysis ran.
```

## ct-b0-N7-1

> We have DNA methylation and expression from the same 70 tumors. We want to establish that promoter methylation of each gene causes its silencing, ruling out confounding by other factors.

- core: proof that promoter methylation causes silencing, ruling out confounding
- status `fallback`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates ['run_dragon'], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON is the closest registered match, but it is not a verified match for
your request.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
  Full explanation: /details
```

Full reply:

```
About "establish that promoter methylation of each gene causes its silencing": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

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

## ct-b0-N7-2

> We have DNA methylation and expression from the same 70 tumors. We want to establish that promoter methylation of each gene causes its silencing, ruling out confounding by other factors.

- core: proof that promoter methylation causes silencing, ruling out confounding
- status `fallback`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates ['run_dragon'], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON is the closest registered match, but it is not a verified match for
your request.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
  Full explanation: /details
```

Full reply:

```
About "establish that promoter methylation of each gene causes its silencing": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

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

## ct-b0-N7-3

> We have DNA methylation and expression from the same 70 tumors. We want to establish that promoter methylation of each gene causes its silencing, ruling out confounding by other factors.

- core: proof that promoter methylation causes silencing, ruling out confounding
- status `fallback`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates ['run_dragon'], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON is the closest registered match, but it is not a verified match for
your request.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
  Full explanation: /details
```

Full reply:

```
About "establish that promoter methylation of each gene causes its silencing": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why. A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes.

Assumptions behind this recommendation (not confirmed facts):

- No scale was stated; DRAGON gives one result for the whole cohort; LIONESS-DRAGON gives one result per sample.

Fallback recommendation: **DRAGON**. This is registry-based guidance, not an exact semantic match. The system could not verify a complete goal-to-workflow match; this does not mean your question is unclear. No clarification is required to read this recommendation, and no executable plan has been selected.

Your question asks for a multi-omic network. **DRAGON** is related to that result.

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

## ct-b0-P1-1

> We have RNA-seq, motif priors and protein interactions for 150 breast tumors. We want a regulatory network for each patient, then a classifier using those networks to predict five-year survival with cross-validated accuracy.

- core: a survival classifier with cross-validated accuracy
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_lioness_panda', 'run_lioness_puma'], recommended [], advised None, model-written False

Card:
```
2 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a per-sample regulatory network from expression
    data, a motif prior and a PPI network.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "to predict five-year survival with cross-validated accuracy": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## ct-b0-P1-2

> We have RNA-seq, motif priors and protein interactions for 150 breast tumors. We want a regulatory network for each patient, then a classifier using those networks to predict five-year survival with cross-validated accuracy.

- core: a survival classifier with cross-validated accuracy
- status `ambiguous`, in_scope True, artifact `regulatory_network`, matched [], candidates ['run_lioness_panda', 'run_lioness_puma'], recommended [], advised None, model-written False

Card:
```
2 registered workflows fit; one detail about your study decides between
them.
  • Understood goal: a per-sample regulatory network from expression
    data, a motif prior and a PPI network.
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
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
About "to predict five-year survival with cross-validated accuracy": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

I can map this to more than one compatible network result:

All of them derive each sample network from all-sample and leave-one-out networks, and iteratively exchange information across biological evidence networks.

**TF-only regulatory network**
- **LIONESS-PANDA** — Needs expression matrix, motif/prior and PPI network.

**TF/miRNA regulatory network**
- **LIONESS-PUMA** — PUMA extends PANDA's message passing to miRNA regulators. Their prior edges usually come from sequence-based target prediction such as TargetScan or miRanda, and can sit in the same prior as TF motif edges. Because miRNAs do not form the protein complexes that the cooperativity network represents, PUMA keeps each miRNA's cooperativity with other regulators at its initial value instead of updating it. Evidence for a miRNA-gene edge therefore comes from agreement between the predicted targets and target-gene co-expression; the miRNA's own expression is not used, and anti-correlation receives no special weight for repression. Needs expression matrix, motif/prior, PPI network and miRNA list.

About your concern that what to do with the result afterwards, for example comparing conditions or relating it to clinical variables:
- **LIONESS-PANDA**, **LIONESS-PUMA** — Per-sample targeting scores: a regulator's outdegree (the sum of its edge weights to its targets) or a gene's indegree, computed in each sample's network, gives a regulator-by-sample (or gene-by-sample) matrix you can relate to sample-level variables -- survival, for example, with a Cox model. An ordered variable such as disease stage can be tested for a trend, for example with ordinal or linear regression on stage; testing every regulator or edge needs multiple-testing correction (for example Benjamini-Hochberg). Stages seen in different patients are cross-sectional, so a trend across them is not one patient's progression. That association needs a clinical table (for survival: follow-up time and event status) keyed by the same sample IDs as the expression matrix; it is not a workflow input, so supply it separately. All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in the association test, which is a later analysis step rather than part of this workflow.

Which regulator type should the network model: transcription factors, miRNA regulators, or both?

No files were inspected and no analysis ran.
```

## ct-b0-P1-3

> We have RNA-seq, motif priors and protein interactions for 150 breast tumors. We want a regulatory network for each patient, then a classifier using those networks to predict five-year survival with cross-validated accuracy.

- core: a survival classifier with cross-validated accuracy
- status `None`, in_scope True, artifact `None`, matched [], candidates [], recommended [], advised None, model-written False

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
About "to predict five-year survival with cross-validated accuracy": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

If you want per-sample results to use as features, say which result you need -- per-sample networks, TF activities or subtypes -- and the data you have.

No files were inspected and no analysis ran.
```

## ct-b0-P2-1

> We already have a validated TF-gene network from 80 lung tumors. We want to find its communities of regulators and genes, and then test whether each community causally drives metastasis.

- core: a test that each community causally drives metastasis
- status `unsupported`, in_scope True, artifact `community_assignment`, matched ['run_condor'], candidates [], recommended [], advised None, model-written False

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
    ✕ “causally drives metastasis” — No registered workflow meets
      this; it needs a clearer measurement or an external method.
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
  Full explanation: /details
```

Full reply:

```
About "test whether each community causally drives metastasis": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

For “causally drives metastasis”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

## ct-b0-P2-2

> We already have a validated TF-gene network from 80 lung tumors. We want to find its communities of regulators and genes, and then test whether each community causally drives metastasis.

- core: a test that each community causally drives metastasis
- status `unsupported`, in_scope True, artifact `community_assignment`, matched ['run_condor'], candidates [], recommended [], advised None, model-written False

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
    ✕ “test whether each community causally drives metastasis” — No
      registered workflow meets this; it needs a clearer measurement
      or an external method.
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
  Full explanation: /details
```

Full reply:

```
About "test whether each community causally drives metastasis": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

For “test whether each community causally drives metastasis”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

## ct-b0-P2-3

> We already have a validated TF-gene network from 80 lung tumors. We want to find its communities of regulators and genes, and then test whether each community causally drives metastasis.

- core: a test that each community causally drives metastasis
- status `unsupported`, in_scope True, artifact `community_assignment`, matched ['run_condor'], candidates [], recommended [], advised None, model-written False

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
    ✕ “test whether each community causally drives metastasis” — No
      registered workflow meets this; it needs a clearer measurement
      or an external method.
    ✕ Show that one thing causes another — Registered workflows
      estimate associations; they can describe what changes, not prove
      its cause.
  Full explanation: /details
```

Full reply:

```
About "test whether each community causally drives metastasis": None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from the expression data, so the networks can describe what differs or changes but not show why.

**CONDOR**. CONDOR uses bipartite modularity and BRIM: regulator and target nodes remain separate partitions, and between-partition connectivity is compared with a degree/strength-preserving bipartite null model. A giant community can reflect an unsuitable null model, resolution or weight handling. Hubs alone do not prove every conventional algorithm fails, and bipartite modularity does not guarantee biologically meaningful modules. Verify the edge-weight conventions.

You would need bipartite network. The analysis would provide network-node community memberships, not patient subtype labels.

For “test whether each community causally drives metastasis”, no registered workflow meets the stated requirement. That part needs a clearer measurement or an external method.

No files were inspected and no analysis ran.

What measurement would let you distinguish the remaining explanation?
```

## ct-b0-P3-1

> We measured expression and DNA methylation in 60 tumors. We want an integrated two-layer network for each patient, and then a forecast of how each patient's network will look after two years of treatment.

- core: a forecast of each patient's network two years after treatment
- status `exact`, in_scope True, artifact `multi_omic_network`, matched ['run_lioness_dragon'], candidates [], recommended ['run_dragon', 'run_lioness_dragon'], advised None, model-written False

Card:
```
LIONESS-DRAGON gives the per-sample result you asked for; it also writes the
cohort network, so DRAGON need not run first.
  • Method: One two-layer partial-correlation network per sample,
    derived leave-one-out.
  • Needs: omics layer 1, omics layer 2.
  • Cost: N samples take N+1 DRAGON runs (for your 60 tumors, 61 DRAGON
    runs).
  • Produces: multi-omic network (one per sample).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
  Full explanation: /details
```

Full reply:

```
About "a forecast of how each patient's network will look after two years of treatment.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 60 tumors, 61 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## ct-b0-P3-2

> We measured expression and DNA methylation in 60 tumors. We want an integrated two-layer network for each patient, and then a forecast of how each patient's network will look after two years of treatment.

- core: a forecast of each patient's network two years after treatment
- status `exact`, in_scope True, artifact `multi_omic_network`, matched ['run_lioness_dragon'], candidates [], recommended ['run_dragon', 'run_lioness_dragon'], advised None, model-written False

Card:
```
LIONESS-DRAGON gives the per-sample result you asked for; it also writes the
cohort network, so DRAGON need not run first.
  • Method: One two-layer partial-correlation network per sample,
    derived leave-one-out.
  • Needs: omics layer 1, omics layer 2.
  • Cost: N samples take N+1 DRAGON runs (for your 60 tumors, 61 DRAGON
    runs).
  • Produces: multi-omic network (one per sample).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
  Full explanation: /details
```

Full reply:

```
About "a forecast of how each patient's network will look after two years of treatment.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 60 tumors, 61 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## ct-b0-P3-3

> We measured expression and DNA methylation in 60 tumors. We want an integrated two-layer network for each patient, and then a forecast of how each patient's network will look after two years of treatment.

- core: a forecast of each patient's network two years after treatment
- status `exact`, in_scope True, artifact `multi_omic_network`, matched ['run_lioness_dragon'], candidates [], recommended ['run_dragon', 'run_lioness_dragon'], advised None, model-written False

Card:
```
LIONESS-DRAGON gives the per-sample result you asked for; it also writes the
cohort network, so DRAGON need not run first.
  • Method: One two-layer partial-correlation network per sample,
    derived leave-one-out.
  • Needs: omics layer 1, omics layer 2.
  • Cost: N samples take N+1 DRAGON runs (for your 60 tumors, 61 DRAGON
    runs).
  • Produces: multi-omic network (one per sample).
  • Nothing has run yet.
  Related, but not available in this agent:
    ✕ Predict outcomes for new samples — No registered workflow builds
      a predictive model; per-sample results can only be its features.
  Full explanation: /details
```

Full reply:

```
About "a forecast of how each patient's network will look after two years of treatment.": No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it.

For the sample-specific output you described, use **LIONESS-DRAGON**.

Required inputs:
   - `omics_layer_1`: Omics layer 1 (samples x features)
   - `omics_layer_2`: Omics layer 2 (the same samples)

Outputs:
   - Aggregate network (`output_file`).
   - Sample-specific network for each patient/sample (`lioness_output`).

You do not need to run **DRAGON** separately; **LIONESS-DRAGON** also produces the aggregate output. Use **DRAGON** alone only when a cohort-level aggregate result is sufficient.

Cost: LIONESS runs DRAGON once on all samples and once more without each sample, so N samples take N+1 DRAGON runs and give N network files (for your 60 tumors, 61 DRAGON runs). Plan the runtime and disk space, and filter edges before downstream statistics.

No files were inspected and no analysis ran.
```

## ct-b0-C1-1

> We have RNA-seq from 90 ovarian tumors plus TF motif and protein interaction data. We want a separate TF-gene regulatory network for every tumor so we can compare patients.

- core: a TF-gene network per tumor
- status `exact`, in_scope True, artifact `regulatory_network`, matched ['run_lioness_panda'], candidates ['run_lioness_panda'], recommended ['run_panda', 'run_lioness_panda'], advised None, model-written False

Card:
```
LIONESS-PANDA gives the per-sample result you asked for; it also writes the
cohort network, so PANDA need not run first.
  • Method: One TF-gene network per sample, derived leave-one-out from
    the cohort.
  • Needs: expression matrix, motif prior, PPI network.
  • Cost: N samples take N+1 PANDA runs (for your 90 tumors, 91 PANDA
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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 90 tumors, 91 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## ct-b0-C1-2

> We have RNA-seq from 90 ovarian tumors plus TF motif and protein interaction data. We want a separate TF-gene regulatory network for every tumor so we can compare patients.

- core: a TF-gene network per tumor
- status `exact`, in_scope True, artifact `regulatory_network`, matched ['run_lioness_panda'], candidates ['run_lioness_panda'], recommended ['run_panda', 'run_lioness_panda'], advised None, model-written False

Card:
```
LIONESS-PANDA gives the per-sample result you asked for; it also writes the
cohort network, so PANDA need not run first.
  • Method: One TF-gene network per sample, derived leave-one-out from
    the cohort.
  • Needs: expression matrix, motif prior, PPI network.
  • Cost: N samples take N+1 PANDA runs (for your 90 tumors, 91 PANDA
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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 90 tumors, 91 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## ct-b0-C1-3

> We have RNA-seq from 90 ovarian tumors plus TF motif and protein interaction data. We want a separate TF-gene regulatory network for every tumor so we can compare patients.

- core: a TF-gene network per tumor
- status `exact`, in_scope True, artifact `regulatory_network`, matched ['run_lioness_panda'], candidates ['run_lioness_panda'], recommended ['run_panda', 'run_lioness_panda'], advised None, model-written False

Card:
```
LIONESS-PANDA gives the per-sample result you asked for; it also writes the
cohort network, so PANDA need not run first.
  • Method: One TF-gene network per sample, derived leave-one-out from
    the cohort.
  • Needs: expression matrix, motif prior, PPI network.
  • Cost: N samples take N+1 PANDA runs (for your 90 tumors, 91 PANDA
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

Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files (for your 90 tumors, 91 PANDA runs). Plan the runtime and disk space, and filter edges before downstream statistics.

Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.

No files were inspected and no analysis ran.
```

## ct-b0-C2-1

> We have expression from 50 kidney samples with TF motif, protein interaction and microRNA target predictions. We want one network of how both TFs and microRNAs regulate genes.

- core: one TF and microRNA to gene regulatory network
- status `exact`, in_scope True, artifact `regulatory_network`, matched ['run_puma'], candidates [], recommended ['run_puma'], advised None, model-written False

Card:
```
PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
  • Method: PANDA's message passing with miRNA regulators added.
  • Needs: expression matrix, motif prior, PPI network, miRNA list.
  • Produces: regulatory network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C2-2

> We have expression from 50 kidney samples with TF motif, protein interaction and microRNA target predictions. We want one network of how both TFs and microRNAs regulate genes.

- core: one TF and microRNA to gene regulatory network
- status `exact`, in_scope True, artifact `regulatory_network`, matched ['run_puma'], candidates [], recommended ['run_puma'], advised None, model-written False

Card:
```
PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
  • Method: PANDA's message passing with miRNA regulators added.
  • Needs: expression matrix, motif prior, PPI network, miRNA list.
  • Produces: regulatory network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C2-3

> We have expression from 50 kidney samples with TF motif, protein interaction and microRNA target predictions. We want one network of how both TFs and microRNAs regulate genes.

- core: one TF and microRNA to gene regulatory network
- status `exact`, in_scope True, artifact `regulatory_network`, matched ['run_puma'], candidates [], recommended ['run_puma'], advised None, model-written False

Card:
```
PUMA fits your goal: cohort-level TF/miRNA-gene regulatory network.
  • Method: PANDA's message passing with miRNA regulators added.
  • Needs: expression matrix, motif prior, PPI network, miRNA list.
  • Produces: regulatory network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C3-1

> We already have a validated TF-gene regulatory network from liver tissue. We want to partition it into communities of regulators and target genes that work together.

- core: communities of regulators and target genes
- status `exact`, in_scope True, artifact `community_assignment`, matched ['run_condor'], candidates [], recommended ['run_condor'], advised None, model-written False

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

## ct-b0-C3-2

> We already have a validated TF-gene regulatory network from liver tissue. We want to partition it into communities of regulators and target genes that work together.

- core: communities of regulators and target genes
- status `exact`, in_scope True, artifact `community_assignment`, matched ['run_condor'], candidates [], recommended ['run_condor'], advised None, model-written False

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

## ct-b0-C3-3

> We already have a validated TF-gene regulatory network from liver tissue. We want to partition it into communities of regulators and target genes that work together.

- core: communities of regulators and target genes
- status `exact`, in_scope True, artifact `community_assignment`, matched ['run_condor'], candidates [], recommended ['run_condor'], advised None, model-written False

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

## ct-b0-C4-1

> We measured gene expression and DNA methylation in the same 120 tumors. We want one network linking the two layers using partial correlations, controlling for all other features.

- core: one partial-correlation network linking expression and methylation
- status `exact`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates [], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON fits your goal: cohort-level multi-omic network.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C4-2

> We measured gene expression and DNA methylation in the same 120 tumors. We want one network linking the two layers using partial correlations, controlling for all other features.

- core: one partial-correlation network linking expression and methylation
- status `exact`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates [], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON fits your goal: cohort-level multi-omic network.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C4-3

> We measured gene expression and DNA methylation in the same 120 tumors. We want one network linking the two layers using partial correlations, controlling for all other features.

- core: one partial-correlation network linking expression and methylation
- status `exact`, in_scope True, artifact `multi_omic_network`, matched ['run_dragon'], candidates [], recommended ['run_dragon'], advised None, model-written False

Card:
```
DRAGON fits your goal: cohort-level multi-omic network.
  • Method: Partial-correlation network across two omics layers of the
    same samples.
  • Needs: omics layer 1, omics layer 2.
  • Produces: multi-omic network (one cohort-level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C5-1

> Using expression from 70 heart samples with motif and protein interaction priors, we want each TF's activity in each sample, since a TF's activity may differ from its mRNA level.

- core: each TF's activity per sample, distinct from its mRNA
- status `exact`, in_scope True, artifact `tf_activity_matrix`, matched ['run_giraffe'], candidates [], recommended ['run_giraffe'], advised None, model-written False

Card:
```
GIRAFFE fits your goal: cohort-level TF activity matrix.
  • Method: Also estimates per-sample TF activity and signed
    activating/repressing effects.
  • Needs: expression matrix, motif prior, PPI network.
  • Produces: regulatory network and TF activity matrix (one cohort-
    level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "a TF's activity may differ from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C5-2

> Using expression from 70 heart samples with motif and protein interaction priors, we want each TF's activity in each sample, since a TF's activity may differ from its mRNA level.

- core: each TF's activity per sample, distinct from its mRNA
- status `exact`, in_scope True, artifact `tf_activity_matrix`, matched ['run_giraffe'], candidates [], recommended ['run_giraffe'], advised None, model-written False

Card:
```
GIRAFFE fits your goal: cohort-level TF activity matrix.
  • Method: Also estimates per-sample TF activity and signed
    activating/repressing effects.
  • Needs: expression matrix, motif prior, PPI network.
  • Produces: regulatory network and TF activity matrix (one cohort-
    level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "a TF's activity may differ from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C5-3

> Using expression from 70 heart samples with motif and protein interaction priors, we want each TF's activity in each sample, since a TF's activity may differ from its mRNA level.

- core: each TF's activity per sample, distinct from its mRNA
- status `exact`, in_scope True, artifact `tf_activity_matrix`, matched ['run_giraffe'], candidates [], recommended ['run_giraffe'], advised None, model-written False

Card:
```
GIRAFFE fits your goal: cohort-level TF activity matrix.
  • Method: Also estimates per-sample TF activity and signed
    activating/repressing effects.
  • Needs: expression matrix, motif prior, PPI network.
  • Produces: regulatory network and TF activity matrix (one cohort-
    level result).
  • Nothing has run yet.
  Full explanation: /details
```

Full reply:

```
Selected path: **GIRAFFE**.

Your question asks for a cohort-level TF activity matrix. **GIRAFFE** fits that result and scale.

What you asked about:

- "a TF's activity may differ from its mRNA level" — GIRAFFE fits each TF's activity (`tf_activity_matrix`) from the expression of its target genes and the TF-TF protein interactions; the TF's own mRNA level is not an input to it. If the TF's gene is among the expression rows it still counts as an ordinary target, so its activity is not tied to its mRNA rather than independent of it.

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

Input compatibility has not been assessed: your data was not checked against the workflow's required inputs; name your input files to have them checked. This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.
```

## ct-b0-C6-1

> We have somatic mutation calls for 400 tumors and want to subtype the patients by summarizing their mutations into pathway-level scores and clustering them.

- core: patient subtypes from pathway-level mutation scores
- status `exact`, in_scope True, artifact `sample_cluster_assignment`, matched ['run_sambar'], candidates [], recommended ['run_sambar'], advised None, model-written False

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

## ct-b0-C6-2

> We have somatic mutation calls for 400 tumors and want to subtype the patients by summarizing their mutations into pathway-level scores and clustering them.

- core: patient subtypes from pathway-level mutation scores
- status `exact`, in_scope True, artifact `sample_cluster_assignment`, matched ['run_sambar'], candidates [], recommended ['run_sambar'], advised None, model-written False

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

## ct-b0-C6-3

> We have somatic mutation calls for 400 tumors and want to subtype the patients by summarizing their mutations into pathway-level scores and clustering them.

- core: patient subtypes from pathway-level mutation scores
- status `exact`, in_scope True, artifact `sample_cluster_assignment`, matched ['run_sambar'], candidates [], recommended ['run_sambar'], advised None, model-written False

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

Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.

What you asked about:

- "want to subtype the patients by summarizing their mutations into pathway-level scores and clustering them." — Subtype labels can be compared with clinical variables -- survival between subtypes, for example; that needs a clinical table keyed by the same sample IDs. The pathway mutation scores show which pathways separate the subtypes.

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

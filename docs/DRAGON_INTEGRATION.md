# DRAGON integration contract

This agent integrates DRAGON through the typed workflow registry as `run_dragon`.
It does not invent a `netzoopy dragon` command: the pinned netZooPy source exposes
DRAGON as Python functions, while the bundled CLI registers PANDA, LIONESS,
CONDOR, BONOBO, and OTTER commands only.

## Verified API evidence

The Dockerfile pins netZooPy commit `60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822`.
That checkout declares version `0.11.0` and exports these relevant callables from
`netZooPy.dragon`:

```text
estimate_penalty_parameters_dragon(X1, X2)
get_precision_matrix_dragon(X1, X2, lambdas)
get_partial_correlation_dragon(X1, X2, lambdas)
estimate_p_values_dragon(r, n, p1, p2, lambdas, kappa='estimate', seed=1, simultaneous=False)
```

The first two arguments are NumPy-like `n x p` arrays. The verified core API has
no file path, sample metadata, motif, PPI, expression-matrix, or three-layer
argument. `LionessDragon` is the separate official file-oriented helper: it reads
CSV with `header=0, index_col=0`, treats rows as samples and columns as features,
and merges its two files on a common sample index.

## Agent input contract

`omics_layer_1` and `omics_layer_2` are separate CSV/TSV/TAB/TXT files with a
header. The first column is a unique sample identifier; every remaining column
name is a unique feature identifier. Both files use rows=samples and
columns=features. The adapter requires exact equality of the two sample-ID sets
and reorders layer 2 to layer 1's order. It rejects missing values, non-numeric or
non-finite cells, duplicate sample IDs, duplicate feature IDs, absent headers,
and fewer than three samples. No imputation, log transform, or normal transform
is silently performed. Because DRAGON is a Gaussian graphical model, continuous
data should be transformed to approximate normality before this workflow when
the measurement scale requires it.

`sample_metadata` is intentionally not an input role: the verified DRAGON API
does not accept it. Metadata-aware preprocessing must produce validated layer
files before `run_dragon`.

The only optional numerical controls are `lambda1` and `lambda2`. They must be
provided together and lie in `[0, 1]`; when omitted, the adapter calls
`estimate_penalty_parameters_dragon`. `output_format` is `matrix` by default or
`edge_list`.

## Output contract

Both output forms are aggregate, undirected association networks. Matrix node IDs
are qualified as `layer1::<feature_id>` or `layer2::<feature_id>` so equal feature
names in different layers remain distinct. A matrix is labeled with `node_id`, is
square and symmetric, and contains the DRAGON partial-correlation GGM with zero
diagonal. An edge list contains one row per undirected pair and exactly these
columns:

```text
source, target, partial_correlation, precision
```

`partial_correlation` is the normalized value derived by the verified API's
precision matrix; `precision` is the corresponding off-diagonal precision entry.
Neither value is a causal effect. They are conditional association estimates.

There is no direct registry handoff from DRAGON to PANDA, PUMA, LIONESS, CONDOR,
BONOBO, or OTTER: those workflows consume different artifacts and/or have
different biological node contracts. In particular, CONDOR requires a validated
weighted source-target bipartite edge list, whereas DRAGON emits an undirected
multi-omic network. A future pairwise/chained workflow must define an explicit
conversion artifact, its provenance and semantics, and obtain user confirmation;
the current agent does not silently chain three or more omics layers.

## Lifecycle

Planning runs the DRAGON-specific inspector and records the two layer paths and
their provenance. Dry-run renders the exact Python API invocation and expected
artifact contract without importing or executing the analysis and without writing
the output. `/execute` remains blocked until the common Plan Evaluator approves a
ready plan. Execute imports the pinned `netZooPy.dragon` module, calls the verified
functions, writes the selected artifact, and validates it before returning success.

# COBRA pinned-API trial

Validated against Docker's pinned netZooPy revision
`60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822`.

The public callable is `netZooPy.cobra.cobra.cobra(X, expression)`:

- `X`: numeric design matrix, samples × covariates;
- `expression`: numeric matrix, genes × samples; netZooPy requires genes > samples;
- returns `psi`, `Q`, `d`, `g`.

Reproducible fixture:

```bash
docker compose run --rm netzoo run-cobra \
  -e data/cobra-toy/expression.tsv \
  -d data/cobra-toy/design.tsv \
  -o outputs/cobra-toy
```

The integration verifies labeled sample alignment before converting the matrices
to NumPy. It writes a manifest, compressed raw components and a compact summary.
COBRA describes covariate-associated co-expression; this project does not treat
it as an expression-correction step for PANDA, PUMA or LIONESS.

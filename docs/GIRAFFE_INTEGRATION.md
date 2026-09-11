# GIRAFFE integration

This project runs GIRAFFE through the pinned Docker runtime. The host Python
environment is used for agent planning and input inspection only; it is not
silently modified to install netZooPy.

## Version and source contract

The Dockerfile pins the netZooPy source checkout to
`60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822`. That checkout reports version
`0.11.0`. The source is the official
[netZooPy repository](https://github.com/netZoo/netZooPy/tree/master/netZooPy),
with the GIRAFFE implementation in
[`netZooPy/giraffe/giraffe.py`](https://github.com/netZoo/netZooPy/blob/master/netZooPy/giraffe/giraffe.py)
and helpers in
[`netZooPy/giraffe/utils.py`](https://github.com/netZoo/netZooPy/blob/master/netZooPy/giraffe/utils.py).

The current host interpreter has no installed netZooPy distribution and cannot
import `netZooPy.giraffe`. This is expected: the supported execution contract
is the Docker image. During image build the Dockerfile checks both
`netZooPy.__version__ == "0.11.0"` and the reflected signature of
`netZooPy.giraffe.Giraffe`.

GitHub `master` is a moving branch; the image does not execute an unpinned
checkout. If a future master version changes the API, update the pinned ref,
source inspection, validation tests, and this document together. No upgrade is
performed automatically.

## Verified API

For the pinned source, the public constructor is:

```python
Giraffe(
    expression,
    prior,
    ppi,
    adjusting=None,
    design_matrix=None,
    cobra_covariate_to_keep=0,
    l1=0,
    max_iter=2000,
    min_iter=200,
    lr=1e-5,
    lam=None,
    balance_fn=None,
    save_computation=False,
    seed=42,
)
```

The adapter intentionally calls only the required three positional arrays and
uses source defaults for optional parameters. It then calls the verified
methods `get_regulation()` and `get_tfa()`. GIRAFFE constructs the model in
the constructor, so the call is not a file-path or CLI invocation.

## Input and output contract

The agent discovers files by content and validates them as a coherent bundle:

- `expression_file`: gene-by-sample numeric table; first column is the unique
  gene ID and remaining columns are samples.
- `motif_file`: either a three-column regulator/gene/weight edge list or a
  labelled TF-by-gene matrix.
- `ppi_file`: either a two/three-column TF edge list or a labelled square
  TF-by-TF matrix. The adapter expands an edge list with an identity diagonal,
  then requires symmetry and diagonal entries equal to one.
- Gene IDs in expression and motif must match exactly. TF IDs in motif and PPI
  must cover exactly the same set. Numeric values must be finite and matrices
  must not contain empty rows or columns.

The adapter converts those labelled files to the arrays expected by the
source: expression `genes × samples`, prior `TFs × genes`, and PPI `TFs × TFs`.
The requested output path stores the labelled TF-by-gene regulation matrix;
the sibling `<stem>.tfa<suffix>` stores the labelled TF-by-sample TFA matrix.
Both artifacts are shape- and identifier-validated after execution.

At the routing boundary, `tf_activity_matrix` is a first-class artifact type,
and `regulatory_network_and_tf_activity` is the typed bundle for the joint
result. GIRAFFE declares both concrete components in `produced_artifacts`; the
matcher derives support for the bundle from that conjunction without naming a
workflow or scanning the raw request for GIRAFFE-specific keywords. Entity
constraints for secondary and composite artifacts come from the shared
artifact ontology (`tf`, `gene`, and `sample`) rather than changing the entity
contract of the primary TF-gene network.

`signed_regulatory_effect_network` is the primary semantic result for GIRAFFE's
regulation matrix. It represents a TF-gene network whose entries are signed
partial regulatory effects rather than generic association strengths. The
installed netZooPy 0.11.0 objective contains the expression reconstruction term
`||Y - R @ abs(TFA)||²`: the sample-varying TFA values act as predictors, and
the corresponding entries of `R` are linear-model coefficients. Positive
coefficients represent activating effects and negative coefficients represent
inhibitory effects. The matcher derives this from the typed artifact and
registry capability; it does not scan raw request text for sign-related words.

## Workflow behavior

`run_giraffe` is registered in the same policy/plan/executor/evaluator path as
the other NetZoo workflows. The plan records the Docker runtime, netZooPy
version, verified API, input evidence, validation result, required parameters,
expected artifacts, and unresolved items. Missing or ambiguous input keeps the
plan in `needs_input`; it cannot reach execution.

The CLI is intentionally two-phase:

```text
python scripts/netzoo_agent.py --task "跑 GIRAFFE，expression_file=... motif_file=... ppi_file=... output_file=..."
```

This creates or resumes the plan and asks for confirmation when file content
does not establish the intended roles. Only an explicit `/execute` in the
interactive session can run a complete, confirmed plan. A dry run previews the
exact Python API call and writes no output.

Example Docker invocation:

```bash
docker compose build
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "Run GIRAFFE with expression_file=data/giraffe-toy/expression.tsv motif_file=data/giraffe-toy/motif.tsv ppi_file=data/giraffe-toy/ppi.tsv output_file=outputs/giraffe.tsv"
```

The built-in toy bundle is available at `data/giraffe-toy/` for planning and
regression tests. It is not a substitute for confirming a user's real files.

## Error categories

The adapter reports typed, user-facing categories for missing files, malformed
tables, incompatible identifiers, missing netZooPy/GIRAFFE, unsupported
versions, unavailable APIs, API errors, invalid output shapes, output
validation failures, runtime failures, and attempts to overwrite an input.
Each message states what was confirmed and what path, setting, or Docker
version is still needed.

GIRAFFE has no direct handoff to PANDA, PUMA, LIONESS, SAMBAR, DRAGON, OTTER,
BONOBO, COBRA, or CONDOR. A downstream conversion requires a separate schema
validation step and explicit user confirmation.

## Verification

The GIRAFFE-specific tests cover source-shaped input conversion, identifier and
PPI failures, plan readiness, dry-run gating, verified API invocation, both
output artifacts, missing-runtime errors, registry metadata, and the Docker
version contract. The existing workflow and contract regression suites remain
part of the required test run.

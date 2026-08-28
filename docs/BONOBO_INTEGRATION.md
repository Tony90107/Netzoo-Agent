# BONOBO integration contract

This project runs the BONOBO adapter against the Dockerfile's pinned netZooPy
0.11.0 checkout (`60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822`). The executable
public API is:

```python
from netZooPy.bonobo import Bonobo
model = Bonobo(expression_file)
model.run_bonobo(
    output_folder=".../bonobo/",
    output_fmt=".h5",  # .h5/.hdf, .txt, or .csv
    keep_in_memory=False,
    delta=None,
    precision="single",
    sample_names=["sample_a"],
    sparsify=False,
    confidence=0.05,
    save_pvals=False,
)
```

`Bonobo` reads the expression table with `header=0` and `index_col=0`: the
first column is the gene axis and the remaining header values are sample IDs.
The agent therefore requires a labelled, unique gene-by-sample matrix with at
least three samples, complete finite numeric values, and explicit declarations
that the values are log-transformed and centered. A requested `sample_names`
list is matched literally against the header. It is never treated as a list of
indices.

The upstream writer creates one matrix per selected sample:

```text
<output_dir>/bonobo_<sample><.h5|.hdf|.txt|.csv>
<output_dir>/pvals_<sample><.h5|.hdf|.txt|.csv>  # only sparsify && save_pvals
```

HDF5 uses keys `bonobo` and `pvals`; TXT is tab-delimited and CSV is
comma-delimited in the agent artifact reader. The matrix has gene IDs as
columns and no row labels, so the agent writes `manifest.json` to preserve the
gene order and sample-to-file mapping. There is no BONOBO aggregate or prior
network output. The agent does not describe a BONOBO matrix as a GRN, TF-gene
regulatory network, or causal network.

## Composition boundaries

BONOBO output is a sample-specific co-expression artifact. It is not directly
valid as PANDA/PUMA `coexpression_file`, which is one validated aggregate,
labeled, square gene-by-gene matrix aligned to the downstream expression gene
axis. For a deliberate BONOBO → PANDA/PUMA handoff, call the explicit
`materialize_bonobo_sample_coexpression(...)` conversion with one real sample
name. It adds the row-label column required by the downstream reader and
preserves the selected sample in the source manifest. No implicit first-sample
selection or averaging is implemented. BONOBO is also not a direct handoff to LIONESS, CONDOR, COBRA,
DRAGON, or OTTER.

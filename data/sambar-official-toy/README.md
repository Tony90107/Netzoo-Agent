# Official netZooPy SAMBAR ToyData

These files are copied from the official netZooPy repository:

`tests/sambar/ToyData/`

Source: https://github.com/netZoo/netZooPy/tree/master/tests/sambar/ToyData

Inputs:

- `mut.ucec.csv` — mutation matrix
- `esizef.csv` — exon/gene sizes
- `genes.txt` — cancer gene list
- `h.all.v6.1.symbols.gmt` — GMT pathway definitions

Reference output:

- `sambar_gt.csv` — upstream expected/reference output

The files are kept separately from `data/sambar-toy/` so the existing agent
fixtures remain unchanged.

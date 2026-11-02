# Official netZooPy toy data

These files were copied from the netZooPy source bundled in this project's
Docker image:

```text
/opt/netZooPy/tests/puma/ToyData/
```

The `.txt` extension is expected. The files use tab-separated/plain-text formats
accepted by netZooPy.

| File | Role |
|---|---|
| `ToyExpressionData.txt` | Expression matrix: gene plus 50 sample values |
| `ToyMotifData.txt` | Regulator-gene prior: regulator, gene, weight |
| `ToyPPIData.txt` | Regulator interaction prior: regulator 1, regulator 2, weight |
| `ToyMiRList.txt` | PUMA regulator list: one name per line |

The toy expression data contains retired gene symbols, which the strict
identifier gate rejects. Switch to Synthetic Test mode with `/test` to run it;
results from that mode are for software testing only.

Execution happens only in an interactive session. Start one with
`OPENROUTER_API_KEY` set:

```bash
./netzoo-chat
```

Then enter `/test`, paste one of the tasks below, review the preview, enter
`/execute`, and confirm with `y`.

PANDA:

```text
Run PANDA using data/official-toy/ToyExpressionData.txt, data/official-toy/ToyMotifData.txt, and data/official-toy/ToyPPIData.txt; write the output to outputs/panda_official_toy.txt
```

PUMA:

```text
Run PUMA using data/official-toy/ToyExpressionData.txt, data/official-toy/ToyMotifData.txt, data/official-toy/ToyPPIData.txt, and data/official-toy/ToyMiRList.txt; write the output to outputs/puma_official_toy.txt
```

To preview a plan without executing anything, pass the task with `--task`
(always preview-only):

```bash
./netzoo-chat --task "Run PANDA using data/official-toy/ToyExpressionData.txt, data/official-toy/ToyMotifData.txt, and data/official-toy/ToyPPIData.txt"
```

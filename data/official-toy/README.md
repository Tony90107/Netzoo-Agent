# Official netZooPy toy data

These files were copied from the netZooPy source bundled in this project's Docker
image:

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

Run PANDA:

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --execute \
  --task "使用 data/official-toy/ToyExpressionData.txt、data/official-toy/ToyMotifData.txt、data/official-toy/ToyPPIData.txt 執行 PANDA，輸出到 outputs/panda_official_toy.txt"
```

Run PUMA:

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --execute \
  --task "使用 data/official-toy/ToyExpressionData.txt、data/official-toy/ToyMotifData.txt、data/official-toy/ToyPPIData.txt 與 data/official-toy/ToyMiRList.txt 執行 PUMA，輸出到 outputs/puma_official_toy.txt"
```

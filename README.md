# Network Zoo PANDA/PUMA Docker + LangGraph Agent

這個專案是為了完成三件事：

1. 了解 PANDA / PUMA 的 input 與 output 格式。
2. 為 PANDA / PUMA 建立 Docker 執行環境。
3. 寫一個 Python script，讓使用者用自然語言描述任務，由 LLM 透過 LangChain / LangGraph 選擇正確工具，並可選擇是否執行。

## 主要文件

| 檔案 | 內容 |
|---|---|
| [TASK_INTERPRETATION.md](TASK_INTERPRETATION.md) | 我對老師任務的邏輯整理 |
| [PANDA_PUMA_Docker_入門.md](PANDA_PUMA_Docker_入門.md) | PANDA/PUMA input-output 與 Docker 入門 |
| [AGENT_USAGE.md](AGENT_USAGE.md) | LangChain/LangGraph agent 使用方式 |
| [NetworkZoo_工具導覽.md](NetworkZoo_工具導覽.md) | Network Zoo 整體工具導覽 |

## Docker 快速開始

建立 image：

```bash
docker compose build
```

進入環境：

```bash
docker compose run --rm netzoo
```

跑 PANDA：

```bash
run-panda \
  -e data/expression.tsv \
  -m data/motif.tsv \
  -p data/ppi.tsv \
  -o outputs/panda_network.tsv
```

跑 PUMA：

```bash
run-puma \
  -e data/expression.tsv \
  -m data/motif.tsv \
  -p data/ppi.tsv \
  -i data/mir.tsv \
  -o outputs/puma_network.tsv
```

## Agent 快速開始

先設定 OpenRouter：

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
export OPENROUTER_MODEL="openai/gpt-4o-mini"
```

讓 agent 判斷任務，但先不真的執行：

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --task "我要用 data/expression.tsv data/motif.tsv data/ppi.tsv 跑 PANDA，輸出到 outputs/panda.tsv"
```

真的執行要加 `--execute`：

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --execute \
  --task "我要跑 PUMA，expression 是 data/expression.tsv，motif 是 data/motif.tsv，PPI 是 data/ppi.tsv，miRNA 是 data/mir.tsv，輸出 outputs/puma.tsv"
```

## 驗證狀態

已在本機 Docker Desktop 驗證：

- `docker compose build` 成功
- `netzoopy --help` 成功
- `run-panda --help` 成功
- `run-puma --help` 成功
- `scripts/netzoo_agent.py --help` 成功
- PANDA 使用官方 toy data 成功跑完
- PUMA 使用官方 toy data 成功跑完

## 注意

PANDA/PUMA 不吃原始 FASTQ。expression data 需要先經過 RNA-seq preprocessing，例如 QC、alignment 或 pseudoalignment、quantification、gene ID mapping、filtering、normalization，最後整理成 expression matrix。

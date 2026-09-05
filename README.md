# Network Zoo PANDA/PUMA Docker + LangGraph Agent

這個專案目前涵蓋：

1. 了解 PANDA / PUMA 的 input 與 output 格式。
2. 為 PANDA / PUMA 建立 Docker 執行環境。
3. 以 LangGraph Planner / Executor / Evaluator 處理自然語言任務：盤點使用者輸入與 workspace 檔案、自主建立多步計畫、執行工具並評估是否繼續。
4. 透過 Context7 MCP 自動查詢本專案相關套件的較新文件。
5. 透過 Tavily Websearch MCP 查詢一般網頁與文獻資訊。
6. 整理 expression 的 gene/sample row/column 方向，讀取 CSV/TSV 時會先略過前置 annotation/comment rows，並輸出 PANDA/PUMA compatible TSV。
7. 試跑 LIONESS-PANDA、LIONESS-PUMA 與 LIONESS co-expression；LIONESS 需要無 header TSV 時，agent 可自動準備 derived expression input。
8. 試跑 CONDOR toy bipartite network。
9. 以 COBRA 分析 sample covariates 對 gene co-expression 的影響，並輸出可重現的 covariance decomposition。
10. 以 SAMBAR 將 somatic mutation matrix 聚合為 pathway mutation scores，並進行可選的 sample clustering。
10. 以 OTTER 的 relaxed graph matching 推論 aggregate TF-to-gene regulatory network，嚴格驗證 TF-TF PPI、gene-gene co-expression 與 seed/prior 的方向、shape、identifier 與 NA 行為。
11. 以 Docker 內固定版本的 netZooPy GIRAFFE 推論 aggregate TF-gene regulation 與 TF-by-sample TFA，並嚴格驗證輸入 identifier、PPI 對稱性與雙輸出。
12. 使用受確認的 UserProfile 與 compact Episode memory，在不同 session 間保留偏好與經驗。

Agent 啟動時先驗證 `AGENTS.md` 與 `workflows/*.yaml`，再進入主要 graph：
`apply project policy -> memory retrieval -> classify -> plan -> execute -> evaluate ->
memory consolidation`。Evaluator 通過後可
回到 Executor 執行下一步，可修復錯誤則走 bounded replan；缺少資料時 CLI 會留在
同一個 resumable session 等待使用者補充。PANDA、PUMA、三種 LIONESS 與 CONDOR
都走同一套 graph，不再由 LIONESS 專用的前置選單攔截。

## 主要文件

| 檔案 | 內容 |
|---|---|
| [CODE_READING_GUIDE.md](CODE_READING_GUIDE.md) | 新讀者的 15 分鐘主線、問題到 owner module 地圖與修改方式 |
| [NETZOO_HARNESS_ARCHITECTURE.md](NETZOO_HARNESS_ARCHITECTURE.md) | Agent 架構、context、記憶與治理 |
| [PANDA_PUMA_Docker_入門.md](PANDA_PUMA_Docker_入門.md) | PANDA/PUMA input-output 與 Docker 入門 |
| [AGENT_USAGE.md](AGENT_USAGE.md) | LangChain/LangGraph agent 使用方式 |
| [AGENTS.md](AGENTS.md) | Runtime 會驗證的人類可讀專案政策入口 |
| [workflows/](workflows/) | PANDA、PUMA、LIONESS、CONDOR、COBRA、DRAGON、OTTER 的 versioned YAML 規格 |
| [NetworkZoo_工具導覽.md](NetworkZoo_工具導覽.md) | Network Zoo 整體工具導覽 |
| [LIONESS_TRIAL.md](LIONESS_TRIAL.md) | 三種 LIONESS toy 實跑、結果與相容修補 |
| [CONDOR_TRIAL.md](CONDOR_TRIAL.md) | CONDOR bipartite toy trial |
| [docs/OTTER_INTEGRATION.md](docs/OTTER_INTEGRATION.md) | OTTER API、CLI、輸入／輸出契約與 handoff 規範 |
| [docs/GIRAFFE_INTEGRATION.md](docs/GIRAFFE_INTEGRATION.md) | GIRAFFE API、Docker runtime、輸入／輸出契約與 workflow 規範 |
| [NEW_TASK_COMPLETE_DEMO_GUIDE.md](NEW_TASK_COMPLETE_DEMO_GUIDE.md) | 四個新任務的完整說明、Demo 與結果驗證 |
| [docs/archive/](docs/archive/) | 歷史進度、舊 demo 與 PR 草稿（不作為現行規格） |

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
export OPENROUTER_MODEL="openai/gpt-4o"
export OPENROUTER_ROUTER_MODEL="openai/gpt-4o"
export OPENROUTER_SEMANTIC_MODEL="openai/gpt-4o"
export NETZOO_RESPONSE_MODEL_ALLOWLIST="openai/gpt-4o"
export NETZOO_MAX_TASK_TOKENS=20000
# 選用：提高 Context7 rate limit
export CONTEXT7_API_KEY="ctx7-..."
# Websearch MCP
export TAVILY_API_KEY="tvly-..."
```

讓 agent 判斷任務，但先不真的執行：

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --task "我要用 data/expression.tsv data/motif.tsv data/ppi.tsv 跑 PANDA，輸出到 outputs/panda.tsv"
```

檢查 project policy，不需 OpenRouter key：

```bash
python scripts/netzoo_agent.py --policy-status
```

試跑完整 LIONESS toy bundle；CLI 會逐步顯示 Planner、Executor 與 Evaluator：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "請幫我跑一次 LIONESS PANDA"
```

如果正式任務缺少路徑，即使使用 `--task` 也會留在 `補充資料 >`，不會直接結束。
可用 `--session NAME` 固定 checkpoint id，之後用 `--resume NAME` 恢復。預設輸出為
可讀且會保留的 activity timeline，會在最終結果前顯示 planning、tool、result 與
evaluation 摘要；`--verbose` 顯示完整 evidence、graph、Evaluator、memory 與 logs，
`--quiet` 則只顯示 compact 最終結果。這些 activity entries 是可稽核的結構化摘要，不是
模型私有 chain-of-thought。

所有 agent 輸出固定為英文，輸入可使用任何語言。成功的自動 one-shot checkpoint
會立即刪除；pending／failed／named session 才會保留。全新互動模式不會暗中接續舊
任務；要恢復最近的 pending session，請明確執行 `--resume latest`。舊的自動 completed session 與 logs
預設保留 30 天後清理；任何 named 或 pending session 最長保留 180 天。

長期偏好與 compact task episodes 以 `--profile` 隔離。偏好只有在使用者明確提出並
再次回答 `yes` 後才會保存；episode 預設依狀態保留 30／60／180 天，每個 profile
最多 200 筆與約 10 MiB，並在讀寫時自動清理。不需 API key 即可檢查、立即清理或刪除：

```bash
python scripts/netzoo_agent.py --profile alice --memory-status
python scripts/netzoo_agent.py --memory-cleanup
python scripts/netzoo_agent.py --profile alice --forget-memory
```

真的執行必須進入互動模式；先建立並核准 Work Plan，再用 `/execute`
授權該計畫單次執行：

```bash
./netzoo-chat
```

```text
What would you like to accomplish with NetZoo?
> /
  execute
```

Planning is the default preview-only state and has no prompt label. Press `/` at
an empty prompt to show the muted `execute` completion; the input itself still
contains only `/`. Press Enter to submit `/execute`, or continue typing to enter
`/planning`, `/status`, or `/help`. `/execute` first checks the current Work Plan,
asks for confirmation, grants execution authority to that graph turn only, and then
automatically returns to Planning mode. A slash typed after other text remains
literal. Path prompts intentionally do not open the completion, so absolute paths
and slash commands can be typed normally. To interrupt analysis already running,
use Ctrl-C.

`--task` 是非互動 preview-only 介面，不接受 `--execute`。

## 驗證狀態

已在本機 Docker Desktop 驗證：

- `docker compose build` 成功
- `netzoopy --help` 成功
- `run-panda --help` 成功
- `run-puma --help` 成功
- `scripts/netzoo_agent.py --help` 成功
- PANDA 使用官方 toy data 成功跑完
- PUMA 使用官方 toy data 成功跑完

## Expression 格式

netZooPy 共用格式是每列一個 gene、第一欄為 gene ID、後續欄位為各 sample
的數值。PUMA 與 legacy LIONESS 的 expression input 使用無 header TSV；本專案
的 `run-lioness` wrapper 會替三種 LIONESS text output 都保留或補上 header。

Agent 可把 sample 在 rows、gene 在 columns 的 CSV/TSV 轉置：

```text
把 data/raw.csv 的 samples×genes 整理成 PANDA 格式，
genes 在 columns，輸出 data/expression.tsv
```

如果原始 CSV/TSV 前幾行是 annotation，例如 `# ...`、`Annotation: ...`、
`metadata ...`，agent 會在讀檔時略過這些前置說明列，再判斷表格方向。
輸出一律使用 tab-delimited TSV，方便接到 PANDA、PUMA 與 legacy LIONESS。

## LIONESS 三種模式

```bash
run-lioness panda \
  -e data/lioness-toy/expression.tsv \
  -m data/lioness-toy/motif-panda.tsv \
  -p data/lioness-toy/ppi.tsv \
  -o outputs/lioness-toy/panda.tsv \
  -q outputs/lioness-toy/lioness-panda.txt

run-lioness puma \
  -e data/lioness-toy/expression.tsv \
  -m data/lioness-toy/prior-puma.tsv \
  -p data/lioness-toy/ppi.tsv \
  -i data/lioness-toy/mirna.txt \
  -o outputs/lioness-toy/puma.tsv \
  -q outputs/lioness-toy/lioness-puma.tsv

run-lioness coexpression \
  -e data/lioness-toy/expression.tsv \
  -o outputs/lioness-toy/coexpression.tsv \
  -q outputs/lioness-toy/lioness-coexpression.txt
```

PUMA 的 `-m` 是 TF/miRNA-to-gene 合併 prior；`-i` 是無 header、每行恰好
一個 miRNA ID 的清單。每個 ID 都必須出現在 prior 第一欄。

## CONDOR toy trial

```bash
docker compose run --rm netzoo run-condor \
  -i data/condor-toy/bipartite.tsv \
  -o outputs/condor-toy \
  --prefix toy
```

## COBRA：covariate-aware co-expression

COBRA 使用有 sample header 的 gene × sample expression matrix，以及 sample × covariate
design matrix。兩者的 sample ID 必須完全一致（順序可以不同，執行時會對齊），且 design
covariates 必須先編碼為數值。COBRA 會保留 covariate-associated covariance decomposition，
並額外將 intercept component 重建成帶 gene ID 的 adjusted co-expression artifact。

```bash
docker compose run --rm netzoo run-cobra \
  -e data/cobra-toy/expression.tsv \
  -d data/cobra-toy/design.tsv \
  -o outputs/cobra-toy
```

COBRA 會在指定資料夾直接產生 `manifest.json`（inputs、checksum、sample ordering）、
`components.npz`（完整 `psi`、`Q`、`d`、`g`）、`summary.tsv`，以及可直接交給 PANDA/PUMA
的 `adjusted_coexpression.tsv` 與 `adjusted_coexpression.npz`。透過 `coexpression_file`
指定 artifact 時，它會取代 PANDA/PUMA 內部的 Pearson co-expression 建構；expression file
仍保留作為 gene/prior 對齊來源。互動模式
啟用 `/execute` 後，同一資料夾還會有一份 `cobra-execution-*.md` execution log；input
inspection 不會另寫公開 log。未指定 output directory 時，所有工作流都使用既有的
`outputs/demo/`，避免新增 workflow 專屬子資料夾。

COBRA 不只可和 PANDA 配合：PUMA 也有相同的 gene-gene co-expression 依賴，現在可用同一
個 artifact。LIONESS-PANDA/PUMA 則需要每個 leave-one-out 子集重新形成的 co-expression，
因此 aggregate COBRA artifact 不能直接冒充 sample-specific LIONESS 輸入；CONDOR 是
調控網路之後的二分圖社群分析，不直接消費 COBRA co-expression。

## SAMBAR：somatic-mutation pathway subtyping

SAMBAR 使用 samples × genes 的 mutation CSV、**一列且 gene IDs 為欄位**的 exon-size CSV、
一行 tab-delimited cancer-gene list，以及 GMT pathway file。這個 exon-size layout 是本專案
pin 的 netZooPy 實際實作所讀取的格式。所有四類輸入都必須有 gene identifier overlap。

```bash
docker compose run --rm netzoo run-sambar \
  -m data/sambar-toy/mutation.csv \
  -e data/sambar-toy/exon_size.csv \
  -g data/sambar-toy/cancer_genes.txt \
  -p data/sambar-toy/pathways.gmt \
  -o outputs/sambar-toy --kmin 2 --kmax 3
```

輸出為 `mt_out.csv`（sample × gene mutation scores）、`pt_out.csv`（pathway × sample
scores），以及 cluster=true 時的 `clustergroups.csv`、`dist_matrix.csv` 和可追溯
`manifest.json`。SAMBAR results 不能直接餵給 PANDA、PUMA、LIONESS、CONDOR 或 COBRA；必須
另行準備並驗證目標 workflow 的宣告 input artifact。

重建 image 後可執行真實容器 release regression；它會先確認 image 內的 SAMBAR runner、
input validator 與 artifact validator 和目前 checkout 完全一致，再跑 toy bundle 並驗證五個
宣告產物：

```bash
NETZOO_RUN_DOCKER_TESTS=1 pytest -q tests/test_sambar_container.py
```

CONDOR 的輸入是 bipartite edge list，至少包含 source、target，第三欄
weight 可選。Toy data 使用 TF-like regulator 到 gene 的二分網路。

## 注意

PANDA/PUMA 不吃原始 FASTQ。expression data 需要先經過 RNA-seq preprocessing，例如 QC、alignment 或 pseudoalignment、quantification、gene ID mapping、filtering、normalization，最後整理成 expression matrix。

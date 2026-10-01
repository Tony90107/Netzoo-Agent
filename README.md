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
11. 以 OTTER 的 relaxed graph matching 推論 aggregate TF-to-gene regulatory network，嚴格驗證 TF-TF PPI、gene-gene co-expression 與 seed/prior 的方向、shape、identifier 與 NA 行為。
12. 以 Docker 內固定版本的 netZooPy GIRAFFE 推論 aggregate TF-gene regulation 與 TF-by-sample TFA，並嚴格驗證輸入 identifier、PPI 對稱性與雙輸出。
13. 以 LIONESS-DRAGON 為同一批樣本的兩層 omics 建立每個樣本的 partial-correlation 網路，並同時輸出整體 DRAGON 網路。
14. 使用受確認的 UserProfile 與 compact Episode memory，在不同 session 間保留偏好與經驗。
15. 依照使用者的下載意圖，取得 STRING 指定物種的蛋白質網路資料；支援一般關聯、物理互作與方向性調控三種網路。

Agent 啟動時先驗證 `AGENTS.md` 與 `workflows/*.yaml`，再進入主要 graph：
`apply project policy -> memory retrieval -> classify -> plan -> execute -> evaluate ->
memory consolidation`。Evaluator 通過後可
回到 Executor 執行下一步，可修復錯誤則走 bounded replan；缺少資料時 CLI 會留在
同一個 resumable session 等待使用者補充。PANDA、PUMA、四種 LIONESS 與 CONDOR
都走同一套 graph，不再由 LIONESS 專用的前置選單攔截。

## 快速開始

第一次使用跑這一個指令就好：

```bash
./setup
```

它會依序檢查 Docker、建立 `.env`（互動詢問 OpenRouter API key，輸入不回顯、檔案權限
600）、建置映像，最後編譯桌面 app。任何一步的前置條件沒滿足時會直接說明要做什麼，
而不是把 compose 的堆疊訊息丟出來。

| 指令 | 用途 |
|---|---|
| `./setup` | 完整安裝：Docker 環境 + 桌面 app |
| `./setup --cli-only` | 只裝 Docker 環境，不編譯桌面 app |
| `./setup --skip-image` | 映像已建好，只做其餘步驟 |

### 前置需求

| 需要 | 用途 | 備註 |
|---|---|---|
| Docker Desktop | 所有 workflow 都在容器裡執行 | 跑 `./setup` 前要先啟動 |
| OpenRouter API key | agent 的 LLM 呼叫 | <https://openrouter.ai/keys>，按 token 計費 |
| Node.js 20+ 與 Rust | 編譯桌面 app | 只有桌面版需要，`--cli-only` 可略過 |

桌面版只在 **macOS（Apple Silicon）** 上驗證過。Docker 環境與終端版不限平台；Tauri 在 Linux／Windows 上會產出 `.deb`／`.AppImage`／`.msi`，但未經測試。

映像是 `netzoo_agent:latest`，實測 **5.58GB**；冷啟建置需要數十分鐘，主要花在下載與
編譯相依套件，之後都走 layer cache。

預設寫入 `.env` 的模型是 `openai/gpt-4o-mini`——這也是 routing 量測所用的模型。
`NETZOO_RESPONSE_MODEL_ALLOWLIST` 與 `NETZOO_ROUTER_MODEL_ALLOWLIST` 是防止請求誤打到
昂貴模型的那道限制，要放寬請明確修改，不要順手拿掉。

### 啟動

```bash
# 桌面版
open "desktop/src-tauri/target/release/bundle/macos/NetZoo Agent.app"

# 終端版
./netzoo-chat
```

### 選項選單、精簡回覆與 session 管理

- **選項選單**：一個問題有多個合適答案時（方法平手、多種讀法、多個假設、澄清），回覆下方會出現選項面板。
  每個選項附一行重點（好處、是否吻合你要的結果、何時選、還缺什麼），有依據的推薦排第一並標 `Recommended`。
  ↑↓ 移動、Enter 或數字鍵選擇；最後一列「Type your own answer」可就地用自己的話回答。
- **精簡回覆**：先顯示結論與 2–5 條重點，以及「此 agent 無法執行的相關項目」；完整說明可展開（終端版用 `/details`，
  `--full-replies` 恢復全文）。
- **下一步**：Execute this plan（仍需兩段式核准）、Plan X with my data、Compare with …、Open the outputs、Start a new task。
- **Session 即實驗**：New session 時取名稱、選模型（限 allowlist）並加 tag；session 記錄並沿用它的模型；
  名稱與筆記可隨時在標題列或 session 檢視修改；tag 可以是標籤（`pilot`）或欄位（`dataset:batch-2`，每個 session 一個值）；
  沒指定輸出路徑時寫到 `outputs/sessions/<session id>/`；Outputs 分頁預設「By session」：一個 session 一筆、最新的在最上面
  （只有一個結果就直接是那個檔案，manifest 與執行紀錄收在「+N run files」；多個結果才是只放該 session 檔案的資料夾），
  「Folders」仍可瀏覽磁碟上的資料夾；
  每次執行的報告（`*-execution-*.md`）在彈窗中以可閱讀的版面呈現（重點卡＋可收合章節，可切回原文）；
  輸出預覽可跳回產生它的 session；
  Resume 沿用原本的 session id（與終端版 `--resume` 相同）；
  session 列表可依名稱、筆記、tag 搜尋與篩選，並可勾選 2–4 個 session 並排比較（每個欄位一列）。

詳見 [docs/ui-choices-sessions-2026-09-30.md](docs/ui-choices-sessions-2026-09-30.md)。

### 為什麼不提供編譯好的 .app

macOS 的 `com.apple.quarantine` 屬性是**下載器**（瀏覽器、AirDrop、郵件）貼上去的。
本機編譯出來的執行檔沒有這個屬性，Gatekeeper 因此不會評估它，可以直接打開——不需要
「右鍵 → 打開」，也不需要 Apple Developer 簽名。

反過來說，若把編譯好的 .app 當成 GitHub Release 讓人下載，它**會**被擋：這個 bundle 是
ad-hoc 簽名、沒有 Team ID。而使用者無論如何都得安裝 Docker 並建置 5.58GB 的映像，
相比之下多編譯一次 app 的邊際成本很低。因此本專案只支援從原始碼建置。

app 請留在 repo 目錄內：它是從自己的路徑往上走去找 `docker-compose.yml` 的，
搬到 `/Applications` 之後上層就沒有 repo 可找了。

## 主要文件

| 檔案 | 內容 |
|---|---|
| [CODE_READING_GUIDE.md](CODE_READING_GUIDE.md) | 新讀者的 15 分鐘主線、問題到 owner module 地圖與修改方式 |
| [NETZOO_HARNESS_ARCHITECTURE.md](NETZOO_HARNESS_ARCHITECTURE.md) | Agent 架構、context、記憶與治理 |
| [PANDA_PUMA_Docker_入門.md](PANDA_PUMA_Docker_入門.md) | PANDA/PUMA input-output 與 Docker 入門 |
| [AGENT_USAGE.md](AGENT_USAGE.md) | LangChain/LangGraph agent 使用方式 |
| [AGENTS.md](AGENTS.md) | Runtime 會驗證的人類可讀專案政策入口 |
| [workflows/](workflows/) | PANDA、PUMA、LIONESS（PANDA／PUMA／co-expression／DRAGON）、BONOBO、CONDOR、COBRA、DRAGON、OTTER、GIRAFFE、SAMBAR 的 versioned YAML 規格 |
| [docs/DESKTOP_UI_ARCHITECTURE.md](docs/DESKTOP_UI_ARCHITECTURE.md) | 桌面版的分層、程序模型、協定與里程碑設計 |
| [docs/ui-choices-sessions-2026-09-30.md](docs/ui-choices-sessions-2026-09-30.md) | 選項選單、精簡回覆卡片、下一步操作與以 session 管理實驗 |
| [NetworkZoo_工具導覽.md](NetworkZoo_工具導覽.md) | Network Zoo 整體工具導覽 |
| [LIONESS_TRIAL.md](LIONESS_TRIAL.md) | 三種 LIONESS toy 實跑、結果與相容修補 |
| [CONDOR_TRIAL.md](CONDOR_TRIAL.md) | CONDOR bipartite toy trial |
| [docs/WEBSEARCH_GENE_TEST_PROMPTS.md](docs/WEBSEARCH_GENE_TEST_PROMPTS.md) | Websearch 與 gene authority 的手動測試 prompts |
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
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -o outputs/panda_network.txt
```

跑 PUMA：

```bash
run-puma \
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -i data/official-toy/ToyMiRList.txt \
  -o outputs/puma_network.txt
```

## Agent 快速開始

### 下載 STRING 網路資料

在 `./netzoo-chat` 或桌面版輸入，例如「下載 STRING 的人類調控網路」或
「Download the STRING physical network for mouse」。如果沒有說明物種，agent 會問物種名稱
或 NCBI taxonomy ID；如果沒有說明網路類型，會問 `functional`（一般蛋白質關聯）、
`physical`（物理互作）或 `regulatory`（方向性調控）。

agent 先顯示下載計畫；輸入 `/execute` 並確認後，才用 `curl` 從 STRING 官方檔案主機下載。
預設放在 `data/string/`，也可在請求中指定 `output_dir=...`。它會先檢查本機
`data/`、`outputs/` 與指定資料夾；若相同物種、網路類型及 STRING 版本的檔案已存在，
會指出原檔位置，不會重複下載或覆蓋。下載採暫存檔，確認 gzip 與資料欄位後才存成正式檔案。

目前使用 STRING **v12.5** 的標準 `protein.links`、`protein.physical.links` 與
`protein.regulatory.links` 壓縮檔。調控檔是**方向性蛋白質連結**，不能直接當成
PANDA／PUMA 的 TF→gene motif prior 或推論出的 gene regulatory network。
Websearch 可用來查詢 STRING 文件；實際下載使用已知的[官方下載頁](https://string-db.org/cgi/download)
及其 `stringdb-downloads.org` 檔案連結，不依賴搜尋結果中的任意網址。

先設定 OpenRouter：

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
export OPENROUTER_MODEL="openai/gpt-4o-mini"
export OPENROUTER_ROUTER_MODEL="openai/gpt-4o-mini"
export OPENROUTER_SEMANTIC_MODEL="openai/gpt-4o-mini"
export NETZOO_RESPONSE_MODEL_ALLOWLIST="openai/gpt-4o-mini"
export NETZOO_MAX_TASK_TOKENS=20000
# 選用：提高 Context7 rate limit
export CONTEXT7_API_KEY="ctx7-..."
# Websearch MCP
export TAVILY_API_KEY="tvly-..."
# Gene authority lookup: auto/on/off. auto enables it when Websearch is configured.
export NETZOO_GENE_ONLINE_LOOKUP="auto"
```

基因 ID 驗證採 cache-first。cache miss 時先查結構化的 NCBI Datasets API
（gene symbol／NCBI Gene ID）或 Ensembl REST API（Ensembl gene ID），並從回傳欄位
核對 taxon/species；權威 API 成功回覆但沒有該 ID 才標記為 `invalid` 並阻擋執行。
只有在結構化 API 無法連線時才使用 Websearch，且搜尋結果只視為 discovery evidence，
不會單獨把 ID 判成有效或無效。沒有網路時仍可使用未過期 cache；未查證的 ID 會標成
`unverified`，格式與跨檔案 ID 相容性檢查仍會繼續。

所有 13 個 run workflow 都在 planning 後與 `/execute` 前共用同一個 fail-closed
preflight gate。檔名只提供弱提示；內容 schema、gene-like label、樣本軸，以及多檔案
集合/順序相容性才是是否可執行的依據。CONDOR node 與 DRAGON／LIONESS-DRAGON feature 允許非基因標籤，
因此不強制查 gene authority，但仍執行各自的二分圖與雙層資料契約檢查。

讓 agent 判斷任務，但先不真的執行：

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --task "我要用 data/official-toy/ToyExpressionData.txt data/official-toy/ToyMotifData.txt data/official-toy/ToyPPIData.txt 跑 PANDA，輸出到 outputs/panda.txt"
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
`/test`, `/planning`, `/status`, or `/help`. `/test` enters Synthetic Test mode:
schema, numeric, and cross-file checks remain enforced, while unresolved gene
labels are explicitly marked test-only instead of being treated as biological
evidence. A resulting plan still requires `/execute` before any workflow runs.
Use `/planning` to leave Synthetic Test mode and return to strict validation.
`/execute` first checks the current Work Plan,
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
把 data/format-demo/sample-by-gene.tsv 的 samples×genes 整理成 PANDA 格式，
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

第四種 LIONESS-DRAGON 不經 `run-lioness`：agent 直接呼叫 netZooPy 的 DRAGON 函式
（`scripts/netzoo_agent_core/execution_lioness_dragon.py`）。輸入與 DRAGON 相同（兩個
sample × feature 表格、sample ID 集合一致），λ 在全部樣本上估計一次，每個樣本的網路為
N_k = n(N_all − N_without_k) + N_without_k（同 netZooPy `lioness_for_dragon.py`）。
`output_file` 是整體矩陣，`lioness_output` 是 edge × sample 表（source、target、每個樣本一欄）；
至少 3 個樣本，edge 數 × 樣本數超過 20,000,000 會在執行前拒絕。LIONESS-OTTER 在 netZooPy
有實作，但此 agent 未登記，只在回覆中列為參考。

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
inspection 不會另寫公開 log。未指定 output directory 時，session 內的工作流寫到
`outputs/sessions/<session id>/`（在 session 外規劃時仍是 `outputs/demo/`），不另建 workflow 專屬子資料夾。

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

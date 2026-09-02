# NetZoo agent 三項功能自測 Prompt 與方法

這份文件讓你可以用目前 repository 已有的資料，逐項驗證：

1. `/execute` 是一次性執行授權，不是 planning／execute toggle。
2. 檔名無法判斷時，agent 是否能以內容提出檔案角色候選，並先請使用者確認。
3. SAMBAR 是否能在容器中執行、產生正確 artifact，且不破壞其他 workflow。

本次沒有另外建立永久的生物資料 fixture；直接使用既有的
`data/lioness-toy/`、`data/sambar-official-toy/` 與 `data/sambar-toy/`。
我新增的只有這份測試指南。

## 0. 測試前準備

在 repository root 執行：

```bash
cd "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent"
docker compose build netzoo
```

互動 agent：

```bash
./netzoo-chat
```

若要保留可恢復的 session，使用固定名稱；若只做一次手動測試，可省略：

```bash
./netzoo-chat --session three-feature-test
```

## 1. `/execute` 一次性執行與 Work Plan 完整性

### 可直接貼給 agent 的 Prompt

```text
請測試目前 NetZoo agent 的執行閘門，不要把 /execute 當成模式切換。

第一階段只做 planning：
1. 使用 data/sambar-official-toy/mut.ucec.csv、esizef.csv、genes.txt、h.all.v6.1.symbols.gmt。
2. 規劃 SAMBAR，輸出到 outputs/manual-execute-sambar。
3. 顯示完整 Work Plan：workflow、每個 input path、參數、預期 artifacts、validation、handoff/rollback 風險。
4. 在我輸入 /execute 前，不得執行 Docker、不得建立輸出檔。

收到 /execute 後，先檢查 Work Plan 是否完整且已通過 validation；列出將執行的步驟並詢問一次確認。
只有我回答 yes/確認後才執行，而且只執行這一次；執行結束後自動回到 planning mode。
```

### 手動步驟與預期結果

1. 貼上 Prompt，確認只看到 plan，`outputs/manual-execute-sambar/` 尚未產生。
2. 輸入 `/status`：應顯示仍在 planning、plan 尚未獲得 execution authority。
3. 輸入 `/execute`：應重新檢查 plan 並要求確認，不應直接執行。
4. 回答 `no`：不應產生 SAMBAR artifacts，仍留在 planning。
5. 再輸入 `/execute` 並回答 `yes`：應只執行一次，產生 `manifest.json`、`mt_out.csv`、`pt_out.csv`。
6. 執行完成後再輸入 `/execute`：若沒有新的完整 plan，應阻擋或要求建立新 plan，不得重跑舊計畫。

通過條件：

- planning 階段沒有 tool side effect。
- `/execute` 是 execution grant，不是永久 mode toggle。
- 不完整 plan（缺 input、output、參數或 validation）會被阻擋。
- `yes` 只授權一個 graph turn／一次執行，完成後回到 planning。

## 2. 檔名失效時的內容辨識與使用者確認

### 準備匿名檔名（使用既有資料的暫存副本）

這個指令只在 `/tmp` 建立可刪除的副本，不修改 repository 原始資料：

```bash
T=$(mktemp -d)
cp data/lioness-toy/expression.tsv "$T/table_01.dat"
cp data/lioness-toy/motif-panda.tsv "$T/table_02.dat"
cp data/lioness-toy/ppi.tsv "$T/table_03.dat"
cp data/lioness-toy/mirna.txt "$T/list_04.dat"
echo "$T"
```

記下最後輸出的 `$T` 路徑。這些檔案內容不變，只有檔名故意失去語意。

### 可直接貼給 agent 的 Prompt

```text
請測試 input role discovery。以下四個檔案的檔名沒有語意，不能只靠檔名猜測：

<把 $T/table_01.dat、$T/table_02.dat、$T/table_03.dat、$T/list_04.dat 的絕對路徑貼在這裡>

我要執行 PUMA，但在辨識完成前不要執行任何 workflow。
請逐一讀取檔案內容與表格結構，為每個檔案提出最可能的角色：
expression_file、motif_file、ppi_file、mirna_file。

對每個候選回報：path、候選角色、confidence、內容證據、與其他檔案的 identifier overlap、仍存在的歧義。
不要把 LLM 猜測直接當成事實；先用清楚的清單問我確認每個 mapping。
若 confidence 不足或有兩個合理 mapping，標示為 unresolved 並停在 needs_confirmation。
只有我回答「確認這個 mapping」後，才建立完整 Work Plan；再次收到 /execute 且我確認後才可執行。
```

### 反向測試（確認不會盲猜）

把其中一個檔案換成內容不相容的檔案，例如：

```bash
cp data/manual-tests/motif-no-gene-overlap.tsv "$T/table_02.dat"
```

重新送出相同 Prompt。agent 應指出 gene identifier 不相容、降低 confidence 或要求替換檔案，不應因檔名位置而強行接受。

通過條件：

- 檔名失效時確實檢查內容，而非直接依序配對。
- 回報候選、證據與 confidence。
- 在使用者確認前不執行、不寫入正式 output。
- 不相容內容會進入 needs_confirmation／needs_input，而不是靜默接受。

完成後可清理暫存資料：

```bash
rm -rf "$T"
```

## 3. SAMBAR 容器整合、相容性與 workflow regression

### 可直接貼給 agent 的 Prompt

```text
請做 SAMBAR release regression，使用官方 netZooPy ToyData：
data/sambar-official-toy/mut.ucec.csv
data/sambar-official-toy/esizef.csv
data/sambar-official-toy/genes.txt
data/sambar-official-toy/h.all.v6.1.symbols.gmt

要求：
1. 只能在我確認 Work Plan 並輸入 /execute 後執行。
2. 在 Docker 中執行 SAMBAR，先用 --no-cluster，kmin=2、kmax=4。
3. 驗證 manifest method/parameters、mt_out.csv、pt_out.csv 的 shape、numeric values、sample IDs。
4. 注意官方 SAMBAR 可能省略 mutation score 全零的 sample；這只有在被省略 row 全為零時才算合法。
5. 執行 pip check，回報是否有 dependency conflict。
6. 說明 SAMBAR output 是否能直接 handoff 到其他 workflow；若不能，列出需要的轉換與重新驗證，不要自行串接。
7. regression 結束後，確認 agent 仍能規劃 PANDA、PUMA、GIRAFFE、BONOBO、DRAGON、OTTER 等其他 workflow。
```

### 不依賴 LLM 的直接容器測試

```bash
NETZOO_RUN_DOCKER_TESTS=1 pytest -q tests/test_sambar_container.py
docker run --rm netzoo_agent:latest python -m pip check
pytest -q
ruff check scripts tests
git diff --check
```

預期結果：

- SAMBAR container regression：`1 passed`
- `pip check`：`No broken requirements found.`
- 完整測試全部通過；目前基準為 `653 passed, 21 skipped`
- lint 與 whitespace check 通過

### SAMBAR 產物形狀檢查

```bash
python - <<'PY'
import pandas as pd
from pathlib import Path

root = Path("outputs/sambar-official-toy")
for name in ("mt_out.csv", "pt_out.csv"):
    frame = pd.read_csv(root / name, index_col=0)
    print(name, frame.shape)
PY
```

目前官方資料的預期形狀是：

- `mt_out.csv`: `(248, 898)`
- `pt_out.csv`: `(50, 247)`

這些是結構與相容性測試，不代表 toy data 可以支持真實生物結論。

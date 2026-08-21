# 歷史文件：本次任務完成說明與 Demo 指令

日期：2026-07-08

這份文件只整理本次對話中的任務，不包含更早以前的其他進度，避免內容太長。

## 任務範圍

本次任務有四項：

1. 去除資料檔前幾行的 annotation。
2. 判斷輸入檔是 TSV 或 CSV，用不同的 pandas read function/參數讀取，並儲存成 PANDA/PUMA compatible format。
3. 讓 agent/LLM 檢查 LIONESS input；如果 expression 不符合 legacy LIONESS 需求，就自動準備可用 input。若缺的是 motif、PPI、miRNA 這種不能憑空產生的生物資料，則停止並要求使用者提供。
4. 試跑 CONDOR。

## 我怎麼判斷 Annotation

老師寫「去除前幾行 Annotation」時，我判斷這比較可能是指資料檔前面的說明列，例如：

```text
# exported by upstream tool
Annotation: demo cohort
metadata: ...
gene,s1,s2,s3
GeneA,1,2,3
```

而不是 Python code 裡面的 type annotation。原因是這句話緊接著「判斷 tsv/csv、用 pandas function read、存成 PANDA/PUMA compatible format」，所以最合理的落點是資料讀取與格式轉換流程。

因此我做的是：讀 CSV/TSV 前先跳過前置註解或 metadata rows，再把真正的表格讀進 pandas。

## 實作重點

主要修改檔案：

- `scripts/netzoo_agent.py`
- `tests/test_agent_gate.py`
- `docker/run-condor`
- `Dockerfile`
- `README.md`
- `CONDOR_TRIAL.md`
- `data/condor-toy/bipartite.tsv`
- `outputs/condor-toy/*`

### 1. CSV/TSV 判斷與 Annotation 跳過

在 `scripts/netzoo_agent.py` 新增共用讀表邏輯：

- 依副檔名 `.csv` 使用 comma delimiter。
- 依副檔名 `.tsv` / `.tab` 使用 tab delimiter。
- 如果副檔名不明顯，從前幾行推斷 comma、tab 或 whitespace。
- 跳過前置空行、`# ...`、`// ...`、`Annotation: ...`、`metadata ...`、`note ...` 等 annotation/comment rows。
- 後續所有 inspection、format expression、co-expression conversion 都走同一套讀取邏輯。

這樣使用者不需要手動刪除資料檔前面的說明列。

### 2. 輸出成 PANDA/PUMA Compatible Format

PANDA/PUMA 比較穩定的 expression 格式是：

```text
GeneA<TAB>1<TAB>2<TAB>3
GeneB<TAB>4<TAB>5<TAB>6
```

也就是：

- gene 在 rows。
- 第一欄是 gene ID。
- 後面每欄是 sample expression value。
- legacy PUMA/LIONESS 使用 headerless TSV 比較安全。

所以 `format_expression_for_netzoo` 現在會：

- 讀 CSV 或 TSV。
- 自動跳過前置 annotation。
- 判斷 genes 在 rows 或 columns。
- 必要時轉置。
- 輸出 tab-delimited TSV。
- 可由 `with_header` 控制是否保留 header；PUMA/LIONESS demo 使用 `with_header=false`。

### 3. LIONESS Input 檢查與自動準備

legacy LIONESS 需要：

- expression 是 headerless TSV。
- gene 在 rows、sample 在 columns。
- 至少三個 samples。
- LIONESS-PANDA 還需要 motif、PPI。
- LIONESS-PUMA 還需要 prior、PPI、miRNA list。

我新增的邏輯是：

- 若 expression 已經是 headerless TSV，就直接用原檔。
- 若 expression 是 CSV、有 header、或前面有 annotation，agent 會自動建立一份 derived expression：

```text
<原檔名>.lioness-expression.tsv
```

- 然後 LIONESS command 會改用這份整理後的 expression。
- 若缺 motif、PPI、miRNA，agent 不會自己猜，因為這些是生物先驗資料，不能合理自動產生。

### 4. CONDOR 試跑

CONDOR 做的是 bipartite network community detection。它不像 PANDA/PUMA 那樣吃 expression、motif、PPI，而是吃二分網路 edge list。

我新增 toy input：

```text
data/condor-toy/bipartite.tsv
```

格式：

```text
source<TAB>target<TAB>weight
TF1<TAB>GeneA<TAB>1.0
TF1<TAB>GeneB<TAB>0.8
```

也新增 Docker wrapper：

```text
docker/run-condor
```

它會：

- 跳過前置 annotation rows。
- 讀 CSV/TSV/whitespace edge list。
- 呼叫 netZooPy CONDOR API。
- 輸出 cleaned edges、membership table、summary。

## Demo 指令

以下指令都從專案根目錄執行：

```bash
cd "/Users/chenzhonghan/Documents/LLM AGENT/network-zoo-panda-puma"
```

### Demo 1：跑單元測試

```bash
python tests/test_agent_gate.py
```

預期結果：

```text
Ran 36 tests
OK
```

### Demo 2：檢查 Python 語法

```bash
python -m py_compile scripts/netzoo_agent.py docker/run-condor
```

預期：沒有輸出，代表語法檢查通過。

如果這個指令產生 `__pycache__`，可以清掉：

```bash
find scripts tests docker -name '__pycache__' -type d -prune -exec rm -rf {} +
```

### Demo 3：Annotation + CSV 轉 PANDA/PUMA TSV

建立一個含 annotation 的 CSV demo input：

```bash
mkdir -p outputs/demo

cat > outputs/demo/annotated-expression.csv <<'EOF'
# exported by upstream tool
Annotation: demo cohort
gene,s1,s2,s3
GeneA,1,2,3
GeneB,4,5,6
EOF
```

用 agent formatter 轉成 headerless TSV：

```bash
python - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, "scripts")
import netzoo_agent as agent

agent.EXECUTE_TOOLS = True
print(agent.format_expression_for_netzoo.invoke({
    "expression_file": "outputs/demo/annotated-expression.csv",
    "output_file": "outputs/demo/annotated-expression-formatted.tsv",
    "genes_axis": "auto",
    "with_header": False,
}))
PY
```

查看輸出：

```bash
sed -n '1,20p' outputs/demo/annotated-expression-formatted.tsv
```

預期輸出：

```text
GeneA	1	2	3
GeneB	4	5	6
```

重點是 report 裡會看到：

```text
detected input delimiter: CSV
skipped leading annotation/comment rows: 2
output delimiter: TSV
```

### Demo 4：LIONESS 自動準備 Headerless Expression

建立一個 LIONESS 不直接相容的 CSV expression：

```bash
mkdir -p outputs/demo

cat > outputs/demo/lioness-expression-with-header.csv <<'EOF'
# annotation
gene,s1,s2,s3
GeneA,1,2,3
GeneB,4,3,2
EOF
```

只 demo 自動準備 expression 的 helper：

```bash
python - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
import netzoo_agent as agent

agent.EXECUTE_TOOLS = True
prepared_path, report, sample_count, has_header, error = agent._prepare_lioness_expression(
    "outputs/demo/lioness-expression-with-header.csv",
    "outputs/demo/lioness-panda.tsv",
)

print("prepared_path:", prepared_path)
print("sample_count:", sample_count)
print("has_header:", has_header)
print("error:", error)
print()
print(report)
PY
```

查看自動產生的檔案：

```bash
sed -n '1,20p' outputs/demo/lioness-expression-with-header.lioness-expression.tsv
```

預期輸出：

```text
GeneA	1	2	3
GeneB	4	3	2
```

這表示 LIONESS 之後會改用這份 headerless TSV。

### Demo 5：Docker Build

CONDOR 和 LIONESS wrapper 都在 Docker image 裡，因此要先 build：

```bash
docker compose build
```

預期結果：`netzoo-panda-puma:latest` build 成功。

### Demo 6：試跑 CONDOR

使用本次新增的 toy bipartite network：

```bash
docker compose run --rm netzoo run-condor \
  -i data/condor-toy/bipartite.tsv \
  -o outputs/condor-toy \
  --prefix toy
```

預期會看到類似：

```text
Read 8 edges as TSV; skipped 2 annotation/comment row(s).
Initial modularity:  0.5274884259259259
BRIM:
0.5383873456790124
Wrote outputs/condor-toy/toy-edges.tsv
Wrote outputs/condor-toy/toy-summary.txt
```

檢查輸出檔：

```bash
find outputs/condor-toy -maxdepth 1 -type f -print
```

預期包含：

```text
outputs/condor-toy/toy-reg_memb.tsv
outputs/condor-toy/toy-tar_memb.tsv
outputs/condor-toy/toy-edges.tsv
outputs/condor-toy/toy-summary.txt
```

查看 summary：

```bash
sed -n '1,80p' outputs/condor-toy/toy-summary.txt
```

本次實跑結果：

```text
CONDOR trial summary
edges: 8
sources: 4
targets: 6
modularity: 0.5383873456790124
Qcoms: [0.16319444 0.10609568 0.16493056 0.10416667]
```

查看 community membership：

```bash
sed -n '1,40p' outputs/condor-toy/toy-reg_memb.tsv
sed -n '1,60p' outputs/condor-toy/toy-tar_memb.tsv
```

### Demo 7：透過 Agent 試跑 CONDOR

CONDOR 現在也已經放進 agent router，不只是 standalone wrapper。

概念問題不會執行工具：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "tell me the purpose of CONDOR"
```

真正執行 CONDOR 需要明確給 network file 和 output directory。Dry-run：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "試跑 CONDOR，network 是 data/condor-toy/bipartite.tsv，輸出資料夾 outputs/demo/agent-condor，prefix toy"
```

真的執行：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --execute \
  --task "試跑 CONDOR，network 是 data/condor-toy/bipartite.tsv，輸出資料夾 outputs/demo/agent-condor，prefix toy"
```

預期 agent 會選到：

```text
run_condor
```

並執行等價於：

```bash
run-condor \
  -i data/condor-toy/bipartite.tsv \
  -o outputs/demo/agent-condor \
  --prefix toy
```

檢查輸出：

```bash
find outputs/demo/agent-condor -maxdepth 1 -type f -print
sed -n '1,80p' outputs/demo/agent-condor/toy-summary.txt
```

### Demo 8：LIONESS Co-expression Smoke Test

確認這次修改沒有破壞既有 LIONESS wrapper：

```bash
docker compose run --rm netzoo run-lioness coexpression \
  -e data/lioness-toy/expression.tsv \
  -o outputs/lioness-toy/coexpression.tsv \
  -q outputs/lioness-toy/lioness-coexpression.txt
```

預期最後看到：

```text
All done!
```

檢查輸出：

```bash
ls -lh outputs/lioness-toy/coexpression.tsv outputs/lioness-toy/lioness-coexpression.txt
sed -n '1,5p' outputs/lioness-toy/lioness-coexpression.txt
```

### Demo 9：透過 Agent Dry-run LIONESS-PANDA

不真的執行，只看 agent 會選什麼 command：

```bash
python scripts/netzoo_agent.py \
  --task "我要試跑 LIONESS PANDA。expression 是 data/lioness-toy/expression.tsv，motif 是 data/lioness-toy/motif-panda.tsv，PPI 是 data/lioness-toy/ppi.tsv，aggregate 輸出 outputs/demo/agent-panda.tsv，LIONESS 輸出 outputs/demo/agent-lioness-panda.tsv"
```

如果要真的執行，要加 `--execute`，而且通常建議在 Docker 裡跑：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --execute \
  --task "我要試跑 LIONESS PANDA。expression 是 data/lioness-toy/expression.tsv，motif 是 data/lioness-toy/motif-panda.tsv，PPI 是 data/lioness-toy/ppi.tsv，aggregate 輸出 outputs/demo/agent-panda.tsv，LIONESS 輸出 outputs/demo/agent-lioness-panda.tsv"
```

如果沒有設定 `OPENROUTER_API_KEY`，上面 agent 指令會因為缺 LLM API key 而不能跑。這不是本地 wrapper 的問題；本地 wrapper 可直接用 `run-lioness` demo 驗證。

## 完成狀態

本次已完成：

- [x] Annotation rows 自動跳過。
- [x] CSV/TSV 分流讀取。
- [x] 輸出 PANDA/PUMA compatible TSV。
- [x] LIONESS expression input 自動檢查與 derived headerless TSV 準備。
- [x] 缺 motif/PPI/miRNA 時不亂補，會要求使用者提供。
- [x] CONDOR toy trial wrapper。
- [x] CONDOR Docker 實跑成功。
- [x] 單元測試通過。

## 一句話總結

這次的核心是把「使用者丟進來的表格」整理成 Network Zoo 工具能穩定吃的格式：前面 annotation 先拿掉，CSV/TSV 正確讀取，expression 統一輸出成 TSV；LIONESS 需要 headerless input 時自動補一份 derived file；CONDOR 則用 bipartite edge list 完成 toy trial。

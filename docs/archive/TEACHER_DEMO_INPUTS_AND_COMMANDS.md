# Historical Snapshot: Teacher Demo Inputs And Commands

這份是給老師 demo 用的最短可跑版，只包含本次要展示的四件事：

1. 去除前幾行 annotation。
2. 判斷 CSV / TSV，用 pandas 讀取並輸出成 PANDA/PUMA compatible format。
3. 試跑 CONDOR。
4. 讓 agent 檢查 LIONESS input；缺 input 時列候選讓使用者選，並在執行前要求授權。

所有指令都從專案根目錄執行：

```bash
cd "/Users/chenzhonghan/Documents/LLM AGENT/network-zoo-panda-puma"
```

---

## Demo 1：CSV 有 Annotation，轉成 PANDA/PUMA Format

先看 input：

```bash
sed -n '1,10p' data/teacher-demo/annotated-expression.csv
```

你會看到前面有 annotation：

```text
# exported by upstream expression tool
Annotation: teacher demo CSV input
metadata: rows are genes, columns are samples
gene,s1,s2,s3,s4
...
```

執行轉換：

```bash
docker compose run --rm netzoo python -c '
import sys
sys.path.insert(0, "scripts")
import netzoo_agent as agent
agent.EXECUTE_TOOLS = True
print(agent.format_expression_for_netzoo.invoke({
    "expression_file": "data/teacher-demo/annotated-expression.csv",
    "output_file": "outputs/teacher-demo/csv-expression.panda.tsv",
    "genes_axis": "auto",
    "with_header": False,
}))
'
```

查看輸出：

```bash
sed -n '1,10p' outputs/teacher-demo/csv-expression.panda.tsv
```

預期看到 header 被移除、annotation 被跳過、CSV 被轉成 TSV：

```text
GeneA	1.2	1.5	0.9	1.1
GeneB	4.1	3.8	4.4	4.0
GeneC	0.2	0.3	0.1	0.4
```

Demo 時可以講：

> Agent 的 table reader 會先判斷這是 CSV，跳過前面的 comment / annotation / metadata rows，再用 pandas 讀入並輸出成 PANDA/PUMA 較穩定的 gene-row、sample-column、headerless TSV。

---

## Demo 2：TSV 有 Annotation，轉成 PANDA/PUMA Format

先看 input：

```bash
sed -n '1,10p' data/teacher-demo/annotated-expression.tsv
```

執行轉換：

```bash
docker compose run --rm netzoo python -c '
import sys
sys.path.insert(0, "scripts")
import netzoo_agent as agent
agent.EXECUTE_TOOLS = True
print(agent.format_expression_for_netzoo.invoke({
    "expression_file": "data/teacher-demo/annotated-expression.tsv",
    "output_file": "outputs/teacher-demo/tsv-expression.panda.tsv",
    "genes_axis": "auto",
    "with_header": False,
}))
'
```

查看輸出：

```bash
sed -n '1,10p' outputs/teacher-demo/tsv-expression.panda.tsv
```

預期看到：

```text
GeneA	2	3	4	5
GeneB	8	6	5	3
GeneC	1	1.5	2	2.5
```

Demo 時可以講：

> 這次副檔名是 `.tsv`，所以 reader 走 tab-separated 讀取流程；但 annotation skipping 和 output format 邏輯跟 CSV 共用。

---

## Demo 3：試跑 CONDOR

先看 input：

```bash
sed -n '1,15p' data/teacher-demo/condor-bipartite.tsv
```

這是一個 bipartite edge list：

```text
source	target	weight
TF1	GeneA	1.0
TF1	GeneB	0.8
...
```

執行 CONDOR：

```bash
docker compose run --rm netzoo run-condor \
  -i data/teacher-demo/condor-bipartite.tsv \
  -o outputs/teacher-demo/condor \
  --prefix teacher
```

查看輸出檔：

```bash
ls -lh outputs/teacher-demo/condor
```

查看 summary：

```bash
sed -n '1,50p' outputs/teacher-demo/condor/teacher-summary.txt
```

查看 regulator/source 端 membership：

```bash
sed -n '1,20p' outputs/teacher-demo/condor/teacher-reg_memb.tsv
```

查看 target/gene 端 membership：

```bash
sed -n '1,20p' outputs/teacher-demo/condor/teacher-tar_memb.tsv
```

Demo 時可以講：

> CONDOR 不推 regulatory network，它吃的是已經存在的 bipartite network，然後把 source nodes 和 target nodes 分到 communities/modules。

---

## Demo 4：LIONESS 缺 Input 時，Agent 列候選讓使用者選

這個 demo 故意只給 expression：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "我要跑 LIONESS PANDA。expression 是 data/lioness-toy/expression.tsv。"
```

現在 agent 不會直接猜檔案。它會先列出候選，例如：

```text
- 搜尋 motif/prior 候選：
- 找到多個 motif/prior 候選，agent 不會自動選：
  1. data/lioness-toy/motif-panda.tsv
  2. data/lioness-toy/prior-puma.tsv
  ...

請選擇要使用的 motif/prior 編號，或直接 Enter 取消：
```

你可以依序選：

```text
motif/prior 選 1
PPI 選 1
```

之後 agent 會推定 output path、檢查 input 格式與 ID overlap，然後問是否授權執行。

如果你只是要展示 dry-run 安全機制，可以在最後授權時按 Enter，不執行。

如果你要讓它真的跑，可以在授權問題輸入：

```text
y
```

---

## Demo 5：LIONESS 明確指定 Input，直接檢查並等待授權

如果你不想在 demo 時手動選候選，可以直接指定完整 input：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "我要跑 LIONESS PANDA。expression 是 data/lioness-toy/expression.tsv，motif 是 data/lioness-toy/motif-panda.tsv，PPI 是 data/lioness-toy/ppi.tsv。"
```

預期行為：

1. 不再列候選清單。
2. 自動推定：

```text
outputs/demo/panda-aggregate.tsv
outputs/demo/lioness-panda.tsv
```

3. 顯示 input inspection。
4. 顯示預計執行的 command。
5. 詢問使用者是否授權執行。

如果想跳過互動、直接視為已授權執行：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --execute \
  --task "我要跑 LIONESS PANDA。expression 是 data/lioness-toy/expression.tsv，motif 是 data/lioness-toy/motif-panda.tsv，PPI 是 data/lioness-toy/ppi.tsv。"
```

執行後查看 LIONESS output：

```bash
sed -n '1,10p' outputs/demo/lioness-panda.tsv
```

預期欄位會像：

```text
tf	gene	1	2	3	4
TF1	GeneA	...
```

其中 `1 2 3 4` 是 sample index，後面的數值是每個 sample-specific network 裡該 edge 的分數。

---

## Demo 6：PANDA / PUMA 也有同樣的候選保護

PANDA 只給 expression：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "我要跑 PANDA。expression 是 data/lioness-toy/expression.tsv。"
```

預期：

- 列出 motif/prior 候選。
- 列出 PPI 候選。
- 多候選時不自動選。
- 使用者選完後才檢查與詢問授權。

PUMA 只給 expression：

```bash
docker compose run --rm netzoo python scripts/netzoo_agent.py \
  --task "我要跑 PUMA。expression 是 data/lioness-toy/expression.tsv。"
```

預期：

- 列出 prior 候選。
- 列出 PPI 候選。
- 列出 miRNA list 候選。
- 檢查 miRNA list 裡的 ID 是否出現在 prior 第一欄。
- 通過 validation 後才會問授權。

---

## 最推薦的老師 Demo 順序

1. 跑 Demo 1，展示 CSV annotation 被跳過並轉成 TSV。
2. 跑 Demo 2，展示 TSV annotation 也能處理。
3. 跑 Demo 3，展示 CONDOR 產生 community membership。
4. 跑 Demo 4，展示 LIONESS 缺 input 時不亂猜，會列候選給使用者選。
5. 跑 Demo 5，展示完整 LIONESS input 可以檢查、授權、執行。

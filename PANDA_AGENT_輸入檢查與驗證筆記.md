# PANDA Agent 輸入檢查與驗證筆記

## 1. 這個任務要完成什麼？

這個 PANDA/PUMA Agent 不只是讓 LLM 回答問題，而是要讓它能安全地處理使用者在執行時提供的實際檔案路徑。

目前完成的功能包括：

1. 解析使用者提供的絕對路徑、相對路徑與 `~` 路徑。
2. 檢查檔案是否存在、是否可讀、是否為一般檔案。
3. 檢查 PANDA expression、motif、PPI 的表格格式。
4. 將 gene-by-sample expression 轉成 gene-by-gene co-expression matrix。
5. 辨識 BED-like 檔案不能直接作為目前 PANDA 的 motif input。
6. 檢查 expression、motif、PPI 之間的 Gene ID 與 TF ID 是否一致。
7. 在輸入不相容時阻止 PANDA 執行。
8. 提供具名自動測試與可自行執行的終端機測試。

主要程式：

- `scripts/netzoo_agent.py`
- `tests/test_agent_gate.py`

---

## 2. LLM、Capability Gate 與工具的分工

整體流程：

```text
使用者輸入自然語言
        ↓
OpenRouter 上的 LLM 理解需求
        ↓
產生固定格式的 TaskDecision
        ↓
Capability Gate 再檢查一次
        ↓
允許工具執行，或強制改成 no_tool
        ↓
Python 工具讀取檔案、檢查格式或執行轉換
```

### 2.1 OpenRouter 是什麼？

OpenRouter 是模型 API 的入口。真正理解使用者句子的是所選擇的 GPT 或其他 LLM。

LLM 根據 routing prompt 判斷使用哪個 action，例如：

```text
inspect_inputs
convert_expression
run_panda
run_puma
query_context7
no_tool
```

### 2.2 LLM 負責什麼？

LLM 負責語意理解，例如判斷：

- 使用者想檢查 PANDA 輸入。
- 使用者想執行 PANDA。
- 使用者想把 expression 轉成 co-expression。
- 使用者要求的是不支援的突變偵測。

### 2.3 Python Capability Gate 負責什麼？

Capability Gate 是確定性的程式規則，負責最後把關：

- 是否缺少必要路徑。
- 信心是否低於門檻。
- 是否為不支援的任務。
- 使用者是否明確要求執行 PANDA、PUMA 或 co-expression 轉換。

因此：

```text
LLM 負責理解
Python Gate 負責授權
Python Tool 負責真正讀檔與計算
```

即使 LLM 選錯工具，Capability Gate 仍可阻止不合理的執行。

---

## 3. PANDA 的三份主要輸入

### 3.1 Expression matrix

```text
gene    S1    S2    S3
GeneA   1     2     3
GeneB   2     4     6
GeneC   3     2     1
```

- 每一列是一個基因。
- 第一欄是 Gene ID。
- 其他欄位是不同樣本。
- 數值是基因表現量。

### 3.2 Motif prior edge list

```text
TF1    GeneA    1
TF2    GeneB    0.8
TF1    GeneC    0.5
```

- 第一欄：TF ID。
- 第二欄：target Gene ID。
- 第三欄：關係權重。

第一列可以讀成：

> TF1 可能調控 GeneA，先驗權重為 1。

### 3.3 PPI edge list

```text
TF1    TF2    1
TF2    TF2    1
```

- 第一欄：第一個 TF ID。
- 第二欄：第二個 TF ID。
- 第三欄：interaction weight。

PANDA 會整合：

```text
PPI：TF ↔ TF
Motif：TF → Gene
Expression 所建立的 co-expression：Gene ↔ Gene
```

---

## 4. 路徑解析與可讀性檢查

`_resolve_user_path()` 支援：

- 絕對路徑：`/Users/name/data/expression.tsv`
- 相對路徑：`data/runtime/expression.tsv`
- `~` 路徑：`~/Downloads/expression.tsv`
- 從目前工作目錄或專案根目錄尋找

`_read_checked_table()` 會依序檢查：

1. 路徑是否為空。
2. 檔案是否存在。
3. 路徑是否指向一般檔案，而不是資料夾。
4. Python 是否能以 UTF-8 開啟。
5. 是否看起來以 Tab 分隔。
6. pandas 是否能解析。
7. 表格是否為空。

看到報告中的完整絕對路徑，例如：

```text
/Users/name/project/data/manual-tests/expression.tsv
```

代表程式確實解析並開啟了該路徑，不是把使用者輸入替換成寫死的 toy data。

### Docker 路徑注意事項

`docker-compose.yml` 將專案目錄掛載到 container 的 `/work`：

```text
.:/work
```

因此透過 Docker 執行時，最好將資料放在專案內，例如：

```text
data/runtime/
data/manual-tests/
```

專案外的 macOS 路徑不一定能被 container 看見，除非額外掛載。

---

## 5. Expression 與 Co-expression 的差別

### 5.1 Expression

```text
gene    S1    S2    S3
GeneA   1     2     3
GeneB   2     4     6
GeneC   3     2     1
```

Expression 的欄是樣本，因此大小為：

```text
基因數 × 樣本數
```

### 5.2 Co-expression

```text
gene    GeneA    GeneB    GeneC
GeneA   1        1       -1
GeneB   1        1       -1
GeneC  -1       -1        1
```

Co-expression 的列與欄都是基因，因此大小為：

```text
基因數 × 基因數
```

最容易辨認的差異：

```text
Expression 欄名：S1、S2、S3
Co-expression 欄名：GeneA、GeneB、GeneC
```

### 5.3 為什麼要轉換？

Expression 描述：

> 某個基因在某個樣本的表現量。

Co-expression 描述：

> 兩個基因跨越所有樣本時，表現趨勢是否相似。

目前轉換使用 Pearson correlation：

- `1`：完全正相關。
- `-1`：完全負相關。
- `0`：沒有線性相關。

測試資料中：

```text
GeneA = [1, 2, 3]
GeneB = [2, 4, 6]
GeneC = [3, 2, 1]
```

所以：

- GeneA 與 GeneB 同方向，correlation 為 `1`。
- GeneA 與 GeneC 完全反方向，correlation 為 `-1`。
- 每個基因與自己比較，對角線為 `1`。

真實資料通常會得到 `0.73`、`-0.41`、`0.08` 等數值，不會只有 `1` 與 `-1`。

### 5.4 何時會轉換？

目前使用者必須明確要求：

```text
把 expression.tsv 轉成 co-expression matrix，
輸出到 coexpression.tsv。
```

這是因為轉換會：

- 產生新檔案。
- 改變資料的意義。
- 對大量基因產生很大的方形矩陣。

若使用者只是要求執行 PANDA，應直接提供原始 gene-by-sample expression。netZooPy PANDA 會在內部建立 correlation，不需要先把轉出的 co-expression TSV 當成 `run-panda` 的 expression input。

### 5.5 轉換前的檢查

轉換工具會拒絕：

- 檔案不存在。
- 不是 expression matrix。
- expression value 不是數字。
- Gene ID 重複。
- 少於兩個樣本。
- 基因完全沒有變異，導致 correlation 無法計算。
- 輸入本身已經是 co-expression。
- 輸入與輸出路徑相同。

只有開啟 `EXECUTE_TOOLS` 或 CLI 的 `--execute` 時才會寫出檔案。

### 5.6 轉換成功訊息

```text
Expression to co-expression conversion:
- input: .../expression.tsv
- output: .../coexpression.tsv
- genes: 3
- samples: 3
- method: Pearson correlation across samples
- result: wrote 3 x 3 co-expression matrix
- status: success
```

解讀：

- 成功讀取指定 input。
- 找到 3 個基因與 3 個樣本。
- 使用 Pearson correlation。
- 成功寫出 `3 × 3` co-expression matrix。

`success` 代表格式、計算與寫檔成功，不代表生物學結論一定正確。

---

## 6. BED 是什麼？

BED 是描述基因組座標的格式。

```text
chr1    10    20    TF1
chr2    30    40    TF2
```

常見欄位：

| 欄位 | 意義 |
|---|---|
| `chr1` | 染色體 |
| `10` | 起始位置 |
| `20` | 結束位置 |
| `TF1` | 選填的區域名稱 |

可以把 BED 想成：

> 這個區域位於哪條染色體、從哪裡開始、到哪裡結束。

最簡單的記法：

```text
BED 回答「在哪裡？」
PANDA motif 回答「誰調控誰？」
```

### 6.1 為什麼 BED 不能直接當 PANDA motif？

BED：

```text
chr1    10    20    TF1
```

只描述一段基因組位置。

PANDA motif：

```text
TF1    GeneA    1
```

描述 TF1 可能調控 GeneA。

若要把 BED 轉成 motif prior，還需要 gene annotation，才能判斷某段座標落在哪個基因或 promoter。Agent 不能憑空猜測 target gene。

### 6.2 目前 BED 測試真正證明什麼？

目前測試是故意把 `motif.bed` 放入 PANDA 的 motif 位置。

Agent 會回報：

```text
format: BED-like intervals
error: PANDA run-panda expects a TF-gene-weight edge list
```

這不是說 BED 本身一定寫錯，而是：

> 這份檔案可能是有效的 BED，但不相容於目前 PANDA motif 參數。

因此這項測試應稱為：

```text
PANDA 輸入相容性檢查：辨識並阻擋 BED motif
```

而不是宣稱已完成所有 BED 欄位與語意驗證。

---

## 7. PANDA ID 檢查

### 7.1 ID 是什麼？

ID 是用來代表基因或 TF 的名稱／編號，不一定是數字。

常見例子：

```text
TP53                 Gene Symbol
7157                 Entrez Gene ID
ENSG00000141510      Ensembl Gene ID
ENSG00000141510.18   帶版本的 Ensembl Gene ID
```

ID 可以想成學號：

> 同一位學生在不同表格中必須使用相同學號，電腦才知道是同一個人。

### 7.2 PANDA 檢查哪兩種連接？

第一種：

```text
Motif 第二欄 target Gene ID
              ↓
Expression 第一欄 Gene ID
```

第二種：

```text
Motif 第一欄 TF ID
              ↓
PPI 第一、二欄 TF ID
```

目的是確認：

```text
PPI TF ──相同 TF ID── Motif TF
Motif Gene ──相同 Gene ID── Expression Gene
```

若名稱完全不相同，PANDA 就無法把三份證據連起來。

### 7.3 Overlap 是什麼？

Overlap 是兩組 ID 的集合交集。

```python
expression_genes = {"GeneA", "GeneB", "GeneC"}
motif_targets = {"GeneA", "GeneB", "GeneC"}

overlap = motif_targets & expression_genes
```

結果：

```python
{"GeneA", "GeneB", "GeneC"}
```

因此：

```text
3/3 (100.0%)
```

分母是 motif 中不重複的 target ID 數量，不是表格總列數。

TF 也使用相同方法：

```python
motif_tfs & ppi_tfs
```

### 7.4 全部匹配

```text
motif target genes overlapping expression genes: 3/3 (100.0%)
status: all motif target gene IDs match expression gene IDs.

motif TFs overlapping PPI TFs: 2/2 (100.0%)
status: all motif TF IDs match PPI TF IDs.
```

表示：

- Motif 的 3 個 target genes 都能在 expression 找到。
- Motif 的 2 個 TF 都能在 PPI 找到。
- ID gate 通過。

### 7.5 部分匹配

```text
motif target genes overlapping expression genes: 1/2 (50.0%)
warning: unmatched motif target gene IDs: 1
(examples: MissingGene)
```

表示：

- Motif 有 2 個不重複 target genes。
- 只有 1 個能在 expression 找到。
- `MissingGene` 找不到對應。

目前部分匹配是 warning，通常仍為：

```text
ok = True
```

應在真正分析前確認未匹配原因。

### 7.6 完全沒有匹配

```text
motif target genes overlapping expression genes: 0/2 (0.0%)
error: no exact ID overlap between motif target gene and expression gene IDs.
```

或：

```text
motif TFs overlapping PPI TFs: 0/2 (0.0%)
error: no exact ID overlap between motif TF and PPI TF IDs.
```

此時：

```text
ok = False
```

`run_panda` 會停止，不會執行命令。

### 7.7 常見 ID 不一致原因

- 一邊使用 Gene Symbol，另一邊使用 Ensembl ID。
- 大小寫不同，例如 `GeneA` 與 `genea`。
- Ensembl 版本尾碼不同，例如 `ENSG001` 與 `ENSG001.1`。
- 拼字錯誤。
- Expression 前處理時過濾掉部分基因。
- 資料來自不同物種。

程式會提示大小寫與數字版本尾碼問題，但不會自動把不同 ID 當成相同基因。真正的 ID mapping 需要外部 annotation database。

### 7.8 BED ID 與 PANDA ID 不同

BED 第四欄 `name` 有時可以放 ID，但不一定是 Gene ID，也可能是：

- Peak ID
- Motif ID
- TF 名稱
- 任意區域名稱

因此「BED ID」不是固定標準。

目前完成的是：

- 辨識 BED-like 檔案與 PANDA motif 不相容。
- 檢查 PANDA expression、motif、PPI 的 Gene/TF ID overlap。

尚未完成的是：

- 判斷 BED 第四欄究竟代表 gene、TF、motif 或 peak。
- 使用 gene annotation 將 BED 座標轉成 motif prior。

---

## 8. 建立本機測試資料

進入專案：

```bash
cd "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent"
```

建立資料夾：

```bash
mkdir -p data/manual-tests outputs/manual-tests
```

建立 expression：

```bash
printf 'gene\tS1\tS2\tS3\nGeneA\t1\t2\t3\nGeneB\t2\t4\t6\nGeneC\t3\t2\t1\n' \
  > data/manual-tests/expression.tsv
```

建立 motif：

```bash
printf 'TF1\tGeneA\t1\nTF2\tGeneB\t0.8\nTF1\tGeneC\t0.5\n' \
  > data/manual-tests/motif.tsv
```

建立 PPI：

```bash
printf 'TF1\tTF2\t1\nTF2\tTF2\t1\n' \
  > data/manual-tests/ppi.tsv
```

查看內容：

```bash
head data/manual-tests/expression.tsv
head data/manual-tests/motif.tsv
head data/manual-tests/ppi.tsv
```

使用 `printf` 與 `\t` 可以確保檔案以真正的 Tab 分隔。

---

## 9. 可重複使用的 PANDA ID 檢查指令

在終端機中定義：

```bash
check_panda_ids() {
  python - "$1" "$2" "$3" <<'PY'
import sys
sys.path.insert(0, "scripts")
import netzoo_agent as agent

report, ok, with_header = agent._inspect_panda_inputs_impl(
    sys.argv[1],
    sys.argv[2],
    sys.argv[3],
)

print("ok =", ok)
print("with_header =", with_header)
print(report)
PY
}
```

### 9.1 Shell 參數

執行：

```bash
check_panda_ids expression.tsv motif.tsv ppi.tsv
```

Shell 中：

```text
$1 = expression.tsv
$2 = motif.tsv
$3 = ppi.tsv
```

引號 `"$1"` 可以保護包含空格的路徑。

### 9.2 `python -`

`python -` 表示 Python 程式從標準輸入讀取，而不是從 `.py` 檔案讀取。

```bash
<<'PY'
...
PY
```

稱為 heredoc，會把中間內容交給 Python。

### 9.3 Python 參數

Shell 實際執行的形式近似：

```bash
python - expression.tsv motif.tsv ppi.tsv
```

Python 中：

```text
sys.argv[0] = "-"
sys.argv[1] = expression.tsv
sys.argv[2] = motif.tsv
sys.argv[3] = ppi.tsv
```

### 9.4 Import

```python
sys.path.insert(0, "scripts")
import netzoo_agent as agent
```

表示讓 Python 能載入：

```text
scripts/netzoo_agent.py
```

### 9.5 回傳值

```python
report, ok, with_header
```

- `report`：完整檢查報告。
- `ok`：整體是否通過。
- `with_header`：expression 是否偵測到 header。

Shell 函式只存在於目前終端機工作階段，關閉終端機後需重新定義。

---

## 10. 手動驗證步驟

### 10.1 正確資料

```bash
check_panda_ids \
  data/manual-tests/expression.tsv \
  data/manual-tests/motif.tsv \
  data/manual-tests/ppi.tsv
```

預期：

```text
ok = True
motif target genes overlapping expression genes: 3/3 (100.0%)
motif TFs overlapping PPI TFs: 2/2 (100.0%)
```

證明：

- 三條路徑可以讀取。
- 三份格式相容。
- Gene ID 與 TF ID 全部匹配。

### 10.2 不存在的路徑

```bash
check_panda_ids \
  data/manual-tests/not-exist.tsv \
  data/manual-tests/motif.tsv \
  data/manual-tests/ppi.tsv
```

預期：

```text
ok = False
expression file does not exist
```

證明程式真的檢查檔案系統，而不是只接收路徑字串。

### 10.3 部分 Gene ID 不一致

```bash
printf 'TF1\tGeneA\t1\nTF2\tMissingGene\t1\n' \
  > data/manual-tests/motif-partial-id.tsv
```

```bash
check_panda_ids \
  data/manual-tests/expression.tsv \
  data/manual-tests/motif-partial-id.tsv \
  data/manual-tests/ppi.tsv
```

預期：

```text
ok = True
motif target genes overlapping expression genes: 1/2 (50.0%)
warning: unmatched motif target gene IDs: 1
(examples: MissingGene)
```

### 10.4 Gene ID 完全不一致

```bash
printf 'TF1\tOtherGene1\t1\nTF2\tOtherGene2\t1\n' \
  > data/manual-tests/motif-no-gene-overlap.tsv
```

```bash
check_panda_ids \
  data/manual-tests/expression.tsv \
  data/manual-tests/motif-no-gene-overlap.tsv \
  data/manual-tests/ppi.tsv
```

預期：

```text
ok = False
motif target genes overlapping expression genes: 0/2 (0.0%)
error: no exact ID overlap
```

### 10.5 TF ID 完全不一致

```bash
printf 'TF_X\tGeneA\t1\nTF_Y\tGeneB\t1\n' \
  > data/manual-tests/motif-no-tf-overlap.tsv
```

```bash
check_panda_ids \
  data/manual-tests/expression.tsv \
  data/manual-tests/motif-no-tf-overlap.tsv \
  data/manual-tests/ppi.tsv
```

預期：

```text
ok = False
motif target genes overlapping expression genes: 2/2 (100.0%)
motif TFs overlapping PPI TFs: 0/2 (0.0%)
```

### 10.6 BED-like motif

```bash
printf 'chr1\t10\t20\tTF1\nchr2\t30\t40\tTF2\n' \
  > data/manual-tests/motif.bed
```

```bash
check_panda_ids \
  data/manual-tests/expression.tsv \
  data/manual-tests/motif.bed \
  data/manual-tests/ppi.tsv
```

預期：

```text
ok = False
format: BED-like intervals
error: must be converted to a motif/prior edge list
```

證明 Agent 能辨識 BED-like 座標檔不相容於 PANDA motif 參數。

---

## 11. Expression 轉 Co-expression 測試

執行：

```bash
python - <<'PY'
import sys
sys.path.insert(0, "scripts")
import netzoo_agent as agent

agent.EXECUTE_TOOLS = True

result = agent.convert_expression_to_coexpression.invoke({
    "expression_file": "data/manual-tests/expression.tsv",
    "output_file": "outputs/manual-tests/coexpression.tsv",
})

print(result)
PY
```

查看輸出：

```bash
cat outputs/manual-tests/coexpression.tsv
```

驗證矩陣：

```bash
python - <<'PY'
import pandas as pd

matrix = pd.read_csv(
    "outputs/manual-tests/coexpression.tsv",
    sep="\t",
    index_col=0,
)

print("shape =", matrix.shape)
print("row IDs =", list(matrix.index))
print("column IDs =", list(matrix.columns))
print("symmetric =", matrix.equals(matrix.T))
print(matrix)
PY
```

預期：

```text
shape = (3, 3)
symmetric = True
```

正確的 co-expression matrix 應該：

- 是 gene × gene 方形矩陣。
- 列與欄使用相同 Gene ID。
- 是對稱矩陣。
- 對角線通常為 1。

---

## 12. 證明不相容輸入會阻止 PANDA

使用完全不匹配的 Gene ID：

```bash
python - <<'PY'
import sys
sys.path.insert(0, "scripts")
import netzoo_agent as agent

result = agent.run_panda.invoke({
    "expression_file": "data/manual-tests/expression.tsv",
    "motif_file": "data/manual-tests/motif-no-gene-overlap.tsv",
    "ppi_file": "data/manual-tests/ppi.tsv",
    "output_file": "outputs/should-not-exist.tsv",
})

print(result)
PY
```

預期：

```text
PANDA input validation failed; no command was executed.
```

這證明 ID gate 不只是顯示訊息，而是真的阻止工具執行。

---

## 13. 自動測試

只跑 PANDA 輸入檢查：

```bash
python tests/test_agent_gate.py -v PandaInputInspectionTests
```

只跑 expression 轉換：

```bash
python tests/test_agent_gate.py -v ExpressionConversionTests
```

跑全部測試：

```bash
python tests/test_agent_gate.py -v
```

目前結果：

```text
Ran 22 tests
OK
```

`-v` 會顯示每個測試名稱，比只顯示測試數量更適合截圖與報告。

重要測試包括：

- 正確 runtime PANDA 輸入。
- 缺少檔案。
- BED-like motif。
- 方形 co-expression 被誤放入 expression。
- 完整 ID overlap。
- 部分 ID overlap。
- Gene ID 零 overlap。
- TF ID 零 overlap。
- Expression 成功轉 co-expression。
- Dry-run 不寫檔。
- 零變異基因被拒絕。

---

## 14. 完整 LLM Agent 測試

前面的 Python 指令直接測試確定性的工具層。若要連同 OpenRouter LLM routing 一起測試：

### 14.1 檢查 PANDA 輸入

```bash
docker compose run --rm netzoo \
  python scripts/netzoo_agent.py \
  --task "請檢查 PANDA 輸入檔案：expression 是 data/manual-tests/expression.tsv，motif 是 data/manual-tests/motif.tsv，PPI 是 data/manual-tests/ppi.tsv"
```

### 14.2 執行 co-expression 轉換

```bash
docker compose run --rm netzoo \
  python scripts/netzoo_agent.py --execute \
  --task "把 data/manual-tests/expression.tsv 轉成 co-expression matrix，輸出到 outputs/manual-tests/coexpression-agent.tsv"
```

這一層驗證：

```text
自然語言
→ LLM action routing
→ Capability Gate
→ Python 檔案工具
```

直接呼叫 `_inspect_panda_inputs_impl()` 則只驗證 Python 工具層，不包含 LLM routing。

---

## 15. 測試資料是不是自己建立的？

分成三類：

### 15.1 手動合成資料

`data/manual-tests/` 中的小檔案是為了測試而建立。

優點：

- 預先知道正確答案。
- 可以刻意製造 BED、缺少檔案、ID 不匹配等錯誤。
- 容易在投影片解釋。

這類資料稱為 test fixture，不應宣稱是真實研究資料。

### 15.2 單元測試臨時資料

`tests/test_agent_gate.py` 使用 `tempfile.TemporaryDirectory()` 動態建立：

- patient expression
- motif/PPI
- BED
- co-expression
- ID mismatch

測試結束後會自動刪除。

### 15.3 官方 toy data

`data/official-toy/` 內容來自 netZooPy 官方測試資料，不是任意編造，但仍屬於 toy/example。

### 15.4 公開真實資料

可再使用 GEO 等公開 expression matrix，證明功能不只適用於合成資料。

最完整的展示方式：

1. 合成正確資料：應通過。
2. 合成錯誤資料：應出現可預期的 warning/error。
3. 公開實際資料：證明可處理執行時提供的外部路徑。

---

## 16. 投影片講解方式

### 16.1 BED 投影片建議標題

建議使用：

```text
PANDA 輸入相容性檢查：辨識並阻擋 BED motif
```

避免只寫「BED 檔案格式錯誤」，因為 BED 本身可能有效，只是不符合 PANDA motif 的需求。

### 16.2 BED 投影片講稿

> 這張投影片驗證 Agent 的工具層能讀取使用者指定的實際路徑，並在執行 PANDA 前檢查三份輸入。我刻意把一份 BED 放在 motif 位置。Expression 被辨識為 expression matrix，PPI 被辨識為三欄 edge list，但 motif 被辨識為 BED-like intervals。BED 描述的是 chromosome、start、end 等基因組座標，而 PANDA motif 需要 TF、target gene、weight。因此這份 BED 不一定是壞檔案，但不能直接作為 PANDA motif。Agent 回報 `ok = False` 並阻止 PANDA 執行。若要轉換，還需要 gene annotation，不能由 Agent 憑空猜測 target gene。

### 16.3 ID 投影片一句話

> ID overlap 是確認 expression、motif 與 PPI 是否在描述同一批 Gene 和 TF，讓 PANDA 能把三種資料正確連接。

### 16.4 若老師問「這是 LLM 判斷嗎？」

回答：

> LLM 負責理解使用者需求與選擇 action；真正的路徑讀取、格式檢查、ID 集合交集與錯誤阻擋，是由確定性的 Python 程式完成。

---

## 17. 目前能力邊界

已完成：

- 路徑存在性與可讀性檢查。
- TSV 解析與基本格式辨識。
- Expression matrix 檢查。
- Pearson co-expression 轉換。
- BED-like 檔案辨識與 PANDA motif 相容性阻擋。
- Motif target Gene 與 Expression Gene overlap。
- Motif TF 與 PPI TF overlap。
- 大小寫與版本尾碼提示。
- 零 overlap 時阻止 PANDA。

尚未完成：

- 使用 annotation database 自動轉換 Gene ID。
- 自動將 BED 座標轉成 TF-gene motif prior。
- 判斷 BED 第四欄的實際生物語意。
- 完整 BED12 規格驗證。
- 判斷資料在生物學上是否正確。

部分 ID overlap 目前只會 warning，不會阻止執行；零 overlap 才會讓 `ok = False`。

---

## 18. 最後快速記憶

```text
Expression：Gene × Sample
Co-expression：Gene × Gene
Motif：TF → Gene
PPI：TF ↔ TF
BED：基因組座標
ID overlap：確認不同檔案能否連接同一個 Gene/TF
```

```text
LLM：理解需求
Gate：決定是否允許
Validator：讀檔、檢查格式與 ID
Tool：轉換或執行
```

```text
ok = True：格式與必要相容性檢查通過
ok = False：至少一個必要條件失敗，不應執行 PANDA
```

`ok = True` 不代表 PANDA 已執行，也不代表生物學分析結果一定正確。

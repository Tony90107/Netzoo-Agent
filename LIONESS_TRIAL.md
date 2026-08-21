# LIONESS toy 試跑紀錄

日期：2026-07-01

## 輸入格式

- Expression：無 header TSV；gene 在 rows，sample 在 columns。
- PANDA motif：`TF<TAB>Gene<TAB>Weight`。
- PUMA prior：TF-gene 與 miRNA-gene edges 合併在同一個三欄檔。
- PPI：`TF1<TAB>TF2<TAB>Weight`。
- miRNA：無 header，每行一個 ID；每個 ID 都存在於 PUMA prior 第一欄。
- LIONESS 至少三個 samples；toy data 使用四個。

資料位於 [data/lioness-toy](data/lioness-toy)。

## 實跑結果

| 模式 | Aggregate | LIONESS | 結果 |
|---|---:|---:|---|
| Co-expression | 9 rows × 3 columns | 9 rows × 6 columns（2 IDs + 4 samples） | 成功，無 NaN/Inf |
| PANDA | 6 edges × 4 columns | 6 edges × 6 columns（TF/gene + 4 samples） | 成功，無 NaN/Inf |
| PUMA | 9 edges × 4 columns | 10 rows × 7 columns（1 header + 9 edges；3 metadata + 4 samples） | 成功，無 NaN/Inf |

PUMA LIONESS 的 header 會由 wrapper 補成 `regulator gene prior_weight 1 2 3 4`；
七欄為 regulator、gene、prior weight，加上四個 sample-specific scores。

輸出位於 [outputs/lioness-toy](outputs/lioness-toy)。

## 試跑時發現並處理

1. Legacy runner 預設會多寫一份無 edge 標籤的 `lioness_output/lioness.npy`。
   Docker build 改用 netZooPy 既有的 labeled export path，只保留使用者指定檔案；
   Agent 同時檢查可用的 `.txt`、`.csv`、`.tsv` 副檔名。
2. 只有一個 TF 或全為相同值的 PPI toy network 會在 normalization 產生 NaN；
   toy data 改為兩個 TF 與有變異的 PPI，Agent 也會拒絕少於兩個 TF。
3. 目前 netZooPy master 的 `LionessPuma.save_lioness_results` 誤用 `os.path`
   module 取代輸出檔參數。Dockerfile 內含最小相容修補，並透過 `PYTHONPATH`
   確保 runtime 使用同一份 `/opt/netZooPy` source。

## 重跑

```bash
docker compose build

docker compose run --rm netzoo run-lioness coexpression \
  -e data/lioness-toy/expression.tsv \
  -o outputs/lioness-toy/coexpression.tsv \
  -q outputs/lioness-toy/lioness-coexpression.txt

docker compose run --rm netzoo run-lioness panda \
  -e data/lioness-toy/expression.tsv \
  -m data/lioness-toy/motif-panda.tsv \
  -p data/lioness-toy/ppi.tsv \
  -o outputs/lioness-toy/panda.tsv \
  -q outputs/lioness-toy/lioness-panda.txt

docker compose run --rm netzoo run-lioness puma \
  -e data/lioness-toy/expression.tsv \
  -m data/lioness-toy/prior-puma.tsv \
  -p data/lioness-toy/ppi.tsv \
  -i data/lioness-toy/mirna.txt \
  -o outputs/lioness-toy/puma.tsv \
  -q outputs/lioness-toy/lioness-puma.tsv
```

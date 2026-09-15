# 盲測 prompt（人看的，不要給 agent）

測資在 `data/blind-tests/`。prompt 本身完全不提測試重點，agent 只會看到一句正常的使用者請求。

**每位測試者一份快取。** 基因快取預設是 `<專案>/.netzoo/gene_validation.sqlite3`，
同一個 checkout 或容器裡的所有人共用。不隔離的話，別人查過的結果會直接回答你的查詢，
盲測就不是盲測了。每一輪盲測都換一個新檔：

```bash
export NETZOO_GENE_CACHE_PATH="/tmp/netzoo-blind-$(date +%s).sqlite3"
```

線上查詢預設就會啟用（NCBI 和 Ensembl 不需要金鑰）。如果會連續跑很多題，
建議申請一個免費的 NCBI key 把速率上限從每秒 3 次拉到 10 次：

```bash
export NCBI_API_KEY=...   # 選用，https://account.ncbi.nlm.nih.gov/settings/
```

---

## A. 檔名誤導，使用者沒指定角色

```
--task "跑 PANDA，用 data/blind-tests/case-1/expression.tsv data/blind-tests/case-1/motif.tsv data/blind-tests/case-1/ppi.tsv 這三個檔案，物種是 human"
```

`case-1` 的三個檔名全部是錯的：`ppi.tsv` 裝的是表達矩陣、`expression.tsv` 裝的是 motif、`motif.tsv` 裝的是 PPI。

- 通過：agent 依內容配角色（expression←ppi.tsv、motif←expression.tsv、ppi←motif.tsv），列出 confidence 與理由，停在確認，確認後可執行
- 失敗：照檔名配，然後丟出 `expression values must be numeric`

## B. 檔名誤導，而且使用者照檔名指定角色

```
--task "跑 PANDA，expression 用 data/blind-tests/case-1/expression.tsv，motif 用 data/blind-tests/case-1/motif.tsv，PPI 用 data/blind-tests/case-1/ppi.tsv，物種 human"
```

- 通過：擋下來，並且明講 `the input roles are crossed`，指出正確的對應
- 失敗：只丟結構錯誤，讓人以為是資料壞掉

## C. 不存在的基因

```
--task "跑 PANDA，用 data/blind-tests/case-2/expression.tsv data/blind-tests/case-2/motif.tsv data/blind-tests/case-2/ppi.tsv 這三個檔案，物種是 human"
```

`case-2` 裡 `GATA9` 不存在，其餘 FOXA1、GATA3、RUNX1、ESR1、NFYA 都是真的。

- 通過：只點名 `GATA9`，其他五個放行
- 失敗：全部放行；或把真基因一起判成 invalid（那是誤殺，比放行更糟）

## D. 同一份壞資料，但在 /test 模式

先送 `/test`，再送 C 的同一句話。

- 通過：`GATA9` 降級成 test-only 警告可以往下走，但結構與跨檔檢查照樣擋，且仍要 `/execute` 才會真的跑
- 失敗：test 模式連結構錯誤也一起放行

## E. 沒講物種

```
--task "跑 PANDA，用 data/blind-tests/case-2/expression.tsv data/blind-tests/case-2/motif.tsv data/blind-tests/case-2/ppi.tsv 這三個檔案"
```

- 通過：要求指定物種
- 失敗：說這些基因不存在（把設定問題講成資料問題）

必須用**全新快取**跑。這些基因如果先前已被某個物種查過並存進快取，沒給物種的查詢會沿用那筆結果直接通過。

---

## 其他值得順手測的

- **跨檔不相容**：`data/manual-tests/motif-no-gene-overlap.tsv` 當 motif，應該報沒有共同基因，而不是照跑
- **PUMA 表頭**：PUMA 要求無表頭表達矩陣，丟有表頭的進去應該擋下並叫人先 `format_expression`
- **物種三種寫法**：`human` / `Homo sapiens` / `9606` 對同一份資料應該得到完全一樣的結論

---

## 已知限制（測之前先看）

**路徑之間用半形空白分隔，不要用頓號。** 頓號 `、` 會讓路徑解析壞掉，
實測 `expression_file` 會被切成 `.tsv、data/blind-tests/case-1/motif.tsv`。
上面的 prompt 已經是空白分隔，照抄即可。

**說「跑 PANDA」不保證直接選中 PANDA。** Router 常會先問你要哪一種網路結果
（PANDA / OTTER / GIRAFFE / LIONESS 都相容）。互動模式下回答即可，這是正常行為。

## 一定要把三個檔案路徑寫完整

只講資料夾（例如「用 data/blind-tests/case-1 裡的三個檔案」）目前不會被當成資料來源。
Planner 會改去掃整個 `data/`，挑到別的資料集（實測會挑到 `data/auto-check-valid`），
測的就不是你要測的東西了。確認畫面會把實際選到的檔案列出來，記得核對。

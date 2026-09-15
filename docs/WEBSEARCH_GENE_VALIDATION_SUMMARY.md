# NetZoo agent：基因權威查詢與 12 個 workflow 輸入檢查的工程驗證摘要

日期：2026-09-15
範圍：本輪未提交變更（gene authority、Websearch 路由、輸入 preflight、12 個 workflow 的測試與文件）

> 本文件是可放入論文「方法／系統驗證」章節的工程摘要。文中將「程式實際觀測到的結果」、「設計上的推論」與「尚未能由 Websearch 證明的事項」分開。它不是生物學新發現，也不應把搜尋引擎結果當成權威資料庫的完整替代品。

## 核心結論

本輪修改把基因驗證拆成三個可檢查的層次：

1. 先讀取本地 cache，避免每次重複查詢。
2. cache miss 時優先呼叫結構化的 NCBI Datasets 或 Ensembl REST API，從回傳欄位核對 identifier、canonical ID 與物種。
3. 結構化 API 無法連線時才使用 Websearch；Websearch 只提供 discovery evidence，不單獨授權 workflow，也不單獨證明基因不存在。

因此，檔名看似正確但內容錯誤時，系統仍會在 preflight 以 schema、gene-like label、樣本軸與跨檔案契約攔截；檔名不正確但內容符合契約時，檔名不再被當成唯一判斷依據。十二個已註冊 workflow 共用同一個 fail-closed preflight gate：PANDA、PUMA、LIONESS-PANDA、LIONESS-PUMA、LIONESS-Coexpression、CONDOR、COBRA、SAMBAR、DRAGON、OTTER、GIRAFFE、BONOBO。

最新的 TP53 測試已得到可重現的精確匹配：

```text
authority=NCBI Gene
canonical_id=7157
symbol=TP53
taxon=Homo sapiens
url=https://www.ncbi.nlm.nih.gov/gene/7157
```

對不存在的 `ENSG00000999999`，系統回報 `Websearch 未找到 exact trusted result`，而不是以相似 ID 推測存在。這個「未找到」只代表目前搜尋的 discovery evidence，不等同於權威資料庫的數學式不存在證明。

## 1. 問題與風險

原本的失敗可歸納為四類：

- **召回不足：** 一般 basic Websearch 可能把 `TP53BP1`、`WRAP53` 等相關頁面排在前面，導致真正的 `/gene/7157` 沒有進入可解析結果。
- **相似字串誤判：** 只用 substring 判斷會把 `TP53` 與 `TP53BP1` 視為同一個 gene label。
- **資料完整性破壞：** 直接對 JSON 做 head/tail 截斷可能切斷括號，使下游 parser 無法讀取 URL、title 與 evidence。
- **路由與驗證邊界混淆：** 使用者明確要求唯讀的 `WEB-SEARCH` 時，不能被「科學 workflow outcome 尚未驗證」的 gate 阻擋；反過來，搜尋結果也不能直接繞過 workflow 的輸入 preflight。

## 2. 實作修改

### 2.1 Gene authority validation

- `gene_validation.py` 新增 NCBI Datasets 與 Ensembl REST 的結構化查詢 seam。
- 對 NCBI symbol／GeneID 與 Ensembl gene ID 分別檢查 namespace、canonical identifier、symbol、taxon/species、object type 與 trusted URL。
- cache miss 的線上結果會依證據來源標記；Websearch 結果為 `unverified`，避免 discovery 被誤當成 authoritative validation。
- 批次大小由單一小上限改為可完整處理的批次；Websearch 仍以小批次分割，避免查詢字串過長。
- `NETZOO_GENE_ONLINE_LOOKUP` 支援 `auto/on/off`。預設 `auto`：有 Websearch 設定時才啟用線上路徑；`off` 時維持 cache-only，未查證項目標成 `unverified`，而不是偽造有效或無效。

### 2.2 Websearch 的 authority-scoped retrieval

- 明確的 NCBI/Ensembl gene request 會改寫為來源限定查詢，例如 `site:ncbi.nlm.nih.gov/gene` 與 `site:ensembl.org`。
- 來源限定的 gene query 使用 `advanced` content retrieval；一般 Websearch 仍維持 `basic`，只在需要提高權威頁面召回率時付出額外成本。
- 結果接受條件是「trusted domain + exact identifier/symbol 欄位 + 物種／來源資訊」，不是模糊相似標題。
- 解析器會把 Websearch 結果壓縮成仍然合法的 JSON，保留 URL、title、content、score 等欄位；只有在極端過長時才減少後續結果數量。

### 2.3 Router、preflight 與 workflow 契約

- 明確的 `WEB-SEARCH`／`CONTEXT7` 是唯讀工具能力，直接選擇對應 capability，並不要求先建立科學 outcome hypothesis。
- 明確要求執行或 input preflight 時，router 會以 deterministic command-language reconciliation 將 intent 設為 execute/inspect_inputs。
- 所有十二個 run action 共用 fail-closed preflight；檢查內容包括檔案存在性、schema、gene-like labels、row/column axis、樣本集合與多檔案相容性。
- CONDOR node 與 DRAGON feature 可能是非基因標籤，因此不強制套用 gene authority lookup，但仍必須通過各自的二分圖與雙層資料契約。
- Docker image build 階段加入 MCP adapter/API import smoke test；environment pin `mcp==1.30.0` 與相容的 `httpx==0.27.2`，避免 `langchain-mcp-adapters` 與 MCP API 漂移到 runtime 才失敗。

## 3. 為什麼這樣改：科學與資訊檢索依據

### 3.1 精確匹配是交集條件，不是字串包含

對一個候選 gene record，接受條件可寫成：

\[
M = D_{authority} \land I_{exact} \land T_{taxon} \land S_{supported}
\]

其中：

- (D_{authority})：URL 位於 NCBI Gene 或 Ensembl 的允許網域。
- (I_{exact})：ID 或 symbol 在 identity 欄位中與查詢值精確相等，而非 substring 相似。
- (T_{taxon})：回傳的 taxon/species 與要求的物種相符。
- (S_{supported})：結果包含可追溯的官方 URL 與證據欄位。

這個交集條件直接對應資料庫識別的基本原則：同一個字串可能是多個 gene symbol 的前綴，只有 namespace、物種與 canonical identifier 一起核對，才可降低 false positive。

### 3.2 Basic 與 advanced retrieval 的取捨

資訊檢索同時追求 precision 與 recall。這次觀測到 basic retrieval 對 TP53 回傳了多個相關但不相等的頁面；改用來源限定的 advanced retrieval 後，能取得 NCBI `/gene/7157` 的頁面內容。這表示 advanced retrieval 在此查詢提高了 recall，但不表示它對所有查詢都普遍較好。因此系統只在明確的 authority-scoped gene request 使用 advanced，並用上面的精確匹配條件維持 precision。

### 3.3 結構化輸出完整性

下游報告器需要解析 JSON。若以字元位置直接取 head/tail，JSON 可能變成語法不合法，結果即使包含正確 URL 也無法使用。現在的 adaptive compaction 先解析 JSON，再逐步縮短 content；只在每個候選結果仍能序列化成合法 JSON 後才返回。這是資料管線的 integrity invariant：

\[
\text{parseable(response)} = \text{true}
\]

同時保留第一筆結果的 identity 與 evidence，讓精確匹配判斷不會因輸出上限而消失。

### 3.4 Discovery evidence 與 authoritative absence 必須分開

搜尋引擎的「未找到」受索引範圍、排序、網路狀態與 query formulation 影響，因此只能表示 discovery evidence。只有結構化 NCBI/Ensembl API 回覆「查詢成功且沒有該項目」時，才適合把項目標成 `invalid`。這個區分可避免把暫時性網路或搜尋召回失敗誤報為生物資料庫中的不存在。

## 4. 實際驗證結果

| 測試 | 期待 | 實際結果 | 判定 |
|---|---|---|---|
| `TP53`, `Homo sapiens`, NCBI Gene | 精確匹配 | GeneID `7157`、symbol `TP53`、taxon `Homo sapiens`、官方 URL `/gene/7157` | 通過 |
| `ENSG00000999999`, `Homo sapiens`, NCBI/Ensembl | 不可用相似 ID 推測存在 | `Websearch 未找到 exact trusted result` | 通過 |
| 檔案名稱看似正確、內容為無效 TSV | 必須阻擋 workflow | 12 個 registered action 都有 malformed-content preflight 測試 | 通過 |
| 大型 Websearch JSON | 必須可解析 | adaptive JSON bounding 測試通過，保留多筆結果與 evidence | 通過 |
| 直接唯讀 Websearch request | 不應被 outcome gate 阻擋 | router 直接選擇 `web_search`，不執行 PANDA 等 workflow | 通過 |

## 5. 可重現性與限制

手動測試 prompt 收錄於 [`docs/WEBSEARCH_GENE_TEST_PROMPTS.md`](WEBSEARCH_GENE_TEST_PROMPTS.md)。最新測試證明的是「在當次設定、query 與 Websearch 索引下，系統能找回並精確解析 TP53」，不是 NCBI 全資料庫的完備性證明。

建議在論文中報告以下限制：

1. Websearch 依賴外部索引與網路可用性；沒有網路時應使用 cache 或結構化 API，而不是把空結果解釋成不存在。
2. cache TTL、物種命名與資料庫版本會影響可重現性，正式實驗應記錄查詢日期、API 回應與 canonical IDs。
3. 本輪 targeted tests 與 lint 已通過；完整舊測試集合仍有與本輪功能無關的既有失敗，因此不能宣稱整個 repository 的 full suite 全部綠燈。

## 6. 參考資料

- [NCBI Gene：TP53（GeneID 7157）](https://www.ncbi.nlm.nih.gov/gene/7157)
- [Ensembl：TP53（ENSG00000141510）](https://www.ensembl.org/id/ENSG00000141510)
- [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene)
- [Ensembl REST API documentation](https://rest.ensembl.org/)

## 總結句（可直接放入論文）

本系統以 cache-first、authority-scoped retrieval、結構化 API 核驗、精確 identifier/taxon matching，以及 workflow-shared fail-closed preflight 組成分層驗證流程；此設計同時降低相似 gene label 的 false positive、降低檔案內容錯誤造成的 silent failure，並將 Websearch 的 discovery evidence 與權威資料庫的 authoritative validation 清楚分離。

# Websearch 與 Gene Authority 手動測試 prompts

這組案例用來區分兩條不同路徑：

1. `WEB-SEARCH` 直接查詢會使用 Websearch MCP。
2. PANDA input preflight 的 gene authority 檢查會先查 NCBI/Ensembl；只有結構化 API 無法使用時，才把 Websearch 當 discovery evidence。Websearch 找到的結果會標成 `unverified`，不能單獨授權 workflow 執行。

## 前置條件

請在專案根目錄的 `.env` 設定（不要每次重新 `export`）：

```dotenv
TAVILY_API_KEY=tvly-...
WEBSEARCH_MCP_URL=https://mcp.tavily.com/mcp
NETZOO_GENE_ONLINE_LOOKUP=auto
```

`docker compose` 會自動讀取 `.env`。`NETZOO_GENE_ONLINE_LOOKUP=auto` 只控制 gene authority 的線上查詢；直接要求 `WEB-SEARCH` 時仍需要 Websearch MCP 設定。
若剛更新過 `environment.yml` 或 Websearch 相依套件，先執行 `docker compose build netzoo`；之後不需要每次重新 `export`。
針對 NCBI/Ensembl gene authority 的 Websearch 會使用 advanced content retrieval，以免 TP53 被 TP53BP1、WRAP53 等相似結果擠出前五筆；一般 Websearch 仍使用 basic retrieval。

## 測試 A：應該在 NCBI 找到的 gene
```text
請使用 WEB-SEARCH 搜尋官方 NCBI Gene 資料：TP53，物種為 Homo sapiens。
只接受 ncbi.nlm.nih.gov/gene 的結果，回報精確匹配的 GeneID、symbol、taxon、官方 URL、搜尋結果中的證據摘要。
不要執行 PANDA，也不要把一般網頁或模糊相似結果當成精確匹配。
```

預期：路由到 `WEB-SEARCH`，結果應包含 NCBI Gene 的 TP53（GeneID 7157）。這是 Websearch discovery 測試，不等同於 preflight 的權威授權。

## 測試 B：應該找不到的 gene

```text
請使用 WEB-SEARCH 搜尋官方 NCBI Gene 與 Ensembl：ENSG00000999999，物種為 Homo sapiens。
只回報官方來源是否有精確匹配、查詢到的 URL 與證據摘要；若沒有精確匹配，請明確寫「Websearch 未找到」，不要用相似 ID 推測存在，也不要執行任何 workflow。
```

預期：路由到 `WEB-SEARCH`，通常沒有精確官方匹配。請注意「Websearch 未找到」不是權威的 invalid 判定；只有 NCBI/Ensembl 結構化 API 明確回覆不存在時，gene preflight 才會標成 `invalid` 並阻擋 workflow。

若看到 A 明明完成 Websearch 卻回報 TP53 未找到，先確認 image 已重建；舊版會在 8,000 字元輸出上限用頭尾截斷 JSON，導致 authority parser 無法讀取。修正版會先壓縮 evidence、保留有效 JSON，再產生 `canonical_id=7157`。B 若只顯示 guidance 而沒有 `Web search` step，代表使用的是未套用直接 retrieval 路由修復的 image。

## 若要測試 PANDA preflight 的 fallback

直接的 `WEB-SEARCH` prompt 不會讀取 expression/motif/PPI。要測試 gene authority fallback，必須先提供存在的檔案路徑，並使用含有 `TP53` 或 `ENSG00000999999` 的資料；若三個檔案不存在，preflight 會在檔案存在性階段停止，完全不會進行 gene lookup 或 Websearch。輸出中請檢查每筆 `gene authority record` 的 `status`、`canonical_id`、`authority`、`source`：

- `source=ncbi_datasets` 或 `ensembl_rest`：結構化權威查詢。
- `source=websearch` 且 `status=unverified`：只找到 discovery evidence，不能執行。
- `status=invalid`：結構化權威 API 明確表示找不到或 taxon 不符。

# 第 4a 階段：數量關係限制、`scope` 標記、完整性與一致性測試（2026-10-16）

## 結論

**4a 完成，離線驗證通過**（spec 第 12.2、12.4 節）。

- COBRA 的「基因數須多於樣本數」現在由一個共用函式判斷：輸入檢查器和請求層都呼叫它，規則只寫在一個地方。
- 在錄製資料上，新規則只改變了 C57。四輪都從誤承諾變成正確的 DECLINE，沒有任何「該做」或「該追問」的題目被影響。

## 做了什麼

- `data/cobra.py`：新增 `gene_sample_error(genes, samples)`，`load_cobra_inputs` 改用它。
- `workflow_conditions`：`WorkflowConditions` 加入 `relation_name` 與 `relation`（COBRA：`features>samples`），內容讀自上述函式，模組本身不存數值。
  - `data_issue` 新增 `single_features` 參數：只有在請求說出單一特徵數時才判斷這條關係，絕不把多個資料型別的數量加總。
- `method_conditions`：記錄說出幾個特徵數（`feature_counts`）。兩個呼叫 `data_issue` 的地方都改傳 `_single(method)`。
- YAML `input_checks` 每一條改為 `{text, scope, limit}`。
  - 23 條中 9 條是 `scope: request`，各自指向一條限制：最少樣本 6 條、`max_values` 1 條、`relation:features>samples` 1 條、`setting:kmax<=samples` 1 條。
  - 其餘 14 條是 `scope: file`。
  - 純字串條目仍可載入，讀成 `scope: file`，不升 `policy_version`。
- policy loader 新增檢查：`request` 必須有 `limit`，`file` 不能有，`limit` 名稱必須合法。
- 測試（`tests/test_contract_limits.py`）：
  - **完整性**：9 條 request 條目都對應到確實存在、而且會生效的限制。
  - **一致性**：用合成表格實際跑 COBRA 的輸入檢查器（5×6、6×6、7×6），結果與請求層的判斷一致；7×6 能乾淨載入，所以這個比對不是空的。
  - 另有 loader 測試與 `method_fitting` 測試。
- 全套測試 3,835 個通過。

## 離線驗證（`offline_4a.py`，不呼叫模型）

用錄製的能力檢查列（列中有 `method` 的 samples/features）重新判斷每個可做判定的 workflow，再重算判定：

| 錄製回合 | 被新規則改變的 session | 判定變化 |
|---|---|---|
| p0 | C57 | DO（誤承諾）→ DECLINE（正確） |
| p1 | C57 | 同上 |
| p2 | C57 | 同上 |
| p3 | C57 | 同上 |
| m3 開發集（162 個錄製判定） | 0 | — |

錄製資料沒有 `feature_counts`，重放時把它當成 1 個特徵數。這是比較嚴格的假設（較容易觸發新規則），在這樣的假設下仍然沒有誤拒。

## 下一步

4b（`ruled_out_inputs` 與路線上的必要輸入，對應 C18）需要新的讀取欄位，依 spec 要跑一次 56 題實測。實測前報備。

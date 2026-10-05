# 第 3、4 項：局部修補與單一來源投影

日期：2026-10-05

## 範圍與結論

第 3 項修補了既有 legacy patch 的權限邊界與引用替換缺口。第 4 項沿用專案已有的實驗性 SemanticClaims 路徑，補強確定性投影、來源追蹤、驗證紀錄與新舊格式對照。沒有切換正式預設：legacy 仍是預設，claims 可由 `semantic_contract="claims"` 啟用。

這次驗證的是 harness 的程式性質，不是模型理解正確率或論文泛化成效。

## 第 3 項修了什麼

1. 修改權限由「所有假設的錯誤聯集」改成「本次指定假設的錯誤，加上全域錯誤」。假設 B 的輸入問題不再授權修改假設 A 的輸入。
2. 欄位修補不能改寫頂層研究目標 `semantic_goal` 或請求模式 `request_mode`；後者仍由原本的意圖處理流程負責。
3. 純引用問題只開放指定的 dimension/value。可替換失敗引用，不能順便加入其他欄位的未驗證依據。
4. 仍在 outcome 中的值，不能藉由刪除其失敗引用、卻沒有替代依據來消除錯誤。修補後仍走相同驗證。
5. 日誌區分實際變動欄位、模型要求變動欄位、被擋下的越界修改與證據。其他假設保留。

適用於主修補與 sibling repair。既有 schema 解碼失敗的完整重建、受限的引用補充、必要澄清及科學判定流程仍各自保留；沒有把它們全部當成值衝突，也沒有增加重試次數。

主要程式：

- `scripts/netzoo_agent_core/contracts/repair_scope.py`
- `scripts/netzoo_agent_core/interpretation/semantic_patch.py`
- `scripts/netzoo_agent_core/graph/semantic_attempts.py`
- `scripts/netzoo_agent_core/graph/sibling_repair.py`

## 第 4 項如何運作

模型每個科學值只寫一次，與來源一起表示為 `Claim(value, support)`；程式將同一個值投影至 RequestedOutcome 及 evidence。既有單值 schema 不能同時為一個欄位填入兩個互斥值；多個解讀使用不同 hypothesis。

本輪新增：

- 清單值排序與去重，完全相同的 evidence 去重；不同的依據保留供驗證。
- 每個原始 claim 的欄位路徑與 support 路徑，即使輸出去重也保留所有來源位置。
- `project_claims` 回傳獨立的投影、同一套 validator 的結果與來源紀錄，不修改模型原始 claims。
- `routing.semantic_claims_projected` 記錄投影的診斷；標記為 `before_normalization`，與後續還原、最終驗證分開。
- claims 修補回饋使用第 2 項的問題分類。

來源狀態分為 `quote_grounded`、`quote_unverified`、`inferred`、`unresolved`。**quote_grounded 只表示引用對得上原文，不表示原文一定支持該語意，也不表示方法適用。**例如「沒有突變矩陣」中的「突變矩陣」可以被引用，但不可因此通過目前輸入檢查。投影的 `validation.valid` 與後续正規化後的驗證仍必須分開檢查。

主要程式：

- `scripts/netzoo_agent_core/contracts/semantic_claims.py`
- `scripts/netzoo_agent_core/interpretation/claim_projection.py`
- `scripts/netzoo_agent_core/interpretation/claim_prompt.py`
- `scripts/netzoo_agent_core/graph/claim_invocation.py`

## 驗證

新增測試先在修復前重現失敗，再以修復後結果驗證：

- 跨假設越權、改寫研究目標或執行意圖被阻止。
- 只替換錯誤引用可以成功，不相關證據不被修改。
- 只刪除引用不能偽裝成修復成功。
- 完整 runtime 引用修補仍只有原有的第一輪與 reviewer，且保留原目標。
- claims 的順序與重複值不改變投影，原始來源仍可追蹤。
- 虛構引用兩輪仍失敗時，不產生已接受的 interpretation。
- 相同手工標註資料在 legacy 與 claims 下：sample-specific miRNA network → `run_lioness_puma`；aggregate miRNA network → `run_puma`；不存在的引用 → 驗證失敗。
- 否定句即使引用對齊，仍被 request-integrity 驗證拒絕。

重現指令：

```sh
python -m pytest -q tests/test_scoped_semantic_repair.py tests/test_claim_projection.py
python -m pytest -q
```

106 個針對性與相鄰流程測試通過。完整測試：3,310 通過、35 跳過、2 個相依套件棄用警告。

## 對照評估與論文界線

既有 `scripts/evaluate_routing.py` 支援 `--semantic-contract legacy` 與 `--semantic-contract claims`。下一階段以同一模型、相同預算、同一份未用於調整的問題集及相同重複次數對照；分開報告選擇正確率、已驗證資訊流失、錯誤執行率、澄清適切性與成本。不要只比較衝突數：claims 在表示上消除重複值，不等於消除了語意理解錯誤。

本輪沒有呼叫付費模型，也沒有使用 heldout 資料調整規則，故不宣稱模型表現或未見問題的泛化能力提升。claims 保持實驗性，避免把契約層面的成功直接當成正式上線依據。

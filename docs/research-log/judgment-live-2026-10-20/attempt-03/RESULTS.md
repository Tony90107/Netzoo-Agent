# Attempt 03：能力核對改用 gpt-4o-mini 後重跑（2026-10-20，Claude）

同一份凍結題目（`items.json` 與 attempt-01/02 相同），程式 `7aa1ab5d`。能力核對從免費 nemotron（NVIDIA 端點 404）改為 `openai/gpt-4o-mini-2024-07-18`（`.env`；自己的 LLM、16k 上限）。6 個 session、6 個回合（T03 第一回合 exit 2 = 需要輸入檔，第二回合沒跑）。費用 US$0.0236。沒有執行任何科學分析。

| 題 | 預期 | attempt-02（404） | attempt-03 | 說明 |
|---|---|---|---|---|
| T01 9 或 17 人 | DO | ASK | ASK | 讀到 unknown sample_count [9,17]，但 `applies_to=[]` → `verified_unknowns` 丟棄；fact agent 問「至少 3 個嗎？」，兩個候選都 ≥3，問了也分不出來 |
| T02 1 或 2 個樣本 | DECLINE | UNCHECKED | DO | 讀取完全沒讀到樣本數疑問（三種數量欄位都空）→ 錯誤放行 |
| T03 2 或 14 個樣本 | ASK | UNCHECKED | DO（run，預檢擋下） | 同 T01，疑問因 `applies_to=[]` 被丟；fact agent 的問題被 R5 交給輸入檔預檢（數樣本、少於 3 會擋），檔案不存在而停。設計上可接受 |
| T04 蛋白 180 或 1,800 | ASK | ASK | ASK | 符合 |
| T05 因果 DAG | DECLINE | UNCHECKED | DECLINE | 符合（404 時的失敗已消失） |
| T06 目標不明 | CLARIFY | UNCHECKED | CLARIFY | 符合 |

## 結論

- 能力模型恢復後，T05、T06 正常，attempt-02 的 UNCHECKED 確實來自 404。
- Codex 的數量修正（`c7511674`）在 live 沒有機會作用：它處理的是「疑問已進入核對」的情況；這三題的疑問在更早就丟了（T01/T03：`applies_to=[]` 被當成「與結果無關」；T02：根本沒讀到）。以三個版本重建 T01/T03 的讀取（ROUND-06 前、Codex 修改前、現在），`verified_unknowns` 都是空的：**不是 Codex 的修改造成，也不是它能修到的地方**。
- 下一個該修的（K6 同一類）：(1) 樣本數候選即使寫在 `unknown_facts` 且範圍是 `[]`，也不能無聲丟棄，應進入同一個「候選是否改變可行性」的程式判斷；(2) fact agent 的問題必須能區分使用者給的候選（T01）。

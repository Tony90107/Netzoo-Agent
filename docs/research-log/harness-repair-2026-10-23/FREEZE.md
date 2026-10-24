# harness repair 凍結版（2026-10-24）

使用者核准：停止逐項修補，凍結系統，轉寫論文。

## 凍結的程式

harness-repair 分支：`8c1ed515`（P5 第 2 輪）加上兩項修補。

| 項目 | 檔案 | 內容 |
|---|---|---|
| B | `graph/capability_check_call.py`（`same_model`）、replay 的 `NETZOO_REPLAY_CURRENT_MODELS` 模式 | 同一個模型的備援讀取不算 provisional |
| A3 | `graph/capability_check_call.py`（`spent`）、`graph/fact_check_call.py` | 可選呼叫在預算預檢被擋，不再讓 check 與 fact check 不跑 |

不在凍結版的：

- **A1′**（候選）：程式存在 `a1prime-candidate.patch`。
  - replay 614 → 622，但這是事後修改；h8 確認的結果是「案例不足」：36 份讀取中只改變 2 份，沒有造成傷害。
  - 正式數字不含 A1′。
- **A2′**（撤回）：`a2-withdrawn.patch`。
- **A1 宣告版**（撤回）：只有紀錄。

## 凍結版的數字

| 量測 | 結果 |
|---|---|
| 完整 `tests/` | 5,007 passed、51 skipped、0 failed |
| 標準 replay（`pFinal.json`） | 判對 614／757（只比種類）；嚴格 600／757 |
| 現行設定 replay（`pFinal-current.json`） | 判對 622／757（只比種類）；嚴格 608／757 |
| P0 基準（`base.json`，相同的金標重標） | 判對 608／757；嚴格 594／757 |
| 理由稽核（`layers-final.txt`，208 則） | 說錯 0、沒附理由 0（P0 基準：說錯 2、沒附理由 67） |
| Fixtures | 與 P5 修正後相同 |
| h7 live | P5 第 1 輪：單輪 A 20 → E 24（/36）；第 2 輪 E′ 22／36、多輪 7／14 |
| h8 live（A3 + A1′ 組，36 份讀取） | 判對 18／36；A3-only 組 17／36 |

## 已知限制（論文要寫）

1. 剩下的錯誤以讀題層為主：replay 中 94%，最寬的算法也有 69%（`attribution/ATTRIBUTION.md`）。
2. 執行句、結果句片段、輸入描述被讀成獨立的需求列，造成誤判為部分可做（replay 中 14 筆）。只比判定種類的計分看不到這類錯誤。
3. 只靠用字分不出「不確定」和「已說明」，所以 R1 需要另一份讀取作證（A2′ 撤回的原因）。h7 S16 這一類漏讀因此無法用程式補救。
4. replay 不能重新呼叫 fact agent。錄製時沒跑 fact agent 的讀取（p0、p1、goal 不明時），在 replay 中低估了 ASK。

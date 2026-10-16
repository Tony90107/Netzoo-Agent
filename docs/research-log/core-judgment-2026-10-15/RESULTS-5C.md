# 第 5c 階段：結果沒定時判 CLARIFY——實作與離線 fact agent（2026-10-16）

## 結論

- **C1、C3 通過，C2 差 1 題沒通過**：U 類追問或說明事實的題數是 16/24，門檻是 ≥ 17/24（第 2 階段的數字）。
- 少掉的 1 題是 **U11**，和 5c 新增的 R7 無關：
  - fact agent 問的問題和第 2 階段一樣，而且把它標成「關於資料」（`about = user_data`），所以 R7 沒有作用。
  - 這次 fact agent 把「是」的結果寫反了（兩個答案都寫 `not_supported`），被 R3 擋掉。第 2 階段同一題通過了 R3，而且因為輸入檢查會驗證，所以是說明、不追問。
  - 只跑一次，無法分辨這是新增欄位造成的，還是模型本來就有的輸出變異。
- 精確度有守住：U 類 0 題被判成「結果沒定」，P 類 0 題被多問（第 2 階段是 1/23）。fact agent 把不少 P 類的請求標成「關於想要的結果」，但都被 R1 擋下，因為能力檢查沒有讀到使用者不確定。
- 程式：`1a33d85e`。全套測試 3,872 個通過。

## 條件（與第 2 階段相同）

- 範圍：m3 開發集英文 U 類 24 題、P 類 23 題，只取有候選 workflow 的題目。
- 模型：gpt-4o-mini（routing 模型），每題呼叫 1 次，共 47 次，0 次失敗。
- 候選 workflow 取自 m3 錄製的決策。
- R1 的第二讀取者：第 2 階段 `live/f2w` 錄製的能力檢查讀取。

## 門檻

| 門檻 | 結果 | 是否通過 |
|---|---|---|
| C1：U 類 0 題產生 `open_results` | 0 | 通過 |
| C2：U 類追問或說明事實 ≥ 17/24 | 16/24 | **差 1 題，未通過** |
| C3：P 類「追問或結果沒定」合計 ≤ 1 | 0 | 通過 |

## 「關於想要的結果」的提案

fact agent 在 9 題中提出了「關於想要的結果」的提案：

| 題目 | 列出的選項 | 結果 |
|---|---|---|
| P03、P05、P25、P29 | 2 個以上 | R1 擋下（能力檢查沒讀到使用者不確定） |
| P07 | 0 個 | R1 擋下 |
| U16 | 1 個（「seven groups」） | R1 擋下 |
| U24 | 2 個 | R1 擋下（第 2 階段也沒有處理到） |
| U30 | 2 個（「network wiring for each sample」「TF activity values for each sample」） | 照常追問，正確 |

- fact agent 標「關於想要的結果」標得很寬鬆，例如 P25 把設定值「2 through 5 clusters」也標成結果。R7 能不能避免誤判 CLARIFY，主要靠 R1 的兩個讀取者都要同意。
- 開發集 m3 沒有「太模糊」類的題目，所以 5c 對 C24 這類題的召回，只能在題庫實測時看到。

## U11 的細節

- 請求：「Run LIONESS-DRAGON on two valid-format layers … They may contain two or ten paired samples; that count is not yet known.」
- 這次的提案：問「Do you have at least three paired samples?」，合約引文是「Require at least three samples.」，yes 和 no 都寫 `not_supported`，所以 R3 擋下。
- U11 是「數量給了兩個候選值」（2 或 10 個樣本），正是 5b 由程式判斷的情況。實際對話中，只要能力檢查讀到這組候選值，就會由程式追問，不需要靠 fact agent。這次離線條件用的是第 2 階段的舊讀取，沒有 `count_alternatives`，所以看不到 5b 的效果。

## 費用

gpt-4o-mini 47 次呼叫，約 US$0.03。

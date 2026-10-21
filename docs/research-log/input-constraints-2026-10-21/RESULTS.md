# ROUND-22 結果：規格書的輸入與設定限制由程式檢查

- 日期：2026-10-21
- 計畫：`collab/ROUND-22-PLAN.md`
- 提交（未推送）：
  - `b03c0124`：R22-A
  - `3f42b483`：R22-B
  - `f09b33ef`：R4 延伸，live 驗證中發現
- 費用：**US$0.022**（gpt-4o-mini）
  - 離線窄讀 8 次：US$0.0006
  - live 5 個 session：US$0.0214
  - 沒有執行任何分析

## 結論

| | 全部 757 份 | 現行讀題形狀的回合（498 份） | 金標「不能做」判對 | 該拒絕卻做了 |
|---|---|---|---|---|
| ROUND-22 前 | 632 | 443（89.0%） | 111/122 | 7 |
| **ROUND-22** | **638** | **446（89.6%）** | **114/122** | **4** |

- 每一步都只修好、沒改壞，門檻全部通過：
  - 有金標的判斷 0 改壞；
  - 觸發範圍外 0 改變；
  - 新的拒絕原因逐句確認為真；
  - 測試 4,919 全過。
- 計畫鎖定的 4 份中，**H27、L48、M25 修好**；M46 依計畫暫不做。
- 另外順帶修好 C18 p3、C30 ×2，它們屬於同樣的錯誤模式。

## R22-A：使用者點名的 CONDOR，沒有網路時不能照做

- **規則（`ruled_out.without_unbuilt_network`）：** 同時符合以下條件時，CONDOR 的 credit 改為「照你要的做不到」，並把 CONDOR 標為這次執行被擋（ROUND-17）：
  - 這一列由使用者點名 CONDOR；
  - 沒有現成網路：讀題標 `input_network: none`，或使用者原話說沒有；
  - 請求沒有點名能先建網路的 PANDA、PUMA 或 OTTER。
- **原因句：**「CONDOR runs only on a regulator-gene (source-target-weight) network; building one first (OTTER, PANDA, PUMA) is a separate run the request does not name.」使用者自己說沒有網路時，會先引用原話（L48：「You said "We haven't built any network yet"」）。
- **harness：** 修好 H27、L48、C18 p3，改壞 0（632 → 635）。三份回覆的原因都和金標相同（CONDOR 只吃調控網路、不吃表現量）。
- **放置位置：** 計畫寫的是 `method_conditions`，實作放在 `ruled_out.py`。原因是它要用到 `ruled_out` 已有的輸入種類與「誰能建網路給 CONDOR」，而且要在 `without_ruled_out` 之後、ROUND-17 的 same-run 之前執行。

## R22-B：沒被讀到的數字，只對被點名 workflow 的數值設定窄讀一次

- **觸發（程式）：**
  - 這一列有 credit，點名的 workflow 有數值設定；
  - 這一列原文中的數字，依位置沒有被任何已讀的數量或設定涵蓋；檔名裡的數字不算。
- **窄讀：** 一次 strict 小呼叫，只列出該 workflow 的數值設定，每個設定一組平的欄位（原文、值）。
- **程式核對後才採用**：原文要在請求中、要涵蓋一個沒讀到的數字、值要出現在原文中。之後交給 `method_fitting`，由 workflow 自己的規則判斷，例如 kmax ≤ 樣本數。
- **觸發 12 份讀取、8 個請求**（`evaluate_settings.py`）。窄讀 8 次全部讀對：M25「2 to 8」、C30「2 through 8」、C35「2 and 6」、L30「3」與「9」等。
- **harness：** 修好 M25、C30 ×2，改壞 0（635 → 638）。對照組 C35（248 個腫瘤）、L30（9 個 organoid、上限 9）維持能做。
- **回覆：** 「SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled.」也附上「SAMBAR 用它自己的設定仍可執行」的替代方案；預設 kmax 4，小於 6 和 5 個樣本，所以這句是真的。

## Live 驗證中發現的問題與修正（`f09b33ef`）

| 題目 | 金標 | live | 原因 |
|---|---|---|---|
| H27 | 不能做 | **不能做** | R22-A 擋下 |
| L48 | 不能做 | **不能做** | R22-A 擋下 |
| C30 | 不能做 | **不能做** | R22-B 窄讀到 2–8，kmax 超過 5 個樣本 |
| M25 | 不能做 | 請說清楚（result_open） | 見下 |
| C35 | 能做 | 請說清楚（result_open） | 見下 |

- **M25、C35 的問題不在 R22，而是 fact agent 把分群數範圍本身當成「使用者沒決定要哪個結果」：**
  - M25 是「trying anywhere from 2 to 8 subtypes」，C35 是「between 2 and 6 subtypes」；
  - 規則 R7 把它變成「請說清楚」，排在所有判斷之前。
- **這兩個範圍其實已經讀成 kmin、kmax：** M25 由讀題讀到，C35 由 R22-B 的窄讀讀到。
- **修正：** 規則 R4（讀題已經當成陳述過的，就不再問）原本只檢查「引用落在已陳述的原文裡」。現在也拒絕「引用裡含有已陳述、且有值的設定」。
- **不受影響、仍會問的：**
  - 沒有值的設定，例如 h2 J21「lam should be 1.5, or maybe 0.15」；
  - 不確定的數量，例如 M38「8 or 15」。
- **第一版有錯：** 沒有要求「有值」，結果 J21 從問一題變成直接做。重放時發現後就修正了。
- **修正後的結果：**
  - harness 錄製的判斷 0 改變；
  - 這 5 個 live session 依它們錄到的讀取重放，**全部得到金標判斷**：M25 不能做、C35 能做。
- **沒有再跑 live：** 計畫上限是 6 個 session，已用 5 個。修正的效果是用 live 錄到的實際輸出重放確認的。

## 和計畫不同之處

1. R22-A 放在 `ruled_out.py`，不是 `method_conditions`（原因見上）。
2. 新增 R4 延伸（`f09b33ef`），不在計畫中，是 live 驗證發現的。
3. 有金標的判斷全都只修不壞；M46 依計畫暫不做。

## 檔案

| 檔案 | 內容 |
|---|---|
| `size.py`、`harness-A.json`、`harness-A2.json`、`harness-B.json` | 計畫時的規則量測（含 M46 的兩種版本） |
| `harness-r22a.json` | R22-A |
| `evaluate_settings.py`、`settings-triggers.json`、`settings-reads.json`、`harness-none-b.json`、`harness-r22b.json` | R22-B |
| `harness-r4.json` | R4 延伸後 |
| `live-check/` | 5 個 live session |

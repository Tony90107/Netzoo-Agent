# 第 0 階段基線（round p0，2026-10-15）

## 結論

- 四態成本分數 **45.6 / 100**；56 題中有 20 題判斷正確。
- 計分方式：程式讀 trace 的 `core.decision` 計分，不用盲標。ASK 題的追問事實由我逐題核對；回覆是否忠實呈現判斷，56 題全部由我核對。
- 本表使用離線重放版（`p0-replay`）。錄製版的 shadow 規則順序有誤，修正後重放，改變的正好是預期的 4 題（C10、C22、C37、C49：UNCHECKED → DECLINE）。
- 忠實度：重放版 55/56，錄製版 51/56。唯一不一致的是 C58：判斷是做 PANDA，但回覆給了 6 個 workflow 的選單。

| 類別 | 正確 | 成本分數 | 判斷分布 | 主要錯誤 |
|---|---|---|---|---|
| 該做（do） | 8/14 | 67.9 | DO 9、DO(partial) 2、UNCHECKED 2、DECLINE 1 | 誤拒 3（C25、C40 把資料描述讀成不可做；C51 把「header row, gene IDs in the first column」讀成 OTTER 設定）；檢查模型失敗 2（C35、C52）；多給選項 1（C59） |
| 不該做（dont） | 8/13 | 66.7 | DECLINE 8、DO 3、DO(partial) 2 | 誤承諾 3（C17 只固定一個 lambda、C18 用表現量直接跑 CONDOR、C57 COBRA 基因數少於樣本數）；部分承諾 2（C14、C47） |
| 該追問（ask） | 3/15 | 33.3 | DO 8、ASK 4、UNCHECKED 2、CLARIFY 1 | 沒問就做 8；問錯事實 1（C44 問「一份還是每樣本一份」，該問的是檔案形式）；問成目標 1（C48） |
| 太模糊（vague） | 1/14 | 14.3 | DECLINE 9、DO 2、UNCHECKED 2、CLARIFY 1 | **回「沒有 workflow 能做」9 題**；直接選 workflow 2 題（C23 DRAGON、C53） |

- 模型與費用：nemotron 檢查成功 50/56（另外 6 次改由備援模型讀取，其中 4 題因此變成 UNCHECKED）。服務例外 0。gpt-4o-mini 共 US$0.11。
- 舊口徑對照：誤承諾含部分承諾為 5/13（嚴格只算完整承諾為 3/13），誤拒 3/14。這組題目的設定與上限陷阱比 m3 多，不能直接和 m3 的 16% 比。

## 失敗型態（給後續階段用，不在本階段修）

1. **模糊請求被當成「做不到」**（第 1 階段的目標）。能力檢查把沒有說出結果的句子讀成被要求的結果，查不到對應 workflow，於是判全缺口，回覆「No registered workflow produces this」。例子：
   - 「send me the results」（C12）
   - 「tell me what you find」（C15）
   - 「Should I go with BONOBO or LIONESS…?」（C09）
   - 「run whichever NetZoo analysis is appropriate」（C19）
   - 「a network analysis」（C24）

   C60 則被路由讀成資料下載。這正是 spec 的界線 2：目標不明時，必須先釐清，才能做可不可做的判定。
2. **追問只在 11 種 dimension 內發生**（第 2 階段的目標）。問對的 3 題（C21 網路型別、C34 結果二選一、C56 體細胞或生殖細胞）都在既有清單內。沒問就做的 8 題，決定性事實不在清單內：
   - 檔案是表現量還是突變（C20）
   - 甲基化是二元還是連續（C42：value_type 在清單內，但沒有被讀到）
   - 每個病人還是每組一份（C11、C43）
   - 是否已做 log 轉換（C50）
   - 特徵數上限（C45）
   - 帶正負號的效應要每個樣本一份還是整體一份（C31）
   - 「調控強度」的兩種讀法（C36）
3. **資料描述被當成設定或結果**（C25、C30、C40、C51）。這不屬於四態判斷本身，而是讀取層的問題，記為第 2 階段 fact agent 的 R4 參考。不在 spec 範圍內另開修正。
4. **合約限制沒套用**（C17、C18、C57）。分別是 lambda 必須成對、CONDOR 的輸入型別、COBRA 要求基因數多於樣本數。第 2 階段的合約接地讀取可能涵蓋其中一部分；若沒有，再依 spec 第 11 節走變更流程。

## 偏差

- 錄製版的 shadow 有兩個量測工具問題，都已修正，並重放錄製的判定（`replay_core.py`，沒有重跑任何 session）：
  - 路由失敗但能力檢查已確認全缺口時，回覆仍會拒絕，所以應判 DECLINE。
  - 能力檢查整段回覆時沒有記錄 view（`whole_check_result` 提早 return）。修正後才會有記錄。本輪錄製資料中，這類回覆的 view 欄是空的。
- 計分腳本 `score_core.py` 沒有改動。其中 do 題的 DO(partial) 被算成誤拒（成本 2）。但 C25、C40 的使用者實際感受是「給了 workflow，外加一行錯誤的不可做」，若改算成本 1，do 類分數會變成 75.0。記錄在此，不改分數。

## 下一步

依 spec 進入第 1 階段（目標不明 → CLARIFY）。門檻：vague 進步；do 類多出的釐清 ≤ 1 題；其他類別最多退步 1 題。

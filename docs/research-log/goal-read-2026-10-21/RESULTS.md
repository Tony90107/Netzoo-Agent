# ROUND-21 結果：R5 撤回與 R21-A（說不出原因的「不能做」再讀一次）

- 日期：2026-10-21
- 計畫：`collab/ROUND-21-PLAN.md`
- 提交（未推送）：
  - `e050d4d7`：R5 撤回
  - `8d777ff4`：R21-A
- 費用：**US$0.021**（gpt-4o-mini）
  - 離線重問 30 個請求：US$0.0020
  - live 5 個 session：US$0.0194
  - 沒有執行任何分析

## 結論

harness 重放 757 份有金標的讀取：

| 階段 | 判對 | 能做 | 不能做 | 問一題 | 請說清楚 |
|---|---|---|---|---|---|
| ROUND-20 | 595（78.6%） | 91% | 85% | 66% | 73% |
| R5 撤回 | 602 | 91% | 85% | **70%** | 73% |
| **R21-A** | **626（82.7%）** | 91% | 85% | 70% | **85%** |

- 兩項都只修好、沒有改壞任何一份。
- 有多次讀取的 58 題中，每次都判對的從 16 題增加到 22 題。

## 1. R5 撤回：檔案能確認的事也先問（使用者決定）

- **原本（R5）：** 使用者說不確定的事，若執行前的檔案檢查能確認，就不問、直接執行。
- **現在：** 一律先問。
- **改動：**
  - `kept_facts` 不再標記 `settled_by_input_check`；
  - `decide_core`、`with_core`、ask 回覆與卡片，都改為詢問每一個被接受的問題，舊紀錄裡的標記一律忽略；
  - 「執行前會檢查」的附註拿掉。
- **harness：** 7 份改變，全部是修好：M38、L40、C44 ×5（其中 g4o1、g4o2 原本被判成 full gap 拒絕），沒有改壞的。

## 2. R21-A：說不出原因的 full gap，換一種形狀再讀一次

### 做法

- **觸發（程式）：** 判成 full gap、每一列依 ROUND-20 的 `stated()` 都說不出原因、check 已確認、目標不是已經不清楚、fact agent 也沒有要問。
- **一次窄讀**（`GoalRead`，strict，最多 400 token）：
  - 先逐字引用「請求中說使用者想要什麼」的文字；
  - 再二選一：`names_a_result` 或 `names_no_result`。
  - 不問模型「這題模不模糊」（CLAMBER）。
- **程式決定：** 同時符合以下條件時，在 check 寫入 `open_goal_quote`，`decide_core` 判「請說清楚」（`goal_open`）：
  - 答案是 `names_no_result`；
  - 引用核對得到原文；
  - 引用沒有點名剛好一個登錄 workflow（沿用 `goal_unclear` 的「問一個具名方法就有目標」）。
- **其他情況，或沒有回答：** 維持原本的「不能做」。
- **結尾句：** 每一列都只說「沒對到」的拒絕，結尾改為「This was not matched to any registered workflow, so none is offered.」，不再斷言「沒有 workflow 能產生」。沒有任何列的拒絕，開頭句也改為「沒有對到」。

### 離線量測（`evaluate.py`）

- 1,060 份讀取中，**55 份會觸發**（30 個不同請求），其中 44 份有金標：
  - 請說清楚 24；
  - 不能做 18（其中 C22 VCF ×10）；
  - 問一題 1、能做 1。

| 比較組 | 改變 | 修好 | 改壞 | 判對 |
|---|---|---|---|---|
| 沒有讀取（現行行為） | 0 | — | — | 602 |
| B0：只用程式，觸發就判請說清楚 | 55 | 24 | **18** | 608 |
| **A：窄讀** | 26 | **24** | **0** | **626** |

- **窄讀在有金標的 30 個請求上分得很乾淨：**
  - 金標請說清楚的全部答 `names_no_result`，例如「a network analysis」「a systems-level view」「Which of these should we apply」「give me figures for the paper」；
  - 金標不能做的全部答 `names_a_result`，例如「give me a filtered VCF」「the list of genes differentially expressed」「a trained model that predicts…」「get gene communities」。
- **沒有金標的改變 2 份：**
  - J16「What kind of network analysis should I be doing with this?」→ 請說清楚，合理；
  - MX15「convert it to a validated edge list for CONDOR communities, and use GIRAFFE itself for native per-patient wiring?」→ 請說清楚，**可能讀錯**：它點名了具體結果，但點名兩個 workflow，不在「剛好一個」規則內。

### 門檻

| 門檻 | 結果 |
|---|---|
| 1. 觸發範圍外的判斷 0 改變 | 通過：改變的 26 份全部是觸發的讀取 |
| 2. 請說清楚至少 +15、不能做最多 −3 | 通過：+24、−0 |
| 3. 拒絕的原因不新增說錯 | 通過：仍判不能做的 183 份，原因行與 ROUND-20 完全相同；22 份的結尾改成「沒對到」 |
| 4. 測試全過 | 通過：4,911 passed（新增 `tests/test_goal_read.py` 5 項） |

### Live 驗證（`live-check/analysis.txt`，5 個 session）

| 題目 | 金標 | live | 窄讀 |
|---|---|---|---|
| C24 | 請說清楚 | 請說清楚（goal_unclear） | 沒觸發：這次的讀題直接判目標不清楚 |
| C23 | 請說清楚 | 請說清楚（goal_unclear） | 沒觸發 |
| C12 | 請說清楚 | 請說清楚（goal_unclear） | 沒觸發 |
| C22 | 不能做 | 不能做（full gap） | 觸發，答 `names_a_result`（「give me a filtered VCF」），維持不能做 |
| M20 | 不能做 | 不能做（full gap） | 觸發，答 `names_a_result`，維持不能做 |

- 5/5 符合金標。窄讀在 live 中確實被呼叫、成功回答，而且沒有把真正不能做的改掉。
- 兩份拒絕都只說「沒對到」，沒有說錯的原因。
- 三題請說清楚這次走既有的 `goal_unclear` 路徑：同一題每次讀法不同，只在讀題沒判出目標不清楚的那幾次，窄讀才派上用場。

## 和計畫不同之處

1. **窄讀改成二選一，不是三選一，也不給登錄表的結果清單。**
   - 計畫中「(a) 清單中的某一類 → 請說清楚」會把 C18（只用表現量找 communities）、C14（OTTER 加 L1）、L17、J31、M18 這類「點名表內結果、但條件做不到」的金標不能做改錯。
   - 少了清單，prompt 也比較短。
2. **計畫中「(b) 表外結果 → 不能做並引用原話說明原因」沒有做。** 「沒有任何登錄 workflow 產生『〈引用〉』」這句仍建立在模型的讀法上，對上述那幾題也不正確。依 ROUND-20 的規則，仍只說「沒對到」。
3. **「引用點名剛好一個登錄 workflow 就不改判」是看到沒有金標的 N21 之後才加的。** 沿用既有的 `goal_unclear` 規則，有金標的結果不受影響。**之後已撤回（`9ea8369c`）：** C31 修正的 live 驗證中，有金標「請說清楚」的 M33 被這條防護擋成「不能做」，見 `research-choice-2026-10-21/RESULTS.md`。
4. **結尾句也一起改了**：`core_views.decline_reply` 和沒有任何列的開頭句。

## 限制

- 觸發的 30 個請求，就是計畫分析時看過的那些題，沒有新的 held-out 題可驗證；h1–h4 與核心題都已看過。
- live 只有 2 次真的觸發，而且都是「維持不能做」的那一邊；「改判請說清楚」這一邊只有離線證據。
- MX15 這類「點名多個 workflow 的能力問題」仍可能被改判成請說清楚。結果不是錯誤資訊，但不如拒絕直接。

## 檔案

| 檔案 | 內容 |
|---|---|
| `harness-r5.json` | R5 撤回後的 harness 判斷 |
| `harness-none.json` | 新程式、沒有窄讀的判斷 |
| `harness-b0.json`、`harness-a.json` | B0 與 A 兩組的判斷 |
| `evaluate.py` | 觸發收集、B0、重問、A 組 |
| `triggers.json` | 55 份觸發的讀取 |
| `reads.json` | 30 個請求的窄讀結果 |
| `replies-a.json` | 套用窄讀後重新產生的拒絕回覆 |
| `live-check/` | 5 個 live session、`analysis.txt` |

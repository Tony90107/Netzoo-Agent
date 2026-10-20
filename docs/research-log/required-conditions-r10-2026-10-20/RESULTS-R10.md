# ROUND-10：數量條件不再被當成已通過（2026-10-20）

計畫：`collab/ROUND-10-PLAN.md`（步驟 0 後縮小，`STEP0.md`）。程式 `e62613f1`（分支 `closed-menu-phase0`，沒有推送）。$0，沒有呼叫模型。

## 做了什麼

1. **背景裡沒被讀到的並列整數候選，由程式判斷**（`request_facts._read_context_candidates`，交給既有的 `count_update`）：
   - T02「either one or two biological samples」：1、2 都少於 LIONESS-PANDA 的 3 → 不可做，回覆寫出「with 1 / with 2: LIONESS-PANDA needs at least 3 samples」。
   - 不會蓋過結果已明說的數量。一個測試抓到這點：原文先說「1 或 2」，又明說「There are 14」，以明說的為準。
   - 不算候選的：黏著字母的數字（「a single 10x run」不是「1 或 10」，由既有測試抓到）、小數、單獨的數字。
   - 「並列整數候選」的定義收成 `count_words.candidate_runs`，`sample_coverage` 改用同一份。
   - 被候選判出局的結果，second opinion 不再拿去問；否則它會用沒有樣本數的 method 再認可回來。
2. **回答能不能做時，說出沒被提到的數量條件**（`required_conditions.quantity_note`，接在「What I understood」每行之後，只有這一個出口）。例：「Not stated in your request: OTTER needs at least 2 samples -- checked against your files before any run.」已讀到數量或候選時不說。
3. **合約文字**：DRAGON（3）、GIRAFFE（2）、COBRA（2）的 `conventions` 與 `input_checks` 補上最低樣本數。執行前檢查本來就會擋（`data/dragon.py:80`、`giraffe.py:125`、`cobra.py:97`），這次補上合約文字。fact agent 看得到合約，所以它的輸入會多這一句。

## 重放（999 份已存讀取，`compare.txt`）

修改前 `867ccbce`、修改後各自重建 check、重跑核心判定（固定已存的 fact agent 答案與 run verdict）：

- 核心改變 **3 份**：live T02 ×3（attempt-02、04、05），ASK → **DECLINE**，執行與規劃都關閉。
- 有金標的 741 份：561 = 561。
- 72 份的「What I understood」多一句條件說明（56 份 DO、8 份 ASK、6 份 CLARIFY、1 份 DECLINE、1 份 UNCHECKED）。

測試：新增 12 個；更新 2 個預期值（request 層 `input_checks` 10 → 13、TaskDecision schema 快照）；全套 4795 passed、51 skipped。

## 限制

- 重建的 check 不含 second opinion，T02 在 live 會不會被 second opinion 再認可，靠新加的跳過規則與單元測試保護，尚未 live 驗證。
- 背景候選數字一律當成樣本數判斷。已存資料裡只有 T02 觸發；若使用者把其他數量（例如 1 或 2 個資料層）寫成並列且沒被讀到，可能被誤判。
- 模型第一次讀取漏讀仍未根治；這是程式端的補救。

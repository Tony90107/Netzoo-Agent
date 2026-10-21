# C31 修正：研究比較的讀取有回答時，不再當成 routing 失敗

- 日期：2026-10-21
- 起點：`c8857a55`
- 提交（未推送）：`0bb03d97`（修正）、`9ea8369c`（拿掉 R21-A 的單一 workflow 防護）
- 費用：live 3 個 session，**US$0.0099**（gpt-4o-mini）；離線 $0

## 結論

harness 757 份有金標：**626 → 632**，6 份修好、0 份改壞。

| 題目 | 金標 | 修正前 | 修正後 |
|---|---|---|---|
| C31（g4o2、p4b、p4c、p5r） | 問一題 | 無法確認（routing_failed） | 問一題（fact agent） |
| L14 | 問一題 | 無法確認（routing_failed） | 問一題（fact agent） |
| M33 | 請說清楚 | 無法確認（routing_failed） | 請說清楚（result_open） |

C31 現在問的正是關鍵問題：「Do you want signed effects for each biopsy separately?」，並引用使用者的原話和 GIRAFFE 規格書的「aggregate R matrix」。

## 原因

1. **研究比較的入口是一個詞表判斷。** `explicit_research_choice` 只要看到「not sure」「undecided」等字就成立，所以「問一題」類的請求（使用者說不確定）都會先進研究比較路徑。
2. **hypothesis reader 正常回答了**：`question_mode: unclear_goal`、沒有接受任何假設。router 卻把這個「有回答」和真正的失敗一起處理，標成 `research_choices_unavailable`。
3. **`decide_core` 遇到這個標記會先回「無法確認」**，在讀 capability check 的結果與 fact agent 已接受的問題之前。fact agent 其實已經問對了問題。
4. **受影響的 7 份讀取都一樣**：沒有呼叫失敗，預算也沒用完。

## 修正（`router_invocation._route_request`）

- **真正的失敗照舊保守失敗**（`research_choices_unavailable`）：
  - reader 沒有呼叫；
  - 呼叫失敗；
  - 預算用完。
- **reader 有回答、但沒有陳述的假設時：** 回傳 `research_choices_unread`。
  - 不選任何 workflow；
  - 清掉原本「請陳述每個假設」的追問（C31 根本沒有陳述假設）；
  - 由 capability check 與 fact agent 決定這一輪。
- **重放同步：** `replay_full` 依紀錄中 reader 是否回答，同步這個標記。harness 結果和事先的模擬（`simulate.py`）完全相同。
- **測試：** 新增一項（reader 回答 `unclear_goal`、沒有假設時：不選 workflow、不算失敗）。原有「失敗時不可退回單一 workflow」的兩項測試照樣通過。全部 4,912 passed。

## Live 驗證（`live-check/analysis.txt`）

| 題目 | 金標 | live | 說明 |
|---|---|---|---|
| C31 | 問一題 | **問一題** | 這次 reader 接受了假設，走 research_guidance 路徑 |
| L14 | 問一題 | 不能做（full gap） | 新標記有生效（`research_choices_unread`），但這次 capability check 沒把「I want DRAGON on serum proteomics and stool metabolomics」對到 DRAGON。這是讀題錯誤；回覆只說「沒對到」 |
| M33 | 請說清楚 | 不能做（full gap） | R21-A 的窄讀答對了「沒指名結果」，卻被我在 R21-A 為沒有金標的 N21 加的「點名一個 workflow 就不改判」防護擋下 |

**依 M33 拿掉 R21-A 的防護（`9ea8369c`）：**
- 這條防護只有沒有金標的 N21 支持，M33 是有金標的反例，因此拿掉。
- 重放這次 live 的 M33 → 請說清楚（goal_open）。
- harness 有金標的判斷不變（632）。只有沒有金標的 N21 改成請說清楚：會列出可得結果並追問，不是錯誤資訊。

## 限制

- live 中 C31 這次走的是另一條路徑（reader 接受了假設），所以修正後的路徑在 live 上只由 L14、M33 驗到「標記不再是失敗」，兩題最後都因其他原因判錯。
- 「問一題」能否答對，仍取決於 capability check 是否讀到結果；L14 這次就沒有讀到。

## 檔案

| 檔案 | 內容 |
|---|---|
| `simulate.py`、`harness-sim.json` | 修正前的離線模擬 |
| `harness-after.json` | 修正後（重放同步） |
| `harness-final.json` | 拿掉防護後 |
| `live-check/` | 3 個 live session |

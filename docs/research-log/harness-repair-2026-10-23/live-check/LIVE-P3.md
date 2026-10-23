# P3 多輪 live check（2026-10-23）

- **範圍**：使用者核准 13 個 session（29 個回合），每個 session 1 次，用 gpt-4o-mini，上限 US$0.30。
  - 程式為乾淨的 `.worktrees/netzoo-harness-live`，固定在 `1dda3692`，執行前後都核對過沒有變動。
  - 第 1 輪是錄製題目的原文，之後的回合是事先寫好的回覆。
  - 第 1 輪沒有停在 ASK 或 CLARIFY 的 session 就停下，記為「未觸發」。
- **花費**：
  - provider 回報 **US$0.0839**，13 個 session 全部完成，沒有碰到上限。
  - S11、S12 的 4 次回覆解析呼叫沒有存進 session（見發現 1），每次約 US$0.00016，未計入；合計約 US$0.0845。
- **用途**：題目都看過。這輪只檢查 P3 在 live 路徑上的多輪行為，不是準確率評估。
- **檔案**：
  - `items-p3.json`：題目、回覆與預期；
  - `run_live_p3.py`：runner；
  - `REPLIES-P3.md`：回覆全文，由 `analyze_p3.py` 產生；
  - `live/p3live/`：每個回合的 session、trace 與 CLI 輸出。

## 結果

| Session | 第 1 輪 | 之後 | 程式綁定 | 判斷 |
|---|---|---|---|---|
| S02 J48 | ASK：「2 or 4?」（count） | t2 DO（LIONESS-PANDA） | sample_count = 4 | ✓ |
| S03 J14 | ASK：「450 or 4,500?」（count） | t2 DECLINE：LIONESS-DRAGON 數值上限（4,800 個特徵、40 個樣本，算式正確） | feature_count = 4500 | 綁定 ✓、沒有再問 ✓；**補充的「整個 cohort 一個」條件沒有被讀到**，沒有改提 DRAGON |
| S08 M06 | ASK：「Are the calls somatic mutations?」（agent） | t2 DO（SAMBAR） | agent = yes（trace 有 `task.answers_bound`） | ✓ |
| S13 C24 | CLARIFY | t2 DO（PANDA） | new_goal：舊任務關閉，沒帶任何事實 | ✓ |
| S01 C45 | ASK：agent 問了無關的「Do you have at least three samples for each panel?」，沒有問 200 或 2,000 | t2 DECLINE，第二層理由（「couldn't match」） | 無：agent 題、回覆不是 yes/no | 判定種類符合預期，但理由不是數量上限（第 2 輪讀題沒有連到結果） |
| S04 J19 | ASK：agent 的「Do you want one network per tumour?」取代了 choice 維度題 | t2 DECLINE，第二層理由 | 無：「One per sample」不是 yes/no | ✗：第 2 輪讀題沒有連到 DRAGON 或 LIONESS-DRAGON |
| S05 J19（對照） | 同 S04 | t2 CLARIFY（第 2 輪） | 無（照設計） | ✗：第 2 輪讀題把目標讀丟了 |
| S11 C12 | CLARIFY | t2、t3 都沒有進到 graph | — | ✗：**兩輪上限碰不到**（發現 1） |
| S12 H13 | ASK：network_given 維度題 | t2、t3 都沒有進到 graph | — | ✗：同上 |
| S06、S07 C56 | DO（SAMBAR），沒問 somatic 或 germline | — | — | 未觸發（第 1 輪誤收） |
| S09 M06 | DO（SAMBAR），沒問 | — | — | 未觸發（與 S08 同一題，讀題變異） |
| S10 L14 | DECLINE，第二層理由 | — | — | 未觸發 |

**P3 的機制在 live 上：**

- **有用**：count 綁定 2/2（S02、S03）、agent yes 1/1（S08）、新任務 1/1（S13）。
- **沒用**：兩輪上限 0/2（S11、S12）。
- **沒觸發**：更正（S07）、兩題時的短答（S10）、以維度選項字作答（S06）。

**理由沒有說錯。** S03 的上限算式核對正確（4,800 × 4,799 / 2 × 40 = 460,704,000）。S01、S04、S10 的第二層理由只說查了什麼，沒有說錯的能力陳述；但它們的判定本身是讀題沒連到結果造成的錯判。

## 發現

1. **「不知道」的回覆進不了下一回合，兩輪上限碰不到（S11、S12）。**
   - 「I'm not sure, whatever is standard.」「I really don't know.」都被回覆解析（`follow_up` 呼叫）判為 needs_detail。CLI 只印出制式的「Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.」，graph 沒有跑，session 也沒有重存。
   - 結果：
     - 輪數不增加，第 3 次回覆仍是同一句制式提示；
     - 這句提示沒有重述還缺什麼；
     - 使用者一直答不出來時沒有盡頭。
   - 這正是 A13「兩輪仍未解」要處理的情況。P3 只讓「待答題已被程式對應到答案」的模糊回覆通過（S08 的 yes），沒有處理「什麼都對應不到」的模糊回覆。整合測試的 A13 用的是會進到 graph 的回覆，所以沒抓到。
2. **agent 的 yes/no 題取代了程式能對應的題（S04、S01）。**
   - S04 的 choice 維度題（「one network for the whole cohort」或「one per tumour」）被 agent 的「Do you want one network per tumour?」涵蓋（P1 的 `asked_as`），使用者自然的回答「One per sample, please.」就對應不到任何題。
   - S01 的 agent 題和引用的原文無關，而且沒有問真正的關鍵（200 或 2,000）。
   - 第 1 輪問了程式能對應的題（S02、S03 的 count）時，綁定都成功。
3. **追問回合的讀題（P3 刻意沒改）在 3 個 session 出錯。**
   - S03：補充的條件沒有讀到。
   - S04：沒有連到結果。
   - S05：目標讀丟了。
   - S04、S05 第 2 輪沒有任何 P3 程式改變判定：沒有已知的 count 或維度事實，輪數也小於 2。所以這是既有的「Previous NetZoo goal: … User follow-up: …」讀法的行為。用 TaskState 改寫讀題文字，是 P3 列為「不做、要 live 才能量」的項目。
4. **第 1 輪的變異讓 4 個 session 沒觸發。** C56 兩次都直接判 DO、推薦 SAMBAR，使用者明說不知道是不是 somatic，這是誤收。上一輪 p12live 同一題有問。M06 同一題一次問、一次不問。這些都在讀題層，不是 P3 的範圍。
5. **預算**：S02、S08 第 2 輪的 capability re-read 被預算擋下，兩個都仍判對。每個追問回合都是新的 run，預算沒有從上一回合帶過來。

## 建議的修正

- **(a) 對應不到答案的模糊回覆要算一輪，只用程式。**
  - 條件：任務有待答問題、回覆沒有對應到任何答案，而且回覆解析判為 needs_detail。
  - 做法：不走制式提示，也不跑 graph、不呼叫模型。
    - 輪數 +1，並存檔；
    - 第 2 輪：用存檔裡的 PendingQuestion 原文重述還缺的題；
    - 第 3 次起：用 exhausted 說明列出仍缺的資訊，不再追問；session 仍可續接。
  - 驗收：單元與整合測試；live 只重跑 S11、S12（2 個 session、6 個回合，約 US$0.01）。
  - 這會改變 needs_detail 的互動方式，**需要使用者決定**。
- **(b) 被 agent 題涵蓋的維度或 count 題，保留選項。** 回覆提到其中一個選項時照樣綁定。這次 live 沒有一個 session 會因此改善：S04 的回答「one per sample」不是選項字「one per tumour」。所以只記錄，不建議現在做。
- **(c) 追問回合的讀題**：是否用 TaskState 改寫讀題文字（例如原始請求加上已答事實與新的補充），屬於會改變模型讀取的改動，要 live A/B 才量得到。等 (a) 之後再由使用者決定。

## 修正 (a) 與重跑（2026-10-23，使用者核准）

### 改了什麼

條件：任務有待答問題、回覆沒有對應到任何答案，而且回覆解析判為 needs_detail。這時這個回覆算一輪，只用程式處理，不跑 graph、不呼叫模型。

- `engine/task_updates.unanswered_reply`：
  - 輪數 +1；
  - 已追問不到兩輪時，用存檔的 PendingQuestion 重述問過的題（含使用者原文）；
  - 已兩輪時，改用 exhausted 說明列出「Still missing」，狀態設為 exhausted，不再追問；
  - 只有一題 agent 題待答時，提示可以回 yes 或 no；
  - 答案選項有標籤就用標籤，沒有標籤時只在問題本身寫了那些選項字時才列出，絕不列內部值。
- `engine/task_updates.unanswered_round`：只把 task_state 存回 session（`session.save_task_state`，不動訊息與計畫），記 trace 事件 `task.unanswered_round`，並把文字交給下一個提示顯示。
- `engine/machine.py`：needs_detail 分支先問 `unanswered_round`；沒有待答任務時，維持原本的制式提示。行數仍是 1,000。

### 驗收

| 項目 | 結果 |
|---|---|
| 單元與整合測試 | 新增 5 個：重述 → exhausted、yes/no 提示只在單一 agent 題時出現、選項命名、真的 ConversationMachine 走兩次模糊回覆（graph 只跑第 1 輪；session 仍可用 `--resume latest` 找到；之後的實際回答照樣綁定並進到 graph）、沒有待答任務時維持制式提示 |
| 完整 `tests/` | **4,968 passed、51 skipped、0 failed**（含選項命名的修正；修正前為 4,967） |
| B2 replay（P3 → 修正 (a)） | 1,382 份讀取，判定 0 改變（這次只改 graph 之外的程式） |
| live 重跑 S11、S12 | 見下 |

### live 重跑（tag `p3a`）

- **程式**：live worktree 在 `1dda3692`，套上未提交的修正 (a)。runner 核對過只有 3 個程式檔不同，而且內容和修正版一致；跑完已還原成乾淨的 `1dda3692`。
- **花費**：**US$0.0096**，上限 US$0.05。第 2、3 輪的回覆解析費用改從 trace 取得。
- **結果**：

| Session | t1 | t2（模糊回覆） | t3（模糊回覆） |
|---|---|---|---|
| S11 C12 | CLARIFY，rounds 1 | 只有回覆解析一次呼叫，沒跑 graph；重述目標題與使用者原文；rounds 2 | exhausted 說明 + Still missing；rounds 3，狀態 exhausted |
| S12 H13 | ASK（network_given），rounds 1 | 同上；重述問題；rounds 2 | exhausted 說明 + Still missing；rounds 3，狀態 exhausted |

兩個 session 最後都仍可續接（有待答問題）。

**重跑發現一個顯示缺陷，已修正。** S12 的提示列出了內部值「Answer with one of: has, none.」，因為 network_given 這個維度沒有標籤。現在只列標籤，或問題本身寫出的選項字（例如 count 的「200 or 2,000」）；network_given 不再列提示。這只影響提示文字，已用單元測試涵蓋，沒有再跑 live。

### 仍然不支援的地方

- **沒有標籤的是非型維度題**（如 network_given）：使用者回「Yes, I have it」綁不到。它不是 agent 題，選項又是 has 或 none。這種回覆仍會交給下一次讀題判斷。
- 回覆解析判為 follow_up 的「不知道」照舊跑 graph，由 graph 的兩輪上限處理（S05 第 2 輪就是這樣）。

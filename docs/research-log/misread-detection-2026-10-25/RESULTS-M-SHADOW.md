# M 的 shadow 試行結果（36 題版，2026-10-25，US$0.2011）

依 [PLAN-M-SHADOW.md](PLAN-M-SHADOW.md) 執行（建置與看新資料之前宣告；sha256 開頭 `51363da46bf14de4`，跑完後未變）。凍結版 `041f0ee9` 沒有改；候選系統 C 在 `.worktrees/netzoo-m-hold`，沒有 commit。

## 結論：D3 不過，依宣告撤回 M；第 2、3 回合沒有跑

| 門檻 | 結果 | |
|---|---|---|
| B1 完整測試（開關關閉） | 5,019 passed（凍結版 5,007 加 12 個新測試）、51 skipped、0 failed | ✓ |
| B2 replay 與 fixtures（開關關閉） | 1,388 份讀取與凍結版逐筆相同（判定種類、partial、basis 都不變），614／757、嚴格 600；fixtures 與 `fixtures-p5fix.txt` 相同 | ✓ |
| B3 replay 與 fixtures（開關打開） | 同上，0 差異 | ✓ |
| B4 h9 離線演練（不計分） | 6 個旗標中 Z21、Z22 問事實，其餘 4 個問結果（`mhold-build/b4-dryrun.txt`） | 已列出 |
| D1 命中 ≥ 4 個錯誤、≥ 4 題 | 6 個：W01、W08、W14、W26、W28、W33 | ✓ |
| D2 精確度 ≥ 50% | 6／11（55%） | ✓ |
| **D3 K 組誤報 ≤ 4，DRAGON 對照誤報 ≤ 2** | **K 組 5 個（W11、W16、W17、W23、W34），其中 DRAGON 3 個（W16、W23、W34）** | **✗** |
| D4 FA、FR、MA 不增加；問錯種類的增加 ≤ MA 的減少 | FA 2 → 2、FR 2 → 2、MA 6 → 1、問錯種類 0 → 1 | ✓ |
| Q、T | 沒有計算：D 不過就停，是宣告的規則 | — |

- `h10-gates-d.json` 記錄 passed = false。`run_h10.py followup` 在任何呼叫之前就拒絕執行，沒有開始第 2、3 回合。
- **DRAGON 的疑慮被確認了。** h9 的 2 個誤報都是 DRAGON。h10 的 8 題 DRAGON 對照中，S 判 DO／DECLINE 的有 6 題，M 標出了其中 3 題，而這 3 題 S 都判對了。menu 讀取對 DRAGON 請求一直判「要哪個結果不明」（`ASK/intent` 的 artifact）。

## 執行

| 回合 | 內容 | 費用 |
|---|---|---|
| 冒煙（W03，不計分） | 2 回合（S 自己在第 1 回合就問了，所以沒有觸發） | US$0.0111 |
| 第 1 回合 | 36 個 session；S 判 DO／DECLINE 的 25 個都做了 menu 讀取（46 次呼叫，US$0.0508） | US$0.1900 |
| **合計** | | **US$0.2011**（上限 US$0.35；計畫估計 D 不過時停在約 US$0.19） |

- C 是 `041f0ee9` 加上 5 個修改的檔案與 4 個新檔案。runner 在每個 session 前後核對這些檔案與所有 tracked 檔案的 hash，全程不變。
- 所有角色都是 gpt-4o-mini。`shadow.m_hold` 事件：held 11、agrees 14、not_triggered 11；沒有讀取失敗。
- menu 讀取的費用只記在 shadow 事件裡，不進回合的 usage，所以沒被攔下的回合與凍結版的預算狀態相同（設計見 `graph/m_hold_call.py`）。

## h10 題組

- 盲寫的 subagent 寫 36 題與腳本化回覆。第二個盲的 subagent 覆核，改了 3 處金標說明（W14 的關鍵字、W26 的證據、W33 的事實描述），判定種類都沒變。
- 我逐題讀過，36／36 同意。封存在 `h10/SEALED.json`，items.json 的 sha256 開頭為 `7809fec3`。
- 分組：V 6、U 8、K1 11、K2 11。DRAGON 對照 8 題（K1 4、K2 4）。

## 凍結版 S 在 h10 第 1 回合的表現（不當門檻）

| 組 | 判對（種類加 workflow） | 錯的 session |
|---|---|---|
| V | 5／6 | W26 判 DO（MA） |
| U | 3／8 | W01、W14、W28、W33 判 DO；W13 判 DECLINE（MA 共 5） |
| K1 | 6／11 | W24、W35 判 DECLINE（FR）；W03、W15 自己提問（多問）；W08 判 DO 但 workflow 不對 |
| K2 | 8／11 | W18、W20 判 DO（FA）；W30 判 CLARIFY（多問） |
| 合計 | **22／36** | FA 2、FR 2、MA 6、多問 3、workflow 錯 1 |

## 被攔下的 11 個回合

| session | 組 | S 的判定 | menu 的判定與問題 | C 問了什麼 |
|---|---|---|---|---|
| W01 | U | DO（錯） | ASK／condition：file | 事實：「What does the named file hold?」 |
| W28 | U | DO（錯） | ASK／condition：file | 事實：同上 |
| W33 | U | DO（錯） | ASK／condition：file | 事實：同上 |
| W14 | U | DO（錯） | ASK／requirement | 結果 |
| W08 | K1 | DO（workflow 錯） | ASK／requirement | 結果 |
| W26 | V | DO（錯） | CLARIFY／result_open | 結果 |
| W11 | K1 | DO（對） | ASK／requirement | 結果（誤報） |
| W16 | K1，DRAGON | DO（對） | ASK／intent：artifact | 結果（誤報） |
| W34 | K1，DRAGON | DO（對） | ASK／intent：artifact | 結果（誤報） |
| W23 | K2，DRAGON | DECLINE（對） | ASK／intent：artifact | 結果（誤報） |
| W17 | K2 | DECLINE（對） | CLARIFY／result_open | 結果（誤報） |

- 以事實為來源的 3 個全部打在錯誤上。但問句是籠統的「What does the named file hold?（It is the file the workflow needs / It is the other one）」。對 W28、W33 而言，真正決定結果的是「那個檔案到底存不存在」，所以這個問句很可能問不到要害。
- 以結果為來源的 8 個：命中 3、誤報 5。誤報來自兩種情形：
  - DRAGON 請求：W16、W34、W23；
  - menu 只是想確認某個要求「是不是必要」（requirement 類問題）：W11。依宣告的規則，requirement 類不算事實疑問，所以落到「問結果」。
- 依宣告，Q（問句）與 T（第二回合）都沒有量，也沒有請標註者判斷。上表只是描述。

## 事後的觀察（不能用來通過任何門檻）

- **只看 menu 的 condition 類疑問，h9 與 h10 合計 5 個、全部命中**（h9 的 Z21、Z22，h10 的 W01、W28、W33），誤報 0。
  - 但只有 5 個，在 h10 上也達不到 D1（3 < 4）；
  - 問句本身很籠統（「What does the named file hold?」），能不能把人引到正確的第二回合沒有量過。
- **menu 讀取在 DRAGON 請求上不可靠。** 兩個題組中，S 判對的 DRAGON 請求有 5 個被 M 標出（h9 的 Z14、Z23，h10 的 W16、W23、W34）。若再試，要先查清楚 menu reader 為什麼讀不出 DRAGON 的結果類型。
- **requirement 類問題不是讀錯的訊號**（W08、W11、W14）。

## 建議

1. **M 依宣告撤回。** 不再以 h9、h10 的資料調整 M 的定義。
2. **整個讀錯偵測方向的總結：**
   - 程式能從已錄下的讀取中看見一部分讀錯：replay 上的 X2、Q2，h9 上的 M。
   - 但在沒看過的題目上：
     - X2、Q2 分不出「表達了不確定」與「不確定會影響結果」（h9 撤回）；
     - M 分不出「真的沒說要什麼」與「menu reader 讀不懂這類結果」（h10 撤回，DRAGON）。
   - 共同的原因：判斷「這個疑問會不會改變結果」需要合約知識。能自動算出這一點的，只有程式已經接到 typed 需求列上的疑問；而那些情形，凍結版本來就會問。
3. **若還要繼續**，唯一還有依據的方向是「menu 讀取的 condition 類疑問」（事後 5／5）。這需要：
   - 先宣告新的門檻，並在新的題組上試；
   - 改寫問句，讓它問到決定結果的那個事實。
   這是新的設計，需要你另外決定，我不建議現在就做。
4. **論文可以寫的**：讀題層的錯誤大多是自洽的。用不同形狀的讀取互相比對，在看過的資料上效果很好，但在新資料上，誤報都來自刻意放進的對照（無關的不確定、DRAGON 的結果類型）。這說明需要「含對照的新題組」才能驗證偵測器，replay 不夠。

## 檔案

| 檔案 | 內容 |
|---|---|
| `PLAN-M-SHADOW.md` | 計畫與門檻（建置前宣告） |
| `h10/` | brief、題目、覆核、標註 brief（未使用）、格式檢查、封存 |
| `.worktrees/netzoo-m-hold`（分支 `m-hold-pilot`，未 commit） | C：`interpretation/m_hold.py`、`m_hold_names.py`、`graph/m_hold_call.py`、`routing_planning.py` 的 hook、ASK／CLARIFY 回覆的開頭、`tests/test_m_hold.py`（12 個測試） |
| `mhold-build/` | B 門檻：`b-gates.txt`、replay 與 fixtures 的輸出、`b4-dryrun.txt`、`b4_dryrun.py` 在上一層 |
| `run_h10.py`、`round-h10smoke.json`、`round-h10.json`、`jobs-*.json`、`finished-*.json`、`turn1-h10.log` | runner 與執行紀錄 |
| `live/h10smoke/`、`live/h10/` | 每個 session 的 trace、session.json、cards |
| `score_h10.py`、`score-h10-turn1.txt`、`h10-gates-d.json` | 計分與 D 門檻 |

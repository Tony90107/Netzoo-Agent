# 第 2 項：跨階段共用的需求物件

日期：2026-10-05
對應：計畫第 2 項；診斷 F3（長訊息裁切）；兩個新發現的階段轉換遺失（見下方「重現」）。
範圍：確定性程式與 CLI 狀態，沒有改任何 prompt 或模型 schema，也沒有呼叫付費模型。

## 結論

每一回合在 classify 時，從**完整訊息**讀一次 `RequestRequirements`，之後各階段都讀同一份：

- **來源身分**：完整訊息的 SHA-256 與字數，以及 routing window 的字數和省略的字數。
- **使用者陳述的值**：輸入檔、輸出路徑、taxon、控制參數等。每一筆都記錄來源：
  - `this_turn`：附原文位置。
  - `earlier_turn`：由 continuation 以 typed state 帶來的、前一個請求中的陳述。
- **操作限制**：第 1 項的 `OperationAuthorization`，讀自完整訊息。
- **路由讀到的目標與未決條件**：routing 結束後填入，標明這是「解讀」，不是使用者原文。

各階段如何使用：

| 階段 | 以前讀什麼 | 現在 |
|---|---|---|
| Router 與所有模型呼叫 | 訊息最後 6,000 字 | 同一個 routing window：不超過預算就是全文；超過則保留開頭 2,000 字與結尾，並在文字中標明省略了多少 |
| 操作 gate | routing 文字 | 需求物件（完整訊息） |
| Planner | 只信任出現在本回合文字裡的路徑 | 也信任需求物件裡使用者陳述過的路徑；只由模型產生的路徑仍會被清除 |
| Plan Evaluator | 本回合文字 | 新的必要項目 `request_requirements` 檢查三件事：計畫對應同一個請求（SHA）；沒有替換任何陳述過的輸入或輸出；`evidence_provenance_contract` 對「provided」的定義與 Planner 相同 |
| CLI 接受建議的 workflow | 重新解析截成最後 4,000 字的 `prior_user_goal` | 改用前一回合的需求物件 |
| CLI `/execute` | 重新路由預覽文字，帶的 continuation 沒有任何值 | 帶入預覽回合需求物件中的陳述值 |
| CLI continuation 綁定 | `task[-6000:]` | 與 graph 相同的 routing window |

## 重現：修改前遺失了什麼

1. **長訊息（F3）**：一則 7,379 字的訊息，開頭是「Run PANDA with expression_file=… output_file=…」。
   - Router 看到的是「Background notes… Please go ahead.」，既不知道要跑 PANDA，也沒有任何檔案。
   - Planner 讀全文卻找得到。兩個階段依據不同的文字做決定。
2. **原請求陳述的輸出路徑**：目標中寫了 `output_file=outputs/my-net.tsv lioness_output=…`。
   - 接受建議後，continuation 回合的 Planner 把它們換成預設的 session 路徑。
   - 原因：路徑不在 continuation 的合成文字裡，被當成「router 猜的」而清除（`planning/evidence.py`）。
   - 確認回合接著把預設值標成 `provided`，原本陳述的路徑就此消失。
3. **原請求陳述的四個輸入檔**：目標寫明 study-b 的檔案，工作區同時有 study-a 和 study-b。
   - 接受建議後，系統忘了使用者指定的檔案，反過來問使用者要選哪一組 bundle。
4. **只修 Planner 不夠**：Plan Evaluator 的 `evidence_provenance_contract` 也只認本回合文字，會把帶過來的值判為「provided 但不在請求中」並拒絕計畫。結果會比修改前更糟：計畫被拒，而不是問 bundle。所以 Planner 和 Evaluator 必須用同一份定義。
5. **`/execute`**：會重新路由預覽回合的文字，但帶的 continuation 沒有任何值。所以由前一個請求帶來的檔案，在執行回合同樣會消失。

既有測試 `test_explicit_paths_and_outputs_survive_the_accepted_reply` 把路徑寫在**回覆**裡（本回合文字），所以沒有抓到 2 到 5。

## 修改的檔案

- `routing_window.py`（新）：head 加 tail 的 window。
- `contracts/requirements.py`（新）：`RequestRequirements`、`StatedValue`。
- `interpretation/request_requirements.py`（新）：
  - 建立需求物件（`read_request_requirements`）。
  - 填入路由結果（`with_routing`）。
  - 取出 continuation 要帶的值（`carried_parameters`）。
  - 陳述值與 continuation 使用同一組 parser。
- `llm.py`：新增 `latest_user_message`（全文）；`latest_user_task` 改回傳 routing window。只改這兩個函式，與 `06d5b48` 的 hunk 不重疊。
- `graph/routing_planning.py`、`graph/operation_authority.py`、`graph/execution.py`、`contracts/state.py`：建立、傳遞、讀取需求物件。
- `planning/builder.py`、`planning/context.py`、`planning/evidence.py`：Planner 信任需求物件中的陳述值。
- `evaluation/plan_review.py`、`evaluation/plan_rules.py`：新增 `request_requirements` 項目；provenance 規則與 Planner 使用同一份定義。
- `engine/state.py`、`engine/machine.py`、`cli/follow_up.py`：CLI 在接受 workflow 與 `/execute` 時帶入陳述值；binding 使用 routing window。
- `routing/request_scope.py`：一個否定詞涵蓋以 or、或、、 並列的多個操作。例如 "do not search the web or run anything"，以前只讀到搜尋。
- 測試：`tests/test_request_requirements.py`（19 項）；更新 `tests/test_operation_authorization.py`。

## 驗證

**測試**：完整測試 3,383 通過、35 跳過、0 失敗。

**驗收情境**

| 情境 | 結果 |
|---|---|
| 5,999 / 6,000 字 | 原文不動 |
| 6,001 / 6,100 / 60,000 字 | 不超過 6,000 字；保留開頭與結尾；省略字數精確 |
| 開頭禁止、結尾命令 | 禁止生效，不提升為執行 |
| 開頭的命令與檔案 | 進入 routing，hydration 取得檔案 |
| 原請求陳述的輸出，經接受與確認兩個回合 | 一路保留；計畫 approved |
| 原請求陳述 study-b、工作區有兩組 bundle | 直接使用 study-b，不再問 bundle；計畫 approved |
| 超過 4,000 字的目標，檔案寫在開頭 | continuation 仍帶到 |
| `/execute`（執行器以 mock 取代） | 執行回合使用 study-b，approved，並執行 `run_lioness_puma` |
| 沒有人陳述過的路徑 | 仍被清除，原有的防護不變 |
| Evaluator：替換了陳述過的輸出 | 拒絕 |
| Evaluator：計畫對應不同的請求 | 拒絕 |
| Evaluator：正常計畫 | approved |

**紀錄重播**
- 992 個已記錄的請求中，沒有一個超過 6,000 字。因此 routing window 對所有已記錄請求都沒有改變模型的輸入。
- 33 個已記錄的 ready 計畫中，`request_requirements` 檢查沒有誤判任何一個。

**模型看得到的內容**：prompt/schema fingerprint 不變（`e920bf3b5d57` / `743b2dd0d73a`）。只有超過 6,000 字的請求，模型讀到的文字會改變：由「最後 6,000 字」變為「開頭 + 結尾」。

## 限制

- `goal` 與 `open_conditions` 目前只是**紀錄**（routing 的解讀），還沒有任何階段根據它們做決定。這是第 3 到 5 項的工作：研究目的、方法適用性、跨階段一致性。
- 跨回合只帶「使用者陳述的值」。第 1 項的禁止條款只從本回合讀取：continuation 只用於本機 workflow，搜尋和下載不會在其中發生；而「現在不要跑」也會被使用者之後的接受或 `/execute` 取代。
- routing window 開頭固定保留 2,000 字。如果關鍵句子剛好落在被省略的中段，模型仍然看不到；不過需求物件中的陳述值與禁止條款不受影響，因為它們讀的是全文。
- 長訊息仍會讓 Planner 讀全文。另一個 session 正在修的 regex 效能問題（`_reverse_named_path`），與本項是分開的。

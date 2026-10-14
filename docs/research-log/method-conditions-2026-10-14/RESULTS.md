# M1：方法、參數與資料條件的可執行性檢查（2026-10-14）

交接計畫：`output/handoff/2026-10-14_下一個session交接計畫.md` §2。開發在 `.worktrees/netzoo-mc-cand`（基準 6c8c79f）。

## 做了什麼

| 步驟 | 內容 | 位置 |
|---|---|---|
| Step 0 | 盤點既有規則，對應 7 個失敗 | `STEP0.md` |
| Step 1 | 單一來源的條件模組：控制項（名稱、型別、範圍、是否接通）、執行環境限制、最少樣本數、資料量上限，全部從既有常數讀取，不另存數值。原本寫在函式內的最少樣本數改成具名常數（LIONESS 的 `3` 原本有四處），行為不變。測試會找出每個檢查實際擋下的門檻並比對。 | `workflow_conditions.py`、`method_names.py`、`tests/test_workflow_conditions.py` |
| Step 2 | 能力檢查的每項需求加上有型別的欄位：指定方法（13 個 workflow、LIONESS、unregistered、none）、設定（`WORKFLOW.控制項` 或 unregistered，附數值原文）、樣本數、特徵數。m1a 後加上：每個控制項的說明（來自 yaml），以及請求層的指定方法與設定。 | `contracts/capability_check.py` |
| Step 3 | 判定全部由程式負責：原文必須在請求中，指定已註冊方法時原文必須提到它，數量必須是原文寫出的數字。之後才判斷：不在指定方法內、沒有該設定或數值超出範圍、執行環境不支援、樣本太少、超過資料量上限。第二意見與條件改判也遵守同一判定。 | `interpretation/method_conditions.py` |

呈現方式：
- 結果寫「not available here as asked」並附理由。
- 另一個方法只當替代提出（「an alternative, not …」）。
- 只因設定不能套用的 workflow，以「它自己的設定」提出，不算 full gap；run 會被擋下，等使用者確認。

## 驗證

1. **規則層單元測試**：6 個負例與配對正例，用固定的結構化輸入全部判對（`tests/test_method_conditions.py`）。
2. **離線重播**：用舊程式（3529927）與新程式重建 1,338 個錄下的檢查，結果與回覆段落完全相同（`replay_checks.py`）。舊錄製沒有新欄位，所以不會觸發新規則。
3. **live 擷取測試**：見下。

### 第一輪 m1a（6348d26，24 題）

| 判準 | 結果 |
|---|---|
| 擷取正確 | 20/23 = 87%（MX05 由備援模型讀取，不計） |
| 負例判為不可做 | N36、N12、N13、N22 ✓；N11 ✗；MX05 未判定 |
| 新措辭 | F2 GENIE3 ✓、F3 兩個樣本 ✓、F1 PANDA alpha ✗ |
| 新增誤拒絕 | MX04 R1：回覆先說 GPU 不可用，接著又說「no workflow is offered」 |

錯在哪裡：
- **N11（擷取）**：「an L1 sparsity penalty of 0.1」被對應到 `OTTER.lam`，也就是共表現與 PPI 的權重。0.1 在 `lam` 的範圍內，所以 run 被核准。schema 只列出控制項名稱，沒有說明意義。→ 依使用者決定，每個控制項補上 registry 說明並放進契約。
- **F1（擷取）**：整個問題被歸為方法問題，沒有任何需求，設定無處附著，run 以「沒有要求任何結果」被核准。→ 依使用者決定，加請求層的指定方法與設定。
- **MX18 R2（規則）**：「LIONESS-OTTER」被讀成 LIONESS 家族。→ 若原文的 LIONESS 版本對應的 workflow 沒有註冊 LIONESS 版本，改判為 unregistered。
- **MX04（呈現）**：→ 結果無法對應時，提出 workflow 自己的設定作為替代。
- **預算**：M1 讓檢查的輸入多約 2.0k token，重讀多約 1.8k。檢查自己用到額外額度時，原本會把整個回合標成已用完，接在後面的 study purpose 與 data facts 因此被擋。→ 額外額度由 8k 提高到 12k；讀取類呼叫改用它們實際得到的預算來記帳。
- **K09（M2）**：第 1 回合「GPU」被擋下並提出替代，這是正確的。第 2 回合「Never mind the GPU - CPU is fine」被讀成不是 run 請求，結果給了說明而沒有排 run。沒有被拒絕，但 run 沒有接上。這屬於 M2 的多輪 run 狀態問題。

### 第二輪 m1b（2b9989a，26 題）

26 題都由主模型完成能力檢查，沒有 provisional 或 unavailable。

| 判準 | 結果 |
|---|---|
| 擷取正確 | **24/26 = 92.3%** ✓。錯的兩題：N12 把「LIONESS-style」讀成 LIONESS 家族；K09 第 2 回合從「Never mind the GPU」讀出 GPU |
| 負例判為不可做 | N11 ✓（擋下 run）、N36 ✓、N13 ✓、N22 ✓、MX05 R2 ✓；**N12 ✗**（第二意見判給 LIONESS-PANDA） |
| 新措辭 | F1 ✓（擋下 run）、F2 ✓、F3 ✓、F6 ✓（擋下 run）；F4、F5 正例維持可做並排入 run |
| 其他混合題 | MX18 R2 ✓、MX04 R2 ✓（回覆提出 OTTER 用自己的設定） |
| 新增誤拒絕 | **MX05 R1**：沒有任何需求被判給「fit GIRAFFE」，第二意見又因為 lambda 先把 GIRAFFE 排除，結果判為 full gap。**K09 第 2 回合**：因為讀到 GPU，判成不可做 |
| 正例 | K06、P19、P20、P09、MX18 R1、N36P、P12（lambda 0.05、100 iterations）、P21、P33、K10、P17、P10、F4、F5 都維持可做 |

P21 這輪沒有排 run，是因為 gpt-4o-mini 路由把意圖讀成「answer」。路由看不到能力檢查的契約，所以這不是 M1 造成的；回覆仍提出 BONOBO。

m1b 後的程式修正（328cab4，都用 m1b 自己錄下的讀取離線驗證過）：
- **N12**：判斷 LIONESS 版本時，指定方法的原文和需求原文一起看。只有沒有每樣本結果的 workflow 能當基底，所以「LIONESS or BONOBO」不會被誤判。重建後判為不可做，第二意見不再判給 LIONESS-PANDA。
- **K09**：只有一項需求時，合併需求層與請求層的設定，同一個控制項以原文最後出現的值為準。重建後判為可做。
- **MX05**：只因設定被排除的 workflow，仍交給第二意見問；若判為 all，以「它自己的設定」提出。
- 離線重播：1,338 個舊錄製仍 0 差異；全部測試 3698 通過。

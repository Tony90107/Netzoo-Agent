# 修補 A：讓錯的讀取凌駕正確資訊的規則（2026-10-24，寫程式前宣告）

起因：錯誤歸因（[attribution/ATTRIBUTION.md](attribution/ATTRIBUTION.md)）找出四種邊界型態。型態 4（只有備援讀取時暫停）已由修補 B 處理；本輪處理型態 1–3。使用者要求先宣告設計與門檻，用 replay 與單元測試驗證，不跑 live。

## 調查結果（不呼叫模型）

### 型態 1：目標讀取凌駕正確的需求列（9 筆）

依 `goal_unclear`（`interpretation/core_decision.py`）觸發的分支，分成兩類：

| 類別 | 筆數 | 情形 | 規則 |
|---|---|---|---|
| 1a | 5 | `goal=result_named`，但目標引用的原文對不上任何需求列。例如目標引用「the network」或輸出檔那一句，而需求列已經正確對到使用者點名的 workflow：J03、H21（PANDA）、J13（LIONESS-PUMA）。或者需求列已是程式建好的待問事實：H39（兩種結果擇一）、C11（整體或每樣本） | 「result_named 而且沒有重疊 → 目標不明」 |
| 1b | 4 | `goal=purpose_only`，但需求列已是程式建好的待問事實，例如 J27（特徵數 600 或 6000）、C34×2（兩種結果擇一）；或者需求列已有結果，例如 C36 | 「purpose_only → 目標不明」 |

金標：J03、J13、H21 是 DO；其餘 6 筆是 ASK。phase 5c 已規定：請求原文列出兩個以上選項的結果事實要 ASK，不是 CLARIFY。

這兩條規則來自 phase 1（`ae98f595`）：請求沒有說出任何結果時，先問目標。它們沒有考慮另一種情形：另一份讀取（需求列）已經用程式核實過使用者要什麼。

### 型態 2：不確定只寫在最上層 unknowns（4 筆）是錄製的產物

- 4 筆都來自 p0、p1 兩輪的錄製（C50×2、C20），那時還沒有 fact agent（phase 2 才加入）。
- 從 p2 起的每一份錄製（p2、p2b、p3、p4b、p4c、p5、p5r、g4o1、g4o2）共 16 份，C50、C20 全部由 fact agent 問對（ASK）。
- 這 4 份讀取的 unknowns 確實接到了需求列，`resolve_unknowns` 也跑過；只是固定維度的兩個值（continuous／binary、somatic／germline）對這些 workflow 給出相同的結果，程式無從追問。這類事實本來就由 fact agent 處理。
- 型態 2 列出的 C24，錯誤其實在目標讀取，不在 unknowns。

**live 的殘留是 h7 S16**（第 1、2 輪都錯）：

- 請求：「Run BONOBO … I centred every gene myself, but I can't remember whether I log-transformed the values first.」
- fact agent 兩輪都提出「Did you log-transform the values?」，user words 就是那句原文，contract 引用的是 BONOBO 的 log_transformed 宣告。
- 規則 R1 拒絕了它，理由是「the check did not read these words as the user being unsure」。capability check 整句沒讀：沒有需求列，也沒有 unknown。
- 正確的提問因此被一份「漏讀」的讀取否決，屬於同一類問題，所以列為 A2′。

### 型態 3：fact agent 被預算擋下

- **h4 的 3 筆（M01、M36、M43）是舊設定的產物：**
  - 錄製於 10-19。當時 fact check 只有回合預算（30,000），沒有 reading allowance；
  - 主要 check 還是 nemotron，推理 token 讓耗用達 57,000–63,000。
  - 今天 fact check 已有 allowance，P5 live 中 fact check 前的耗用最多約 45,000。
- **今天的 live 仍會發生，只在 M09。** P5 兩輪（A、D、E、E′）中，預算擋下而判 UNCHECKED 的回合有 5 個，全是 M09：A 第 3 輪、D 第 3 輪、E 第 1 輪、E′ 第 2 與第 3 輪。
- **原因是同一條規則：** 可選的呼叫在預算預檢時被擋下，就把整個回合標成用完（`usage.budget_exhausted = True`）。
  - 可選的呼叫包括 selection_conditions、semantic_discriminator、intent_router、study_purpose、data_facts、second opinion 等 11 處。
  - 必要的兩次讀取看到這個旗標就不呼叫：capability check（`request_capability_check`、`with_reading_allowance`）和 fact check（`request_fact_check`）。
  - 但實際耗用還遠低於上限：M09 E 第 1 輪耗用 26,760／30,000，E′ 第 3 輪 42,645／60,000。被擋的只是「預估」，不是真的用完。
- study_purpose 和 data_facts 在 10-21 已改成「保留了 fact 讀取時，被擋下不標用完」；second opinion 與 routing 階段的呼叫沒有改。

## 要做什麼

依 A3 → A1 → A2′ 的順序，一次做一項、各自量測，最後再量合計。

**A3（預算）：必要的讀取依「實際耗用」判斷回合是否用完，不看預估被擋的旗標。**

- 新增一個判斷：回合的實際耗用（`usage.total_tokens`）是否已達某個預算。
- 用在三處，取代 `usage.budget_exhausted`：
  - `with_reading_allowance`：實際耗用未達回合預算，就給 allowance。Log 394 的「已用完的回合不再加碼」照舊，只是「用完」改指實際耗用。
  - `request_capability_check`：實際耗用已達回合預算才回 `blocked`。
  - `request_fact_check`：實際耗用已達 allowance 後的預算才回 `blocked`。
- 每一次呼叫仍各自做預檢，所以每回合的上限（回合預算加 allowance，60,000）不變。
- 可選呼叫被擋時仍會設旗標，其他可選呼叫照舊受它限制；本項只讓兩次必要讀取不再被它擋住。

**A1（目標）：需求列已核實的結果，不被目標讀取推翻。**

在 `goal_unclear` 裡，`method_choice` 與「目標點名兩個以上方法」兩條規則照舊，而且先判。之後，只要有一個需求列是「錨定」的，就不因 1a、1b 兩條規則判為目標不明。錨定指以下其中一種，都由程式核實：

1. **點名的方法已被採信**：
   - 需求列的 `method.named` 是一個已登錄的 workflow；
   - 其 `named_quote` 在請求原文中，且 `workflows_in(named_quote)` 認得這個名字；
   - 需求列的狀態是 available、with_step 或 partial，而且 `delivered_by` 裡有這個 workflow 的項目。
2. **程式建好的待問事實**：
   - 需求列是 needs_fact，`unknown_quote` 在請求原文中；
   - `outcomes` 至少有兩組不同的結果，而且至少一組不是空的。

不屬於錨定、維持原判的情形：

- C36（需求列被採信給兩個 workflow，沒有點名，也沒有待問事實）；
- 沒點名也沒待問事實的需求列；
- outcomes 都相同的 needs_fact；
- 點名但沒被採信的方法。

`goal_unclear` 另外用在三處，跟著一起改變，行為一致：`_failed_closed` 的防護、fact agent 的「目標不明就不問」、ROUND-21 的 goal read。

**A2′（宣告的疑問）：被漏讀的必要宣告，fact agent 的提問可以由程式作證。**

R1 原本要求 capability check 把同一段原文讀成「使用者不確定」。新增一條替代的作證，限定在 workflow 的**必要宣告**：

- 必要宣告來自合約，由 `judgment_defaults.required_settings` 讀出，例如 BONOBO 的 log_transformed、centered。
- 使用者決定 2026-10-19 (a)：必要宣告沒給時要問，不能假設。

替代作證的條件，全部由程式判斷：

1. 提案的 workflow 有必要宣告；
2. 提案的 user words 在請求原文中，而且含有該宣告控制項自己的名稱。比對方式和 `control_boolean_value` 一樣，從控制項名稱推出，不用詞表；
3. 程式從那段原文讀不出確定的值（`control_boolean_value` 回 None）。像「I centred every gene myself」讀得出 True，就不問；
4. 提案的 contract 引用含有該控制項名稱；
5. 其餘 R2–R7 照舊。

---

replay 原本只沿用錄下的 fact check 結果。這裡加一步：錄下的提案中，只因 R1 作證被拒、而且符合上述條件的，用今天的 `kept_facts` 重新判一次。

- 沒有 A2′ 的程式時，這一步不做任何事（ImportError），所以基準不變。

## 門檻

**共同門檻**（每一項做完都量）：

1. **單元測試**，每項各自的正例與反例：
   - A3：
     - 可選呼叫被擋（旗標已設）但實際耗用未達預算，capability check 與 fact check 仍會呼叫；
     - 實際耗用已達回合預算，capability check 回 `blocked`（Log 394 不變）；
     - 實際耗用已達 allowance 後的預算，fact check 回 `blocked`；
     - 預檢仍會擋下超過上限的呼叫。
   - A1：
     - 1a 的點名、1a 的待問事實、1b 的待問事實三種情形，都不判目標不明；
     - 以下情形仍判目標不明：
       - C36 的形狀；
       - 只有未點名、未錨定的需求列；
       - outcomes 相同的 needs_fact；
       - 點名但 not_available；
       - `method_choice`；
       - 目標點名兩個方法而且沒有結果列。
   - A2′：
     - S16 的提案被保留；
     - 會被拒絕的情形：
       - 原文讀得出確定值（「I centred every gene」「I did not log-transform」）；
       - user words 不含控制項名稱（S16 的 centering 提案）；
       - workflow 沒有必要宣告；
       - contract 引用不含控制項名稱。
2. **完整 `tests/` 通過**，不新增略過項。基準：4,997 passed、51 skipped。
3. **Fixtures**：`fixtures.py check` 的 F01–F09 不變，有改變就逐筆列出原因。
4. **理由**：`layers.py` 不得新增說錯的理由，也不得出現沒附理由的回覆。

**各項門檻：**

| 項目 | 標準 B2 replay（614/757、FA 15、FR 5、MA 64、問錯種類 18、多問 11、UNCHECKED 30） | 其他 |
|---|---|---|
| A3 | **判定 0 改變**：replay 依錄製事件重建，不重新做預算預檢 | **trace 計算**：在 P5 與 live-check 的錄製 trace 上，依錄下的耗用與輸入大小重算預檢，列出 A3 改變「必要讀取會不會呼叫」的每一個回合。預期只有 M09 的 5 個回合，而且每一個都要通過自己的預檢。其他回合有任何改變，就逐一列出並說明 |
| A1 | 逐筆列出改變。**新增 FA 為 0**；不得有任何一筆是 DO 跳過了目標原文點名的結果；判對淨增加大於 0；每個 BREAK 列出由我判斷。預期上述 9 筆中 8 筆改變（C36 不變） | 現行設定 replay：新增 FA 為 0 |
| A2′ | 逐筆列出改變。**新增 FA 為 0**；多問（無必要追問）不增加；每個 BREAK 列出 | S16：用 h7 兩輪錄下的提案離線重跑 `kept_facts`，E 與 E′ 都要保留 log transform 的提問；h7 其他 session 錄下的提案，列出所有被新規則保留的提案並逐筆判斷是否多問 |

**採用規則**：

- 每項各自判斷：門檻全過才保留，任何一項沒過就撤回該項，其他項照舊。
- 最後量三項合計，在標準與現行設定兩種 replay 上報告。

## 不做的事

- 不改 prompt 或讀取的 schema。
- 不跑 live。A3 與 A2′ 在 live 的實際效果，要等下一次 live 才看得到；本輪只用錄製的 trace 推算。
- 不改型態 2 的固定維度：它在今天的系統已由 fact agent 處理。

## 限制

- replay 不能重新呼叫 fact agent。A1 讓目標變明確後，live 會多跑一次 fact agent，replay 只能沿用錄下的結果；錄製時目標被判不明的，沒有 fact agent 的紀錄。
- A3 的 trace 計算是推算：真的呼叫時，輸出長度可能不同。
- 這三項都是「讓另一份正確的讀取被採用」。它們能救的，只限於另一份讀取是對的情形，不會提高讀取本身的正確率。

## 實作中的更正（2026-10-24，宣告後補記，上文不改）

1. **A3 的「實際耗用」**：
   - 實作為「旗標已設，而且耗用已達上一次記帳時所給的預算」（`spent`）。
     - 上一次記帳的預算在 check 之前是回合預算，check 之後是 allowance 後的預算。
     - 只看回合預算的版本，會讓 check 之後（耗用常已超過 30,000）的 fact check 拿不到 allowance。
   - 上文「可選呼叫被擋時仍會設旗標，其他可選呼叫照舊受它限制」不精確：
     - `with_reading_allowance` 是共用的，所以 study purpose、data facts、second opinion、condition check 在被擋之後也會拿回 allowance；
     - 會自己檢查旗標的呼叫照舊受限：goal read、settings read、contract veto、hybrid gate、re-read。
   - 這個更正是在單元測試時發現的（`test_graph_skips_llm_when_task_budget_cannot_cover_router`），在 replay 量測之前。
2. **A1 宣告版沒過我的 BREAK 判斷**：
   - 3 個 BREAK 都是「COBRA or CONDOR」這類方法二選一的請求被 DO 執行。
   - A1′ 加了「同一句提到另一個已登錄方法並以 or／either／versus 連接，或錨定的需求列點名兩個不同方法」就不算錨定。
   - **這是看過 replay 之後的事後修改**，詳見 RESULTS-A。
3. **A2′ 的條件 3 在量測前已改**：
   - 單元測試發現，`control_boolean_value` 會把 S16 的「I can't remember whether I log-transformed」讀成 True（沒有否定詞），無法區分疑問與陳述。
   - 因此改成：使用者原文、agent 的問題、contract 引用三者都點名同一個宣告控制項。原文與問題用字首比對，「log-transform」對應 log_transformed。
   - 量測後 A2′ 仍沒過門檻，已撤回。

# 修補 A 的結果（2026-10-24，$0，沒有跑 live）

設計與門檻見 [ROUND-A.md](ROUND-A.md)，實作中的更正補記在它的最後一節。

## 結論

| 項目 | 結果 | replay 判對（/757） | 新增 FA |
|---|---|---|---|
| A3 預算 | **保留** | 614 → 614（replay 不重做預算預檢，0 改變） | 0 |
| A1 目標（宣告版） | **撤回**：3 個 BREAK，都是方法二選一的提問被當成 DO 執行 | 614 → 619 | 0 |
| A1′ 目標（事後修改版） | **候選**（使用者決定，2026-10-24）：8 FIX、0 BREAK；在新的 held-out 或下一次 live 確認後才算採用 | 614 → **622** | 0 |
| A2′ 宣告的疑問 | **撤回**：0 FIX、2 BREAK，多問 8 → 10 | 622 → 620 | 0 |

- 合計（A3 + A1′）：
  - 標準 replay：**614 → 622**，FA 15 → 15，MA 64 → 64，問錯種類 18 → 13，多問 11 → 8；
  - 現行設定 replay：**622 → 630**，FA、FR、MA 都不變。
- 型態 2 的 4 筆是錄製的產物，不需要改程式（見 ROUND-A）。它在 live 的殘留是 h7 S16，原本嘗試以 A2′ 處理，但 A2′ 沒過門檻。
- **A1′ 是看過 replay 之後才加的修改**，所以 622 這個數字不是獨立的驗證。
- 使用者決定（2026-10-24）：A1′ 先留在程式裡當候選，在新的 held-out 或下一次 live 確認後才算採用。確認條件見本文最後一節，在看到任何新資料之前宣告。

## A3：被擋的可選呼叫不再把回合標成用完

**改了什麼**：

- `graph/capability_check_call.py` 新增 `spent(usage)`：旗標已設，而且實際耗用已達上一次記帳時所給的預算。
- 三處改用 `spent`，不再看旗標：
  - `with_reading_allowance`；
  - `request_capability_check` 的兩處；
  - `graph/fact_check_call.py` 的 `request_fact_check`。

**門檻**：

| 門檻 | 結果 |
|---|---|
| 單元測試（`tests/test_a3_required_reads.py`，10 個） | 通過：可選呼叫被擋後，check 帶著 allowance 照常呼叫；second opinion 被擋後，fact check 照常呼叫；routing 真的用完回合預算時 check 仍被擋（Log 394）；fact check 自己的預檢仍會擋下超出上限的呼叫 |
| 既有測試 | 3 個測試原本用「只設旗標、沒有耗用」代表用完，改成真的耗用。`test_graph_skips_llm_when_task_budget_cannot_cover_router` 改為斷言 router 與 routing 階段的呼叫都沒有跑：1 token 預算的回合，現在 check 會用自己的 allowance 嘗試一次，但最後仍是 UNCHECKED，沒有選任何 workflow |
| 標準 replay | **0 改變**（`pA3-compare.txt`） |
| trace 計算（`a3_trace.py`） | P5 與 live-check 的錄製中，必要讀取因旗標而沒跑的回合**正好是 M09 的 5 個**，A3 之後每一個都通過自己的預檢（見下表）。沒有其他回合改變 |

| session | 回合 | 沒跑的讀取 | 被擋的可選呼叫 | 當時耗用 | A3 之後的預估 | 上限 |
|---|---|---|---|---|---|---|
| p5r1 M09 A | t3 | capability check | selection_conditions | 22,725 | 48,633 | 58,500 |
| p5r1 M09 D | t3 | fact check | second opinion | 44,653 | 47,833 | 58,500 |
| p5r1 M09 E | t1 | capability check | semantic_discriminator | 26,760 | 52,668 | 58,500 |
| p5r2 M09 E′ | t2 | capability check | selection_conditions | 22,941 | 48,849 | 58,500 |
| p5r2 M09 E′ | t3 | fact check | second opinion | 42,645 | 45,825 | 58,500 |

- **限制**：p5r1 M09 E 的 t1 連 intent router 也被擋，routing 判為 budget_fallback。check 跑了也只能說出確認的缺口或不明的目標，這一回合很可能仍是 UNCHECKED。
- 另外 4 個回合能不能判對，要等 live。

## A1：需求列已核實的結果不被目標讀取推翻

### 宣告版（撤回）

標準 replay：8 FIX、3 BREAK、7 個沒有金標的改變；614 → 619；FA 不變；MA 64 → 67。

| BREAK | 請求 | 改變 |
|---|---|---|
| p3 C10 | 「Should I be using COBRA or CONDOR on our lupus nephritis cohort? … not sure what either would give me」 | CLARIFY → DO（COBRA 與 CONDOR 都排了 run） |
| p3 C26 | 「Is SAMBAR the right thing to run, or one of the network methods like PANDA? I'm open to whatever …」 | CLARIFY → DO（SAMBAR、PANDA） |
| p5 C26 | 同上 | CLARIFY → DO + partial（SAMBAR） |

我的判斷：

- 使用者只是問該用哪一個，宣告版卻把點名的方法當成目標而排了 run。
- 門檻的字面都過了：新增 FA 為 0，也沒有 DO 跳過目標原文點名的結果。
- 但這是「替使用者做他沒要求的分析」，所以判為**不可採用**，依規則撤回。

沒有金標的 7 筆裡：

- h5 Q44 兩筆（「We'd like to try OTTER or maybe GIRAFFE …」→ DO OTTER）也是同一類問題；
- h6 R10 兩筆、h6 R39 是合理的 DO；
- h4smoke M38 見下文。

### A1′（事後修改，候選）

在宣告版之上加兩條排除，都只用程式判斷，或沿用 `method_choice` 既有的標記：

- 點名方法的那一句，若也提到另一個已登錄的方法，並以 or／either／versus／vs 連接，就是使用者在問選擇，不算錨定（`_offered`）。
  - or／either／versus／vs 這組標記與 `goal_evidence.method_choice` 共用同一個常數 `ALTERNATIVE`，不是新加的詞表。
- 錨定的需求列若點名兩個以上不同的方法，也不算（`_anchors`）。

標準 replay（`pA1p-compare.txt`）：**8 FIX、0 BREAK**，判對 614 → 622，FA、FR、MA、UNCHECKED 都不變，問錯種類 18 → 13，多問 11 → 8。

| FIX | 改變 |
|---|---|
| h2 J03、h1 H21、h2 J13 | CLARIFY → DO：點名 PANDA、LIONESS-PUMA |
| h1 H39、g4o2 C11、h2 J27、p4c C34、p5r C34 | CLARIFY → ASK：問程式建好的待問事實 |

- 沒改的：p5r C36。它的需求列被採信給 LIONESS-PANDA 與 GIRAFFE 兩個 workflow，沒有點名，也沒有待問事實，依設計維持原判。
- 沒有金標的改變剩 4 筆：
  - h6 R10 兩筆、h6 R39：DO，是合理的請求；
  - h4smoke M38（「either 8 or 15 tumours, and I'm not sure which version」）：CLARIFY → DO。
    - 這份錄製走的是 closed-menu 實驗的 contract veto 路徑，沒有 fact agent 的紀錄，所以 replay 只能判 DO。
    - 同一題的另外兩份錄製有 fact agent：h4main 問了「8 or 15」，replay 判 ASK；h4smoke2 也是 ASK。
    - live 時目標已明確，fact agent 會照常執行。
- 現行設定 replay（`pA1p-current-compare.txt`）：同樣的 8 FIX、0 BREAK，622 → 630，沒有新增 FA。
- 單元測試（`tests/test_a1_goal_anchor.py`，15 個）：
  - 宣告版的正例與反例；
  - A1′ 的 C10、C26、Q44 形狀判為目標不明；
  - J03 形狀（「from yesterday's COBRA run」是輸入來源，不是選項）仍算錨定。

**要使用者知道的**：

- A1′ 的兩條排除，是看了宣告版的 BREAK 之後才加的。
- replay 的 757 份讀取全部都看過了，所以 0 BREAK 不是獨立驗證。
- 依過去的做法（設計中途不改），這一版應在新的 held-out 或下一次 live 上確認，才算採用。

## A2′：被漏讀的必要宣告（撤回）

- **設計**（量測前已依單元測試更正，見 ROUND-A 最後一節）：
  - 對有必要宣告的 workflow（BONOBO 的 log_transformed、centered），fact agent 的提問若同時滿足兩點，就可以代替 capability check 為 R1 作證：
    - 使用者原文、問題、contract 引用三者點名同一個控制項；
    - R4 沒有把那段原文讀成已陳述。
- **h7**（`a2_h7.py`）：
  - 167 個「check 沒作證」而被 R1 拒絕的提案中，新規則只保留 S16 的「Did you log-transform the values?」，也就是 A、E、E′ 三個 session，都是目標；
  - 其他 h7 session 沒有被影響。
- **標準 replay**（`pA2-compare.txt`）：0 FIX、2 BREAK、1 個沒有金標的改變，判對 622 → 620，多問 8 → 10：

  | 讀取 | 使用者原文 | 改變 |
  |---|---|---|
  | h3 L38 | 「Expression is already log2-transformed and centered per gene.」 | DO → ASK「Can you confirm that the expression is log2-transformed and centered?」 |
  | p5r C40 | 「(27 multiple sclerosis lesion samples; log2-transformed and centered per gene)」 | DO → ASK |
  | h2hyb J30 | 「log2 CPM, centered per gene」 | DO → ASK |

- **結論**：
  - 這三筆使用者都已經說了，fact agent 仍要求確認；capability check 正確地沒有把它們讀成不確定。
  - 程式沒辦法只靠用字區分「不確定」和「已說明」，這正是 R1 要求另一份讀取作證的原因。
  - 依門檻「多問不增加」撤回。程式與測試存在 `a2-withdrawn.patch`。
- S16 因此仍是讀題層的錯誤：capability check 整句沒讀。

## 共同門檻（A3 + A1′）

| 門檻 | 結果 |
|---|---|
| 完整 `tests/` | **5,022 passed、51 skipped、0 failed**（基準 4,997，加上 A3 的 10 個與 A1 的 15 個；略過項不變） |
| Fixtures（`fixtures-A.txt`） | 與 P5 修正後（`fixtures-p5fix.txt`）完全相同；與基準不同的仍是 P1／P2 預期改變的 F03、F04、F05、F07、F08、F09 |
| 理由（`layers-A.txt`，208 則） | 說錯 0、誤導 2、說對 91、屬實非主因 29、第二層 86、沒附理由 0，與 P5 修正後相同 |

## 檔案

| 檔案 | 內容 |
|---|---|
| `pA3.json`、`pA3-compare.txt` | A3 的標準 replay |
| `a3_trace.py` | A3 的 trace 計算 |
| `pA1-declared.json`、`pA1-declared-compare.txt` | A1 宣告版（撤回）的標準 replay |
| `pA1p.json`、`pA1p-compare.txt`、`pA1p-current.json`、`pA1p-current-compare.txt` | A1′ 的標準與現行設定 replay（也是 A3 + A1′ 的合計） |
| `pA2.json`、`pA2-compare.txt`、`a2_h7.py`、`a2-withdrawn.patch` | A2′（撤回）的量測與程式 |
| `fixtures-A.txt`、`replies-A.json`、`layers-A.txt` | 共同門檻 |

## A1′ 的確認條件（2026-10-24 宣告，尚未看到任何新資料）

A1′ 要在**沒看過的請求**上確認：新的 held-out，或下一次 live。只用 replay 不算確認。

1. **比較方式**：同一批讀取，分別用「A3 加 A1′」與「只有 A3」判定，逐筆列出改變。live 可以用同一份錄製的讀取離線重判，不必跑兩次。
2. **題目至少要包含三類**：
   - A1′ 要修的兩種形狀：
     - 點名一個方法，但目標讀取引用了別的原文；
     - 目標讀成 purpose_only，但需求列已有程式建好的待問事實。
   - A1′ 要擋下的形狀：同一句以 or／either／versus 提出兩個方法（「X or Y?」）。
   - 對照：目標本來就不明確、沒點名方法也沒待問事實的請求。
3. **通過條件**：
   - 新增 FA 為 0；
   - 「X or Y?」類的請求沒有任何一筆變成 DO；
   - 改變中判對的筆數多於判錯的筆數；
   - 每一筆判錯的改變都列出，由使用者判斷。
4. **沒過**：撤回 A1′，只留 A3。改動只在 `interpretation/core_decision.py` 的 `_anchored`、`_offered`、`_anchors`，加上 `goal_unclear` 裡的一行，以及 `goal_evidence.ALTERNATIVE`。

## A1′ 確認回合的結果（2026-10-24）

見 [RESULTS-A1C.md](RESULTS-A1C.md)。

- h8 共 36 份讀取，A1′ 只改變 2 份：1 份判對，1 份兩組都錯。新增 FA 為 0，沒說結果的選擇題變成 DO 的也是 0。
- 改變的讀取少於宣告的 4 份，所以**案例不足**。A1′ 維持候選。

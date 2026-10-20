# 嚴格度稽核：現行系統在 h1–h4 的判定（2026-10-20）

計畫：`collab/ROUND-01-PLAN.md`。離線、唯讀、$0，沒有呼叫任何模型，也沒有修改程式。

範圍：四組全新盲寫題 h1–h4，共 192 題，計分用的是現行系統那一組（h1 `live`，h2–h4 `main`）。這些 session 跑的程式是 `netzoo-core-p0-run` @ `54d08ce7`；下文的 `file:line` 都指那份程式。

- `audit.py`：讀取 gold、計分結果、每個 session 的 trace，再合併 `labels.json`，輸出 `audit.json`。執行 `python3 -I audit.py`，兩次輸出逐位元相同。
- `labels.json`：我依 trace 逐題標的原因。標記者只有我一人；trace 看不出原因的題目標為 `confidence: medium`。
- 答對的非 DO 題（113 題）依 gold 類別給預設標記。其中 DECLINE 的拒絕行另外用程式檢查有沒有合約理由，沒有理由的 3 題再逐題手標。

## 結論

- **「放寬或收緊」這個軸不對，計畫的假設成立。**
  - 沒有任何一個錯誤是「沒說的型別欄位被當成不能做」：程式對沒說的值一律不判（`method_fitting`、`_fitting`、`setting_issue`、`data_issue` 的 docstring 和程式碼都是如此）。
  - 真正把事情變成「不能做」的，是**沒被歸給任何 workflow 的句子**，以及兩條 CLARIFY 規則。
- **錯誤偏向太寬鬆，不是太嚴格。** 38 個錯中：
  - 太寬鬆 15 個；
  - 檢查沒跑完 7 個；
  - 太嚴格 9 個；
  - 其他 7 個。
- **全面放寬（R）和全面收緊（T）都不划算：**
  - R 修 7 題，壞 3 題正確的拒絕；
  - T 若嚴格解讀「明說」，約 31 題正確的 DO 會多問一題。
- **四個針對性修法**（A–D）合計可修 27/38，被波及的正確題最多 2 題，詳見 Q5。

## Q1 太嚴格的 9 個錯

| 代碼 | 數量 | 題號 | 說明 |
|---|---|---|---|
| S1 沒對到就算不能做 | 2 | M13、M23 | 描述句（「…should go through DRAGON.」「Launch LIONESS-DRAGON with …」）沒被歸給任何 workflow，被記為 not_available，結果變成部分執行。`capability_check.py:65-69` |
| S2 讀錯值 | 1 | H37 | 把要輸入的 PANDA 網路讀成要產出的東西，registry 判為 unsupported，直接拒絕，沒有任何合約原文。`core_decision.py:235` |
| S3 規則比合約嚴 | 4 | H21、J03、J13、J17 | H21、J03、J13：目標原文只抓到「the network」或輸出路徑，和唯一一個點名 PANDA 或 LIONESS-PUMA 的需求句沒有重疊，因此判成 CLARIFY（`core_decision.py:140-141`）。J17：「keep the normalization」解不成 true/false，布林值無法解析就算違反（`workflow_conditions.py:256-257`） |
| S4 多問 | 0 | | |
| S5 目標不清卻拒絕 | 2 | H46、J06 | H46：「finding groups」沒被歸給任何 workflow，整題判成缺口。J06：「PANDA or GIRAFFE」被讀成一個未註冊方法 |

S1 的兩題都是「沒被歸給任何 workflow 的句子」，不是「沒說的欄位」。沒有一題是沒說的型別欄位造成拒絕。

## Q2 答對的 DECLINE / ASK / CLARIFY（113 題）

| 欄位狀態 | 題數 | 判定 | R 會弄壞 | T 會弄壞 |
|---|---|---|---|---|
| F2：沒說，且會改變判定 | 40 | CLARIFY（vague） | 0 | 0 |
| F3：有說但不確定或矛盾 | 40 | ASK（ask） | 0 | 0 |
| F4：明說且違反合約 | 33 | DECLINE（dont） | **3：L17、M18、M20** | 0 |

這 33 個正確拒絕中：

- 30 個附有合約理由（limits、violations、sheet 條目）。
- L17、M18、M20 只是「沒對到任何 workflow」。這三題都是具體但清單外的交付物：突變矩陣建 TF 網路、differential modularity、預測模型。
- 若採 R「沒對到就不能擋」，這三題會變成追問。

## Q3 淨效果（R：沒說的欄位永不擋，F1 用預設、F2 追問；T：任何決定性欄位沒明說就問）

假設：欄位狀態本身讀對了。讀錯的值（S2、L1、L4）兩種政策都修不到。

| 類 | R 修 | R 壞 | T 修 | T 壞（狹義） |
|---|---|---|---|---|
| do | J17、M13、M23 | 0 | 0 | 0 |
| dont | 0 | L17、M18、M20 | 0 | 0 |
| ask | 0 | 0 | M01、M36 | 0 |
| vague | H46、J29、J32、M33 | 0 | H46、J29、J32、M33 | 0 |
| **合計** | **7** | **3（淨 +4）** | **6** | **0（淨 +6）** |

- T 的代價取決於「明說」怎麼定義：
  - 狹義：只看合約限制實際用到的數量與設定。41 個正確 DO 都有寫，代價是 0。
  - 廣義：連資料單位（bulk 或單細胞）都要明說。41 個正確 DO 中約 31 個沒寫 bulk，會多問一題。名單見 `audit.json` 的 `summary.tighten_broad_at_risk`，這是粗估。
- R 與 T 都不碰最大的兩類錯：部分承諾（L4，7 題）與檢查沒跑完（U1，7 題）。

## Q4 能產生 DECLINE、部分執行或 UNCHECKED 的路徑（T2 關卡清單）

**粗體**表示 F1/F2（沒說）可以走到「不能做」或擋住執行。

| # | 位置 | 觸發條件 | 可到達的狀態 | 例 |
|---|---|---|---|---|
| G1 | `core_decision.py:205-206` UNCHECKED routing_failed | routing 失敗、沒有任何候選 | 任何狀態（失敗或預算） | M33 |
| **G2** | `core_decision.py:207-208`；`run_check.py:64` | run 被擱置在 unread（有句子沒檢查到）或 unconfirmed | **F1**：一句沒對上的句子就能擋住執行 | J37 |
| G3 | `core_decision.py:229-230`；`contracts/capability_check.py:617-619` | 檢查屬於 provisional、unavailable 或 gap_unconfirmed | 任何狀態（失敗或預算） | H11、H33、L24、M43 |
| G4 | `core_decision.py:231-232`；`routing/method_rejections.py:30`；`concept_answers.py:566` | 字面規則（演算法組合、COBRA→PANDA） | F4 | 無 |
| **G5** | `core_decision.py:233-234`；`capability_check.py:373-377` full_gap | 所有結果列都是 not_available | **F1/F2**：經由 R1 的未歸屬列 | H46；正確：L17、M18、M20 |
| **G6** | `core_decision.py:235-236` routing_unsupported | 什麼都沒讀到、不是 run、registry 判 unsupported | **沒有正面證據** | H37 |
| G7 | `core_decision.py:241-242` all_results_not_available | 有讀到的列全部 not_available | 同 R1–R11 | J17 |
| G8 | `core_decision.py:246-251` DO partial | 部分列 not_available | 同 R1–R11 | M13、M23；L4 各題 |
| **R1** | `capability_check.py:65-69` `_status([])` | 某結果列沒被歸給任何 sheet 條目 | **F1/F2：沒對到就算不能做**（`apply_second_opinion` :940 只對 blank 列重看一次） | M13、M23、H46 |
| R2 | `capability_check.py:324-372` `_fitting` | 已讀的型別屬性排除條目；沒說的值放行（:341；scale 沒說不排除） | F4（屬性讀錯時是 S2） | J15 反向 |
| R3 | `method_conditions.py:104-140、240-252` | 明說的設定或數量超出限制；「沒說的不判」 | F4 | 正確：M07、H48、M08 |
| **R4** | `workflow_conditions.py:213-257` `setting_issue` | 未註冊或未接線的設定、超出範圍（F4）；**enum 或布林值解析不了（:247-249、:256-257）** | **F3 → 不能做** | J17 |
| R5 | `workflow_conditions.py:278-318` `combination_issues` | 明說的組合違反 | F4；漏洞見 D | 正確：J35、L28、M12；漏：H34、M40 |
| R6 | `count_alternatives.py:106-108` | 不確定數量的每個候選值都不行 | F3 且全部違反，等同 F4 | |
| R7 | `needed_facts.py:318-319` | 未知事實代入後都不可能 | F3 | |
| **R8** | `ruled_out.py:80-112`、`:41-60` | 使用者排除了某種輸入；且 **input_network 沒說時當成缺網路（:100-101）** | **F2**，但只在使用者另外排除過某種輸入時才觸發（:88-89） | 本組無 |
| R9 | `requirement_split.py:66-75、82-103、176-189` | 明說的結果形式、交付方式、同句條件被判違反 | F4 | 正確：J46、L44 |
| R10 | `capability_check.py:266-292` | 條件核對模型回答 violates | F4（由模型判） | H27 的 violation 列 |
| R11 | `graph/fact_check_call.py:85-94` | 舊式等待列沒有可歸屬的結果 | F2/F3（理論上） | 無 |
| R12 | `run_check.py:44-66`、`run_hold.py` | partial_gap、other_workflow、outside_step、gap 時擱置 run 並附拒絕行 | 同上游各列 | H40、L21、L09 |

**直接回答「沒填的欄位會不會擋住執行」：**

- 型別欄位不會，R2、R3、R5 都不判沒說的值。
- 會擋住的是三種情形：
  - **沒被歸屬的句子**：R1 → G5、G7、G8；
  - **讀不到東西**：G6；
  - **沒對上的句子擱置 run**：G2。
- 另有 R4（解析不了的值算違反）與 R8（沒說網路就當沒有）兩個較小的入口。

## Q5 前三個修法（依「修好的錯 − 被波及的正確題」排序）

| | 修法（設計變更） | 修好 | 被波及 | 單次雜訊題 |
|---|---|---|---|---|
| **A** | 需求列加上型別 `form`：交付物、run 指令、輸出路徑、描述或背景、對我們的提問。只有「交付物」能成為 not_available；run 指令與輸出路徑併入它所屬的交付物；描述句不計分 | **8**：H18、H40、J44、L13、L21（部分承諾 → 拒絕）；M13、M23（部分執行 → 全做）；L09（輸出檔不另算結果） | ≤2（低）：J40、M17 只有 run 句被歸屬，改後會退回 routed 或 run，判定預期不變 | J44 |
| **B** | 檢查與 fact agent 有保留的 token 額度，失敗或被擋時重試一次（程式規則，不是措辭） | **≤7**：H11、H33、J37、L24、M43（UNCHECKED）；M01、M36（fact agent 被擋，沒讀到不確定）。M01、M36 還要讀對才算修好 | 0（只增加成本） | J37 |
| **C** | CLARIFY 的優先順序：已讀到的決定性事實（needs_fact 列，或 fact agent 已接受的問題）先問；需求列自己點名「單一」註冊方法時，目標就算已說，不再要求目標原文與需求句重疊 | **6**：H21、J03、J13（多問 → DO）；H39、J27、H47（問錯種類 → ASK） | 0：5 個正確 CLARIFY 中有被歸屬列的（H05、J12、J16、M15、M28），沒有一列點名單一方法，也沒有 needs_fact 列 | J03、J13、J27 |

- **第四名 D**：合約加上可執行的輸入種類檢查，並修正設定的語意。
  - 輸入種類：CONDOR 不吃表現量矩陣；COBRA 的匯總產物不能交給 LIONESS-PANDA。
  - 設定語意：sparsify 的 confidence 值不等於 false（`workflow_conditions.py:298`）；「estimated」不等於已提供（`:285`）；布林值解析不了時，用預設或追問，不判違反（`:256-257`）。
  - 可修 6 題：H27、L48、M46、H34、M40、J17。正確的 CONDOR 題（J40、L35、M45）收的是邊表，仍然通過。
- **修不到的 11 題**：
  - 讀錯：H37、J06、J15、M48；
  - 限制沒讀到：L10、M25；
  - 開放選擇沒讀出：J29；
  - 「點名單一方法就算目標」規則：J32、M33；
  - 疑問交給輸入檢查：L40；
  - 未歸屬的模糊交付物：H46。
- A 要讓 H46 這類「有交付物、但對不到」的句子變成追問，又不能波及 L17、M18、M20，須另外的正面證據（sheet near-miss 條目），不在 A 的範圍。

## 不穩定（T3）

- 可對照的重跑只有兩種：
  - h2 `h2hyb`：與 `h2main` 程式相同，只多了預設關閉的閘門，扣除閘門改變的 J15、J28、J40；
  - h4 smoke：取否決前的 live 判定。
- h2 可對照的 9 個錯中，**7 個在重跑時答對**：J03、J06、J13、J17、J27、J37、J44。只有 J29、J32 兩次都錯；M25、M40 在 smoke 中也錯。
- h1、h3 沒有同程式的重跑，無法判斷是否不穩定。
- 預算：18 個 session 出現 `budget.blocked`（每輪 30,000 token 上限），其中 7 個答錯（39%）；沒被擋的 174 個 session 錯 31 個（18%）。

## 限制

- 原因由我一人依 trace 判斷，沒有第二位標記者，也沒有用模型輔助。
- R/T 的效果是推演，不是重跑。
- A–D 的「修好」是依 trace 推論；被波及的正確題只根據已記錄的需求列，沒有重新讀取。

# M2 Step 0：需求拆分、條件歸屬、多輪狀態、檔案綁定（2026-10-14，只讀盤點）

基準版本 54a59a6（M1 完成）。錄製資料來自 a24b（`.worktrees/netzoo-final-live`）以及 M1 的 m1a–m1c（`.worktrees/netzoo-mc-cand`）。多輪與檔案綁定由兩個只讀子代理調查，關鍵行已抽查。

## A. 需求拆分與條件歸屬（能力檢查）

| 代號 | 案例 | 錄製讀取 | 原因 | 修法 | 性質 |
|---|---|---|---|---|---|
| A1 | MX10（CONDOR 社群 + 允許重疊） | 需求「TF-gene communities」交給 CONDOR，但需求本身標成 several_groups，請求層也有同一條件，原文是「allow genes to sit in more than one community」 | 結果形式條件（重疊、空間鄰近、動態）寫在需求原文外，卻被套到核心需求上，把 CONDOR 排除 | 條件寫在需求原文外時，另列一項「不可做」，核心依自己的原文判定。CK3–CK6 的標準答案只評條件那一句，所以兩邊一致。資料單位、樣本配對等**適用條件**維持套用到需求（CK1、CK2、K02） | 純程式 |
| A2 | MX03（兩層 DRAGON + 第三層）、MX09（TF+miRNA + lncRNA） | 整句只有一項需求：layers 3／含 lncrna，並引用 near miss | 核心和延伸寫在同一個引文內，程式分不開 | 契約：每項需求加 `adds`（延伸部分的原文和種類：omics_layer、regulator_class、group_overlap、other），由程式拆成核心（可做）與延伸（不可做） | 契約形狀，需 live |
| A3 | N35（PUMA 由 miRNA 表現量決定）、MX14（每週一自動重跑） | 都被歸為 how_computed，而且和需求同句 | Log 414 的前置規則丟掉同句條件（為了避免 PC4 的誤判） | 同句、但在需求原文外的條件也交給條件檢查。若回答 violates，另列一項不可做，核心保留，run 擋下 | 依賴模型判定，需 live |
| A4 | MX02（儀表板） | 交付要求「put the per-sample networks into an interactive dashboard」被丟掉 | 交付要求**包含**需求原文就被丟，規則應是**位於**需求原文內才丟 | 改成「位於」判斷 | 純程式 |
| A5 | S138（P30）「Outputs can go to /registry/sambar_run1」 | 被歸成交付，列為不可做 | 輸出資料夾不是交付 | 交付引文的去處只是檔案路徑、沒有網址或信箱時，不算交付 | 純程式 |
| A6 | M1 遺留：兩項以上需求時，請求層的設定沒有歸屬 | — | — | 已註冊設定（`WORKFLOW.控制項`）套用到判給該 workflow 的需求 | 純程式 |
| A7 | M1 遺留：跨控制項規則 | — | 只寫在執行器裡 | lambda1、lambda2 必須一起給；kmax ≥ kmin、kmax ≤ 樣本數；save_pvals 需要 sparsify；sparsify 時 delta < 1/3。寫成共用函式，執行器與能力檢查都呼叫 | 純程式 |

錄下的 2,676 個讀取中，同句、在需求原文外的 how_computed／what_it_contains 有 99 個，大多只是輸入描述（例如「from expression, motifs and PPI」）。錄下的條件檢查只有 25 對，太少，無法離線估計誤判率。

## B. 多輪狀態（CLI 引擎）

| 代號 | 案例 | 路徑 | 原因 |
|---|---|---|---|
| B1 | K02：第 1 回合 DRAGON 進入輸入精靈；第 2 回合說「資料來自不同小鼠」 | `cli/bootstrap.py:265` 把待答計畫還原成 pending_plan，不還原 follow-up 脈絡（`engine/machine.py:134`）；`_accept_task`（machine.py:673）把整句當成同一 workflow 的 continuation；`router_invocation.py:163` 因為 continuation 而略過能力檢查；`continuation_invocation.py:67` 蓋上 `user_selected`（核准） | 有待答精靈時，新訊息完全不經過檢查。互動模式下更糟：非數字的文字會被當成檔案路徑（`cli/clarification.py:45`） |
| B2 | K09：第 1 回合 GPU 被擋下；第 2 回合「Never mind the GPU - CPU is fine」 | 解析器回 adds_condition 或 follow_up，任務被組成「Previous NetZoo goal: …\nUser follow-up: …」；`EXPLICIT_EXECUTION_PATTERNS`（`routing/capability.py:123`）不把冒號當子句邊界，所以「Run」不算執行要求 → no_tool | 被擋下的 run，修正之後沒有重新規劃；接受 offer 只能靠解析器回 accept_workflow |
| B3 | K06、K09：「fixed lambdas of 0.2 and 0.6」「single precision」 | 控制項只從 `name=value` 綁定（`extract_explicit_workflow_controls`） | M1 驗證過的設定沒有進入 run，run 會默默用預設值 |

## C. 檔案綁定（規劃）

| 代號 | 案例 | 原因 |
|---|---|---|
| C1 | P21（`yeast_stress_logc.tsv`）、P16（DRAGON 兩層）、P24、P33（`/proj/mac/priors`）、P04 | 沒有指定角色的路徑，只有檔名剛好含一個角色提示才會綁定（`interpretation/discovery.py:41-65`），DRAGON 層完全沒有提示；綁不上的路徑被丟掉，也不記錄使用者寫過檔名；找不到的資料夾改掃 `data/`（`planning/evidence.py:394`） |
| C2 | 24 個進到輸入關卡的 session 中，18 個列出或自動填入 toy／fixture 資料；P19 因為「endome**trial**」被判成示範需求，自動填入 dragon-toy | `_is_demo_request`（`presentation.py:774`）沒有字界；探索結果不排除示範資料夾（`*-toy`、`teacher-demo`、`auto-check-*`、`blind-*`）。這違反 AGENTS.md「正式分析不可因為 workspace 存在 toy data 就自動採用」 |
| C3 | S001=P02、S116=P28：資料事實呼叫被預算擋下，字詞後備又沒認出「TF-TF interaction」；S046=P06：讀到 priors stated，卻因「last month's aggregate run」被歷史規則拒絕，又被當成模型讀到 unstated（`data_plan.py:153`） | 「有沒有這份資料」和「它從哪裡來、給了路徑沒」混在一起；被拒絕的讀取被當成「unstated」，而不是「沒讀到」 |

C3 的預算問題已由 M1 的 3dee444（讀取類呼叫用額外額度記帳）處理，需離線確認。

## 建議順序

1. **C1、C2（安全）**：純程式，用單元測試與錄製重播驗證。
2. **A1、A4、A5、A6、A7、C3（被拒絕的讀取改回字詞判斷）**：純程式，離線驗證。
3. **B1、B2、B3**：引擎修改，用單元測試覆蓋多輪路徑。
4. **A2、A3**：契約或模型判定，最後跑一輪小型 live，同時檢查多輪與檔案綁定的 run 回合。

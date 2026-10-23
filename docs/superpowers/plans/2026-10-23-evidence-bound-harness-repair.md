# NetZoo harness 全面修復：實作與驗證計劃

日期：2026-10-23（同日修訂，見決策紀錄）。狀態：**計劃草案，尚未執行本計劃的程式修改**。

規格：[判斷、追問與記憶修復 spec](../specs/2026-10-23-evidence-bound-harness-repair-design.md)。所有決策語意、兩輪澄清與研究門檻以該 spec 為準。

基準：`netzoo-agent/main` 的凍結系統 `91a8c2d9`。實作在由 `netzoo-agent/main` 建立的 worktree 進行，不在 main tree（`evidence-contract-grounding`，`dfbcbfd8`，少 138 個 commit）。下列「現有檔案」都指 `91a8c2d9` 上的版本。

## 先看這一頁

建議先做 **P0 → P1 → P2**，得到能單獨評估的判斷修復；再做 **P3 → P4**，補多輪與記憶；最後用 **P5** 完成論文證據。P5 的題庫設計與標註規範可提前準備，但正式結果必須在版本與計分規則凍結後產生。

| 優先序 | 交付 | 解決的核心問題 | 完成標準 |
|---|---|---|---|
| P0 | 固定 baseline 與 replay | 不知道改好的是哪一層 | 環境／版本／gold／trace 可重現；replay 基準 613/757 |
| P1 | 未決條件不能無故消失 | agent 有提問就整批解除舊 waits、沒交付被當反證、第三題丟失 | A01（回歸）–A04 通過；replay 對→錯 0 |
| P2 | 有證據的判定、合約否決、partial 與兩層理由 | 空 matching 誤拒、引文假接地、同 run 整題 DECLINE、制式 not-matched 回覆 | A05–A10、A18、A20–A22 通過；replay 對→錯 0，wrong reason 不增加，不附理由的拒絕為零 |
| P3 | 任務事實與兩輪追問 | 重問、忘記、改條件仍沿用舊核准 | A11–A15 通過 |
| P4 | 重用與版本失效 | 舊成功被視為當前有效 | A16–A19 通過 |
| P5 | 精簡的最後驗證與論文表格 | 測試全綠但真實語意未驗證 | FA／FR／MA、追問成本、消融、誤差與限制 |

不以重寫 agent、換模型或新增 workflow 作為前置條件。下列新檔名是建議實作位置，**目前尚不存在**；執行時可依現有模組邊界調整，但需保持同一權威資料流。

## P0：封存可比較的基準

**修改／新增範圍**

- 新增 `docs/research-log/harness-repair-2026-10-23/BASELINE.md` 與 `ROUND.md`。
- 新增 `tests/fixtures/harness_repair/` 的最小 reading／decision fixtures；不得放帳號、API key 或使用者完整資料。
- 評估沿用 `scripts/saved_trace_replay.py`、`scripts/routing_repair_replay.py`；先確認可讀目前 schema，缺欄位要報 incompatible，不補成成功。

**工作**

1. 由 `netzoo-agent/main` 建 worktree（detached `91a8c2d9`）。記錄 commit、dirty diff 摘要、Python／套件版本、目前模型設定與 policy hash；不印出環境憑證。
2. 在 worktree 重跑完整 `tests/`（10-22 紀錄 4,931 項通過），結果記入 manifest。10/23 的 432 項是 `dfbcbfd8` 上的子集，只作舊樹參考。環境或依賴改變需更新 manifest。
3. 用 B2 harness 在 `91a8c2d9` 跑 replay 基準（應為 613/757），存成 `base.json` 供之後 `compare`；用 `reason-accuracy-2026-10-21` 工具記錄 wrong reason 與不附理由（制式 not-matched）的基準數。
4. 建立小 fixtures：checked-empty（`91a8c2d9` 應已通過，作回歸）、agent 只問一題而其他舊 waits 仍有效、沒交付的 wait、all-proposals-rejected、empty-match、方法限制作用對象錯誤、同一 run 設定不支援。記錄 baseline 的實際行為及 spec 預期，兩者不能混寫。
5. 將核心 56 題、h1–h6、23 組 heldout、a24b、m3 都標為 development/regression；正式題不得從這些題改幾個字冒充新情境。
6. 列 appearance／reading／decision／render／execution 的 evidence boundary；frozen replay 測決策，新 live 測讀取。

**驗收**：舊行為可重現；未修改 agent。輸出 manifest、案例表與 baseline trace IDs。不要為了湊綠色結果改掉 baseline 記錄。

## P1：建立最小 obligation ledger，修掉空清單放行

**現有檔案**

- `scripts/netzoo_agent_core/contracts/{fact_check,core_decision,requirements,decisions}.py`
- `scripts/netzoo_agent_core/graph/fact_check_call.py`
- `scripts/netzoo_agent_core/interpretation/{fact_check,core_decision,needed_facts}.py`
- `tests/test_fact_check.py`、`tests/test_core_decision.py`、`tests/test_needed_facts.py`

**建議新檔**：`contracts/evidence.py`、`interpretation/obligations.py`、`tests/test_obligation_lifecycle.py`。

**工作**

1. 實作 FactRecord／Obligation／RuleEvaluation 的最小型別、stable IDs 與引用驗證；初版先支援現有需求與未知維度，尚未要求跨回合保存。
2. 建立 needs_fact adapter，保留來源、候選、規則／未知欄位及 by_code；不能只從問句文字產生 identity。
3. `tests/test_fact_check.py` 在 `91a8c2d9` 已分成兩個方向（agent 有提問時舊維度是 shadow；沒提問時保留，回 `needs_fact`）。新增：agent 只問一題時，其他仍有效的舊 needs_fact 不被解除；沒交付的 wait 不得變成 `not_available`；all-rejected 與 failed/not_run/blocked 分支。先確認新測試在 `91a8c2d9` 失敗。
4. 把 `waits_after_agent`／`without_legacy_waits` 的整批解除改成逐條 discharge；同步檢查 `decide_core` 的 `agent_questions`、`legacy_kept` 與 `network_given` 路徑，只修其中一處會留下另一個放行路徑。
5. 實作 resolve／discharge，要求 evidence reference；缺乏 resolution 的 open 不得變 satisfied。舊疑問可以因不適用解除，不全部無條件保留。
6. 區分 invalid proposal 與 valid-but-not-asked；前兩題供呈現，其餘進 queue。fact agent 成功、提案無效、預算不足與無問題分開記錄。
7. R5 改成 pending_file_check；只有 validator 的實際結果能 resolve，不因引文比對就寫成 settled。

**驗收**：A01（回歸）–A04；再跑 fact/core/needed-facts。B2 harness `compare base.json new.json`：對→錯 0，或逐份列出交使用者決定；新增的追問逐份列出（成本，不是錯誤）。具體觀察「CONDOR unknown + agent 只問別的事 → 仍問網路種類，resolved 後依值重新判定」，且確實不相關的舊疑問不造成永遠 ASK。這一步只改讀取之後的判定，不跑 live。

**風險／回復**：舊規則可能過問。以 scope/relevance 解決，不能回復整批放行。baseline 行為只在隔離 replay 保留供比較；不為實際執行提供繞過開關。

## P2：拒絕需要反證，合約限制只作用於相應需求

**現有檔案**

- `contracts/{capability_check,policy,core_decision}.py`
- `interpretation/{capability_check,core_decision,request_requirements,ask_facts,core_views}.py`
- `interpretation/{same_run,method_conditions}.py`（partial 規則、`named_limits` 的理由來源）
- `interpretation/{stated_reasons,hypothesis_routes}.py`、`reply_cards/builder.py`（拒絕理由文字的其他來源）
- `graph/{routing_planning,router_invocation,response}.py`
- `scripts/netzoo_agent_core/workflow_conditions.py`、`scripts/workflow_registry.py`
- `workflows/*.yaml`、`scripts/netzoo_agent_core/policy.py`（只修改實際需要結構化規則的部分）
- `tests/test_policy_registry_contract.py`、`tests/test_operation_authorization.py`、`tests/test_same_run.py`、`tests/test_m3_method_fitting.py`、`tests/test_stated_reasons.py`

上列短路徑除 scripts/workflow_registry.py、workflows、tests 外，均相對 `scripts/netzoo_agent_core/`。

**建議新檔**：`interpretation/contract_rules.py`、`tests/test_contract_rule_evidence.py`、`tests/test_empty_match_unresolved.py`、`tests/test_decline_reason_layers.py`。

**工作**

1. 盤點 `_status`、`_full_gap`、`routing_unsupported`、boundary 與 run gap 的拒絕來源；建立「來源 → 所需證據 → 轉換」表。不要只改 `_status` 字串而漏掉 downstream renderer／enum。
2. 為未建立 matching 的結果保留 unresolved，明確反證仍是 contradicted。原有 `not_available` 如保留，限定為已具備反證，不再代表空集合。
3. 為現有數量、controls、組合與必要資料規則加入穩定 rule IDs；重用既有 predicate 與 validators，避免兩套限制表。
4. 加 requirement/action/subject binding；同一限制不因 result 或 about_methods 類別而漏查，歷史背景也不能變成目前設定。
5. 契約 veto 只消耗候選的相關事實。驗證引文＋scope＋typed operands；引文對但推論不對的測試必須被擋下。無法形式化者保留 unresolved，記錄局部重讀的成本與失敗。
6. 在 `classify_task` 內，於最終 `decide_core` 前整合證據與規則結果；不要先產生 DO 回覆後再另寫一個最終判斷者。現有設計提過 `hybrid_gate_call.py`，但本 checkout 指定 runtime 路徑不存在，不能假設可直接掛上。
7. 重新計算各需求及聚合狀態，處理部分可做、已拒＋待問、獨立反證優先消除無用詢問；保留既有 run authorization。
8. partial（使用者 10-23 決定）：改 `interpretation/same_run.py::same_run_holds`。被擋 workflow 上的可做列不再改成 `not_available`，而是保留可做、標記不可執行（run_allowed=false），回覆 DO + partial；子集要執行需使用者確認修改後的請求。依新決定更新 `tests/test_same_run.py`、`tests/test_m3_method_fitting.py` 的相關預期，並在研究紀錄列出受影響的舊金標（J44、L21、H40、L13；a24b MX04／MX05）與重標結果。
9. 兩層理由（使用者 10-23 決定，spec 第 10 節），取代制式的 not-matched 回覆：
   - 先盤點所有產生拒絕文字的位置：`interpretation/capability_check.py` 的 `NOT_MATCHED` 與 “no registered workflow produces …” 各句、`interpretation/stated_reasons.py::stated`、`interpretation/core_views.py`、`interpretation/hypothesis_routes.py`、`graph/router_invocation.py`、`reply_cards/builder.py`。
   - 每處歸為第一層（前提全部核實；能力陳述須是對全部註冊 workflow 計算、且綁定已核實），否則改成第二層。
   - 第二層文字只由程式從 typed 欄位組成：引用 span、比對結果、registry 選項；不含模型自由文字或 rule B 的條件答案。
   - 完全無候選時用第二層；有候選但未建立支持則為 unresolved。
10. renderer 只呈現最終判斷與可溯源理由，規則／binding 失敗不得被模板包裝成確定結論。理由的任一前提無法核對時，不顯示該理由，改用第二層（A21）。

**驗收**：A05–A10、A18、A20–A22。測「明確能做仍 DO、明確違反仍 DECLINE、讀取錯誤不假裝 CLARIFY、空 matching 不假裝反證」。B2 harness `compare`：對→錯 0（重標過的金標用新標籤），或逐份列出交使用者決定。`reason-accuracy` 稽核：wrong reason 不增加，不附理由的拒絕降為零，第二層回覆另列一類檢查是否誤導。之後如需端到端 smoke，只跑受影響的題、每題 1 次、最多約 20 個 session，開跑前報 session 數與費用。這一步不宣稱真實語意準確率已改善。

**風險／回復**：UNCHECKED 或誤拒增加需看分母與個案。新 verifier 先影子記錄，僅在 A/B harness 切換；正式採用由凍結指標決定。不能因追求低 false accept 而默默拒絕所有題。partial 改回 DO 後，若 replay 出現先前被 ROUND-17 擋下的錯誤放行，逐份列出交使用者決定，不自行恢復整題 DECLINE。

## P3：補 task state、兩輪回答與修正失效

**現有檔案**

- `contracts/{requirements,interaction,state,decisions}.py`
- `engine/{state,machine,recheck,choices}.py`
- `cli/{bootstrap,follow_up,reply_resolution}.py`
- `session.py`、`graph/{routing_planning,continuation_invocation}.py`
- `tests/test_workflow_continuation.py`、`tests/test_run_recheck.py`、`tests/test_resume_follow_up.py`、`tests/test_session_management.py`

以上非 tests 短路徑相對 `scripts/netzoo_agent_core/`。

**建議新檔**：`contracts/task_state.py`、`engine/fact_updates.py`、`tests/test_task_fact_memory.py`、`tests/test_clarification_budget.py`。

**工作**

1. 在現有 RequestRequirements 上加入本任務 evidence refs；TaskState 成為跨輪權威，RequestRequirements 保持每輪操作與明示參數的權威。明定兩者 projection，避免雙重可寫。
2. 將 TaskState 透過 CliRuntime → ConversationState → graph invocation → result → save_session → bootstrap resume 全程傳遞；CLI、one-shot resume 與 daemon 使用同一規則。
3. 穩定 question IDs、typed answers、queued obligations。新 FactPatch 只更新有來源且 scope 一致的欄位；更正、新需求與新資料走相應分支。
4. 以 task/subject/revision 管理依賴；更正 facts 後 invalidate rules、plan、preview 和 validation。既有 WorkflowContinuation.recheck 保留並接到相同更新機制。
5. 對已知前提不重問；對無明示 uncertainty 但決定性缺漏建立 obligation。合法預設與 file check 先處理，避免問完整 YAML 表單。
6. 兩輪計數、exhausted 狀態與後續主動補充；resume 不能重置預算。保留必要的 paths／execution confirmation 流程並單獨記帳。
7. 純 ASK／CLARIFY 回合即持久化。更新 pending-session 判斷與 retention：目前只看 needs_input／needs_confirmation 的地方也要識別新 pending task，避免 pending 問題被當成已結束刪除。
8. schema version、舊 session migration、未知版本拒絕、atomic storage；保持 `load_session` 既有 tuple 使用者相容，新增 typed load API 或由 payload 取得新狀態，不偷偷改回傳 tuple 長度。
9. 對話壓縮保留 active facts 與最小來源，限制 event history 大小；錯誤版本或資料損壞保留原件，不自行清空記憶。

**驗收**：A11–A15。至少有真正走 conversation engine → graph → save/load 的多輪整合測試；mock 僅替代 LLM/外部服務，不 mock 掉被驗證的 state update 或 persistence。另以 live 小樣本驗證 resolver 對更正／換任務的辨識，分開報告。

**風險／回復**：舊存檔可讀、未驗證 approval 不可復活。任務切分不明確時標衝突，而非丟棄現有資料或自動傳承全部設定。

## P4：輸入與長期記憶的有效期

**現有檔案**

- `contracts/memory.py`、`memory/{episodes,profiles,storage}.py`
- `interpretation/episode_reuse.py`、`planning/evidence.py`
- `graph/{policy_memory,execution}.py` 與 `evaluation/`、執行前 preflight 的實際接點
- `tests/test_agent_gate.py`（profile／episode cases）、`tests/test_episode_semantic_retrieval.py`、`tests/test_request_input_binding_priority.py`

以上非 tests 短路徑相對 `scripts/netzoo_agent_core/`。執行前接點以實作前精確呼叫追蹤補入任務紀錄，不能假設只改 episode_reuse 就覆蓋 executor。

**建議新檔**：`data/artifact_revision.py`、`tests/test_episode_freshness.py`、`tests/test_plan_evidence_revision.py`。

**工作**

1. 以 additive、versioned schema 記錄 input revision／validator／contract hash；現有 Episode、retention 與 profile 行為不重寫。
2. 重用一律是提供候選路徑；是否保留當前驗證，取決於 revision 與依賴的規則版本。必要時重新驗證，仍遵守使用者明確路徑優先。
3. 舊 episode lazy migration：無 hash 則 unverified，不全庫重算。失敗／dry-run 不得誤變為成功執行紀錄。
4. 執行前核對 plan evidence fingerprint 與目前 facts、files、controls、policy；變動則 hold/replan。關於 snapshot／TOCTOU 的可保證範圍寫入設計與測試說明。
5. 補真實 typed parameter snapshot 僅為重現用途；不從歷史參數推導新授權。確認 inspect/delete、private storage 與容量限制涵蓋新增欄位。

**驗收**：A16–A19，且既有 profile 與 explicit input priority 仍通過。包括相同路徑不同內容、同 size/mtime 不同內容、舊記憶缺 metadata、不同政策、同檔案但不同目標，以及 valid reuse 仍可成功。

**風險／回復**：hash 增加 I/O；報實測成本。必要檢查因資源不足未完成時保持 pending，不回退到「上次成功所以通過」。

## P5：研究驗證與論文材料

**交付範圍**

- `docs/research-log/harness-repair-2026-10-23/` 下的題目 schema、split manifest、gold、ROUND、results、error analysis。
- 擴充既有 replay／score runner；若不合適，再建 `scripts/evaluate_harness_repair.py`，此名稱目前僅是計劃。
- 單輪與多輪情境 runner；多輪按被問的 obligation 回答預先凍結的事實，不把錯誤問題也餵成正確答案。

**工作**

1. 依 spec 第 13 節定義主要指標（FA／FR／MA）、追問成本、可接受動作集合、排除規則、樣本量與停止規則；公開 UNCHECKED、provider failures 與無法計分的數量。
2. 建 oracle/replay 比較，分辨 semantic reading、decision、rendering 與 memory 的貢獻；缺新 schema 欄位不可無聲補值。
3. 單輪 A–D 以 replay 比較（零 API 成本）；多輪 A／D／E 才跑 live。
4. 最後驗證依精簡測試規則：新寫約 50 個不同情境，每題跑一次找共同問題，離線修正後同一組再跑一次；開跑前報 session 數與預估費用（gpt-4o-mini 已預先授權，gpt-4o 需先問）。多次 rerun 和改寫均在同一情境 group 內統計。
5. annotation artifacts 檢查：新題先跑 TF-IDF+LR 基線（`text-baseline-2026-10-22`），另報困難子集；省略關鍵欄位、無關 uncertainty、最小反轉與跨模板。基線只作稽核，不取代人工審核。
6. 同時計分判定、理由、前提綁定、追問必要性與最終解決；不能只用 core.kind 或 substring match 決定語意正確。
7. 報各類分母、paired 差值、按情境群聚的區間、token／延遲／輪數；寫失敗案例與未形式化條件限制。
8. 更新論文：問題與假設 → harness 分工 → 可重現規格 → 控制實驗 → 消融與限制。將「記憶」具體描述為 task fact persistence／revision invalidation，而非籠統長期記憶能力。

**完成標準**：新設計是否達門檻有明確結論；不保證必然改善。若證據不足就明列，不因不顯著持續換題直到有漂亮分數。

## 測試命令與執行紀律

本機已確認可用 interpreter：`/opt/anaconda3/bin/python`。命令在 repository 根目錄執行。新測試檔在建立前不能當作已通過項目。

P1/P2 起步使用既有套件，再加入各階段新增測試：

```bash
/opt/anaconda3/bin/python -m pytest tests/test_fact_check.py tests/test_core_decision.py tests/test_needed_facts.py tests/test_policy_registry_contract.py tests/test_operation_authorization.py tests/test_same_run.py tests/test_m3_method_fitting.py tests/test_stated_reasons.py --fail-on-skip -q
```

P1/P2 的 replay 驗收（在 worktree 執行；`base.json` 由 P0 在 `91a8c2d9` 產生）：

```bash
/opt/anaconda3/bin/python docs/research-log/stability-round13-2026-10-21/harness.py run new.json
```

```bash
/opt/anaconda3/bin/python docs/research-log/stability-round13-2026-10-21/harness.py compare base.json new.json
```

P3：

```bash
/opt/anaconda3/bin/python -m pytest tests/test_workflow_continuation.py tests/test_run_recheck.py tests/test_resume_follow_up.py tests/test_session_management.py tests/test_session_model.py --fail-on-skip -q
```

P4：

```bash
/opt/anaconda3/bin/python -m pytest tests/test_agent_gate.py -k 'memory or episode or profile or conversation or session or preference or reuse' --fail-on-skip -q
/opt/anaconda3/bin/python -m pytest tests/test_memory_package.py tests/test_episode_semantic_retrieval.py tests/test_request_input_binding_priority.py tests/test_agent_stability.py --fail-on-skip -q
```

最終整合補回 test_clarification_planner 及本計劃新增套件，依實際變更範圍執行更廣的 routing/planning/evaluation/execution checks。fixture 隔離 profile/session/data；不把使用者正式記憶或科學資料作測試寫入目標。live 評測另存 run manifest 與成本；依 10-13 精簡測試規則，開跑前向使用者報 session 數與預估費用，執行時依當時使用者授權範圍處理，不在本計劃虛構已核准的預算。

## 每階段要留下什麼

每階段只需一份簡短結果紀錄：修改範圍、規格案例 ID、測試命令與結果、before/after trace、仍不支持的條件、成本或相容性風險。文件變更不需要重跑整個 agent 測試；程式修改才跑相關行為測試。

完成 P1/P2 後即可先看收益與過度追問風險；P3/P4 支撐多輪與記憶主張。若論文時間有限，先縮小研究主張與受測範圍，不刪除 blocker、不把 mock 測試改稱實際模型能力，也不為擴充功能延後必要實驗。

## 決策紀錄

- 2026-10-23：使用者要求可審閱的全面修復 spec／計劃。本次只新增這兩份文件；沒有更改 agent、模型、既有測試預期、使用者記憶或歷史實驗分數。
- 2026-10-23（修訂）：基準改為 `netzoo-agent/main` 的 `91a8c2d9`，在 worktree 實作；P1 縮為 `91a8c2d9` 仍存在的整批解除與沒交付變反證。使用者決定採用 DO + partial，取代 ROUND-17 的整題 DECLINE（P2 第 8 項）。沿用不給錯誤理由、追問成本、精簡測試與單一盲標；P1／P2 改以 B2 replay 驗收，live 限受影響的題。
- 2026-10-23（修訂）：使用者決定每則拒絕都說理由，P2 第 9 項改為兩層理由（核實的合約理由／說明查了什麼），取代 not-matched 制式回覆；新增 A22。

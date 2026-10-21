# ROUND-07 補充：十類重複判斷盤點與既存紀錄量化

日期：2026-10-20。只讀程式與既存 JSON；沒有呼叫模型／API，沒有更改行為、prompt、YAML 或測試。

## 先說範圍與狀態

磁碟上的 `collab/ROUND-07-PLAN.md` 要求本盤點，但既有 REPORT 寫的是數量 G1–G3 修復。這份補充不覆寫既有 REPORT，也不把其 979 筆重放當成十類均已完成量化。

程式快照：`cf31e7f3c6bf48f96553601eb292c66e272780f5`。當前原始碼的責任分工與歷史 session 的觀察分開列；歷史不一致不代表目前仍有同樣行為。

本次讀到 999 個有 proposal 的 capability-check event，來自 983 個 session_id、979 種 task/proposal/reread 組合。不同模型版本與回合不是獨立隨機樣本。

其中可精確連回 ROUND-01 金標 baseline 的有 189 個事件；其餘不補造對錯。沒有 capability proposal 的失敗 session 不在主分母，另見金標覆蓋表。

**flag 是待檢視的差異訊號，不是「這一類造成了幾個錯誤」。** 值不同可能是正確修正、不同作用域或兩種文字表示；有金標也只量關聯，不能直接當因果。

## 1. 主分母：歷史事件的可比資料與差異訊號

| 類別 | 可比事件 | 重填／雙來源事件 | 差異訊號 | 訊號率 | 金標有訊號：錯/總 | 金標無訊號：錯/總 |
|---|---:|---:|---:|---:|---|---|
| K1 指定方法 | 367 | 367 | 0 | 0.0% | — | 13/60 (21.7%) |
| K2 執行／說明意圖 | 723 | 723 | 61 | 8.4% | 0/4 (0.0%) | 25/133 (18.8%) |
| K3 結果／目標是否明確 | 441 | 441 | 80 | 18.1% | 3/24 (12.5%) | 11/80 (13.8%) |
| K4 結果粒度 | 293 | 293 | 48 | 16.4% | 3/6 (50.0%) | 5/43 (11.6%) |
| K5 workflow 選擇 | 305 | 305 | 18 | 5.9% | 1/6 (16.7%) | 7/48 (14.6%) |
| K6 不確定事實與追問 | 584 | 23 | 319 | 54.6% | 20/85 (23.5%) | 7/57 (12.3%) |
| K7 輸入存在／種類／排除 | 1 | 1 | 0 | 0.0% | — | 0/1 (0.0%) |
| K8 數量與歸屬 | 388 | 388 | 0 | 0.0% | — | 13/88 (14.8%) |
| K9 設定解讀與參數綁定 | 112 | 112 | 0 | 0.0% | — | 3/18 (16.7%) |
| K10 最終判定與回覆 | 625 | 0 | 5 | 0.8% | 2/2 (100.0%) | 33/187 (17.6%) |

分母依各類是否有足夠欄位而不同。K7 的窄比較若樣本很少，不代表資料歸屬風險很小；K10 沒有 renderer mismatch flag 也不代表回覆內容一定正確。K8/K9 只在單一要求及原文重疊時配對；同一引文可能含多個對象，仍需人工核對。

### K6 必須拆開看

K6 的總訊號混合「兩份數量讀取不一致」與「程式成功拒收追問」；不能用總數 319 當錯誤數或收益排名。細項如下；同事件可同時屬於兩項。

| 子類 | 事件數 | 細項數 | 金標錯/總 |
|---|---:|---:|---|
| fact_proposal_rejected_by_uncertainty_reader | 313 | 516 | 20/84 (23.8%) |
| legacy_wait_without_accepted_fact | 6 | 6 | 0/1 (0.0%) |
| same_quote_different_quantity_property | 2 | 2 | — |

## 2. 各類責任、消費者、優先權與來源

### K1 指定方法

- 性質：同一名稱多處讀取／文字解析
- 產生者：語意與原文方法名稱、每個結果 named_method、整段 named_method
- 讀取者：registry 配對、method_fitting、run verdict
- 衝突／優先規則：要求層有 named 時保留；單一要求缺 named 才補整段；明確選擇另有優先規則。
- 本輪可量口徑：單一要求、整段與要求層都明列方法時，排除 LIONESS 家族相容名稱後的不同名稱。
- 限制：名稱不同不必然是錯；多要求的不同方法不互相比。

來源：
- [method_conditions.py:verified_method:39](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/method_conditions.py:39>)
- [method_conditions.py:with_request_method:157](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/method_conditions.py:157>)
- [named_labels.py:named_workflow_action:46](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/routing/named_labels.py:46>)

### K2 執行／說明意圖

- 性質：不同讀取者共同控制授權
- 產生者：semantic request_mode、intent mode、capability asked_as、明確命令文字規則
- 讀取者：assemble_task_decision、_with_requested_run、操作授權閘門
- 衝突／優先規則：語意與 intent 都要求執行才設 execution_requested；後段 capability 結果仍須 available 且 asked_as=request；文字規則可協調。
- 本輪可量口徑：intent=execute，但所有結果被 capability 讀成 question；另計明確命令協調事件。
- 限制：不把 intent=answer 與 asked_as=request 視為矛盾；成功 semantic 的 request_mode 沒有逐次完整存檔，無法完整量三方差異。

來源：
- [intent_invocation.py:_invoke_intent_router:28](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/intent_invocation.py:28>)
- [assembly.py:assemble_task_decision:17](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/assembly.py:17>)
- [router_invocation.py:_with_requested_run:302](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/router_invocation.py:302>)
- [capability.py:reconcile_request_mode:337](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/routing/capability.py:337>)

### K3 結果／目標是否明確

- 性質：語意結果與能力目標的再判讀
- 產生者：outcome_hypotheses、capability goal、研究假設讀取、fact wanted_result/R7
- 讀取者：goal_unclear、decide_core、CLARIFY renderer
- 衝突／優先規則：confirmed capability goal_unclear 及 fact open_results 可先導向 CLARIFY；單一具名方法另視為有目標。
- 本輪可量口徑：單一語意解讀為具體 artifact、capability 卻 purpose_only；或相反：語意 unknown、capability result_named 且有結果。
- 限制：可能是能力核對合理更正語意推測；不從差異直接判定哪份對。

來源：
- [core_decision.py:goal_unclear:124](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/core_decision.py:124>)
- [core_decision.py:decide_core:189](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/core_decision.py:189>)
- [fact_check.py:kept_facts:110](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/fact_check.py:110>)
- [hypothesis_bases.py:invoke_hypothesis_matcher:211](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/hypothesis_bases.py:211>)

### K4 結果粒度

- 性質：同一結果的粒度重讀
- 產生者：semantic granularity、capability ask.scale
- 讀取者：registry 配對、能力 fitting、回覆的結果說明
- 衝突／優先規則：早期 registry 用語意粒度，後段 check 用自己的 scale；confirmed check 在限定條件下可接管匹配。
- 本輪可量口徑：單一解讀、單一要求且兩邊均為 aggregate/sample_specific 等可直接對照值時不同。
- 限制：unknown／unstated 不當成錯值；多結果與 per-group 不強行歸併。

來源：
- [outcome_matching.py:match_semantic_request:928](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/routing/outcome_matching.py:928>)
- [capability_check.py:build_capability_check:383](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/capability_check.py:383>)
- [checked_match.py:checked_match:92](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/checked_match.py:92>)

### K5 workflow 選擇

- 性質：分階段選擇及有條件覆核
- 產生者：registry match、capability delivered_by、checked_match、run verdict
- 讀取者：TaskDecision、Planner、fact candidates、回覆
- 衝突／優先規則：原 match 與 check 不是任意最後寫入者獲勝；checked_match 有既有匹配、使用者明選、unconfirmed 等限制。
- 本輪可量口徑：registry 與第一份能力核對都只指向一個 workflow，但兩個名稱不同；另記接管事件。
- 限制：可為正確的後段修正，也可能之後被輸入／限制排除；不把兩個階段都當最終決策。

來源：
- [router_invocation.py:_with_checked_match:270](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/router_invocation.py:270>)
- [checked_match.py:checked_match:92](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/checked_match.py:92>)
- [run_check.py:run_verdict:71](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/run_check.py:71>)
- [fact_check.py:fact_candidates:56](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/fact_check.py:56>)

### K6 不確定事實與追問

- 性質：候選數量、舊維度及 fact agent 多處決策
- 產生者：unknown_facts、count_alternatives、open_choices、fact agent
- 讀取者：count_update、resolve_unknowns、weigh_sample_doubts、kept_facts、decide_core
- 衝突／優先規則：fact checked 時舊非程式追問轉 shadow；程式數量追問仍優先；R1 要求能力讀取也認為同段不確定。unknown sample count 仍有獨立處理。
- 本輪可量口徑：同段候選數量被兩個入口指定不同 property，或可見 legacy needs_fact 最後未保留問題／R1 拒收。
- 限制：去重與抑制問題可能是正確行為；原文兩種讀取均錯也不會被一致性偵測抓到。

來源：
- [needed_facts.py:resolve_unknowns:215](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/needed_facts.py:215>)
- [needed_facts.py:verified_unknowns:256](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/needed_facts.py:256>)
- [count_alternatives.py:count_update:78](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/count_alternatives.py:78>)
- [count_alternatives.py:weigh_sample_doubts:113](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/count_alternatives.py:113>)
- [fact_check.py:kept_facts:110](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/fact_check.py:110>)
- [fact_check_call.py:apply_fact_check:97](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/fact_check_call.py:97>)
- [request_facts.py:FactRecord.read_alternatives:254](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/request_facts.py:254>)

### K7 輸入存在／種類／排除

- 性質：資料的多種讀取與驗證來源
- 產生者：語意 input_artifacts、ruled_out_inputs/only_inputs、data_facts、veto A3、檔案預檢
- 讀取者：without_ruled_out、data plan、核心資料追問、Planner
- 衝突／優先規則：語意輸入線索、使用者否定與真實檔案驗證意義不同；without_ruled_out 可移除前段 credit；veto 另有資料讀取。
- 本輪可量口徑：同一原文區段，同時被明確語意證據當作擁有某輸入，及 capability 當作該輸入不存在。
- 限制：僅在有 explicit input_artifact 證據與重疊引文時比；不把「方法需要」等同「使用者擁有」。

來源：
- [ruled_out.py:without_ruled_out:80](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/ruled_out.py:80>)
- [router_invocation.py:_with_applicability:220](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/router_invocation.py:220>)
- [data_plan.py:build_data_plan:140](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/data_plan.py:140>)
- [contract_veto.py:_core_data_question:422](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/contract_veto.py:422>)

### K8 數量與歸屬

- 性質：要求／整段重填，另有否決層讀取
- 產生者：ask sample_count/feature_counts、conditions 同名欄位、veto focus counts
- 讀取者：FactRecord、with_request_method、method_fitting、count_update、veto gates
- 衝突／優先規則：一般數量要求層先取值、缺才補整段；ROUND-03 共有紀錄；ROUND-07 加入候選擱置與檔案數量，但未取消所有 raw 重填。
- 本輪可量口徑：重疊證據的同類數量在要求與整段重填；其中讀出不同值的疑點另計。
- 限制：belongs_to 缺失且一句含多層數量時，只能標候選疑點；不同資料／群組不直接認定衝突。

來源：
- [request_facts.py:FactRecord.read_method:86](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/request_facts.py:86>)
- [request_facts.py:FactRecord.note_conflicts:388](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/request_facts.py:388>)
- [method_conditions.py:with_request_method:157](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/method_conditions.py:157>)
- [slim_reader.py:merge_focus:849](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/slim_reader.py:849>)
- [contract_veto.py:_count_violations:242](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/contract_veto.py:242>)
- [contract_veto.py:_flip_questions:375](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/contract_veto.py:375>)

### K9 設定解讀與參數綁定

- 性質：重填＋不同消費規則，部分已收斂
- 產生者：要求 settings、整段 settings、request_parameters、hydration
- 讀取者：setting_issue、typed_setting、verified_controls、run binding、Executor
- 衝突／優先規則：ROUND-06 兩條 run 已共用 _bind_run_settings；明確 name=value 的非預設值可優先，未綁定設定使 run 等待；raw settings 仍重填。
- 本輪可量口徑：同 setting 名稱且重疊原文的整段／要求讀取，value_quote 不同；另列原始值為空與去向事件。
- 限制：空字串 vs empty 或不同格式可能語意相同，不自動算錯；重放改善需引用 ROUND-06 的對照，不混成此掃描因果。

來源：
- [router_invocation.py:_bind_run_settings:373](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/router_invocation.py:373>)
- [router_invocation.py:_on_run_verdict:404](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/router_invocation.py:404>)
- [router_invocation.py:_with_requested_run:302](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/router_invocation.py:302>)
- [method_conditions.py:run_setting_value:433](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/method_conditions.py:433>)
- [method_conditions.py:verified_controls:453](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/method_conditions.py:453>)
- [method_conditions.py:unbound_settings:481](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/method_conditions.py:481>)
- [hydration.py:hydrate_router_decision:27](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/hydration.py:27>)

### K10 最終判定與回覆

- 性質：核心決策＋有行為判斷的多 renderer
- 產生者：full_gap、routing unsupported、run verdict、veto、decide_core、部分 renderer
- 讀取者：core_view、respond、DO 專用 renderers、CLI cards
- 衝突／優先規則：非 DO 先走 core_view；DO 有多個 renderer 與後附說明；core.view 記錄 mismatch。不是所有 renderer 都有最後判定權。
- 本輪可量口徑：只採 trace 明確標記 core.view.mismatch=true，不從 DO/needs_input 這類合法狀態差異推造錯誤。
- 限制：較舊紀錄缺 core.view，且歷史 mismatch 不等於目前程式仍會重現。

來源：
- [core_decision.py:decide_core:189](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/core_decision.py:189>)
- [core_views.py:core_view:60](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/core_views.py:60>)
- [response.py:respond:82](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/response.py:82>)
- [response.py:_respond:95](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/graph/response.py:95>)
- [hypothesis_routes.py:render_hypothesis_routes:451](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/hypothesis_routes.py:451>)
- [contract_veto.py:vetoed_core:530](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/contract_veto.py:530>)

## 3. 差異樣例（可追到 session/event；不自動認定病因）

### K1 指定方法

本口徑未觀察到訊號，或沒有足夠可比欄位；不作不存在問題的推論。

### K2 執行／說明意圖

- `hb-h2main-J08-1` capability event sequence=13；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2main/hb-h2main-J08-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.intent_classified",
    "sequence": null,
    "mode": "execute"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 13,
    "asked_as": [
      "question"
    ]
  }
]
```

- `hb-h1-H13-1` capability event sequence=18；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-phase1b-2026-10-18/heldout/live/h1/hb-h1-H13-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.intent_classified",
    "sequence": null,
    "mode": "execute"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 18,
    "asked_as": [
      "question"
    ]
  }
]
```

- `hb-h3main-L22-1` capability event sequence=20；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-slim-2026-10-19/h3/live/h3main/hb-h3main-L22-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.intent_classified",
    "sequence": null,
    "mode": "execute"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 20,
    "asked_as": [
      "question"
    ]
  }
]
```

- `hb-h3main-L30-1` capability event sequence=20；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-slim-2026-10-19/h3/live/h3main/hb-h3main-L30-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.intent_classified",
    "sequence": null,
    "mode": "execute"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 20,
    "asked_as": [
      "question"
    ]
  }
]
```

### K3 結果／目標是否明確

- `hb-h4main-M04-1` capability event sequence=16；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M04-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "artifact": "measurement_dataset"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 16,
    "goal": "purpose_only",
    "goal_quote": "Process counts_synovium_140.tsv and covariates_140.csv now (batch, age, sex and disease activity score for each of the 140 patients) and put the results in out/ra/."
  }
]
```

- `hb-h4main-M10-1` capability event sequence=18；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M10-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "artifact": "multi_omic_network"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 18,
    "goal": "purpose_only",
    "goal_quote": "what we want to get out of the integration."
  }
]
```

- `hb-h4main-M11-1` capability event sequence=26；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M11-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "artifact": "regulatory_network"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 26,
    "goal": "purpose_only",
    "goal_quote": "Can COBRA or CONDOR do anything useful with our liver fibrosis RNA-seq?"
  }
]
```

- `hb-h4main-M15-1` capability event sequence=20；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M15-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "artifact": "regulatory_network"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 20,
    "goal": "purpose_only",
    "goal_quote": "I just want to see something network-like"
  }
]
```

### K4 結果粒度

- `hb-h4main-M25-1` capability event sequence=16；gold=false_accept；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M25-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "granularity": "aggregate"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 16,
    "scale": "per_sample",
    "quote": "Set SAMBAR going on mut_pilot.csv (6 tumours x 900 genes, non-negative counts), exon_sizes.csv, cancer_genes.txt and h.all.v2023.gmt, trying anywhere from 2 to 8 subtypes."
  }
]
```

- `hb-h4smoke2-M38-1` capability event sequence=18；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4smoke2/hb-h4smoke2-M38-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "granularity": "aggregate"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 18,
    "scale": "per_sample",
    "quote": "Time to run SAMBAR: mut_hnscc.csv, exon_size.csv, cancer_genes.txt and kegg.gmt, trying 2 to 10 subtypes, output to sambar_hnscc/."
  }
]
```

- `hb-h2hyb-J17-1` capability event sequence=16；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2hyb/hb-h2hyb-J17-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "granularity": "sample_specific"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 16,
    "scale": "whole_cohort",
    "quote": "Please set up SAMBAR"
  }
]
```

- `hb-h2hyb-J22-1` capability event sequence=21；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2hyb/hb-h2hyb-J22-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "session.plan.decision",
    "sequence": null,
    "granularity": "aggregate"
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 21,
    "scale": "per_sample",
    "quote": "We want to group tumours into 2 to 6 subtypes based on pathway-level somatic mutation scores"
  }
]
```

### K5 workflow 選擇

- `hb-h4main-M14-1` capability event sequence=20；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M14-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.registry_match_completed",
    "sequence": null,
    "actions": [
      "run_dragon"
    ]
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 20,
    "credited_prefixes": [
      "lionesspanda"
    ]
  }
]
```

- `hb-h2hyb-J13-1` capability event sequence=18；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2hyb/hb-h2hyb-J13-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.registry_match_completed",
    "sequence": null,
    "actions": [
      "run_dragon"
    ]
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 18,
    "credited_prefixes": [
      "lionesspuma"
    ]
  }
]
```

- `hb-h2hyb-J14-1` capability event sequence=20；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2hyb/hb-h2hyb-J14-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.registry_match_completed",
    "sequence": null,
    "actions": [
      "run_dragon"
    ]
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 20,
    "credited_prefixes": [
      "lionessdragon"
    ]
  }
]
```

- `hb-h2hyb-J23-1` capability event sequence=22；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2hyb/hb-h2hyb-J23-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "routing.registry_match_completed",
    "sequence": null,
    "actions": [
      "run_giraffe"
    ]
  },
  {
    "event_type": "routing.capability_checked",
    "sequence": 22,
    "credited_prefixes": [
      "lionesscoexpression"
    ]
  }
]
```

### K6 不確定事實與追問

- `hb-h4main-M03-1` capability event sequence=24；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M03-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "user_data",
      "alternatives": [],
      "contract_quote": "Require at least three samples and validate expression inside the execution wrapper.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Will at least three samples remain after dropping the failed ones?",
      "uncertainty": "two_versions",
      "user_quote": "the sequencing core flagged one, possibly two, as failed",
      "workflow": "LIONESS-COEXPRESSION",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  },
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "user_data",
      "alternatives": [],
      "contract_quote": "Require at least three samples and validate expression inside the execution wrapper.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Will at least three samples remain after dropping the failed ones?",
      "uncertainty": "said_unknown",
      "user_quote": "the matrix has four libraries right now",
      "workflow": "LIONESS-COEXPRESSION",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  }
]
```

- `hb-h4main-M05-1` capability event sequence=15；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M05-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "user_data",
      "alternatives": [],
      "contract_quote": "GIRAFFE consumes gene-by-sample expression, a TF-by-gene motif/prior, and a TF-by-TF PPI matrix after explicit labelled-file conversion.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Do you have the required files prepared for GIRAFFE?",
      "uncertainty": "said_unknown",
      "user_quote": "I'd like to change the optimizer: learning rate 1e-4, 2,000 iterations, and double the weight on the PPI agreement term.",
      "workflow": "GIRAFFE",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  },
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "user_data",
      "alternatives": [],
      "contract_quote": "Missing files, delimiter/shape errors, empty or non-finite values, duplicate IDs/pairs, non-square or non-symmetric PPI data, and identifier mismatches are rejected before the API call.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Are the expression, motif prior, and PPI files free of errors and matching identifiers?",
      "uncertainty": "said_unknown",
      "user_quote": "Expression, motif prior and PPI are ready with matching identifiers.",
      "workflow": "GIRAFFE",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  }
]
```

- `hb-h4main-M07-1` capability event sequence=20；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M07-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "user_data",
      "alternatives": [],
      "contract_quote": "Expression must be a labeled gene-by-sample matrix with more genes than samples.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Does expr_panel.tsv have more genes than samples?",
      "uncertainty": "said_unknown",
      "user_quote": "expr_panel.tsv is a 400-gene targeted panel across 520 samples",
      "workflow": "COBRA",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  },
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "user_data",
      "alternatives": [],
      "contract_quote": "Design rows must use exactly the expression sample IDs and numeric covariates.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Does design_520.csv use exactly the sample IDs from expr_panel.tsv?",
      "uncertainty": "said_unknown",
      "user_quote": "design_520.csv has an intercept plus smoker (0/1) and batch (0/1) columns for exactly those samples",
      "workflow": "COBRA",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  },
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "wanted_result",
      "alternatives": [],
      "contract_quote": "run_cobra writes adjusted_coexpression.tsv and adjusted_coexpression.npz using the intercept component, with gene IDs on both axes.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Is cobra_panel/ a valid output directory for the COBRA workflow?",
      "uncertainty": "said_unknown",
      "user_quote": "outputs should go to cobra_panel/",
      "workflow": "COBRA",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  }
]
```

- `hb-h4main-M08-1` capability event sequence=15；gold=correct；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4main/hb-h4main-M08-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.fact_check",
    "sequence": null,
    "rule": "R1 the check did not read these words as the user being unsure",
    "proposal": {
      "about": "wanted_result",
      "alternatives": [
        "partial-correlation network linking 2,500 CpG methylation features with 1,500 transcripts"
      ],
      "contract_quote": "DRAGON output is aggregate, not sample-specific. Its partial correlations and precision values represent conditional associations, not causal relationships.",
      "no_outcome": "not_supported",
      "no_workflow": "",
      "question": "Do you want to keep all 4,000 features without filtering?",
      "uncertainty": "said_unknown",
      "user_quote": "we explicitly do not want any filtering",
      "workflow": "DRAGON",
      "yes_outcome": "supported",
      "yes_workflow": ""
    },
    "reason": "fact_proposal_rejected_by_uncertainty_reader"
  }
]
```

### K7 輸入存在／種類／排除

本口徑未觀察到訊號，或沒有足夠可比欄位；不作不存在問題的推論。

### K8 數量與歸屬

本口徑未觀察到訊號，或沒有足夠可比欄位；不作不存在問題的推論。

### K9 設定解讀與參數綁定

本口徑未觀察到訊號，或沒有足夠可比欄位；不作不存在問題的推論。

### K10 最終判定與回覆

- `hb-h4smoke-M31-1` capability event sequence=21；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4smoke/hb-h4smoke-M31-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.view",
    "sequence": null,
    "basis": "contract_veto_fact",
    "core_kind": "ASK",
    "mismatch": true,
    "reply_kind": "outcome_clarification"
  }
]
```

- `hb-h4smoke-M38-1` capability event sequence=17；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-hybrid-2026-10-19/h4/live/h4smoke/hb-h4smoke-M38-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.view",
    "sequence": null,
    "basis": "contract_veto_fact",
    "core_kind": "ASK",
    "mismatch": true,
    "reply_kind": "workflow_contract"
  }
]
```

- `hb-h2hyb-J17-1` capability event sequence=16；無精確 baseline 金標；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-options-first-2026-10-18/h2/live/h2hyb/hb-h2hyb-J17-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.view",
    "sequence": null,
    "basis": "results_given",
    "core_kind": "DO",
    "mismatch": true,
    "reply_kind": "unmapped_request"
  }
]
```

- `hb-h1-H34-1` capability event sequence=20；gold=false_accept；[events](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/docs/research-log/closed-menu-phase1b-2026-10-18/heldout/live/h1/hb-h1-H34-1/t1/events.jsonl>)
```json
[
  {
    "event_type": "core.view",
    "sequence": null,
    "basis": "results_given",
    "core_kind": "DO",
    "mismatch": true,
    "reply_kind": "unmapped_request"
  }
]
```

## 4. 現行程式重建的共用紀錄（若提供）

使用既有 ROUND-03 replay 對固定 readings 做純程式重建；不重跑任何模型。與前述歷史端到端判定不是同一口徑。

```json
{
  "readings": 979,
  "facts": 1354,
  "reads": 2514,
  "repeated_facts": 975,
  "result_facts": 1008,
  "also_request": 949,
  "result_only": 59,
  "unsure_facts": 44,
  "duplicate_uncertainty_facts": 12,
  "derived_facts": 29,
  "conflicts": 6,
  "conflict:latest_stated": 2,
  "conflict:unsure_candidates": 4
}
```

新增 metadata 或衝突紀錄不等於判定改善；所有重建衝突另存 rebuilt-metrics.json。

## 5. 否決層獨立抽樣

h4/veto.json 有 19 筆 checked 讀取。它們是與 baseline 成對的另一份讀取，不合併進上面一般 capability event 分母。詳 supplemental-veto.json。

M38（DO→DECLINE）、M48（DO→DECLINE）、M31（DO→ASK）等既知差異，只引用其原始記錄與 H2 評分，不將「改變」一律當成錯誤。這些是 ROUND-02 前的歷史紀錄，不能當成現在仍未修復的證據。

## 6. 排序與下一個收斂範圍

**建議先處理 K6 的數量不確定性雙入口，與 K8 的數量歸屬一起界定責任。** 這是按可定位的結構衝突及現行路徑排序，並非估計修好多少題。

1. K6/K8：同段數量分到不同 property 有 2 個事件（同一道 C45 的兩次讀取）；現行純程式重建另有 C45 三次與 H46 一次的 sample_count 擱置。前者能直接核對出「蛋白數當樣本數」的內部矛盾；其中也有不確定數量入口缺失、另一入口單獨讀錯的情況。不能相加算六題，也不能把 319 個 guard 訊號當成錯誤。先讓數量的 property、對象、不確定性及使用／擱置理由只有一個解析後的權威入口；第一讀本身錯誤仍需另行追蹤。

2. K10：625 個有 core.view 的事件中 5 個明記 mismatch（0.8%）；精確金標只有 2 個，均為錯誤。優先逐案確認現行版本能否重現；若仍重現，再收斂核心決定與 renderer 的責任。兩個金標的 cause 含 L2_no_check/X_other，不能聲稱 mismatch 就是全部病因。

3. K9：ROUND-06 已把 run 綁定收斂，應保留這項成果。單一要求且引文重疊的 112 個雙來源事件，本口徑沒有不同 value_quote；但它不會量出「同值被兩個消費者用不同規則解讀」。依 ROUND-06 現成的 180-run 配對重放，10 個 turn 改變且已逐項驗證；這才是此類已有的直接修復證據，不列成現行新故障。C40 清單歸在「值已讀到、執行綁定仍無法表示」，不要先加原文詞表。

4. K4、K5、K3、K2：差異分別為 48/293、18/305、80/441、61/723。金標差異中也有正確案例，且 K3/K4 使用後期語意快照；不宜現在直接合併成一個值。先保留「前段假設、後段更正、最終採用理由」的界線。K4 差異金標錯誤 3/6 的 cause 是限額／部分承諾，未證明粒度差異造成錯誤。

5. K1/K7 與 K8/K9 的零值衝突不能代表已解決。K7 只有 1 筆能做窄比較，屬觀測不足；K1 是名稱不同的窄口徑。K8/K9 仍有大量重填，也可能兩份一致地讀錯或作用域錯。

**目前能完成的是十類盤點、可觀察差異與金標關聯的排序；尚不能從既存紀錄得到十類的完整「因果錯誤數」或現行端到端錯誤率。** 本輪未做完整 Router/Planner replay、未重新呼叫語意或事實模型、未跑新盲題。

## 7. 限制與重現

- scope 限於計畫 K1–K10 所列 routing／interpretation／response 及其 run/planning 接縫；未完整審計 Executor 或所有 planner 模組。不是全專案所有函式的形式化證明。
- workspace graph generation 2026-10-16T10:16:00Z 明確排除 .worktrees；圖搜尋無結果後，以限定 source AST 與原始碼讀取補足。來源行號及 SHA 在 inventory.json。
- 部分已保存語意值是 Planner 後快照，無法完整還原第一次成功讀取。K3/K4 僅是跨階段差異訊號。
- 報表分開保存全部事件與去除相同 task/proposal/reread 組合後的敏感度分析。任一類的不同訊號可落在同一個 session，不能相加當總錯誤。
- 金標只套用到 session_id 和 prompt 均吻合的原 baseline；不把同題其他版本／smoke 的對錯套過來。
- 所有 session 與輸入紀錄保持原樣。資料解析限制：{"task_quote_match_failed": 6}
- 未解析的 source references：[]

```sh
python3 -I audit.py
# 若要加入現行程式對 readings 的純程式重建指標：
python3 -I audit.py --rebuilt /absolute/path/to/checks.json
```

重新生成 summary.json、records.json、inventory.json、manifest.json、supplemental-veto.json 與本報告。相同來源的核心輸出必須逐位元一致。

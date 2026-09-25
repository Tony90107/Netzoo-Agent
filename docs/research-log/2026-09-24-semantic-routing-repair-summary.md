# NetZoo Agent 語意路由修復：方法、因果與證據

**整理日期：2026-09-24**
**範圍：** 2026-09-23 至 2026-09-24 的 semantic-routing 與 guidance 修復，以及本次離線測試。
**文件性質：** 工程研究紀錄與論文寫作素材；內部 traces 和測試不是外部文獻，也不等同於獨立、同分布的基準評估。

## 摘要

本輪修復處理的核心問題不是單一模型「選錯工具」，而是自然語言請求經過多個階段後，使用者已明確說出的生物學角色、輸出粒度或當前目標會被遺失、錯誤降級，或與 workflow 能力定義不一致。修復因此落在確定性 request witness、欄位還原、ontology 驗證、workflow matching、clarification ranking 與回覆呈現，而不是藉由增加 prompt 指令要求模型自行改善。

最新定向 live A/B 在 5 個 prompt 上各測一次 legacy 與 claims 契約，共 26 次 provider calls；兩契約各有 5/5 個案例通過預先設定的 route 與 semantic criteria，沒有錯誤推薦、fallback 或 workflow execution。但同一輪也發現一項尚未關閉的語意狀態不一致：claims 對一個尚未決定輸出粒度的案例，在仍提出澄清問題時，最終結構化 outcome 已填成 `sample_specific`。因此目前結論是**定向場景已有改善證據，semantic routing 尚未完全修復或完成全面驗證**。

本次另外執行 10 個離線情境 fixture，結果 10/10 通過；澄清 planner、回覆呈現和 guidance consistency 的聚焦測試共 66 項通過。這些測試檢查已建立的候選決策如何產生問題與說明，**不代表原始自然語言 prompt 已由 live model 正確分類**。

## 1. 問題是如何形成的

路由流程可簡化為：

```text
使用者請求
  → intent / requested outcome 解讀
  → request witness 與欄位還原
  → typed outcome 驗證
  → workflow capability matching
  → reviewer / clarification
  → guidance 或執行路徑
```

追查 saved provider trace 後，確認錯誤可以出現在模型輸出之後的確定性階段。例如，使用者明確要求 cohort-level aggregate network 時，PUMA 與 LIONESS-PUMA 的 registry 都宣告可產生 aggregate 結果；matcher 因而把本來足以區分候選的明確粒度視為平手，再多問一次粒度。另一類問題是模型的 hypothesis 雖然包含正確訊息，evidence 標籤、引用文字或型別形狀不合規，導致 restoration、review 或 matcher 丟失該訊息。

因此只調整 model wording 不足以修復整條路由。修正原則是：保留能由使用者原文直接驗證的事實；將自動推論維持為推論；只在明確 witness 支持時套用窄範圍 ontology 約束；仍有多種科學解讀時就停在澄清，而不任意選 workflow。

## 2. 已完成的修復

| 修復領域 | 原因 | 做法 | 為什麼有幫助／目前證據 |
|---|---|---|---|
| 明確粒度與歷史/目前目標 | 英文「separately in each patient」「their own network」等寫法未被 granularity witness 捕捉；輸入矩陣提到 per-sample 也曾被誤認成輸出粒度；歷史需求可能蓋過目前目標。 | 擴充 `request_integrity` 的粒度 witness，使樣本/病人字詞必須與 network 輸出相連；增加 cohort-level witness 與常見中文形式；用 request witness 修復缺失或不可信的同值 evidence；對 hypothetical 後續目標不當成目前意圖。 | 訊息來源是請求原文，降低模型把明確粒度改成 `unknown` 或把輸入粒度誤套到輸出的機率。32 個 family cases、8 個 variants、39 個 main scenarios 的 witness 稽核未發現與預期粒度相反的 explicit witness；其中一個刻意拼錯的案例沒有抓到 witness，但也沒有產生相反 witness。這是 witness audit，不是 live routing accuracy。 |
| TF、miRNA 與 gene 角色 | 協同的 TF/miRNA-to-gene 敘述曾逐角色更新；中間狀態不完整而違反 outcome contract。像 `miR->gene`、`microRNAs regulate their target genes` 等明確形式也曾漏抓。 | 將一個明確 regulator→target 敘述的角色一次還原；角色及 artifact 的更新採一致性檢查；補上限定的英文、中文與 abbreviated role witnesses；當已知 regulator/target 已完整時，只在允許條件下移除多餘 `unknown` placeholder。 | 原子更新避免 transient incomplete outcome；closed witness 讓 deterministic matcher 可依已陳述角色區分 TF-only 與 miRNA+gene 網路。保存的 P1 traces 及 `miR->gene` traces 經當前 restoration、validation、matching 重播後符合預期 workflow；這些是 saved-response replay，不是新 live model trial。 |
| Aggregate 與 sample-specific workflow matching | PUMA 與 LIONESS-PUMA 都能產生 aggregate network；把所有可支援粒度都拿來比較，會讓已陳述的 aggregate 仍陷入 ambiguity。 | 當 LIONESS 類 pipeline 的 registry predecessor 也在候選中，且 predecessor 能滿足請求已陳述的粒度，matcher 會移除不必要的 pipeline 候選。另擴充粒度 witness，並只在 witness 確認的 patient-clustering 情境將 `sample_cluster_assignment` 套用其唯一合法粒度 `aggregate`。 | 候選縮減依照使用者已說出的粒度，不是 workflow 名稱或任意優先序。另以 scoped ontology alignment 避免把 TF sample-specific 網路錯對齊成只能 aggregate 的 TF-activity artifact。保存 trace replay 及定向 live case 支持角色/粒度案例改善；仍需擴大未見 prompt 的重複驗證。 |
| Claims repair contract 與 evidence | Claims repair 曾可重複修改同一 hypothesis index，導致 patch 無法套用或輸出截斷；reviewer 也可能以刪 evidence 或降成 `unknown` 來讓本體驗證通過。 | 將 repair schema 限定為單一 hypothesis index/outcome；對本體衝突提供結構化、可檢查的 repair facts；明確 witness 支持的 `operation=explain` 可在 advice/guidance 條件下記為 inferred，而非偽稱為逐字 explicit。 | 型別/schema 限制可阻止某些無法套用的 patch；provenance 區分 explicit 與 inferred。此領域仍有殘餘 reviewer/semantic-completeness 問題，不能把 validation pass 數直接解讀成語意修正成功。 |
| Guidance 意圖與簡短工具詢問 | 「Which tool/workflow/method?」等簡短詢問有時落在未知 request mode，claims review 因此反覆補問，未能把單一相容 workflow 提升為 guidance。 | 對明確詢問 tool/workflow/method/pipeline 的請求，若未明確要求執行或直接檢索，就將未知模式收斂為 guidance；執行意圖仍有優先權。若數個 hypotheses 都完全符合同一個 workflow，guidance promotion 才允許使用該單一 workflow。 | 依詢問功能而不是特定工具字串推導 advice/guidance，減少「只問解釋卻像要執行」的誤解。三筆保存的 terse miRNA prompt claims traces 重播後均 exact 到 LIONESS-PUMA，且不授權 execution。 |
| 需要澄清時解釋候選差異 | Planner 原本能選問題，但使用者未必知道候選 workflow 在方法、輸入、輸出或粒度上差在哪。 | `ClarificationPlanner` 依 artifact、granularity、regulator type、algorithmic tags、required input bundle 對候選分組與排序。回覆以 registry 顯示方法前提、必要輸入/替代輸入、輸出 artifact 和粒度；假設標成未確認；多個候選保持並列。單一 workflow 但粒度未明時，先問粒度，再呈現候選的粒度細節。 | 問題直接指出能區分 2–3 個候選的科學選擇；registry-backed 說明減少只列工具名稱、讓使用者猜差異的情形。10 個離線 fixture 及 66 個聚焦回歸測試通過。這尚未測量 live LLM 對任意原始 prompt 的分類能力。 |
| Trace 可觀測性 | 原 evaluator report 不足以分辨錯誤來自初次 interpretation、reviewer patch、restore 還是 matcher。 | `scripts/evaluate_routing.py` 增加 opt-in `--trace-out`，保存結構化呼叫 schema/hash、messages、raw arguments、解析錯誤、finish reason、usage、invalid calls、routing events 與 final decision；system prompt 只保存 hash。 | 可用逐 trial 證據定位失敗階段，並將固定 provider response 離線重播。這改善可診斷性，不會自行提高路由正確率；live trace 擷取仍需在可連 provider 的環境驗證。 |

相關程式位置：[`request_integrity.py`](../../scripts/netzoo_agent_core/interpretation/request_integrity.py)、[`stated_field_restoration.py`](../../scripts/netzoo_agent_core/interpretation/stated_field_restoration.py)、[`semantic_patch.py`](../../scripts/netzoo_agent_core/interpretation/semantic_patch.py)、[`claim_prompt.py`](../../scripts/netzoo_agent_core/interpretation/claim_prompt.py)、[`outcome_matching.py`](../../scripts/netzoo_agent_core/routing/outcome_matching.py)、[`clarification_planner.py`](../../scripts/netzoo_agent_core/routing/clarification_planner.py)、[`concept_answers.py`](../../scripts/netzoo_agent_core/interpretation/concept_answers.py)、[`verified_guidance.py`](../../scripts/netzoo_agent_core/interpretation/verified_guidance.py)、[`evaluate_routing.py`](../../scripts/evaluate_routing.py)。

## 3. 量化結果與解讀

以下結果來自不同測試設計，分母不可相加，也不可視為同一個 benchmark 的前後比較。

| 證據來源 | 設計與分母 | 結果 | 可以支持的結論 |
|---|---|---|---|
| Aggregate disambiguation | 兩個明確 aggregate prompt；legacy/claims；修正前後各 repeat=3。 | 綜合 F1–F4 修正後，兩個 prompt 在兩種契約都由 0/3 exact 改為 3/3；另有 10,395 個生成 outcomes 的 before/after 比對，只有 aggregate regulatory-network ambiguity 改變，沒有 exact 結果改變。 | 支持 matcher 的候選縮減沒有廣泛改寫既有 exact 結果。這是多項修正後的合併結果，不能單獨歸因於 F1。 |
| Claims patch 結構 | 歷史 reviewer patch validation 記錄；重複 hypothesis index 與 token 截斷為觀察指標。 | schema 修正後，重複 index 和截斷降至 0；一組 8 題 reviewer validation 記錄由 0/11 到 4/5。 | 結構可套用性有改善，但 validation pass 不等於語意修正正確；後續 traces 仍顯示 reviewer 可能降級已陳述欄位。 |
| P1 saved-response replay | 6 筆 legacy 與 6 筆 claims 保存回應；各自重播 restoration、validation、matching。 | 兩份契約的 6/6 保存回應都到達預期 exact workflow。 | 確定性修正可修復這些已記錄的輸出；不能估算新 prompt 的模型穩定度。 |
| Advice-to-explain / terse guidance replay | P4 的保存 Round-6 回應，以及 3 筆 terse miRNA「which tool」claims 回應。 | P4：legacy 2/2、claims 3/3 重播為預期 LIONESS-PUMA；terse guidance：3/3 exact 到 `run_lioness_puma`，未授權 execution。 | 支持受限的 advice/guidance 正規化和短工具詢問處理；屬於保存 response replay，不是新增 provider trial。 |
| P2 witness audit | 32 個 semantic-family cases、8 個 variants、39 個 main scenarios，集合可能重疊。 | 沒有 explicit granularity witness 與預期 aggregate/sample-specific 相反的案例；缺少 sample-specific witness 的預期案例為 0/32、0/8、1/39。 | witness 沒有在這些已稽核案例中提供相反粒度；最後一個 misspelled case 未被 witness 覆蓋，需保留限制。 |
| 當前來源 frozen-response replay | 每個 trial 必須有完整且完全相符的保存模型呼叫序列才列入 full-pipeline coverage；每種契約共 96 個目標 trials。 | Legacy：70/96 有完整回放覆蓋，覆蓋者 70/70 通過。Claims：65/96 有完整覆蓋，覆蓋者 62/65 通過；3 個未通過者 route status 為預期 ambiguous，但 reviewer 回覆 no-op 或無效。 | 在可完整重播的 trials 中，legacy covered set 全數通過；claims covered set 有 3 個 semantic-completeness review 失敗。覆蓋不足與失敗須分開報告；不能把 70/96 或 65/96 直接稱作模型準確率。 |
| 2026-09-24 live semantic A/B | `gran-tf-ss-individual-en`、`role-mirna-ss-en`、`zh-compare-patients-ss`、`gran-mirna-unstated-control`、`role-tf-agg-control-en`；claims、legacy 各跑一次；`openai/gpt-4o-mini`、temperature 0、`when_needed`；共 26 次 provider calls（12 claims、14 legacy）。 | 兩契約各 5/5 通過此次預先設定的 route/semantic criteria；0 錯誤推薦、0 fallback、0 workflow execution。 | 這 5 個定向案例上，兩契約都達成 100% pass；每案僅一次，未計算信賴區間或顯著性，不能代表完整語料或跨次穩定度。 |
| 同一 live A/B 的狀態一致性檢查 | 檢視 `gran-mirna-unstated-control` 的最終 claims outcome、route status 和互動問題。 | Route 為 ambiguous 且詢問 aggregate/sample-specific，但最終 `requested_outcome.granularity` 是 `sample_specific`，hypotheses 沒有明確 aggregate 假設。 | 目前 evaluator 漏掉「問題尚未回答，結構化狀態卻已選定粒度」的不一致；這是待修語意正確性與評分問題，不是此次觀察到的 workflow execution 事故。 |
| 2026-09-24 本次離線情境 | 10 個 deterministic fixtures，覆蓋算法、粒度、regulator、input、output、未確認假設、並列候選與先問再詳述。 | 10/10 通過。 | 驗證 planner 和 renderer 對建立好的 candidate decision 輸出符合預期；不是 raw-prompt live semantic test。第 10 項是刻意固定其他條件、只改 input bundle 的受控 planner fixture。 |
| 本次聚焦自動測試 | `test_clarification_planner.py`、`test_concept_answers.py`、`test_guidance_consistency.py`。 | 66 passed；1 個 `pytz` deprecation warning。 | 改動相關的 planner、呈現和 guidance consistency 測試通過；沒有代表全 repo 目前完整測試套件通過。 |

本次測試命令：

```bash
PYTHONPATH=scripts python -m pytest -q \
  tests/test_clarification_planner.py \
  tests/test_concept_answers.py \
  tests/test_guidance_consistency.py
```

該 live A/B 使用的 corpus SHA-256 為 `96e6d1a31c184cfb04621dc0f7d3887adcb8840a3657c617af66677d6874d6ec`，policy SHA-256 為 `a52d8476a7eca616b7ab908cfed71c01885c40cf7501cc266d1bc165c96a46ba`。Trace 不保存 credential；system prompt 以 hash 保存。

## 4. 為什麼這些修復有實際效果

1. **修在失敗發生的層級。** Trace/replay 顯示部分請求在模型已提出正確角色或粒度後，仍被 evidence validator、欄位 restoration 或 matcher 改壞。對這些案例，修改確定性程式比加重 prompt 指令更直接，也更容易重現。
2. **依使用者可驗證的原文保留事實。** 明確角色、粒度和目前目標由 witness 支持；假設仍標成 inferred/unconfirmed。這減少把模型推論呈現成使用者已確認資訊的風險。
3. **限制 ontology 修正的適用範圍。** 例如只在明確 patient-clustering goal 下套用唯一合法的 aggregate 粒度，避免把同一種對齊規則擴大套用到 TF activity 或其他網路 artifact。
4. **把 clarification 從「猜工具」轉成「選科學假設」。** 候選方法以目標 artifact、實驗粒度、調控角色、演算法假設和必要輸入拆解；使用者可以依自己的實驗設計回答，而不必先熟悉 NetZoo 工具名稱。
5. **以 traces 和明確分母驗證。** Frozen replay 用完整呼叫序列限制可比較樣本；live A/B 使用相同 5 個 prompts 和兩份契約；離線測試則只聲稱 renderer/planner 的 deterministic behavior。這些證據層級不混為單一 accuracy 數字。

## 5. 尚未完成與論文主張邊界

- **首要待修：** ambiguous guidance 尚未回答時，`requested_outcome` 必須保留 `unknown` 粒度；evaluator 必須檢查 outcome、hypotheses、route status 和 clarification 是否互相一致。
- **Claims 全面表現仍需驗證。** Frozen replay 有 3/65 個完整覆蓋 trials 未通過 reviewer completeness；5-prompt live round 只涵蓋定向案例，不足以升級 claims 為 production default。
- **P1 協同 TF+miRNA 的 fresh live round 證據不足。** 已有保存輸出的確定性重播，但須與新 prompt、重複試驗區分。
- **sample-as-network-node 的 F5 缺 live 壓力測試。** 歷史測試中觸發次數少；可在新 prompt 上定向驗證，不應由低觸發次數推論已完全解決。
- **本次的 10/10 不是原始 prompt 的線上模型評估。** 當前回合沒有送出新的 provider request，也沒有執行 workflow；若論文要主張端到端語意路由改善，需另報 live prompt、模型/設定、重複次數、錯誤定義及可重現 trace。
- **不應把單次 5/5 寫成全面 100% accuracy。** 合適寫法是「在預先指定的 5 個定向案例、每案每契約一次的 bounded A/B 中，兩契約皆為 5/5 通過」，並立即說明狀態一致性缺口。
- Claims contract 依先前交接紀錄仍未升為 production default；這次測試未改變該決定。

截圖中的 `prompt_seq` desktop protocol/schema 錯誤，使用者已表示另行處理完成。本報告不推測那項修復細節，也不把它併入 semantic-routing 成效數字。

## 6. 可供論文改寫的結果敘述

> 我們依據逐 trial routing traces 將語意路由失敗拆解為 request interpretation、evidence validation、欄位還原、capability matching 與 reviewer completeness 等階段，並針對明確粒度、regulator/target 角色及歷史/目前目標加入受限的 deterministic witnesses 與 ontology checks。對候選 workflow 的澄清則使用註冊能力差異排序，並回報各方法的科學前提、必要輸入及輸出型別。2026-09-24 的定向 live A/B 包含 5 個案例、兩種語意契約及 26 次 provider calls；兩契約在該 bounded set 均為 5/5 通過，且未觀察到錯誤推薦、fallback 或 workflow execution。完整 frozen-response replay 中，legacy 有 70/96 個目標 trials 具完整呼叫序列覆蓋，覆蓋 trials 為 70/70 通過；claims 的完整覆蓋為 65/96，其中 62/65 通過。由於測試分母、呼叫覆蓋率和重複設計不同，這些數值不應合併為單一 accuracy。另在 5-case live A/B 中發現一項尚未解決的狀態一致性問題：系統提出粒度澄清時，claims 的結構化結果仍可能暫存為 `sample_specific`。因此，結果支持定向路由改善與確定性修復的可行性，但尚不足以宣稱完整語料上的普遍正確性。

正式論文使用前，應將上述敘述改寫為符合研究設計的 Methods/Results，並引用實際 prompt corpus、trace、程式版本與 preregistered pass criteria；不要只引用本摘要中的總結句。

## 7. 可重現資料與內部來源

- [2026-09-23 semantic-routing handoff](2026-09-23-semantic-routing-handoff.md)：F1–F7、N1 根因、修正方式、歷史測試限制與 production-default 狀態。
- [2026-09-23 open issues](2026-09-23-open-issues-for-agent.md)：round-6 問題盤點；視為當時快照，後續狀態以較新的 follow-up 為準。
- [P1 coordinated-role follow-up](2026-09-23-p1-role-both-live-validation.md)：保存回應重播、角色修正和 bounded live criteria/results。
- [P2 granularity witness audit](2026-09-23-p2-granularity-witness-follow-up.md)：positive/negative witness phrasing 與跨語料 audit。
- [P3 scoped ontology alignment](2026-09-23-p3-scoped-ontology-alignment.md)：patient-clustering artifact 的限縮式 ontology 對齊及 P2 guard。
- [P4 advice-to-explain root cause and authorization](2026-09-23-p4-legacy-review-root-cause.md)：授權後的 advice/guidance `explain` evidence 修正及 replay。
- [2026-09-24 current-source frozen replay](2026-09-24-current-source-frozen-replay.md)：完整呼叫序列覆蓋率、通過數與殘餘 reviewer failures。
- [2026-09-24 evaluator trace capture](2026-09-24-evaluator-trace-out.md)：`--trace-out` 的欄位、隱私邊界和驗證範圍。
- [2026-09-24 live semantic contract A/B](2026-09-24-live-semantic-contract-ab.md)：5-case、26-call live A/B 數據與尚未關閉的粒度狀態不一致。
- [2026-09-24 terse guidance routing follow-up](2026-09-24-terse-guidance-routing-follow-up.md)：短工具詢問、單 workflow guidance promotion 和 saved-response replay。

## 8. 工作樹狀態

本報告整理的是截至 2026-09-24 已留下的程式與研究紀錄。Repository 仍有多個未提交修改，且部分檔案由前一個 session 留下；本報告不代表這些變更已全部提交、已在乾淨 checkout 重現，或屬於單一 commit。整併前應依既有 handoff 分開確認修改來源，避免 reset/checkout 覆蓋工作。

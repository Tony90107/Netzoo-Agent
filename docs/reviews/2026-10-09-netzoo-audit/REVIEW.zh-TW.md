# NetZoo Agent 全面檢查 — 2026-10-09–10

**判斷：目前具備相當完整的研究工作流程與治理基礎，但仍有會影響分析可信度、結果保存及桌面交付的缺口。建議先修復本報告的 P1，再擴充新演算法。** 這不是對架構的全面否定；最需要補強的是「執行是否真的成功、產物屬於哪次執行，以及使用者能否可靠地控制它」。

檢查涵蓋架構、科學輸入／輸出契約、執行與恢復、桌面互動、資料生命週期、測試、部署與可維護性。這是有界的跨層審查，並非每行程式、每個模型或全部生物學案例的正確性證明。

**版本與證據範圍**

- 工作區：`/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`；分支 `evidence-contract-grounding`；HEAD `5e90a7f8e610473d0337ecb6ac54d1f9f3a3c9ec`。
- 2026-10-09 晚間（Asia/Taipei）檢查當下的工作樹；2026-10-10 完成證據與交付核對。開始時已有未提交修改，期間其他 capability-check 檔案亦持續變動。因此測試數字是本次執行時的觀測，不是對後續變動的保證。未修改產品程式；僅新增本報告與證據。
- Graph：`Users-chenzhonghan-Documents-LLM-AGENT-netzoo_agent`，full generation `2026-10-09T10:34:45Z`，ready。以 Auditor 規格處理本文的有界判斷：graph 定位、相關雙向 trace、精確 source 與 coverage 檢查；結果分頁已讀完。
- Graph 對通用名稱如 `get`、`join`、`close` 有明顯誤連，故未以 fan-in/fan-out 數字判斷架構品質。`App.test.tsx:10`、`FilesPane.test.tsx:7` 的 parse gap 已直接讀 source；`data/paths.py`、`evaluation/plan_review.py` 的 metadata changed 已直接核對 source。這些檔案沒有本次造成的產品差異。排除的 cache、研究資料與大型 CSV 不用來證明不存在功能。
- Docker daemon 未啟動，未執行真實容器中的數值回歸或生物學分析，亦未發起新的付費 LLM 呼叫。原生 Tauri 打包／CSP 實機驗證未完成。
- Vite 介面已開啟；正式首頁顯示 daemon 無回應。另以**實際 React 元件＋合成 props**測試輸入、計畫、核准與斷線畫面，截圖明示 fixture。這不是完整桌面端到端通過的證據。

**實際驗證結果**

| 驗證 | 結果 | 解讀 |
|---|---|---|
| `/opt/anaconda3/bin/python -m pytest tests -q --tb=short` | 3,449 passed、35 skipped，102.53 秒 | 一般回歸通過；容器 gated 測試不可算通過 |
| `npm test -- --reporter=dot` | 25 個檔案、117 tests passed | 元件與單元測試通過 |
| `npm run build` | 失敗，TS2322 | 目前不能經正常流程重新打包桌面版 |
| 故障注入：DRAGON API unavailable＋既有產物 | 錯誤被整理成 success | F1 已重現 |
| 產物驗證：PANDA inf、LIONESS NaN/inf | 通過驗證 | F2 已重現 |
| 同 session 輸出／既有結果檔 | 同名、plan approved、替代命令覆寫 | F3 已重現，僅操作暫存檔 |
| 斷線送出、取消 HTTP 503 | 丟失送出／沒有取消失敗提示 | F5、F6 已重現 |
| 不再輸出訊息的已死 worker | 關閉後仍留 3 個 pump threads | F7 以最小測試替身重現 |

完整原始輸出在本資料夾的 `evidence/`。35 個 skip 包括整個數值回歸檔的 34 個項目與 1 個 SAMBAR container gate；現有數值測試已涵蓋 PANDA、PUMA、COBRA、CONDOR、OTTER、GIRAFFE 與多種 LIONESS，不能再沿用舊文件「只有 SAMBAR 有 numeric check」的說法。

**已確認問題：5 個 P1、3 個 P2**

P1 表示正式分析／發布前應修復；P2 表示特定條件的可靠性或可用性缺口。F8 是 source/config 層面已確認的不一致，其原生執行影響仍需 Tauri 驗證。未把單純功能偏好列成 bug。

| ID | 優先 | 問題 | 使用者影響 |
|---|---|---|---|
| F1 | P1 | 執行失敗可能被舊產物掩蓋為成功 | 把前一次網路當成這次分析結果 |
| F2 | P1 | PANDA/LIONESS 產物的非有限數值未被擋下 | 無效網路仍被宣告驗證通過 |
| F3 | P1 | session 隔離不等於 run 隔離；重跑可覆寫 | 失去先前結果與可靠比較基準 |
| F4 | P1 | 前端測試全過但正式 build 失敗 | 使用者無法依標準流程重新安裝／打包 |
| F5 | P1 | 斷線時仍能送出，先清除問題再嘗試傳送 | 訊息未送達、畫面可能卡在 Connecting |
| F6 | P2 | 取消請求沒有檢查回應、錯誤被吞掉 | 不知道運算是否仍在繼續 |
| F7 | P2 | worker 異常退出後 pump 沒有可靠收尾 | 長駐 daemon 累積執行緒與相關資源 |
| F8 | P2 | 可設定 daemon port，CSP 卻只允許 8765 | 換 port 後桌面可能無法連上 |

**F1 — 執行器與結果解析器的錯誤格式不一致。**

[execution.py:810](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/execution.py:810>) 回傳 `DRAGON execution failed; error: ...`；[results.py:54](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/results.py:54>) 只讀取行首 `error:`，而 hard-failure markers 不包含這種 execution-failed 格式。後續只要既有檔案通過 artifact check，便在 [results.py:125](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/results.py:125>) 產生 success。

重現使用真實 `run_dragon` 與 `structure_tool_result`，只將 API loader 替換為拋出 RuntimeError：raw 明確說執行失敗、舊檔 mtime 完全沒變，結果卻是 `status=success, errors=[]`。已確認 DRAGON 路徑；OTTER／LIONESS-DRAGON 亦使用相近字串，應列為修復時的回歸範圍，不冒稱本次逐一重現。

建議讓 executor 直接回傳 typed execution outcome，錯誤不得再靠展示文字推斷。每次 run 綁定自己的 output manifest／artifact IDs；明確失敗必須優先於任何檔案存在與結構驗證。驗收至少包括「API 失敗＋舊有效產物」「API 失敗＋無產物」「API 成功但沒有本次新產物」。

**F2 — 結構驗證把 numeric 當成 finite。**

[artifacts.py:104](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/data/artifacts.py:104>) 只用 `isna()`，所以正負 infinity 被接受；[artifacts.py:150](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/data/artifacts.py:150>) 對 LIONESS `.npy` 只檢查非空、維度與 numeric dtype，甚至全由 NaN/inf 組成也能通過。

重現：PANDA 兩條邊的權重為 inf／-inf → artifact ok、result success；LIONESS 2×2 全非有限陣列 → artifact ok。此處驗證的是 gate 缺口，不表示正常資料一定會讓 upstream 產生這些值。

建議按 artifact 語意定義有限性、shape、ID 與 sample coverage；大型陣列採分塊驗證。NaN 若是某種產物的刻意表示（例如非邊位置），須有明確例外，不能一律接受。DRAGON validator 已有 finite check，可作一致性參考；勿把整個專案說成完全沒有數值驗證。

**F3 — 同一實驗中的不同執行會共用檔名。**

[session_outputs.py:28](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/session_outputs.py:28>) 只隔離到 session；[discovery.py:152](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/discovery.py:152>) 用 expression basename＋method 決定輸出。[plan_review.py:464](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/evaluation/plan_review.py:464>) 保護的是 input/output 相撞，不是舊結果；[command.py:109](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/command.py:109>) 只記錄原來的 size/mtime，並允許覆寫。

同一 session 兩次預設 PANDA 都是 `outputs/sessions/audit/panda.tsv`。另以暫存既有結果建立真實 plan，仍得到 ready／approved；用同一 command runner 執行良性替代命令，舊結果直接變成新內容。未跑實際 PANDA，也沒有覆寫使用者檔案。

建議改成 `outputs/sessions/<session>/runs/<run-id>/`，先寫 staging、全部驗證通過才發布 manifest；保留「最新結果」索引方便 UI。明確指定既有路徑時顯示衝突，提供另存／顯式取代。COBRA、SAMBAR 都有 `manifest.json`，同 session 切換方法也應納入衝突測試。

**F4 — 型別契約變了，test fixture 沒有跟上。**

[fixtures.ts:73](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/desktop/src/test-support/fixtures.ts:73>) 的 `makeOption` 未提供必填 `compare_actions`；該欄位見 [contracts.ts:186](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/desktop/src/generated/contracts.ts:186>)。Vitest 轉譯測試不代表 `tsc --noEmit` 會過；目前 build 因 TS2322 結束。

建議補齊 fixture 的真實預設值，將 typecheck/build 與單元測試並列為發布門檻。不要修改生成契約來遷就缺欄位，也不要單純把測試從型別檢查排除。未實際完成 Tauri binary build，因此還可能有其後的原生建置問題。

**F5 — 斷線狀態沒有鎖住輸入，傳送也沒有 ACK。**

[Conversation.tsx:100](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/desktop/src/features/conversation/Conversation.tsx:100>) 只看 stopped/view/busy；斷線時原有 view 仍在。 [session.ts:253](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/desktop/src/transport/session.ts:253>) 先把 view 清掉、加入使用者訊息，才呼叫 send；send 不檢查 socket readyState，也沒有送達確認或失敗還原。

實際元件在 Reconnecting 時仍能觸發 Execute callback。transport 替身模擬 closed socket 丟棄 send 後，得到 `view=null, busy=false, sent=null`，使用者訊息卻留在畫面。重連僅從上個 seq 續接；若 server 沒有新事件，舊問題未必會重播。此問題會造成未送達／卡住，不是繞過後端執行授權的證據。

建議離線時保留草稿並停用提交／核准；加入 client message ID、ACK、明確 pending/failed 狀態與 reconnect snapshot。重試需 idempotency，避免把舊核准重送為第二次執行。

![實際元件：底部 Reconnecting，Execute 仍觸發 callback；頂部明示合成 fixture](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/reviews/2026-10-09-netzoo-audit/evidence/disconnected-approval.jpg>)

**F6 — 取消的失敗被隱藏。**

[session.ts:290](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/desktop/src/transport/session.ts:290>) 未檢查 HTTP `ok` 或後端 `{interrupted:false}`，catch 也不呈現任何結果。模擬 HTTP 503 後只留下「Requested interruption」，沒有錯誤事件。這雖沒有明說已停止，但使用者無法知道請求是否有效。

建議呈現 cancelling → interrupted／failed，只有收到後端確認才顯示已停止；逾時或失敗時提供可理解的錯誤與重試。測試 HTTP 401/404/503、網路拒絕、interrupted=false，以及取消後仍傳回晚到事件。

**F7 — worker 死亡時 pump 可能永久等待。**

[supervisor.py:267](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/server/supervisor.py:267>) 用無 timeout 的 `from_worker.get()` 等 sentinel；[supervisor.py:180](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/server/supervisor.py:180>) close 只往 inbox 發 cancel，必要時 terminate worker，沒有喚醒 outbox pump 或 join pump。

模擬已死亡、未送 sentinel 的 worker，建立／關閉 3 次後 supervisor sessions 為空，但 3 個 pump threads 仍存活。尚未量測真實多小時記憶體增長；可以確認的是收尾路徑不完整。

建議採有 timeout 的 queue read＋process liveness check／可靠 stop event，保存 thread handle，close 時 join 並關閉 queue，確保 abnormal exit 也發出 stopped。不能只依賴 worker 自己正常收尾。

**F8 — 自訂 port 與 CSP 的允許範圍不同。**

[lib.rs:133](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/desktop/src-tauri/src/lib.rs:133>) 讀取 `NETZOO_DAEMON_PORT`，但 [tauri.conf.json:24](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/desktop/src-tauri/tauri.conf.json:24>) 的 connect-src 固定為 localhost port 8765。HTTP/WS 換成其他 port 時不在該允許清單內。

建議要麼正式限定並驗證固定 port，要麼由受控 IPC／一致的設定生成支援 port 的連線方式；不應靠把 CSP 整體拿掉處理。驗收必須用正式 Tauri build 測預設 port 與一個自訂 port；本次只完成 source/config 驗證。

**架構：保留主幹，優先修補三個邊界**

現有優點有具體程式與測試支撐：CLI/GUI 共用 ConversationMachine；workflow registry＋typed plan＋Plan Evaluator；一個 session 一個 worker 隔離執行旗標；輸入角色／生物 ID 檢查；bounded recovery；session、trace、報告與產物檢查；桌面 token、outputs path containment 與大型文字分頁。這些能力值得保留。

| 邊界 | 現況與風險 | 建議的漸進方向 |
|---|---|---|
| Executor → Result Evaluator | 外層 typed，內層仍把自然語言字串重新解析為成功／失敗；F1 已證明其後果 | 由 adapter 回傳 typed status/error/artifact facts，文字只負責顯示 |
| Session → Run → Artifact | 有 session，輸出卻缺少不可變 run 版本；F3 | 增加 RunRecord 與 ArtifactManifest，session 負責組織，run 負責重現 |
| GUI → transport → worker | view 有序號，送出的請求沒有完整交付狀態；F5/F6 | ACK/idempotency、snapshot resync、取消狀態機 |

其他維護風險：`runtime.set_runtime_value` 會掃描已載入 modules 改寫全域設定，目前靠 process isolation 保護；若未來做常駐多任務 worker，不能直接共用。`planning/evidence.py` 的 `_build_evidence_ledger` 約 523 行、`outcome_matching.py` 的 `_match_semantic_request` 約 289 行，處理多種理由的變動，值得依「資料角色解析／preflight／預設輸出」與「理解結果／候選相容性／澄清」拆出可測試邊界，而不是為了檔案長度再添 facade。

`environment.yml` 的多數科學套件與 LangChain/LangGraph 只有範圍限制，固定 netZooPy commit 不等於整個環境可重建。建議每個正式 image 保存 lock／resolved package 清單、image digest、netZooPy ref 與本地 patch hash；每個 run 引用該 runtime identity。先保住 single-user local desktop 的正確性，再考慮多使用者服務化。

**使用者體驗：最有價值的是把現有能力接成完整旅程**

| 使用階段 | 已經有 | 目前主要摩擦 | 值得補的功能與可驗收結果 |
|---|---|---|---|
| 安裝／第一次啟動 | setup、Environment、故障 remedy | 原始碼建置、Docker、大 image；README 明示 app 需留在 repo | 安裝預檢＋進度／可恢復建置；可記住 workspace，將來再處理簽署發佈 |
| 選研究方法 | Method guide、研究選項卡、澄清 | 對新使用者仍容易變成「先懂工具才能回答工具問題」 | 以研究目的開始，給「可以回答／不能回答／需哪些資料」的可操作範例 |
| 匯入資料 | 路徑抽取、workspace discovery、role/content checks | UI 仍主要要求 full path 或 field=path；container 只能看到 mounted project | 檔案選擇／拖放＋明確匯入工作區；資料預覽與角色欄位；確認複製位置 |
| 修正資料 | backend 有格式、ID、alignment gate | validation 描述常是技術欄位，修正仍靠聊天文字 | QC 面板：行列方向、樣本／特徵數、缺失、ID overlap／丟棄明細；逐項改後重驗 |
| 核准計畫 | ready state、evidence、steps、plan hash | PlanCard 沒呈現 decision/step.arguments 參數，關鍵設定仍散在文字 | 可展開參數與來源（你指定／預設／推定）、預期輸出、覆寫影響、資源預估；更改後產生新 hash |
| 等待／恢復 | trace、Activity、Interrupt、resume | 連線／取消回饋缺口；背景作業控制尚不完整 | job 狀態、可靠取消、從可重跑 step 恢復；不把 session resume 宣稱為演算法 checkpoint resume |
| 看懂結果 | Outputs、table/text 預覽、npz shape、報告 | 能找到檔案，但數值品質和生物意義還需自行接工具 | workflow-aware result overview：QC、edge/weight 分布、top regulators、樣本 coverage；附來源與限制 |
| 比較／分享 | 2–4 session Compare、tags、model、inputs、notes | 現有比較偏 metadata，不是結果差異分析 | 先補每次 run 的參數／環境／校驗碼差異，再做網路差異、gene targeting 或其他已定義分析 |

資料匯入與 parameter editor 必須繼續通過現有 gate。不要為了方便把整個主機目錄自動掛進容器，也不要讓前端更改未重新審核的 plan。

**科學可信度與結果功能**

建議把「命令完成」「結構有效」「數值有效」「適用於研究問題」分成可辨識的狀態。目前 typed status 與 artifact gate 已存在，但 F1/F2 表明它們不足以支撐單一「成功」結論。結果頁應顯示完整／保留／排除樣本數、feature overlap、數值異常、方法假設與資料限制，並讓使用者看到被移除的識別碼。

不要把不同方法的 edge scores 直接當成同一量尺。官方 LIONESS 文件把 sample-specific network 與下游比較視為可接續的研究步驟，也列有 limma 和 differential targeting 的教學；可把它當成果分析路線的參考，而非宣稱現在的 Compare 已有推論統計。[官方 LIONESS 介紹與 netbooks](https://netzoo.github.io/zooanimals/lioness/)

運算前的規模檢查應整理成共通 UI：預估矩陣／邊數、記憶體下限、儲存量，先提供 subset pilot，數值不夠可靠時不要硬給 ETA。已有部分 workflow size gate，應把它們呈現並統一。官方 LIONESS CLI 亦提供 subset、precision 與逐樣本保存選項，可用來設計有依據的資源規劃。[netZooPy CLI 文件](https://netzoopy.readthedocs.io/en/stable/functions/cli.html)

**效能、隱私與品質治理**

- 可見歷史 `r8-report.md` 的兩個方法諮詢例子用了 5／6 次模型呼叫、12,697／17,242 tokens。這是既有記錄，不能當成本次版本的 latency／成本基準。應用現有 replay／routing grids 加上 calls、tokens、p50/p95 latency、clarification turns、最終完成率；避免只追分類正確率。
- 測試本身很豐富，缺口在門檻連結：unit／contract、typecheck/build、真實 image 數值回歸、桌面 user journey 必須分開報告。`--fail-on-skip` 已存在，應在指定的 release suites 啟用，不能把預設 gate 的 skip 算成安全證據。本文沒有宣稱 repository 完全沒有 CI；本次只未見根目錄 `.github/`。
- 保留現有 token 與路徑邊界。增補使用者可理解的資料流說明：哪些請求／欄位／摘要會送給 LLM 或外部查詢、哪些只在本機；讓外送內容可預覽、可遮蔽。此為產品透明度建議，本次未確認未授權資料外洩。
- 有限預覽是優點；但完整 artifact validator 仍可能把大表／npy 載入記憶體，長對話的前端 trace/message 也持續累積。建議以有代表性的 10× 資料與長 session 量測後，再決定 streaming／chunking／virtualization；本次沒有大型效能測量。
- 文件漂移已可見：`DESKTOP_UI_ARCHITECTURE.md` 仍寫「尚未實作」與舊的約 93 失敗基準，部分測試 docstring 也仍說只有 SAMBAR 有數值回歸。應明示歷史設計與現行規格，讓 README 指向維護中的驗證結果。

**建議工作順序與驗收**

| 順序 | 工作包 | 完成條件 |
|---|---|---|
| 1 | 執行真實性：F1＋F2 | 失敗＋舊產物必定 failed；非有限網路不被稱為有效結果；錯誤是 typed |
| 2 | 結果保存：F3 | 每次執行版本可追溯；重跑／失敗／中斷不破壞前次成功產物 |
| 3 | 可交付桌面：F4＋F5＋F6 | typecheck/build 通過；斷線不掉草稿；核准有送達狀態；取消有結果 |
| 4 | 長駐可靠性：F7＋F8 | abnormal worker 清理測試；正式 Tauri 預設／自訂 port 驗證 |
| 5 | 完成第一個真實研究旅程 | 新使用者能自行匯入、看 QC、改欄位、核准、看結果、重跑並比較 |
| 6 | 增強研究價值 | immutable run 導出、標準化結果摘要、參數比較，再依使用者任務增加下游分析 |

此階段不優先投入更多 workflow 名稱、全面更換 agent framework、多人協作或複雜 workflow canvas。它們不能直接修復這次已重現的可信度與操作問題。若要驗證產品方向，選幾位沒有參與開發的研究者，給真實但可分享的資料，量測「首次成功分析時間」「自行修正輸入的比例」「是否能正確解釋結果與限制」，比再加一批按鈕更有價值。

**重現與證據使用方式**

從 repository root 執行：

```bash
/opt/anaconda3/bin/python docs/reviews/2026-10-09-netzoo-audit/evidence/reproduce_backend.py .
node docs/reviews/2026-10-09-netzoo-audit/evidence/reproduce_transport.mjs .
```

需本機 Python 分析依賴與既有 desktop node_modules；不需要 API key、Docker 或網路。backend probe 只操作暫存檔，故障注入與 worker 為測試替身；transport probe 使用真實 SessionSocket，network 為替身。`source-sha256.json` 記錄關鍵來源版本；`backend-probes.jsonl`、`transport-probes.jsonl` 保存結果。UI fixture 要在 desktop 根目錄暫時還原為 `audit-review-20261009.html/.tsx` 兩檔再經 Vite 開啟；不可把 fixture 當正式 app。

本報告沒有修復以上問題；它交付的是可定位、可重現、可安排優先順序的審查結果。

# NetZoo Agent 修復與改善清單 — 2026-10-10

目標：正確理解使用者要的結果，既不把做不到的事承諾成能做，也不把可做的事錯誤拒絕；執行後的成功宣告必須對應本次有效產物。

原始開發清單依 10 月 9–10 日審查、能力判定核對及 Logs 398–402 整理，以 `8e6f2a9` 為原始基準。問題證據見 [審查報告](REVIEW.zh-TW.md)；原始能力實驗見 [f10](../../research-log/capability-traps-2026-10-08/heldout-live/f10-analysis.txt)／[o10](../../research-log/capability-traps-2026-10-08/heldout-live/o10-analysis.txt)。已撤回的候選不算現有功能，歷史數字不算目前產品的整體準確率。

**10 月 10 日中午版本接手狀態**：Log 403 A／B／C 通過凍結的 n11／s11 比較門檻；本次另修正五個判定／選項問題及評估工具。第 1 項的這一輪評估已完成；2–6 有已驗證修正，但仍有方法問句漏抽、混合需求誤拒絕／遺漏及卡片矛盾，不能整批標為完成。7–20 未因本次工作而完成。版本、數字、實際修改及剩餘驗收見 [接手報告](MIDDAY-TAKEOVER.zh-TW.md)。

優先順序分為：A 核心能力判定；B 執行可信度；C 桌面可靠性；D 使用旅程；E 持續交付。A 與 B 都是主要發布門檻。C 中 F4 build 問題可先獨立處理。D 是功能改善，不全部屬於已重現 bug。

**A｜意圖理解與能力判定：最優先**

1. **建立同時約束誤承諾與誤拒絕的評估門檻。**
   - 問題：只減少「瞎掰」可能增加「明明能做卻拒絕」；總分也可能掩蓋混合需求退步。
   - 修法：既有案例保留作回歸；另外凍結未看過的題組，涵蓋完全支援、不支援、近似、部分支援、缺資料、歧義、方法問句、多輪修正與服務故障。加入同一意圖的不同說法，以及只差一個必要條件的最小對照。先測理解，再測能力判定，最後獨立檢查完整回覆／卡片／操作。
   - 驗收：分開報告誤承諾、誤拒絕、部分需求完整交代、需求遺漏、澄清有效性及未確認比例；不得靠把所有題目都轉成澄清來過關。新增數值門檻須在實驗前凍結，不能看結果後放寬。關鍵案例人工複核；LLM 標註保留疑難與分歧。重複抽樣不當成獨立題目。
   - 範圍：`tests/test_capability_check.py`、routing／outcome 測試、既有 research-log 評估工具。若中文輸入屬於預期使用範圍，另建中英混合輸入題組；產品回覆語言遵守既有英文規範。

2. **方法問句也要抽出功能要求，混合需求要逐項拆解。**
   - 問題：「有沒有能整合 miRNA 的方法」可能被歸為純方法諮詢，miRNA 條件沒有進入能力檢查；「找社群，再做互動式 3D」可能被整句判成不能做。
   - 修法：保留諮詢／執行意圖，但讓諮詢也能含有結果要求。每項要求保存原文、目標結果、必要條件、資料事實與相依步驟；不要把使用者的資料描述或否定條件當成新要求。同一句中可做與不可做部分分開，無法拆清時標示待確認。
   - 驗收：陳述句與方法問句得到一致能力結論；只問原理不變成執行；部分可做時保留可做部分、明列缺口；背景句和否定句不造成誤判。
   - 範圍：`contracts/capability_check.py`、`graph/capability_check_call.py`、`interpretation/capability_check.py`。

3. **讓能力配對覆蓋完整必要條件，避免相近工具冒充精確答案。**
   - 問題：現有型別檢查已涵蓋部分資料與粒度，重疊社群、時間動態、空間形式等仍可能被錯配。
   - 修法：對已確認的差異增補具執行器依據的能力欄位；先核對實際產物，再決定表示方式。逐項驗證必要條件，不因基本結果名稱相同就算完整支援。未知條件不能默認已滿足，也不能因為表中缺欄位就武斷判不支援。候選的不同參數／流程組合也要說明範圍。
   - 驗收：普通／重疊社群、每樣本／動態網路、一般／空間平滑結果等最小對照分清楚；同時保住正常 CONDOR、LIONESS 等對照。Logs 399、402 的撤回候選只能作參考，不能直接視為合格修復。
   - 範圍：`scripts/capability_sheet.yaml`、capability sheet loader、能力相容性與配對層。

4. **統一逐項判定，修正局部候選失敗被說成整題不能做。**
   - 問題：能力檢查與 hypothesis/routing 回覆可能互相矛盾；SC1 是已有實驗證據的案例。
   - 修法：建立每項需求的共同判定來源，回覆、卡片、候選與下一步都從它生成。某個解讀沒有 workflow，只能否定該解讀；已經有合理可行解讀時，不得宣告整題不支援。不要直接刪掉所有「不支援」句子來掩蓋問題。
   - 驗收：把 SC1 固定 decision 重放為確定性回歸；文字、選項、按鈕與最終能力狀態一致；能做的部分不被另一個無效候選蓋掉。
   - 範圍：`interpretation/hypothesis_routes.py`、`graph/router_invocation.py`、reply cards 與共同 decision 契約。先以 graph 定位具體 renderer 消費端再修改。

5. **分開「功能支援」與「現在能否執行」。**
   - 問題：缺資料、環境未就緒、需要外部步驟、能力不支援及理解不確定，不能都落成同一個「不能做」。
   - 修法：沿用並釐清現有狀態的語意：直接支援、支援但缺條件、部分／外部步驟、不支援、未確認。能力判定與執行準備狀態分開保存；回覆列出最小缺口及下一步。外部步驟清楚標明由誰執行，不能承諾 agent 自動完成整條流程。
   - 驗收：已支援但尚未提供檔案時，要求所需輸入；已有不相容資料時說明原因；不確定時問能區分候選的問題；所有 ready plan 繼續經既有 Plan Evaluator。
   - 範圍：decision、capability check、applicability/data plan 與回覆整合。

6. **主檢查模型故障時，保留可探索選項，但不能把未確認變成承諾。**
   - 問題：已保留的 provisional 備援可降低誤拒絕，但故障實驗的誤承諾／含糊總數沒有改善到可放心的程度。
   - 修法：保留未確認狀態，與「已驗證符合」的推薦／執行路徑清楚分開。對備援肯定與否定都保留證據與來源；必要時恢復主檢查、澄清或讓使用者看明確條件後再決定。不要只加一句免責文字，下面仍完整承諾可以交付。
   - 驗收：timeout、空回覆、格式錯誤、429、預算耗盡時，不誤稱已確認，也不因檢查服務失敗而說功能不存在；檢查正常與故障兩套評估都獨立通過。換模型需量測成本、延遲與兩類錯誤，不視為自動解法。
   - 範圍：`graph/capability_check_call.py`、`graph/router_invocation.py`、`interpretation/capability_check.py` 及選項顯示層。

**B｜執行與產物：修復先前 F1–F3**

7. **F1：執行器直接回傳結構化結果。** `execution.py` → `routing/results.py` 不再靠展示字串猜成功或失敗。明確 error 必須優先，success 必須對應本次 run 的產物。驗收：真實 API 拋錯＋舊有效檔案必定 failed；成功但沒有本次輸出不可 completed；取消、dry-run 也不能混為成功。先建立共同 outcome，再逐個 adapter 遷移並核對消費端。

8. **F2：補齊數值與科學產物驗證。** 在 `data/artifacts.py` 依產物語意檢查有限性、shape、ID、sample coverage；大型陣列分塊讀取。明確記錄哪些 NaN 是允許的特殊表示。驗收 PANDA inf／-inf、LIONESS 全 NaN／inf 失敗，正常與合法特殊值仍通過；不得將「結構通過」等同「研究結論成立」。

9. **F3：每次執行擁有不可變的結果版本。** `session_outputs.py`、輸出規劃、`command.py` 與 plan review 加入 run ID、獨立目錄及 manifest；暫存產物完成後才正式發布，latest 僅作索引。驗收同資料重跑、參數改變、失敗或取消不破壞前次成功產物，舊 session 仍能讀取；現有產物不可被背景遷移覆寫。

**C｜桌面與長駐服務：修復先前 F4–F8**

10. **F4：修復正式 build。** 補齊 `desktop/src/test-support/fixtures.ts` 的 `compare_actions`，核對生成契約；不要放寬型別躲過錯誤。驗收 `npm test -- --reporter=dot` 與 `npm run build` 都通過，正式流程保留 typecheck/build 門檻。

11. **F5：斷線送出不可遺失，也不可重複執行。** `desktop/src/transport/session.ts` 與 server 協定共同加入 ready-state、草稿保留、client request ID、ACK、去重及重連 snapshot。ACK 前顯示待送達；高影響核准不在重連時盲目重播。驗收送出前後斷線、ACK 遺失、重連重試都不丟訊息、不重複跑分析，核准綁定原 plan 身分。

12. **F6：取消必須回報真正結果。** transport 檢查 HTTP 狀態與回傳內容，呈現 requested／cancelling／cancelled／failed；worker 確認停止後才顯示已取消。驗收 503、timeout、已完成與取消競爭、部分產物處理及安全重試。

13. **F7：worker 死亡後回收資源。** `server/supervisor.py` 的 queue pump 加入可中止等待、liveness／stop signal、thread join 與 queue 收尾；涵蓋 graceful close、abnormal exit、terminate。驗收反覆建立／關閉 session，thread/process 不持續累積；正常訊息不因清理順序遺失。

14. **F8：統一 daemon port 與 CSP。** `desktop/src-tauri/src/lib.rs` 與 `tauri.conf.json` 採一致策略：明確固定 port，或以受控方式支援自訂 port；不移除整體 CSP。驗收正式 Tauri 的預設與自訂／拒絕不支援 port 行為。此項目前是 source/config 不一致，原生影響仍待實機確認。

**D｜完成使用旅程：功能改善**

15. **資料匯入＋QC。** 檔案選擇／拖放、明確複製到 workspace、角色預覽；呈現行列方向、樣本／feature 數、ID overlap、缺失及排除清單。繼續經既有輸入 gate，不默默修正科學資料。驗收新使用者不用手打完整路徑，能辨識並修正一個輸入錯誤再重驗。

16. **計畫參數與資源預檢。** PlanCard 可展開必要參數、值的來源、輸出位置與資源估算；規模過大時提供合理 subset pilot。參數修改必須重新產生／審核 plan，不能保留舊核准。驗收可回答「這次到底跑什麼、需要什麼、結果存哪裡」；無可靠依據不顯示精確 ETA。

17. **結果摘要、重現包與比較。** 在 run 版本化後，呈現數值 QC、分布、樣本覆蓋與方法限制；保存輸入 hash、參數、環境與產物 manifest。先做參數／環境差異，再做有定義且尺度相容的網路比較。top regulators 等未實作計算須有明確衍生分析與驗證，不能只由文字生成。驗收兩次 run 可追溯、可比較，匯出包能在相同環境重現。

18. **首次啟動與資料流透明度。** 呈現 workspace、Docker／模型連線狀態、安裝失敗的恢復動作；說明哪些請求或摘要外送、哪些只留本機，並提供適當遮蔽。驗收乾淨環境能完成第一個真實旅程，使用者知道資料流向。簽署與安裝包發佈在本機建置可靠後安排。

**E｜維持可靠性**

19. **環境重現與發布門檻。** 保存依賴鎖定／解析清單、image digest、netZooPy ref 與 patch hash；能力表、workflow 規格及執行器同步驗證。發布分開呈現本機回歸、build、真實 image 數值回歸及原生桌面 E2E。指定 release suite 不能用 skip 代替通過；保留一般開發測試的合理 skip。驗收原先跳過的 35 個容器項目在所需環境下實際執行，並完成代表性研究旅程。

20. **量測後重構，並更新文件。** 記錄模型 calls、tokens、p50/p95 latency、澄清次數、完成率與長 session 資源；先量測大表驗證與 trace 累積，再決定分塊／串流／虛擬列表。隨上述修復抽離過大的理解與 evidence 函式；全域 runtime 改寫在引入共用 worker 前消除。更新架構、測試能力及模型備援說明，區分歷史設計與現況。驗收效能變更不惡化能力品質，文件與可執行驗證一致。

**建議實作批次**

- 第 1 批：1 建立基準與驗收 → 4 固定 SC1 矛盾回覆 → 2 方法問句／需求拆解 → 3 完整條件配對 → 5 統一狀態 → 6 故障退化。共同契約分階段演進，避免一次大改後無法歸因。10 build 是可獨立的早期修復。
- 第 2 批：9 run identity 的最小骨架 → 7 typed outcome → 8 數值驗證 → 完成 9 的保存與讀取。先讓舊產物不能冒充本次成功，再補完整產品體驗。
- 第 3 批：11–14 桌面／daemon。11 的 ACK 需前後端一起交付，不能只在前端加 disabled。
- 第 4 批：15–18 第一個完整研究旅程；17 依賴 9，16 依賴既有 plan gate 與更新後的核准身分。
- 19 作為每批發布門檻；20 在有量測與相關模組改動時推進，避免單獨展開全面重寫。

**驗證方式**

本次延伸核對的能力／routing 本機測試 224 passed；先前總回歸 3,449 passed、35 skipped，前端 117 passed、build failed。這些是不同時間與範圍的觀測，不可合成新的全量結果。本次未新增付費模型呼叫。

確定性回歸可從以下命令開始：

```bash
/opt/anaconda3/bin/python -m pytest tests/test_capability_check.py tests/test_capability_reachability.py tests/test_capability_corpus_coverage.py tests/test_outcome_matching.py tests/test_outcome_routing.py -q --tb=short
/opt/anaconda3/bin/python docs/reviews/2026-10-09-netzoo-audit/evidence/reproduce_backend.py .
node docs/reviews/2026-10-09-netzoo-audit/evidence/reproduce_transport.mjs .
```

後兩項是已知問題的重現探針；修復時要把相應結果變成有明確期望的回歸測試，不能以「探針程式正常退出」代表 bug 已修好。真實模型、容器科學運算與原生桌面驗證須各自記錄版本、設定、結果與限制。

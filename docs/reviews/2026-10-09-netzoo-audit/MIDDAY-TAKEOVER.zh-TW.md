# 10 月 10 日中午修改：評估與接手紀錄

結論：Log 403 的 A／B／C 候選通過原先凍結的比較門檻，值得保留；它確實降低誤承諾，沒有增加這份題組的誤拒絕。但通過門檻不代表已完全解決意圖理解。接手時另外發現五個確定性問題，已修正並加入回歸；這些新修正的證據與中午候選的模型測量分開保存。

## 版本與範圍

- 原始基準：`8e6f2a9`。
- 凍結候選 A／B／C：`c6e8c77`；實驗使用乾淨的 `netzoo-verdict-base`／`netzoo-verdict-cand` worktree。
- 中午後續 D：`7057a86`，將 routing 的 unknown 排除為「所有 workflow 平手」。D 沒有包含在 n11 的候選模型數字裡。
- 本次接手：在 `evidence-contract-grounding` 上補修 D 與逐項 verdict、第二意見、卡片／下一輪，以及評估工具；保留既有其他 session 的未提交修改。
- 本次沒有啟動新的真實模型實驗。使用中午已完成的錄製、補完盲標、確定性重放與本機測試。沒有修改乾淨的比較 worktree。

## 中午候選的評估已補完

n11：42 個英文題目，每題兩臂各 3 次，共 252 個 session。每臂 150 項需求，其中正例 87、負例 63。兩位獨立子代理各盲標全部 252 個 session／300 項需求；24 個 session 有分歧，已逐一複核並保留定案理由。重複抽樣是同一題的重複觀測，不當作獨立題目或產品整體準確率。

| 指標 | 原始基準 | 中午候選 |
|---|---:|---:|
| 誤承諾 FC（負例） | 9／63 | 3／63 |
| 誤拒絕 FR（正例） | 1／87 | 1／87 |
| 軟拒絕（正例僅說部分可做） | 3 | 0 |
| 需求遺漏 OM | 8 | 3 |
| 未確認 UC | 1 | 2 |
| 部分需求完整交代 PC | 9／15 | 12／15 |
| 陳述／問句一致 TW | 15／18 | 15／18 |
| 多輪最後判定 MT | 9／9 | 9／9 |
| 程式偵測矛盾／盲標矛盾 | 1／8 | 0／4 |

N-V1 與 N-G1–N-G9 全部通過；沒有放寬凍結門檻。全部 252 個回覆重放與原錄製相同，沒有缺失 session。分歧定案中，CONDOR 的輸入 thresholding 視為前處理；它不是取得 communities／core scores 所需的外部後續分析。routing 驗證失敗與 capability 已確認輸出分開判讀，理由保存於 resolved JSON。

s11：42 題、每臂各 2 次，共 168 個 session。沿用中午已保存的兩份盲標與 26 個分歧定案，重新驗證完整性與重放；S-G1–S-G4 全部通過。誤承諾 18 → 0，誤拒絕 0 → 0，但候選 100 項需求中有 87 項未確認、6 項遺漏。這證明故障時較少承諾，不能解讀為故障時仍能可靠完成科學判定。

依 FREEZE403 的保留規則，A／B／C 可保留，不需要觸發撤回 C 後的 B-only 重跑。這不是整個產品的發布批准；原先 B／C 類的執行與桌面問題仍是另外的發布門檻。

## 本次實際修正

1. **逐項 verdict 借錯其他需求的證據。** 原本在所有引文中取最長 overlap，edge-test 的判定可能被另一需求的 network scale 引文蓋掉。現在成果引文優先；一段跨多個成果不選其中一個代表全部；主要成果未匹配也不能借 scale／input 的判定。保留原 SC1 三筆錄製回歸，另測短引文與主要成果未檢查。
2. **部分 workflow 被列成完整替代品。** 原本 GIRAFFE=`all`、PANDA=`part` 會合併成「GIRAFFE 或 PANDA 都給完整需求」。現在按 requirement 分開完整／部分 credit，有完整方案時不混入部分方案，兩種答案順序結果一致。
3. **未確認選項被下一輪升格為已確認成果。** 原卡片的 `confirm_workflow` 會產生 `CONFIRMED_OUTCOME_ACTION`，丟失 splicing 等原需求，且 next prompt 還能提供 planning。現在選項是帶回原需求的 `follow_up`；未確認及尚未映射的 turn 禁止直接 continuation／planning。原執行核准 gate 仍存在；此問題是語意偷換，並非已證實的未授權执行。
4. **選擇已支援的一部分時改成 workflow 的主要產物。** 原「每樣本 TF activity」選項只確認 `run_giraffe`，下一輪會被修成 cohort signed network。現在保留原需求與選定成果文字，不使用 action-only confirmation。長引文的 answer 有長度界線，完整原需求仍由 follow-up context 帶入。
5. **routing unknown 卻把全部已確認的需求說成僅部分支援。** 回覆及卡片改讀相同的完整覆蓋條件：全部 result 已確認、無 unchecked、每項有 delivering entry 時，正確說明每項成果都有 workflow；部分支援則保留部分描述。

獨立唯讀覆核曾再找到「主要成果未匹配仍借 scale」及長 answer 導致卡片消失兩個漏網；都已補回歸並修正。

## 評估工具也已修正

- 原工具缺少盲標也能輸出 outage PASS；`zip` 會靜默忽略未標需求。現在兩位標註員、所有 session／requirement、enum、ambiguity、矛盾標籤與分歧定案都必須完整。
- 必須覆蓋凍結的全部 42 題、兩臂及重複次數；一份較小而完整的子集不能冒充完成的實驗。
- 必須與原錄製回覆重放相同，才允許計算 promotion gates。
- 舊基準有一筆卡片 overflow。實際 runtime 會保留文字並略過卡片；重放原本將整個 render 當失敗。現在忠實保留文字及 card error；168 筆 s11 重放均相同。

新修正另用中午候選的 210 個錄製 session（n11 126、s11 84）重放：0 render error、0 card error；一般回覆文字沒有變更、故障回覆 2 筆變更。未確認卡片不再提供 confirm／plan 的 next step。這是既存 decision 的離線證據，沒有重新量測新版本的模型理解率。

## 還沒解決的核心問題與下一步

1. **P1：結果問句仍可能被當作純方法介紹。** VN5q 的三次候選錄製都沒有 result requirement：問「每個時間點的 TF-gene edge 如何依賴前一個時間點」被放進 about_methods。這是本輪剩餘三次誤承諾的來源。應增加 routing／capability 之間的意圖一致性檢查；當其中一個讀到具體成果，另一個只說 methods question，不得直接提供完整符合的 workflow。重新拆需求或明確保持未確認；同時用真正的原理問題做正對照，避免全面拒絕方法諮詢。用新的未見過題组量測，不只改這句的關鍵字。
2. **P1：混合需求的二次驗證仍以整題 full_gap 啟動。** VC4s 有一筆把 CONDOR core genes 說成沒有 workflow，但同一回覆又介紹 core score，造成剩餘一筆誤拒絕。應按 requirement 找出 capability 與已知 workflow output 的分歧，再決定需不需要二次驗證；不能因其他部分已支援就跳過。多個 `part` 也不能累加當作整題 `all`。
3. **P1：矛盾檢查仍未覆蓋所有 renderer。** 候選剩餘四筆盲標矛盾：三筆 VT2 在否定重疊社群時，卡片仍說 CONDOR fits；另一筆是 core genes。应逐項绑定已确认需求與卡片 headline／badge，能力不支援只能提供明確放寬條件的替代方案。驗收必须读完整文字、卡片與下一輪任务，不能只查 opening paragraph 或少數關鍵字。
4. **P2：混合需求仍有遺漏。** VP1 的 dashboard、VP5 的 raw-read alignment 共三筆未完整交代。應保留原 request 的 requirement ID 與覆蓋追蹤，把背景／前置步驟與想要的結果分開；只有真正被交代的項目才能計為 addressed。

本次沒有把上述剩餘項目標為已完成，也沒有將原清單 7–20（執行產物、桌面、旅程、發布）標為修好。

## 證據與重現

- 原凍結規則：`docs/research-log/requirement-verdicts-2026-10-10/FREEZE403.md`。
- 完整標註／定案／分析：同目錄 `live/n11-labels-{A,B,resolved}.json`、`n11-analysis.txt`、`s11-analysis.txt`。
- 接手版重放：`live/takeover-replay.jsonl`；版本及 hash 記錄：`live/takeover-evidence-manifest.json`。
- 回歸：`tests/test_requirement_verdicts.py`、`tests/test_requirement_verdict_evaluation.py`。測試涵蓋真實 `_submit_option` 的任務生成，沒有呼叫模型。
- 完整 pytest、ruff 與 diff check 的最終結果記入 evidence manifest。35 個跳過項目不能當作已通過的真實容器／科學計算驗證；本次未重新做原生桌面、前端 build 或 Docker 科學計算。
- Graph generation `2026-10-09T10:34:45Z` 早於中午修改；已查相關 coverage，對 metadata changed／not tracked 的範圍使用當前精確 source／diff 與離線回歸，未把舊圖當成新版本完整性證據。

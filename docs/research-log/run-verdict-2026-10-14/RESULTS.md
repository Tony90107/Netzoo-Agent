# 判定層第 1+2 項：能力判定成為執行計畫的必要條件（2026-10-14）

## 背景

工程審查（923e493）重現了兩種錯：

- **選錯 workflow 仍保留 run**：能力檢查判 `other_workflow`。
- **只做得到一半，仍保留完整執行意圖**：能力檢查判 `partial_gap`。

自 3578b00 起，只有完全缺口（`gap`）會改變 run，其他判定都只是記錄下來。

使用者 2026-10-14 決定：

- 部分可做時，**一律不自動執行子集**，先說明並請使用者確認。
- 中文不進驗收門檻。

## 改了什麼

**一份判定紀錄 `RunVerdict`**（`contracts/capability_check.py`），掛在 `TaskDecision.run_verdict` 上。內容包括：

- run 的 workflow 與判定；
- 每項需求的狀態與可交付的 workflow；
- 沒讀到的句子；
- 是否已擋下、使用者是否點名；
- 這份判定對應哪一則請求（`request_sha256`，由 `classify_task` 蓋上）。

**第 1 項：路由**（`graph/router_invocation._on_run_verdict`）

只有下列判定保留 run：

| 判定 | 意思 |
|---|---|
| `agrees` | 全部直接可做 |
| `no_result` | 除了跑它，沒有其他需求 |
| `not_on_sheet` | STRING 下載，沿用自己的規則 |
| `no_check_model` | 只在測試與 harness 中出現 |
| `user_selected` | 使用者從前一輪選的 workflow，或延續已核可的計畫 |

其他判定的處理：

- **未點名的選錯 workflow**：清掉路由原本的選擇，交給詢問路徑同一套規則（`checked_match` + `_with_requested_run`）重新規劃。規劃成功就改跑能力檢查認可的 workflow，最多只到預覽。
- **其餘情況一律擋下**（`interpretation/run_hold.py`），包括：
  - 點名的選錯 workflow（說明衝突，不替換）；
  - `partial_gap`、`outside_step`（需要外部步驟）、`unread`（有句子沒讀到）、`unconfirmed`（檢查失敗或只有備援模型讀過）；
  - 重新規劃不成立的情況。

  擋下時，回覆會說明哪些可做、哪些不可做，並附「Plan X with my data」讓使用者確認。點選後走 continuation，判定為 `user_selected`，仍然只到預覽，必須再 `/execute`。

**第 2 項：Plan Evaluator 與執行入口**

- **Plan Evaluator**（`evaluation/plan_review._capability_verdict_item`）新增必要條件 `capability_verdict`。13 個分析 workflow 都必須有核可判定，而且判定的 workflow 與請求 hash 都要和這份計畫一致。資料檢查、查文件、下載仍用各自的規則。
- **執行入口**（`graph/execution._unapproved_run`）在執行器被呼叫前再驗一次：
  - 計畫評估必須是 approved；
  - 判定仍核可這個 workflow；
  - 判定仍對應目前這則請求。

  不符合就記錄 `tool.refused`，不呼叫執行器。

## 驗收

**故障注入**（`tests/test_run_verdict.py`）共 7 種狀態：

- 沒有判定
- 未確認
- 其他 workflow 才能完成
- 只做得到一部分
- 已擋下（即使判定是 agrees）
- 請求已改變
- 判定屬於另一個 workflow

結果：

- 每一種都被評估器拒絕，而且唯一失敗的條件就是 `capability_verdict`。
- `route_plan_evaluation` 不會走到 `execute_tool`。
- 偽造成 approved 後直接送進執行入口：執行器呼叫 0 次。
- 合法計畫：approved，執行器呼叫 1 次。
- 批准後若請求被換掉：執行器呼叫 0 次。

**完整流程**（`tests/test_graph_tracing.py`）：

- 點名 PANDA、但能力檢查認可的是另一個 workflow：沒有 `plan.approved`，沒有 `tool.started`，執行器呼叫 0 次。
- 能力檢查失敗：擋下，提供 PANDA 讓使用者確認。

**全部測試**：3639 passed。

**離線重播**（`replay_runs.py`）：r17/r17b 錄下的 29 個 run 路徑 session，不呼叫模型。

| 標準答案 | 之前會跑 | 現在會跑 |
|---|---|---|
| neg（8） | 0 | 0 |
| pos（18） | 16 | 14 |
| mixed（3，MX1） | 3 | 3 |

- 改變的只有 PS1-2 ×2：「compute TF activity per sample and compare it between tumor and normal」。GIRAFFE 加上外部統計步驟，從直接跑改成先確認。這是決定「不自動執行子集」的代價。若要讓需要外部步驟的 run 直接跑，只要把 `outside_step` 加進 `APPROVING_RUN_VERDICTS`。
- MX1（建網路並上傳公開資料庫）在錄下的檢查中漏讀了「上傳」，所以仍判 agrees。現行程式在 run turn 也會重讀（88d820a）；重讀若讀到「上傳」，就會判 `partial_gap` 而擋下。這一步需要真實模型確認，**尚未 live 驗證**。
- r17/r17b 的檢查全部是 confirmed（0 次 provisional），所以「檢查失敗就擋下」在這批資料中沒有成本。但免費額度用完、只剩備援模型時，每個 run 都要多按一次確認。

## 尚未做

- 沒有跑 live。這次改的是程式判斷，不是模型讀法；依 lean-testing 原則，用單元測試與離線重播即可。若要 live，建議只跑 run17 的 MX1、PS1，加上 3 題點名錯 workflow 的題目，各 1 次，共 5 個 session 以內。
- 第 3 項（scale 有原文依據時才成為硬限制）尚未開始。

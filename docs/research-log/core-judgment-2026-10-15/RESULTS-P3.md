# 第 3 階段：回覆收斂——round p3 與 G2 重跑 p3b（2026-10-16），以及四個階段的總結

## 結論

- **第 3 階段通過**（一次修正並重跑，在 spec 上限內）。
- 56 題的回覆全部由各自判定允許的路徑產生，不一致為 0（p1 為 8、p2 為 4）。
- 四態成本分數 45.6 → 63.1 → 72.5 → **75.3**，正確題數 20 → 30 → 33 → 36。
- spec 第 8 節的最終門檻只有 ask 達標。其餘的差距主要來自使用者先擱置的待決事項，詳見下方。

| 類別 | p0 | p1 | p2 | p3 | 最終門檻 |
|---|---|---|---|---|---|
| 該追問（ask） | 3/15 | 2/15 | 7/15 | **10/15** | ≥ 9（達標） |
| 太模糊（vague） | 1/14 | 9/14 | 9/14 | 9/14 | ≥ 10（差 1） |
| 該做（do） | 8/14 | 11/14 | 10/14 | 11/14 | ≥ 12，誤拒 ≤ 1（差 1；誤拒 1） |
| 不該做（dont） | 8/13 | 8/13 | 7/13 | 6/13 | ≥ 11，誤承諾 ≤ 1（誤承諾 3、部分承諾 1） |
| 四態成本分數 | 45.6 | 63.1 | 72.5 | **75.3** | ≥ 80 |
| 判定與回覆路徑不一致 | — | 8 | 4 | **0** | 0（達標） |

每題只跑一次；同一題在兩輪之間可能變化，主因是能力檢查模型的解碼失敗與讀取差異。

## 第 3 階段做了什麼（`89d471d`，修正 `9cd49e94`）

- `respond` 的第一步是 `core_views.core_view`。CLARIFY、ASK、DECLINE、UNCHECKED 各自只有一個入口，依判定渲染；DO 保留既有的 renderer。
- 兩個正則 boundary（COBRA → PANDA 表現量、Graphical Lasso + 貝氏最佳化）改成 `decide_core` 判 DECLINE 的證據，不再自己回覆。
- 能力檢查無法確認的說明性回合判為 UNCHECKED。
- Plan Evaluator 與 executor 共用的 `run_approval_failures` 另外要求 `core.run_allowed`。
- 每個回覆的 `core.view` 事件記錄 `mismatch`，由程式量測收斂。
- 盤點：分類階段約 25 個判定改寫點列在 `INVENTORY-P3.md`。

## 門檻（PHASE3.md，實測前凍結）

| 門檻 | 結果 |
|---|---|
| G1 判定與回覆路徑不一致 = 0 | p3 為 0，通過 |
| G2 非 DO 回覆加 10 個 DO 回覆，0 矛盾 | p3：C42、C43 不通過 → 修正 → p3b 的 5 題全部通過 |
| G3 每類最多比 p2 少 1 題 | do 11、dont 6、ask 10、vague 9，通過 |

p3 的 G2 失敗與修正：C42、C43 是因檢查無法確認而暫停的 run，標頭寫「✓ Workflow — DRAGON」，內文有一行沒有標示的「available from DRAGON」（來自備援讀取）。修正方式：

- 判為 UNCHECKED 時，進度行不列 workflow。
- 備援讀取讀到可做時，寫成「the backup check matched X to this (not confirmed)」。

## 沒有達到最終門檻的原因

| 缺口 | 題目 | 屬於哪一項 |
|---|---|---|
| 不該做卻承諾 | C18（用表現量直接跑 CONDOR）、C30（SAMBAR kmax 大於樣本數）、C57（COBRA 基因數少於樣本數）、C08 部分承諾 | 待決事項 3（dont 誤承諾），合約限制沒套用在讀取上 |
| 不該做卻追問或要求釐清 | C14（使用者自己的問題被當成不確定）、C27（讀成目標不明） | fact agent 與 goal 讀取的誤判 |
| 能力檢查解碼失敗 | C42、C43 在 p3 成為 UNCHECKED（p3b 讀取成功後都問對） | 待決事項 2（nemotron 截斷） |
| 追問的結果說明錯誤 | 例如 C06「If no: PUMA does it instead」 | 待決事項 1（ASK 結果未驗證） |
| 模糊請求被判做不到或直接做 | C24、C49（DECLINE）、C53（DO） | goal 讀取把「a network analysis」等讀成具名結果 |

## 待使用者決定

1. 第 3 階段沒有把約 25 個改寫點逐一改寫，而是在回覆與執行兩個出口強制執行判定（spec 變更紀錄，`INVENTORY-P3.md`）。要接受，還是另開工作照字面改？
2. 先前擱置的 3 個待決事項：ASK 結果驗證、nemotron 解碼失敗、dont 誤承諾。
3. `core-decision-phase0` 分支要不要推送到 `netzoo-agent` 遠端，並合併回主樹的 `evidence-contract-grounding`。

## 費用

- p3 56 個 session（US$0.109，nemotron 50/56），p3b 5 個（約 US$0.01）。
- 全套測試：3,826 個通過。

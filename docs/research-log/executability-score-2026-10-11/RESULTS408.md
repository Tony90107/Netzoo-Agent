# Log 408 結果：可執行性判別評分（2026-10-11）

事前凍結：`FREEZE408.md`（`f24acb3`）。受測：上線版 `ec97bd6`。回合 `x15`：heldout15 50 題 × 2 次 = 100 個 session；全部重放相同、provider 錯誤 0、98/100 由 nemotron 完成檢查（有效性條件成立）。標註：4 個盲標子代理（每 packet 一個）＋我複核 20 個指定 session，另為一致性多看 1 個（`live/x15-labels-checked.json`）。

## 總分

| 指標 | 結果 |
|---|---|
| **誤承諾率 FAR**（不能做 → 說能做，含 PARTLY） | **3/64 = 4.7%**（95% CI 1.6–12.9%） |
| 新題型 FAR（NV＋MX6 第二項） | 0/14 |
| 「可做」判定精確度 | 44/47 = 93.6% |
| **誤拒絕率 FRR**（能做 → 說不能做） | **2/48 = 4.2%**（95% CI 1.2–14.0%） |
| 負例明確拒絕 | 61/64 = 95.3% |
| 正例明確承諾 | 44/48 = 91.7%（另 2 個 UNCONFIRMED） |
| 標註矛盾 session | 9/100 |
| **加權分數** | **94.7 / 100** |
| **等級** | **B**（FAR ≤ 6% 且 FRR ≤ 10%；FAR 超過 A 的 3%） |

程式層輔助：檢查判定與金標準一致 負例 60/64、正例 44/48；正例中 routing 提供了正確 workflow 的只有 37/48（77%）。

## 抽查更正（2 處，都對系統不利）

- S071（KN1-2）：OMITTED → GIVEN。回覆與卡片和 S006（KN1-1，標 GIVEN）逐字相同，統一標註。
- S037（NM6-2）：UNCONFIRMED → GIVEN＋矛盾。回覆唯一關於能力的陳述是 "available from DRAGON or LIONESS-DRAGON"，正文只說驗證失敗、請重試，沒說做不到；與 S022/S029 同型的讀法一致。這是判斷題。
- 敏感度：只用盲標原始標籤，FAR = 1/64 = 1.6%，等級 A；只做 S071 一致性更正，FAR = 2/64 = 3.1%，等級 B。

## 誤判明細與成因

| session | 方向 | 成因 |
|---|---|---|
| KN1 ×2（第二輪：spot 是空間位置、鄰近 spot 要共享資訊） | 誤承諾 | 檢查把追問句讀成 context（不是需求），重讀也沒讀出結果；routing 卻把它 exact 配到 **SAMBAR**（"cohort-level sample distance matrix … SAMBAR fits"）。檢查沒有結果時不否決 routing（Log 404 part 1 已撤回），所以完全不相干的 workflow 被說成符合。 |
| NM6-2（lncRNA ceRNA） | 誤承諾 | 檢查模型自己把 ceRNA 認給 DRAGON，第二意見對 DRAGON 與 LIONESS-DRAGON 都答 "all"；同題 NM6-1 正確拒絕。routing 同時驗證失敗。屬已知殘留「檢查過度認可」。 |
| PL6 ×2（蛋白–轉錄體偏相關網路，只留 adjusted p < 0.05 的邊） | 誤拒絕 | 檢查空白判定 → 第二意見（layers≥2 → DRAGON）答 "part"（過濾是使用者的一步）。Log 407 起 "part" 不認可，於是整題 full gap。`dragon.edge_pvalues` 明明存在：這是 Log 407 規則在新題上的第一個代價。 |

## 判別以外的問題（不計入分數）

- 9 個 session 的理解段落與正文選的 workflow 不同：每樣本 TF 目標強度（PS1、PS3）理解為 LIONESS-PANDA、正文選 GIRAFFE；每樣本雙層網路（MX2）理解為 LIONESS-DRAGON、正文退回 DRAGON；MX6 理解為 PANDA、正文選 GIRAFFE。可執行性判斷對，但使用者看到兩個不同的方法。
- 正例中 11/48 沒提供正確 workflow（上列加 KP1 的 LIONESS-PANDA/PUMA 平手）。

## 與舊量測的關係

題組不同，不能直接相減。參考：Log 385 基線（2026-10-08）45 個不支援請求只有 9 個誠實回答；Log 406 cand（heldout14，較多問句與追問）負例明確拒絕 17/26、誤承諾 4/26。本輪負例明確拒絕 61/64。多數 NM／NF 題型在舊題組出現過（措辭不同），新題型 14 個判斷全部正確，但樣本小（CI 上限 21.5%）。

## 建議的下一步（依影響排序）

1. **追問句的限制沒被當需求讀**（KN1）：誤承諾裡最嚴重的一類——完全不相干的 workflow 被說成符合。
2. **第二意見 "part" 一律不認可造成誤拒絕**（PL6）：需要區分「結果本身部分不符」與「結果符合、只差使用者自己做的過濾步驟」。
3. 理解段落與正文選擇不一致（9/100）。

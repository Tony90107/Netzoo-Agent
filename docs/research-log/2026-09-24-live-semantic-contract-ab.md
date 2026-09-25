# 2026-09-24 Live Semantic Contract A/B

## 範圍

- 模型：`openai/gpt-4o-mini`，temperature `0.0`
- 合約：claims 與 legacy；兩組皆使用 `review_policy=when_needed`
- 案例：5 個指定 routing family，各跑 1 次
- 實際 provider 呼叫：claims 12 次、legacy 14 次，合計 26 次（低於核定的 40 次上限）
- 評估範圍：semantic routing、guidance 與 next step；沒有執行 planner、workflow 或生物資訊分析
- 兩組使用相同 corpus SHA-256 `96e6d1a31c184cfb04621dc0f7d3887adcb8840a3657c617af66677d6874d6ec` 與 policy SHA-256 `a52d8476a7eca616b7ab908cfed71c01885c40cf7501cc266d1bc165c96a46ba`

## 結果

| 案例 | Claims | Legacy | 判讀 |
|---|---|---|---|
| `gran-tf-ss-individual-en` | exact → `run_lioness_panda` | exact → `run_lioness_panda` | 一致、正確識別逐樣本 TF 網路 |
| `role-mirna-ss-en` | exact → `run_lioness_puma` | exact → `run_lioness_puma` | 一致、正確識別逐病患 miRNA 網路 |
| `zh-compare-patients-ss` | exact → `run_lioness_puma` | exact → `run_lioness_puma` | 一致、中文逐病患路由正確 |
| `gran-mirna-unstated-control` | ambiguous；列出 PUMA 與 LIONESS-PUMA，詢問 aggregate 或 sample-specific | 同樣 ambiguous 並詢問 granularity | 兩者都沒有替使用者選定 workflow，也沒有執行 |
| `role-tf-agg-control-en` | ambiguous；列出 PANDA、OTTER、GIRAFFE，詢問建模假設 | 同樣 ambiguous 並詢問建模假設 | 兩者都保留 aggregate TF 網路目標，安全地要求補充方法偏好 |

兩組皆為 **5/5 通過**，route 與 semantic pass rate 都是 100%，沒有互動錯誤、fallback、錯誤推薦或 execution。Claims 使用 12 次呼叫；legacy 使用 14 次，claims 少 2 次。這是五個 prompt、每個僅一次的定向比較，不代表完整語料或重複測試的穩定度。

Claims 有 2 次 semantic-completeness review，兩次 patch 都通過驗證。Legacy 有 2 次 review（包含 1 次 contract repair），另記錄 1 次 evidence-validation 問題與 1 次 granularity downgrade；該 downgrade 發生在使用者明確尚未決定 aggregate/sample-specific 的案例，最後回到 `unknown` 並提出澄清。Legacy 的 discriminator 在兩個 ambiguous 案例分別記錄為 `failed` 與 `rejected`，但路由仍安全地停在 clarification。

## 仍需處理的精確問題

`gran-mirna-unstated-control` 的 claims trace 中，最終 `requested_outcome.granularity` 是 `sample_specific`，但同一筆決策的 route status 是 `ambiguous`，而互動又詢問使用者要 aggregate 還是 sample-specific。其 `outcome_hypotheses` 保留了 `unknown` 與 `sample_specific`，沒有明確的 aggregate 假設。Legacy 在同一案例最後保留 `granularity=unknown`。

這次沒有發生錯誤 workflow 推薦或執行，使用者仍會被要求澄清；但評分器將 claims 判為通過，沒有檢查「尚未決定」是否被保留在最終 `requested_outcome`。因此目前應把它視為**語意狀態不一致與評分缺口**，而非已觀察到的執行安全事故。下一個修正應讓尚未回答澄清的結果保持 `granularity=unknown`，並讓評分器拒絕把未決意圖記為已選定 granularity。

## Trace

- Claims：[`live-semantic-trace-2026-09-24-next-step-claims.json`](live-semantic-trace-2026-09-24-next-step-claims.json)
- Legacy：[`live-semantic-trace-2026-09-24-next-step-legacy.json`](live-semantic-trace-2026-09-24-next-step-legacy.json)

Trace metadata 標示 credentials 未記錄；provider calls 保留結構化輸入、解析結果與 routing events，system prompt 僅存 hash。

# Attempt 06：ROUND-10 之後重跑（2026-10-20，Claude）

同一份凍結題目，程式 `0f4b8dfd`（ROUND-10 `e62613f1`）。能力核對用 gpt-4o-mini。6 個 session、6 個回合（T03 第一回合 exit 2，第二回合沒跑），費用 US$0.0248。沒有執行分析。

| 題 | 預期 | attempt-05 | attempt-06 |
|---|---|---|---|
| T01 9 或 17 人 | DO | DO | DO ✓ |
| T02 1 或 2 個樣本 | DECLINE | DO | **DECLINE** ✓（「with 1 / with 2: LIONESS-PANDA needs at least 3 samples」） |
| T03 第一回合 2 或 14 | ASK | ASK | **DO（run）** ✗，在檔案預檢停下 |
| T04 蛋白 180 或 1,800 | ASK | ASK | ASK ✓ |
| T05 因果 DAG | DECLINE | DECLINE | DECLINE ✓ |
| T06 目標不明 | CLARIFY | CLARIFY | CLARIFY ✓ |

6 個第一回合中 5 個符合。T02 第一次在 live 判對。

## T03 為什麼錯（已離線確認）

- 這次模型把同一句請求拆成兩個「結果」，原文互相包含（「one TF-to-gene network per biological sample from pine_bulk.tsv…」與「one TF-to-gene network per biological sample」）。程式把它們當成兩個結果。
- ROUND-09／10 的規則只在「單一結果」時，套用沒有範圍的樣本數候選，所以「2 或 14」沒有套到任何結果。
- ROUND-10 把「2 或 14」記成候選事實後，`sample_coverage` 的保護網把它當成「已解釋」，也沒有出聲。這是 ROUND-10 造成的漏洞。
- fact agent 的「至少 3 個嗎？」被標成交給檔案檢查（R5），所以直接規劃 run。檔案預檢會數樣本，2 個會被擋，不會誤跑。但這不是預期的追問。
- 把兩個重疊的結果視為一個重建，結果變成等待「2 或 14」，候選結論由程式算出（2 → 無，14 → LIONESS-PANDA）。

## 待修（未做）

1. 計算「有幾個結果」時，原文重疊的結果算同一個。
2. `sample_coverage` 不能把只來自背景候選、但沒有被套用的事實當成「已解釋」。

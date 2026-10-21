# ROUND-18 結果：點名的 workflow 沒拿到結果時，也說出真正原因

2026-10-21。起點 `c6b58f5b`，程式提交 `31d5b700`。離線 $0；live 3 個 session，gpt-4o-mini，**US$0.012**，沒有執行任何分析。

## 問題（ROUND-17 live 驗證）

H40、C08 都點名了 GIRAFFE，但讀題沒有把結果歸給任何 workflow，還把使用者的優化器設定標成 OTTER 的設定（eta、iterations、lam）。結果判斷雖然是「不能做」，回覆卻只說「not matched to any registered workflow」，沒有說出真正的原因：GIRAFFE 不接受任何設定。

## 做法

`method_conditions.named_limits`：一列結果點名了已登錄的 workflow、卻沒有任何結果歸給它時，由程式拿這個 workflow 自己的規格書，核對使用者寫的設定、樣本數和資料量。

- 標到別的 workflow 的設定，對點名的 workflow 來說就是「沒有這個設定」。
- 核對出的原因寫進這一列；這一列也會擋下點名的 workflow，也就是讓 ROUND-17 的規則生效。
- 不會把結果歸給它。如果規格書沒有擋，就什麼都不加。

## 離線重放（`compare.py`，對照 `c6b58f5b`）

| | 修改前 | 修改後 |
|---|---|---|
| 判對（757 份有金標） | 595 | 595 |
| 判斷改變 | — | **0 份** |
| 只有說明的原因改變 | — | 5 份，全部改成真正的原因 |

| 讀取 | 修改前 | 修改後 |
|---|---|---|
| ROUND-17 live 的 C08、H40 | 沒有原因（not matched） | GIRAFFE 只用預設值，learning rate、iterations 無法套用 |
| p4b、p5 的 C14 | 沒有原因 | OTTER 沒有「L1 (lasso) sparsity penalty」這個設定 |
| h3 L44 | 沒有原因 | COBRA 需要基因數多於樣本數（150 個基因、400 個樣本） |

完整測試：`tests/` 4,899 項通過（新增 2 項），51 項略過。

## Live 驗證（`live-check/analysis.txt`）

| 題目 | 判斷 | 回覆說明的原因 | 和 ROUND-17 live 比 |
|---|---|---|---|
| C08 | 不能做 | **正確**：「NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "a learning rate of 1e-4" cannot be applied …」 | 原本沒有原因 → 正確 |
| H40 | 不能做 | **大致正確**：讀題這次切成三列。第 1、3 列說出 GIRAFFE 不接受設定；第 2 列是被切斷的片段「I'd like GIRAFFE run on 75 AML samples with a」，仍說 not matched | 原本沒有原因 → 2/3 列正確 |
| H18（對照組） | 不能做 | 仍不準確：說成「lambda1 和 lambda2 要一起給」 | 不變；原因不同，不在這次修改的範圍 |

## 還沒處理的

1. **H40 的片段列。** 這一列點名了 GIRAFFE、卻沒有設定可以核對。可以改成：同一則請求中，若有其他列已經擋下 GIRAFFE，這一列就沿用那個原因。
2. **H18。** 讀題把「a lambda_inter of 0.2」標成了 `DRAGON.lambda2`。程式依「lambda1、lambda2 要一起給」判斷，結論正確，但真正的原因（DRAGON 沒有 lambda_inter）沒有說出來。這是設定被標錯欄位的讀題問題。

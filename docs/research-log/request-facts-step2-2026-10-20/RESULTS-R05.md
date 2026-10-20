# ROUND-05：shape 3（設定說明只送一次）——gpt-4o-mini 除錯重讀（2026-10-20）

計畫：`collab/ROUND-05-PLAN.md`。程式：`185a5294`（`NETZOO_CHECK_SCHEMA=3`，預設仍是 1）。題目：ROUND-04 的 `items.json`（凍結於 `e83db9c3`，沒改）。  
費用：**US$0.125**（A′ 26 次、C 26 次，全部成功）；上限 US$0.32。兩輪合計 US$0.237。

## 結論

**判準沒有全過，不建議預設啟用。** 輸入確實降了 19%；數量召回與誤套用和 shape 1 相同。但設定召回少 1，判定差異也超出同一 schema 兩次讀取的變異範圍（9 題對 6 題）。看差異的內容，比較像讀取變異，而不是 shape 3 造成的；不過每組只讀一次，無法區分。

## 判準（25 題；U12 在 ROUND-04 的 A 組失敗，三組比較時排除）

| | A（shape 1，ROUND-04） | A′（shape 1，今天重讀） | C（shape 3） | 判準 |
|---|---|---|---|---|
| 輸入 token | 369,975 | 369,975 | 300,479（−18.8%） | G1 ≥15%：**過** |
| 輸出 token | 13,366 | 13,224 | 14,741（+11%） | — |
| 數量召回 | 36/40 | 36/40 | 36/40 | G2：過 |
| 設定召回 | 17/27 | 18/27 | 16/27 | G2 ≥ 17：**差 1，沒過** |
| 誤套用 | 1 | 1 | 1 | G3：過 |
| 結果狀態不同的題數 | A↔A′：6 | — | A′↔C：9；A↔C：8 | G4 ≤ 6：**沒過** |
| 費用（25 題） | US$0.0635 | US$0.0634 | US$0.0539 | |

A 和 A′ 的輸入 token 完全相同（同一 schema、同一提示），所以輸入差異全部來自 schema。

## 判定差異（A′ → C，對照金標）

| 題 | 金標 | A′ | C | 與設定有關？ |
|---|---|---|---|---|
| M38 | ask | available | **needs_fact** | 否（候選樣本數），C 對 |
| H18 | dont | DRAGON available | **兩列都 not_available** | 是（lambda_inter），C 對 |
| C45 | ask | LIONESS-DRAGON available | not_available | 否：C 把每個樣本的網路記給 DRAGON，被 scale 規則移除，C 錯 |
| J11 | do | available | not_available | 否：C 沒讀到任何結果，C 錯 |
| M39、L10、M34、L13、P24 | | | | 結果列的切法不同，結論大致相同 |

依金標，C 對了 2 題、錯了 2 題。錯的兩題都和設定無關。

## 不能宣稱的地方

- 26 題都看過、每組讀 1 次；判準是事先寫好的除錯門檻，不是驗收。
- 只測 gpt-4o-mini。production 的能力核對是 nemotron，它對 schema 長度的反應可能不同。
- 每次呼叫省下約 7k 輸入 token。mini 上大約 US$0.0004；nemotron 是免費額度，省下的是時間與 turn 預算。

## 檔案

`live/arm1b.json`、`live/arm3.json`、`live/arm1b.log`、`live/arm3.log`。計分程式：`reread.py`（ROUND-05 加上 enum 超限時改用 compact schema）。

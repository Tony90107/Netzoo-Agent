# ROUND-27 第 0 階段結果（2026-10-25，$0）

依 [ROUND.md](ROUND.md) 執行。沒有改任何程式，也沒有呼叫 API。

## 1. h10：已封存

- **出題、覆核、欄位標註各由一個新的 subagent 完成。** 它們只回報數量。
- **我沒有讀** `items.json`、`items-author.json`、`GOLD-REVIEW.md`、`fields.json`。sha256 記在 [h10/SEALED.json](h10/SEALED.json)。
- **題組：** 48 題，Y01–Y48，全部是英文，證據引文都能逐字找到。
- **分組：**

| 組 | 內容 | 題數 |
|---|---|---|
| S | 用研究目的描述設定 | 10 |
| D | 衍生的輸入 | 10 |
| U | 不確定輸入是什麼或從哪裡來 | 8 |
| T | 陷阱與對照 | 8 |
| G | 一般 | 12 |

- **期望判斷：** DO 20、DECLINE 11、ASK 10、CLARIFY 4、PARTIAL 3。
- **覆核：** 金標改了 0 題，題目文字改了 1 題（Y32）。
- **和 brief 不同：** PUMA 只出現在 1 題，brief 要求每個 workflow 至少 2 題。
- **欄位金標：**
  - 結果 49、設定 20、has 115、lacks 7、source 16；
  - has 之中，共表現矩陣 8、調控網路 3、`unsure` 11。
- **一個尚未解決的問題：** dev 標註者把 `certainty` 標得太寬（見第 2 節），h10 的欄位標註者用的是同一份定義，很可能也一樣寬。
  - 我不能打開 h10 自己裁定。
  - **事先宣告：** 最後驗證之前，由一個新的封存 subagent 用 `adjudicate.py` 的同一條規則裁定 h10 的 `certainty`，它只回報數量。

## 2. C1 的開發金標

細節見 [CONTENT-SPOT-CHECK.md](CONTENT-SPOT-CHECK.md)。

- 687 個 `has` 單位都已標註。抽查 69 個：`content`、`made_by` 69/69 可接受，`certainty` 65/69。
- **`certainty` 有整批的標法問題：** 標註者把所有對資料的不確定都標成 `unsure`。我依 brief 自己的定義重新裁定 53 個 unsure，剩 14 個屬於 C1（不同的可能對應到不同的內容或來源）。
- **衍生資料很少：** 共表現矩陣 8 個、調控網路 10 個。所以 C-G1 要另外報告衍生資料子集。

## 3. 影響判斷的案例

細節見 [CENSUS.md](CENSUS.md)。

| 方向 | 目標 |
|---|---|
| C1，離線 | 10 筆讀取：M46、C18 ×3、C27、C20 ×2、S07 ×2、S08 |
| C1，live 小量 | R31、R12、R25、Q46、Q15 |
| B1 | 約 16 筆：kmin/kmax、output_format、sparsify、log_transformed 的宣告與不確定等 |
| B2 | 漏 credit 與誤記功共約 15 筆 |

- COBRA 交給 LIONESS-PANDA 這個錯誤，在 h4、h5、h6、h7 四組題目裡都出現。
- 「修好」的定義已經在 C1 動工前寫定：
  - 金標是 DECLINE 的題目，只要判斷不再是 DO 就算修好；
  - 從 FA 變成確認提問所增加的「多問」，另外列出代價。

## 4. 下一步

**C1。** 先在 `docs/research-log/round27-c1-2026-10-xx/ROUND.md` 宣告：
- 資料項目讀取的小呼叫，以及程式要怎麼用它的結果；
- 門檻 C-G1 到 C-G5；
- 離線量測方法。

宣告完之後才寫程式。

# Harness repair P2b：live 驗證後的三項修正（2026-10-23）

起因是 [live-check/LIVE.md](live-check/LIVE.md) 發現了三個 replay 看不到的問題，使用者核准修正 (a)(b)(c)。這次只改模型讀取之後的程式判定，沒有呼叫模型，費用 **$0**。

## 改了什麼

### (a) 點名的 run 搭配不支援的設定，整列也判 DO + partial（`method_conditions.settings_apart`、`capability_check.apply_second_opinion`、`same_run`）

使用者的原文點名了 workflow，該 workflow 仍可用自己的設定執行，而設定不被接受時，就把設定拆成獨立的列，不論它是否和 run 寫在同一個子句。run 列寫成「available from W, run with its own settings (the settings asked for are below)」，run 照樣暫停。第二意見也走同一條規則，因為 L21 live 的 GIRAFFE 是第二意見才記進來的。

以下情況不拆，維持整列：

- 契約禁止的數值（C13 的 lam=1.5）。
- 對不到允許值的模糊字（precision 設成「half」）：照舊追問。
- 程式說不出理由的「設定」（C58：「use cobra_out/adjusted_coexpression.tsv」其實是 PANDA 接受的輸入檔，拆出去會被錯誤地宣告為不可做）。判斷方式沿用 ROUND-20 規則 A 的 `_settable`。
- 只要有一項不支援的設定說不出理由，就全部不拆（L21 live 那項沒有數值的「heavier weight on the PPI term」）。這樣 run 那一列會保留原本附有核實理由的回覆，不會變成「我對不到」。

另外，被放行的 workflow 底下若有問句列，問句列照樣擋下（H18 的「Can you set it up that way?」問的就是這個設定能不能用）。

### (b) 設定綁定要核實（`interpretation/setting_words.py`、`stated_reasons._verifiable`）

讀題把某段話讀成控制項 X，但那段話自己寫了另一個參數名（含底線或「字母加數字」，例如 lambda_inter），而且那個名字既不是 X、也不是 X 的允許值時，凡是以 X 為前提的理由都不說。

- H18 live 的「lambda1 and lambda2 must be supplied together」因此不再說出。
- C17 的「transcript layer's shrinkage is fixed at 0.3」原文沒有參數名，綁到 lambda1 照舊，那條說對的成對規則也保留。

設定字詞的判斷移到新的 `setting_words.py`，避免 `method_conditions` 和 `stated_reasons` 之間產生循環依賴。

### (c) 檔案檢查題不涵蓋舊問題（`obligations.file_check`）

agent 的問題若引用 workflow 的 `input_checks` 文字，就不能和舊的維度待問條件互相涵蓋。count 題照舊可以涵蓋 agent 題（phase 5b 的規則）。第一版連這條也擋掉了，造成 C43、H29、J48 等多問一題重複的樣本數問題，已經收窄。

### 一併修正

`run_hold` 的「no registered workflow covers "…"」是 P2 盤點時漏掉的未核實能力陳述。現在有核實限制的寫「cannot be given as asked (above)」，沒有的寫「I couldn't match … to any registered workflow」。

## 重標的金標（`gold-p2.json`，依決定 (a)）

| 題目 | 舊 → 新 | 理由 |
|---|---|---|
| H18（h1） | DECLINE → DO | 「With DRAGON, I'd like … a lambda_inter of 0.2」點名 DRAGON；DRAGON 可自行估計 lambda。lambda_inter 被拒，問句列一起擋下，run 暫停 |
| J41（h2） | DECLINE → DO | 「BONOBO should write … as a .parquet file」點名 BONOBO；BONOBO 用自己的輸出格式執行，parquet 被拒，run 暫停 |

## 驗收

| 項目 | 結果 |
|---|---|
| 完整測試 | **4,940 passed，51 skipped**，0 failed |
| replay（新金標），P2 → P2b | **0 BREAK**；判對 612 → **614**（H18、J41）；FR 7 → **5**；FA 15、MA 64、多問 11、UNCHECKED 30 都不變。無金標的改變：J44 hyb、J41 hyb、K09，都變成 DO + partial |
| 理由 | 與 P2 相同：說錯 2、誤導 5、說對 104、第二層 67、沒附理由 0。兩則改變的回覆（H18、J41）只是同一句理由移到被拆出的設定列，維持「說對」 |
| Fixtures | 改變的仍是 F03–F05、F07、F08 |
| 每個回合問的題目 | 4 個回合多問了一個舊問題：C56 p3 補問 somatic；L14 補問「是否同一批樣本」（檔案 ID 相同不能證明生物樣本相同，spec 第 3 節）；C44 p5r 補問 scale；M03 smoke 多了一題重複的樣本數問題（代價） |

18 份 live 錄製用 P2b 重放：

- **(b)**：H18 不再說錯誤的成對規則。
- **(c)**：C56 補問 somatic。
- **(a)** 對 L21、J44、H40 這三題 live 都沒有作用，原因都在讀題層：
  - L21 有一項無法核實的設定，所以整列不拆；
  - J44 的 GPU 被貼在沒有點名 OTTER 的輸出句上；
  - H40 讀題沒有把結果算給任何 workflow（named_limits 路徑）。

  三題的回覆內容都屬實：設定附上理由拒絕，並說 workflow 可用自己的設定執行。只有判定種類仍是 DECLINE。

## 測試

完整 `tests/`：4,940 passed，51 skipped（與 P2 相同的 Docker 與遠端 action 略過），0 failed。新增或改寫的測試：

- (a)：F6、N11、GPU、MX05、unmapped、request-method、same_run 的問句列與資料量上限；
- (c)：`test_obligation_lifecycle`；
- 共用的設定字詞判斷：`test_stated_reasons`。

## 仍然不支援的地方

- **(a) 的觸發取決於讀題。** run 和設定要讀在同一列、算給點名的 workflow，而且每項不支援的設定都說得出理由。live 的三種失敗型態（設定無法核實、引號貼錯句、沒有算給任何 workflow）都在讀題層。
- **(b) 只核對「原文寫了別的參數名」這一種錯綁。** 用一般描述的錯綁（例如把「the cross-layer weight」讀成 lambda2）程式分不出來。
- **(c) 之後偶爾會多問一題語意重複的問題**（M03）。

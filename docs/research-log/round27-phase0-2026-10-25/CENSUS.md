# ROUND-27 第 0 階段：影響判斷的 B、C 案例普查（2026-10-25，$0）

## 來源

- **replay：** `harness-repair-2026-10-23/attribution/`，共 143 筆錯誤讀取。這批是 E′（`5d4a19e3`）的錯誤，各自帶有分類者的子類與理由。
  - 凍結版 `041f0ee9` 比 E′ 多了 Fix B 與 A3，有些項目在凍結版可能已經是對的。
  - 量測時用 `041f0ee9` 重跑。目標若在基準就已經對了，從清單移除並列出，不算修好。
- **h7 live：** 同一份歸因，第 1、2 輪。
- **h5、h6 live：** `heldout-h6-2026-10-22/RESULTS.md` 的逐項錯誤，以及 `field-gold-2026-10-22/RESULTS.md` 的 h5 診斷。
- **怎麼挑：** 只挑子類是 R-link、R-cond、R-type、R-unc 的錯誤，再逐筆判斷它屬於 B1、B2、C1，或都不屬於。這一步只讀分類者寫的理由與舊的結果檔，沒有讀 h10。

## C1：使用者資料的種類與來源

| 題 | 金標 | 現在 | 錯誤 | 為什麼屬 C1 |
|---|---|---|---|---|
| M46（replay） | DECLINE | DO | FA | COBRA 的 adjusted_coexpression.tsv 交給 LIONESS-PANDA；只被當成 context，沒有 refuses_input 限制 |
| C18 ×3（replay） | DECLINE | DO | FA | 只有表達量（明說沒有 motif、PPI），CONDOR 需要網路輸入 |
| C27（replay） | DECLINE | DO | FA | 只有表達量（明說沒有突變資料），SAMBAR 需要體細胞突變。同時是 R-link |
| C20 ×2（replay） | ASK | DO | MA | 不確定 tumour_profiles_v2.tsv 是表達量還是突變資料；PANDA 拒收突變矩陣 |
| S07 ×2（h7） | DECLINE | DO | FA | 和 M46 同一種：COBRA 調整後的共表現矩陣交給 LIONESS-PANDA |
| S08（h7） | DECLINE | DO | FA | 用表達量做 SAMBAR 分型。同時是 R-link |
| R31 ×2（h6） | DECLINE | DO | FA | 和 M46 同一種 |
| R12 ×2（h6） | ASK | DO | MA | 不確定檔案是 TF–基因網路還是基因–基因網路 |
| R25 ×2（h6） | ASK | DO | MA | 不確定共表現矩陣是哪裡產生的 |
| Q46（h5） | DECLINE | DO | FA | 和 M46 同一種 |
| Q15（h5） | DECLINE | — | — | 只有突變矩陣，卻要 TF–基因網路（缺表達量）。h5 run 的判斷要從結果檔核對 |

- **COBRA → LIONESS 交接這一種，在 h4、h5、h6、h7 四組題目裡都出現。** 它是最穩定的 C 類錯誤。
- **不屬於 C1 的鄰近錯誤**（原因是 C1 的詞彙表達不了它們）：
  - C44：聚合矩陣還是逐樣本矩陣；
  - C42：甲基化是 beta 值還是二值化；
  - M36：單細胞還是 bulk；
  - C56、M08：體細胞還是生殖細胞突變（已經有 typed 的 `mutation_origin`）。

## B1：設定連結

| 題 | 金標 | 現在 | 錯誤 | 漏讀或讀錯的設定 |
|---|---|---|---|---|
| C30 ×2、M25（replay） | DECLINE | DO | FA | 分型範圍「2 到 8」沒讀成 kmin/kmax，所以 kmax ≤ 樣本數的規則沒有觸發 |
| C32（replay） | DO | DECLINE | FR | 「edge list」沒對到 `output_format=edge_list`，反而變成未登錄設定的限制 |
| C51（replay） | DO | DECLINE | FR | 輸入檔描述（「header row」）被讀成 OTTER 沒有的設定。屬於精確率問題 |
| C52（replay） | DO | DECLINE | FR | log_transformed、centered 的宣告值留空，卻記成違反 |
| H34（replay） | DECLINE | ASK | 多問 | 「sparsify at confidence 0.05」綁成 sparsify=0.05，應為 sparsify=true 加 confidence=0.05 |
| J17（replay） | DO | ASK | 多問 | norm_patient 的值讀成「keep」，應為 true |
| C50 ×2（replay） | ASK | DO | MA | 不確定有沒有做 log 轉換，沒接到 BONOBO 的 log_transformed |
| S16 ×2（h7） | ASK | DO | MA | 同上 |
| R43 ×2（h6） | DO | DECLINE | FR | sparsify 沒讀到，所以判成「save_pvals requires sparsify」 |
| R04-2（h6） | DECLINE | DO | FA | sparsify 時 delta=0.4 超出上限。rep1 有擋下，屬於讀取變異 |
| Q09、Q42（h5） | — | — | — | sparsify 漏讀，或讀成 keep_in_memory |

## B2：結果連結（B1 通過才做）

| 題 | 錯誤 | 說明 |
|---|---|---|
| C21（replay）、H37（replay）、S09 ×2、S04 ×2（h7） | MA／FR／DECLINE | **漏 credit**：CONDOR communities、GIRAFFE tf_activity 明明有對應，卻沒記到 |
| S05 ×2（h7） | 少了平手的提問 | 只 credit 到 GIRAFFE，漏了 LIONESS-PANDA |
| S28 ×2（h7） | 記錯 | 要逐邊 p 值，應該是 BONOBO，卻記給 LIONESS-COEXPRESSION |
| C47 ×2、J15、C14 ×2（replay） | FA | **誤記功**：記給了不產生該結果的 workflow |
| S25（h7） | 誤記 | 輸出路徑被讀成要求的結果 |
| Q10（h5） | — | signed regulation 漏讀 |

## 目標清單與「修好」的定義（C1 動工前宣告，之後不改）

**C-G2 的單位：**
- replay：M46、C18 ×3、C27、C20 ×2；
- h7：S07 ×2、S08（用錄製的讀取重放）。

h5、h6 的 R31、R12、R25、Q46、Q15 是 live 紀錄。它們在 live 小量檢查時一併跑，不放進離線的 C-G2 計數。

**「修好」怎麼算：**

| 金標 | 算修好的條件 |
|---|---|
| DECLINE | 判斷不再是 DO。改成 ASK（確認）或 DECLINE 都算 |
| ASK | 判斷變成 ASK，而且問的是那份資料的內容或來源 |

**要另外報告的代價：** 依共用原則，單靠新讀到的資訊不能直接拒絕。所以金標是 DECLINE 的題目，C1 最多只能把它從 FA 變成確認提問。四類計分會把它記成「多問」而不是「對」，這個代價要另外列出。

**「改壞」怎麼算：** 原本判斷正確的單位，判斷改變了，就算改壞。

# P1/P2 live check（2026-10-23）

- **範圍**：使用者核准 18 題、每題 1 次，用 gpt-4o-mini，上限 US$0.20。程式為乾淨的 `.worktrees/netzoo-harness-live`，固定在 `4739549b`，執行前後都核對過沒有變動。
- **花費**：provider 回報 **US$0.0767**。18 個 session 全部完成，沒有中途停止。
- **用途**：這 18 題都是看過的題目。這輪只檢查 live 路徑的行為和回覆文字，不是準確率評估。
- **檔案**：題目與 replay 預期在 `items.json`，回覆全文在 `REPLIES.md`，逐題摘要由 `analyze.py` 產生。

## 結果

判定種類正確 **14/18**（用 P2 重標後的金標）。所有回覆都不再出現舊的制式句「not matched to any registered workflow」。

| 題目 | 檢查什麼 | live 判定 | 結果 |
|---|---|---|---|
| L21、J44、H40 | P2 partial | DECLINE | **沒有出現 partial**。live 把 run 和設定讀成同一列，沒有拆成兩列，所以沒有可做的 run 列（下面第 1 點） |
| H18 | 對照組 | DECLINE | 判定對，但**理由錯**：說「lambda1 and lambda2 must be supplied together」；實際原因是 DRAGON 沒有 lambda_inter（下面第 2 點） |
| C08、L13 | 對照組 | DECLINE | 判定和理由都對 |
| C12、C24 | 第二層理由 | CLARIFY | 對：live 的目標判斷（goal_unclear）先問了要哪個結果；replay 做不到這一步 |
| C51 | 曾經說出錯的「no registered workflow produces this」 | DECLINE | 判定仍錯（金標 DO，這是讀題層的錯）。但回覆改成第二層，沒有再說錯的能力陳述 |
| C07 | near miss | DO | 對；這次讀題沒有產生 near miss |
| M20 | 第二層理由不能誤導 | DECLINE | 對；第二層只說查了什麼，並列出接受表現量資料的 workflow |
| J19、J34、M06、C11、L05、C31 | P1 | ASK | 都對，也都問到關鍵事實。L05 是 run 請求，在 live 上正確走了等待路徑 |
| C56 | P1 | ASK | 判定對，但**問錯事實**：問了「Do the mutation rows contain unique sample IDs?」，somatic 的舊問題被綁定到這一題而沒問（下面第 3 點） |

## 發現（replay 看不到的部分）

1. **partial 會不會出現，取決於讀題。** replay 用的錄製讀取把「Please run GIRAFFE」和設定拆成不同的列；live 這次把整句當成同一列，該列不可做，`defaults` 裡有 GIRAFFE。於是同一個請求，replay 是 DO + partial，live 是 DECLINE。兩邊的回覆內容其實相同：設定附上核實的理由，並說 GIRAFFE 仍可用自己的設定執行，run 也都沒有排入。不同的只有判定種類。ROUND-12 的 C13 也是同樣的引號長度問題。
2. **A21 的案例在 live 出現（H18）。** 讀題把「a lambda_inter of 0.2」讀成 DRAGON 的 lambda2，於是程式說出 lambda 成對規則。理由本身是程式從設定推出的，但「lambda_inter 就是 lambda2」這個綁定沒有核實：使用者的原文裡沒有 lambda2 這個控制名。spec 的 A21 要求這種情況改用第二層理由，P2 還沒實作。
3. **C56 的綁定錯誤在 live 出現。** agent 的問題引用 SAMBAR 合約 `input_checks` 裡的檔案檢查句（「Mutation rows are unique sample IDs ...」）。它和 somatic 的舊問題原文重疊、workflow 也相同，所以被當成同一件事，關鍵的 somatic 問題就沒有問。91a8c2d9 同樣不會問（當時整批解除），但 live 證實這會造成實際損失。

## 建議的修正（都只改程式判定，可用 replay 與單元測試驗收）

- **(a) partial 不再依賴讀題怎麼切。** 一列若只因 workflow 不接受的設定而不可做，該 workflow 被點名且在 `defaults` 裡，就判定為 DO + partial：workflow 用自己的設定，設定附理由拒絕，run 暫停。契約禁止的數值（C13 的 lam=1.5）不算，照 ROUND-12 擋下。這改變單列情況的語意，**需要使用者決定**。
- **(b) A21：設定綁定要核實。** 讀題把某段文字讀成控制 X，但使用者原文沒有提到 X 或它的允許值時，以 X 為前提的理由不說，改用第二層。H18 會改成「lambda_inter 對不到 DRAGON 的任何設定」。
- **(c) 檔案檢查題不涵蓋使用者才知道的事實。** agent 的問題若引用的是 workflow 的 `input_checks` 文字，就不能綁定或涵蓋舊的待問條件，那個條件要照常問或排隊。C56 會改成同時問 somatic。

# ROUND-17 結果：做不到就擋下，並說明原因

2026-10-21。起點 `08740c36`。費用 $0，沒有呼叫模型。

## 使用者的決定（2026-10-21）

> 要判不能做。當手頭的工具無法組成一個可行的結果就不該做，寧願擋下來，也不要交出有問題的東西給使用者；但這部分也必須對使用者說明為什麼不行。

依這個決定，h 系列金標的判法成為準則（J44、L21、H40 判不能做），a24b 中相反的判法（MX04、MX05：run 可做、設定不可做）不再採用。

## 結論

| | 修改前 | 修改後 |
|---|---|---|
| 1,045 份已存讀取中，757 份有金標，判對 | 586 | **595**（+9，對→錯 0） |
| 現行讀題形狀中，金標「不能做」卻判「做」 | 13 | 7 |

- **改對的 9 份：**
  - 7 份部分執行目標中的 6 份：J44、H18、H40、L13、L21、p5r C08；
  - 另外是舊回合的 C08（p2、p3、p5）。
- 另有 2 份沒有金標的 m3 舊題（MX18、MX12）跟著改判，符合上面的決定。
- 6 份改判的回覆都是「不能做」，而且逐項說明原因（`replies.txt`）。例如 L21：

  > 1. "Please run GIRAFFE" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so "learning rate 0.0005" cannot be applied. ...
  > No registered workflow can give these as you asked, so none is offered as asked. No files were inspected and no analysis ran.

  能用預設值跑的 workflow，回覆會另外說明「可以用它自己的預設設定跑，但這不是你要的設定」。J44 的 OTTER、H18 的 DRAGON 都是這樣，只當作替代選項提供，不會自動執行。
- **測試：** `tests/` 4,897 項通過（新增 4 項），51 項略過。

## 做法

1. **`CheckedRequirement.blocks`（新的合約欄位）：** 記錄這一列顯示「無法照要求執行」的 workflow。只由程式依規格書判斷的原因填入：
   - `method_fitting` 因設定不能用、樣本數、資料量而移除的 workflow。不含「使用者點名了別的方法」（`instead`）。
   - `settings_apart` 拆出設定時，該設定所屬的 workflow。
2. **`interpretation/same_run.py` 的 `same_run_holds`：** 放在「使用者說沒有的資料」之後執行。
   - 一列「可做」的結果，如果只靠被擋下的 workflow，就跟著擋下，並寫上相同的原因。
   - 若有其他 workflow 能給這個結果，就照常保留。不同的結果各自判斷，例如 PANDA＋DRAGON 的請求，DRAGON 的設定做不到時 PANDA 仍可做。
3. **B2 重放（`replay_full.py`）也加上同一步，** 和 live 保持一致。

## 第一版改錯 4 份，因此收窄

第一版也用了另外兩種原因：「模型判的條件不符」，以及「文字對不到允許的選項」。結果改對 11 份、改錯 4 份：

| 改錯 | 原因 | 處理 |
|---|---|---|
| C40（g4o1、g4o2） | genes_axis 的文字「gene IDs in the first column, sample IDs in the header」對不到允許的選項。這是文字沒說清楚，不是做不到 | 這類原因不擋（共用常數 `UNCLEAR_CHOICE`） |
| C40（p0） | 條件檢查答 violates。這是 nemotron 時期的答案，gpt-4o-mini 讀 4 次都答 satisfies | 模型判的條件不符不擋 |
| C32（p2） | 「complete continuous values with no NAs」，gpt-4o-mini 讀 4 次都答 violates，答錯，而且很一致 | 同上 |

- gpt-4o-mini 對「同一句裡描述資料的條件」常常答錯，而且每次都錯：M47、C58 ×2、C35、C32，4 次讀取都答 violates。如果讓這類答案擋下 run，就會一直誤拒。M2 當初把它們放在獨立的一列，正是為了避免這種情況。
- 代價：H27（CONDOR 直接跑表現量；模型判對了）仍是部分執行，沒有修到。

## 還沒做的

- H27、M25、M46、J15、L48、C14 ×2（gpt-4o）這些「該拒卻做了」，原因各不相同，見 ROUND-12、16。
- 回覆中相同的原因會在每一列重複出現（例如 L21 的三個設定），可讀性還可以再整理。
- 沒有 live 驗證。

# ROUND-14 結果：把套件使用情境寫成結構化欄位

2026-10-21。起點 `e8382238`（分支 `closed-menu-phase0`）。模型呼叫 374 次（gpt-4o-mini），費用 **US$0.034**。

## 結論

使用者的想法是：把各套件的使用情境寫得更清楚，寫成結構化欄位，能讓程式判斷的就交給程式。

1. **欄位已經加上，並保留下來。**
   - 9 個 workflow 在 `capability_sheet.yaml` 新增 `expects`，共 10 條，寫的是「輸入資料應該已經是什麼樣子」。
   - 每條一行，依據該 workflow 自己的規格書，並註明出處；撰寫時沒有看任何測試題。
2. **程式判斷的部分已經上線。**
   - 只有一種情況由程式判斷：使用者的文字用某個設定的名稱，說出和 workflow 預期相反的值。例如對 BONOBO 說「raw counts, not log-transformed」，程式直接判「不符合」，不再問模型。
   - 程式從不判「符合」，因為一句話裡可能還有別的要求。
   - 在 1,045 份已存讀取上重放，沒有任何一份判斷改變；這條規則是防護用的。
3. **把這些文字給模型看的做法：量過之後不採用。**
   - 測試的兩處：
     - 條件檢查：加上「It expects: …」；
     - second opinion：加上「It does not give: …」（各 workflow 已有的 near misses）。
   - 結果模型明顯變得更常拒絕，連無關的句子也會：

| 指標 | 舊文字（A） | 加上欄位（C） |
|---|---|---|
| 130 份有金標的讀取，判對 | 101 | 99 |
| second opinion 的答案往「給更少」方向改 | — | 65 次（all→part 34、part→none 31）；反方向只有 11 次 |
| 條件檢查 satisfies→violates | — | 10 次；反方向 4 次 |

   - 例子：C55 的「all using the same gene symbols」和 PANDA 的「Normalization and batch correction are done before PANDA」毫不相干，模型卻答 violates，把能做的 PANDA 判成不能做。
   - 這和文獻（無關的上下文會干擾小模型）以及這個專案 Logs 229–233 的 prompt 長度效應一致。
4. **意外發現：舊紀錄和重問的結果差很多。**
   - 用完全相同的舊文字重問一次，130 份中有 13 份判斷改變：5 份變對、8 份變錯。
   - **ROUND-15 更正：** 差異主要來自換了模型，不是 gpt-4o-mini 自己不穩。舊紀錄大多是 10/19 以前由 nemotron 回答的；gpt-4o-mini 自己獨立讀兩次，181 份中有 178 份判斷相同。
   - C52 就屬於這一類：用 gpt-4o-mini 重問就答對了，原本的錯不是缺資訊。

## 1. 做了什麼

| 檔案 | 內容 |
|---|---|
| `scripts/capability_sheet.yaml` | 9 個 workflow 加上 `expects`（PANDA、OTTER、GIRAFFE、DRAGON、LIONESS-DRAGON、BONOBO ×2、COBRA、CONDOR、SAMBAR）；檔頭說明寫明「不給模型看，因為量過會讓它更常拒絕」 |
| `scripts/netzoo_agent_core/interpretation/expects.py` | 載入並驗證欄位（id 唯一、要有出處、綁定的設定必須是該 workflow 的 boolean 設定）；`stated_opposite`、`code_answer` |
| `scripts/netzoo_agent_core/graph/capability_check_call.py` | 條件檢查先讓程式判斷，程式判斷不了的才問模型；全部都由程式判斷時不呼叫模型 |
| `tests/test_expects.py` | 3 項測試：欄位驗證；只判相反值（C52 的寫法不判、同時提到多個設定不判、無關的否定不判）；全部由程式判斷時不需要模型 |
| `docs/research-log/false-accept-replay-2026-10-21/replay_full.py` | B2 重放也套用程式判斷的答案，和 live 一致 |
| `reask.py`、`asked.json`、`scored.json`、`score.txt`、`harness-after.json` | 重問實驗與結果 |

兩處給模型看的文字已經撤回，`router_invocation.py` 沒有任何改動。產生文字的函式移到 `reask.py`，實驗仍可重現。

## 2. 重問實驗

- 對象：已存的 185 次呼叫（85 次條件檢查、100 次 second opinion），A、C 兩組各問一次，共 370 次。另外有 4 次先行試跑。
- 兩組的 system prompt、schema 和解析方式，都和 live 完全相同。
- 每組的答案放回 B2 重放（取代紀錄中的答案），再和金標比對。

| 使用的答案 | 有重問的讀取共 181 份（其中 130 份有金標），判對 |
|---|---|
| 紀錄中的答案 | 104 |
| A：舊文字重問 | 101 |
| C：加上欄位重問 | 99 |

A → C 改變的判斷：
- 改錯 3 份：h3 L29（不能做→做）、p1 C55、p3 C55（做→不能做）。
- 改對 1 份：g4o2 C26。
- g4o1、g4o2 的 C37 本來就錯，C 也錯，只是錯成另一種。

## 3. 後續

ROUND-15（`judge-agreement-2026-10-21`）測了文獻建議的「同一個判斷讀兩次，兩次一致才採用」。結果 gpt-4o-mini 讀兩次本來就很穩定，這個規則反而讓結果變差，所以不採用。

# ROUND-12 結果：「該拒卻做了」補齊重放後的件數與原因

2026-10-21。計畫：`collab/ROUND-12-PLAN.md`。起點 `9e83314d`（分支 `closed-menu-phase0`）。模型呼叫 0 次，費用 $0；沒有修改 `scripts/`、`tests/`。

## 結論

- **真正的件數。** 補齊重放（B2）後，mini 金標「不能做」的 39 份中，仍判「做」的只剩 **5 份**。另外 2 份判成「請說清楚」，不在本輪範圍。
  - ROUND-11 的 9 份中，有 4 份（C18 ×3、C27）是重放少了步驟造成的，補上後都正確判「不能做」。
  - 剩下 5 份：p4b C17、p5r C17、p4c C13、p5r C13、p5r C08。這 5 份在當時的紀錄裡也是判錯的。
  - gpt-4o 的 26 份中有 4 份：C17 ×2、C14 ×2。
- **5 份裡，沒有一份是因為模型漏讀了限制。** 限制都有讀到，錯在後面的程式。
  - **C17 ×2：規格書的規則沒寫完整（E）。**
    - 模型讀到了兩個設定：`DRAGON.lambda1` = 0.3；`DRAGON.lambda2` 由資料估計（沒有數值）。
    - 程式的「兩個 lambda 要一起給」規則，只看有沒有提到 lambda2，不看它有沒有數值。所以「一個固定、一個估計」沒被攔下。
    - 修這一條規則，可以同時攔下 mini 2 份和 gpt-4o 2 份。
  - **C13 ×2：限制被程式拆到另一列，主要的 run 仍可做，判成部分執行（B 加 F）。**
    - 模型把 `OTTER.lam = 1.5` 正確掛在「Run OTTER」上。
    - 但 ask 的引文很短（只有「Run OTTER」或「OTTER」），和「lam set to 1.5」之間隔著檔名清單的逗號。`settings_apart`（`method_conditions.py:356`）因此把這個設定拆成自己的一列「不能做」。
    - 結果「Run OTTER」仍然可做，判斷變成「部分執行，run 暫停」。
    - p4b 的引文涵蓋整句，限制留在 run 那一列上，所以正確判「不能做」。同一個請求，判斷取決於模型引文的長短。
  - **C08（p5r）：設定句被當成一項分析，背景又多出一項可做的分析，判成部分執行（B 加 F，另有 E3 片段分類錯誤）。**
    - 「I want a learning rate…」被讀成一項分析，並正確列出 GIRAFFE 不能接受設定。
    - 重讀又把背景中的「TF activity matrix」（「預設值給出的 TF activity matrix 看起來太平滑」）當成一項可做的分析。
    - 結果判成部分執行。p4b 沒有多出這一項，所以正確判「不能做」。
- **條件檢查沒問（C）、條件檢查答錯（D）、重放限制（G）在這 5 份中都是 0 份。** 只有 gpt-4o 的 C14 ×2 是漏讀（A）：它把「L1 sparsity penalty」讀成方法問題，沒有讀成設定。mini 三次都讀到了。
- **B2 是可信的。**
  - 用 p5r 當時凍結的程式（`54d08ce7`）跑 B2，p5r 的 56 份判斷全部和紀錄相同（56/56）；gpt-4o 是 110/111。
  - 用目前的程式跑，mini 有 163/168 和紀錄相同；不同的 5 份都有原因（第 2 節）。
- **另外發現一個反方向的問題：p4c C52，金標「做」，B2 判「不能做」（第 2 節）。**

## 1. 做了什麼

| 檔案 | 內容 |
|---|---|
| `replay_full.py` | B2：照 `_with_capability_check` 的順序，用已存的模型答案重放，並可用 `--scripts` 改用別的 checkout 的程式 |
| `declines.py` | `tables`：B2 與紀錄的比對，以及金標「不能做」的判斷表；`round11`：用 B2 重算 ROUND-11 的各變體 |
| `b2.json`、`b2-at-54d08ce7.json`、`round11-b2.json` | 逐份結果 |
| `tables.txt`、`round11-b2.txt` | 上面兩個指令的輸出 |

重現方式（在本資料夾執行）：

```
python3 replay_full.py b2.json
python3 replay_full.py b2-at-54d08ce7.json --scripts <54d08ce7 的 scripts 資料夾>
python3 declines.py tables b2.json > tables.txt
python3 declines.py round11 round11-b2.json > round11-b2.txt
```

`54d08ce7` 的程式是用 `git archive 54d08ce7` 解壓到暫存資料夾取得的，沒有新增 git worktree。

和計畫不同之處：
- `replay_full.py` 會依函式的參數個數自動調整，好讓舊程式也能跑。舊版的 `build_capability_check` 不收檔案樣本數，`apply_second_opinion` 不收請求原文；`bound_expression_samples` 是 ROUND-07 才加入的。
- 計畫中的原因 B 寫的是「讀到但放錯位置」。C13 被放錯位置的是程式（`settings_apart`），不是模型，所以表中特別標出是誰放錯的；分類本身沒有改。

## 2. B2 與紀錄的比對

| 模型 | 讀取份數 | B2 與紀錄相同 | 紀錄判對 | B2 判對 | 沒錄到答案的配對 |
|---|---|---|---|---|---|
| mini（目前的程式） | 168 | 163 | 135 | 134 | 0 |
| gpt-4o（目前的程式） | 111 | 107 | 86 | 88 | 0 |
| p5r（`54d08ce7`，當時的程式） | 56 | **56** | — | — | 0 |
| gpt-4o（`54d08ce7`） | 111 | 110 | — | — | 0 |

ROUND-11 的 B 有 9 份和紀錄不同。B2 補上「使用者說沒有的資料」與條件檢查後，C18 ×3、C27、C51 都和紀錄相同了。

目前程式跑出的 B2，和紀錄不同的有：

| 題目 | 紀錄 → B2 | 原因 |
|---|---|---|
| C10（p4b、p4c） | UNCHECKED → CLARIFY | 程式較新（phase 5a），對的方向 |
| C31（p4b、p4c） | ASK → UNCHECKED | 程式較新。p5r 的紀錄本身已經是 UNCHECKED，這個改變發生在 p4c 之後 |
| C52（p4c） | DO → DECLINE | 見下 |
| C43（g4o1、g4o2） | DO → ASK | 程式較新（ROUND-09／10 的數量規則），對的方向 |
| C10（g4o2） | DECLINE → CLARIFY | 程式較新，對的方向 |
| C31（g4o2） | ASK → UNCHECKED | 同上面的 C31 |

**p4c C52（金標「做」）：**
- 請求：「Can BONOBO build a co-expression network for each of my 6 rhesus macaque lymph node samples? The data are log2-transformed and centered per gene, …」
- 條件檢查對「The data are log2-transformed and centered per gene」回答 violates。這個答案是錯的：BONOBO 本來就有 `log_transformed`、`centered` 這兩個設定。
- 當時的程式把這句算成「和 ask 同一句的條件」，只多加一列「不能做」，BONOBO 仍可做，判「做」，碰巧對了。
- 目前的程式依 Log 414 的規則，把它算成 ask 句子之外的條件，同一個錯誤答案就會移除 BONOBO，判「不能做」。
- 這是模型答錯（D），但在目前的程式下後果變大了。模型如果再這樣答，就會拒絕一個能做的請求。這不是本輪的範圍，列為另一個問題。

## 3. 金標「不能做」的判斷（B2）

| 模型 | 份數 | 不能做 | 做 | 做（部分執行） | 請說清楚 |
|---|---|---|---|---|---|
| mini | 39 | 32 | 2 | 3 | 2 |
| gpt-4o | 26 | 22 | 4 | 0 | 0 |

### 仍判「做」的每一份

| 題目 | B2 | 最早的那一層 | 其他 | 證據 |
|---|---|---|---|---|
| p4b C17 | 做 | E 規則沒寫完整 | — | 讀取：`DRAGON.lambda1` 值 0.3，`DRAGON.lambda2` 值為空（「estimated from the data」）。`combination_issues` 只在 lambda2 完全沒被提到時才報錯（`workflow_conditions.py:342-344`、`data/dragon.py:18-20`）；直接測試：兩個都提到時回傳 []，只提到 lambda1 時回傳 "lambda1 and lambda2 must be supplied together"。規格書：`workflows/dragon.yaml:24, 64` |
| p5r C17 | 做 | E | — | 同上 |
| p4c C13 | 做（部分），run 暫停 | B（由程式 `settings_apart` 拆開；模型讀對） | F | 讀取：兩個 ask 都是「Run OTTER」，設定 `OTTER.lam` 值 1.5。check：「Run OTTER」可做；「lam set to 1.5」不能做，限制是「OTTER's lam must be between 0 and 1」。run verdict：partial_gap。`settings_apart`：`method_conditions.py:356`（round m3 MX12 的規則） |
| p5r C13 | 做（部分），run 暫停 | B（同上） | F | 同上，另外同一句條件的檢查答 violates，又多加一列（`apply_own_sentence_answers`），兩列都沒有擋下 run |
| p5r C08 | 做（部分） | B（設定句被讀成一項分析） | E3（重讀把背景的「TF activity matrix」讀成分析）、F | check：設定句那一列不能做，限制是 GIRAFFE 不接受設定；「TF activity matrix」可做（由 GIRAFFE）。「Can GIRAFFE be run with my own optimizer settings?」被放在 about_methods，沒有被檢查 |
| g4o1 C14、g4o2 C14 | 做 | A 漏讀 | — | 整句被讀成 methods_question；asks 是空的，settings 是空的，沒有任何列可以檢查，所以由 routing 對到 OTTER。mini 三次都判「不能做」 |
| g4o1 C17、g4o2 C17 | 做 | E | — | 同 mini 的 C17 |

**每一層修了能攔下幾份：**

| 層 | mini | gpt-4o | 說明 |
|---|---|---|---|
| E：lambda 規則改成看數值，不只看有沒有提到 | 2 | 2 | 「estimated／empty」算成沒有給數值。單一規則，影響範圍可以離線重放確認 |
| B 加 F：一個設定若是同一個 run 的設定，它的限制應該擋下那個 run，而不是變成另一列，讓 run 部分執行 | 2（C13） | 0 | 牽涉 `settings_apart` 的 m3 規則。MX12 的金標是分開判，所以要找出兩者的差別：C13 的設定是用「with」修飾 run，MX12 是另外用「and use」加上的要求 |
| B 加 E3 加 F：C08 | 1 | 0 | 要同時處理設定句被讀成分析，以及背景被讀成分析。屬於讀題形狀的問題（D1 那一類），不是單一規則能修的 |
| A：C14 | 0 | 2 | 只有 gpt-4o 會出錯 |

### 另外 2 份判成「請說清楚」（不在本輪範圍）

- **p4b C57：** 結果列已正確寫出「COBRA requires more genes than samples; 48 genes and 600 samples」，但 goal 被讀成不清楚，所以判「請說清楚」。這是 ROUND-11 中 goal 那一類。
- **p4c C08：** 設定句那一列不能做，限制也正確，但 goal 被讀成不清楚。

## 4. ROUND-11 用 B2 重算

| | ROUND-11 的 B | B2 |
|---|---|---|
| mini 判錯（W） | 37 | 34 |
| O-ab：錯→對／對→錯 | 2／1 | 2／1（相同題目） |
| O 全部：錯→對／對→錯 | 4／14 | 4／14（相同題目） |

- 依 ROUND-11 事先定的規則：F = 4 是 W 的 11.8%，不低於 10%；R = 14 遠大於 F/5。判定仍是「待決定」，結論不變。
- gpt-4o：B2 判錯 23 份（B 是 25 份），各變體的改變也和之前相同。

## 5. 限制

- check 之前的 routing 和 run verdict 仍沿用紀錄。279 份中有 13 份有 run 暫停的紀錄。用 B2 的 check 重算 run verdict，只有 g4o1 C52（金標「做」）不同：紀錄是 gap，重算是 agrees。也就是說，目前的程式會讓這個 run 通過，但 B2 仍用紀錄中暫停的 decision。本輪關心的 C13 ×2 重算後和紀錄相同（partial_gap）。
- 原因由我一個人判定，沒有第二位標記者。
- 56 題都已經看過。這裡量的是現有紀錄中的錯誤原因，不代表在新題目上的比例。

## 6. 下一步的選項（由使用者決定）

1. **修 DRAGON 兩個 lambda 的規則（建議先做）：**
   - 「沒有數值」也算沒有給（例如「estimated」，或值為空）；
   - 用 ROUND-12 的 B2 在 279 份讀取上確認影響範圍（$0）；
   - 再加上單元測試。
2. **處理「同一個 run 的設定被拆成另一列」（C13）。** 要先寫清楚 `settings_apart` 什麼時候該拆、什麼時候不該拆（MX12 對 C13），再離線重放，確認 MX12、MX04、MX05 等舊題不會變錯。
3. **C52 的反方向問題：** 條件檢查答錯 violates 會拒絕能做的請求。可以先用 B2 在 192 題新題目上看看類似情況有多常見。

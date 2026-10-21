# ROUND-11 結果：D1 段落分類的離線評估

2026-10-21。計畫：`collab/ROUND-11-PLAN.md`。起點 `4c7f953e`（分支 `closed-menu-phase0`）。模型呼叫 0 次，費用 $0；沒有修改 `scripts/`、`tests/` 或金標檔。

## 結論

- **依事先定的規則，判定是「待決定」。**
  - 用 gpt-4o-mini 三回合計：用目前的程式重判（B），168 份中錯 37 份（W）。
  - 「O 全部」把 4 份錯的改對（F），但把 14 份對的改錯（R）。
  - F = 10.8%·W，沒有低於 10%，所以不是「停」。R 遠大於 F/5，所以也不是「往下」。
- **但 14 份改錯幾乎全部來自 O-c（依金標設定 goal），原因是兩套定義不一致，不是分類有提升空間：**
  - 金標把「run the network analysis」這類泛稱的要求也算成「要做的分析」，閉合選單用結果類型是泛稱來判 vague。
  - 現行合約的 `goal=result_named` 卻表示「指名了具體結果」。
  - 只看片段分類本身（O-a 加 O-b，goal 維持模型讀到的），結果是錯→對 2、對→錯 1，只佔 W 的 5.4%。
  - 只把 goal 的值改成金標對應的值，最多再救回 3 份（C57、C34×2）。goal_quote 對不上（例如 H21 那類）不在這個量測範圍內。
- **我的建議：現行流程這條線不做付費的 D1 分類步驟。**
  - 片段分類錯誤很常見：判錯的 22/37、判對的 57/131 都有。
  - 但在目前的程式下，這些錯誤很少改變判斷，因為之後幾輪修的規則已經吸收了大部分：句子歸屬、重疊片段合併、CLARIFY 優先序。
  - 現行流程剩下的錯，主要是該拒卻做了、goal 讀錯導致 CLARIFY 誤判、以及 routing 失敗（見第 3.3 節）。
  - **ROUND-12 更正**：「該拒卻做了」補齊重放後只剩 5 份，而且限制其實都有讀到。原因是 DRAGON 兩個 lambda 的規則沒寫完整，以及部分執行的判斷規則，見 `false-accept-replay-2026-10-21/RESULTS.md`。
- **Q3 的對照方向相反：closed-menu 的 v7 讀取，分類修正的上限明顯較大。**
  - 112 份從 75 份對變成 83 份對：錯→對 10、對→錯 2。
  - 這是因為 `decide_menu` 直接依每段的 form 判斷。
  - 套用同一個門檻（W 也是 37），F = 27% ≥ 25%，且 R = 2 ≤ F/5，會落在「往下」。
  - 但 v7 的基準本身比現行流程低（67% 對 78%）。只有重新啟用 closed-menu 那條線時，這個結果才有意義。

## 1. 做了什麼

| 檔案 | 內容 |
|---|---|
| `units.py` | 載入金標、比對引文、為片段分類計分（Q1、Q3 的片段部分）。`--self-test`：金標當成讀取，結果 64/64 對、0 個多出、0 句找不到 |
| `oracle.py` | 第 4 節各變體的重建與重判（Q2），以及 v7 的 `decide_menu` 重判（Q3） |
| `report.py` | 從 `units.json`、`oracle.json` 產生本報告的所有表格（輸出存成 `report.txt`） |
| `units.json`、`units-any.json`、`oracle.json` | 逐份結果；`units-any.json` 是「只要重疊就算對上」的敏感度版本 |

重現方式（在本資料夾執行）：

```
python3 units.py --self-test
python3 units.py score units.json
python3 units.py score units-any.json --any
python3 oracle.py oracle.json
python3 report.py units.json oracle.json > report.txt
```

### 和計畫不同之處（全部在看到判斷結果前或因除錯而改，逐項記錄）

1. **金標引文的省略號。** 5 句金標引文用「...」省略中段（C15、C22、C35、C39、C46），原本的定位函式找不到。改成「從第一段的開頭到最後一段的結尾」當作區間。自我測試因此從 59/64 變成 64/64。
2. **E2（重複）的定義。** 第一版會把「第一次讀與重讀都出現的多出片段」兩個都算成 E2，這樣它們就不會被算成真的多出。改為：第一個出現的依內容分成 E1 或 E3，之後的才算 E2。這符合計畫寫的「重複」的意思。
3. **配對時平手的處理（程式錯誤）。** 第一次讀和重讀的引文完全相同時，原本會配到重讀那一份，把第一次讀的那份當成重複。O-b 因此刪掉第一次讀的 ask，而重讀單獨無法產生結果列（例如 C21 從 ASK 變成 CLARIFY）。改為平手時配第一次讀的。另外，O-b 不刪「重讀中對應到金標 D 的片段」，因為重讀本來就是把同一段再讀一次，由 `merge_reread` 併回那一列。改完後，O-b 在 mini 上的對→錯從 8 降到 1。
4. **O-ab 變體。** 在看到 O-c 的結果之後才加上。它只是計畫中 O-a 和 O-b 兩個部分的組合，沒有新的規則。
5. **second opinion 的答案改用引文對回列。** 刪掉片段後列的位置會移動，所以每個已存的答案改成對到「引文相同」的重建列，而不是同一個位置的列。B 也用同一種方式，所以前後一致。

「至少重疊一半」與「只要重疊」兩種比對規則的結果完全相同（`units-any.json`）。

## 2. Q1：現行讀題把哪些片段當成要做的分析

金標片段共 64 個：D 50、Q 8、P 6。

| 回合 | D 讀到／漏讀／當成問題 | Q 被當成分析 | P 被當成分析 | 多出：E1／E2 第一次讀／E2 重讀複本／E3 | 分類全對的讀取 |
|---|---|---|---|---|---|
| p4b（mini） | 44／1／5 | 3/8 | 1/6 | 2／6／6／7 | 31/56 |
| p4c（mini） | 42／3／5 | 3/8 | 3/6 | 3／5／4／9 | 30/56 |
| p5r（mini） | 42／2／6 | 5/8 | 1/6 | 2／4／9／9 | 28/56 |
| g4o1（4o） | 43／2／4 | 7/8 | 5/6 | 1／4／16／14 | 24/55 |
| g4o2（4o） | 44／2／4 | 6/8 | 5/6 | 1／4／19／15 | 24/56 |
| v7-0（mini） | 41／9／0 | 4/8 | 0/6 | 0／0／0／5 | 42/56 |
| v7-1（mini） | 42／8／0 | 4/8 | 0/6 | 0／1／0／6 | 41/56 |

- **E2 重讀複本不算錯。** 重讀會把同一段再讀一次，由 `merge_reread` 併回同一列。表中列出只是為了完整。
- **「D 當成問題」大多是定義差異，不是讀錯。** 這些是問某方法能不能用某些設定或條件執行，例如 C08「Can GIRAFFE be run with my own optimizer settings?」，以及 C33、C51、C39、C48。closed-menu 把這類算成要求，現行合約則把它們放進 `about_methods`。
- **gpt-4o 更常把問題和目的當成要做的分析。** Q 被當成分析 13/16（mini 是 11/24）；P 被當成分析 10/12（mini 是 5/18）；多出的背景片段 E3 也更多。這和 10/17 觀察到「gpt-4o 在 CLARIFY 類比較差」一致。
- **v7 的分類比較穩定。**

| 兩次讀取 | 同一片段兩次結果相同 | 「分類全對」兩次一致 |
|---|---|---|
| p4b vs p4c | 56/64 | 45/56 |
| g4o1 vs g4o2 | 60/63 | 51/55 |
| v7-0 vs v7-1 | 63/64 | 53/56 |

- v7 每個金標片段被讀成哪一種 form（兩次合計）：

| 金標 | 讀成 D | 讀成 Q | 讀成 P | 讀成資料／背景或沒對上 |
|---|---|---|---|---|
| D | 83 | 11 | 1 | 5 |
| Q | 8 | 8 | 0 | 0 |
| P | 3 | 0 | 6 | 3 |

  其中「P 讀成 D」的 3 次，是目的被併進同一個 deliverable 片段，不是另外產生一項分析。

- **歸因（mini，以 B 的判斷分組）。** B 判錯的 37 份中，有 22 份有片段分類錯誤；B 判對的 131 份中，也有 57 份有。分類錯誤在對的判斷裡同樣常見。

## 3. Q2：把分類換成金標再判一次（現行流程）

### 3.1 B 與已存判斷

| 模型 | 讀取份數 | B 與已存判斷相同 | 已存判斷對 | B 對 |
|---|---|---|---|---|
| mini | 168 | 159 | 135 | 131 |
| gpt-4o | 111 | 103 | 86 | 86 |

mini 有 9 份不同，原因都已確認：

| 題目 | 已存 → B | 原因 |
|---|---|---|
| C18 ×3 | DECLINE → DO | 重放少了兩個步驟：p4b 是條件檢查；p4c、p5r 是「使用者說沒有的資料」（`without_ruled_out`）。**ROUND-12 更正**：原本寫三份都是條件檢查 |
| C27（p4b） | DECLINE → DO | 「只有某資料」的排除步驟沒有重放 |
| C31 ×2 | ASK → UNCHECKED | 已存的 ASK 來自 fact agent 的等待，重建的 check 沒有這個等待 |
| C10 ×2 | UNCHECKED → CLARIFY | 目前的程式較新（phase 5a：目標確定不清楚時，即使 routing 失敗也回答） |
| C51（p4b） | UNCHECKED → DECLINE | 第一次 check 失敗後的暫用讀取，被重建成一般的 check |

gpt-4o 的 8 份不同也屬於同樣幾類：
- C18 ×2：「使用者說沒有的資料」這一步沒有重放（ROUND-12 更正，原本寫條件檢查）；
- C44 ×2、C43 ×2、C10：目前的程式較新（已存的 C44 沒有條件檢查事件，是當時的程式沒有認可那一列）；
- C31：fact agent 的等待。

### 3.2 各變體相對 B 的轉移

| 變體 | mini 錯→對 | mini 對→錯 | gpt-4o 錯→對 | gpt-4o 對→錯 |
|---|---|---|---|---|
| O-a 刪掉被當成分析的 Q／P | 2 | 0 | 4 | 0 |
| O-b 刪掉多出的分析 | 0 | 1 | 0 | 2 |
| O-c goal 依金標 | 3 | 18 | 0 | 11 |
| O-ab（a＋b） | 2 | 1 | 4 | 2 |
| O 全部 | 4 | 14 | 1 | 11 |

依金標類別看 mini 的「B 對 → O 對」：DO 39→39/42、ASK 29→31/45、DECLINE 28→28/39、CLARIFY 35→23/42。

### 3.3 逐題說明（mini）

**O-ab 改對的 2 份**
- **p4c C23。** 目的句「I'd like a systems-level view…」被當成一項分析，又對不到任何方法，所以判 DECLINE full_gap。刪掉後判 CLARIFY，正確。
- **p5r C37。** 問句「Which of these should we apply」被當成兩項分析。刪掉後判 CLARIFY，正確。

**O-ab 改錯的 1 份：p4b C08（DECLINE → CLARIFY）**
- 設定句「I want a learning rate of 1e-4, 2,000 iterations…」被當成一項分析（E1）。B 因為這一列對不到方法而判 DECLINE，結論對，但理由不對。
- 真正的要求「Can GIRAFFE be run with my own optimizer settings?」被模型放在 `about_methods`。本輪規定不補漏讀的 D，所以刪掉 E1 之後沒有任何結果列，變成 CLARIFY。
- 這是只刪不補的上限算法造成的，不是分類修正本身的副作用。

**O-c 的 18 份改錯，都來自兩套定義不一致**
- **12 份是泛稱要求被強制設成 result_named：** C12 ×2、C15 ×3、C19 ×3、C49 ×3、C53 ×1。
  - 例句：「run the network analysis」「Analyze everything… and tell me what you find」「run whichever NetZoo analysis is appropriate」「Do whatever makes sense…」「see how genes are connected」。
  - 金標依 closed-menu 規則把它們算成 D，再用泛稱的結果類型判 vague。
  - 現行合約的 `result_named` 表示指名了具體結果，所以 CLARIFY 這條路被拿掉，變成 DECLINE full_gap 或 DO。
- **6 份是只有問題或目的的題目被設成 method_named：** C09 ×2、C23 ×2、C37 ×2。
  - 現行流程把 method_named 當成「點名了方法」走下去。O-c 單獨使用時，被誤判成分析的列還在，所以判 full_gap DECLINE。
- 金標的 form 無法直接換算成現行的 goal 值。計畫第 10 節預期的定義風險，實際出現在 O-c 而不是 O-a。

**O-c 改對的 3 份：p4b C57、p4c C34、p5r C34**
- 這幾份讀取把 goal 讀成不是 result_named，雖然請求其實指名了具體結果（C57 的 covariate-adjusted co-expression；C34 的兩種批次校正結果擇一）。
- 這就是 goal 讀錯最多能救回的份數。

**B 判錯的 37 份（mini），依「金標 → B」分類**

| 類別 | 份數 | 和片段分類的關係 |
|---|---|---|
| 該拒卻做了（DECLINE → DO results_given／run_held） | 9 | 無關。其中 4 份（C18 ×3、C27）是重放少了步驟造成的：p4b C18 是條件檢查，其餘 3 份是「使用者說沒有的資料」。ROUND-12 補齊重放後只剩 5 份，原因見 `false-accept-replay-2026-10-21/RESULTS.md` |
| 該問或該拒，卻請說清楚（→ CLARIFY no_result_read／goal_unclear） | 8 | 主要是 goal 讀錯，O-c 最多救回 3 份 |
| 該問卻未確認（ASK → UNCHECKED） | 5 | 無關（含 C31 ×2 的重放差異） |
| 該請說清楚卻拒絕（CLARIFY → DECLINE full_gap） | 3 | 就是 39% 那一類，O-a 救回 2 份 |
| 該請說清楚卻問或做（CLARIFY → ASK／DO） | 4 | 無關 |
| 該問卻做了（ASK → DO） | 4 | 無關（沒讀到疑問） |
| 該做卻拒絕（DO → DECLINE） | 2 | 1 份 full_gap、1 份 all_results_not_available |
| 該問卻拒絕（ASK → DECLINE full_gap） | 1 | 39% 那一類 |
| 該做卻未確認（DO → UNCHECKED run_held_unconfirmed） | 1 | 無關 |

合計 37 份。

**10/18 瓶頸分析中佔 39% 的「沒認可的列被算成做不到」（full_gap 或 all_results_not_available），在目前的程式下只剩 6 份。** 這一類已經大幅縮小。

## 4. Q3：v7 讀取的對照

用目前的程式重判第 1 階段的 112 份 focused 讀取，以 `phase0_gate.score` 計分。

| 變體 | 錯→對 | 對→錯 | 對的份數 |
|---|---|---|---|
| B（照讀） | — | — | 75/112（第 1 階段當時記錄 74/112） |
| forms：配對到金標的片段改成金標 form | 4 | 0 | 79 |
| extras：沒配對的 deliverable 改成 context | 4 | 2 | 77 |
| O：兩者都做 | 10 | 2 | 83 |

**改對（各兩次）**
- C09、C10、C26：「選哪個方法」的問句被當成 deliverable，改成 question_to_us 後判 CLARIFY。
- C37、C41：多出的 deliverable 片段改成 context 後判 CLARIFY。

**改錯：C34 ×2（ASK → CLARIFY）**
- 金標把「batch-corrected expression matrix，或 batch-adjusted co-expression」記成同一個片段的 artifact 疑問。v7 則讀成兩個 deliverable 片段。
- 把它們改成 context 後，疑問也一起消失。這是只改類型、不搬屬性的上限算法造成的。

## 5. 限制

- 56 題都已經看過，金標讀題是在知道答案的情況下寫的。這裡量的是上限，不是推廣能力。
- 重放不包含條件檢查、「只有某資料」的排除步驟和 fact agent 的等待，所以一律和 B 比，不和當時的分數比。
- 「只刪不補」：漏讀的 D 不補，也不把被刪片段的屬性（例如疑問）搬到保留的片段上。C08、C34 的改錯就是這個原因。
- 不是 D 的金標片段只有 14 個（Q 8、P 6），所以 Q 與 P 只報個數。
- 片段比對、判定類別和變體都由我一個人訂定與檢查，沒有第二位標記者。

## 6. 下一步的選項（由使用者決定）

1. **現行流程：不做 D1 付費試做（建議）。** 下一步改看第 3.3 節表中份數最多的兩類：
   - 該拒卻做了：需要重放條件檢查後再確認；
   - goal 讀錯導致 CLARIFY：需要先在金標補上「是否指名具體結果」這一欄，才能正確量測。
2. **如果要重新評估 closed-menu 路線：** Q3 顯示每段分類在那條線的上限是 +10／−2，可以把 D1 的分類步驟放進那條線做付費試做（上限 US$0.1，另外請你同意）。

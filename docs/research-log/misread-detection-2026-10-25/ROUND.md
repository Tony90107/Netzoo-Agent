# 讀錯偵測：程式能不能看出模型讀錯了請求（2026-10-25，寫偵測程式前宣告）

起點：`041f0ee9`（凍結版，`netzoo-agent/harness-repair`）。分支 `misread-detection`，worktree `.worktrees/netzoo-misread`。
本輪只量測，$0，不呼叫模型，不改凍結的程式，不採用任何東西。

## 起因

- 錯誤歸因（`harness-repair-2026-10-23/attribution/ATTRIBUTION.md`）：replay 的 143 筆錯誤中 135 筆在讀題層，h7 的 41 筆中 37 筆。
- 程式觸發的重讀只在程式看到缺口時才跑。多數讀錯在讀取內部是自洽的，所以什麼都沒觸發。
- 同一個模型重讀會重複同樣的錯（h5：46 題中 41 題每次讀法相同，8 題穩定讀錯；投票只 69 → 72／92）。
- 使用者決定（2026-10-25）：先不換更強的模型；先試試看程式能不能「看見」讀錯。

## 問題

錄製裡已經有好幾份**形狀不同**的讀取（routing 的語意讀取、intent router、hypothesis reader、data facts、fact agent、capability check、它的重讀），另外 capability check 本身也有程式能核實的結構。這些東西之間的不一致，能不能標出歸因標為讀題層的錯誤？標錯的（標到判對的讀取）有多少？

旗標的用途只有一種：**問使用者，而且只在答案會改變結果時才問**。絕不默默改採另一份讀取。

## 已排除、不重做的方向

| 方向 | 為什麼不重做 |
|---|---|
| 同一個判斷讀兩次、一致才採用（ROUND-15） | gpt-4o-mini 兩次讀取 98% 一致；不一致的 42 對被當成沒回答，判對 101 → 97／100 |
| 目標窄讀雙向交叉檢查（ROUND-23） | 給了結果但窄讀說沒指名 → 請說清楚：修好 7、改壞 6（點名 workflow 的執行請求被讀成沒指名結果） |
| 沒被引用的句子重讀（ROUND-16，D4） | 現行讀題形狀幾乎不漏句（0.7%），81 份判錯中最多 3 份可能有關 |
| A2′：fact agent 的提問代替 check 為 R1 作證 | 0 FIX、2 BREAK；使用者已說明的 log 轉換被追問（多問 8 → 10） |
| 同模型重讀投票 | h5 投票 69 → 72／92，8 題穩定讀錯 |

本輪和它們的差別：只量「旗標」與「問了會怎樣」，不採用；而且每個訊號都要先算「答案會不會改變結果」。ROUND-16 的未讀句子、A2′ 的 fact agent 提問會在本輪以訊號 Q1、X5 重新量一次，作為對照（不是新方法）。

## 資料

### 主要：B2 replay（`stability-round13-2026-10-21/harness.py` 的 1,388 份讀取，757 份有金標）

- 程式：凍結版 `041f0ee9`，標準模式（不設 `NETZOO_REPLAY_CURRENT_MODELS`），與歸因用的判定相同（A3 在標準 replay 0 改變）。
- 金標：`gold-p2.json` 的重標，計分用 `score.py` 的 `kind_of`。
- **錯誤**：143 份，每份有歸因標籤（`attribution/labels-replay-*.json`：層、子類）。
  - 讀題層 135：R-goal 61、R-fail 29、R-unc 22、R-cond 14、R-link 8、R-type 1；判定層 8。
  - **R-fail（29）不計入召回率的分母**：check 沒有可用的讀取，程式已經看得見（判 UNCHECKED）。另外單獨列出。
  - 所以主要分母是讀題層、非 R-fail 的 **106 份**。
- **判對**：614 份。旗標打在這裡 = 誤報。
- 同一題被讀很多次（56 題核心題各讀數次到數十次），所以每個數字同時報「依讀取」與「依題目」。

### 次要：h7 live（`harness-repair-2026-10-23/p5/live`）

- E（第 1 輪，`p5r1`）與 E′（第 2 輪，`p5r2`），各 36 個單輪 session，用 trace 裡的事件做同樣的計算（`a1c/redecide.py` 的讀法）。
- 錯誤：歸因標籤（`labels-h7-*.json`）中單輪的部分；判對的單輪 session 是誤報池。
- 多輪 session（各 14 個）只描述，不進門檻：歸因標的錯常在第 2、3 回合（R-follow），與第 1 回合的讀取無關。

## 訊號（全部只用程式計算，不呼叫模型）

共同條件（每個訊號都要）：**目前的判定是 DO 或 DECLINE**。程式已經在問（ASK、CLARIFY）或暫停（UNCHECKED）時，旗標不會改變結果，只記為「同時觸發」，不算命中也不算誤報。

「目前的判定」指凍結版在該讀取上的 replay 判定。

### X：兩份形狀不同的讀取不一致

| 代號 | 比的兩份讀取 | 觸發條件 | 主要目標 | 旗標後的動作 |
|---|---|---|---|---|
| X1 | routing 的 registry match ↔ capability check | registry match `status=ambiguous`，routing 的候選 workflow（`matched_actions`、`hypothesis_actions`、`recommended_actions`）≥ 2 個；discriminator 沒有 accepted、selection conditions 沒有 recommended；沒有任何需求列點名已登錄的方法，也不是執行請求；check 採信的 workflow 是 routing 候選的**真子集**（check 自己縮小了範圍，沒有任何一份讀取替它作證） | R-goal、R-link | CLARIFY |
| X2 | hypothesis reader ↔ check | `routing.hypothesis_bases_matched.question_mode = unclear_goal`，而判定是 DO 或 DECLINE（check 讀到了具體結果或整體缺口） | R-goal | CLARIFY |
| X3 | routing 的語意讀取 ↔ check | routing 讀到的 `requested_outcome.artifact_type = unknown`，或 `operation ∈ {unknown, explain}`；而判定是 DO 或 DECLINE | R-goal | CLARIFY |
| X4a | registry match ↔ check | registry match `status=unsupported`（routing 找不到任何 workflow），而 check 採信了結果、判 DO | R-link | ASK |
| X4b | registry match ↔ check | registry match `status=exact`，有 matched workflow，而判定是 DECLINE（check 判全部做不到） | R-link、R-cond（FR） | ASK |
| X5a | fact agent ↔ check | fact check 有被 R1（「the check did not read these words as the user being unsure」）拒絕的提案，而且該提案自己寫的 yes／no 兩個結果不同（`yes_outcome ≠ no_outcome` 或 `yes_workflow ≠ no_workflow`） | R-unc | ASK |
| X5b | 同上 | X5a，再限 `uncertainty = said_unknown`（使用者自己說不知道，不是模型認為可以兩讀） | R-unc | ASK |
| X6 | check 的第一次讀取 ↔ 它的重讀 | 錄製裡有重讀；同一段原文在兩份讀取中都有需求列，但一份可做（available／with_step／partial）一份做不到，或採信的 workflow 沒有交集 | R-link、R-cond | ASK |
| X7 | data facts reader ↔ check | data facts 讀到使用者沒有 priors（或 miRNA）（`ruled_out`），但 check 採信的 workflow 需要它，且 check 沒有記為 ruled_out；或反過來，data facts 讀為 stated，check 卻記為 ruled_out | R-cond | ASK |

X7 的「需要」只用 registry 或合約裡已有的輸入定義，不新寫詞表；若程式裡找不到這種定義，X7 不計算，在結果中註明。

### Q：同一份讀取內部，程式能核實的結構

| 代號 | 觸發條件 | 主要目標 | 旗標後的動作 |
|---|---|---|---|
| Q1 | 有沒被任何需求列涵蓋的句子（`check.unchecked` 非空） | 全部（ROUND-16 的對照） | ASK |
| Q2 | check 自己標為不確定的原文（`uncertain_quotes` 或最上層 `unknowns`）沒有接到任何需求列（沒有需求列的 `unknown_quote` 與它重疊，也沒有 needs_fact 列）——歸因的邊界型態 2 | R-unc | ASK |
| Q3 | 同一段原文同時在 `stated_quotes`（讀成有確定值）與 `uncertain_quotes`（讀成不確定）中 | R-unc、R-cond | ASK |
| Q4 | 一個可做的結果列同時有採信（`delivered_by`）與 near-miss（`not_by`）：讀取同時說「有 workflow 產生它」與「它是某個不產生的項目」 | R-link | ASK |
| Q5 | 同一句請求裡有兩個結果列，一個可做、一個做不到（同一句被拆成部分可做） | 次要目標：嚴格計分的 14 筆誤判部分可做；R-cond、R-link | ASK |
| Q6 | check 記錄了值的衝突（`fact_conflicts` 非空：結果自己的值與請求層的值不一致） | R-cond、R-type、R-count | ASK |

「重疊」一律用程式既有的比對（`request_spans.same_words`，不行時用去空白、小寫後的子字串），不新寫比對規則。

### 組合

- `ANY_X`、`ANY_Q`、`ANY`：各組任一觸發。
- `PASS`：通過個別門檻的訊號的聯集（若有）。

不另做其他組合。

## 量測：旗標會帶來什麼

### 1. 偵測

- **召回率**：讀題層、非 R-fail 的錯誤中被標出的比例，依子類（R-goal、R-unc、R-cond、R-link、R-type）與依錯誤類型（FA、FR、MA、問錯種類、多問）分開報。
- 判定層錯誤、R-fail 被標出的數目另列。
- **誤報率**：614 份判對的讀取中被標出的比例，依金標種類分開報。
- 每個數字都附「依題目」的版本：題目在任一份錯的讀取被標出，算該題命中。

### 2. 模擬第一回合的判定

旗標後的判定：目標類訊號（X1–X3）改成 CLARIFY，其餘改成 ASK。然後用 `kind_of` 對金標重新計分，報：

- FA、FR、MA、問錯種類、多問、判對，前後各多少；
- 新增的錯誤逐筆列出。

依 `score.py`：判對的 DO 或 DECLINE 被改成提問，算「多問」（代價，不是錯誤）；金標 CLARIFY 被改成 ASK、或金標 ASK 被改成 CLARIFY，算「問錯種類」（錯誤）。

**這個模擬是上限**：它假設問的正是該問的事，而且使用者回答後會得到對的判定。問句內容與第二回合都沒有量（記憶：第二回合從未量過）。

### 3. 例子

每個訊號各列幾筆命中與幾筆誤報；最好的訊號抽 15 筆誤報（seed 1025）由我逐筆看：那份讀取其實也讀錯了、只是碰巧判對，還是讀得沒問題。只報告，不改門檻。

## 門檻（量測前宣告）

一個訊號要同時滿足 G1–G3，才算「值得試行」：

| 門檻 | 內容 | 理由 |
|---|---|---|
| G1 命中 | 標出 ≥ 10 份讀題層、非 R-fail 的錯誤，分布在 ≥ 5 題 | 不能只是同一題被讀很多次 |
| G2 精確度 | 會改變判定的旗標中，打在錯誤上的份數 ≥ 打在判對上的份數（精確度 ≥ 50%） | 每一個多問至少要換到一個錯誤被移除 |
| G3 主要指標不變差 | 模擬後 FA、FR、MA 都不增加；問錯種類的增加 ≤ MA 的減少 | FA、FR、MA 是主要指標；問錯種類是錯誤 |
| G4 h7（次要） | 精確度不低於 30%，且至少標出 3 個錯的 session | replay 的讀取來自多個舊版本；h7 是接近凍結版的 live 讀取。不過 G4 只能否決，不能讓訊號通過 |

結論的三種寫法：

- **有訊號通過 G1–G4**：建議試行，方式是在新的 held-out 上以 shadow 模式記錄旗標（不改判定）。試行計畫另行宣告，需使用者核准。
- **有訊號通過 G1、G3，但 G2 不過**：報告為「看得見、但代價太高」，列出它們的精確度，不建議實作。
- **都不過**：建議不建；說明讀錯在現有錄製的形狀之間是否一致（也就是「錯得自洽」的程度）。

## 過度配適的限制（現在就寫下）

- 757 份讀取與 h7 在歸因時都已看過；訊號是在知道歸因子類與一些例子之後設計的。因此本輪的數字是**偏樂觀**的上限。
- 訊號在看到任何數字之前宣告於本文件，量測後不調整。量測後若想到新的變體，標為「事後」，不能用來通過門檻。
- 真正的確認只能在沒看過的請求上做，且要使用者核准費用。

## 付費步驟（只提議，不執行）

量完之後，若訊號的命中在某個子類明顯不足（例如 R-goal），提議一個新的、形狀不同的讀取，例如 closed-menu 的 per-workflow 讀取（`interpretation/menu_reader.py`，`judgment_defaults.yaml` 的 artifacts、generic 與 required 設定），只跑在幾十份錯誤讀取與同樣數量的判對讀取上。提議會附題目清單、份數與費用，等使用者核准。

## 產出

| 檔案 | 內容 |
|---|---|
| `ROUND.md` | 本文件 |
| `signals.py` | 每份讀取的訊號（replay） |
| `signals_h7.py` | h7 的訊號 |
| `measure.py` | 召回率、誤報率、模擬計分、例子 |
| `signals-replay.json`、`signals-h7.json`、`measure.txt` | 輸出 |
| `RESULTS.md` | 結果與建議 |
| `tests/test_misread_signals.py`（若需要） | 訊號計算的單元測試 |

不改 `scripts/` 下的任何檔案。

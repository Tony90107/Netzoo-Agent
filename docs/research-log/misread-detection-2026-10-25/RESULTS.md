# 讀錯偵測的結果（2026-10-25，$0，沒有呼叫模型）

設計與門檻見 [ROUND.md](ROUND.md)（量測前宣告；sha256 開頭 `35113c8ca563`，記於 2026-10-25 15:50:59）。起點 `041f0ee9`，凍結的程式沒有改。

## 結論

1. **依宣告的門檻，沒有訊號全部通過。**
   - X2、Q2 在 replay 上通過 G1–G3，誤報 0／614 與 1／614。
   - 但 h7 沒有任何一個單輪 session 是它們能作用的情形，G4「至少標出 3 個錯的 session」達不到。這是**案例不足**，不是反證。
2. **「讀錯在讀取內部是自洽的」只對了一半**（以下為事後分析，不用來過門檻）：
   - **MA 家族（該問沒問）看得見。** replay 的 64 份 MA 中，有 37 份在**已經錄下的讀取**裡留著程式看得見的痕跡，分布在 22 題。只有兩種痕跡：
     - research-framing reader（`routing.hypothesis_bases_matched`）判 `unclear_goal`（使用者不確定要追求哪個結果）；
     - check 自己記下了使用者不確定的原文（`uncertain_quotes`／`unknowns`），卻沒有接到任何需求列。
   - 這兩種痕跡合起來，只在 614 份判對的讀取中誤報 1 份。
   - **FA／FR 家族看不見。** 條件、輸入角色、結果連結讀錯（R-cond、R-link）的 FA 共 15 份。$0 能算的訊號裡：
     - 抓得到其中一部分的，都會同時標出大量判對的讀取（X4b 誤報 52、X5 誤報 171–223）；
     - 誤報少的（X1、X4a、X6、X7、Q4、Q5）幾乎抓不到。
3. **fact agent 的提問不能當「另一份讀取」**（X5，A2′ 的教訓的擴大版）：
   - 在 replay 與 h7，fact agent 都對約三分之一的判對讀取提出被 R1 拒絕的不確定；
   - 抽查的 15 筆誤報，它引用的全是使用者**陳述**的事實或請求本身，不是不確定。
4. **建議：現在不建。**
   - X2、Q2 的命中有 20／22 題是 56 題核心題（看過、讀過很多次），而且 h7 沒有可確認的案例。
   - 若要繼續，先付費確認（下面的 P2，約 US$0.15），再考慮試行。
   - FA 家族需要一份新的、形狀不同的讀取（P1，約 US$0.2），$0 的方法到此為止。

## 資料

| | 讀取 | 判對 | 錯誤 | 召回率分母（讀題層、非 R-fail） |
|---|---|---|---|---|
| replay（757 份有金標） | 757 | 614 | 143 | **106 份**（51 題）：R-goal 61、R-unc 22、R-cond 14、R-link 8、R-type 1 |
| 其中判定是 DO／DECLINE（旗標能改變判定） | | | | 82 份：MA 63、FA 15、FR 4 |
| h7 單輪（E、E′ 各 36） | 72 | 46 | 26 | 讀題層 25 |

- R-fail 29 份不計入分母：check 沒有可用的讀取，程式已經判 UNCHECKED。
- 凍結版重判 h7 的 trace，100 個 session 中 99 個與 live 判定相同。

## 每個訊號（宣告的量測）

「命中」= 讀題層、非 R-fail 的錯誤被標出，而且判定是 DO／DECLINE。「誤報」= 判對的讀取被標出，而且判定是 DO／DECLINE。精確度 = 被標出的錯誤 ÷（被標出的錯誤 + 誤報）。

| 訊號 | 比的是什麼 | 命中（題） | 誤報／614 | 精確度 | G1 | G2 | G3 | h7 命中／誤報 | G4 |
|---|---|---|---|---|---|---|---|---|---|
| X1 | routing 平手，check 自己縮小範圍 | 8（3） | 14 | 36% | – | – | ✓ | 2／0 | – |
| **X2** | **research-framing reader 判 unclear_goal，判定卻是 DO／DECLINE** | **21（11）** | **0** | **100%** | ✓ | ✓ | ✓ | 0／0 | – |
| X3 | routing 的結果是 unknown／explain | 11（8） | 29 | 28% | ✓ | – | ✓ | 1／0 | – |
| X4a | routing 說不支援，check 採信 | 3（1） | 11 | 21% | – | – | ✓ | 0／0 | – |
| X4b | routing 完全吻合，判定卻是 DECLINE | 10（7） | 52 | 17% | ✓ | – | ✓ | 5／4 | ✓ |
| X5a | fact agent 的提問被 R1 拒絕，且兩個答案的結果不同 | 23（14） | 223 | 10% | ✓ | – | ✓ | 17／18 | ✓ |
| X5b | X5a，限「使用者說不知道」 | 18（12） | 171 | 10% | ✓ | – | ✓ | 17／14 | ✓ |
| X6 | 第一次讀取與重讀對同一段原文的判斷相反 | 2（2） | 7 | 22% | – | – | ✓ | 0／0 | – |
| X7 | data facts 與 check 對「有沒有 priors／miRNA」相反 | 1（1） | 0 | 100% | – | ✓ | ✓ | 0／0 | – |
| Q1 | 有句子沒被讀（ROUND-16 的對照） | 1（1） | 3 | 25% | – | – | ✓ | 0／0 | – |
| **Q2** | **check 記下的不確定原文沒接到任何需求列** | **32（21）** | **1** | **97%** | ✓ | ✓ | ✓ | 0／0 | – |
| Q3 | 同一段原文既是「已陳述」也是「不確定」 | 1（1） | 1 | 50% | – | ✓ | ✓ | 0／0 | – |
| Q4 | 同一列同時有採信與 near-miss | 4（3） | 22 | 19% | – | – | ✓ | 0／0 | – |
| Q5 | 同一句被拆成可做與做不到兩列 | 3（3） | 15 | 17% | – | – | ✓ | 0／2 | – |
| Q6 | check 記錄了值的衝突 | 0 | 0 | – | – | – | ✓ | 0／0 | – |
| ANY_X | | 54（28） | 252 | 18% | ✓ | – | ✓ | 17／19 | ✓ |
| ANY_Q | | 38（26） | 34 | 53% | ✓ | ✓ | ✓ | 0／2 | – |
| ANY | | 71（40） | 257 | 22% | ✓ | – | ✓ | 17／19 | ✓ |

- **依子類**（ANY 的命中）：R-goal 34／61、R-unc 20／22、R-cond 11／14、R-link 6／8、R-type 0／1。R-cond 與 R-link 的命中幾乎全來自 X5、X4b，所以都帶著大量誤報。
- 判定層錯誤被標出的最多 2 份（X5a），R-fail 0 份。
- X4b、X5 的誤報大多是金標 DECLINE 的正確拒絕（X4b 52 份全是，X5a 91 份），被改成提問。依 `score.py`，這算「多問」。

### 模擬第一回合的判定（宣告的量測；上限，問句與第二回合都沒量）

| 訊號 | 判對 | FA | FR | MA | 問錯種類 | 多問 |
|---|---|---|---|---|---|---|
| 凍結版 | 614 | 15 | 5 | 64 | 18 | 11 |
| X2 | 629 | 15 | 5 | 43 | 24 | 11 |
| Q2 | 634 | 15 | 5 | 32 | 29 | 12 |
| X5b | 443 | 11 | 3 | 51 | 31 | 188 |
| ANY | 400 | 3 | 0 | 8 | 31 | 285 |

- 沒有任何訊號新增 FA、FR 或 MA（提問不會造成這三種錯）。
- 只有 ANY 把 FA 降到 3，代價是多問 11 → 285。

### 抽查（ROUND 宣告：最好的訊號抽 15 筆誤報）

- X2 沒有誤報；Q2 只有 1 筆：
  - p3 C27「Can SAMBAR subtype our 210 hepatocellular carcinomas from the RNA-seq expression matrix? …」；
  - check 把這個提問句放進了不確定的原文。問了只是在一個正確的拒絕前多問一句。
- 所以改抽 X5b 的 15 筆誤報（seed 1025，`posthoc.txt` 第 5 節）。fact agent 標為「使用者說不知道」而引用的是：
  - 已陳述的事實：「every gene has been mean-centered」「the weights were already thresholded so none are negative」「120 matched samples, 2,000 transcripts and 500 proteins」；
  - 請求本身：「Can GIRAFFE estimate an activity score …」「I need that patient's own TF-to-gene regulatory network」；
  - 設定：「sparsify on with bonobo_confidence 0.01」「please use a learning rate of 0.001」。
  - **15 筆中沒有一筆是真正的不確定。** fact agent 的 `uncertainty` 欄位不可靠，A2′ 失敗的原因不只在 BONOBO 的宣告。

## 事後分析（不能用來過門檻；`posthoc.py`、`posthoc.txt`）

### X2、Q2 為什麼精確

- research-framing reader 判 `unclear_goal` 的 160 份有金標讀取，金標**全是** CLARIFY（98）或 ASK（62），沒有一份是 DO 或 DECLINE。h7 的 24 個 session 也一樣（ASK 18、CLARIFY 6）。
- Q2 觸發的 200 份讀取，金標是 ASK 121、CLARIFY 77、DECLINE 2，沒有 DO。
- 這些讀取大多已經在問（X2 的 160 份中 131 份已是 ASK／CLARIFY）。少數判 DO／DECLINE 的，幾乎都是錯的。

### 它們出現在什麼情形

| | fact agent 之前（p0、p1） | fact agent 之後（p2 起、h1–h4） |
|---|---|---|
| 讀取／判對 | 127／73 | 630／541 |
| 目標錯誤（判定是 DO／DECLINE） | 43（39） | 63（43） |
| X2∪Q2 命中 | 19（15 題），誤報 0 | **18（11 題），誤報 1／541** |
| X5b 命中 | 0 | 18，誤報 171 |

- **X2∪Q2 在 fact agent 之後的錄製仍然有效**，不只是 ROUND-A 說的「型態 2 是錄製產物」。
- 命中時 fact agent 的狀態：沒有跑 27、被預算擋下 3、失敗 1、有跑 6。
- 凍結版在 check 判整體缺口時沒有候選 workflow，`fact_candidates` 為空，fact agent 就不跑。C24、C37、C54、C41 這類「模糊請求被讀成做不到的結果 → DECLINE」正走這條路，現行 live 仍會發生。h7 沒有這種題（模糊題 9／9 判對），所以沒有案例。
- **h7 中唯一能作用的是多輪 M05（兩輪都錯）**：X2 觸發，DECLINE 會改成 CLARIFY。它的金標是 ASK，所以會變成問錯種類，不過拒絕被拿掉了。

### X2∪Q2 合起來（X2 先問目標）

- 全部讀取：判對 614 → 643；MA 64 → 27；問錯種類 18 → 25；多問 11 → 12；FA、FR 不變。
- 只算 fact agent 之後：判對 541 → 553；MA 33 → 15；問錯種類 15 → 20。
- 標出的 37 份錯誤全是 MA，分布在 22 題：C09、C10、C11、C20、C21、C24、C26、C31、C34、C36、C37、C39、C41、C42、C43、C44、C45、C50、C54、C56，以及 h4 的 M01、M36。
- 問錯種類增加，是因為 X2 對金標 ASK 的題也觸發（C11、C31、C34、C21），Q2 對金標 CLARIFY 的題也觸發（C24、C37、C09、C10）。**兩個訊號都只說「該問」，不說該問目標還是事實。**

### closed-menu 的讀取當作另一份讀取（M）

- closed-menu phase 1 曾為 56 題核心題各錄 2 次 menu 讀取（`closed-menu-phase1-2026-10-18/live/p1`）。用它自己的判定當作題目層級的旗標。
- **兩次 menu 讀取都判要問，而 check 判 DO／DECLINE**：命中 56／95（26 題，R-goal 39、R-unc 16、R-link 1），誤報 29／444。誤報只來自 3 題：C04、C28、C58，都是金標 DO 而 menu 讀取會多問的題。
- 其中 24 份是 X2∪Q2 沒抓到的，幾乎全是 R-goal：C53（「how genes are connected」）8 份、C23 6 份、C12 3 份，其餘 7 題各 1–2 份。
- 限制：這是題目層級的比對（每題一份 menu 讀取對上同一題的十幾份 check 讀取），而且只有核心題有 menu 讀取。

## 限制

- **過度配適。** 757 份讀取與 h7 在歸因時都已看過；X2、Q2 的命中有 20／22 題是核心題。核心題每題被讀的次數中位數 10、最多 13，所以讀取數會放大題目數。
- **replay 的讀取大多不是現在的模型。** replay 中 capability check 的呼叫有 890／1,443 次是 nemotron（`:free`），383 次是 gpt-4o-mini。h7 才是現在的 gpt-4o-mini。
- **h7 沒有 X2、Q2 能作用的單輪案例。** G4 因此無法確認，也無法否決。
- **模擬只到第一回合的判定種類。** 它假設問的正是該問的事，而使用者回答後會得到對的判定。X2、Q2 都不說該問目標還是事實，也不知道答案會導向哪個 workflow，所以「只在答案會改變結果時才問」只能由共同條件（判定是 DO／DECLINE）近似。
- **research-framing reader 不是每個回合都跑**：replay 757 份中 320 份沒有它，h7 100 個 session 中 31 個沒有。
- 論文整理的檔案 `output/thesis/2026-10-24_harness修復與錯誤歸因_實驗整理.md` 不在指定的路徑（`output/thesis/` 最新的是 10-22）。本輪改以 `attribution/ATTRIBUTION.md` 與 `FREEZE.md` 為依據。

## 建議

**現在不建，凍結版不動。** 理由：沒有訊號通過全部宣告的門檻；唯一有希望的 X2、Q2 只在看過的核心題上量到，h7 無案例可確認。

若要繼續，有兩個付費步驟，都只提議，等你核准：

### P2：在沒看過的請求上確認 X2、Q2、M（建議先做）

- **目的**：拿到 G4 缺的案例。這是決定 X2、Q2 值不值得試行的唯一方法。
- **題目**：新的盲寫題組 h9，24 題，由盲的 subagent 只依合約撰寫，第二個盲的 subagent 覆核，寫完封存。分四組，各 6 題：
  - V：模糊的目的，容易被讀成一個做不到的具體結果（C24 形狀：「reviewers asked for a network analysis」）；
  - U：具體請求，旁句有一個決定結果的不確定（C20 形狀：「I'm not sure which file this is」）；
  - K1：對照，能做的請求，帶不影響結果的問句或客氣的保留語；
  - K2：對照，做不到的請求，範圍外。
- **跑法**：凍結版 live，每題 1 次（24 個 session），錄 trace；再用 closed-menu reader 讀每題 1 次（算 M）。X2、Q2、M 都離線計算，不改判定。
- **門檻**（跑之前另行宣告）：沿用 G1–G4，改成在 h9 上計算；另加「K1、K2 的誤報 ≤ 2」。
- **費用**：session 約 US$0.10（h8 是 24 個 session US$0.096）；menu 讀取約 US$0.04（phase 1 實際每次讀取加聚焦重讀約 US$0.0017）。**合計約 US$0.15，上限 US$0.20**，gpt-4o-mini。

### P1：per-workflow 的合約讀取，看 FA 家族能不能被看見

- **目的**：$0 的訊號都看不見 R-cond、R-link 的 FA。測一份形狀不同、只看已採信 workflow 的讀取，會不會在這些地方和 check 不一致。
- **用的程式**：現有的 contract veto 讀取（`graph/contract_veto_call.veto_reads` 與 `interpretation/contract_veto.contract_veto`：slim 核心讀取、限制欄位讀取、合約條款核對）。只計算「會否決」與「會追問」的旗標，不改判定。不寫新的提示。
- **讀取清單**（判定 DO、X2∪Q2 沒標出的錯誤，加對照）：
  - replay 錯誤 28 份，共 14 個請求：C01、C03、C14、C18、C23、C27、C30、C36、C47、C53、J15、M25、M46、M48（FA：R-cond 9、R-link 5、R-type 1；MA：R-goal 12、R-unc 1）；
  - h7 單輪錯誤 11 個 session，共 7 題：S05、S07、S08、S16、S19、S25、S28（R-link 6、R-cond 2、R-unc 3）；
  - 對照：replay 判對的 DO 讀取 175 份，共 63 個請求（h1–h4 48 份、核心題 127 份），加上 h7 判對的單輪 DO 13 個。
  - 依（請求、check 採信的 workflow）去重，約 100 組。
- **費用**：錄製中的 contract veto 呼叫，核心讀取約 2.3k 輸入、250 輸出 token，限制讀取約 0.9k、180，每組約 US$0.0009。每組讀 2 次（看穩定度）約 US$0.18。**上限 US$0.25**，gpt-4o-mini。
- **已知風險**：closed-menu hybrid 在 h4 曾經 FA 3 → 1，但 4 次否決中有 2 次是讀錯的。當作旗標（問而不拒）時，讀錯的否決會變成多問，不會變成誤拒。

## 後續：P2 已執行（2026-10-25，US$0.1548）

使用者核准 P2。結果見 [RESULTS-H9.md](RESULTS-H9.md)：

- X2、Q2 在 h9 上 0 命中，誤報都打在刻意放了「無關不確定」的對照題上，依宣告撤回。本文件中它們在 replay 上的精確度，是題組裡沒有這類對照所造成。
- M（closed-menu 讀取不同意）在 h9 上命中 4、誤報 2，通過宣告的門檻；可以提議 shadow 試行，需要另行宣告並核准。

## 後續：M 的 shadow 試行（36 題版，2026-10-25，US$0.2011）

見 [RESULTS-M-SHADOW.md](RESULTS-M-SHADOW.md)：

- 在新的 h10 上，D1、D2、D4 通過（命中 6、精確度 6／11）；
- D3 不過：K 組誤報 5 個，其中 DRAGON 3 個。依宣告撤回 M，第 2、3 回合沒有跑。

## 檔案

| 檔案 | 內容 |
|---|---|
| `ROUND.md` | 設計與門檻（量測前宣告） |
| `signals.py`、`signals-replay.json` | replay 每份讀取的判定與訊號 |
| `signals_h7.py`、`signals-h7.json` | h7 每個 session 第一回合的判定與訊號 |
| `measure.py`、`measure.txt`、`measure.json` | 宣告的量測：召回率、誤報、模擬、門檻、例子 |
| `posthoc.py`、`posthoc.txt` | 事後分析：依年代、fact agent 狀態、X2∪Q2、closed-menu 的 M、抽查、P1 的讀取清單 |

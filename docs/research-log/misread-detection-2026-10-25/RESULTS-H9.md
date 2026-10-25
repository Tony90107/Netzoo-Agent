# P2 的結果：在沒看過的請求（h9）上確認 X2、Q2、M（2026-10-25，US$0.1548）

依 [ROUND-H9.md](ROUND-H9.md) 執行（任何 live 呼叫前宣告；sha256 開頭 `abf1d4e64deb6f48`，記於 16:11:36，跑完後未變）。沒有改任何判定，也沒有改凍結的程式。

## 結論

| 訊號 | 命中（可作用的錯誤） | 誤報（判對的 DO／DECLINE） | 精確度 | G1 | G2 | G3 | G5 | 依宣告的規則 |
|---|---|---|---|---|---|---|---|---|
| X2 | 0 | 1（Z24） | 0% | – | – | ✓ | ✓ | **撤回** |
| Q2 | 0 | 2（Z17、Z24） | 0% | – | – | ✓ | ✓ | **撤回** |
| X2∪Q2 | 0 | 2 | 0% | – | – | ✓ | ✓ | **撤回** |
| **M** | **4（Z03、Z05、Z21、Z22）** | **2（Z14、Z23）** | **67%** | ✓ | ✓ | ✓ | ✓（剛好 2） | **在沒看過的請求上通過**；可提議 shadow 試行，需另行宣告並核准 |
| X2∪Q2∪M | 4 | 4 | 50% | ✓ | ✓ | ✓ | –（4） | 不通過 |

- **案例足夠**：V、U 兩組共有 3 個可作用的錯誤（Z03、Z21、Z22），不是「案例不足」。
- **X2、Q2 在 replay 上的精確度是題組造成的。** 它們偵測的是「使用者表達了不確定」，而不是「這個不確定會影響結果」。
  - replay 的核心題中，寫進請求的不確定幾乎都是關鍵的，因為題目就是這樣設計的。
  - h9 的 K1、K2 刻意放了無關的不確定。兩個訊號都標了它們：
    - Z17：「I'm not sure if my supervisor will want the figures in colour or greyscale.」被 check 記成不確定；
    - Z24：「trying between 2 and 6 subtypes」被記成不確定，而 research-framing reader 也判 `unclear_goal`。
- **h9 的 3 個 V／U 錯誤，讀錯都是自洽的**，X2、Q2 都無從觸發：
  - Z21、Z22：check 完全沒讀到不確定（`uncertain_quotes` 是空的；Z22 把「either … or …」那段當作背景）。research-framing reader 在 Z21 沒有執行，在 Z22 判 `single_goal`。
  - Z03：check 把「understand the regulation and interactions」採信給 PANDA、PUMA、OTTER；research-framing reader 也判 `single_goal`。
- **只有 closed-menu 讀取（M）不同意。** 這是唯一一份形狀完全不同、從頭讀整個請求的讀取。

## 執行

| 項目 | 數量 | 費用 |
|---|---|---|
| 冒煙測試（Z05，不計分） | 1 個 session | US$0.0067 |
| 主回合 | 24 個 session | US$0.0987 |
| closed-menu 讀取（v8，第一次讀取加聚焦重讀） | 24 次 | US$0.0495 |
| **合計** | | **US$0.1548**（上限 US$0.20，runner 從未擋下） |

- 系統：乾淨的 detached worktree `.worktrees/netzoo-h9-run`，HEAD `041f0ee9`，沒有改動。三輪（冒煙、主回合、menu）的前後與每個工作的前後都核對了指紋，全部相同（`finished-*.json` 的 `runtime_code_unchanged: true`）。
- 所有角色都是 gpt-4o-mini；capability check 與 goal read 是 `gpt-4o-mini-2024-07-18`。
- 凍結版離線重判 24 個 trace，24／24 與 live 判定相同。
- 24 次 menu 讀取全部成功，沒有失敗的讀取。

## 題組 h9

- 盲寫的 subagent 只讀合約與 registry；第二個盲的 subagent 覆核，0 處修改。
- 我逐題讀過 24 題金標，24／24 同意。Z06 的算術重算過，COBRA、LIONESS-COEXPRESSION、DRAGON→CONDOR、COBRA→LIONESS、SAMBAR 的條件都在合約原文中核對過。
- 封存：`h9/SEALED.json`，items.json 的 sha256 開頭為 `351cc3aa`。
- 分組：V（沒選結果）6 題、U（具體請求加一個關鍵的不確定）6 題、K1（能做，附無關的問句或不確定）6 題、K2（做不到，同樣附一句）6 題。

## 凍結版在 h9 上的表現（不當門檻）

| 組 | 判對 | 錯的 session |
|---|---|---|
| V | 4／6 | Z03 判 DO（MA）；Z18 判 UNCHECKED（check 未確認） |
| U | 4／6 | Z21 判 DO（MA）；Z22 判 DECLINE（MA） |
| K1 | 4／6 | Z05 判 DECLINE（FR：GIRAFFE 的兩個結果都被讀成做不到）；Z19 判 DECLINE（FR：「gene IDs in the first column」被綁到 `genes_axis`，判為不明確的值而拒絕） |
| K2 | 5／6 | Z12 判 CLARIFY（多問：「證明因果」被當成目標不明） |
| 合計 | **17／24** | FA 0、FR 2、MA 3、多問 1、UNCHECKED 1 |

另外 Z24 判 DO + partial：無關的那一句（「I'm not sure yet whether I'll show the subtypes at the department retreat …」）被讀成一個做不到的結果列。依嚴格計分，這是誤判部分可做。

## M 的細節

- **命中的 4 個**：
  - Z03（V，金標 CLARIFY）：menu 判 ASK／intent，也就是問要哪個結果。依 `score.py`，ASK 對金標 CLARIFY 算問錯種類，所以 MA 變成問錯種類。
  - Z05（K1，金標 DO）：menu 判 ASK／intent。FR 變成多問。
  - Z21、Z22（U，金標 ASK）：menu 判 ASK／intent，依判定種類算判對。
- **誤報的 2 個**：Z14（K2，DRAGON 三層）與 Z23（K1，DRAGON 兩層），menu 都判 ASK／intent。兩個都是 DRAGON。
- **模擬第一回合**：判對 17 → 17；MA 3 → 0；FR 2 → 1；問錯種類 0 → 1；多問 1 → 4；FA 0 → 0。
- **要特別注意的地方**：
  - M 在 Z21、Z22 問的是「要哪個結果」，不是真正決定結果的事實（是哪個檔案）。計分只比判定種類，所以算判對；問句是否導向正確的第二回合沒有量。Z05 的結果其實已經說清楚，M 是因為 menu 自己讀錯才問。
  - menu 讀取本身很常問：24 題中有 15 題判 ASK 或 CLARIFY。旗標只在判定是 DO／DECLINE 時作用，在已在提問的 9 個 session 上不改變任何事。
  - menu 自己的判定也是 17／24 判對，和凍結版一樣多，但錯在不同的題：U 組 menu 6／6、系統 4／6；K1 組 menu 3／6、系統 4／6。兩份讀取的錯誤互補，所以不一致才有資訊。
  - 樣本很小：精確度 4／6，G5 的 2 個誤報剛好在上限。
  - replay 上的 M（事後分析，v7 形狀、每題讀 2 次、只有核心題）：命中 56、誤報 29，誤報集中在 3 題。

## 其他訊號（只描述，不進門檻）

| 訊號 | 標出的錯誤 | 標出的判對 |
|---|---|---|
| X5a | Z03、Z05、Z19、Z21、Z22 | 8 個（Z08、Z09、Z13、Z14、Z15、Z20、Z23、Z24） |
| X5b | Z03、Z05、Z19 | 7 個 |
| X4b | Z19、Z22 | Z08、Z14、Z17 |
| X3 | – | Z20 |
| X6 | – | Z13 |
| X1、X4a、X7、Q1、Q3–Q6 | – | – |

fact agent 的不一致（X5a）在 h9 上，對 9 個判對的 DO／DECLINE session 觸發了 8 個。它不能當作讀錯的證人，與 replay、h7 的結論一致。

## 建議

1. **X2、Q2 依宣告撤回。** 它們偵測的是「表達了不確定」，不是「不確定會影響結果」，而能分辨這兩者的正是決定結果的合約知識。replay 的結論應改為：這兩個訊號在核心題上的精確，是題組裡沒有無關不確定的對照所造成。
2. **M 依宣告通過，可以提議 shadow 試行**（只記錄旗標、不改判定）。試行計畫要另行宣告並核准。我建議計畫至少包含：
   - **量問句，不只量判定種類**：M 的旗標要問什麼？menu 的 intent 問題在 Z21、Z22 問錯了東西。可以讓旗標只負責「先不要執行」，問句另由 fact agent 或 clarify 路徑提出，並量第二回合；
   - **更大的新題組**，把精確度的區間縮小：現在是 4／6。DRAGON 類的對照要多放，因為兩個誤報都是 DRAGON；
   - **費用**：每回合多一次 menu 讀取，約 US$0.002。
3. **對論文的意義**：
   - 「讀錯在讀取內部是自洽的」在現在的 live 讀取上大致成立。h9 的錯誤，check 與 research-framing reader 都一起錯；只有一份形狀完全不同、獨立讀整個請求的讀取，才會在錯誤處不同意。
   - 同模型、同形狀的重讀做不到這一點（ROUND-15）。

## 檔案

| 檔案 | 內容 |
|---|---|
| `ROUND-H9.md` | 設計與門檻（跑前宣告） |
| `h9/` | brief、題目、覆核、格式檢查、封存 |
| `run_h9.py` | runner（上限、指紋、menu 讀取） |
| `round-h9smoke.json`、`round-h9.json`、`round-h9menu.json`、`jobs-*.json`、`finished-*.json`、`main-h9.log`、`menu-h9.log` | 執行紀錄 |
| `live/h9smoke/`、`live/h9/` | 每個 session 的 trace、session.json、cards |
| `menu-h9.json` | 24 次 menu 讀取（讀取內容、判定、費用） |
| `score_h9.py`、`score-h9.txt`、`score-h9.json` | 離線計算與計分 |

# P2：在沒看過的請求（h9）上確認 X2、Q2、M（2026-10-25，任何 live 呼叫前宣告）

使用者核准（由 session「Evidence-bound harness repair」轉達，原話）：「Approve P2 as proposed in the misread-detection RESULTS.md: fresh blind h9 set (24 items, 4 groups V/U/K1/K2), frozen system live 1 session each plus one closed-menu read each, X2/Q2/M computed offline, gates declared before running, cap US$0.20.」

起因與候選訊號見 [RESULTS.md](RESULTS.md)：X2、Q2 在 replay 通過 G1–G3，但 h7 沒有它們能作用的案例（G4 案例不足）；M 是事後分析。本輪只量測，不改任何判定，不採用任何東西。

## 要確認的訊號（定義不變，見 ROUND.md）

| 代號 | 觸發條件 | 旗標後的動作 |
|---|---|---|
| X2 | research-framing reader（`routing.hypothesis_bases_matched`）的 `question_mode = unclear_goal`，而判定是 DO 或 DECLINE | CLARIFY |
| Q2 | check 自己記下的不確定原文（`uncertain_quotes` 或最上層 `unknowns`）沒有接到任何需求列，也沒有 needs_fact 列，而判定是 DO 或 DECLINE | ASK |
| M | 同一題的 closed-menu 讀取（第一次讀取加聚焦重讀，`decide_menu` 的判定）是 ASK 或 CLARIFY，而判定是 DO 或 DECLINE | 依 M 的判定種類 |
| X2∪Q2 | 任一觸發；X2 先問目標 | |
| X2∪Q2∪M | 任一觸發；X2 先問目標，其次 M 的種類，最後 Q2 | |

- X2、Q2 用 `signals.py` 的 `compute`，在每個 session 第一回合的 trace 上計算（與 `signals_h7.py` 相同的讀法）。
- 「判定」是 live 錄下的 `core.decision`。凍結版離線重判同一份 trace 的結果一併記錄；兩者不同的 session 逐一列出。
- **M 的差別**：phase 1 錄的是 v7 形狀，每題 2 次讀取；凍結版的 menu reader 是 `READER_SHAPE = "v8"`，本輪每題讀 1 次。所以 M 在 h9 上是「新形狀、單次讀取」的版本，結果只代表它自己。
- 其他 13 個訊號也會算，只描述，不進門檻。

## 題組 h9

- 24 題、單輪，id 為 Z01–Z24，以固定 seed 打亂，讓 id 的順序看不出分組。
- 由盲的 subagent 撰寫：只讀 `workflows/*.yaml` 與 `scripts/workflow_registry.py`（本 worktree 的，等同 `041f0ee9`）。brief 只描述使用者的情境，不提任何訊號、不提舊題。
- 由第二個盲的 subagent 依合約覆核金標；我再逐題看過金標後封存（sha256），封存後才跑 live。
- 分四組，各 6 題：

| 組 | 使用者的情境 | 金標 |
|---|---|---|
| V | 有具體的理由和資料，但沒說要哪一種結果；用字可能聽起來像一種輸出（「a network」「regulation」「modules」），卻沒挑定一種 | CLARIFY |
| U | 具體請求，結果已說明；另一句說自己不確定一個事實，而依合約這個事實決定結果 | ASK |
| K1 | 能做的請求；其中有一句問句或保留語，但不影響結果（客氣的問法、無關的不確定，例如報告的場合） | DO |
| K2 | 做不到的請求，原因清楚；同樣帶一句不影響結果的問句或保留語 | DECLINE |

## 跑法

- **系統**：凍結版 `041f0ee9`，放在乾淨的 detached worktree `.worktrees/netzoo-h9-run`（不 commit，沒有任何改動，沒有未追蹤的檔案）。
- **指紋**：每個 session 前後，都核對 `scripts`、`workflows`、`prompts`、`AGENTS.md` 每個檔案的 hash 與 HEAD。只要不同就停止，那一輪作廢。
- **模型**：gpt-4o-mini（`OPENROUTER_CAPABILITY_MODEL = openai/gpt-4o-mini-2024-07-18`，其餘角色 `openai/gpt-4o-mini`）。設定不符就不開始。
- **次數**：
  - 冒煙測試 1 個 session（一題 K1），確認設定，不計分，費用計入上限；
  - 主回合 24 個 session，每題 1 次，從不重跑；
  - closed-menu 讀取每題 1 次（第一次讀取加聚焦重讀），同樣從不重跑。
- **費用上限 US$0.20，由 runner 強制**：
  - 每開始一個工作前，先算「已花費 + 進行中工作的預留 + 這個工作的預留」。超過 US$0.20 就不開始，並記錄停止原因。
  - 預留：每個 session US$0.015（回合預算 30,000 加 allowance 30,000 token 的上限估計），每次 menu 讀取 US$0.005。
  - 已花費以提供者回報的費用為準：session 取 trace 與 session.json 的 `cost_micro_usd`，menu 讀取取回應的 usage。
- **預估**：冒煙 US$0.006 + 24 個 session 約 US$0.10（h8 為 US$0.096）+ 24 次 menu 讀取約 US$0.04，**合計約 US$0.15**。
- 沒有條件性的第二輪。案例不足就照實報告，要再跑需要另外核准。

## 計分

- 金標種類：PARTIAL 視為 DO（系統以 DO + partial 表示）。`also_acceptable` 中的種類也算對。
- 錯誤種類依 `score.kind_of`：FA、FR、MA、問錯種類、多問、UNCHECKED。
- **可作用的錯誤**：判定是 DO 或 DECLINE 而且錯的 session。旗標只能改變這些。
- **誤報**：判定是 DO 或 DECLINE 而且對的 session 被標出。
- h9 沒有逐筆的歸因標籤，所以召回率的分母是可作用的錯誤，不再區分讀題層與判定層。我會對每個可作用的錯誤，附一句我讀 trace 後的層次判斷，只當描述。

## 門檻（ROUND.md 的 G1–G4，改成在 h9 上計算）

| 門檻 | 在 h9 上的定義 | 與 ROUND.md 的差別 |
|---|---|---|
| G1 命中 | 標出 ≥ 3 個可作用的錯誤 session（每題只跑 1 次，所以也是 ≥ 3 題） | 原本是 replay 的 ≥ 10 份、≥ 5 題；h9 只有 24 題，改用原 G4 的案例數 |
| G2 精確度 | 被標出的錯誤 ≥ 被標出的判對 session（精確度 ≥ 50%） | 相同 |
| G3 主要指標不變差 | 模擬後 FA、FR、MA 都不增加；問錯種類的增加 ≤ MA 的減少 | 相同 |
| G4 live | h9 本身就是凍結版的 live 讀取，所以原 G4（精確度 ≥ 30%、≥ 3 個錯）已被 G1、G2 涵蓋 | 併入 G1、G2 |
| G5 對照 | K1 與 K2 合計誤報 ≤ 2 | 新增（使用者指定） |

**結論的寫法**：

- **某訊號通過 G1、G2、G3、G5**：在沒看過的請求上確認。可以提議試行，方式是 shadow 模式（只記錄旗標，不改判定），計畫另行宣告、需要核准。
- **V、U 兩組合計的可作用錯誤少於 3 個**：凍結版在 h9 上本來就幾乎沒有這類錯誤，結論是「案例不足」，訊號維持候選。
- **其他情形（有案例但不過門檻）**：撤回該訊號，不再以這份錄製調整定義。

## 產出

| 檔案 | 內容 |
|---|---|
| `ROUND-H9.md` | 本文件 |
| `h9/AUTHOR-BRIEF.md`、`h9/REVIEW-BRIEF.md`、`h9/items-author.json`、`h9/items.json`、`h9/GOLD-REVIEW.md`、`h9/check_format.py`、`h9/SEALED.json` | 題目與封存 |
| `run_h9.py` | live 與 menu 讀取的 runner（上限、指紋） |
| `live/`、`round-*.json`、`jobs-*.json`、`finished-*.json`、`menu-h9.json` | 錄製與執行紀錄 |
| `score_h9.py`、`score-h9.json`、`score-h9.txt` | 離線計算與計分 |
| `RESULTS-H9.md` | 結果 |

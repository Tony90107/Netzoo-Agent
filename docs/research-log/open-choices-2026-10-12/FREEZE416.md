# Log 416 事前凍結：使用者沒決定的結果選擇，要問，不拒絕也不替他選（2026-10-12，執行前寫下）

來源：可行性評測 2026-10-12（`outputs/feasibility-eval-2026-10-12/ISSUES_AND_IMPROVEMENTS.zh-TW.md`）的 G2。
使用者決定（2026-10-12）：先修 G8（已完成，5b468c1），再做 G2；中文題照舊不修。

## 根因（已看過的英文題）

- **F39、F37**：
  - 「have not decided」命中 `explicit_research_choice`，請求先送 framing。
  - 模型回 `unclear_goal`，但沒有列出任何選項。程式把這當成「驗證失敗」，直接結束，路由不再進行。
  - 結果：F39 沒走到 STRING 下載，被判全缺口；F37 回覆「Please state each hypothesis」。
- **F43**：
  - 能力檢查把「activity 還是 wiring」記成背景（has），只剩「Help me choose」一句當需求。
  - 這一句沒有 workflow 給得出，請求被判全缺口，回覆「No registered workflow produces this」。
- **共同缺口**：使用者明說「還沒決定、列出幾個選項」，在任何契約裡都沒有欄位。

## 候選與基準

- 基準 `base`：`5b468c1`（上線版，含 G8 修正），`.worktrees/netzoo-oc-base`。
- 候選 `cand`：`3ceef22`，`.worktrees/netzoo-oc-cand`。改動如下：
  - **B**：framing 回 `unclear_goal` 且沒列任何選項時，不再當驗證失敗，請求照常路由。
  - **UD**：能力檢查的每一句加 `open_choices`。使用者說還沒決定的選擇，每個選項是一個獨立的 ask，照常對照 sheet。
    - 至少兩個選項的引文都在請求裡找到，才組成一個選擇。
    - 選項全是註冊 workflow 名稱時，視為方法問題，跳過（預量測 C1）。
  - **觸發條件**：檢查已確認，且選擇中至少一個選項有 workflow 給得出，且各選項導向不同的 workflow。
  - **觸發後**：
    - 路由清掉選定與推薦，只把各選項的 workflow 列為候選。
    - 回覆列出每個選項各得到什麼，問一個問題（reply kind `open_choice`，clarification 卡）。
- 單元測試全過；新增 `tests/test_open_choices.py` 7 個測試。

## 預先量測（凍結前已做，全是看過或為此設計的題，不是 held-out）

`premeasure416.py` → `premeasure416a.json`，只跑檢查呼叫（nemotron），每題 2 次：
- 目標題（F37、F39、F43、D1–D3）：11/11 填出正確選項，另有 1 次解析失敗。
- 對照題（C2–C5）：0 次誤觸發。
- C1（「LIONESS-PANDA 還是 BONOBO？」）觸發 1/1。之後加了「選項是 workflow 名稱就跳過」的規則。
- C6（「兩層合併的網路還是各層分開比較合適？」）觸發 2/2。這題本來就在問選哪種結果，視為合理觸發。
- 解析失敗 3/24。

已看過的英文題實跑（cand）：
- F37：列出兩個選項，不選 workflow。
- F43：列出兩個選項，不選 workflow。殘留問題：「network wiring」對到 PANDA，不是 LIONESS-PANDA。
- F39：只問 STRING 的 network type。

## 題組

`heldout416.json`，28 題，執行前從未跑過，只有英文：

| 族 | 題數 | 內容 |
|---|---:|---|
| OC | 8 | 沒決定的結果選擇，每個選項都做得到，且導向不同 workflow |
| ON | 3 | 同上，但其中一個選項做不到 |
| OP | 3 | 同一個 workflow 內的選擇（參數，或同一個 workflow 的兩種結果） |
| OR | 3 | 以「run／plan」措辭提出的未決選擇；只報告，不設判定（候選只處理非執行路徑） |
| XC | 6 | 已決定的請求，但含不確定或假設字眼，講的是別的事 |
| XM | 2 | 直接點名 workflow 的方法問題 |
| XD | 3 | 單純已決定的請求 |

## 回合

`o16`：兩臂交錯執行，每題 2 次，共 112 個 session，執行 `run_heldout416.py o16 2`。

## 判讀

全部用程式判讀，見 `analyze416.py`，不用標註者：
- **offered**：回覆呈現的 workflow，包括 matched、tie、推薦、advice 或已規劃的 run。
- **selected**：替使用者決定了 workflow，包括已規劃或執行的 run、唯一 exact match、推薦或 advice。
- **refused**：全缺口；或回覆說「No registered workflow produces」，且沒有提供任何 workflow。
- **named**：每個選項都在回覆裡被點名。
- **asked**：回覆含問號。
- **目標成功**：not refused、not selected、named 且 asked。

我會讀過兩臂全部 OC、ON 回覆，確認程式判讀和實際內容一致；不一致的逐一記在 RESULTS。

## 判定

| 判定 | 條件 |
|---|---|
| V1 | 112 個 session 齊全；每臂空回覆或缺檔 ≤ 4 |
| **G0（不能傷到做得到的請求）** | 對照題（XC＋XM＋XD，每臂 22 個 session）中 answered（有提供 workflow 且未拒絕）：cand ≥ base；且 cand 的 `open_choice` 誤觸發 ≤ 1 |
| G1 | 目標題（OC＋ON，每臂 22 個 session）成功數：cand ≥ base ＋ 8，且 cand ≥ 15 |
| G2 | 目標題的 selected 與 refused：cand 都 ≤ base |
| G3 | OP 的 refused：cand ≤ base；OP1 問 STRING network type 的次數：cand ≥ base |

全部成立才保留，否則撤回。OR 只報告。

## 補充：盲測題組（2026-10-12，o16 進行中寫下，任何盲測回合之前）

使用者要求（2026-10-12）：修正不能只針對特定題目改進。heldout416 是我在知道修法之後寫的，可能偏向這個機制。所以另外加一組盲測題：
- `heldout416b.json`，30 題，由獨立子代理撰寫。
- 撰寫者只拿到 G2 的問題定義和各 workflow 的產出說明，沒看過程式碼、這個候選或 heldout416。
- 我讀過全部題目，一題都沒改。
- B06（「either is fine by me, you pick and start」）等於把選擇權交出來，替使用者選也說得通。依出題者的預期保留 ASK，但結果另外註記。

| 族 | 題數 | 預期 |
|---|---:|---|
| OPEN | 8 | ASK：使用者列出結果選項，各選項導向不同 workflow |
| VAGUE | 3 | ASK：目標本身沒說 |
| UNKNOWN_INPUT | 5 | ASK：結果明確，但決定 workflow 的資料性質使用者不知道 |
| RUN_OPEN | 4 | ASK：以 run 措辭提出，帶著未決選擇或未知性質 |
| DECIDED | 7 | ANSWER：其中 4 題以上帶有無關的不確定或假設字眼 |
| IMPOSSIBLE | 3 | REFUSE |

回合 `b16`：兩臂交錯，每題 2 次，共 120 個 session，執行 `run_heldout416b.py b16 2`，在 o16 結束後才跑。判讀用 `analyze416b.py`，判讀定義同 `analyze416.py`。

| 判定 | 條件 |
|---|---|
| GB0（不傷做得到與做不到的判斷） | DECIDED answered：cand ≥ base；IMPOSSIBLE 說明做不到：cand ≥ base；兩族的 `open_choice` 觸發合計 ≤ 1 |
| GB1（泛化） | OPEN 成功數（16 個 session）：cand ≥ base ＋ 5 |

VAGUE、UNKNOWN_INPUT、RUN_OPEN 只報告。這三族不在這個候選的範圍內，用來量測 G2 還剩多少沒做。

Log 416 要保留，o16 的判定（V1、G0–G3）和 GB0、GB1 必須全部成立。

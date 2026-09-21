# NetZoo Agent 桌面介面：實作報告

日期：2026-09-21
範圍：commit `1732c41`（不含）到 `a22b636`，15 個 commit
相關文件：[DESKTOP_UI_ARCHITECTURE.md](DESKTOP_UI_ARCHITECTURE.md)（設計與決策）

---

## 0. 這份報告哪些能放進論文

先說結論，免得你花時間在不適合的段落上。

**可以放（§4、§5）**：routing 契約矛盾的診斷，以及它的對照實驗。那是一個方法論上完整的
負面結果——包含「沒有對照組會得到相反結論」這件事本身。以及語料覆蓋缺口的量測。這兩者
和你論文的證據契約主題直接相關。

**不建議放（§1–§3、§6）**：介面架構、工程缺陷、測試紀律。這些是軟體工程，不是研究貢獻。
放進論文會稀釋主線。如果需要提及，一句「另實作了桌面介面，架構見附錄」就夠了。

**可能可以放進「系統與方法」章節的一小段（§2.1）**：「同一個狀態機、兩個 driver」這個
結構選擇，因為它是「終端與 GUI 的行為等價」這個性質的來源，而那個性質對可重現性有意義。

---

## 1. 做了什麼

把原本只有終端介面的 NetZoo agent，加上一個桌面應用程式（macOS `.app`），分六個里程碑：

| 里程碑 | 內容 |
| --- | --- |
| M0 | 把對話狀態機從終端 I/O 抽離 |
| M1 | FastAPI daemon，一個 session 一個行程 |
| M2 | Tauri 殼層、Docker 生命週期、三欄視窗 |
| M3 | 對話、Plan 審核、兩段執行確認 |
| M4 | 推理時間軸、契約型別生成 |
| M5 | PathMapper、結果檢視、session 歷史與設定 |

### 量化

| 項目 | 數值 |
| --- | --- |
| 變更檔案 | 90 |
| 新增程式碼（不含測試、不含生成檔） | engine 928 · daemon 1,891 · UI 2,704 · Rust 428 行 |
| 新增測試 | Python 109 · TypeScript 41 · Rust 4 |
| 專案測試通過數 | 1,646 → 1,755（+109） |
| 既有失敗集合 | **83（本機）/ 107（容器），15 個 commit 全程逐行不變** |
| CLI golden transcript | 13 個情境，M0 之後從未改變一個位元組 |
| 冷啟動（開啟 app 到可輸入） | 2.5–3.3 秒 |

「失敗集合逐行不變」是本次工作採用的驗收標準，理由見 §6.1。

---

## 2. 架構

```
Tauri 殼（Rust）── 視窗、docker 生命週期、每次啟動新鑄 token
      │ IPC
WebView（React + TS）── 三欄：Sessions │ Conversation │ Plan/Timeline/Outputs
      │ WebSocket（loopback）
Agent Daemon（FastAPI）── SessionSupervisor
      │ JSON lines over Pipe
Session Worker（每 session 一個行程）── ConversationMachine
      │
既有的 LangGraph 10 節點
```

### 2.1 同一個狀態機，兩個 driver

原本 `cli/conversation.py` 的 `run_conversation()` 有 711 行，在同一個迴圈裡同時做四件事：
決定該問什麼、讀終端、呼叫 graph、更新 12 個區域變數當狀態。

GUI 無法重用它，而**複製一份等於把狀態機分叉成兩套**。所以第一步（M0）是純機械式地把它
抽成 `ConversationMachine`，終端與視窗各自成為它的 adapter：

```
                 ConversationMachine
                   ↙            ↘
      cli/conversation.py     server/driver.py
        （76 行，終端）          （socket）
```

這個選擇帶來一個可驗證的性質：**兩個介面的狀態轉移必然相同，因為它們是同一段程式碼**。
UI 不從訊息或計畫推導「現在能輸入什麼」，只渲染 daemon 送來的 `view`。

抽離的驗收條件刻意訂得很硬：既有測試失敗集合逐行相同、13 個 golden transcript
（同時比對 stdout **與傳給 `input_func` 的提示字串**）逐字元相同、使用者可見字串以 AST
比對確認零遺失。三項全部通過。

### 2.2 一個 session 一個行程

`runtime.MUTABLE_RUNTIME_NAMES` 有 14 個成員全是行程全域值，包含 `EXECUTE_TOOLS` 與
`TEST_DATA_MODE`。多個 session 共用行程會讓「在一個視窗核准執行」把執行權交給所有視窗。
把它們改成 per-invocation 參數會觸及 graph 的每個節點。

選擇用行程隔離換取零語意變更，並用**真 spawn 行程**驗證：A session 開啟 `EXECUTE_TOOLS`
的同一瞬間，斷言 B 仍為 `False`。

### 2.3 執行授權

終端問 `[y/N]` 然後相信下一行輸入。UI 離它看到的那份計畫有一個網路來回的距離，所以核准
必須指名計畫：`approve_execution` 帶 plan 的 SHA-256，對不上就拒絕。在執行確認提示上送
一般 answer 會被拒絕。兩段確認（先預覽、再核准）在兩個 driver 上都成立，UI 沒有任何
「一鍵從目標到執行」的路徑。

---

## 3. 整合驗證

完整 PANDA 流程在原生視窗實跑，七個步驟：

1. 送出「Run PANDA on the toy dataset in data/official-toy」
2. Plan Card：**PANDA / Needs input**，evidence ledger 帶實際路徑；輸入驗證失敗，
   agent 的理由完整呈現（gene symbols 需要 taxon）
3. 切換到 Synthetic Test 模式
4. 修正輸入 → **Needs confirmation**，evidence 改標「you gave it」
5. 確認 → **Ready**，2 個步驟與完整 dry-run 指令
6. 兩段核准
7. 執行完成 → `outputs/demo/ToyExpressionData-panda.tsv`（3,113,777 bytes），
   時間軸 123 個事件

時間軸的驗收條件是「UI 顯示的事件數等於 `.netzoo/traces/` 的筆數」。第一次實跑是
**30 對 31**，缺的那一筆是 `run.paused`（原因見 §6.2）。修正後 **26 對 26**。

---

## 4. Routing 契約矛盾（適合論文）

### 4.1 觀察

在測試桌面介面時，prompt「Explain the difference between PANDA and PUMA. Do not run
anything.」穩定失敗，回覆「Semantic routing output failed validation, so no workflow was
selected. (ValueError)」。同一個 prompt 在當時的 HEAD 與更早的 commit 都失敗，不是新引入的。

### 4.2 診斷

從 trace 取出被拒絕的 interpretation，模型的輸出是：

```json
{
  "request_mode": "guidance",
  "outcome": {
    "operation": "explain",
    "artifact_type": "unknown",
    "granularity": "not_applicable"
  },
  "evidence": [{
    "dimension": "operation", "source": "explicit", "value": "explain",
    "text_span": "Explain the difference between PANDA and PUMA."
  }]
}
```

這完全符合契約欄位描述的要求——`operation` 的 description 明寫
「**Required scientific operation, even for guidance requests.** Infer it from the original
scientific goal, not a tool name or request_mode」。

驗證器仍然以 `hypothesis[0].inconsistent_not_applicable_outcome` 拒絕，重試一次、同樣問題、
然後 `ValueError`。

離線把變因拆開重現：

| outcome 形狀 | 通過？ |
| --- | --- |
| `operation=explain` + 有明確 span 的 evidence | ✗ |
| `operation=unknown` + 同一份 evidence | ✗（`reconcile_outcome_with_grounded_evidence` 會把 `explain` 寫回去） |
| `operation=explain` + 無 evidence | ✗（兩條 issue） |
| **`operation=unknown` + 完全沒有 evidence** | ✓ 唯一能過的形狀 |

也就是說：**一個概念性問題要通過驗證，模型必須丟掉一個有明確文字依據的正確讀法、
宣稱自己什麼都沒理解。**

根因在 `outcome_validation.py` 的 `_is_not_applicable()` 要求 `operation == "unknown"`。

更關鍵的是**兩層契約互相矛盾**：`routing/outcome_matching.py` 的 `_match_semantic_request`
在 guidance 模式下**本來就會把 `operation` 抹成 unknown**（註解寫「explanatory wording is not
itself a workflow operation」）。所以驗證器擋掉的那個欄位，下游根本不會用到。

### 4.3 修正

`_is_not_applicable` 接受 `{"unknown", "explain"}`：解釋一個方法本來就不產生 artifact，
所以它和「unknown artifact + not_applicable granularity」是一致而非矛盾。

會產生東西的 operation（`infer`/`analyze` 等）配 `not_applicable` 仍然照抓；宣稱
not_applicable 卻同時列出 mirna regulator 也照抓——那兩種正是既有測試釘住的形狀，
所以**一個測試斷言都沒有改**。

### 4.4 對照實驗（這一節是重點）

**如果只做天真的比較，會得到完全錯誤的結論。**

修正後跑一輪（round 21），對上研究日誌裡最近的舊碼輪次：

| | pass_rate | route_pass_rate |
| --- | --- | --- |
| round18（舊碼） | 39.4% | 55.6% |
| round19（舊碼） | 38.4% | 57.6% |
| round20（舊碼） | 36.4% | 52.5% |
| round21（修正後） | **45.5%** | **73.7%** |

看起來是 +9 / +21 點的大幅改善。但 round20 之後，專案本身的 `Semantic recognition` 與
後續 commit 在 routing/interpretation/graph 加了 **957 行**。round21 量到的是
「那些工作 + 這一行修改」，對照的卻是早於那些工作的基準。

於是建立**匹配對照組**：同一份程式碼基礎、同一份語料、同一個模型，唯一差別是
`_NO_RESULT_OPERATIONS` 那一個常數。各跑兩輪：

| | pass_rate | route_pass_rate | semantic_pass_rate |
| --- | --- | --- | --- |
| treatment round21 | 45.5% | 73.7% | 49.5% |
| treatment round22 | 46.5% | 71.7% | 52.5% |
| control round23 | 45.5% | 75.8% | 50.5% |
| control round24 | 46.5% | 72.7% | 51.5% |
| **treatment 平均** | **46.0%** | 72.7% | 51.0% |
| **control 平均** | **46.0%** | 74.2% | 51.0% |
| **差** | **+0.0** | −1.5 | **+0.0** |

四輪的 `corpus_sha256` 與 `prompt_schema_sha256` 完全相同（已驗證），每輪 33 cases × 3
repeats = 99 trials。同組跨輪差距 1–3 點，所以 route 的 −1.5 在噪音內。

**結論：這個修正對這個語料沒有可量測的效果。** 那 +9 / +21 點完全來自專案既有的
routing 工作，不是這一行。

### 4.5 為什麼量不到：語料覆蓋缺口

99 個 trial 裡 `operation=explain` 只有 **3 個**，而實際踩到的那種純概念題**一個都沒有**。
`inconsistent_not_applicable_outcome` 命中的 5–7 個 trial 主要是另一種形狀——「宣稱
not_applicable 卻同時列出 mirna regulator」那種真矛盾，那些本來就該被擋。

研究日誌記載這個 issue「28 次出現、0% 通過」，據此推估的「約 +9 點空間」是錯的：
那 28 次裡絕大多數不是 explain 形狀。

**這是一個量測有效性的問題，不是模型能力的問題。** 這一類失敗目前在指標上根本量不到。

### 4.6 決定

保留修正，但不當成效能改善：
- 它修的是一個可重現的、使用者可見的失敗（實跑從 `Semantic routing unavailable` 變成
  真的回答）
- 它消除了一個真實的契約矛盾
- 代價為零：pass_rate 與 semantic 各 0.0 點，兩個環境的失敗集合逐行不變

---

## 5. 對論文而言可引用的三點

1. **契約的兩層可以互相矛盾而不被任何測試發現。** 驗證器拒絕一個欄位，而下游本來就會
   抹掉它。發現它的不是測試，是實際使用。

2. **沒有匹配對照組的前後比較會得到相反的結論。** 這裡的天真比較顯示 +9 點，對照實驗
   顯示 0.0 點。差異全部來自基準線期間累積的其他變更。

3. **語料決定了什麼問題「存在」。** 99 個 trial 只有 3 個 explain、0 個純概念題，所以這
   一類失敗在指標上是隱形的——即使它在實際使用中穩定重現。

---

## 6. 工程紀錄（不建議放進論文）

### 6.1 驗收標準：為什麼不是「測試全綠」

專案測試從來不是全綠的（`HANDOFF.md` 記載基準約 93 個既有失敗）。因此採用
**失敗集合相等**作為驗收標準：不是數量相同，而是同一批 node id、同樣的失敗訊息。

同時發現**只驗本機等於沒驗**：`test_workflow_continuation.py`（最重壓 `run_conversation`
的檔案）在本機因缺 langchain 整檔 skip，只有容器會真的跑它。因此每次變更都在兩個環境
各驗一次。15 個 commit 全程：本機 83、容器 107，逐行不變。

### 6.2 只有實際執行才會發現的缺陷

七個，全部讀程式碼看不出來：

| 缺陷 | 後果 |
| --- | --- |
| 沒有 macOS 應用選單 | Cmd-V 完全失效，而貼檔案路徑是回答這個 agent 的主要方式 |
| `/health` 不需 token 就重用殘留 daemon | app 被強制關閉後再開，每個請求 401 |
| Interrupt 送 WebSocket 訊息 | worker 執行中不讀 channel，訊息躺到下一個提示才被讀到，**把 session 悄悄結束**；分析照跑完 |
| Finder 啟動時 PATH 不含 `/usr/local/bin` | 裝好 Docker 的使用者被告知「請安裝 Docker」 |
| clarification 顯示「Needs an input」 | preflight 失敗時問不出欄位名，且表單模式錯誤 |
| agent 的提問文字被 UI 丟棄 | 使用者看不到「為什麼被拒絕」 |
| 廣播包在 recorder 而非 store | `pause_run` 直接呼叫 store，事件從未送達；時間軸少一筆 |

其中三個（Interrupt、Finder PATH、廣播缺漏）會讓功能在真實使用中失效或誤導，而且都是
先前「看起來沒問題」的程式碼。

### 6.3 契約型別生成

`scripts/generate_ui_types.py` 走訪 Pydantic 模型產出 TypeScript
（不走 JSON Schema，因為 `RequestedOutcome` 的 schema hook 會展開成每個 artifact type
一個條件分支）。`tests/test_ui_contract_sync.py` 在檔案過期時失敗——已實測：往契約加一個
欄位會讓它失敗。

導入當下立刻回本：編譯器指出手寫的 `WorkflowPlan` 少了 4 個欄位、`NextTurnPrompt` 少了
4 個。那些漂移早就存在。

### 6.4 儲存

| | 數量 | 邏輯大小 | 保留 |
| --- | --- | --- | --- |
| sessions | 401 檔 | 3.6 MB | 30 天（暫停中的不刪），180 天硬性 |
| traces | 1,739 runs | 17.3 MB | 30 天（僅已封存） |

磁碟實際佔用 28 MB，差額主要是 1,739 個小目錄的 block 碎片而非內容。

trace 保留期從 90 天改為 30 天，理由是與 session 保留期一致，讓一個 run 的 trace 和它的
checkpoint 一起過期而不是留下孤兒。原設定從未真正刪過任何東西（沒有任何 run 超過 90 天）。

**保留期本身無法限制成長**：1,739 個 run 裡有 350 個未封存（中斷/暫停），而清理只移除已
封存的。這是對的——一個 run 不該因為被中斷就失去它的證據——但代表未封存的數量會單調增加。
設定頁現在把這個數字顯示在總數旁邊。

---

## 7. 已知限制

| 項目 | 狀態 |
| --- | --- |
| 打包後的 `.app` 找專案路徑 | 從執行檔往上找 `docker-compose.yml`；安裝到 `/Applications` 需設 `NETZOO_PROJECT_ROOT` |
| 輸入檔瀏覽 | 只能瀏覽 `outputs/`；輸入路徑目前手動輸入，原生檔案選擇器未做 |
| 未封存 trace | 永不清理，數量單調增加 |
| 語料概念題 | 99 trial 中 0 個純概念題（§4.5） |
| 時間軸重播 | 未做（讀舊 run 的 trace 逐步播放） |
| 設定頁 | 唯讀，已定案；修改限制需改容器啟動環境 |

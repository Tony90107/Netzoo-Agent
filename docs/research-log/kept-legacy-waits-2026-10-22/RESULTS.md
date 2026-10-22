# 保留舊的待問事實：fact agent 沒問任何問題時不撤除等待

2026-10-22。起點 `ba7d828d`（分支 `closed-menu-phase0`），修改在分支 `keep-legacy-waits`。模型呼叫 0 次，費用 $0。

## 改了什麼

舊行為（phase 2 起）：fact agent 只要成功回傳（`status == "checked"`），`without_legacy_waits` 就把舊維度的
`needs_fact` 全部撤除。即使 agent 一個問題都沒留下，回合也會往 DO 走。

新規則（使用者決定）：**agent 沒提出任何問題時，舊的待問事實保留。**「沒提出問題」的定義：

- 沒有 `open_results`（R7 的目標追問）；
- `decide_core` 會問的題目是空的（`agent_questions`：程式判定的數量題，加上 agent 保留、且不屬於數量題的事實）。

保留後的流程，與 agent 沒有執行時完全相同：router 的 `waiting_decision` 暫停選擇與執行，
`decide_core` 回 `ASK / needs_fact`，回覆由 `needed_fact_reply` 產生。agent 有提問時，行為不變。

程式位置：

- `graph/fact_check_call.py`：`waits_after_agent`，由 `apply_fact_check` 呼叫。
- `interpretation/core_decision.py`：抽出 `agent_questions`。agent 沒提問時，改走舊的 `needs_fact` 分支，
  並在 evidence 記錄 `legacy_kept`。原本的 shadow 分支已不會被執行到，所以刪除。
- `false-accept-replay-2026-10-21/replay_full.py`：步驟 8 改用 `waits_after_agent`（較舊的程式仍無條件撤除），
  並把 R4 stated-setting 篩選移到撤除判斷之前。這和 live 的順序一致：R4 本來就在 `kept_facts` 裡。

## 離線 replay（ROUND-13 harness，B2）

舊程式用 `--scripts .worktrees/netzoo-closed-menu/scripts`（`ba7d828d`），新程式用本分支。兩者都用本分支的 `replay_full.py`。

| | 舊 | 新 |
|---|---|---|
| 重放讀取 | 1,171 | 1,171 |
| 有金標的 757 份中判對 | 610 | **613** |
| 改變的判定 | — | 4 |
| 對→錯 | — | **0** |

改變的 4 份全部是 DO → ASK/needs_fact，而且題目的金標都是 ASK：

| session | 舊 | 新 | 追問內容（舊維度） |
|---|---|---|---|
| cj-p2-C11-1 | DO/run | ASK | one network per diagnostic group 或 one network per donor |
| cj-p4c-C11-1 | DO/run_held | ASK | one result for all samples together 或 one per sample |
| cj-g4o1-C31-1 | DO/results_given | ASK | signed effects for each biopsy separately 或 one set |
| hb-h2hyb-J19-1 | DO/results_given | ASK | one result for all samples together 或 one per sample |

J19 屬於 h2 hybrid 臂，harness 沒有逐 session 的金標。題目金標是 `class: ask`，
理由是「cohort 網路屬 DRAGON，每個 tumour 一張屬 LIONESS-DRAGON」，所以新的追問正好問到決定性事實。

- h5 的 94 份讀取：0 份改變。
- 最初在錄製呼叫中數到 6 份（`count_lifted.py`）。其中 C43 ×2 與 C44 現行程式已經會問（count_fact／fact_agent），
  所以不受這次修改影響。

## 測試

- `tests/test_fact_check.py`：原本的 `test_when_the_agent_ran_the_fixed_dimensions_are_shadow` 要求
  「agent 沒提問也撤除」，已改寫成兩個方向：
  - agent 有提問時，舊維度是 shadow；
  - agent 沒提問時，舊維度保留，回覆是 `needs_fact`，而且不選 workflow、不執行。
- 完整 `tests/`：4,923 項通過、51 項略過。
- 沒有跑 live：這次只改模型讀取之後的程式判定，沒有改變任何模型讀取。依 lean-testing 規則，
  離線 replay 加單元測試已足夠；回覆路徑和「agent 沒執行」時相同，並已在測試中渲染確認。

## 限制

- 改變的 3 份有逐 session 金標的讀取，都在反覆調整過的 56 題（C11、C31）。J19 是 h2 的題目。新題的效果仍未知。
- 觸發條件很少見：1,171 份讀取中只有 4 份。這次修改是補一個語意漏洞（「沒問」不等於「已解決」），
  不是提高整體分數的主要來源。

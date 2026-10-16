# 第 3 階段盤點：分類階段的判定改寫點（spec 第 7 節）

方法：在 `graph/`、`interpretation/`、`routing/` 中，找出所有把 `action` 改成 `no_tool`、把 `should_execute` 設為 False、改寫 `capability_match_status`，或清空 `matched_actions` 的地方（2026-10-16，`core-decision-phase0` 分支）。

## 改寫點與第 3 階段之後的角色

| 模組 / 函式 | 改寫什麼 | 第 3 階段之後 |
|---|---|---|
| `interpretation/assembly.assemble_task_decision` | 從語意讀取與 intent 組出初始的 action 與 match status | 證據：`decide_core` 讀取最終結果 |
| `interpretation/repair.repair_router_decision`（6 處）、`_lioness_mode_plan`、`_ready_named_decision` | 修補路由輸出（LIONESS 模式、點名的 workflow） | 證據 |
| `routing/outcome_matching.apply_outcome_match` | registry 比對後清掉不符合的候選 | 證據 |
| `routing/capability.enforce_capability_gate`、`apply_input_preflight_intent` | 能力閘、輸入預檢把 run 改成 no_tool 或檢查檔案 | 證據；run 仍受執行閘限制 |
| `routing/authorization.enforce_operation_authorization` | 使用者禁止的操作把 run 改成 no_tool | 證據；run 仍受執行閘限制 |
| `interpretation/checked_match.checked_match` | 檢查後重新規劃，換成檢查認可的 workflow | 證據 |
| `interpretation/unmapped_routes.without_unmapped_candidates` | `unknown` 讀取下清空候選 | 證據 |
| `interpretation/needed_facts.waiting_decision` | 舊的 11 種 dimension 追問時，什麼都不選 | 只在 fact agent 沒有執行時作用（第 2 階段）；結果同樣進入 `decide_core` |
| `interpretation/run_hold.hold_run` | run 沒被核准時暫停 | 證據（`decide_core` 的 `run_held_*` 依據） |
| `graph/router_invocation._on_run_verdict`（2 處）、`_with_capability_check`（3 處，全缺口時清空候選）、`_route_request`（語意失敗時） | run 判決、全缺口、路由失敗 | 證據（UNCHECKED、DECLINE 的依據） |
| `interpretation/core_decision.with_core` | CLARIFY 與 fact agent 的 ASK 時，什麼都不選、不跑 | 依 core 判定執行（唯一由判定本身改寫的地方） |
| `interpretation/research_choices.render_research_choices` | 回覆層讀取，不改判定 | 只在判定為 DO 時可能被用到 |

## 收斂方式：在兩個出口強制，不是逐點改寫

- **回覆**：`respond` 的第一步是 `core_views.core_view`。CLARIFY、ASK、DECLINE、UNCHECKED 都只從這一個入口回覆，內容只依 `CoreDecision`（加上它記錄的檢查列）渲染。DO 才交給既有的 renderer。
- 兩個正則 boundary（`render_cobra_expression_boundary`、`render_unsupported_algorithm_boundary`）不再自己回覆，改成 `decide_core` 判 DECLINE 的證據（`_boundary`）。
- **執行**：Plan Evaluator 與 executor 共用 `run_approval_failures`，現在另外要求 `core.run_allowed`。
- **量測**：每個回覆的 `core.view` 事件都記錄 `mismatch`，表示回覆的 renderer 不在該判定允許的清單內（`core_views.ALLOWED`）。

| 錄製回合 | 判定與回覆路徑不一致 |
|---|---|
| p1 | 8 |
| p2 | 4 |
| p2 用第 3 階段程式離線重放（`replay_p3.py`） | **0** |

重放時，唯一判定改變的 C19 是重放的限制：錄製的判定已經被 `with_core` 清空，重算時會看成路由失敗。正式流程中，`decide_core` 讀的是清空之前的判定。

## 與 spec 字面的差異（待使用者確認）

spec 第 7 節寫的是把上表每個改寫點「逐一改成只寫證據欄位」。這次沒有逐點改寫（共約 25 處，分佈在 11 個模組，牽動路由語意），而是在回覆與執行兩個出口強制執行判定。

結果是：上游改寫只能成為 `decide_core` 的輸入，無法自己產生回覆或 run，而且有程式量測。若要照字面逐點改寫，需要另開工作；這次的做法也已記入 spec 的變更紀錄。

## 取捨

被暫停的 run 如果判為 DECLINE（例如 C13 的 OTTER lam=1.5），現在由 DECLINE 入口回覆。回覆仍會說明「OTTER 本身可以用預設設定跑」，但卡片上不再有「直接跑」的按鈕。

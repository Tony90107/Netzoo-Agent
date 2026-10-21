# 拆分 Codex 2026-10-21 修復：保留結構性部分（Claude）

依使用者指示，拆分 Codex 在 `closed-menu-phase0` 工作樹的未提交修改。拆分在獨立的工作樹 `.worktrees/netzoo-codex-split`（分支 `codex-split`，起點 `56d3bc84`）進行。Codex 的完整狀態備份在 `tmp/codex-2026-10-21-repairs-backup/`（`tracked.patch` 和 `untracked.tgz`）。本輪沒有呼叫模型。

## 保留

| 部分 | 檔案 | 說明 |
|---|---|---|
| 檢查預留預算，失敗重試一次 | `graph/required_check_budget.py`（新增）、`capability_check_call.py`、`fact_check_call.py`、`data_facts_call.py`、`study_purpose_call.py`、`router_invocation.py` | 原封保留 Codex 的版本，只拿掉讀題提示新增的那段文字 |
| fact agent 沒跑完就不當作可做 | `decision_guards.unchecked_fact_quotes`、`core_decision`（UNCHECKED `fact_check_incomplete`） | 原封保留 |
| 設定值解讀不出就問 | `workflow_conditions.setting_unresolved`、`method_conditions.unresolved_settings`、`decision_guards.unresolved_setting_questions`、`core_decision`（ASK `setting_unresolved`） | **改寫成不用字詞清單**，只看三種情況：布林值讀不出是或否；數字給了一個以上；enum 點出一個以上的允許值。<br>另外新增 `control_boolean_value`：值的字詞裡出現這個設定自己名稱中的詞（例如 log_transformed 對「log2-transformed」、centered 對「centered per gene」、norm_patient 對「patient」），而且沒有否定詞，就算「是」。<br>這條取代 Codex 的前處理片語清單，避免 C40 被多問。 |
| 兩個方法給出不同結果時請使用者選 | `goal_evidence.method_choice`、`core_decision.goal_unclear` 和 `_clarify_need` | 拿掉命令動詞清單和「your call／whichever」清單。<br>改用結構條件：在本輪的子句裡，兩個註冊方法用 or 連接，而且兩者都在這一輪實際考慮的方法中（routing 挑出的方法，或 check 認可的方法）。<br>所以「Our inputs came from DRAGON or LIONESS-DRAGON… Run CONDOR」不會被當成選擇。 |
| 排除使用者否決過的方法 | `checked_match.py` | 原封保留 |
| 其他附帶的結構修正 | `workflow_conditions._tokens` | 小數不再被拆成布林的 0 或 1；只有一個數字才算一個值；設定的值優先在設定自己的字句內找 |

## 拿掉

- 讀題提示新增的那段文字，以及讀取的新欄位 `requirement_role`、`parent_quote`；
- 六個模組：`request_ownership`、`setting_evidence`（P20 的來源）、`source_assertions`、`input_role_evidence`、`recovered_input_contract`、`deterministic_refusal`；
- 以下字詞規則：「keep normalization」「sparsify at confidence」「trying … subtypes」、命令動詞、「your call」、表示不確定的字詞、表示沒有資料的字詞、前處理片語、whole-cohort 的 regex；
- fact agent R1 改用字詞比對的放寬；
- 沒有任何方法被認可時，用點名方法的設定產生拒絕理由的那段；
- 對應以上功能的測試，以及 `test_deterministic_refusal.py`、`test_judgment_requirement_repairs.py`。

## 驗證

- **全套測試**：4,889 通過、51 略過。
- **凍結重放**：1,009 份，基準是乾淨的 `3eb5a74f`，比較見 `replay-clean-vs-split.txt`。
  - 有金標的 741 份：**561 → 566**，7 個判定改變，全部是變對或變得較安全，沒有一份變錯。
  - 變對：C26、J06、H46、C10 ×2，都從 DECLINE 變成 CLARIFY。
  - 變得較安全：H34 從 DO 變成 ASK（金標是 DECLINE）；J17 從 DECLINE 變成 ASK（金標是 DO）。
  - 沒有金標的讀取沒有任何改變。
  - 作為對照，Codex 的完整版是 561 → 577，但有 2 份沒有金標的讀取變錯（P20、M38 smoke）。
- **P20**：判 DO，不再問 centered 是多少。
- **M38 smoke**：判 CLARIFY，和修改前一樣，不再是 Codex 版的 DO。
- **M38 h4main**：判 DO，和修改前一樣。Codex 版的 ASK 來自「trying … subtypes」的 regex，這次拿掉了。
- **換句話說測試**（`paraphrase-split.txt`，每題 1 個原句加 2 個改寫，共 21 句）：拆分版 8/21，修改前 4/21，Codex 版 14/21。
  - Codex 版：原句 7/7，改寫 7/14。
  - **拆分版對同一題的原句和改寫，幾乎都給出相同的判定**。唯一例外是 J17：原句「keep」會問，兩個改寫都判 DO。
  - 也就是說，這次的進步不依賴題目的原句。
  - 沒有修到的題（H18、H21、M25、H34 的 DECLINE）需要改讀取格式，例如區分「要做的分析」和「附屬說明」，並且要在新寫的盲測題上量。

## 尚未處理

- 共用工作樹 `closed-menu-phase0` 仍保留 Codex 的未提交修改。要把這個分支併進去，必須先撤掉那些未提交的檔案（已有備份）。這需要使用者同意。
- 沒有 live 測試。

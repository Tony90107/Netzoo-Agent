# Harness repair P0：凍結系統 91a8c2d9 的基準（2026-10-23）

計畫：[P0](../../superpowers/plans/2026-10-23-evidence-bound-harness-repair.md)。這一步沒有修改 agent，沒有呼叫任何模型，費用 **$0**。

## 版本與環境

| 項目 | 值 |
|---|---|
| 程式 | worktree `.worktrees/netzoo-harness-repair`，分支 `harness-repair`，起點 `netzoo-agent/main` `da39e8ac` |
| 與凍結系統的關係 | `git diff 91a8c2d9 da39e8ac -- scripts tests workflows AGENTS.md` 為空：程式即 `91a8c2d9` |
| Python | `/opt/anaconda3/bin/python` 3.12.4；pydantic 2.12.3；pytest 8.4.2 |
| Policy | `policy_version: 2`；`policy_hash` `cf89ad9eddd6cf458f3e06c101b10c2c762814fe62b9e36d4149dfcb7a53f9c1` |
| 模型設定（main tree `.env`，只列名稱） | routing／semantic／response：`openai/gpt-4o-mini`；capability：`openai/gpt-4o-mini-2024-07-18` |
| replay 讀到的 main tree | `dfbcbfd8`（`evidence-contract-grounding`），`docs/research-log` 無未提交改動 |

## 1. 完整測試

`/opt/anaconda3/bin/python -m pytest tests -q -rs`：**4,931 passed，51 skipped，0 failed**（142 秒）。與 10-22 紀錄相同。

略過的 51 項都有明確條件，與本計劃無關：

| 檔案 | 項數 | 原因 |
|---|---|---|
| `test_execution_numeric_reference.py` | 34 | 需 `NETZOO_RUN_DOCKER_TESTS=1` |
| `test_executor_argument_types.py` | 16 | 遠端 action 沒有本機工具 |
| `test_sambar_container.py` | 1 | 需 `NETZOO_RUN_DOCKER_TESTS=1` |

## 2. B2 replay 基準（`base.json`）

`harness.py run base.json`：重放 **1,340** 份錄製讀取（worktree 589、main tree 751），有金標的 **757** 份中判對 **613**，與 keep-legacy-waits 的紀錄相同。讀取數比 10-22 的 1,171 多，是因為 harness 也讀到之後新增的錄製（例如 h6）；有金標的集合沒有變。

- 3 份 T01（`judgment20261020*`，無金標）重放失敗：舊 schema 缺 `data_unit`。記為 incompatible，不算成功。
- 14 份含錄製沒有回答過的配對（unrecorded），依 replay 規則當成未回答處理。

757 份有金標讀取的判定分布（P1／P2 的門檻以此為準）：

| 類別 | 定義 | 份數 |
|---|---|---|
| 判對 | 與金標相同 | 613 |
| FA 誤承諾 | 金標 DECLINE → DO | 15 |
| FR 誤拒 | 金標 DO → DECLINE | 5 |
| MA 該問沒問 | 金標 ASK／CLARIFY → DO 或 DECLINE | 64（ASK→DO 21、ASK→DECLINE 1、CLARIFY→DECLINE 27、CLARIFY→DO 15） |
| 問錯種類 | ASK ↔ CLARIFY | 18 |
| 多問（成本） | 金標 DO／DECLINE → ASK 或 CLARIFY | 11 |
| UNCHECKED | — | 31 |

## 3. 理由基準（`replies-base.json`、`reasons-base.txt`）

ROUND-20 的 `replies.py` 在本 checkout 重放並產生回覆：有金標讀取中，說「做不到」（DECLINE，或 DO 中有不可做部分）的回覆共 **208** 份。

- 205 份的理由與 ROUND-20 相同，或沒有附任何理由：沿用 ROUND-20 的最終分類（模型初判加人工確認），沒附理由的由程式標為 `no_reason`。
- 3 份理由改變（H27、L44、L48）：我逐份對照金標理由判定，三份都是說對。數量少且全部人工確認，所以沒有跑模型初判（它判「說錯」本來就不可靠：43 份中只確認 14 份）。
- C44 ×2 已不再拒絕（現在是 ASK），所以從 209 份變成 208 份。

| 金標 | 份數 | 說錯 | 誤導 | 說對 | 屬實非主要 | 沒附理由 |
|---|---|---|---|---|---|---|
| 全部 | 208 | **2** | 6 | 103 | 30 | **67（32.2%）** |
| DECLINE | 157 | 0 | 6 | 103 | 28 | 20 |
| DO | 19 | 2 | 0 | 0 | 0 | 17 |
| CLARIFY | 30 | 0 | 0 | 0 | 2 | 28 |
| ASK | 2 | 0 | 0 | 0 | 0 | 2 |

- 說錯：C07 g4o1、g4o2（其實能做；PANDA 的 near miss 被當成做不到的理由）。
- 誤導：C08 ×2、C57 ×2、C47 g4o1、H40。
- 沒附理由的 67 份中，47 份的判斷本身就錯（金標 DO、CLARIFY、ASK）。P2 修好判斷後這些應該不再拒絕；其餘 20 份金標 DECLINE 的，需要第二層理由。

## 4. Fixtures（`tests/fixtures/harness_repair/`）

`fixtures.py run|record|check` 執行。錄製 fixture 複製了 6 份讀取（共 408K，已檢查沒有金鑰、email 或個人路徑），不再依賴 main tree。每個 fixture 的 `baseline`（`91a8c2d9` 實際行為）與 `expected`（spec 要求）分開存放。完整輸出見 `fixtures-base.txt`。

| ID | 案例 | 來源 | 91a8c2d9 的行為 | spec 要求 |
|---|---|---|---|---|
| F01 | A01 | J19（h2 hybrid） | agent 沒提問，舊的 scale 問題保留 → ASK／needs_fact | 相同（回歸） |
| F02 | A02、A04 | M06（h4） | agent 用別的字問同一件事（somatic／germline），舊問題整批解除 | 只有同一 fact key 才能引用解除，否則保留 |
| F03 | A02 | 合成 | agent 問 BONOBO，CONDOR 的網路種類問題被解除，該列直接算可做（等於假設 regulator-gene） | CONDOR 問題保留或排隊，使用者回答前不算可做 |
| F04 | A02、A05 | 合成 | 解除後沒有任何交付的列變成 `not_available` | 維持 unresolved，不能成為拒絕理由 |
| F05 | A03 | 合成 | 三題有效問題，第三題被 R6 丟掉 | 第三題排隊，不丟 |
| F06 | A05、A22 | C12 p0 | 沒點名結果 → 空 matching → DECLINE／full_gap，沒附理由（金標 CLARIFY） | CLARIFY；若仍拒絕要有第二層理由 |
| F07 | A06、A07、A22 | H40（h1） | GIRAFFE 的理由也貼在背景片語 “TF activities stabilised” 上；PPI 權重列沒附理由 | 背景不當需求；每個不可做項目都有理由 |
| F08 | A08、A22 | L21（h3） | 同一 run 整題 DECLINE；PPI 權重列沒附理由 | DO + partial，run_allowed=false（10-23 決定） |
| F09 | A21 | C07 g4o1 | 能做的請求，附上不相干的 PANDA near miss（說錯） | 不說無法核實綁定的理由 |

建 fixture 時的發現：

- **agent 的問題沒有 fact key。** 48 份「agent 有提問且有舊問題」的讀取中，36 份的舊問題在字面上對不到 agent 的問題，但人工看大多是同一件事換句話說（如 M06）。所以 P1 要逐條解除，必須先讓 agent 的問題帶上 fact key（spec 5.2 的 `fact_key`）；只比對字串無法分辨。
- **R6「超過兩題」在 1,340 份讀取中從未發生。** A03 目前只有合成案例。
- **沒有任何錄製的舊問題是「完全沒有交付」的。** F04 是程式路徑風險，不是已觀察到的錯誤。

## 5. 證據邊界

| 層 | P0 量到的 | 怎麼量 |
|---|---|---|
| appearance（使用者原文） | 不量 | 錄製中的原文 |
| reading（模型讀取） | 不量：沿用錄製 | 新 prompt／schema 需要 live |
| decision（程式判定） | 量 | B2 replay、synthetic fixtures |
| render（回覆文字與理由） | 量 | `replies.py`、`reasons_base.py` |
| execution | 不量 | P4 才處理 |

## 6. 重現

```bash
/opt/anaconda3/bin/python -m pytest tests -q -rs
/opt/anaconda3/bin/python docs/research-log/stability-round13-2026-10-21/harness.py run docs/research-log/harness-repair-2026-10-23/base.json
/opt/anaconda3/bin/python docs/research-log/stated-reasons-2026-10-21/replies.py docs/research-log/harness-repair-2026-10-23/replies-base.json
/opt/anaconda3/bin/python docs/research-log/harness-repair-2026-10-23/reasons_base.py docs/research-log/harness-repair-2026-10-23/replies-base.json docs/research-log/harness-repair-2026-10-23/changed-base.json
/opt/anaconda3/bin/python docs/research-log/harness-repair-2026-10-23/fixtures.py check
```

## 7. 限制

- `base.json` 的 751 份讀取來自 main tree（`dfbcbfd8`）。main tree 若改變，需在同一份程式重跑 `base.json` 再比較；fixtures 已複製所需讀取，不受影響。
- 理由基準只涵蓋有金標的 757 份讀取中說「做不到」的回覆，不含 h5／h6。
- 依 10-23 決定需重標的舊金標（J44、L21、H40、L13；a24b MX04／MX05）尚未重標，在 P2 處理。本基準用的是原金標。

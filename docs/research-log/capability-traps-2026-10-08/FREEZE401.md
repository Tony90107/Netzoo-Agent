# Log 401 事前凍結：mini 備援的發現只報告、不清空 routing；以模擬斷線評估（2026-10-10，執行前寫下）

## 候選

候選為 `efe3d02`，放在 `.worktrees/netzoo-cc-cand`。基準是上線版本 `856a2c7`，放在 `.worktrees/netzoo-trap-base`。

候選分兩部分：

1. **備援**（Log 400 的 B，未修改）：檢查呼叫或第二意見用自己的模型失敗時，改用 semantic 模型（gpt-4o-mini）。
2. **安全條件**（使用者 2026-10-10 選的 (a)）：檢查只有靠備援模型回答時（狀態 `fallback`），檢查標成 `provisional`：
   - 它找到的完全缺口不會清空 routing，也不會改成「unsupported」。
   - 理解段落中，做不到的行改寫成 "the backup check matched no registered workflow to this (not confirmed)"。
   - 段落最後加一句說明：一般的檢查沒有執行，以上各行未經確認，下面的方法也沒有因此被移除。
   - 卡片上的不可用列也用同樣的說法。

當自己的模型正常回答時，程式路徑和上線版本完全相同（單元測試 3452 passed）。

## 量測條件：模擬斷線

Log 400 已經顯示免費每日上限會在一輪中途用完，而這個候選只在那種時候才有作用。所以這一輪讓**兩臂都處在斷線狀態**：

- `OPENROUTER_CAPABILITY_MODEL=nvidia/netzoo-outage-simulation:free`：不存在的模型 ID，加進白名單，provider 每次都回錯誤。
- 基準：檢查無法執行，回覆會說 "could not be checked"，和 Log 400 額度用完時一樣。
- 候選：由 mini 接手，結果標成 provisional。

這一輪不使用 nemotron 額度。開發時試跑一題（splicing）確認可行：mini 接手、標成 provisional、routing 的選項保留。

**題組**：`heldout10.json`，共 35 題，凍結前從未跑過，與 Log 402 共用。每題 3 次，兩臂交錯，tag `o10`。標註規則與 Log 400 相同，由兩個獨立子代理各盲標一半。分析用 `analyze401.py o10`。

## 判定（全部成立才保留，否則撤回）

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤 ≤ 10（檢查呼叫的預期錯誤不算，只算記錄在 session 的 exception） |
| G1 | U+N 的 FAB＋HEDGE：候選 ≤ 基準 |
| G2 | C 的 FALSE_GAP：候選 ≤ 基準 |
| G3 | C 的 OK：候選 ≥ 基準 − 2 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 1，而且 P 的 FALSE_GAP：候選 ≤ 基準 |
| S1 | 候選 no_tool session 中，靠備援完成檢查的 ≥ 總數 − 5 |
| S3 | 候選中，被備援判出的缺口清空 routing 的 session = 0 |

over_credit 和 false_negative 這兩種逐行判斷，這一輪只報告、不設判定：基準在斷線時沒有理解段落，無從比較；而 provisional 的行不會改變提供哪些方法。

## 事前預測

- **G1 的風險**：做不到的題目在候選中會得到「未確認」的行，再加上 routing 的選項，有時是 "These all fit"。標註可能判成 HEDGE 或 FAB，所以候選不一定明顯比基準好，但不應該更差。
- **G2**：預期兩臂都是 0。安全條件就是為了這一點。

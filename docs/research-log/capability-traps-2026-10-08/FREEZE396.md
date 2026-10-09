# Log 396 事前凍結：第二意見也問「檢查曾點名其近似條目的 workflow」，並附上使用者資料；以 heldout6 加上「模擬 routing 失敗」評估（2026-10-09，執行前寫下）

## 候選

候選是 `713e253`，放在 `.worktrees/netzoo-cc-cand`，detached，工作區乾淨。它是在已上線版本 `a38356c` 上加兩個 commit：

1. **`7c7d1b3`**：完全缺口時，第二意見要問的 workflow，從「routing exact 的 workflow」擴大為「routing exact 的 workflow，加上檢查曾引用其近似條目的 workflow」。型別欄位仍然先行篩選；如果篩選後沒有任何配對，就不呼叫第二意見。
2. **`713e253`**：第二意見先列出使用者自己的資料，也就是檢查時被判為 context 的引文。

**來源**：TEST_PROMPTS r12 test9。routing 失敗後，「infer a gene regulatory network for a rare tissue」被判成缺口。開發時重放這一題的記錄 3/3 都修正了。

**開發探針**（只用已看過的題目，每題 2 次）：
- 不附資料時，「for a rare tissue」對 OTTER 為 0/2。
- 附上資料後為 2/2；PPI 社群對 CONDOR、TF 複合體對 OTTER 都維持 0/2。

## 基準、題組與設定

- **基準**：`b61f660`。
- **題組**：`heldout6.json`，共 35 題，凍結前一次都沒跑過：
  - NU1-8（完全做不到）
  - NN1-10（近似）
  - NP1-5（部分可做）
  - NC1-12（對照）
- **設計重點**：對照題刻意帶上像是在限定方法、其實是在描述使用者資料的限定詞，例如 rare tissue、pediatric、mouse model、organoids。
- **模型設定**：routing 用 gpt-4o-mini，檢查用 nemotron；這是已量測過的設定。

## 量測

**A. 完整回合**：每題 3 次，兩臂交錯；標註規則與 Log 394 相同，由兩個獨立子代理標註。

判定（與 Log 394 相同，分母依題數）：

| 判定 | 條件 |
|---|---|
| V1 | provider 錯誤 ≤ 10 |
| G1 | U+N 的 FAB+HEDGE：候選 ≤ 5，且 ≤ 基準 − 10 |
| G2 | C 的 FALSE_GAP：候選 = 0 |
| G3 | C 的 OK：候選 ≥ 基準 − 3 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 1 |
| G5 | 有 over_credit 行的 session ≤ 10 |
| G6 | C 中有 false_negative 行的 session ≤ 4 |
| S1 | 檢查沒成功 ≤ 10 |

**B. 模擬 routing 失敗**：用 `sim_routing_failure.py`，`CODE_ROOT` 指向候選。每題 2 次，只跑檢查和第二意見，而且 routing 沒有任何候選。完全不需人工標註，直接看 full_gap。

| 判定 | 條件 |
|---|---|
| SF1 | C（24 次）的完全缺口 = 0 |
| SF2 | U+N（36 次）的完全缺口 ≥ 32，也就是第二意見重新放行的情況 ≤ 4 |

## 事前預測

- **SF2 的風險**：NN6（從網路學 motif）、NN8（PANDA 精煉的 PPI 網路），模型可能會點名 PANDA 的近似條目，第二意見可能答「是」。
- **G2／SF1 的風險**：NC1、NC2、NC4、NC11 這幾題帶有限定詞。

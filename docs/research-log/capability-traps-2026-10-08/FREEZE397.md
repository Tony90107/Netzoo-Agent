# Log 397 事前凍結：白卷判定依型別欄位問第二意見；以 heldout7 加模擬 routing 失敗評估（2026-10-09，執行前寫下）

## 候選

候選為 `fb01338`，放在 `.worktrees/netzoo-cc-cand`，detached，乾淨。它包含兩部分：

1. Log 396 的兩項修改：第二意見也會問「被引用的近似條目所屬的 workflow」，並且附上使用者自己的資料。
2. 新增的一項：
   - 若某個 not_available 的結果，所有讀法都沒有點名任何條目（`blank`），就依它的型別欄位找出對應的 workflow，一併納入第二意見。
   - 只有具辨識度的欄位會指向 workflow：
     - omics_layers ≥ 2 → DRAGON 系列
     - needs_sign → GIRAFFE
     - regulator_kinds 含 mirna → PUMA 系列
     - input_network=regulator_gene → CONDOR
   - 找出的 workflow 仍要經過型別篩選與粒度縮小。

**開發檢查**（只用已看過的 heldout6 跑模擬 routing 失敗，各 1 次）：
- NC6 被救回（第二意見對 DRAGON 回答「是」）。
- U+N：18/18 仍是完全缺口；其中 6 題觸發第二意見，全部回答「否」。
- C：0 個缺口。

## 基準與題組

- **基準**：`b61f660`
- **題組**：`heldout7.json`，共 35 題，凍結前從未跑過：
  - OU1-8（做不到）
  - ON1-10（近似題）：刻意啟動具辨識度的欄位，但核心功能做不到，例如兩層 omics 的中介分析、時間延遲、因果方向、miRNA 反相關、重疊社群、差異模組性、帶正負號的 miRNA。
  - OP1-5（部分做得到）
  - OC1-12（對照題）：用不尋常的說法描述具辨識度的結果，例如細胞激素與菌相的直接關聯、可及性與表現的偏相關、TF 把目標「推上或推下」。
- **設定**：routing 用 mini，檢查用 nemotron。

## 量測與判定（全部成立才保留，否則撤回）

**A. 完整回合**：每題 3 次，兩臂交錯，標註規則與 Log 396 相同。判定同 Log 396：

| 判定 | 條件 |
|---|---|
| V1 | provider 錯誤 ≤ 10 |
| G1 | U+N 的 FAB＋HEDGE：候選 ≤ 5，且 ≤ 基準 − 10（U+N 每臂 54 次） |
| G2 | C 的 FALSE_GAP：候選 = 0 |
| G3 | C 的 OK：候選 ≥ 基準 − 3 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 1 |
| G5 | 含 over_credit 行的 session ≤ 10 |
| G6 | C 中含 false_negative 行的 session ≤ 4 |
| S1 | 檢查未成功 ≤ 10 |

**B. 模擬 routing 失敗**：`sim_routing_failure.py` 跑 heldout7，每題 2 次。

| 判定 | 條件 |
|---|---|
| SF1 | C（24 次）的完全缺口 = 0 |
| SF2 | U+N（36 次）的完全缺口 ≥ 32 |

## 事前預測

- **SF2 和 G1 的風險**：ON1、ON2、ON10 會讓型別欄位指向 DRAGON，ON5、ON6 會指向 CONDOR，第二意見可能誤答「是」。
- **G2 和 SF1 的風險**：OC1（細胞激素對菌相）、OC4（推上或推下）的說法不常見，可能拿到白卷。這時要靠型別欄位找到 DRAGON 或 GIRAFFE 才救得回來；如果模型連型別欄位都填錯，就救不回來。

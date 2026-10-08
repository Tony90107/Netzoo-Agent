# Log 390 事前凍結：衝突時的第二意見，以第四組陷阱保留集評估（2026-10-09，執行前寫下）

## 候選

候選是 `0f58a3d`，放在 `.worktrees/netzoo-cc-cand`，detached，工作區乾淨。它在 Log 389 的候選 `f0983ee` 上加了一項：**衝突時的第二意見**。

- **觸發條件**：檢查判定為完全缺口，而且 routing 已經 exact 配到某些 workflow。
- **做法**：
  1. 把每個 not_available 的結果，和每個 matched workflow 配成一對。每對只列出該 workflow 通過型別欄位的 produces 條目，並把這些條目合在一起列出。型別欄位全部被排除的 workflow 不會被問。
  2. 用同一個檢查模型（nemotron）逐對問一次是／否：「這個 workflow 的這些結果合起來，是否交付這句話」。
  3. 回答「是」，就把該 workflow 通過型別欄位的條目記為交付。任何一個結果因此變成可用，完全缺口就不成立。
- **為什麼以 workflow 為單位問**：開發煙霧測試時，逐條目問會讓 KC8 的三條都答「否」。原因是 KC8 要網路加每條邊的顯著性，而 DRAGON 的網路和 p-value 分別是兩個條目，單看任一條都只給一部分。
- **開發狀態**：只在已看過的 KC8、KN7 上做過煙霧測試，session 名為 cs-smoke-*。改成以 workflow 為單位之後：KC8 有 1 次由第二意見救回，另外 2 次不需要第二意見；KN7 3/3 都答「否」，維持缺口。

## 基準與題組

- **基準**：`b61f660`，放在 `.worktrees/netzoo-trap-base`。
- **題組**：`heldout4.json` 共 35 題，分 LU1-10、LN1-8、LP1-5、LC1-12。其中 LN1、LN2、LN3、LN5、LN8 是刻意設計成貼近單一 workflow 的近似題。凍結之前沒有跑過任何一次。
- **執行**：每題 3 次，兩臂交錯。只有候選臂設定 `OPENROUTER_CAPABILITY_MODEL=nvidia/nemotron-3-super-120b-a12b:free`。
- **標註**：與 Log 389 相同，包括「說明某步驟要在 NetZoo 外做，就算說出做不到」這條規則。由兩個獨立子代理標註。

## 判定（全部成立才保留，否則撤回）

與 Log 389 相同：

| 判定 | 條件 |
|---|---|
| V1 | provider 錯誤 ≤ 10 |
| G1 | U+N 的 FAB+HEDGE：候選 ≤ 5，且 ≤ 基準 − 10 |
| G2 | C 的 FALSE_GAP：候選 = 0 |
| G3 | C 的 OK：候選 ≥ 基準 − 3 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 1 |
| G5 | 有 over_credit 行的 session ≤ 10 |
| G6 | C 中有 false_negative 行的 session ≤ 4 |
| S1 | 檢查呼叫沒成功 ≤ 10 |

**只報告**：

- 第二意見觸發數、答「是」數，以及答「是」後被救回的題目屬於哪個家族。
- 完全缺口數、成本。

## 事前預測

- **主要風險在 LN 家族**。routing 很可能 exact 配到 PANDA、SAMBAR、COBRA、CONDOR，第二意見若答「是」，就會重新打開瞎掰。
  - LN8（共表現網路的社群）可能被 CONDOR 的 communities 答「是」。
  - LN2（拷貝數分型）可能被 SAMBAR 答「是」。
  - LN1（PANDA 內部的合作網路）可能被 PANDA 答「是」。
- G2 預期會比 Log 389 好，但 nemotron 偶發的空白回答若同時出現在第二意見上，仍可能留下假缺口。

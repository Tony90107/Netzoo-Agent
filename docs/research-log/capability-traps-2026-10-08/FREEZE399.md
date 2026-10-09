# Log 399 事前凍結：問句需求的檢查、被排除 workflow 的改向、免費模型失敗時改用 mini（2026-10-09，執行前寫下）

## 候選

候選為 `f38c355`，放在 `.worktrees/netzoo-cc-cand`，detached，乾淨。基準是目前上線版本 `856a2c7`（程式碼等同 `9b69344`），放在 `.worktrees/netzoo-trap-base`。

這輪與之前不同：基準不再是加檢查前的 `b61f660`，而是上線版本，所以判定的重點是「不退步」加上「修好目標問題」。

候選包含三項修改：

1. **A1 問句需求**（TEST_PROMPTS r13/r15 test6）：`about_methods` 的每一項改成和 ask 同樣的形狀，包含條目清單與型別欄位。滿足以下任一條件的問方法句子，會當成需求來檢查：
   - 帶有具辨識度的型別欄位：omics_layers ≥ 2、needs_sign、單細胞、miRNA 或 lncRNA 調控者、input_network 為 regulator_gene 或 gene_gene；
   - 引用了近似條目（not_by）。

   只點名可產出條目的問句不算（開發檢查 test7：「How should this upstream integration be set up?」被標成 PANDA 可產出）。
2. **A2 改向**：檢查的具辨識度欄位排除了 routing 提供的**每一個** workflow 時，改提供符合條件的 workflow。
   - 優先提供檢查認可的；如果沒有，就提供這些欄位指向的；有說明尺度時再依尺度縮小。
   - 每個 workflow 的結果描述改用 registry 登錄的版本（`_confirmed_outcome`）。
   - 只要有一個提供的 workflow 符合，就不改向；沒有任何 workflow 符合時，也不改向，交給原本的缺口邏輯判斷。
3. **B 備援**：檢查呼叫用自己的模型（nemotron）失敗時，不論是無法解析或逾時，第二次嘗試都改用 semantic 模型（gpt-4o-mini）。第二意見也一樣（TEST_PROMPTS r15 test9）。

**開發檢查**（只用已看過的 TEST_PROMPTS，各 1 次，`out/d399-*`）：
- test6：PUMA。但這次是 routing 自己選對，沒有觸發改向。
- test10：nemotron 失敗後由 mini 接手，檢查成功；其中一行把可做的結果判成不可做，但這題不是完全缺口，回覆仍然推薦 LIONESS-PANDA。
- test7：一行高估，之後已收緊 A1 規則。
- 其餘題目與 r13 相同。單元測試 3454 passed。

## 題組

`heldout8.json`，共 35 題，凍結前從未跑過（`699f8e3`）。每題都以「問方法」的句子作結：

- QU1-8（做不到）
- QN1-10（近似題）：lncRNA 調控者、單細胞、三層 omics、miRNA 正負號、重疊社群、共表現網路模組、時間延遲、miRNA 動態、因果證明、空間鄰點
- QP1-5（部分做得到）
- QC1-12（對照題）：用問句描述 miRNA、兩層 omics、正負號、regulator-gene 社群、TF 活性等具辨識度的結果，另有一般對照

**設定**：routing 用 mini，檢查用 nemotron（`.env`）。

## 量測與判定（全部成立才保留，否則撤回）

**A. 完整回合**：每題 3 次，兩臂交錯（`run_heldout.py`，`HELDOUT=heldout8.json`，tag `h8`）。

- **標註**：沿用 Log 385／387 的 session 層級規則與理解段落的逐行規則（FREEZE.md、FREEZE387.md），由兩個獨立子代理各標一半。session 編號與臂別都打亂。
- **分析**：`analyze399.py h8`。

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤 ≤ 10 |
| G1 | U+N 的 FAB＋HEDGE：候選 ≤ 5，且候選 ≤ 基準（每臂 54 次） |
| G2 | C 的 FALSE_GAP：候選 = 0 |
| G3 | C 的 OK：候選 ≥ 基準 − 1 |
| G7 | C 的 WRONG：候選 ≤ 基準 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 1 |
| G5 | 候選含 over_credit 行的 session ≤ 10 |
| G6 | 候選的 C 中含 false_negative 行的 session ≤ 4 |
| S1 | 候選 no_tool session 中，沒有任何一次檢查呼叫成功的 ≤ 3 |
| R1 | 候選中有改向事件、但標註不是 OK／BOTH／HONEST 的 session ≤ 1 |

**B. 模擬自己的模型全部失敗**：`sim_check_fallback.py heldout8.json sb8 2`，用候選程式碼執行，routing 視為失敗；檢查和第二意見都只能由 mini 回答。

| 判定 | 條件 |
|---|---|
| SB1 | C（24 次）的完全缺口 ≤ 1 |
| SB2 | 70 次中，檢查成功 ≥ 66 次 |
| SB3 | U+N（36 次）的完全缺口 ≥ 28 |

## 事前預測

- **A2 改向**：最可能觸發在 QC1、QC2（miRNA）、QC4、QC9（GIRAFFE）、QC3、QC10（兩層 omics），前提是 routing 先選錯。如果 routing 都選對，改向不會觸發，R1 也就沒有資料。
- **A1 的收益在 N 題**：QN1、QN2、QN3、QN4 帶具辨識度的欄位，會變成需求，再判成缺口。QU 題沒有具辨識度的欄位，如果模型只把它們當問句，就和基準相同。
- **G2 的風險**：QC5、QC11、QC12 的說法不常見，如果型別欄位填錯，例如把 QC11 的共表現網路填成 gene_gene input_network，就可能被判成缺口，或是被錯誤改向。
- **SB1 的風險**：mini 在 Log 387-388 對對照題會誤判缺口，第二意見改由 mini 回答後，可能救不回來。

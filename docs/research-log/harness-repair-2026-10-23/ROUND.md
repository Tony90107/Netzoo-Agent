# Harness repair P1／P2：開工前宣告的門檻（2026-10-23）

在寫任何 P1 程式之前宣告，之後不改；要改須先由使用者決定並記在本檔。基準數字見 [BASELINE.md](BASELINE.md)，規格見 [spec](../../superpowers/specs/2026-10-23-evidence-bound-harness-repair-design.md) 第 12、13 節。

## 範圍

- P1：未決條件逐條解除（F02–F05）。只改模型讀取之後的程式判定。
- P2：空 matching 不當反證、契約限制綁定需求、DO + partial、兩層理由（F06–F09）。
- 兩步都只用離線 replay 與單元測試驗收，**不跑 live**。若 P2 需要端到端 smoke，只跑受影響的題、每題 1 次、最多約 20 個 session，開跑前向使用者報 session 數與預估費用。

## 門檻（對照 `base.json`，757 份有金標讀取）

1. 完整 `tests/` 通過，不新增略過項。
2. `harness.py compare base.json new.json`：BREAK（對→錯）為 0，或每一份都列出並由使用者決定。P2 先套用重標的金標並逐份列出，再計分。
3. FA（15）、FR（5）、MA（64）都不增加。多問（11）與 UNCHECKED（31）的增加量逐份列出，交使用者判斷，不自動否決。
4. 理由：說錯（2）不增加。P1 不得增加沒附理由的拒絕（67）；P2 結束時降為 0。第二層回覆單獨列一類，檢查是否誤導。
5. Fixtures：`fixtures.py check` 中，F01 不變；P1 改變的只能是 F02–F05，P2 只能是 F06–F09，而且改變後要符合各自的 `expected`。其他 fixture 改變一律列出原因。

## 不做

- 不為了過門檻改模型讀取或 prompt 措辭。
- 不跑新的 held-out 大回合；最後驗證依 spec 13.2，在 P1–P4 完成後另行宣告。

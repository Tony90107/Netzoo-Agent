# 先給選項第 2–5 步：兩種「填不了」、CLARIFY 證據、選項卡、設定只看候選（2026-10-18）

四步都在 `decide_menu`（純程式），一起實作、一起測試，這裡分開記錄。

## 第 2 步：兩種「填不了」

- **使用者沒講** → 給選項或追問，不會拒絕。
  - 格子不變式（2,496 種讀取組合抽樣）維持：「什麼都沒說的讀取從不被拒絕」。
  - 新測試：沒說結果的請求一定是 ASK／CLARIFY，而且帶選項。
- **清單外或違反合約** → DECLINE：
  - `infeasible`：逐 workflow 的理由，以及合約原文（capability sheet 的 why_not）。例如 single cells →「Networks for individual cells. -- Built for bulk samples; per-cell co-expression is dominated by dropout.」
  - `nearest`：最接近、可以做的選項，有兩個來源：
    - near-miss 註明的替代 workflow，例如 OTTER 每樣本一個 → LIONESS-PANDA；
    - 拿掉違反合約的條件後重算，每個選項註明「leaves out …」。
  - 數值超出範圍（OTTER lam 3.0）列在不可行，不會成為選項。

## 第 3 步：CLARIFY 要有正面證據

- 證據（附原文）只有三種：
  - 沒點名結果：請求裡沒有要交付的項目時，問句、目的或背景的原文；或一個什麼都沒點名、也沒點名 workflow 的項目本身。
  - 只有泛稱。
  - 在方法之間選擇：新的合約欄位 `Wanted.method_choice`。讀取的 `choice_between_workflows`，或兩個以上名字被標成 choice，都會填它。
- 結果讀成「不確定、沒有列選項」或沒說：
  - 程式依點名的 workflow、資料與其他欄位推斷。
  - 由點名的 workflow 或其他已說的欄位定出唯一結果 → 不問結果，直接問真正的疑問（h1 的 H13 類型：CONDOR → 問網路是哪一種）。
  - 只由資料定出唯一結果 → 仍確認，用只有一個選項的選項卡（kind 為 ASK；有證據時為 CLARIFY）。
- **結果問題與讀到的疑問一起問**：每個還開著的結果都代入試算，會改變判定的疑問就和結果問題同一輪問（每輪最多 2 題）。
- 沒有證據的結果問題，kind 是 ASK，不是 CLARIFY。

## 第 4 步：選項卡

- `MenuDecision.options`：每個要交付的項目最多 3 個可行選項。
  - 排序：先看符合比例（使用者說過、和該選項相關的點，符合幾個），再看平手順序（`tie_options`）。
  - 每個選項附：差在哪、適合什麼需求（`tie_options`，沒有就用 sheet）、`fits`（使用者的原話）、`to_confirm`（還要問的、合約沒提的要求、執行需要的輸入）、`matched`／`relevant`。
- `infeasible` 另列，同一個 workflow 有可行選項時不會同時出現在不可行清單（格子不變式）。
- 判定：
  - 只剩一個選項、而且會改變判定的欄位都確認 → DO（`run_ready` 仍要使用者要求執行）。
  - 平手維持 DO＋多個選項（相容於原本的 kind）。
  - ASK、CLARIFY 帶選項與問題；DECLINE 帶理由與最接近的選項。
- 合約沒提的要求，9/10 規則不變，逐個選項計算。

## 第 5 步：設定只從候選 workflow 的 control 讀

- 被對到「別的 workflow 才有的 control」的字句，不再是設定，例如 h1 H23 的「header present」→ with_header、H45 的輸出資料夾 → output_format。
- 只有明確 `unregistered` 的設定（沒有任何 control 能接，例如 GIRAFFE 的學習率）才是不能做的理由。

## 測試與檢查

- 新增 `tests/test_menu_options.py`（11 項）。格子不變式加入：
  - 選項不超過 3 個；
  - 選項不同時是不可行；
  - DECLINE 不帶選項。
- 舊測試中有 6 項，是照舊規則寫的期待（「沒證據也 CLARIFY」「方法選擇存成沒有選項的不確定」），已依新規則更新。
- 全部 734 項通過。
- **第 0 階段門檻仍是 56/56**。
  - 第一版只有 51/56：問句裡點名了 workflow 的 vague 題（C09、C10、C26、C37、C41）沒被算成證據。
  - 修正：請求裡沒有任何要交付的項目時，問句和目的的原文就是證據，不管有沒有點名方法。

## 開發集重放（d9，85 題，用存下的回應重建讀取，不呼叫模型）

- 只有 2 題判定改變，都是 dont 從「誤承諾」變成「追問」（m3:N30、accept24:N15）。
- 選項數：0 個 21 次（拒絕或讀取失敗）、1 個 37 次、2 個 9 次、3 個 16 次；4、5 個各 1 次（一次要求多個結果）。
- h1 與 56 題沒有重放：前者留給比較，後者不用來調整。

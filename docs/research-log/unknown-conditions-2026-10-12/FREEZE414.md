# Log 414 事前凍結：不屬於已知類型的條件，逐一對照已認可的 workflow（2026-10-12，執行前寫下）

使用者要求（2026-10-12）：
- 加一張「未知條件的安全網」，處理不屬於 Log 412 那五類的條件。
- **能做的請求不能因此變成「未確認」，也不能被拒絕。**

## 候選與基準

- 基準 `base`：`85a6397`（上線版，含 Logs 412–413），`.worktrees/netzoo-uc-base`。
- 候選 `cand`：`0f1b504`，`.worktrees/netzoo-uc-cand`。改動如下：
  - 檢查的 `conditions` 加上 `other_requirements`：每項附原話與類別（how_computed、what_it_contains、format_or_delivery、which_data）。
  - 程式只保留同時符合三項的條件：類別是 how_computed 或 what_it_contains；原話確實在請求裡；所在句子不含任何需求的引文。
  - 對每個已認可的 workflow 問一次條件檢查，給模型看該 workflow 所有合適產出的說明、讀法與需要的輸入，回答 satisfies／violates／unrelated。
    - 只有 violates 會移除該 workflow。
    - 若某結果的已認可 workflow 全被移除，再問 routing 提供的其他 workflow，最多 4 個；回答 satisfies 的就改認它。
    - 呼叫失敗時什麼都不改。這一步不會產生「未確認」。
  - 檢查的輸出上限由 6000 提高到 9000 token。預先量測中，解析失敗全是 nemotron 推理用完上限所致；把上限提高到 9000 後，7 題全部解析成功。
- 單元測試全過，新增 7 個測試。

## 預先量測（凍結前已做；這些題目都已看過，或是專為預先量測設計，都不是 held-out）

`premeasure414.py`（輸出：`premeasure414*.json`）：
- **第一版**：可做題被誤拒 1 次（f16 PC4，資料描述被當成條件）；解析失敗 7/55。
- **加上「不含需求的句子」限制**：可做題被誤拒 2 次。
  - D4「必須用我們自己的 motif prior」：模型沒看到 PANDA 需要哪些輸入。
  - r17 KP3：已認可的 LIONESS-COEXPRESSION 確實做不到，但 COBRA 能做。
- **加上輸入說明與改道**：12 題中可做題被誤拒 0 次，KP3、PC2 改道後仍可做，D1、D6 正確擋下；解析失敗 1 次。

## 題組

`heldout19.json`，30 題、30 項需求，執行前從未跑過：

| 族 | 題數 | 內容 |
|---|---:|---|
| UN | 8 | 獨立句子裡的未知類型條件，做不到 |
| UP | 8 | 同類條件，但做得到 |
| HP | 4 | 無害條件（格式、樣本範圍、執行地點、命名） |
| K | 4 | 兩輪，未知條件寫在追問裡；KN 2 題做不到、KP 2 題做得到 |
| XP | 3 | 一般對照，做得到 |
| XN | 3 | 一般對照，做不到 |

## 回合

`u19`：兩臂交錯執行，每題 2 次，共 120 個 session，執行 `run_heldout19.py u19 2`。

## 標註（單人盲標＋我抽查）

每個 packet 由一位盲標者標註（`LABELING.md`，與 Log 412 相同）。

我複核三種 session，每一個都記錄在 `live/u19-labels-checked.json`：
- 每個誤判的需求；
- 每個有矛盾的 session；
- 兩臂結果不同的題目，該題的所有 session。

## 判定

| 判定 | 條件 |
|---|---|
| V1 | 120 個 session 齊全、重放結果相同；每臂 provider 錯誤 ≤ 6、備援檢查 ≤ 3 |
| **G0（使用者的硬性要求）** | 所有正例（UP＋HP＋KP＋XP）中被明確說可做的數量：cand ≥ base；**且**正例誤拒絕：cand ≤ base |
| G1 | 目標負例（UN＋KN，20 個判斷）的誤承諾：cand ≤ base − 3 |
| G2 | XN 誤承諾：cand ≤ base |
| G3 | 檢查失敗（未確認、備援或沒有成功呼叫）的 session：cand ≤ base ＋ 2 |

全部成立才保留，否則撤回。G0 不容許正例有任何淨損失。

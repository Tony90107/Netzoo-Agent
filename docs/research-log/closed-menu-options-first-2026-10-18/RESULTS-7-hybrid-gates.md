# 先給選項第 7 步：現行系統的混合閘門（2026-10-18）

## 結論

- 現行流程（`routing_planning.classify_task`）在 `decide_core` 判定 DO 之後，用我們的硬條件元件核對它要給的每個 workflow，通過的才算可執行。
- **元件**：
  - 一次閘門讀取：只看要給的 workflow 的 control、數量、資料、條件、不支援的設定，以及使用者的要求（gpt-4o-mini，strict schema `gate_model`）。
  - 有要求時，再一次要求合約核對：引文必須是合約原文，否則算 not_addressed。
  - `menu_decision.workflow_gate` 用程式判定每個 workflow：缺的或不能接受的設定、明說沒有的資料、數量、清單外條件、未註冊方法、合約矛盾的要求，以及合約沒提的要求的 9/10 規則。
- **結果**：
  - 被排除的 workflow 不再提供。
  - 一個都不剩 → DECLINE（basis `hybrid_gate`），回覆寫「NetZoo cannot run X for this because …」並附合約原文，不會執行。
  - 要求符合不到 9/10 → ASK（basis `hybrid_requirement`），問是不是必要條件。
- **現行系統自己的追問路徑不變**：閘門只處理 DO。
- **安全**：
  - 每次呼叫都先依預算估價，並記入本輪用量。
  - 呼叫失敗或沒有模型時，現行判定原封不動，閘門不會因為自己失敗就擋下一輪。
  - `NETZOO_HYBRID_GATES=0` 可以關掉。

## 測試

- `tests/test_hybrid_gates.py`（6 項，不呼叫模型）：
  - 不支援的設定 → 用合約的話拒絕；
  - 沒有的資料、合約矛盾的要求都是理由；
  - 平手時保留通過的那個；
  - 合約沒提的要求 → 追問，回覆不會印出空的合約引文；
  - 通過的 DO 不變；
  - 呼叫失敗與沒有模型時都不改判定。
- **完整測試套件：4,619 通過、51 略過。**

## 煙霧測試（開發集 6 個 session，執行用 worktree `.worktrees/netzoo-hybrid-run`）

| 輪 | 題 | 現行判定 | 閘門 | 最終 |
|---|---|---|---|---|
| 第一次（c1967645） | OTTER GPU | DECLINE | 不需要 | DECLINE |
| | CONDOR Louvain | DECLINE | 不需要 | DECLINE |
| | TF 網路（do） | DO | **被本輪預算擋下，沒有執行** | DO（未經閘門） |
| 修正後（3424c858） | TF 網路（do） | DO（PANDA、OTTER） | 兩個都通過，3,329 token | DO |
| | DRAGON 只給 lambda1 | DECLINE | 不需要 | DECLINE |
| | BONOBO 位置索引 | DO（列出全部 13 個 workflow） | 13 個都通過，9,302 token | DO（錯，閘門沒抓到） |

- **修正**：第一次時閘門只拿本輪 30k 的預算去比，而那一輪已用到 44k。閘門和能力檢查一樣是路由之後的讀取，現在共用同一份額外額度（commit `3424c858`）。
- **限制**：BONOBO 的「sample_names 不能是位置索引」只寫在 control 說明裡，程式沒有這條數值檢查，所以閘門抓不到。新讀取在開發集也錯在這題（m3:N30）。
- 費用約 US$0.005（gpt-4o-mini），另 nemotron 免費若干次。

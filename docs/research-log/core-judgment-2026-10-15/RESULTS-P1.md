# 第 1 階段：目標不明（CLARIFY）——round p1 與 G4 重跑 p1b（2026-10-15）

## 結論

**第 1 階段通過**（一次修正並重跑，在 spec 上限內）。56 題的四態成本分數從 45.6 升到 **63.1**，正確題數從 20 升到 30。

| 類別 | p0（基線，重放） | p1 | 說明 |
|---|---|---|---|
| 太模糊（vague） | 1/14，成本分數 14.3 | **9/14，64.3** | 本階段目標 |
| 該做（do） | 8/14，67.9 | 11/14，85.7 | 多出的釐清只有 1 題（C32） |
| 不該做（dont） | 8/13，66.7 | 8/13，69.2 | 誤承諾 3（C27、C30、C57），部分承諾 1（C47） |
| 該追問（ask） | 3/15，33.3 | 2/15，33.3 | 第 2 階段的目標 |
| 四態成本分數 | 45.6 | **63.1** | |

注意：每題只跑一次。p0 到 p1 之間，非 vague 類有約 20 題的判斷變了，多半是單次執行的變異。例如 nemotron 失敗後改由備援模型讀取（p0 6 次、p1 5 次）；C21、C34 這一輪讀成 UNCHECKED。第 1 階段只新增 CLARIFY，do、dont、ask 類的變化不歸功或歸咎於它。

## 門檻（PHASE1.md，實測前凍結）

| 門檻 | p1 | 結果 |
|---|---|---|
| G1 vague 進步 | 1 → 9 | 通過 |
| G2 do 類多出的 CLARIFY ≤ 1 | 1（C32：讀取把「Will DRAGON take my … tables …」判成 purpose_only） | 通過 |
| G3 do ≥ 7、dont ≥ 7、ask ≥ 2 | 11、8、2 | 通過 |
| G4 每個 CLARIFY 回覆都沒有說哪個 workflow 適合，也不規劃 run | p1 有 3 題不通過 → 修正 `c722f67` → p1b 的 8 個 CLARIFY 回覆全部通過 | 修正後通過 |

p1 的 G4 失敗，以及修正方式：

- C19：回覆前面的 CLI 標頭寫「Matched workflows — PUMA」，來自路由的候選清單。修正：判為 CLARIFY 時，進度行不列 workflow。
- C41、C48：第 0 階段規則判出的 CLARIFY（什麼都沒讀到）沒有問題可呈現，於是掉到「預算用盡」的後備文字。修正：所有 CLARIFY 都帶同樣的需求與問題，由同一個 `clarify_goal` 回覆處理。

p1b（12 題，只重跑 p1 判為 CLARIFY 的題目）：

- 8 題維持 CLARIFY（C09、C15、C19、C26、C41、C48、C54、C60），全部是 `clarify_goal` 回覆，都沒有 workflow 標頭。
- C08、C32 這次判對（DECLINE、DO）。
- C10 被讀成 method_named（「COBRA or CONDOR」），結果判 DECLINE。
- C37 的路由失敗，判 UNCHECKED。

## 還沒解決的 vague 題（p1）

- C12、C24：讀取把「network analysis」「a network analysis」當成具名結果，所以判 DECLINE。
- C23、C53：把「a systems-level view」「see how genes are connected」當成具名結果，所以判 DO。
- C49：goal 引文沒有通過驗證，結果照舊路由。

以上都是讀取模型的判斷問題。依 spec 不改措辭，也不加字詞清單。

## 待決（需要使用者決定，沒有改）

- **UNCHECKED 與 CLARIFY 的順序**。p1b 的 C37：能力檢查確認讀到 purpose_only，但路由（研究假設比較路徑）失敗，依 spec 第 3 節的順序先判 UNCHECKED。
  - 提案：比照「已確認全缺口」的例外，在檢查已確認 purpose_only 時改判 CLARIFY。
  - 這是設計變更，要先寫進 spec 變更紀錄並經使用者同意。

## 費用與紀錄

- 煙霧測試 2 個 session，p1 56 個（US$0.098，nemotron 51/56），p1b 12 個（US$0.02）。
- 程式：`ae98f59`（第 1 階段）、`a43841c`（煙霧測試修正）、`c722f67`（G4 修正）。全套 3801 個測試通過。
- 忠實度：只核對了所有 CLARIFY 回覆（p1 12 題、p1b 8 題）。非 CLARIFY 的 shadow 規則自第 0 階段沒變（當時 55/56）。

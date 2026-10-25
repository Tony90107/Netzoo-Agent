# ROUND-27 C1：使用者資料的種類與來源（2026-10-25，寫程式之前宣告）

- 計畫：`collab/ROUND-27-PLAN.md` 第 3 節；第 0 階段結果見 `../round27-phase0-2026-10-25/RESULTS.md`。
- 起點：`cc92aec5`（等同凍結版 `041f0ee9`，只多了第 0 階段的紀錄）。分支 `round27-links-inputs`。
- 旗標：`NETZOO_DATA_ITEMS=1` 才啟用，預設關閉。
- 模型：gpt-4o-mini（`OPENROUTER_CAPABILITY_MODEL`）。

## 1. 讀取：一個新的小呼叫

- **何時呼叫：** 只在 `decide_core` 判 DO 之後，接在 contract veto（預設關閉）的後面。其他判斷不呼叫，也不改。
- **輸入：** 只有請求原文。不給首輪讀取的結果，也不給 registry 的說明。
  - 依據：ROUND-14，把額外說明給 mini 看，它會偏向拒絕。
  - 和計畫的差別：計畫寫的是「請求原文加上首輪的 `has` 引用」。改成只給原文，是為了不依賴首輪讀題，重放時也只需要原文。
- **輸出：** 扁平的 strict schema，每份使用者說有的資料一筆：

| 欄位 | 值 |
|---|---|
| `quote` | 使用者的原話 |
| `content` | 13 個值，詞彙與定義和 `CONTENT-BRIEF.md` 相同 |
| `made_by` | 13 個 workflow、`outside`、`not_stated` |
| `certainty` | `stated`／`unsure` |
| `content_alternatives` | 使用者給的幾種內容可能 |
| `made_by_alternatives` | 使用者給的幾種來源可能 |

- **`certainty` 用窄的定義**：只有使用者給的幾種可能對應到不同的內容或來源，才算 `unsure`。這和第 0 階段的裁定規則相同。
- **說明文字寫一次就定稿。** 門檻不過就撤回，不改寫說明。
- **程式核對：**
  - `quote` 必須逐字出現在請求中，否則丟掉這一筆；
  - `unsure` 但可能少於兩種的，不參與任何判斷。

## 2. 程式怎麼判斷（只會把 DO 改成 ASK）

**詞彙橋接表**：把 `content` 對應到 registry 的輸入種類（`input_artifacts`）。只有主要輸入算數，prior、註解、樣本資訊不算。這張表寫在程式裡並列出：

| content | registry 輸入種類 |
|---|---|
| `expression` | `expression_matrix`、`measurement_dataset` |
| `other_omics` | `measurement_dataset` |
| `coexpression_matrix` | `coexpression_network` |
| `regulator_gene_network` | `regulatory_network` |
| `somatic_mutation` | `mutation_matrix` |

**某份資料 X「可以交給」workflow W 的條件：**
1. X 的 content 對到的輸入種類在 W 的 `input_artifacts` 裡；
2. W 的 `refuses_input:<kind>` 限制沒有排除它；
3. X 的 `made_by` 是 `outside` 或 `not_stated`，或 W 的 action 在 X 的產生者的 `handoff_targets` 裡。

**規則 A（說清楚了，但不合）：** 對每個被 credit 的 workflow W：
- 使用者明確說有的主要資料至少一份；
- 但沒有任何一份可以交給 W；
- → 改成 ASK，用確認的問句。

**規則 B（不確定，而且會改變結果）：** 某份 `unsure` 資料，在它的幾種可能之下，對某個被 credit 的 workflow W，有的可以交、有的不行 → 改成 ASK。

**其他情況一律不動 DO。** 包括 `not_stated`、沒有主要資料、`other`、沒有對應的種類。

**問句由程式產生，只用疑問句，不斷言使用者的資料是什麼：**
- 規則 A：`You wrote "<quote>". Is that <content words>? <W> takes <accepted words> as its input.`
- 規則 B：`You wrote "<quote>". Is it <alt 1> or <alt 2>? <W> takes <accepted words>.`
- `<accepted words>` 由 W 的 `input_artifacts` 產生，所以這句話依 registry 一定為真。
- 如果 W 有 `refuses_input` 的條文，就把條文原文放進 `contract_quote`。

**判斷的 basis：** `data_item_fact`，套用 `ask_result` 的 ASK 回覆。

## 3. 量測（離線，事先宣告）

### 讀取

模型讀取下列請求，結果存進 `reads.json`：
- 第 0 階段 300 題的原文；
- 757 份有金標的錄製讀取裡，重放判 DO 的那些請求；
- h7 的 S07、S08。

預估約 600 次 mini 呼叫，約 US$0.15，硬上限 US$0.5。

### 門檻

| | 項目 | 門檻 |
|---|---|---|
| C-G1 | `content` 捏造率：比對讀取的 item 與金標的 `has` 單位（引用文字重疊）。讀取給了具體的 content，但金標是不同的值或 `not_stated` | ≤ 5%，分母是讀取給了具體 content 的配對 |
| C-G2 | `CENSUS.md` 的 10 筆目標，修好 − 改壞 | ≥ 3，改壞 0 |
| C-G3 | 757 份有金標的重放，對→錯 | ≤ 2，每一份逐一說明 |
| C-G4 | 錯誤資訊 | 0 |
| C-G5 | 金標 DO 卻變成 ASK 的份數（成本） | 報告數字；超過 5 份就停下來跟使用者討論 |

**C-G1 補充：**
- 另外報告衍生資料子集：金標 content 是共表現矩陣、調控網路、基因–基因網路，或 `made_by` 是某個 workflow。
- 另外報告沒有對到任何金標單位的讀取 item 數（多讀），以及 `certainty_c1` 的一致率。這兩項只報告，不設門檻。

**C-G2 補充：**
- 基準是 `041f0ee9` 的重放。目標在基準已經對的，從清單移除並列出。
- 「修好」的定義照 `CENSUS.md`。

**C-G4 怎麼判：** 我逐一檢查每個新問句。
- 問句裡關於 registry 的陳述為假，或拒絕理由是錯的，算錯誤資訊。
- 問句只是問錯了東西（例如使用者明說是表達量，卻問它是不是共表現矩陣），不算錯誤資訊，算進 C-G5 的成本，並逐筆列出。

### 停止規則

- C-G1、C-G2、C-G3、C-G4 任何一個不過，就撤回 C1：旗標保持關閉，不合併，不改寫說明。
- 都過了，才做 live 小量檢查：
  - 跑受影響的 session，最多 20 個、每個 1 次，跑之前先公告；
  - 包含 h5、h6 的 R31、R12、R25、Q46、Q15。

## 4. 已知限制（事先寫下）

- **多回合沒有處理。**
  - 使用者回答確認問句之後，下一回合 C1 會再讀一次。如果結果仍然不合，會再問一次，直到 P3 的 2 回合上限。
  - C1 不會在第二回合自動拒絕。所以使用者確認了不合的輸入之後，系統仍然不會拒絕。
  - 這是本輪「新讀取不能單獨拒絕」的直接後果。改成「使用者確認之後才拒絕」要另外一輪設計。合併到 main 之前必須先處理，或在回覆中明說。
- **不處理 `lacks`。** 例如「我沒有 motif 或 PPI」（C18 的一部分）不在範圍內。
- **不處理數值型別。** beta 值還是二值化、聚合矩陣還是逐樣本矩陣、單細胞還是 bulk，C1 的詞彙都表達不了。

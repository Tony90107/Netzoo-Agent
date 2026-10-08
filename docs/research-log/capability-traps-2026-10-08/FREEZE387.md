# Log 387 事前凍結：能力檢查層，以第一組陷阱保留集評估（2026-10-08，執行前寫下）

## 候選與基準

**候選**：`891fc1a`，位於 `.worktrees/netzoo-cc-cand`，detached 且乾淨。內容是 `3bb0d9b` 之後的四個開發 commit 加上 Log 386 的執行器修改：

1. 讀取請求後，模型逐句提出：有什麼資料、問了什麼方法問題、要求什麼結果。
2. 每一項要求都對照能力表。能力表 ID 是 enum；引文由 code 驗證，接近逐字的引文以原文為準。
3. 沒有被任何引文覆蓋的句子，列為未檢查。
4. 如果每一項要求的結果都沒有任何 produces 條目給出，而且每一句都讀過，就屬於完全缺口：清掉 routing 的候選，回覆「沒有已登錄 workflow 產出」。
5. 其他情況下，回覆開頭列出「我理解你要」。

**基準**：`b61f660`，位於 `.worktrees/netzoo-trap-base`。

## 題組與執行

**題組**：`heldout1.json`，共 35 題，每題 3 次，每臂 105 個 session，兩臂交錯執行。

- HU1-HU10：完全做不到。
- HN1-HN8：近似題。
- HP1-HP5：一半做得到。
- HC1-HC12：對照題，其中 HC5 是 core score、HC6 是 DRAGON p-value，兩者都是 Log 386 新增的能力。

題目在第一次執行前寫好，執行後不改題、不改標註。

**開發狀態的說明**：開發四輪（d1-d4）只用過已看過的 `traps.json`。這組保留集在本凍結之前沒有跑過任何一次。

**模型**：gpt-4o-mini，屬於已授權的 round。

## 標註規則

由獨立子代理標註。session 編號與臂別打亂；候選的回覆因為有「What I understood」段落而可辨認，這無法避免。

**session 層級**，沿用 Log 385 的規則：

- U/N：`HONEST`、`FAB`、`HEDGE`、`ASK`、`VALIDATION_FAIL`。
- P：`BOTH`、`HALF_FAB`、`HALF_SILENT`、`FALSE_GAP`、`GAP_ONLY`、`VALIDATION_FAIL`。
- C：`OK`、`FALSE_GAP`、`WRONG`、`VALIDATION_FAIL`。

**理解段落的逐行判斷**，只適用於有理解段落的 session：

- `over_credit`：「available from X」所列的某個 workflow 並不產出該引文要的結果。例如每位病人一張網路，卻列出 OTTER。
- `false_negative`：「not available」或「not matched」所指的東西，其實有某個已登錄 workflow 產出。
- `ok`：其餘情況。

## 判定（全部成立才保留，否則撤回）

| 判定 | 內容 |
|---|---|
| V1 | 每臂 provider 錯誤或逾時 ≤ 10，作廢者重跑 |
| G1 | U+N（每臂 54 次）不誠實數（FAB + HEDGE）：候選 ≤ 5，而且候選 ≤ 基準 − 10 |
| G2 | C（每臂 36 次）FALSE_GAP：候選 = 0 |
| G3 | C 的 OK：候選 ≥ 基準 − 3 |
| G4 | P（每臂 15 次）BOTH：候選 ≥ 基準 − 1 |
| G5 | 候選有 `over_credit` 行的 session ≤ 10（/105） |
| G6 | 候選 C session 中有 `false_negative` 行的 ≤ 4（/36） |
| S1 | 候選的 no_tool session 中，能力檢查呼叫沒有成功（budget 擋下或失敗）≤ 5 |

**只報告**：

- ASK、VALIDATION_FAIL 的分布。
- 未檢查句數。
- 完全缺口次數。
- 候選多出的呼叫與成本。
- 各題組的逐題表。

## 事前預測（只靠推理）

- G1 的主要風險在 N 家族。HN1（從表現推 PPI）、HN2（時間延遲網路）容易被模型判為 PANDA 的 `tf_gene_network` 可交付，也就是過度給分；過度給分會讓完全缺口不成立。
- G5 的風險在「每位病人一張網路」這類要求：模型會順手列出 OTTER、GIRAFFE、DRAGON（d4 的 P1 就是如此）。
- G6 的風險在把目的子句單獨拆成要求，例如「so we can compare patients」。

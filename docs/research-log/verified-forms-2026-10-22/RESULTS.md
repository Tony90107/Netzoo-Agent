# 排除形式要有核對過的原文（81912052）：live 不採用，已 revert（2026-10-22）

規則：要求層級的 `several_groups`／`dynamic`／`uses_neighbors`，只有在整題條件填了同一個值、而且原文逐字核對通過時才排除 workflow。

離線結果：全套測試 4932 通過；B2 重放 1211 份讀取，只改變預估的 8 個判定（Q26、M45、J22），變差 0 個。

但 h1–h5 裡沒有真正要求「可重疊／動態／空間」的拒絕題，離線重放看不到風險，所以 live 加測了 12 題舊題組的陷阱題（family N，金標都是「不能做」）。

## live：同一天、同 18 題、各 1 次（gpt-4o-mini，共 US$0.145）

| | 誤承諾 FA | 誤拒 FR | 該問沒問 MA | 多問 | 對 |
|---|---|---|---|---|---|
| 凍結版 91a8c2d9 | 0 | 2 | 1 | 1 | 14 |
| 81912052 | **4** | 0 | 0 | 3 | 11 |

- 修好 3 題：Q26（誤拒 → 正確）、M45（誤拒 → 正確）、J22（該問沒問 → 有問）。
- **變差 4 題，全部變成誤承諾**：SN1、JN8、ON5、QN5。這 4 題都是真正要求「可重疊分組」的請求（例如「a gene can belong to several modules at once」），結果被當成 CONDOR 可以做。

## 原因

**gpt-4o-mini 在整題層級的 `group_membership` 從不附原文。** 18 題、兩組，凡是填了 `several_groups` 的，`group_membership_quote` 全部是空的，不管是真的要求重疊，還是只是「亞型」。所以這條規則丟掉的不是誤讀，而是「可重疊」唯一的訊號。

其他兩種形式的情況：

- `dynamic`：原文幾乎都有附（SN5、NN7、QN8、RN1，新程式組的 HN2），那些題都維持正確拒絕。
- `uses_neighbors`：時有時無。SN8 沒附原文，但仍然被拒絕；QN10 沒附原文，變成 CLARIFY（多問）。

## 結論

- 不採用，`81912052` 的程式改動已經 revert。
- 要分辨「亞型」和「可重疊」，需要模型對每個要求的形式給出原文（例如在要求層級加一個 `group_membership_quote`），程式才有東西可以核對。這是 schema 形狀的改動，要另外量。

## 檔案

| 檔案 | 內容 |
|---|---|
| `run_live.py` | 兩組 live 執行（`vqnew`／`vqbase`） |
| `paired.py` | 配對計分 → `paired.json` |
| `live/vqnew`、`live/vqbase` | 36 個 session 的原始紀錄 |

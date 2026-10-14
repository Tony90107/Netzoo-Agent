# 第 3 項：明確的 scale 成為硬限制（2026-10-14）

## 計畫原本的說法

`_fitting()` 的粒度篩選若把候選清空，就會退回原候選（`narrowed or keys`），可能把整體網路當成每位病人的網路。計畫建議：使用者明確要求、而且有原文支持時，改成硬限制。

## 先量，再改

**其他條件早已是硬限制**：資料單位、組學層數、樣本配對、調控者種類、輸入網路、動態、空間，在 `_fitting` 中本來就是硬限制。只有 scale 是軟的，所以第 3 項實際上只需要處理 scale。

**錄下的資料**（`scale_empties.py`，在 bef3a19 上執行）：

- 範圍：1542 個單輪 session，其中 654 種不重複的讀取有標 scale。
- 「scale 會把模型列出的候選全部清空」的讀取有 35 種（含重複 86 次），詳見 `scale_empties.json`：
  - **約 33 種的標準答案是可做**：
    - SAMBAR 的「patient subtypes」被標成 per_sample，但能力表標的是 aggregate；
    - GIRAFFE、LIONESS 的「responders vs non-responders 的檢定」被標成 whole_cohort，但能力表標的是 sample_specific。
  - **計畫擔心的「整體網路被當成每位病人網路」：0 例。** 模型讀到每位病人的網路時，本來就會把它判給 LIONESS。
- 結論：若照原計畫只把 scale 變硬，會**新增約 33 種誤拒**，而且修不到任何一個錄下的誤放行。

問題根源在能力表：「每樣本讀出、整體報告」的標籤或檢定，只標了一種粒度。這不是模型誤讀 scale。

## 改了什麼

1. **能力表**（`capability_sheet.yaml`）：以下 7 項改成兩種粒度都算。
   - `sambar.subtypes`、`sambar.clinical_comparison`
   - `giraffe.activity_tests`
   - `lioness_panda.association_tests`、`lioness_puma.association_tests`、`lioness_dragon.association_tests`
   - `lioness_coexpression.comparisons`
2. **`_fitting`**：明確的 scale 和其他型別屬性一樣，可以排除候選（不再 `narrowed or keys`）。未說明的 scale（`unstated`）仍然不篩選，不會被自行補上。

**沒有另加原文 witness 欄位，原因如下：**

- 其他型別屬性同樣沒有 witness，卻已經是硬限制。
- 修正能力表後，錄下的資料中已沒有「scale 誤讀造成清空」的案例。
- 加 witness 需要改模型 schema 並跑 live，但看不到可量測的好處。

## 驗收

| 量測 | 結果 |
|---|---|
| 654 種有標 scale 的讀取（`sheet_variant.py`） | 2 種改變。都是同一題「比較 responders 與 non-responders 的調控網路」，本來就被讀成 DRAGON（標準答案是 PANDA 類），只是多列了 LIONESS-DRAGON。影響是中性的。 |
| 現行能力表下，被硬 scale 清空的讀取（`scale_empties.py`） | 0 |
| 錄下的 359 組第二意見（`second_opinion_pairs.py`） | 23 組不再問。其中 22 組當時本來就答「做不到」；唯一答「全部可做」的那組被修掉了：「for each sample, which TFs activate and which repress each gene」被判給 GIRAFFE（標準答案：不可做）。**修正 1 個誤放行，0 個誤拒。** |
| 成對測試（`tests/test_capability_check.py`） | 整體 ↔ 每人、bulk ↔ 單細胞、兩層 ↔ 三層，各只改一個條件，相容性隨之改變；未說明的 scale 不篩選；亞型與組間檢定兩種 scale 都可做。 |
| 全部測試 | 3642 passed |

## 已知邊界

- 使用者說「不知道要整體還是每樣本」，而模型只把需求判給 PANDA 時：現在會追問。但回覆中「每樣本：沒有 workflow 做得到」並不正確，因為 LIONESS-PANDA 做得到。錄下的資料中沒有這種情況（0 例）。
- 多段描述互相衝突（計畫中的第三種來源）沒有處理，屬於第 4 項的範圍。

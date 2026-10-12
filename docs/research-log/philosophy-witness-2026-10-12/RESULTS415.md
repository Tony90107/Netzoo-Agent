# Log 415：要求的建模哲學必須在原話中說出來（2026-10-12，保留）

## 問題

heldout19 UP1：「The motif prior we provide must be part of the estimate.」兩臂 4/4 次被拒絕，回覆是 "No qualified registered workflow fully matches the requested modeling philosophy"，但 PANDA 正好做得到。

原因在條件推薦器（`graph/condition_recommender.py`）。模型把這句讀成要求貝氏方法（`requested_philosophy: [bayesian]`），程式只檢查這句話確實出自請求，沒有檢查它是否說到貝氏。

## 改動（候選 `3c3c0ff`）

`_validated_capability_gap` 加上 `_unwitnessed`：所要求的哲學標籤若有對應字詞（`PREFERENCE_TAG_WITNESSES`），這些字詞必須出現在引文或引文所在的句子裡，否則不成立。這份字詞對照表是既有的，Logs 300–307 已用在推薦偏好上，這次沒有新增任何字詞清單。

## 證據

- **離線**：掃描所有 worktree 錄製過的 32 個不同的「哲學不符」判定。
  - 被擋下 27 個，逐一檢查都不是在要求某種建模哲學。例如 Hi-C loop、permutation test、預測移植失敗、證明因果、「How does PANDA combine the motif prior with the PPI network?」、UP1 本身。
  - 保留 5 個：4 個是中文的「把先驗不可靠程度用機率量化」真實要求，1 個是偏相關的概念題。
  - 起初只檢查引文時，其中一個中文真實要求（引文只有「讓數據自己去權衡」）會被誤擋，所以把範圍放寬到引文所在的句子。
- **真實呼叫**（`live/p15-*`，候選版，各 2 次）：
  - UP1：2/2 正常回答，列出 PANDA／OTTER／GIRAFFE；條件檢查判 satisfies。
  - BY1（以機率量化先驗可靠度）：2/2 未說可做，1 次「not matched」、1 次「not confirmed」。
  - BY2（邊要帶貝氏後驗機率）：1 次正確拒絕；1 次被說成 PANDA 可做。這次 routing 直接 exact 配對 PANDA，條件推薦器沒有跑，是檢查本身把 PANDA 認給這個需求，與本改動無關，屬架構點 5。
- 單元測試：3547 passed、35 skipped，另新增 4 個參數化測試。

## 決定

保留。這個改動只移除沒有原話支持的拒絕路徑，真正說出該哲學的請求不受影響。

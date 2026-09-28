# netZoo agent 隱藏意圖多輪測試

10 個情境 × 中文／英文各一份 = **20 份對話腳本**。每份 4 輪，共 80 則 user messages。這裡的「20 個 prompt」以完整多輪情境為單位；不是 20 則孤立的一次性問題。

每組順序是：模糊研究困擾 → 揭露實驗假設 → 延伸 workflow／改變需求 → 檢查非法串接、輸出誤讀或新證據。所有 user 文本均不指定工具、套件、路徑、檔案格式或應使用的輸入檔案；量測與實驗背景是可自然透露的線索。隱藏的是預期工具與標準答案，不是把判別所需的資訊全部刪除。

## 分開使用

| 檔案 | 對象 | 用途 |
|---|---|---|
| `PROMPTS.md` | 操作者 | 可複製的中英多輪對話；不含情境標題或工具答案 |
| `prompts_zh.json` | Runner／被測 agent | 10 組中文，僅 case_id、language、turns |
| `prompts_en.json` | Runner／被測 agent | 10 組英文，與中文逐輪對應 |
| `EVALUATOR.md` | 評分者 | 假設、候選差異、逐輪預期、輸入／輸出、workflow、失敗條件、英文回覆示例 |
| `evaluator_key.json` | 評分者 | 相同答案的結構化版本；目前是語意人工評分，不是自動 scorer |
| `scores_template.csv` | 評分者 | 20 列記錄表 |
| `contract_snapshot.json` | 維護者 | 建立時 12 個 workflow 與 registry/policy 的 SHA-256，用於版本比較 |

**不要讓被測 agent 讀取整個測試目錄、EVALUATOR.md 或 evaluator_key.json。** 若 agent 可以搜尋 workspace，測試時應只暴露選定語言的 user 訊息與正常工具規格，把答案放在 runner 不提供給 agent 的區域。分檔本身不提供存取隔離。

## 執行方式

1. 每個 case、每種語言開新 session，共 20 個 session；避免另一語言或其他 case 的答案污染記憶。固定模型、temperature、正常 system prompt 和工具集，記錄 agent/registry 版本。
2. 每次只送 T1、T2、T3、T4 中的一輪，等待 agent 回覆後再送下一輪。不得一次送完四輪，不得讓 agent 提前看到未來線索。
3. 這是固定腳本測試：agent 的追問可由下一輪提供研究線索；沒有提供的檔案、樣本標籤或生物先驗仍屬 missing。若因輸入要求卡住，記錄卡住輪次和是否已合理辨識工具，不自行補入工具名或標準答案。
4. 保留每轮回覆、候選工具、規劃 action、tool calls、plan status 及轉向理由。工具選擇可以暫定；「尚需澄清」也可能是該輪正解。
5. 不輸入 `/execute`。本套沒有提供可執行資料，所以不要求 ready 或產生真實生物結果；正常的 read-only 工具／文件查詢可以發生。這裡測的是 intent、工具規劃、假設、契約與多輪狀態，不是 runtime 數值正確性。
6. 由評分者使用 EVALUATOR.md 的逐輪預期與 10 分規則評分。CSV 中 intent、algorithm、inputs、workflow、outputs 各填 0–2；critical_failure 填 yes/no；verdict 填 pass/partial/fail。只要 critical_failure=yes，verdict 必須 fail。
7. 分別報中文／英文通過數、雙語配對通過數（兩版皆通過）、五個面向平均分、首輪過早唯一選工具率與 critical failures。可重複多次估計穩定性，不以單次樣本當整體能力結論。

若另要測可執行的端到端 workflow，需另外準備不洩漏工具名稱的資料 bundle，經 agent 依內容辨識與驗證，確認後才授權執行；不要把本套「預期產物」當作已執行結果。本次沒有建立資料 fixtures 或執行模型。

## 情境覆蓋（僅供評分者）

| Case | 核心分辨 | 延伸／邊界 |
|---|---|---|
| 01 | PANDA / OTTER / GIRAFFE | aggregate → LIONESS-PANDA；拒絕複製共同網路 |
| 02 | PANDA / PUMA / DRAGON | miRNA priors → LIONESS-PUMA；不強制 miRNA abundance |
| 03 | GIRAFFE / LIONESS-PANDA | activity vs wiring；預後關聯不等於因果 |
| 04 | OTTER / PANDA / GIRAFFE | OTTER → export → CONDOR；regularization 不保證 sparsity |
| 05 | COBRA / PANDA / DRAGON | adjusted C → PANDA；混淆與 LIONESS 串接限制 |
| 06 | LIONESS-coexpression / BONOBO / COBRA | cohort contribution；共表現不等於調控 |
| 07 | BONOBO / LIONESS-coexpression / COBRA | 完整網路+pvalues；未 threshold／粒度不可偷換 |
| 08 | DRAGON / COBRA / PANDA | two-layer conditional association；拒絕三層與因果箭頭 |
| 09 | SAMBAR / CONDOR / PANDA | scores-only → patient clustering；突變分數不能當 GRN input |
| 10 | CONDOR / SAMBAR / DRAGON | 既有 edges 的社群；role collision 與內容推翻先前假設 |

工具名只出現在本 README 與評分檔，不出現在給 agent 的對話。演算法背景參考 [netZooPy 官方儲存庫](https://github.com/netZoo/netZooPy)，本 agent 能執行的能力以本地契約為準。

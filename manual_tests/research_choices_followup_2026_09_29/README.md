# 單一方法被誤拆成兩個假設：原因與修正

日期：2026-09-29。這次修正套用全部 12 個科學工作流。

## 主因

1. `explicit_research_choice` 的「假設／assumptions」線索只適合觸發語意檢查；上一版卻讓下游直接信任模型的 multiple_hypotheses 標記。詢問一個方法的結構假設，被當成提出多個競爭解釋。
2. 驗證只要求原文引文不同。使用者描述的「失敗現象」與「為何失敗」雖然是兩段原文，實際仍指向同一個 CONDOR 候選。回答迴圈以引文分組，於是重複輸出同一個工具。
3. 只要引文分組成立，router 就設為 ambiguous 並加上選擇題。因此不只正文重複，CLI 的 Next step 也要求使用者選擇。
4. 回答模板直接排列 assumptions、inputs、artifact 欄位；它列出方法性質，卻沒有先回應使用者想知道的失敗原因。先前驗證偏向正向的多假設案例，缺少「一句問題的不同部分其實不是多個候選」的反向案例。

## 已改進的行為

- **至少兩個不同、相容的候選，才呈現比較並詢問選擇。** 一個候選直接解釋；沒有候選就說明缺口。不支援的方向不算第二個工具。
- 模型即使錯拆同一問題，候選仍經程式去重。每個工具的完整說明只出現一次；真正不同的問題仍保留與工具的對應。
- 單候選的 decision、進度訊息、正文與 CLI Next step 同步，不再製造選擇題。舊路徑若將同一方法的兩種產出（如 GIRAFFE 活性與調控係數）拆開，也會合併成一次方法說明。
- 概念問題先解釋科學問題與方法的關係，再自然交代所需資料及結果。使用者明確要求參數、API、欄位等操作資訊時，仍保留規格型回答。
- CONDOR 案例先說明二分圖、虛無模型及投影的影響，再說明方法。結尾詢問原先使用的演算法、是否做過投影及權重是否帶符號，以協助診斷。
- 暫定候選也使用概念說明，但保留 fallback 的不確定性，不冒充精確匹配。曾讀取檔案的情況，不會錯誤宣稱「沒有檢查檔案」。
- 實測也發現 downstream 引文漏逗號會遺失「腫瘤分型」終點；現在只容許標點差異，保留文字與詞界，拒絕增字與改寫。

這裡的科學說明是可檢查的結構解釋，沒有把未見過的資料直接診斷為某個原因。一般 modularity 也可以校正 degree，不能僅憑 hubs 或巨型社群就推論所有傳統方法失效；二分圖方法也不保證生物學意義。核對來源：[Barber 原始論文](https://arxiv.org/html/0707.1616v3)、[CONDOR 官方文件](https://netzoo.github.io/netZooR/articles/CONDOR.html)。

## 驗證

- 完整測試：**2,745 passed，35 skipped**；略過的整合／容器測試並未執行。兩個既有 dependency deprecation warnings。
- 新增 **19 個回歸案例**：使用者原題、模型錯拆時的保護、全 12 工具單候選、共享候選去重、fallback 科學解釋、標點與增字證據區別、技術細節 opt-in、檔案檢查紀錄、舊路徑的相同方法合併。
- 最後一輪實際模型測試：**4/4 通過完整 evaluator**。中英 CONDOR 都是單一 exact 候選；原本 DNA／調控網路與 TF／miRNA 都仍為真正的多候選比較。模型為 `openai/gpt-4o-mini`，temperature 0。
- 舊有 8 個跨套件案例的模型輸出，用最終程式離線重播：**8/8**，另驗證不再出現 API 式標題。這是重播，不是新一輪 live。
- Ruff（24 個變更 Python 檔）及 `git diff --check` 通過。

第一次 live 有 2 個 evaluator failure：中文 CONDOR 進入 fallback 規格模板，中文分型引文漏逗號造成終點遺失。原始檔保留在 `initial-results.json`／`initial-trace.json`，未算作成功。修正後重播這份初次 trace，行為檢查為 4/4，但原始中文 fallback 仍不是 strict-routing success，詳見 `replay-checks.json`。後續 final live 的四例則都是完整 evaluator 成功，詳見 `checks.json`。

有限測試不代表模型對所有新問題都能完全理解。程式層的候選去重與選擇題門檻，不依賴模型剛好分類正確；其餘語意與證據仍須經既有驗證。未分析病患資料，未新增執行授權。

## 檔案與重跑

- `corrected-condor-answer.md`：最後 live 的原題回答，維持專案既有英文輸出設定。
- `cases.json`：中英原題與兩個真實多候選回歸題。
- `results.json`、`trace.json`、`checks.json`：最後 live 的完整結果。
- `replay-results.json`、`replay-checks.json`：初次失敗 trace 經修正後程式重播的結果。
- `full-test.log`：最終完整測試輸出。

```sh
# 檢查已保存的最後 live 結果，不呼叫模型
python manual_tests/research_choices_followup_2026_09_29/run_live.py
# 重播目前 trace（會覆蓋 replay 檔，不呼叫模型）
python manual_tests/research_choices_followup_2026_09_29/run_live.py --replay
# 明確開啟新的四例付費模型測試；只傳合成問題，覆蓋 live 檔
python manual_tests/research_choices_followup_2026_09_29/run_live.py --live
```

Codebase Memory MCP 在本 session 未提供，採精確來源檔與測試驗證，未宣稱完成 graph 刷新。

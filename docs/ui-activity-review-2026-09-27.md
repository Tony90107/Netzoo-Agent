# Activity / Log review — 2026-09-27

## 檢查結論

上一版 Log 將對話、workflow 與內部 routing / node / token 事件全部放在同一層，閱讀用途與除錯用途沒有區分；Timeline 則把整次執行的 CLI Session 與細部節點並列，也沒有明確的日期、時區與 Run 邊界。

時間有一項實際缺陷：trace 使用 `occurred_at`，Agent 訊息卻在前端接收時呼叫現在時間。WebSocket 補播舊訊息後，訊息可能顯示在現在，與原始 trace 分離。已新增 worker 訊息的 UTC 原始時間，supervisor 保留它於 replay buffer，前端優先使用原始時間。舊版訊息沒有原始時間時，明確標示 **Received time**，不能回推真實發生時間。

原始 trace 時區轉換本身正常。例如最新紀錄中的 `2026-09-26T16:11:08.599212Z` 在台灣是 `2026-09-27 00:11:08.599`。統一使用本機時區、24 小時制與毫秒，並顯示日期和 `Asia/Taipei` 等時區名稱。階段耗時仍採原本的 `duration_ms`；Run 的 elapsed 使用原始起訖時間，包含中間等待使用者的時間。

## 已完成調整

- Activity 預設為 Timeline，按真正 `run_id` 分組。舊 Run 收起，最新 Run 展開，顯示開始、結束、狀態與 elapsed。
- 修正 Run 已恢復／結束，但舊階段仍顯示 Waiting 的狀態殘留。
- Timeline 例行 policy / memory 階段收進 System stages；若階段失敗，仍直接顯示。執行階段使用工具名稱，區分 Inspect input data 與 Run LIONESS-PUMA。
- Log 預設 **Highlights**，包含使用者操作、Agent 訊息、Run 起訖、計畫、工具、結果與錯誤。內部 routing / node / token 等事件在 **All events** 可讀取，並保留於資料中。
- 日誌標題改為可讀名稱；原始事件名稱、run ID、sequence 與 payload 留在 Technical details，All events 也顯示原始事件名稱。
- 長回覆先顯示摘要，可展開全文；較大的字級、行距與分隔減少資訊擠在一起。
- 搜尋保持可用，Source / Status / Run 篩選及 Copy / Export 移到 Filters and export。單一 Run 篩選限定該 Run 的執行事件；對話訊息在 All runs and messages 查看。
- Follow latest 預設追蹤最新紀錄；向上捲動或改變篩選會暫停，重新勾選即可繼續。篩選後回到第一筆符合紀錄。
- 匯出包含目前篩選範圍內所有已接收紀錄，包含原始時間、時區、事件資訊；選 All events 才會匯出完整細節。不是原本 hash-chain audit archive 的替代品。

## 驗證

- 最新四次已保存的 Run 共 182 筆 trace，Highlights 顯示 39 筆，143 筆內部事件隱藏但可切換查看。
- 回放只讀既有 JSONL，沒有重新跑 workflow、呼叫模型或啟動使用者 daemon。
- 340 px 窄面板與較寬的 Activity 畫面檢查日期、時區、折疊、失敗篩選和自動追蹤。
- 前端 61 個測試通過；Python driver / supervisor / UI contract 48 個相關測試通過。涵蓋訊息補播時間、跨午夜的台灣日期、重要事件篩選、完整匯出及多 Run 分組。
- TypeScript / Vite 與 Tauri macOS 正式建置完成。

## 使用新版

關閉舊 app 後，開啟專案中的 `desktop/src-tauri/target/release/bundle/macos/NetZoo Agent.app`。重新啟動會讓 daemon 載入新版 Python 訊息時間處理。既有舊訊息的真實時間無法補造；原始 trace 時間保持不變。

## 後續優先順序

1. **歷史 Activity 回看**：在舊 session 畫面讀取保存的 Run，讓重新開啟後也能檢查執行歷程。
2. **Run 結果摘要**：將輸入、參數、軟體版本、成功／失敗原因與產物入口集中於同一份摘要，方便報告與重現。
3. **錯誤修復入口**：將工具的具體錯誤、影響的輸入欄位及可行修復方式放在失敗階段，減少閱讀整份 payload。

先改善這三項，避免持續增加頁面與按鈕，使介面再次變得密集。

## 索引維護

再次嘗試 full / persistence 重建 Codebase Memory，仍因既有 generation 衝突被服務拒絕。現有圖譜不能視為包含此次修改；來源、測試與正式建置已直接驗證。

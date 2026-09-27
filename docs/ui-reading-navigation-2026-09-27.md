# 紀錄閱讀、搜尋與返回流程

這次延續歷史 Activity／結果／時區功能，處理搜尋區字體跑版與 Log 難讀，並補上歷史查找及閱讀配置。

## 使用方式

- Sessions 新增 Search sessions，依原始請求、workflow 或 session ID 搜尋；Latest saved state 可篩選待輸入、待批准、成功、失敗與僅預覽。Load older sessions 分頁讀取更早的對話，搜尋涵蓋完整保存紀錄，不只目前載入的前 60 筆。
- 搜尋和狀態選單改為上下排列，標籤 11px、輸入 12px，套用應用程式字體並限制寬度。macOS 搜尋框與選單不再繼承過大的字級。
- 上方標示 Current session 或 Saved session / Read only，避免把歷史紀錄與即時 Plan 混淆。Layout 提供 Automatic、Focus view、Show inspector，偏好存在本機；Automatic 在歷史／Activity／輸出閱讀時收起右欄，對話時顯示。
- Log 新增連續垂直時間線，依日期分段，用節點區別使用者、工具、一般事件、執行開始／結束與警告／錯誤；文字標籤同時保留，避免只靠顏色判讀。錯誤保持紅色，警告黃色，正常事件維持中性色。
- Highlights 只呈現重要事件；原始 event type、序號與 JSON 放在 Technical details，需要時展開。Run 選單直接可用，其他篩選及匯出預設收合。
- Log 的 Run 選單以英文標出 workflow／活動類型、結果、run 次序與短 ID，例如 “Advice only · Completed” 和 “LIONESS-PUMA · Failed”，方便分辨同一對話裡不同目的的執行。
- Log 控制列與歷史 run 選單改為緊湊排列，次要說明收合；進階控制展開時可捲動，保留事件區空間。1280×720 的歷史 Log 畫面，事件區由約 40px 增加至約 234px。
- Preview output 可返回原本的 Activity 或對話。歷史預覽保留選取的 run 和目前分頁；即時閱讀保留 Activity 狀態，切換另一個工作區分頁時清掉不適用的返回提示。

## 資料語意

- Sessions 的狀態採用保存的 evaluation／工具結果；plan ready 不等於正式執行成功。待輸入與待批准狀態優先，成功的 dry run 顯示 Preview only。
- 新增 GET `/v1/history` 的 query、status、offset 參數與 has_more／next_offset；仍需 bearer 驗證，仍讀取現有 checkpoint。先篩選再分頁，搜尋不建立或恢復 worker。
- 請求切換時取消舊讀取、忽略晚到回應；執行狀態改變後回到第一頁更新紀錄。讀取失敗有明確訊息與 refresh 重試。
- 最新保存狀態只描述 checkpoint；每次執行的結果仍以 Activity 裡的個別 run 判讀。輸出預覽仍讀目前檔案，沒有新增歷史輸出快照。

## 驗證與交付

- 前端 78 tests passed，涵蓋歷史搜尋、較早分頁、晚到回應、刷新失敗重試、StrictMode 啟動、歷史及即時輸出返回、閱讀配置保存、日期與事件順序、原始內容收合及匯出。
- Python 選定的 history search / saved activity / server supervisor / server driver / environment UI 測試 61 passed，file browsing 回歸測試 28 passed，合計 89 passed。
- TypeScript / Vite production build 與 Tauri macOS App 打包通過。
- 實際完整 App 檢查使用本機獨立測試頁；即時 session 為假資料，歷史／檔案使用真正的只讀 API。讀取 `248a44d4` 的成功與失敗 run，確認時間線、具體物種／identifier 修復提示、輸出預覽與返回同一 run。沒有執行科學分析。
- 測量最窄 170px 側欄：搜尋框寬 146px、字級 12px、右緣 158px，位於側欄範圍內；一般 240px 側欄同樣沒有溢出。
- 新版 App 位置：`desktop/src-tauri/target/release/bundle/macos/NetZoo Agent.app`，關閉舊版再開此版本以載入更新。未替換 `/Applications` 版本。
- 暫時測試頁、UI fixture 與本次啟動的服務已清理，既有開發服務未停止。

Codebase Memory generation 仍為 `2026-09-21T13:19:20Z`。已對本次檔案做 coverage 檢查並直接讀取改動／尚未追蹤的來源。依 AGENTS 要求嘗試 full + persistence rebuild，worker 仍回報 `a pre-coordination or unverified CBM generation is active`；本次結論依當前原始碼與測試，沒有宣稱索引已更新。

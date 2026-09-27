# NetZoo Agent UI completion — 2026-09-26

本次依教授的八項紀錄補強現有 React / Tauri 桌面介面。保留專案的英文產品文字，採用「工作區分頁 + 右側 Work Plan / Run activity」架構。

## 需求與完成項目

| 教授紀錄 | 現在的操作方式 |
| --- | --- |
| Slash command 檢查 Docker / image | Conversation 的 `/doctor` 按鈕與指令檢查容器內環境；Environment 頁另外由桌面 shell 檢查主機 Docker CLI、engine、Compose 與 compose 設定的 image。啟動失敗畫面也能開啟環境檢查。 |
| 工具使用說明、輸入／輸出、GitHub | Method guide 可搜尋十種 NetZooPy 方法與五項 Agent 工具；展開可讀用途、輸入、輸出及存取說明，附官方文件與固定版本原始碼連結。說明目前不需要連接 GitHub 帳號；image build 讀取公開的 netZoo/netZooPy repository。 |
| Render Markdown | 即時對話、提問與已儲存的 Agent 回覆支援標題、清單、GFM 表格、程式碼與連結。Raw HTML 不執行。桌面連結透過指定 IPC 在系統瀏覽器開啟。 |
| Outputs 分頁、lazy loading / buffer | 獨立 Outputs 頁先取檔案中繼資料，每頁 100 個項目；點選後才讀內容。表格每頁最多 200 列、50 欄，文字每頁最多約 200 KB；前後頁使用 byte cursor，保留 CSV quoted newline 與 UTF-8 字元邊界。版本檢查防止改寫中的檔案被拼成錯誤結果。 |
| 執行 Log | Run activity 的 Log 與 Activity 主畫面提供時間、來源、階段／事件、工具名稱、詳細 payload，支援搜尋、來源／狀態篩選、複製及文字／JSON 匯出。畫面每次最多渲染 200 筆；匯出包含所有符合篩選的已接收紀錄。 |
| GitLens 類型 timeline | 按真實 node 執行次序分段，同一個 node 重跑會是新階段；可展開事件、耗時、tokens、參數與輸出，並直接開啟 outputs/ 內的 artifact。 |
| 執行錯誤紅字 | `error.recorded`、工具回傳 failed、result evaluation failed、run failed 都標紅；warning / replan 使用黃色，其他事件保留中性色。Waiting / Interrupted 與 Completed 分開顯示。 |
| highlight 使用者 | 訊息、模式切換、執行確認／拒絕與中斷要求皆有時間與獨立 You 標示；確認與 command 另有文字標籤。 |

## 實作邊界

- Python daemon 的 HTTP endpoint 仍要求 bearer token；檔案讀取仍限 outputs/，拒絕外部 symlink 與路徑穿越。
- 環境檢查為唯讀，不 build、pull image、不執行 analysis。模組存在不代表所有依賴可運行；每次分析仍通過 input validation 與 Plan Evaluator。
- 主機檢查在 Tauri 執行；一般瀏覽器會明確顯示 unknown。單次 Docker 查詢有 8 秒上限。
- Log 匯出在桌面存至 Downloads，使用新檔名避免覆寫；一般瀏覽器使用下載。UI 匯出的 trace 是閱讀用紀錄，並非完整的 hash-chain audit archive；保留原本的 trace archive 功能。
- Log 包含目前畫面已接收到的事件與訊息。若 reconnect 缺失事件，畫面與 JSON / text 匯出都標註 incomplete。Agent 訊息時間為前端接收時間，trace 使用原事件時間；舊 checkpoint 的訊息沒有補造原始時間。
- 不支援的 binary 檔案會顯示無預覽；超寬矩陣僅預覽前 50 欄，原始輸出不變。過大的單一 CSV / TSV record 會顯示改用專用資料檢視器的建議。
- 修正 React StrictMode / 重試時重複連線與過期回應更新現有 session 的問題。

## 驗證

- 前端 TypeScript / Vite 正式建置成功，Vitest 53 個測試通過。
- Python 87 個相關測試通過，涵蓋檔案分頁、quoted CSV newline、UTF-8、版本變更、路徑隔離、環境修復說明、API token 與執行授權。
- Rust 7 個原生指令測試通過：環境查詢唯讀、Compose image 設定、非 HTTP URL 拒絕、匯出格式與大小限制。
- 隔離的瀏覽器 UI fixture 檢查 Markdown、方法搜尋、450 列資料分為 200 / 200 / 50 列、Log 篩選、警告與失敗狀態、環境檢查畫面及重複連線修正。fixture 未執行生物分析，也未呼叫模型。

## 索引維護狀態

已嘗試以 full / persistence 重建 Codebase Memory，但服務拒絕啟動 index worker，理由為 `a pre-coordination or unverified CBM generation is active`。現有圖譜雖回報 ready，不能視為已包含此次變更；需先由 MCP 服務管理端排除既有 generation 衝突，再重新索引。本次程式碼已用直接讀取來源、測試與正式建置驗證。

## 使用新版

新版 macOS bundle 位於 `desktop/src-tauri/target/release/bundle/macos/NetZoo Agent.app`。關閉舊版後，在專案路徑啟動新版；若從其他目錄啟動，設定 `NETZOO_PROJECT_ROOT` 指向包含 `docker-compose.yml` 的目錄。此次沒有覆寫 `/Applications/NetZoo Agent.app`。

若使用開發模式，於 `desktop/` 執行 `npm run tauri dev`；終端需可找到 Cargo。重新開啟桌面 app 會以新的 launch token 啟動／重建 daemon container，載入掛載工作區中的新版 server。

科學方法摘要參考 [NetZooPy 官方文件](https://netzoopy.readthedocs.io/en/latest/)；實際 API、所需欄位與輸出以固定版本程式碼、Python workflow registry 及每次 Work Plan 為準。

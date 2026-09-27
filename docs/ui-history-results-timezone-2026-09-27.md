# 歷史 Activity、結果摘要、修復提示與時區

## 使用方式

- 在 Sessions 選擇舊對話，再切換 Activity；預設顯示最新一次執行的 Results。Saved run 可選另一筆紀錄，Timeline / Log 可查看流程與詳細事件。
- 即時 Activity 也新增 Results：區分一般對話、輸入檢查、dry run、正式分析，顯示耗時、tokens、工具結果、輸出路徑數量、重要數值與警告。
- 成功工具記錄的 outputs 路徑可以 Preview output；dry run 只顯示預計路徑，不當成已產生檔案。
- 工具失敗時顯示 Suggested repair，完整錯誤與警告保留在可展開區域。提示涵蓋物種、基因識別碼、路徑、Docker、依賴、權限、記憶體、格式、矩陣相容性與連線問題。未知原因顯示一般檢查步驟，不自行推測確切根因；提示不會執行修復或繞過科學驗證。
- Settings → Display time → Time zone · country / city，提供常用國家城市、其他 IANA 時區及 Follow system。偏好保存在本機，所有已開啟的 Activity / Log / 檔案時間同步更新；夏令時間交由 Intl 處理，UTC 原始事件不變。
- 複製或文字匯出使用所選時區，並保留原始時間。JSON 保留原始事件時間，另記錄顯示時區與 incomplete 標記。

## 資料來源與限制

- 歷史執行從 `.netzoo/traces/<run UUID>/manifest.json` 的 session_id 關聯，不能由目錄名稱推測對話歸屬。
- 新增 authenticated GET `/v1/history/{session_id}/activity`，只列 manifest，每頁預設 50 筆；GET `/v1/history/{session_id}/activity/{run_id}` 每頁最多 200 個事件。先選 run 才讀事件；不建立 worker、不恢復 session、不修改 journal。
- 逐段驗證事件型別、run ID、sequence、previous hash 與 event hash；最後核對 manifest。分頁使用 sequence/hash 版本，紀錄變動時要求重新讀取。損毀資料只顯示通過驗證的前段並標示 incomplete。
- 單筆事件最多 2 MiB，單個 run 預覽最多 64 MiB；超過限制會明確提示。只接受配置 trace root 中的正常檔案，拒絕越界、錯誤 UUID、symlink 與跨 session run 存取。
- 沒有保存 trace、或 trace 已依保留政策刪除的舊對話，無法補造歷史 Activity。未 sealed 的紀錄標示未完成，載入期間與缺損資料的匯出均標示不完整。
- 原始 checkpoint 的對話沒有完整訊息時間，因此歷史 Activity 顯示 trace 事件；不替舊對話製造時間戳。
- 輸出路徑是當時的紀錄，預覽讀目前檔案。此變更不建立歷史輸出快照；檔案可能已改寫或刪除。
- 國家可能有多個時區，因此採國家／城市而非固定國家 UTC 偏移。其他地區透過瀏覽器提供的 IANA 時區清單選擇。

## 驗證

- Frontend：71 tests passed，包含歷史分頁、只讀所選 run、快速切換的晚到回應、舊對話無 trace、dry run 不誤開輸出、修復提示、UTC 跨日、夏令時間、偏好保存與匯出原始時間。
- Python：57 tests passed（saved activity、server supervisor、server driver、environment UI），涵蓋 bearer auth、session 隔離、頁面上限、hash 篡改、截斷、多餘事件、symlink、大小限制與不修改紀錄。
- TypeScript / Vite production build 與 Tauri macOS `.app` build 成功。
- 實際 UI：只讀既有 `248a44d4` 對話的 4 個 run。確認成功分析有 2 個輸出、失敗分析有 5 項具體驗證錯誤、Log 隱藏例行內部事件、輸出可直接預覽。台北 27 Sept 00:12 切紐約變 26 Sept 12:12；Activity 與 Log 一致。確認寬畫面與 340px 窄欄可換行且無橫向擠出。
- 暫時檢查頁、測試 API 與 Vite server 已清理。未重新執行科學分析。

## 交付

新版位置：`desktop/src-tauri/target/release/bundle/macos/NetZoo Agent.app`。關閉舊版後開啟此版本，以重新載入前端與 daemon；未替換 `/Applications` 裡的 App。

Codebase Memory 原索引 generation 為 `2026-09-21T13:19:20Z`。本次按 AGENTS 指示嘗試 full/persistence rebuild，服務仍回報 `a pre-coordination or unverified CBM generation is active`。因此以當前原始碼與測試驗證新增功能；沒有宣稱索引已更新，也沒有停止其他工作使用的 MCP process。

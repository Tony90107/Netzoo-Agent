# 選項選單、精簡回覆與以 session 管理實驗 — 2026-09-30

本次依使用者的需求清單補強桌面版與終端版。所有使用者可見的 agent 文字仍為英文；
routing、prompt、schema、policy 皆未改（見研究紀錄 Log 287）。

## 需求與完成項目

| 需求 | 現在的操作方式 |
| --- | --- |
| 多個選項時跳出選單，附「對你的任務有什麼好處」、依有效程度排序 | 回覆下方出現選項面板（類 Claude Code／Codex）：標題列、問題、編號選項，每個選項一行重點（好處 · 是否吻合你要的 · 何時選 · 還缺什麼）。有引文依據的推薦標 **Recommended**；唯一吻合所有 typed 維度的標 **Best match**；面板寫出排序依據。↑↓ 移動、Enter 或數字鍵選擇。清單最後一列固定是「Type your own answer」：點它、按它的數字或直接開始打字，那一列就變成輸入框；Enter 送出、Shift+Enter 換行、Esc 回到選項（草稿保留）。送出的文字和下方輸入框一樣處理，agent 會連同上一個請求一起理解，不會因此授權執行。卡片的 `allow_other` 為 false 時不顯示這列。 |
| 輸出太冗長，重點多一點 | 每則回覆先顯示「卡片」：類型標籤、一句結論、2–5 條重點、「此 agent 無法執行的相關項目」；完整說明收在「Full explanation」可展開，內容一字未改。 |
| 統一輸出模板、條列 | 所有回覆類型（方法選擇、澄清、多讀法、多假設、能力缺口、單一 workflow、計畫就緒、執行完成／失敗、無法解讀）共用同一種卡片。 |
| 正確渲染 Markdown | 修正：泡泡的 `white-space: pre-wrap` 把 Markdown 區塊之間的換行印成空白行（清單與表格都被拉開）。改由渲染器保留作者寫的單一換行。終端版也把 Markdown 轉成終端樣式（粗體、清單符號、程式碼上色）。 |
| 互動內容用彈出視窗或選單 | 選項面板、下一步按鈕列、「New session」對話框（名稱、模型與 tag）、Notes 對話框。 |
| 明確告知相關但無法執行的任務 | 卡片與選單都有「Related, but not available in this agent」：例如無法下載的網路、netZooR 才有的方法（TIGER）、NetZoo 外的分群步驟、沒有 workflow 的讀法，各附原因。 |
| 清楚的下一步操作 | 「Next」列：Execute this plan（仍停在原本的兩段式核准）、Plan X with my data、Compare with …、Open the outputs、Check the environment、Start a new task。 |
| 一個 session 對應一個模型 | 建立 session 時選模型（清單來自 daemon allowlist，只能縮小不能放寬）；session 記錄它的模型，resume 時沿用（仍須在 allowlist 內）。標題列與 session 列表都顯示模型。桌面版 Resume 沿用原本的 session id（與終端版 `--resume` 相同）：名稱、筆記、tag、輸出資料夾都延續；該 session 的 worker 還在執行時直接接回。先前桌面版 Resume 會開新的 id，舊的 tag 與輸出資料夾跟不過去。 |
| 輸出只屬於該 session | 沒有指定輸出路徑時，預設寫到 `outputs/sessions/<session id>/`。先前多個 session 都寫同一個 `outputs/demo/puma-aggregate.tsv`，後者覆蓋前者。明確路徑與已確認的偏好仍優先。 |
| 從結果快速跳回 session | Outputs 預覽上方顯示「From session …」並可點回該 session；若同一路徑曾被多個 session 寫過，會標示目前檔案是最新一次的版本。 |
| session tag、方便找與比較 | 標題列、session 檢視、新 session 對話框都能加 tag；列表可依 tag 篩選，搜尋也涵蓋 tag；「compare」可勾 2–4 個 session 並排比較 workflow、結果、模型、輸入、輸出、tag、token，不同的列會標色。有 tag 的 session 視同具名 session，不會被 30 天例行清理刪除。tag 是自己取的短標籤（每個 session 最多 12 個、每個 ≤48 字，可用中英文、數字、空白與 `. + / -`），只給人整理用，agent 不會讀取；Sessions 的 Tag 篩選在有任何 tag 之後才出現。tag 可寫成欄位 `key:value`（例：`dataset:batch-2`、`hypothesis:dna-damage`）：key 存成小寫，同一欄位每個 session 只有一個值（新值取代舊值）；Tag 篩選依欄位分組，Compare 每個欄位一列、值不同的列標色。 |
| 可改 session 名稱 | 標題列與 session 檢視點名稱即可就地修改（Enter 或離開欄位儲存、Esc 取消）；列表與 Compare 以名稱為主、原本的請求顯示在下方；搜尋涵蓋名稱。 |
| 每個 session 的筆記 | 標題列「Notes」開啟對話框，session 檢視有筆記欄；記錄目的、資料版本與結論（≤4000 字，⌘Enter 儲存）；列表標示有筆記的 session，Compare 並排顯示；搜尋涵蓋筆記。 |
| 名稱、筆記與 tag 的保留 | 有名稱、筆記或 tag 的 session 視同具名 session，不會被 30 天例行清理刪除（仍有硬性上限）。 |

## 終端版（`./netzoo-chat`）

- 互動終端預設顯示卡片重點與方向鍵選單；`/details` 顯示完整回覆；`--full-replies` 恢復逐字全文。
- 輸入數字、方向鍵加 Enter、或直接打字皆可。管線、非 tty 與測試錄製的輸出與先前逐字相同（13 個 golden transcript 未變）。

## 設計邊界

- 卡片只由同一個 typed decision 與 registry 推出；每個選項指名的 workflow 都出現在原回覆文字中（1777 個錄下決策重播，0 例外）。
- 選項只送出 machine 本來就接受的文字，不新增執行授權；任何會執行的步驟仍需 `/execute` 與明確核准。
- 選項的信任檢查：選到的 workflow 必須是上一輪 decision 的候選或其 continuation／alternative。
- 名稱、筆記、tag、模型、卡片存在 `.netzoo/session_meta/<id>.json`，不寫入 checkpoint，也不會送給 agent。

## 使用新版

- 關閉舊 App，開啟 `desktop/src-tauri/target/release/bundle/macos/NetZoo Agent.app`（重新啟動會載入新版 daemon）。
- 開發模式：於 `desktop/` 執行 `npm run tauri dev`。

## 驗證

- 後端 pytest 全數通過；前端 vitest 94 個通過；TypeScript 與 Vite production build 通過。
- 以隔離的 daemon 容器（獨立 `.netzoo/`、`outputs/`，不動使用者紀錄）實機操作：方法選擇面板與鍵盤選擇、選擇後自動說明所選方法、
  New session 對話框（模型＋tag）、Synthetic test 模式下實跑 PANDA toy（輸出寫到 `outputs/sessions/<id>/`）、
  從輸出預覽跳回 session、兩個 session 並排比較。
- 終端版以 PTY 驗收：精簡卡片 → 方向鍵選 OTTER → 下一輪說明 → `/details` 顯示全文。

# 桌面版介面圖

擷取自實際執行中的 `NetZoo Agent.app`（macOS，Retina 2×，PNG）。
每一張都是一次真實 PANDA 執行的中間狀態，不是模擬畫面。

擷取條件：

| 項目 | 值 |
|---|---|
| 資料 | `data/official-toy/` 的 netZooPy 官方 toy data |
| 模型 | `openai/gpt-4o-mini`（response / router / semantic 三者相同） |
| 模式 | Synthetic Test（toy data 內含已淘汰的 gene symbol，嚴格模式會被 gate 擋下） |
| 產出 | `outputs/demo/ToyExpressionData-panda.tsv`，3,113,777 bytes |

| 檔案 | 畫面 | 論文可引用的內容 |
|---|---|---|
| `ui-01-startup.png` | 啟動後的空狀態 | 四個面板的資訊架構；sessions 列表與 token 計數 |
| `ui-02-synthetic-test-mode.png` | 切到 Synthetic Test 模式 | 模式切換是 UI 控制項而非輸入指令；模式本身印出「結果僅供軟體測試，不是生物學證據」 |
| `ui-03-plan-evidence-timeline.png` | 計畫就緒 | Plan 面板的 evidence 表（每個輸入標註來源「you gave it」）；Timeline 68 個事件，逐節點耗時與 token 數 |
| `ui-04-dry-run-and-outputs.png` | Dry run 與結果瀏覽 | 執行前的驗證數據：expression 1000 genes × 50 samples、motif targets ↔ expression genes 913/913、motif TFs ↔ PPI TFs 87/87；Outputs 面板導覽進 `outputs / demo` |
| `ui-05-output-preview.png` | 結果檔預覽 | 不載入整個檔案就能看內容；顯示主機端絕對路徑 |

## 缺一張

**兩階段核准卡**（「Run the validated PANDA workflow now? / Execute this plan / Cancel」）
沒有原生視窗的截圖。這個畫面確實存在且運作正常——在這次工作中已於瀏覽器驅動的
同一個 daemon 上驗證過——但自動化擷取它需要對視窗送出文字輸入，而合成鍵盤事件
會送給當下最前景的應用程式，不保證是這個視窗。要補這一張，手動操作一次最快：
送出請求 → 計畫就緒後按「Review and execute this plan」→ 截圖。

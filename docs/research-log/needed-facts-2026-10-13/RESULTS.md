# 判定層第 2 步：使用者說「不知道」的資料性質（2026-10-13）

程式：aacebd4（本地提交，這份結果寫完後推上 GitHub）。

## 讀取量測

`premeasure.py`：只跑能力檢查（免費模型），每題 1 次，題目都已看過。
- 有「不知道」的 8 題：8/8 讀對，維度也都歸對。
- 已決定的對照 7 題：0 題誤讀。
- 程式判為關鍵的 5/8。B23、F49 是 miRNA 輸入問題，改由資料需求計畫詢問。B30 沒有對到任何 workflow，無從判斷。

## 實跑

`outputs/needed-facts-check-2026-10-13/`：完整流程，每題 1 次，共 15 個 session。

| 題 | 結果 |
|---|---|
| B03（網路的節點角色） | 改為追問；說明「調控者–基因 → CONDOR；基因–基因 → 沒有」，只問一個問題 |
| B10（單細胞或 bulk） | 改為追問；說明「bulk → LIONESS-COEXPRESSION／BONOBO；單細胞 → 沒有」 |
| B18（兩份資料是否同一批病人） | 改為追問；說明「同一批 → DRAGON；不同 → 沒有」 |
| F41（「不知道兩張表的欄位順序是否一致」） | 改為追問，但問偏了。模型把「順序」歸成「是否同一批樣本」；DRAGON 依樣本 ID 自動對齊，真正該問的是樣本 ID 和檔案 |
| B23（prior 是否含 miRNA） | 資料需求計畫加了引用原話的詢問；回覆裡另一段已問「Do you also have a miRNA list?」，所以這段不重複顯示 |
| F46（中文） | 這次模型沒有把「請跑 CONDOR」對到 CONDOR，判為整題做不到，沒有候選可比較 |
| B30 | 沒有對到 DRAGON，判為整題做不到（讀取的限制） |
| F49 | routing 走到「研究假設比較」，回覆是一長串方法（既有的 G5 問題） |
| 對照 7 題 | 0 題讀出「不知道」，回覆照常；B21 STRING 下載照常進入 needs_input |

## 結論

- 保留並推上 GitHub。
- 同一批題目先前 0/8 有追問；這次 3 題完全正確、2 題部分正確，對照題沒有任何變化。

## 尚未處理

- 讀取對到 0 個 workflow 時，無從判斷（F46、B30）。
- 「欄位順序」被歸到「是否同一批樣本」（F41）。
- 使用者列出「結果選項」的情形（open choice）仍未處理。

# 判定層第 2b 步：使用者還沒決定要哪種結果（2026-10-13）

程式：cc522fb。

## 讀取量測

`premeasure_choices.py`，只跑能力檢查，每題 1 次。
- 結果選擇 10 題：7 題觸發。
  - B04：沒有把任何 workflow 對到選項。
  - B11：讀成兩項需求，沒有讀成一個選擇。
  - B14：解析失敗。
- 對照 5 題：0 題觸發。Log 416 的兩題方法問題（LIONESS／BONOBO、PANDA／OTTER）都被標為 method。
- 量測時發現 F37 的同一句話也被讀成「組學層數不明」。已修正：與結果選擇原文重疊的「不知道」不另外追問。

## 實跑

`outputs/result-choices-check-2026-10-13/`，完整流程，每題 1 次，共 15 個 session。

| 題 | 結果 |
|---|---|
| F43 | 追問："if their activity: GIRAFFE; if their network wiring: LIONESS-PANDA"。另多出一行「Help me choose ...」標為 not matched |
| F37 | 追問：TF regulation → LIONESS-PANDA；gene-gene coexpression → LIONESS-COEXPRESSION 或 BONOBO |
| B08 | 追問：DRAGON 或 LIONESS-DRAGON |
| B14 | 追問：PANDA 或 SAMBAR |
| B29 | 追問：aggregate → PANDA、OTTER、LIONESS-PANDA；per sample → LIONESS-PANDA |
| B22 | 沒觸發：模型把一個選擇拆成兩個各只有一個選項的選擇；同一題在讀取量測時是讀對的 |
| B11 | 沒觸發：讀成兩項都做得到的需求 |
| B02 | 能力檢查失敗，改用備援，依設計不採取行動 |
| B04、B19 | 路由階段 gpt-4o-mini 解析失敗 |
| XM1、XM2 | 被標為方法問題，回覆和原本相同（BONOBO 推薦；PANDA／OTTER 平手） |
| XC6、B12、B25 | 正常 |

## 結論

- 保留，推上 GitHub。
- 讀取正常的 7 題中，5 題回覆完全正確；對照題沒有任何變化。
- 沒有為 B22 這種讀取錯誤加合併規則，避免針對讀取錯誤補洞。

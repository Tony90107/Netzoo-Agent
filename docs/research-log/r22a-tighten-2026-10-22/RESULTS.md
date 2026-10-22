# R22-A 收緊（2026-10-22）

起點 `c5204069`。ROUND-24 的 held-out h5 中，R22-A 誤拒了 Q13-2。使用者給了邊列表檔，但讀題在輸出資料夾的子句「write the communities to condor_psoriasis/」上標了「沒有現成網路」。

## 修改（`ruled_out.without_unbuilt_network`）

- **讀題標的「沒有現成網路」**，只在「包含使用者點名該 workflow 的那一列」才採用。依位置判斷、區分大小寫，所以 `condor_psoriasis/` 不算點名。
- **使用者自己的話**，對該請求的每一列都有效，包括：
  - 明說沒有網路（`ruled_out`）；
  - 「只有某些資料」的陳述裡沒有網路，例如 C18「just this expression table」。

## 量測（`measure.py`，$0）

| 範圍 | 結果 |
|---|---|
| h5 的 96 份 live 紀錄重放 | 65 → 66：**Q13-2 修好** |
| 看過的 757 份有金標讀取 | 638 → 637：**C18 p3 改壞** |

- **C18 p3 改壞的原因：** 這次讀題完全沒讀到使用者說的「I don't have any motif or PPI files, just this expression table」，既沒有 `ruled_out`，也沒有「只有」。CONDOR 那一列又只是子句「to get gene communities」。它原本是靠和 Q13-2 同一個不可靠的訊號擋下的。
- **兩題結構相同，現有的型別欄位分不開。** 收緊後整體淨 0，但只依賴可靠的訊號，而且是新題決定了方向。C18 p3 列為讀題錯誤。

## 同一輪順帶修正：單層輸出資料夾被當成「傳送」

- **缺陷：** `_names_a_folder` 不認得「glioma_out/」這種只有一層、結尾帶斜線的資料夾，因為 `_DIRECTORY_TOKEN` 要求至少兩層。
- **影響：** 讀題把「Outputs can go to glioma_out/」標成 delivery 時，程式沒有把它排除，於是能做的執行被判為「傳送，做不到」。
- **修正：** 加一個依形狀判斷的單層資料夾樣式（`_FOLDER_TOKEN`）。網址與 e-mail 仍是傳送。
- **量測：**
  - h5 重放 66 → 68：Q37 兩次都修好；
  - 看過的題目 637 不變，改壞 0；
  - 測試 4,922 全過。
- **Q13-1 沒有因此修好：** 這次讀題把每一句都當背景，完全沒讀出要做的事，routing 再判 unsupported。屬於讀題錯誤。

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

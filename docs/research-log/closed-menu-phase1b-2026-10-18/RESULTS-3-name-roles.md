# 第 1b 階段第 3 步：讓 context_mentions 真的被填（2026-10-18）

## 結論

- 舊形狀是一個「只當背景提到的方法」清單，第 1 階段 56 題 × 2 次讀取從來沒有填過（0/4）。
- **新形狀**：
  - 程式先用 `workflows_in` 找出原文裡的每個註冊名稱，每個名字在 schema 裡各一個欄位，模型給它一個角色：
    - target：要跑或要問的；
    - choice：在幾個之間選的其中一個；
    - background：只當背景，例如之前的分析、輸入的來源。
  - background 的名字進入 `context_mentions`，計算點名的 workflow 時排除；名字仍由程式數。
- 開發集 d8：43 次讀取有名字，全部被標成 target。開發集裡沒有只當背景提到的方法，所以量不到效果。
- 第 1 階段離線把金標的 context_mentions 放回去，判定不變（C44、C58 錯在別處）。這一步主要是讓欄位能被填，效果在第 6 步看。

## 檔案

- `menu_reader.py`：`Layout.names`、`name_key`、`NamesWire`。
- 測試：`test_names_found_by_code_get_roles_and_background_ones_are_not_counted`（PANDA 為 target、COBRA 為 background → 只跑 PANDA）。

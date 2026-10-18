# 第 1b 階段第 4 步：聚焦重讀加入「候選都沒有的設定」（2026-10-18）

## 結論

- 第 1 階段的 C08（GIRAFFE 沒有任何 control）：學習率、迭代次數這類設定，聚焦重讀沒有欄位可放，所以誤承諾。
- 聚焦重讀加了 `unsupported_settings`：使用者要求、但候選 workflow 都沒有的設定，附逐字引文與「是要用來跑，還是只在描述資料」。合併後是一條 `unregistered` 設定，成為不能做的正面理由。
- **開發集 d8 只看到代價**：
  - 讀出 3 條，3 條都不對：m3:U08 是疑問句、m3:U15 是「設定是不是預設值」的疑問、m3:U18 是輸入檔名。
  - U15、U18 這兩題 ask 因此被誤拒。
  - 開發集裡沒有 C08 那一類題目。
- 已加上一條和 v6 相同的程式規則：引文裡有檔名或欄位識別字的（`covariance_bundle.tsv as coexpression_file`）是輸入，不是設定。這擋掉 U18；U15 仍會被誤讀。
- **風險**：這個欄位的精確度不高，誤讀會直接變成拒絕。第 6 步要專門看它在 do、ask 題上誤拒了幾次。

## 檔案

- `menu_focus.py`：`UnsupportedSetting` 與合併規則。
- 測試：`test_an_unsupported_setting_for_a_workflow_without_controls_is_a_reason`（只描述資料的、不在原文的、檔名的，都不採用）。

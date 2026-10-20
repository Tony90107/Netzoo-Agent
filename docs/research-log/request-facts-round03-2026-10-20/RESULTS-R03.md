# ROUND-03：數量與設定的共用事實紀錄（2026-10-20）

計畫：`collab/ROUND-03-PLAN.md`。依據：`output/thesis/2026-10-20_共用事實紀錄與判斷架構改造建議.md` 第 8 節第 2–3 步。  
程式 commit：`76fbe22b`（分支 `closed-menu-phase0`，沒有推送）。對照：`d9679a2b`。  
只做離線驗證，$0，沒有呼叫模型，沒有改模型 schema 或提示。

## 結論

- **共用紀錄已接上現行判定路徑**：能力核對裡每個樣本數、特徵數、設定、候選數量的每一次讀取，經原有規則驗證後存成一筆事實；每個結果的 method 與候選數量改由紀錄編譯，結果用 `fact_ids` 引用它判定時用到的事實；執行參數綁定記錄每個設定事實的去向。
- **判定完全不變**：979 筆已保存讀取（含 re-read 合併）用新舊程式重建，`build_capability_check` 的輸出（排除新增欄位）**979/979 相同**。
- 測試：新增 11 個；全套 4696 passed、51 skipped（TaskDecision schema 快照因新增欄位而更新）。乾淨 checkout 跑相關 148 個測試通過。
- **本輪不會讓判定分數變好**，這是預期中的：效益是可追溯、量得出重複，並為第二步打底。

## 量測（`metrics.txt`，979 筆讀取）

| 指標 | 數值 | 意思 |
|---|---|---|
| 讀取次數 → 使用者事實 | 2,514 次 → 1,356 筆（另 29 筆程式衍生總和） | 平均每筆事實被寫 1.85 次 |
| 被讀不只一次的事實 | 974 / 1,356（72%） | 重複輸出是常態 |
| 要求層讀到的事實中，整段也讀到 | 949 / 1,010（94%） | 要求層的數量／設定欄位大多是重填 |
| 只有要求層讀到 | 61（樣本數 43、特徵數 9、設定 9） | 直接刪掉要求層欄位會遺失這些，第二步必須讓整段事實帶上「適用哪個結果」 |
| 同一疑問同時寫在 count_alternatives 與 unknown_facts | 12 / 44 筆不確定事實 | 同一疑問兩處紀錄 |
| 判定時實際引用事實的結果 | 755 / 1,178 | 其餘結果沒有數量或設定 |
| 衝突紀錄 | 2（都在 h2 J11） | 「Leave lambda1 and lambda2 empty」被讀成一次無值、一次值為 "empty"；意思相同，沿用「最後陳述者」規則，判定不受影響 |
| 要求層 method 欄位的葉值 | 填值 4,839、空值 4,969（1,405 個要求） | 第二步可移除的輸出量上限（另含 named_method） |
| 整段 method 欄位的葉值 | 填值 4,126、空值 2,875 | |
| 新紀錄佔已存 check 的大小 | 中位數 +678 bytes（總量 +33.5%） | 只進 trace；已從一般 response 模型的輸入排除 |

計畫時掃描到的 C47（整段 400 位、另一醫院 150 位）在重建時**沒有**產生衝突：那題有兩個結果，整段的數量本來就不套用到個別結果。紀錄裡兩個樣本數是兩筆事實，`belongs_to` 為空（現行讀取沒有此欄，不猜）。

## 做了什麼（對照建議文件）

| 建議 | 本輪 |
|---|---|
| 穩定 ID、property、value／alternatives、state、evidence、origin | `RequestFact`：ID 由屬性與原文位置組成（re-read 也一樣）；evidence 記每次讀取的 reader 與所屬結果；origin 分 user_stated／derived |
| belongs_to | 欄位存在但保持空白：現行讀取沒有這一格，不從猜測補 |
| 同一事實不重複計 | 同屬性同值、原文重疊 → 同一筆、讀取次數加一；原文不重疊 → 分開（RNA 300 與 CpG 300 是兩筆） |
| 總數是衍生值 | 多個特徵數的總和存成 derived 事實，含 operands 與算式（例 `300 + 300`） |
| 判定、追問、參數引用同一份紀錄 | 數量限制與設定組合（method_fitting）、數量候選追問（count_update）、執行參數（verified_controls 的去向事件）都從紀錄取值或標出事實 ID |
| 每項明確要求都有去向 | `routing.run_fact_bindings`：applied／set_by_request／no_value／unbound／held。不能做的設定在結果的 limits，不會綁到 run |
| 遷移期間的成本 | 紀錄不送進模型；只增加 trace 大小 |

## 沒做、仍未解決

- 模型的重複輸出**還沒減少**：這一輪沒有改 schema。
- `needed_facts`／`resolve_unknowns` 仍直接讀 unknown_facts（本輪只把數量值記成同一疑問的另一次讀取）。
- 命名方法（named_method）不在本輪事實範圍。
- 否決層（預設關閉）仍有自己的數量讀取，尚未與這份紀錄合併。

## 第二步建議（需要模型讀取，另行決定）

把要求層的 `sample_count`／`feature_counts`／`settings` 拿掉，改成整段事實帶 `applies_to`（引用結果原文），並沿用 ROUND-02 的 `belongs_to`。驗證：在已見讀取上先看 61 筆「只有要求層」的事實是否能由新形狀讀回，再量輸出 token 與召回。這會改變模型讀取，需另開一輪、先報預算。

## 重現

```sh
cd docs/research-log/request-facts-round03-2026-10-20
python3 -I replay.py checks /tmp/old.json --scripts <d9679a2b checkout>/scripts
python3 -I replay.py checks /tmp/new.json
python3 -I replay.py compare /tmp/old.json /tmp/new.json
python3 -I replay.py metrics /tmp/new.json
```

讀取來源與輸出雜湊見 `manifest.json`。來源包含本工作樹未追蹤的 h1–h4 session 與主專案的 research-log。

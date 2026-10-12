# 判定層第 1 步：run 路徑的 shadow 量測（2026-10-12，執行前寫下）

使用者決定（2026-10-12）：
- 停止逐題、逐功能加規則，改整理判定層。
- 依序做三步：(1) run 請求也要經過同一個能力檢查；(2) 每項需求只有一個 verdict 物件，且狀態完整；(3) 所有 renderer 都只讀這個 verdict。
- 先從第 1 步開始，用 shadow 模式量測。

## 已知事實

- 可行性評測 2026-10-12 中，走 run 或下載路徑的有 8 題（F11、F12、F13、F15、F32、F38、F41、F44），能力檢查都沒有執行。
- 其中 F32 誤接受：只有 expression，卻判定 exact `run_sambar`。sheet 其實有 `sambar.no_expression_subtypes` 這個 near-miss，只是檢查從來沒有讀到這題。
- 已錄的 6,295 個 session 中，只有 29 個走 run 路徑，扣掉重複只剩 6 種請求。也就是說，過去的 held-out 題組幾乎量不到 run 路徑。

## 程式（dc00b58）

- 設 `NETZOO_SHADOW_RUN_CHECK=1` 時，run 請求也會呼叫同一個能力檢查。
- `routing.run_check_shadow` 會記下檢查對「routing 選定的 workflow」的判定，共七種：agrees、other_workflow、partial_gap、gap、no_result、not_on_sheet、unconfirmed。
- 這個判定只記錄，不會改變任何行為。開關預設關閉；關閉時，全部單元測試與上線版行為相同。

## 題組

`run17.json` 是 heldout17（Log 411）45 題單輪題改寫成 run 命令的版本：
- 改寫由不看程式碼的子代理完成；我逐題核對過，事實與條件都沒有變。
- 金標準直接沿用 heldout17 的需求標註。這組題已經看過，所以這次是量測，不是 held-out 驗證。

## 回合

- `r17`：每題跑 2 次，共 90 個 session，只有一臂（`.worktrees/netzoo-rp-shadow`，開關開啟）。
- 先確認免費檢查模型的額度已在 2026-10-13 08:00 重置。

## 量測（`analyze_run17.py`，只讀錄製結果）

- M0：走 run 路徑的 session 數，依金標準分類（neg／mixed／pos）。
- M1：現行 run 路徑的誤接受數，指以下兩種情況：
  - neg 題走了 run 路徑；
  - pos 題 run 的 workflow 不在金標準的 `by` 裡。
- M2（召回）：在 M1 的誤接受中，shadow 判為 gap、other_workflow 或 partial_gap 的比例。
- M3（代價）：在正確的 run 中，shadow 判為上述三種的比例。
- unconfirmed 另外計數。V：provisional／unavailable 的檢查若超過 10%，這輪無效。

## 下一步的事前規則

- **M2 ≥ 60% 且 M3 ≤ 10%**：設計會實際作用的第 1 步候選。shadow 判為非 agrees 時，不 run，改依 verdict 回覆；之後再用全新的盲測 run 題組驗證。
- **否則**：逐例檢查 shadow 判錯的原因，先改善檢查在 run 措辭上的讀取，再量一次。

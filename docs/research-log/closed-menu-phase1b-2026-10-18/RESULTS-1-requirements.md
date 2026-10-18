# 第 1b 階段第 1 步：要求的合約核對（2026-10-18）

## 結論

- 每個「使用者要求 × 候選 workflow」都有了判定：met／contradicted／not_addressed。
- **met 和 contradicted 必須附上該 workflow 合約的原文**，程式逐字核對，對不上就算 not_addressed（照 spec 3.10 會追問「是不是必要」，不會假設符合）。
- 開發集 d8（85 題）：
  - 要求核對在 8 題觸發，共 13 組，約 US$0.002。
  - 9 個判定有核對過的合約原文；1 個被程式降為 not_addressed：P12 的引文不是 GIRAFFE 合約的原文。
  - **把判定拿掉、只重跑決策表：2 題由錯變對**：
    - m3:N24：使用者要保留 PPI 的分數權重，OTTER 合約寫明會二值化 → 正確拒絕。
    - heldout13:CP1：「每條邊的 BH 校正 p 值」DRAGON 合約符合 → 從多問一題變成直接做。
  - BP3 從「問」變成「拒絕」，兩種都錯，原因是 signed 讀錯，不在這一步。
- 56 題不重讀。第 1 階段的離線估計是：要求這一項佔 7 次錯，全部拿掉可到 80/112。實際效果要看第 6 步的新題組。

## 做法

| 部分 | 內容 |
|---|---|
| 合約文字 | `workflow_contract(workflow)`：沿用 `contract_text`（YAML 的 description、conventions、settings、guidance_notes、handoff_contract），加上 capability sheet 該 workflow 的「給什麼＋怎麼讀」與「不給什麼＋為什麼」 |
| 呼叫 | 一次呼叫讀完所有組（最多 18 組）。每組先抄合約條文，再給判定（strict schema，每組一個欄位） |
| 核對 | met／contradicted 的條文必須逐字出現在該 workflow 的合約文字裡；沒有條文或對不上 → not_addressed |
| 順序 | 第一次讀取 → 聚焦重讀 → 要求核對（用合併後的候選）→ `decide_menu` |

## 檔案

- `scripts/netzoo_agent_core/interpretation/menu_requirements.py`
- `scripts/netzoo_agent_core/graph/menu_reading_call.py` 的 `read_requirements`
- `tests/test_menu_requirements.py`：6 項。驗證：合約文字的組成、組數上限、strict schema、只有引文對得上才算數、contradicted 會排除 workflow、呼叫失敗時保留原讀取。

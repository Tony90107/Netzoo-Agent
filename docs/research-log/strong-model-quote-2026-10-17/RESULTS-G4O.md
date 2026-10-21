# 讀取角色換成 gpt-4o：兩輪 56 題（2026-10-17）

## 設定

- 程式：p5r 那份（run worktree `54d08ce7`，`freeze-p5.json`）。
- 讀取角色：router、semantic 和 capability check 全部用 gpt-4o。capability check 用日期 id `openai/gpt-4o-2024-11-20`，保留自己的模型槽與 16,000 token 上限。
- 回覆模型：維持 gpt-4o-mini。
- 兩輪 tag：`g4o1`、`g4o2`，每輪 56 題各跑 1 次。
- 執行：`run_capped.py` 分批跑，硬上限 US$10。
- 計分：沿用 `score_core.py`，不做任何改動。
  - ASK 事實由我對照 gold 判定：兩輪 12＋13 題全部問對。
  - g4o1 的 C11 在回覆階段當掉（`IndexError`），`collect_g4o.py` 從 trace 取回它的判定（DO）照常計分。
- 費用：帳戶實扣 US$6.427，每輪約 US$3.1–3.2。p5r 一輪是 US$0.11。

## 結果

| 輪次 | 讀取模型 | core | 正確 | do | dont | ask | vague | UNCHECKED | 誤承諾 | 誤拒 |
|---|---|---|---|---|---|---|---|---|---|---|
| p4b | mini＋nemotron | 89.6 | 46/56 | 11/14 | 11/13 | 12/15 | 12/14 | 3 | 1 | 1 |
| p4c | mini＋nemotron（同 p4b 程式） | 79.0 | 39/56 | 10/14 | 11/13 | 8/15 | 10/14 | 1 | 1 | 2 |
| p5r | mini＋nemotron（同程式） | 83.3 | 43/56 | 11/14 | 10/13 | 11/15 | 11/14 | 3 | 3 | 1 |
| **g4o1** | gpt-4o | 74.2 | 41/56 | 10/14 | 11/13 | 12/15 | **8/14** | **0** | 2 | **4** |
| **g4o2** | gpt-4o | 74.9 | 41/56 | 11/14 | 11/13 | 13/15 | **6/14** | **0** | 2 | 3 |

- 兩輪 gpt-4o 判定不同的題數是 7；p4b 對 p4c（同程式、mini）是 13。gpt-4o 比較穩定。
- gpt-4o 兩輪都錯的有 13 題，其中 5 題（C04、C07、C14、C26、C44）mini 三輪全對。

## 結論：換強模型沒有讓答對率變高

gpt-4o 消除了讀取失敗（UNCHECKED 0、沒有解碼失敗、速度快很多），ASK 類也最好。但 vague 類大幅變差，do 類誤拒變多，總分落在 mini 三輪的範圍以下。**瓶頸不在模型讀不懂，而在決策規則對「讀取怎麼切分」太敏感**；這些規則是在多輪 mini 實測中逐題調出來的。

gpt-4o 錯誤的具體形態（兩輪一致）：

| 形態 | 例子 | 發生了什麼 |
|---|---|---|
| 片段被當成結果 → partial → 計誤拒 | C04、C07 | gpt-4o 把 "For each of our 25 … I need"、"within and across the two layers" 這類片段列成獨立的 result，`delivered_by` 空 → not_available → DO(partial) |
| 目的不明被判全缺口 → DECLINE | C23、C24、C26 | 兩個模型對 "a systems-level view …" 都讀成 not_available。mini 的 `goal` 讀成 purpose_only，得到 CLARIFY；gpt-4o 讀成 result_named，得到 full_gap DECLINE。一個 enum 欄位就決定了澄清還是拒絕。C26 把一個「該用哪個方法」的問題拆成三個 not_available 結果。 |
| 點名執行已註冊 workflow 也被判全缺口 | C44 | 「Run OTTER with …」整句引成 result，`delivered_by` 空 → full_gap → 拒絕執行一個已註冊的 workflow |
| 限制沒被讀成 result → 誤承諾 | C14 | 「L1 penalty」只留在 about_methods，沒有 result 列 → routed DO |

這些正是 spec 第 4.3 節的問題：not_available 太容易成立，空對應被當成不支援。現在有兩個模型的證據說明它不是 mini 特有的現象。

## 另外的發現

- g4o1 C11 的 `IndexError` 是回覆組裝的程式錯誤。core 判 DO 後才崩潰，p5r 沒觸發過。需要另外修。
- 用 gpt-4o 作正式讀取模型不划算：成本約 30 倍，答對率沒有提升。

## 檔案

- `run_capped.py`、`collect_g4o.py`、`run-g4o.log`
- `../core-judgment-2026-10-15/live/g4o1`、`g4o2`：structure.json、review-sheet.md、facts-checked.json、score-core.json

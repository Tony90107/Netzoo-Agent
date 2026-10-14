# 第 4、5 項：每項需求都被處理到、只問會改變判定的事（2026-10-14）

## 先量：漏讀在哪裡（`coverage.py`、`recent_misses.py`）

用 heldout11–19 中 255 題有逐項標準答案的單輪題，比對錄下的最後一次檢查（重讀之後）。一項需求「讀到」的定義是：有某個結果引文和它的原文重疊。不呼叫模型。

| 範圍 | 可做的需求 | 不可做的需求 |
|---|---|---|
| 全部 1179 個 session（跨版本） | 96%（漏讀的都是被歸成 context） | 90%（context 38、同句尾段 19） |
| 10-11 之後 789 個 session | 100%（context 1） | 95%（**同句尾段 13**、context 6） |

**同句尾段漏讀**，舉例：

- 「…, emailed to each patient's doctor automatically」
- 「…, uploaded automatically to a public database」
- 「plus a dashboard that updates live…」
- 「and the networks uploaded to a public repository for us」

這些尾段的重讀其實**有觸發**（rr-cand、score2-live），但送給模型的是整句。模型又引用了同一個已讀過的結果（「each patient's TF-gene network」），或回傳空的，所以尾段始終沒讀到。

**超過 12 句的請求**：0 例。**整句沒讀到**：8/334，全是「Opinions welcome.」「Which would you start with?」這類閒聊句。

## 第 4 項：改了什麼（`interpretation/reread.py`）

- **重讀只送「沒有任何引文涵蓋的片段」**。範圍是句中第一個引文之後的部分，句子開頭的「We want」「Which method」不算；整則請求仍附上作為上下文。
- **觸發條件不再依賴英文**：用 `letter_runs` 計算任何文字的詞數。無空格的文字（中日韓）每兩個字算一個詞。門檻 `MIN_UNREAD_WORDS = 3`。
  - 校準依據（`stretches.py`，361 個錄下的首次檢查）：漏讀的尾段都有 7 個詞以上。
  - 門檻 3 會觸發 16/361 次（舊條件 8 次），8 段漏讀全部涵蓋，也包含「and upload them」這類 3 個詞的短尾。
  - 門檻 2 會觸發 45 次，沒有多涵蓋任何漏讀。
- **首次檢查留下的未讀句子也進重讀**，包括第 12 句之後的句子，每次最多 12 段。
  - 重讀明確回傳「沒有需求」時，這句就算讀過，不再列為「Not checked」，也不再讓 run 因為「未讀完」被擋下。
  - 但重讀若引用了請求中找不到的文字，這句仍保持未讀。
- **合併規則**：重讀找到的新結果，必須引用它被交付的片段；引用其他地方的，算第一次讀取的結果。

## 第 5 項：先量，才發現原計畫的規則不成立（`unstated_decisive.py`）

計畫原本的規則是：「使用者沒說、但不同答案會改變判定」的條件一律追問。在 157 個標準答案為可做（含外部步驟）的結果上，這條規則會多出 61 次不必要的追問：

- 雙組學是否同一批樣本：36
- 資料單位：21（大多是 CONDOR，只給網路，不涉及資料單位）
- scale：5

在不可做的結果上，這些追問的答案也救不回任何一題。所以照舊：**只有使用者說不知道時才問**。

計畫中站得住的是「程式查得到的事，先查，不問」，以及 F41：

- DRAGON 與 LIONESS-DRAGON 都用 `load_and_align_dragon_layers` 讀資料。它要求兩層的樣本 ID 完全相同，並依 ID 對齊；不同時會擋下，並列出差異。
- F41 的使用者說「不知道兩張表的欄位是否同一個樣本順序」，被追問「是否同一批樣本」。這是問錯了：順序從來不影響結果，是否同一批樣本則會由檔案檢查判定。

**改了什麼**（`needed_facts.FILE_CHECKED`、`CheckedRequirement.file_checked`）：

- 使用者說不確定「兩層是否同一批樣本」，而且相關 workflow 全是會比對樣本 ID 的 DRAGON 類：不再等使用者回答，照常判可做，並說明執行前會比對 ID、順序不影響。
- 第二意見路徑（`wait_on_asked`）也照此處理。
- **CONDOR 的節點角色**仍然要問：它的輸入檢查對重疊節點只發警告，基因-基因網路照樣會跑（B03）。**資料單位**也仍然要問（B10）。

F41 的錄製讀取重算後：判為可做，回覆說明「DRAGON checks that both tables list exactly the same sample IDs…; their order does not matter」。

## 驗收

- 單元測試：
  - 短尾重讀（任何文字）；
  - 重讀只看被交付的字；
  - 未讀句子讀完後會被清掉；
  - F41、B18 不再追問；B03、B10 仍會追問。
- 全部測試：3648 passed。

## Live 驗證（2026-10-14，共 44 個 session，0 次供應商錯誤）

執行腳本 `run_live17.py`，分析腳本 `analyze_live17.py`；題目檔為 `live17.json`、`live13.json`、`live8.json`、`live6.json`；worktree 在 `.worktrees/netzoo-cov-live`。

| 回合 | 程式 | 結果 | 發現與修正 |
|---|---|---|---|
| c1（17 題） | f0a0536 | 漏讀題 3/8、對照題 5/5、閒聊句 2/3（B14 為備援模型讀取，依 Log 401 不重讀）、F41 1/1 | 交付類 4 題：首次檢查**已讀到**，但被歸成 format_or_delivery 後遭程式丟棄；重讀拿到正確片段，模型也不把寄送算成結果。VP5q 被背景引文切成兩段。→ d806644：拆出 `delivery` 類、能力表新增 `delivery` 條目、片段合併 |
| c2（13 題） | d806644 | 交付類 4/4、c1 已通過的 3 題 3/3、對照題 2/2、檔案格式題 2/3 | **退步**：HP4「Name the output after our project, ZEBRA」被歸成 what_it_contains，條件檢查判 DRAGON「違反」，整題被拒絕。→ e50cf50：條件檢查新增答案 `not_about_results` |
| c3（8 題） | e50cf50 | HP4 2/2、HP1 與 HP2 通過、UN6 違反仍成立 | HP3「在自己的伺服器過夜執行」2 次中 1 次被歸成交付（定義含「排程重跑」）。UN3：首次讀取沒有判給 SAMBAR，第二意見補判可做，k-means 條件因此沒被檢查（既有的順序漏洞）。→ c4c5919：收窄交付定義；第二意見新判可做的 workflow 也要做條件檢查 |
| c4（6 題） | c4c5919 | **6/6**：HP3 2/2 判可做；上傳、email、即時儀表板 3/3 判不可做；UN3 判不可做 | UN3 這次走一般路徑；「第二意見後的條件檢查」只有單元測試覆蓋 |

## 最終狀態與仍未解決的部分

- **交付類需求**：上傳公開資料庫或 repository、寄 email、儀表板、網站呈現，在最後兩輪都讀成不可做，可做的部分維持可做。run 遇到這類需求會照第 1 項的規則擋下確認。
- **仍漏讀：VP5q**。「aligns our raw reads to the genome」（比對讀序這類前處理）即使片段已經合併，重讀仍不把它當成需求。這需要另一個契約類別，例如「分析前的資料處理」，還沒做。
- **輸出檔設定**（檔名、格式、資料夾、在哪裡執行）不會再成為拒絕的理由。
- 中文未測，依使用者決定不納入驗收門檻。

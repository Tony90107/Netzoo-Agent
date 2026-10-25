# ROUND-27 第 0 階段：準備（2026-10-25，任何讀取或出題之前宣告）

- 計畫：`collab/ROUND-27-PLAN.md` 第 2 節。使用者在 2026-10-25 同意：順序 C1 → B1 → B2、B1 重開一輪、費用照計畫。
- 程式：工作樹 `.worktrees/netzoo-r27`，分支 `round27-links-inputs`，起點 `041f0ee9`。本階段不改任何程式。
- 費用：本階段不呼叫 API；出題、覆核、標註都由 subagent 完成。

## 1. 新題組 h10（封存）

- **出題：** 一個新的 subagent，brief 是 `h10/AUTHOR-BRIEF.md`。它只讀本工作樹的 13 個 `workflows/*.yaml` 與 `scripts/workflow_registry.py`。
- **金標覆核：** 另一個新的 subagent，brief 是 `h10/REVIEW-BRIEF.md`。
- **欄位金標：** 第三個新的 subagent，brief 是 `h10/FIELD-BRIEF.md`，輸出 `h10/fields.json`。它包含 C1 要的 `content`、`made_by`、`certainty`。
- **封存規則：**
  - 本輪開發期間，我不打開 `h10/items-author.json`、`h10/items.json`、`h10/GOLD-REVIEW.md`、`h10/fields.json`；
  - subagent 只回報數量；
  - 只有 `h10/check_format.py` 會讀這些檔案，而且只印數量與格式；
  - 封存時把 sha256 記進 `h10/SEALED.json`。
- **和 h9 的不同：** h9 是我讀過全部金標後才封存的。h10 我不讀，因為 C1、B1 的開發會用到它要測的情境。
- **用一次：** 只在計畫第 6 節的最後驗證時使用。

## 2. C1 的開發金標：每份使用者資料是什麼

- **範圍：** 現有 300 題逐欄位金標（`field-gold-2026-10-22/labels-*.json`）的 687 個 `has` 單位。
- **標註：** 只用 1 位盲標 subagent，brief 是 `CONTENT-BRIEF.md`。它補上 `content`、`made_by`、`certainty`。
  - 它只看請求原文、`has` 引用與 slot、13 個 YAML 與 `workflow_registry.py`；
  - 看不到代理的讀取結果，也看不到四類金標。
- **輸入與輸出：** 輸入是 `content-batch.json`，由 `make_batch.py` 從 labels 產生；輸出是 `content-labels.json`。
- **抽查：** 我抽查 10%（`random.Random(27)`），記在 `CONTENT-SPOT-CHECK.md`。抽查只修明顯錯誤，並逐筆記錄。

## 3. 影響判斷的案例普查

- **做法：** 用 757 份重放（ROUND-13 harness，現行程式）和 h5、h6 的錄製讀取，列出 B、C 錯誤實際改變判斷的 session。
- **結果：** 寫進 `CENSUS.md`。
- **用途：** C-G2 的單位清單在 C1 動工前就固定下來。

## 4. 寫這份文件時已經知道的事

- **C 的一部分 registry 已經寫好了。** `workflows/lioness-panda.yaml:50-52` 已經有一條限制，原文是 `"An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff"`，對應 `limit: "refuses_input:coexpression_matrix"`。
  - 缺的是讀題沒有告訴程式「使用者手上的資料是共表現矩陣」。
  - 這是 C1 設計的依據，不是看 h10 得到的。

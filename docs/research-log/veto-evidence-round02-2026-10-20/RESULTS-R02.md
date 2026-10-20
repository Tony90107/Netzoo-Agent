# ROUND-02：否決層證據歸屬（2026-10-20）

計畫：`collab/ROUND-02-PLAN.md`。程式 commit：`ce1ba1fc`，分支 `closed-menu-phase0`，沒有推送。

這一輪只做離線開發驗證，$0，沒有呼叫任何模型。第 8 節的新盲題驗收沒有執行，因為還沒凍結預算，也沒有授權。否決層仍預設關閉。

## 結論

- **四項任務都完成並有測試**：
  - A：數量與資料的歸屬、更正；
  - B：三條證據檢查；
  - C：逐格紀錄；
  - D：M46 的輸入種類檢查。
- 測試：新增 22 個；全套 4685 passed、51 skipped。
- **在已存的 63 個讀取上原樣重放**（h4 19 個、h1–h3 44 個，全部看過，只用來除錯與回歸）：
  - M38、M48 兩個錯誤否決消失；
  - M25、M40 的正確否決保留；
  - **L13 的正確否決消失**：舊讀取只有一個總數「2,500」，沒有拆成兩層各自的數字，依本輪規則不能拿來否決；
  - M46 仍沒擋到：舊讀取沒有「要給哪個 workflow」這一格。
- **新讀取形狀還沒在真的模型輸出上量過。** gpt-4o-mini 會不會正確填 `belongs_to`、`input_for`、`corrects`，要等下一次讀取才知道。所以 M01、M46、L13 在新形狀下是否變好，目前未驗證。

## 重放結果（`replay.json`、`manifest.json`）

改變的 4 列：

| 列 | 之前（c32ba444） | 之後（ce1ba1fc） | 原因 |
|---|---|---|---|
| h4 M38（ask） | DECLINE：kmax 10 > 8 | DO | 「either 8 or 15 tumours」：8 旁邊緊鄰另一個數字，不能當成確定的樣本數。SAMBAR 的 kmax 規則也讀不到它，依賴鏈一起生效。DO 正是 H2 現行系統原本答對的判定 |
| h4 M48（vague） | DECLINE：未註冊方法「NetZoo」 | DO | 工具包名稱不算方法。**整題仍然錯**（vague 應該追問），錯在上游的現行系統，本輪不碰 |
| h4 M01（ask） | 兩題追問 | 兩題追問，數量題標為 `legacy_unverified` | 舊讀取沒有證據，只標記、不改。continuous／binary 那題仍在，要新形狀才會拿掉 |
| h3 L13（dont） | DECLINE：2,500 features 超過上限 | DO（**變差**） | 2,500 是兩層加總，舊讀取的引文是「2,000 transcripts」，沒有各層的數字。依計畫，沒有 operands 的總數不能當成已驗證的數量 |

另有 4 列的數量被擱置，但判定不變：

- H07、L09：舊讀取裡的總數；
- J44、J47：「sample_count 2」不在它自己的引文裡，屬於讀錯，擱置是對的。

L48 的 C6 否決來自合約核對時模型抄的條文，那份 payload 沒有存下來，所以無法重放。

### h4 逐格對照（`gold-cells.json`，19 列 44 格，手寫）

| | 之前 | 之後 |
|---|---|---|
| 值召回 | 32/41 | 32/41（讀取不變） |
| 不確定的事實召回 | 1/3（只有 M01） | 1/3 |
| 歸屬 | legacy_unknown | legacy_unknown |
| 否決全對的列 | 16/19 | **18/19** |
| 無依據的否決 | M38（B5）、M48（C5） | **0** |
| 漏掉的否決 | M46（C8） | M46（C8），舊讀取沒有 `input_for` |
| 無依據的追問 | M01 value_type、M31 核心資料 | 相同（舊讀取不改） |
| 漏掉的追問 | M36 data_unit、M38 sample_count | 相同 |

剩下的都是**讀取召回**問題，不是規則問題：

- M31：「64 mouse liver RNA-seq samples」沒被讀成有表現量資料；
- M36：單細胞與 bulk 的矛盾沒被讀出；
- M38：沒讀成 8 或 15；
- M13、M19：設定沒讀到。

逐格紀錄（重放的 63 列合計 655 格）：read 245、not_mentioned 410。

## 各任務的實作

| 任務 | 做法 | 檔案 |
|---|---|---|
| A1 數量 | 讀取的 counts 每筆加 `belongs_to`（必須是原文）與 `corrects`；同一層的不同版本是替代值（不相加）；不同層是 operands，由程式加總並保留算式；重述只算一次；更正須指向較早出現的原文、同一個 what、同一個物件，否則保留衝突 | `slim_evidence.py`、`contracts/slim_reading.py`（`Evidence`、`derived`） |
| A2 資料 | A3 增加 `unsure`（不知道≠沒有）、`input_for`（必須是原文中的註冊名稱）、`corrects`；沒有驗證過的有／無矛盾一律 unsure | 同上 |
| B1 | 數量只有在以下情形才能被判定：數字就在它的引文裡、旁邊沒有緊鄰的另一個數字（中間至多一個字）、檔名裡的數字不算；衍生總數必須有 operands，而且各自在自己的引文裡。其餘在任何規則讀取之前就擱置 | `veto_evidence.backed_counts` |
| B2 | `PROJECT_IDENTITIES = (netZoo, netZooPy)`，有測試核對 Dockerfile 的 clone URL；只接受整個名稱，不比對子字串 | `method_names.py` |
| B3 | 數量追問：新形狀必須有替代值的證據，問題改問那一層，總數另附算式；舊讀取保留並標記。分類追問：引文如果是某個數量的疑問，就刪掉 | `veto_evidence.backed_questions`、`contract_veto._question` |
| C | `veto_reads` 收集 ReadReport；`core.contract_veto` 事件附逐格紀錄（read／dropped／not_mentioned／not_run，以及判定結果）；預算不足或讀取失敗時也記錄 | `veto_evidence.veto_ledger`、`graph/contract_veto_call.py` |
| D | `lioness-panda.yaml` 加 request-scope 輸入檢查 `refuses_input:coexpression_matrix`，引用合約原文；使用者把該資料指定給 LIONESS-PANDA 時，判為 C8；`fact_check` 不把這類檢查當成可由檔案確認；registry 本來就沒有 co-expression 輸入，不需修改 | `workflows/lioness-panda.yaml`、`policy.py`、`contract_text.py`、`fact_check.py`、`judgment_defaults.yaml` |

`slim_reader.py` 超過 1,000 行的模組上限，所以把證據組裝拆到 `slim_evidence.py`。

## 偏差與限制

- A2 沒有另設 `negated` 欄位。A3 的 `lacks` 本身就是對該資料命題的否定；這次新增的是 `unsure`，避免「不知道」被當成「沒有」。
- B1 的「緊鄰」是結構規則（字數與距離），不是詞表。它會漏掉「8 or maybe 15」這種中間隔兩個字的寫法；新形狀讀取的 `values` 可以補上。
- 樣本數若有多個不同數字，仍取最大值當總數（例如 60 個腫瘤＋60 個正常 → 120），這是沿用原本的行為。只有更正驗證失敗時，才改成保留衝突。
- 金標由我一人根據 h4 的題目手寫，沒有第二位審核者。
- 舊讀取上的重放只能證明「程式規則」的作用，不能證明新讀取形狀的作用。

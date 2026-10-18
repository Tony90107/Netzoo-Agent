# 封閉清單判定（Closed-menu Judgment）設計提案

日期：2026-10-18　狀態：**提案，待使用者確認**（確認前不動程式）
取代範圍：`2026-10-15-core-decision-design.md` 的第 5、6 節（goal 欄位、fact agent 自由提案）與能力檢查的「逐句切結果列」讀法；第 3 節四態定義、第 4.3 節回覆分派、run 的三道閘全部保留。
分析資料與腳本：`docs/research-log/judgment-bottleneck-2026-10-18/`（`analyze_bottleneck.py`、`out.txt`），只讀既有 trace，未呼叫模型。

---

## 0. 結論

1. **瓶頸不在模型，在讀取的形狀。** 現在由模型把請求切成「結果列」，再把每列對到 capability sheet；**沒對到就等於做不到**。「沒對到」其實混了三種情況：真的不在清單、這段話根本不是結果（是問句或目的）、模型沒認出來。強模型切得更細，空列更多，所以換 gpt-4o 反而更差。
2. **你的想法方向是對的**：以註冊 workflow 為封閉清單，清單外一律不做、不編。但要多一條規則：**「做不到」必須有正面證據，不能從「沒對到」推出來。** 沒對到是「不確定」，要追問或釐清，不是拒絕。
3. **追問改由程式算，不靠模型自由想。** 模型只讀「使用者說了什麼」（每個維度：說了什麼值／沒說／說不確定），程式拿這些去篩清單，得到候選結果集合。候選分不開的那個維度，就是要問的問題。問題和選項都來自清單，所以問的一定是清單內、會改變判定的事，不會亂編。

---

## 1. 現況診斷（5 輪 × 56 題 = 280 個判定，p4b、p4c、p5r、g4o1、g4o2）

### 1.1 錯在哪一層（70 個錯誤）

| 類型 | 次數 | 佔比 | 例子 | 發生了什麼 |
|---|---|---|---|---|
| A 沒對到被當成做不到 | 27 | 39% | C23「a systems-level view」、C41「Which one should I run?」、C07「within and across the two layers」 | 問句、目的、片段被切成結果列，沒有 sheet 對應 → `not_available` → 全缺口拒絕或 partial |
| D 該問／該釐清卻沒問 | 12 | 17% | C53「how genes are connected」、C11「per group 還是 per donor」 | 追問要等使用者說「不確定」（R1）；沒說就直接選一個做 |
| B 一個 enum 決定 CLARIFY | 9 | 13% | C34、C36 | `goal` 被讀成 `purpose_only`，有明確問題的請求被改成「目標不明」 |
| C 限制沒讀到 → 誤承諾 | 9 | 13% | C14 OTTER 加 L1、C17 只固定一層 shrinkage | 設定沒有被讀成設定，程式規則沒機會觸發 |
| E 讀取失敗 | 7 | 10% | C31、C58 | 每輪 3–11 次模型呼叫，任何一次失敗或超預算就 UNCHECKED |
| F 類別對、目標錯 | 6 | 9% | C59、C45 | — |

### 1.2 主要是「不穩」，不是「不會」

- 56 題裡有 31 題在 5 輪中至少錯過一次；**連錯 4 次以上的只有 3 題**。
- 同一份程式、同一個模型（p4b vs p4c），有 14 題判定不同；兩輪都同意的 42 題，對 36 題（86%），單輪平均只有 76%。
- 每輪參與判定的模型讀取角色有 15 種（capability_check、study_purpose、semantic_interpreter、intent_router、semantic_reviewer、fact_check、hypothesis_bases、capability_reread…），中位數 7 次呼叫。`decide_core` 是一條優先序鏈，**任何一個讀取翻轉，判定就翻轉**。讀取越多，整體越不穩。

### 1.3 換強模型為什麼沒用

gpt-4o 的讀取更細：把「For each of our 25 … I need」「within and across the two layers」列成獨立結果，把「Run OTTER with …」整句當結果。這些列都對不到 sheet，於是變成做不到。規則是在 mini 的切法上逐題調出來的，換一種切法就失準。**只要判定依賴「模型怎麼切」，換多強的模型都會換一種錯法。**

### 1.4 「做不到」的證據來源（DECLINE 與 partial 背後的 not_available 列）

| 金標 | 判定 | 列的依據 | 對／錯 | 次數 |
|---|---|---|---|---|
| dont | DECLINE | 有合約理由（設定不存在、數值超界、near-miss） | 對 | 37 |
| dont | DECLINE | 只是沒對到 | 對 | 11 |
| vague / ask | DECLINE / partial | 只是沒對到 | **錯** | 12 |
| do | DECLINE / partial | 有「理由」 | **錯** | 9 |

- 錯的 12 列全是**問句或目的**：「Which one should I run?」「What can we do?」「can you set something up that would satisfy them?」「a systems-level view」。
- 對的 11 列全是**具體交付物**：「filtered VCF」「order the cells along a pseudotime trajectory」「most edges exactly zero」（C22、C16、C14）。
- 所以只要讀取時把一段話**標成「具體交付物」還是「問句／目的」**，這兩組就能分開。現有欄位分不開：直接要求「拒絕必須有合約理由」會讓那 11 個對的拒絕一起掉。
- do 類 9 個錯在「有理由」，其實是**設定值對不上 enum**（「log2-transformed」→ `log_transformed`、「HDF5」→ `.h5`、「edge list」→ `output_format`），以及 C07 的片段被丟進全部 near-miss。這是設定讀取的形狀問題，不是清單問題。

---

## 2. 設計原則

1. **封閉清單**：能做的事 = capability sheet 的 `produces` 條目 + 每個 workflow YAML 的 `controls` 與條件。清單外的不做，也不給清單外的做法步驟。
2. **模型只讀，不判**：模型只回報「使用者說了什麼」，每個欄位都有逐字引文，或標成「沒說」「說不確定」「說了兩種」。可不可以做、要不要問，全部由程式決定。
3. **做不到要有正面證據**：使用者點名了一個清單外的具體交付物、某個合約條件不成立、或要求的設定不存在。「沒對到」永遠不等於做不到。
4. **不確定是一個狀態，不是錯誤**：沒說的維度會擴大候選集合；候選分不開時就問，問題由程式從清單產生。
5. **少讀幾次**：判定只依賴一次讀取（另加一次只在拒絕時才用的複核），其他角色降為呈現用或移除。

---

## 3. 新架構

```
使用者訊息
  → 讀取（1 次）：MenuReading           模型只填「說了什麼」，每格都要引文或標 not_stated / unsure / conflicting
  → 候選計算（程式）：清單 ∩ 已陳述維度    沒說的維度不篩 → 候選變多
  → 條件判定（程式）：每個候選 × 合約條件  FIT / FAIL(合約原文) / DEPENDS(哪個維度)
  → 決策表（程式）：CLARIFY / ASK / DECLINE / DO
  → 拒絕複核（只有 DECLINE 才呼叫）：     一個 workflow 的合約 vs 使用者原文，不同意就降為 ASK
  → 回覆：依 kind 的模板 + 接地檢查
```

### 3.1 讀取：`MenuReading`（取代逐句切結果列、`goal` enum、fact agent 的自由提案）

模型拿到的是**選單**：每個 `produces` 條目的維度值、每個 workflow 的 controls 與允許值、registry-wide 不提供的類型。輸出：

```python
class Said(BaseModel):                 # 每個維度共用
    value: str | None                  # 選單裡的值
    status: Literal["stated", "not_stated", "unsure", "conflicting"]
    basis: Literal["explicit", "implied", "answered"] | None = None   # stated 時：明說／由字句推斷／追問後使用者回答
    quotes: list[str] = []             # stated/unsure/conflicting 必須有逐字引文（implied 引的是推斷依據的字句）

class Wanted(BaseModel):               # 使用者要交付的一個東西
    quote: str                         # 逐字
    form: Literal["deliverable", "question_to_us", "purpose", "data_description", "context"]
    artifact: Said                     # 值域 = sheet 的結果類型 + registry-wide 類型 + "outside"
    granularity: Said                  # aggregate / sample_specific
    regulators: Said                   # tf / mirna / none
    layers: Said                       # 幾層 omics
    outside_name: str = ""             # artifact=outside 時：使用者點名的交付物（逐字）

class SettingAsked(BaseModel):
    quote: str
    workflow: str
    control: str                       # YAML controls 的名字，或 "not_a_control"
    value: str                         # 必須是該 control 的允許值之一（enum 由模型對到），或 "not_allowed"

class MenuReading(BaseModel):
    wanted: list[Wanted]
    settings: list[SettingAsked]
    facts: dict[str, Said]             # 樣本數、特徵數、有哪些資料（expression / motif / PPI / miRNA / mutation / 第二層）…
    named_workflows: list[str]         # 程式由原文算（method_names.workflows_in），不交給模型
```

和現在的差別：

- **片段不能自成一列**：「for each patient」「within and across two layers」只會變成某個 `Wanted` 的 `granularity`、`layers`，不會變成一個沒對到的結果（修 A 類的 C04、C07）。
- **問句、目的有自己的 `form`**：「Which one should I run?」是 `question_to_us`，「a systems-level view」是 `purpose`；兩者都不會進拒絕（修 A 類的 vague、ask 題）。
- **清單外要正面點名**：`artifact = outside` 必須附 `outside_name` 的逐字引文（「filtered VCF」「pseudotime」）。保留那 11 個對的拒絕。
- **設定值由模型對到 enum**：模型看得到允許值，「edge list」直接填 `output_format=edge_list`，對不到才填 `not_allowed`（修 C32、C40、C52 的誤拒，也讓 C14、C17 的限制一定被讀到）。
- **不確定是欄位值**：`unsure`、`conflicting` 取代「fact agent 引用使用者不確定的話 + 能力檢查第二次讀同一句」的 R1 雙讀機制。

這是**合約形狀的改變**（schema、選單、typed vocabulary），不是改 prompt 措辭，符合 no-prompt-wording 規則；prompt 只描述新的輸出形狀。

### 3.2 候選計算與條件判定（純程式）

對每個 `form = deliverable` 的 `Wanted`：

1. `artifact = outside` → 這一項 **DECLINE**，附最接近的清單結果（程式依其餘維度找最相近的 `produces` 條目）。
2. 否則候選 = 所有維度相符的 `produces` 條目。`stated`（明說、推斷或回答）的維度才篩；`not_stated` 的意圖維度不篩，留給第 3.8 節的追問；條件維度依第 3.3 節。
3. 每個候選的 workflow 對 `facts` 與 `settings` 跑條件（沿用 `workflow_conditions`：最少樣本數、特徵數上限、genes > samples、設定組合限制）：
   - `FIT`：條件都成立，或要到檔案才查得到（YAML `input_checks` 的 `scope: file`）→ 交給執行前的輸入檢查。
   - `FAIL`：附合約原文（例如「manual value needs lambda1 and lambda2 together」）。
   - `DEPENDS(維度)`：某個 `scope: request` 條件的值是 `unsure` 或 `conflicting`。

### 3.3 預設值表（新，寫在 YAML 或 sheet，不寫在程式裡）

每個維度宣告「沒說時怎麼辦」。這張表決定了「什麼該問、什麼不該問」，是這次設計的核心資產。完整內容見第 9 節（草案 2，2026-10-18 修訂）。

**「沒說」的定義（2026-10-18 修訂）**：只有使用者的話裡完全沒有線索，才算沒說。明說的（explicit），以及可以從字句推斷的（implied，例如「每位病人一個數字拿去和存活比較」推出每個樣本一個值），都算有說，但推斷必須附上依據的原文。

維度分四類，處理方式不同：

| 類別 | 維度 | 沒說時 |
|---|---|---|
| **意圖** | 結果類型、granularity、regulators、layers | **不設預設，追問**（第 3.8 節）；只在它會把剩下的候選分成不同結果時才問 |
| 資料條件 | data_unit、mutation_origin、value_type、mirna_driver、動態／空間／分組 | 用預設值（清單外的值通常會被正面提出），並寫在回覆的「我先假設」 |
| 執行前檢查 | 樣本數、特徵數、兩層是否同一批樣本、有沒有 motif/PPI 等輸入 | 不問；輸入檢查會驗，或列為執行需要 |
| 設定 | YAML controls | 用 YAML 預設值 |

### 3.4 決策表（取代 `decide_core` 的優先序鏈）

| 條件（依序） | kind | 回覆 |
|---|---|---|
| 讀取失敗 | UNCHECKED | 如實說無法判斷 |
| 沒有任何 `deliverable`，也沒有 `outside` | **CLARIFY** | 依已說的資料，列出清單裡能得到的結果，問一個目標問題 |
| 有 deliverable，但候選橫跨 ≥ 4 種不同結果（artifact 沒說，或只說了主題） | **CLARIFY** | 同上，清單限縮在相符的候選 |
| 候選有 2–3 種**不同結果**，而且分開它們的維度是 `not_stated`（無預設）、`unsure` 或 `conflicting` | **ASK（選哪個）** | 封閉選項：「你要的是 A（每位病人一個網路）還是 B（每組一個網路）？」選項文字取自 sheet |
| 結果唯一，但它的 workflow 是 `DEPENDS(維度)`，而且這個維度的兩個值會導向 FIT 和 FAIL | **ASK（事實）** | 問該維度，附使用者原文與合約原文 |
| 所有 deliverable 都是 outside 或 FAIL | **DECLINE** | 先經 3.5 拒絕複核；理由只引合約原文或「清單沒有 X」，附最接近的已註冊結果 |
| 有的 FIT、有的 outside 或 FAIL | DO（partial） | 逐項列出；絕不自動只跑可做的部分（2026-10-14 決定） |
| 候選的結果相同、只是 workflow 不同（平手） | DO（選項） | 沿用平手回覆 |
| 其他 | DO | — |

說明：

- **2026-10-18 修訂**：CLARIFY 和「選哪個結果」的 ASK 改由同一個追問迴圈產生（第 3.8 節）。問的是結果類型時記為 CLARIFY，問的是其他意圖維度時記為 ASK。上表的「≥ 4 種」與「2–3 種」兩列，改成「先問能把候選分成最少組的那個維度」。
- **CLARIFY 和 ASK 的界線由候選數算出**，不再由 `goal` 一個 enum 決定（修 B 類）。
- **「選哪個結果」的 ASK 不需要使用者說「不確定」**：只要話本身分不開候選就問（修 D 類的 C11、C41、C53）。**「資料事實」的 ASK 仍然只在 `unsure`／`conflicting` 時問**，沒說就用預設或交給輸入檢查，保留 2026-10-14 的精確度決定。
- 問題的數量上限沿用 R6（最多 2 個）。

### 3.5 拒絕複核（只在 DECLINE 時呼叫一次）

把「最接近的那個 workflow 的合約原文」和使用者的 `outside_name` 或 FAIL 的那句話給模型，問一件事：這個 workflow 的輸出是否就是使用者要的東西。

- 同意做不到 → DECLINE。
- 不同意 → 降為 ASK（「你要的是不是 X 的輸出 Y？」）。

誤拒會變成一個多餘的問題，而不是錯的拒絕。這沿用現有 second opinion 的機制，只是改成在決策之後、針對單一 workflow 才呼叫。

### 3.6 兩次讀取一致性（選用，第 1 階段離線就能量，不另花錢）

同一請求讀兩次（mini 兩次，或 mini + nemotron），各自走決策表：

- 一致 → 照判定做。
- 不一致 → 改用較保守的那個：DO vs DECLINE → ASK 確認；涉及 CLARIFY → CLARIFY。

既有資料的估計：兩輪一致時的正確率是 80–91%，單輪是 73–76%。這是**安全機制**，不是提分機制：它把「錯的承諾或錯的拒絕」換成「多問一句」。要不要開，看第 1 階段量到的不一致率。

### 3.7 不亂編：回覆接地檢查

- CLARIFY、ASK、DECLINE 的回覆**全部用模板**（大致已是如此：`clarify_goal`、`ask_facts`、`capability_check_gap`），內容只來自清單與合約原文。
- 清單外的請求只能說三件事：清單沒有 X、最接近的已註冊結果是 Y、Y 和 X 差在哪（合約原文）。**不給清單外工具的操作步驟**。
- 最後的模型自由回覆（`graph/response.py` 約第 256 行，現在只去掉 CLI 尾巴，沒有檢查內容）加上一道程式檢查：回覆裡出現的 workflow 名、參數名、處理步驟，必須在 `CoreDecision`、該 workflow 的 YAML controls 或 sheet 的 `with_step` 內。不符合就改用模板回覆，並記錄 trace 事件。

### 3.8 追問迴圈：意圖不清楚就問，確定後才填欄位（2026-10-18 加入，使用者決定）

原則：**意圖維度不替使用者猜。** 使用者沒說、也推不出來，而且這個維度會改變結果時，就問；使用者回答後，才把欄位填上（`basis = answered`），再重算。

**1. 什麼時候問**

- 只問**意圖維度**：結果類型、granularity、regulators、layers。
- 只在它**會分開剩下的候選**時才問：不同的值會導向不同的結果，或一個 FIT、一個 FAIL。不影響結果的維度不問，例如兩個值都導向同一個 workflow。
- 如果剩下的候選已經是同一種結果（只是 workflow 不同的平手），就不問，直接走 DO 的平手回覆。
- 資料條件類只在使用者說不確定或說了兩種時才問（沿用 2026-10-14 的精確度決定）。執行前檢查類一律不問。

**2. 先問哪一個**

- 每輪最多問 2 題。
- 先問**能把候選分成最少組、而且每組都有東西的維度**，由粗到細：通常是結果類型的大類，接著 granularity、regulators、layers。
- 一題的選項 ≤ `ask_max_options`（3）。候選超過 3 種時，先問大類（YAML `question_groups`，例如「基因之間的關聯」「調控因子對基因」「兩種 omics 之間的關聯」「分群／分型」），不一次列出 8 個結果。

**3. 問題長什麼樣**

- 封閉選項，選項文字取自清單，每個選項寫「你會得到什麼 · 和另一個差在哪 · 什麼情況選它」（沿用 option lines 的使用者視角），不寫演算法機制。
- 每題固定再加兩個選項：「不確定，請建議」與「都不是（請說明）」。
- 問題附上引發它的使用者原文（如果有的話），讓使用者知道為什麼被問。

**4. 回答怎麼填**

- 下一輪只讀回答對應到哪個選項（封閉對應），不重讀整段請求。
- 對到選項 → 該維度填 `stated`，`basis = answered`，引文是使用者的回答。**回答過的維度鎖定**，之後的讀取不能覆蓋。
- 「都不是」且說明的是清單外的東西 → 該項走 outside（DECLINE，附最接近的結果）。
- 「不確定，請建議」→ 依使用者已說的目的或資料，給一個建議並說明理由（使用者的語言，不講機制），請使用者確認；確認後才填入。使用者若說「你決定」，就填建議值，`basis = answered`，回覆寫明是代為決定的。
- 回答和原請求矛盾（例如原文說「每位病人」，回答選了「整體一個」）→ 以回答為準，並在回覆中點出。

**5. 狀態跨輪保存**

- 原請求的讀取，加上每一輪回答填入的維度，存在 session 的 `IntentState`。每輪都對「原請求＋全部回答」重算候選與決策表，不再只看最新一句（修正 2026-10-12 指出的「每輪單獨判定」問題）。
- 最多 3 輪追問。3 輪後仍有多種結果時，列出剩下的選項讓使用者直接選，不再追問細節。

**6. 回覆中的「我的理解」**

分三段列，讓使用者一眼看出哪裡是被猜的：

1. 你說的，或我從某句推斷的（附原文）。
2. 你回答的。
3. 你沒說、我先假設的（只有資料條件類；意圖維度不會出現在這裡）。

**7. 驗證**

- 追問迴圈是純程式，可以用「金標讀取＋模擬使用者回答」離線測試。模擬的回答取自題目 gold 的意圖。
- 量三個數字：幾輪後確定、最後結果是否正確、do 類題目被多問的次數（目標 0，因為 do 題的意圖都已明說或可推斷）。

### 3.9 欄位齊全性：不能太少，也不能多到干擾（2026-10-18 加入）

欄位是從封閉的合約推出來的，所以「齊不齊全」可以用程式機械檢查，不靠直覺。`tests/test_judgment_defaults.py` 檢查四件事；之後新增 workflow、near-miss 或限制時，沒有對應欄位，測試就失敗：

| 檢查 | 內容 | 防止什麼 |
|---|---|---|
| C1 分得開 | 任兩個不同 workflow 的 sheet 結果，至少有一個意圖欄位不同；完全相同的必須列為**方法平手**（目前只有 PANDA／OTTER），平手時兩個都列給使用者選 | 太少：系統分不開，只好替使用者選 |
| C2 擋得住 | 每個 near-miss 與 registry-wide 條目（35 個），都對應到某個欄位的清單外值 | 太少：清單外的要求沒有欄位可擋，結果亂執行 |
| C3 限制有人管 | 每個 workflow YAML 中 `scope: request` 的限制（最少樣本數、genes > samples、數值上限、設定範圍），都對應到欄位 | 太少：限制讀不到，誤承諾 |
| C4 沒有閒置欄位 | 每個欄位都必須服務 C1–C3 之一、讀取一個既有條件，或寫明它決定什麼 | 太多：沒用的欄位只會增加讀錯的機會 |

多出來的欄位會不會干擾原本能做的請求？以下規則限制了這個風險：

1. **只問會分開候選的意圖欄位**。其他欄位再多，也不會多出問題。
2. **欄位只對它適用的候選起作用**。例如 `mutation_origin` 只在 SAMBAR 還是候選時才有影響；讀錯一個不相關的欄位，判定不變。
3. **清單外的值要有逐字引文**。只靠一個欄位造成的拒絕，還要經過 3.5 的拒絕複核。
4. 第 1 階段**逐欄量測**：在 do 類題目上，每個欄位「沒說卻被讀成有說」的比率。這個數字太高，就把讀取拆成兩次：第一次讀意圖與資料，第二次只讀剩下候選的條件欄位。

### 3.10 判定的結局（2026-10-18 補充）

| 情況 | 結局 |
|---|---|
| 欄位都填好，對上清單，而且條件成立 | **DO**。之後還有輸入檢查：檔案不合格是「這份資料目前不能跑」，不是任務做不到 |
| 欄位填好了，但值在清單外，或違反合約條件 | **不能做**（DECLINE），附合約原文與最接近可做的結果 |
| 使用者回答「都不是」，說的是清單外的東西 | 那部分**不能做** |
| 意圖欄位還沒確定（使用者不確定、3 輪後還沒選） | **還沒決定**：給建議或列出剩下的選項。不執行，也不拒絕；這**不是**「不能做」 |
| 某句話填不進任何欄位，也沒有點名清單外的東西 | **不清楚**：追問那句想得到什麼。不拒絕 |
| 有些部分能做、有些不能 | 分項列出，不自動只跑能做的部分 |

**可以進入執行的條件（草案 4，使用者的 8/10 規則）**，依欄位種類分開判斷：

| 欄位種類 | 規則 | 依據 |
|---|---|---|
| 硬條件（合約明寫的限制、清單外的值） | **一個不符就不能做那一部分**，不看比例 | accept24 的 11 個誤承諾中，9 個正是「結果類型對、其他都符合、只差一個條件」：OTTER 加 L1、GIRAFFE lambda、TIGER、LIONESS-OTTER、PUMA 用 miRNA 表現量、只有 2 個樣本、超過 LIONESS-DRAGON 上限、兩層來自不同小鼠、四到五層。比例規則會讓這 9 個都變成「可以跑」 |
| 會改變 workflow 的意圖欄位 | **沒確定就追問**，不看比例 | 不知道該跑哪一個 |
| 使用者自己提的要求，合約沒有寫到（not_addressed） | **使用者的規則（草案 5）**：合約符合的 ≥ 90% → 可以進入執行，沒寫到的列在執行前的確認裡；< 90% → 追問沒寫到的是不是必要條件，直到 ≥ 90%。使用者回答「不是必要」的就不再計入。3 輪後仍不到 90%：不執行，列出未確認的要求，由使用者逐項確認後才放行 | `thresholds.soft_requirements_met: 0.9`。要求少於 10 個時，90% 等於全部都要符合或確認 |
| 資料條件的預設值、執行前才查的欄位 | 不擋；寫在「我先假設」，輸入檢查再驗 | — |

---

## 4. 會移除或降級的部分

| 現有元件 | 處理 |
|---|---|
| 能力檢查「逐句切結果列 + credit」的讀法 | 由 `MenuReading` 取代；`not_available` 只從 outside 或 FAIL 產生 |
| `goal` enum（result_named / purpose_only / method_named） | 移除；CLARIFY 由候選數決定 |
| fact agent 自由提案 + R1–R7 | 移除；ASK 由決策表產生。合約接地的精神（問題一定對應合約條文）保留在 3.4 |
| `count_alternatives`（5b）、`open_results`（5c） | 併入維度的 `unsure` / `conflicting` |
| capability_reread、second_opinion、condition_check 等 | 只保留 3.5 的拒絕複核 |
| semantic_interpreter / reviewer / intent_router / discriminator / hypothesis_bases | 判定不再讀它們；第 3 階段盤點哪些還被回覆呈現使用，其餘移除 |

目標：**判定只依賴 1 次讀取 + 最多 1 次複核**（現在中位數 7 次）。

---

## 5. 驗證方式（改成分層量，不再只看端到端分數）

1. **決策表 = 純程式 → 窮舉單元測試**：對每個 workflow、每個維度的每種狀態（stated-fit / stated-fail / not_stated / unsure / conflicting），從合約算出應有的 kind。不需要模型，也不需要標註。
2. **讀取 = 模型 → 量每個欄位的準確率**：每題的 gold 改成「金標讀取」（每個維度該填什麼）。錯誤會直接指到「哪個維度讀錯」，不用再從端到端分數反推。
3. **穩定度**：每題讀兩次，報告 kind 一致率。目標 ≥ 90%（現在同程式兩輪是 75%）。
4. **新的保留題庫由合約生成**：從「workflow × 維度 × 狀態」的組合抽樣，請另一個模型盲寫成自然語言請求；gold 由合約機械算出，我抽查。這可以解決保留題庫快用完的問題（已看過 23 組以上），也避免繼續在 56 題上調。

---

## 6. 階段、成本與門檻

| 階段 | 內容 | 花費 | 通過門檻 |
|---|---|---|---|
| **0 先證偽**（不寫功能） | 預設值表與選單從 YAML / sheet 產生；決策表寫成純函式 + 窮舉單元測試；把 56 題的金標讀取寫好 | US$0 | 用**金標讀取**跑決策表，56 題 ≥ 52 題正確。不到就代表決策表本身有洞，先修表，不往下做 |
| **1 離線讀取** | 只呼叫 `MenuReading`（不跑完整 session）：開發集（m3、accept24、heldout）先調 schema 形狀，最後 56 題 × 2 次只量一次 | 約 US$0.3（mini） | 各維度讀取準確率；kind 一致率 ≥ 90%；vague 被拒 ≤ 1；dont 的對拒絕不少於現在 |
| **2 shadow** | 接進 `classify_task`，和現有 `decide_core` 並行寫 trace，不改回覆 | ≤ 20 個 session，先報備 | 新舊不同的題逐題看，新的錯誤要可解釋 |
| **3 切換 + 刪除** | 決策表生效；移除第 4 節列出的路徑；回覆接地檢查 | 單元測試 + 錄製資料重放 | G4（判定與回覆 0 不一致）維持 |
| **4 驗收** | 第 5 節的合約生成新題庫，盲寫 | 約 60 題 × 1 次 | do / dont / ask / vague 各類門檻沿用 spec 第 8 節；另加 kind 一致率 ≥ 90% |

遵守既有規則：

- 每階段先報備 session 數與費用（lean testing）。
- 不在 56 題上調設計（第 1 階段只在開發集上調，56 題只量一次）。
- 階段中不換設計；要換先寫進變更紀錄，經你同意。

---

## 7. 風險與會失去的東西

- **forced-choice 偏向清單內**：Log 385 的舊 router 就是因為沒有「以上皆非」，把請求投射到最近的結果。這次有明確的 `outside` 值，且必須附逐字的 `outside_name`；第 1 階段要專門量 dont 類的 outside 召回。
- **預設值表是新的人為判斷**：例如「沒說 granularity 就是 aggregate」。它必須寫在 YAML 裡、可審查，不寫在程式裡。表的每一列都要你確認。
- **5b、5c 的成果會被併入而不是保留原樣**：C45（蛋白數量）會變成 `facts.feature_count = conflicting`；C24 會變成 artifact `not_stated` → CLARIFY。第 0 階段要確認這些題在金標讀取下仍然判對。
- **這是一次中型重構**：讀取層換掉，但 run 閘、輸入檢查、回覆模板、`CoreDecision` 型別都沿用。

---

## 8. 需要你決定的事

1. 是否同意第 2 節第 3 條：「做不到必須有正面證據；沒對到算不確定，不算做不到」。
2. 第 3.3 節預設值表的每一列，特別是 granularity 預設 aggregate。
3. 「選哪個結果」的 ASK 不需要使用者說不確定；「資料事實」的 ASK 仍需要。這個分法是否同意。
4. 第 3.6 節的兩次讀取一致性，是否列為第 1 階段的量測項目（不另花錢）。
5. 先做第 0 階段（零成本、可證偽），結果出來再決定是否往下。

---


## 9. 欄位清單草案 3（第 0 階段，2026-10-18，待確認）

- 檔案：`scripts/judgment_defaults.yaml`
- 載入檢查：`scripts/netzoo_agent_core/judgment_defaults.py`
- 測試：`tests/test_judgment_defaults.py`（28 項通過，含 3.9 節的 C1–C4）
- **這份清單只依據合約、sheet，以及 Log 385–414 累積的 typed 欄位擬定，沒有參考 56 題題庫。**

### 9.1 結果類型詞彙

| 類型 | 意思 | sheet 條目 |
|---|---|---|
| regulatory_network | 調控因子→基因的加權網路 | PANDA、PUMA、LIONESS-PANDA、LIONESS-PUMA、OTTER、GIRAFFE 的 signed matrix |
| targeting_scores | 每個 TF 的 out-degree、每個基因的 in-degree | PANDA、PUMA、OTTER、LIONESS-PANDA、LIONESS-PUMA（with_step） |
| tf_activity | 每個樣本中每個 TF 的活性 | GIRAFFE |
| coexpression_network | 基因–基因共表現網路 | LIONESS-COEXPRESSION、BONOBO |
| covariate_adjustment | 依共變量拆分或校正的共表現（及接著建的網路） | COBRA |
| multi_omic_network | 兩層 omics 的偏相關網路 | DRAGON、LIONESS-DRAGON |
| edge_significance | 每條邊的 p 值 | DRAGON |
| communities | 社群與核心分數 | CONDOR |
| community_enrichment | 社群的通路富集 | CONDOR（with_step） |
| patient_subtypes | 依體細胞突變分型 | SAMBAR |
| comparison | 上面某個結果的比較（NetZoo 外的步驟） | 8 個 with_step 條目，各自記錄比較的對象 |

問題大類（候選超過 3 種時先問）：基因之間的關聯／調控因子對基因／兩種 omics 之間的關聯／分群與分型。

### 9.2 欄位（25 個，分四類）

**「推斷」的標準（草案 3，使用者決定）**：只有和明說一樣清楚的字句才算推斷。「a network」只代表要網路型結果，不代表對所有樣本或所有層只建一個。

**意圖（11 個）：不設預設值，會分開候選時就追問**

| 欄位 | 值 | 什麼才算有說 | 狀態 |
|---|---|---|---|
| 結果類型 | 上面 10 種 + 清單外 | 使用者點名結果；清單外的要有原文（例如「filtered VCF」） | 草案 2 已有 |
| 點名的 workflow | 程式從原文數 + 未註冊的方法 | 未註冊的方法（TIGER、LIONESS-OTTER、DESeq2）為清單外 | 草案 2 已有，**加入未註冊方法** |
| **integration** | 整合成一個 ／ 各層各一個 | 只有連結各層的字句才算，例如「between miRNAs and cytokines」「within and across the two layers」「one integrated network across all layers」；有兩層資料本身不算 | **新增**（你提的） |
| granularity | 整體一個 ／ **每組一個** ／ 每個樣本一個 | 例如「that patient's own network」「one network per diagnostic group」；「a network」不算 | **加入「每組一個」** |
| regulators | 只有 TF ／ TF＋miRNA ＋ 清單外（lncRNA、RBP、splicing factor） | 只有點名調控因子才算；有 motif prior 不代表沒有 miRNA | **改嚴**：不再由資料推斷 |
| layers | 兩層 ＋ 清單外（三層以上一起建模） | 整合時剛好說了兩層就是這兩層；三層以上要問哪一對 | 草案 2 已有 |
| signed | signed ／ unsigned | 沒要求就兩種都列給使用者選（方法平手） | 草案 2 已有 |
| compare | 不比較 ／ **並列比較 ／ 統計檢定** | 沒提就是不比較；「之後要比較」是目的。統計檢定需要逐樣本結果 | **加入比較的種類** |
| requirements | 合約符合 ／ 合約矛盾 ／ 合約沒提 | 使用者對算法或內容的要求（「convex」「用我們的 miRNA 表現量加權」）；矛盾就不能做，沒提就問是不是必要條件 | **新增** |
| claims | 關聯 ＋ 清單外（因果、預測模型） | — | **新增**（原本由另一個讀取角色處理） |
| delivery | 寫成檔案 ＋ 清單外（寄送、上傳、儀表板） | — | **新增** |

**資料條件（9 個）：用預設值並寫在「我先假設」，使用者說不確定才問**

| 欄位 | 預設 | 清單外 | 狀態 |
|---|---|---|---|
| data_unit | bulk | single cell | 已有 |
| **data_stage** | 已處理好的表格 | FASTQ／BAM／peak 檔：說明需要先在 NetZoo 外處理，不代做、不編步驟 | **新增**（VP5q 的已知漏洞） |
| mutation_origin | somatic | germline | 已有 |
| value_type | 連續值 | 二元值 | 已有 |
| mirna_driver | target prior | 用 miRNA 表現量 | 已有 |
| time_model／spatial／group_membership | 非動態／非空間／每項只屬一組 | 動態模型／空間鄰近／重疊分組 | 已有 |
| **input_network** | 執行前檢查（CONDOR 會警告節點 ID 重疊） | gene–gene 網路 | **新增**（sheet 有，草案 2 漏了） |

**執行前檢查（4 個）：不問**：樣本數、特徵數、兩層是否同一批樣本、有哪些資料。有哪些資料這一欄另有兩個作用：用來縮小可提供的結果（例如分型需要突變資料）；明說沒有某項資料時，需要它的 workflow 不能做。

**設定（1 個）**：必須對到 control 和允許值；不是 control、超出範圍、違反組合限制 → 不能做。檔案格式不在 control 裡 → 說明是 NetZoo 外的轉換步驟，不拒絕。

### 9.3 機械檢查的結果

- C1：13 個 workflow 的結果兩兩比較，分不開的只有 PANDA 與 OTTER（同樣是整體 TF 網路），列為方法平手，兩個都給使用者選。
- C2：35 個 near-miss／registry-wide 條目都有欄位可以擋。
- C3：9 條 request-scope 限制都有欄位負責。
- C4：25 個欄位沒有閒置的。
- 驗證過檢查會抓錯：把方法平手拿掉，C1 就失敗。

### 9.4 請確認

1. 新增與修改的欄位（上表標**粗體**的部分），特別是：
   - integration 的推斷標準；
   - granularity 加入「每組一個」；
   - regulators 改成只有點名才算。這會讓「regulatory network」沒說 TF 時也要問。
2. 方法平手的處理：PANDA／OTTER、signed／unsigned 都列給使用者選，不替使用者決定。
3. 「合約沒提」的要求要追問，而不是假設符合。
4. 追問流程參數：每輪 2 題、每題 3 個選項、最多 3 輪。

### 9.5 依歷史資料的評估（草案 4，2026-10-18）

資料：10 個開發用題組（heldout11–19、accept24、m3 heldout），去重後的請求，**不含 56 題**。腳本是一次性的文字統計，只用來評估規則，不會進入執行時的判斷。

**regulators：改用「附加型」規則**

| 規則 | 108 個調控類請求的結果 |
|---|---|
| 草案 3：沒點名 TF 或 miRNA 就問 | 問 27 次（25%），其中 **0 次**真的需要 miRNA workflow；2 次 TF 或 miRNA 都可以 |
| **草案 4：完全沒提 miRNA → 只有 TF；有提但沒說角色 → 問** | 沒提 miRNA 的 93 個請求，**0 個**需要 miRNA workflow；有提 miRNA 的 15 個，**15 個**都需要 |

**原則**：使用者必須主動要求的「附加項」（miRNA 調控、比較、檢定），完全沒提就是沒要，不算不清楚。兩種讀法都說得通的（整體一個或多個、整合或分層、要哪種結果），沒明說就問。

**granularity：照你的規則追問，代價是多一個問題**

- 138 個網路類請求中，有 53 個點名了單一 workflow，scale 已經確定，不會問。
- 沒有任何 scale 字句、會被問的有 19 個（14%）。
  - 其中 16 個的 gold 是整體一個，3 個兩種都可以。
  - 大多是 multi-omic 請求，例如「a partial-correlation network linking them」：要在 DRAGON 和 LIONESS-DRAGON 之間選。
- 歷史上**沒有任何一題**想要每個樣本一個網路、卻沒寫出來。
- 兩個選項，由你決定：
  - **A（目前的決定）**：沒明說就問。約 14% 的請求多一個問題；好處是不依賴「使用者會主動說每個樣本」這個經驗規律。
  - **B**：把「每個樣本一個」當附加項。沒提就是整體一個；但請求裡提到分組或條件（例如 AD 與 control）時，仍然要問整體一個或每組一個。依歷史資料，這樣不會多問，也沒有錯誤。

**integration：維持你的規則。** 歷史上的 multi-omic 請求幾乎都會寫連結字句（linking、between、two-layer），所以很少觸發追問，代價低。

**新增的 8 個欄位：都對應到歷史上的失敗，建議全部保留**

| 欄位 | 對應的失敗 |
|---|---|
| 未註冊方法 | accept24 N36（TIGER）、N12（LIONESS-OTTER） |
| compare 種類 | accept24 N15（差異模組度）、cobra.no_pair_significance |
| requirements | Log 414 的 how_computed／what_it_contains |
| claims、delivery | accept24 MX02（儀表板）、MX14（每週自動重跑） |
| data_stage | VP5q（read alignment） |
| input_network | heldout416b F46（CONDOR，不確定是 gene–gene 還是 TF–gene） |
| granularity 的「每組一個」 | heldout416b 的 per group 與 per donor |

### 9.6 方法平手的選項說明（草案 5，使用者決定）

平手時列出所有選項，不替使用者選。

- **給使用者看的**：只寫兩件事：
  - 針對這個問題，各選項差在哪；
  - 各選項適合什麼需求、為什麼。
- **不給使用者看的**：演算法機制。演算法背後的邏輯（YAML 的 `logic`，附 `source`）只在內部用來判斷哪個選項符合需求，也供審閱。
- **對應到使用者的話**：使用者說過的欄位符合某個選項的 `fits_when` 時，例如「只有共表現矩陣」對上 OTTER，回覆會寫「你說了…，所以 X 比較適合」。這一步由程式依欄位比對，不由模型自由發揮。
- 所有文字都事先寫在 YAML，回覆時不由模型另寫。

中文審閱版：

**整體一個 TF→基因網路：PANDA／OTTER／GIRAFFE**

| | 差在哪 | 適合什麼需求 |
|---|---|---|
| PANDA | NetZoo 的標準網路；每條邊代表你的 motif、PPI、表現量資料對「這個 TF 調控這個基因」有多一致 | 想和已發表的 PANDA 網路比較，或之後要在同一份網路上做每樣本網路（LIONESS-PANDA）或社群（CONDOR） |
| OTTER | 可以自己決定共表現和 PPI 各占多少比重；沒有表現量檔、只有共表現矩陣也能做 | 只有共表現矩陣，或想自己控制兩種證據的比重（**你說只有共表現矩陣時，回覆會標出它比較適合**） |
| GIRAFFE | 看得出每個 TF 對每個基因是活化還是抑制，也會給每個樣本的 TF 活性；不能調設定 | 問題和活化或抑制有關，或也需要每個樣本的 TF 活性 |

**整體的 targeting 分數：PANDA／OTTER**

| | 差在哪 | 適合什麼需求 |
|---|---|---|
| PANDA | 用標準基礎算，可以和已發表的 PANDA targeting 分析比較 | 要和其他 PANDA 研究比較，或之後和 LIONESS-PANDA 的每樣本 targeting 比較 |
| OTTER | 可以設共表現和 PPI 的比重，能從共表現矩陣開始；分數只能和其他 OTTER 結果比較 | 只有共表現矩陣，或想控制比重 |

**每個樣本一個共表現網路：LIONESS-COEXPRESSION／BONOBO**

| | 差在哪 | 適合什麼需求 |
|---|---|---|
| LIONESS-COEXPRESSION | 也會給整體網路，每個樣本的網路和它在同一尺度，可以拿個別樣本對照整體；資料不需要額外前處理 | 想把個別樣本和整體放在一起看，或資料沒有做 log 轉換和中心化 |
| BONOBO | 可以給每個樣本的每條邊一個 p 值，只留顯著的邊；沒有整體網路，資料要先 log 轉換、中心化 | 需要每個樣本的邊顯著性，或想要較稀疏的網路 |

## 10. 變更紀錄

- **2026-10-18 使用者同意方向，開始第 0 階段**：第 8 節的第 1、5 點已決定。
- **2026-10-18 使用者決定：不清楚的意圖要追問、確定後才填欄位。**
  - 新增第 3.8 節追問迴圈。
  - `Said` 加上 `basis`。
  - 第 3.3 節改成四類維度。
  - CLARIFY 與「選哪個結果」的 ASK 由同一個迴圈產生。
  - 第 8 節第 3 點由第 3.8 節取代。
- **2026-10-18 使用者決定：「a network」不推斷為整體一個。** 只有和明說一樣清楚的字句才算推斷；「整體一個／分層多個」會改變判定時，視為目標不明，需要釐清。
  - 新增 integration 欄位。
  - granularity 改為三個值。
  - regulators 不再由資料推斷。
- **2026-10-18 欄位齊全性**：新增第 3.9 節（C1–C4 機械檢查）與第 3.10 節（判定的結局）。依合約與 Log 385–414 的 typed 欄位核對後，補上 8 個欄位：未註冊方法、比較種類、requirements、claims、delivery、data_stage、input_network，以及 granularity 的「每組一個」。
- **2026-10-18 草案 4（使用者決定與依歷史資料的評估）**：
  - regulators 改用「附加型」規則（第 9.5 節）；新增 policy `extra`，compare 也改用它。
  - 方法平手時，每個選項列出怎麼做、好處、什麼情況選、限制，文字取自合約（第 9.6 節，YAML `tie_options`），回覆時不由模型另寫。
  - 可以進入執行的條件：硬條件一票否決；意圖沒確定就問；合約沒寫到的使用者要求用 80% 門檻（第 3.10 節）。
  - 追問流程參數（每輪 2 題、每題 3 個選項、最多 3 輪）定案。
  - granularity 的 A／B 待使用者決定（第 9.5 節）。
- **2026-10-18 草案 5（使用者確認，預設值表定案）**：
  - granularity 用 A，沒明說就問。
  - 平手選項只寫「差在哪、適合什麼需求」，演算法邏輯只在內部使用（`logic`），並用 `fits_when` 依欄位標出比較適合的選項。
  - 合約沒寫到的要求，門檻由 80% 改為 90%：不到就追問；3 輪後仍不到，就逐項確認後才放行。
  - 追問流程參數定案。
- **2026-10-18 第 0 階段完成**（結果見 `docs/research-log/closed-menu-phase0-2026-10-18/RESULTS-P0.md`）：
  - 門檻 56/56。
  - 漏讀一個欄位：86% 不變、7% 變成追問、6% 判錯。判錯的都屬限制類與疑問類欄位。
  - 寫讀取時補上的實作細節（不改設計方向）：
    - 不確定時用使用者自己的選項發問。
    - 結果沒說是 CLARIFY，點名兩個具體結果是 ASK。
    - 使用者的要求縮小平手。
    - 沒指定 workflow 的設定要對每個候選檢查。
    - `required_settings`。
    - `unsure_files`：run 時由輸入檢查確認。
    - 二元值也排除表現量類 workflow。
  - 漏讀檢查後補上的規則：
    - 沒點名的結果一律確認。
    - 資料裡有 miRNA 就算有提到 miRNA。
    - `context_mentions`：只當背景提到的方法不算點名。
- **2026-10-18 第 1 階段完成**（結果見 `docs/research-log/closed-menu-phase1-2026-10-18/RESULTS-P1.md`）：讀取＋聚焦重讀，限制召回 138/154、疑問 28/32、kind 一致 52/56；判定 74/112，低於現行系統。
- **2026-10-18 使用者同意第 1b 階段的修正**（依第 1 階段的錯誤分析）：
  - 要求的合約核對：met／contradicted 必須引用該 workflow 合約原文，程式逐字核對，否則算 not_addressed。
  - 結果讀取加入「在 workflow 之間選擇」；結果未定且沒有列出選項時一律問目標。
  - 程式找到的每個註冊名稱各有角色（target／choice／background）。
  - 聚焦重讀加入「候選都沒有的設定」。
  - 在全新的盲寫題組上，和現行系統並列比較。
- **2026-10-18 使用者決定：加入「意圖聚焦確認」，當成獨立變體量測。** 使用者原話：「同意加入「意圖聚焦確認」：程式找出會改變判定的意圖欄位，模型逐一回答小問題並附原文，兩次不一致就問使用者。請在三步完成後，當成獨立的變體量測。」
  - 只確認會改變判定的意圖欄位：結果類型（或方法選擇）、integration、granularity、regulators、layers。「會改變判定」= 留有候選的值之間判定不同（`deciding_intents`）。其他欄位一律不確認。
  - 每個欄位一個封閉小問題：選項是選單值（標籤取自 `judgment_defaults.yaml`）加「沒說」；回答必須逐字引用原文，程式核對。
  - 合併（`merge_intent`，純程式）：一致就保留；不一致、沒有核對過的引文，或第一次說了值而確認說「沒說」→ 該欄位轉為不清楚（conflicting，或結果保持未定），追問使用者；第一次沒說、確認給出核對過的明說值 → 採用，basis explicit。
  - 這符合第 3.8 節：意圖不替使用者猜，兩次讀取不一致就問。
- **2026-10-18 第 1b 階段與意圖聚焦確認的結果**（`docs/research-log/closed-menu-phase1b-2026-10-18/`）：
  - 全新盲寫題組 h1：現行系統 37/48，新讀取 33/48，意圖確認 28/48。
  - 意圖確認不納入預設流程。
- **2026-10-18 使用者決定：先給選項（options-first）。** 使用者原話：「我覺得你填不了的原因分這兩種 可以照這樣去做 就是使用者沒講 給選項或追問，不是無法執行 然後使用者要的是清單外的東西，或違反合約（例如 single cell、參數超出範圍） 無法執行，說明原因（附合約原文），並給最接近、可以做的選項 ／ 你講的我都同意 可以開始照你講的東西開始實作 不能做的就明確說不能做 模糊的話就追問使用者」
  - **兩種「填不了」**：
    - 使用者沒講 → 給選項或追問，絕不說「無法執行」。
    - 使用者要的是清單外的東西，或違反合約（single cell、參數超出範圍…）→ 無法執行：明確說不能做，附合約原文說明原因，並給最接近、可以做的選項。
  - **模糊（CLARIFY）要有正面證據**，附原文，必須是下列之一：
    - 沒有點名任何結果，只有目的或主題；
    - 只有泛稱（「network analysis」「how genes are connected」）；
    - 在方法之間選擇，沒有點名結果。
  - 結果被讀成「不確定、但沒有列出選項」**不算模糊**：程式依點名的 workflow、資料與其他欄位推斷結果；只剩一個結果時，就去問真正的疑問。
  - 同一輪可以同時問結果和決定性的疑問（每輪最多 2 題），**不能把讀對的疑問藏在結果問題後面**。
  - 沒點名的結果、資料只容許一個選項時，仍要確認：用只有一個選項的選項卡。
  - **選項卡是判定的輸出**（`MenuDecision.options`），和原本的 kind 相容：
    - 最多 3 個可行選項。排序先看是否通過全部硬條件，再看符合比例（使用者說過、與該選項相關的欄位中，該選項符合幾個，給使用者看「符合你說的 10 點中的 9 點」），最後看平手順序。
    - 每個選項附：差在哪、適合什麼需求（tie_options，沒有就用 sheet）、「符合你說的」（附原文）、「還要確認」。
    - 不可行的候選另列：「不能做，因為…」＋合約原文，絕不混在選項裡。
    - 保留一個自由輸入列：使用者可以自己打想用的套件。
    - 只剩一個選項、而且會改變判定的欄位都已確認 → DO；執行仍需使用者同意。
    - ASK、CLARIFY 也帶選項，外加決定性事實的問題。
    - DECLINE 給明確理由，以及最接近、可以做的選項。
    - 合約沒提的要求，9/10 門檻不變，逐個選項套用。
  - **設定只從候選 workflow 的 control 讀**：描述資料（「header present」）或輸出位置（「put everything in X/」）的字句不是設定（h1 的 H23、H45）。
  - **英文回覆渲染**：照 AGENTS.md，給使用者的輸出是英文。
    - 必須直接寫「NetZoo cannot do X because …」並附合約原文，列出選項與說明，並提出問題。
    - 這些文字不由模型在回覆時撰寫。
  - **現行系統的混合閘門**：把硬條件元件移植到現行流程，在任何東西被當成可執行之前檢查。
    - 元件：附原文的要求合約核對、不支援的設定、明說沒有的資料。
    - 保留現行系統自己的追問路徑。
  - **新的盲寫題組 h2**：三組並列（現行、現行＋混合閘門、先給選項），量四個指標：
    - 正確的 workflow 是否在提供的可行選項中；
    - 是否沒有把不可行的選項當成可執行；
    - 選項清單長度；
    - 需要時是否問了決定性的事實。
    - 舊的嚴格分數一併列出作參考。

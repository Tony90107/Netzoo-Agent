# 提案：研究目的契約（`comparison_design`／`claim_kind`）

狀態：**提案，待使用者決定**。尚未宣告，沒有改任何程式碼。
日期／時區：2026-10-04，Asia/Taipei。
基準：HEAD `18b6358`，指紋 legacy `e920bf3b5d57`、claims `743b2dd0d73a`（`docs/research-log/tools/fingerprint.py`，本日重算）。
依據：Log 340–341（最小對照組）。

---

## 1. 要解決的問題

### 1.1 Log 341 看到的行為

輸入相同、只換最後一句研究目的時：

- 目的能對應到既有型別欄位，候選就會分開：
  - per-sample → LIONESS-PANDA
  - TF activity → GIRAFFE
  - 分群 → `GUIDANCE_COMPOSITIONS`
- 目的只差在「誰跟誰比」或「想下什麼結論」時，結果相同：
  - A0 對照組（一個網路概括 48 份樣本）與 A1（網路是否在治療後改變）的回覆，只有最後一句追問不同。
  - 卡片都寫「Understood goal: a cohort-level TF-gene regulatory network」。
- 27 次回覆中，比較步驟 0 次，因果限制 0/3，「沒有工具能建預測模型」0/3。
  - B3（預測）3/3 都變成 `semantic_fallback`，顯示「系統無法驗證解讀」。
- A2 說「for your 24 patients, 25 PANDA runs」，實際是 48 份樣本、應為 49 次：`practical_notes._COUNT` 把病人數當樣本數。

### 1.2 遺失發生在哪裡

- 理解階段有引用目的句。例如 A1 的證據有「regulatory network changes after treatment」，B1 有「gene co-expression differs between responders and non-responders」。
- 型別欄位只有 operation／artifact_type／granularity：A0 與 A1 都是 `infer regulatory_network aggregate`。
- 下游只讀型別欄位，所以引文存在卻沒有任何階段使用。

### 1.3 需要的內容其實大多已經存在

- `_AGGREGATE_TARGETING_NOTES`（`workflow_registry.py`）已寫好：「比較條件需要每個條件各跑一次、輸入對齊；比較各網路的 out-degree 可看出 targeting 改變的調控子」。
- `_LIONESS_TARGETING_NOTES` 與 `DOWNSTREAM_ANALYSES` 已寫好 LIONESS 網路不獨立、per-sample 分數與臨床變數關聯等說明。
- 但這些只在 downstream_use concern 被宣告時才出現（Log 336）。A1 沒有出現，因為沒有任何型別訊號說「這是比較」。
- `concept_answers._render_beginner_group_network_guidance`（6a72164，2026-09-25）是同一需求的特例：
  - 觸發條件很窄：PANDA 在平手中、TF-gene、問題是「which modeling assumption」、請求含 between/compare…groups。
  - 文字寫死「between cancer and normal groups」，B1 這種 responders 比較若觸發也會說成 cancer／normal。
  - A1 的「changes after treatment」沒有觸發它。

### 1.4 現有語料測不到這個能力

- 所有 traced 錄音（3,592 列、78 個不重複請求、56 個英文）用草擬的字詞掃描：
  - paired 1（誤中：「For the same individuals I have gene expression … and methylation」，是多體學配對，不是前後）
  - groups 0、causal 0
  - prediction 1（誤中：「predicted targets」）
- 使用者實際 session（`.netzoo/sessions`，排除 mp-／t10-，236 則不重複訊息）則有：
  - 「兩組病人（癌症 vs. 正常）… 這兩組之間有沒有什麼關鍵的轉錄…」（群體差異＋調控子）
  - 「tumor subtyping to predict chemoresistance」（分群後預測）
  - 「This is not causal」（否定句，witness 必須排除）
- 結論：
  - 改動在既有語料幾乎不會觸發，所以 no-op 檢查容易做。
  - 但效果必須用新的最小對照組測，既有 corpus 沒有能力回答這個問題。

---

## 2. 目標與非目標

**目標**
- **G1**：回覆說出這個方法對使用者的問題提供什麼證據、還需要哪一步、不能支持什麼。適用於每個呈現的 workflow，前提是請求明說了比較設計或結論類型。
- **G2**：平手時，若已說明的結論類型能區分候選，依 registry 宣告給有條件的推薦。若比較設計已說明、結論類型沒說明，先問結論類型，而不是問計算資源或 miRNA。
- **G3**：範圍外的目的（因果、預測）得到明確的能力缺口說明，而不是錯誤訊息。

**非目標（以及理由）**
- 不改 first-pass prompt 或 schema。
  - 約 200 token 的額外長度曾讓 case 2 的 method tag 從 10/10 掉到 0/10（Log 233）。
  - `named_methods` 欄位 9/9 是空的（Log 130）。
  - 措辭修正是禁用手段。
- 不新增 LLM 呼叫，也不讓 LLM 判斷「是否適合」。
  - CC1（Logs 288–289）的 review 會自創 method tag，寫出「沒有已登錄 workflow」的假缺口。
- 不新增可執行 workflow。比較或檢定步驟屬於 NetZoo 外，只以文字指引呈現，跟 `OutsideStep` 一樣。
- 不排除任何候選。輸入輸出相容仍是進入候選的唯一條件。
- 不處理中文 gate（英文優先），中文結果另列。
- 不碰授權與執行層（診斷報告 F1–F7 另案）。

---

## 3. 設計

### 3.1 請求側：兩個封閉值，由字詞 witness 決定

**v1 為什麼不讓模型填：**
- Log 341 中，`selection_conditions` 在 A0 對照組也拿目的句來宣告 `tf_activity_vs_expression` 和 `established_method`，3/3 都被 witness 擋下。A1、A4、A5 也一樣。
- 模型會把目的句複製給任何提供的選項。如果新增一個讓模型填的 `claim_kind`，最可能的結果是同樣不分青紅皂白，最後還是要靠 witness 把關。所以 v1 直接只用 witness。

**值與定義**（未命中＝unknown＝行為與現在完全相同）：

| 欄位 | 值 | 定義 | 例句（Log 340） |
|---|---|---|---|
| `comparison_design` | `paired` | 同一批個體在兩個以上的時間點或處理下取樣 | A：「each sampled before and after treatment」 |
| | `groups` | 不同個體分成兩組以上 | B：「30 responders and 30 non-responders」 |
| `claim_kind` | `group_difference` | 群體層級是否不同或改變 | A1、B1 |
| | `individual_change` | 哪些個體不同或改變最多 | A2 |
| | `regulator_change` | 哪些調控子改變最多 | A3；使用者 session 的「哪些關鍵轉錄因子」 |
| | `causal` | 主張 X 造成 Y | A4 |
| | `prediction` | 對新樣本預測結果 | B3 |

- 分群不另設值：沿用 `sample_cluster_assignment` 與 `READING_WITNESSES`，不重複。
- 「描述一個網路」不設值：就是 unknown。

**witness 規則**（完整字詞表在宣告時寫定）：
- 引文取 witness 所在的整句（`_sentence_at`，同 Log 336）。卡片與回覆引用使用者自己的話。
- **否定排除**：witness 前 6 個詞內有 not／no／without／rather than／instead of 時不算。依據是使用者 session 中真實的「This is not causal」。
- **已知誤中**（第 1.4 節）：「predicted targets」不算 prediction；「the same individuals」要搭配時間或處理字詞才算 paired。
- **重疊**：`READING_WITNESSES["sample_cluster_assignment"]` 含 `classif`。「classifier」會同時命中分群與 prediction，宣告前要決定優先序（建議：明說 predict／new patient 時以 prediction 為準）。
- 數字不是 witness（同 Log 315 的 cohort_size 規則）。「24 patients」不構成任何設計。

**實作位置**：新增 `routing/study_purpose.py`，內含 `study_purpose(task) -> StudyPurpose(design, design_quote, claim, claim_quote)`。
- 純函式，在 routing 結束時記錄事件 `routing.study_purpose_detected`。
- 回覆層用同一函式重算，所以 `TaskDecision` 與 provider schema 都不變。

### 3.2 registry 側：`CLAIM_SUPPORT` 表（Python-only，不進任何 prompt）

**為什麼不用既有的 `scientific_objectives`：** `contracts/policy.py:195` 會把它寫進模型可見文字（「Objectives: …」）。改它會動到指紋，也增加 prompt 長度。新表比照 `GUIDANCE_COMPOSITIONS`／`OUTSIDE_STEPS`／`DOWNSTREAM_ANALYSES`：不屬於 policy snapshot，路由永遠不讀它來選工具。

**形狀**（草案）：

```python
class ClaimSupport(NamedTuple):
    level: Literal["direct", "with_step"]   # 沒有 "no"：見下方規則
    gives: str          # 這個 workflow 為此結論提供什麼
    step: str           # 還需要的步驟（NetZoo 外），direct 時可為空
    caveats: tuple[str, ...]

CLAIM_SUPPORT: Mapping[tuple[str, str, str], ClaimSupport]   # (action, claim_kind, design or "*")
UNSUPPORTED_CLAIMS: Mapping[str, str]                        # causal、prediction：全域缺口說明
```

**關鍵規則：未宣告 ≠ 不支持。**
- 只有 `UNSUPPORTED_CLAIMS` 會產生「做不到」的句子，而且它對所有 workflow 一體適用，不需要逐一判斷。
- 某格沒有宣告時，回覆就不說任何話，回到現狀。
- 這是針對 CC1 失敗形狀的結構性防護：缺口只能來自人寫、明確的全域宣告，不能從「查不到」推出來。

**v1 要填的格子**（草稿；每句上線前都要對照 netZoo 文件或論文查證，標準同 Log 320）：

| workflow | `group_difference` | `individual_change` | `regulator_change` |
|---|---|---|---|
| PANDA／PUMA／OTTER（整體） | with_step：每組或每個時間點各建一個網路，比較邊權重。paired 時加註：整體網路比較會丟掉配對資訊，要保留配對需改用 LIONESS-* | 不宣告。LIONESS-* 與 GIRAFFE 已經是另一組候選 | with_step：每個條件各建一個網路後比較 out-degree（沿用 `_AGGREGATE_TARGETING_NOTES`） |
| LIONESS-PANDA／PUMA | with_step：per-sample 摘要（邊或 out-degree）做配對或組間檢定；加註 LIONESS 不獨立；樣本數＝個體 × 時間點 | with_step：每位個體各時間點的差值 | with_step：per-sample out-degree，配對或組間檢定 |
| GIRAFFE | with_step：TF 活性矩陣做配對或組間檢定 | with_step：每位個體的 TF 活性差值 | with_step（同 group_difference，以 TF 為單位報告） |
| COBRA | **direct？（待查證）**：組別放進 design matrix，取該共變數的共表現成分 | 不宣告 | 不宣告 |
| LIONESS-COEXPRESSION／BONOBO | with_step：per-sample 基因 degree 做組間或配對檢定（沿用 `DOWNSTREAM_ANALYSES` 的句子） | with_step | 不宣告（共表現沒有調控子） |

- CONDOR、SAMBAR、DRAGON、LIONESS-DRAGON 在 v1 不宣告，保持沉默。
- 差異模組化沿用既有 `OutsideStep`（ALPACA）。

**`UNSUPPORTED_CLAIMS`**（草稿）：
- `causal`：已登錄的方法都是從觀察性資料估計關聯或模型係數，不能證明因果。沒有未處理對照組的前後比較，也無法把改變歸因於處理本身。網路結果能描述改變，不能證明處理造成改變。
- `prediction`：沒有已登錄 workflow 產生預測模型。per-sample 網路摘要（out-degree、TF 活性）可以作為外部分類器的特徵，但需要獨立的驗證資料。

### 3.3 決策側：分兩階段，各自宣告、各自撤回

**階段 1：只改回覆，所有決策欄位不變**

1. **目的段落。** 呈現 workflow 的回覆中，若 `claim_kind` 已知，加一段「For your question」，內容取自 `CLAIM_SUPPORT[(action, claim, design or "*")]` 的 gives／step／caveats。位置：結尾段落之上（`inspected_answers.above_closing`）。v1 只在單一讀法時加；多讀法（`hypothesis_routes`）延後。
2. **全域缺口。** `claim_kind ∈ {causal, prediction}` 時加入 `UNSUPPORTED_CLAIMS` 的句子，而且排在候選清單之前，不讓回覆說「These all fit」。
3. **B3 路徑。** `semantic_fallback` 且 witness 為 causal 或 prediction 時，回覆改成缺口說明加上網路能提供的部分，而不是「could not validate」。
   - 這是失敗路徑上的回覆改動，決策仍是 no_tool。
   - Log 226 曾因用字串替換接進 `_semantic_failure` 而讓整輪作廢，所以必須有 wiring test。
4. **取代 6a72164 的特例。** `_render_beginner_group_network_guidance` 改由同一張表產生，文字不再寫死 cancer／normal。既有測試 `test_beginner_group_network_guidance_does_not_ask_for_algorithm_assumptions` 的修改要在宣告中列出。
5. **（選擇性，待你決定）A2 樣本數。** `design=paired` 且引文說明每位個體的時間點數時（before and after＝2），practical note 改說「24 patients × 2 = 48 samples → 49 PANDA runs」。無法確定倍數時，不引用病人數。

**階段 2：選擇層，候選集合不變，只影響推薦與追問**

- **(a) 推薦。** 平手中，對已說明的（claim, design），若剛好有一部分候選是 `direct`、其他是 `with_step`，就有條件地推薦 `direct` 那部分，並引用請求原句（同 PW 規則：推薦必須有引文 witness）。例：B1 → COBRA（前提是查證成立）。
- **(b) 追問。** `comparison_design` 已知、`claim_kind` unknown，而且平手候選對不同 claim 的支持方式不同時，卡片問題改成結論類型。例如：「Do you want to know whether the cohort as a whole changes, which patients change most, or which regulators change most?」（A5）。這只取代沒有 witness 的追問軸。
- **(c) 永不做的事。** 不新增或移除候選；不從「未宣告」推出缺口；不呼叫模型。
- **實作。** 在 `invoke_condition_recommender` 之前做確定性判斷，解決了就不呼叫 condition recommender（省一次呼叫）。condition recommender 的 prompt 不變。
- 呼叫序列的 pinned test 修改要事前宣告（Log 140 曾因此撤回）。

---

## 4. 評估與 gate（宣告時寫定，不事後重解）

### 4.1 語料

- **開發集**：Log 340 的 9 句與其錄下的決策，可以離線重播。
- **保留集**：
  - 寫程式之前寫好，宣告 commit 時記下 sha256，不拿來調整 witness，最後只跑一次。
  - 建議 6 個家族、每個 4 句，共約 24 句。
  - 每個家族共用同一句資料描述，只換目的；每個家族至少 1 個對照（描述型、無 claim）。
  - 另加 2 個否定陷阱（「this is not a causal analysis」「we are not trying to predict」）。
  - 家族建議：多時間點時序（paired）、tumor vs normal（groups，有 TF prior）、藥物處理細胞株（paired，只有表現量）、性別差異（groups，只有表現量）、knockdown 後「證明 X 造成 Y」（causal）、per-sample 網路預測預後（prediction）。
  - 每句事前寫下：設計、結論類型、可接受候選、回覆必須包含的句意、紅旗。
  - 格式依使用者偏好：一段、英文 25–35 字、不點名工具或檔案。

### 4.2 離線 gate（每個階段都要過）

- **O1**：全套件通過；兩個指紋與 condition recommender prompt hash 不變（兩個階段都不應改任何 prompt）。
- **O2 witness 精確度**：跑過 78 個錄音請求、236 則實際 session 訊息、開發集。每次命中都列在 log 中並逐一人工判讀。
  - `causal`／`prediction` 誤中＝0（它們會產生缺口句）。
  - 其他值誤中 ≤ 1。
- **O3 no-op**：重播全部錄音決策（3,592 列）。沒有 witness 命中的決策，回覆變化＝0。
- **O4（階段 1）**：所有重播的 `TaskDecision` 與 baseline 完全相同，只有回覆文字變。
- **O5 開發集**：
  - A1、A2、A3 有目的段落；A4 有因果缺口，且不再出現「These all fit」；B3 有預測缺口而非 fallback 訊息；A0 回覆不變。
  - 階段 2 加：A5 追問結論類型；B1 推薦 COBRA（若查證成立）。

### 4.3 Live gate

- 模型：gpt-4o-mini，已預先授權。
- 方式：baseline 用宣告 commit 的 worktree，與候選版交錯同時跑。保留集 ×3，每臂約 72 個 session。

- **有效性**：兩臂 provider 錯誤皆為 0，否則依 Log 290 補充 4 重跑。
- **效果**（結構計數；baseline 預期為 0，因為這些段落現在不存在）：
  - **E1**：有 witness 的保留集句子中，≥ 80% 的句子在 ≥ 2/3 次回覆出現對應的目的段落。
  - **E2**：causal／prediction 句子每句 ≥ 2/3 次出現缺口句。
  - **E3（階段 2）**：設計已知、結論未知的平手句，≥ 2/3 次追問結論類型。
- **傷害**：
  - **H1 假缺口**：標註為沒有 causal／prediction 的句子（含否定陷阱與對照），回覆出現缺口句＝0。這是 CC1 的教訓。
  - **H2 對照不變**：每個對照句，候選與追問軸的眾數形狀與 baseline 相同。
  - **H3 呼叫數**：階段 1 每次 trial 與 baseline 相同；階段 2 ≤ baseline。
  - **H4 blind_en ×1**：OK ≥ baseline − 1；WRONG ≤ baseline ＋ 1（`replay_pw.verdict`）。
- **撤回**：O 不過就先修，或不上線；任何 H 不過就撤回該階段；E 不過依宣告撤回，不重新解讀。
- **雜訊**：以上都是每句的結構計數，不是分數差。同碼重跑波動是 3–4（Log 98），因此不對任何 ≤ 3 的分數差下結論。

---

## 5. 步驟與成本

1. **宣告（Log 342）**：本設計的定案版、保留集與其 sha256、標註、gate、宣告時 HEAD 的指紋。
2. **registry 文字**：每句附來源連結，或標為「未查證→不上線」。
3. **witness 與單元測試**（否定、誤中、重疊），做 O2 稽核。
4. **階段 1 實作**，跑 O1–O5，再跑 live（E1、E2、H1–H4）。
5. **階段 2 另行宣告（Log 34x）**，實作後跑 O 系列，再跑 live（E3、H1–H4）。

成本：
- 離線部分不花錢。
- live 每個階段約 144 個 CLI session（約 US$0.3）加 blind_en 兩臂（約 US$0.2），合計約 US$0.5。

---

## 6. 和論文的關係

- **決策表示**：研究目的（設計＋結論類型，都有原文引文）→ registry 宣告的證據與步驟 → 方法前提（既有 `SELECTION_AXES`）→ 工具（既有 matcher）。每個主張都追溯到一句請求原文和一句人寫的 registry 句子，可以審計。
- **適用性檢查是確定性的**，不額外呼叫模型。這本身就是對 CC1 失敗模式的回應，可以寫進論文。
- **評估**：最小對照組 benchmark，指標包括目的敏感度、適當追問、誠實缺口、假缺口、成本。baseline 是 Log 341。這也補上現有 corpus 測不到的部分（第 1.4 節）。
- **計畫書**（10/15 截止）可以寫成方法與評估設計，結果放到後面。

---

## 7. 已知風險

- **召回率有限**：同義說法會漏掉，漏掉時回到現狀（fail-safe）。保留集會如實報告召回率，不為了提高召回而放寬誤中標準。
- **registry 文字錯誤**：錯的科學建議比沉默更糟，所以未查證的格子不上線。COBRA 的 `direct` 是最需要查證的一格。
- **與既有推薦路徑的順序**：PW、condition recommender、discriminator 的優先序要在階段 2 宣告中寫清楚。建議請求明說的結論類型優先於沒有 witness 的偏好。
- **多讀法請求**：v1 不處理，`hypothesis_routes` 的回覆不加段落。
- **字詞表的維護成本**：與現有 `SELECTION_AXES`、`READING_WITNESSES` 同一類，集中放在 registry。

---

## 8. 需要你決定的事

1. **詞彙 v1**：claim 5 個（group_difference、individual_change、regulator_change、causal、prediction）、design 2 個（paired、groups）。要增減嗎？例如是否加入連續變數（年齡、分期）的 `association`。
2. **保留集誰寫**：(a) 你寫，最乾淨；(b) 由看不到 witness 字詞表的 subagent 依規格寫，你審；(c) 混合，各寫 3 個家族。
3. **B3 fallback 回覆**：放在階段 1，或獨立一項？
4. **A2 樣本數修正**：跟階段 1 一起做，或獨立修？
5. **階段 2 的 (a) 推薦與 (b) 追問**：都做，或只做其中一個？

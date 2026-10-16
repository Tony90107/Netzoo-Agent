# 核心判斷四態（Core Decision）設計 spec

日期：2026-10-15　狀態：草案，待使用者確認　範圍：架構與驗收，不列逐題補丁

## 0. 為什麼要這份 spec

過去一個月的修正都是「補洞式」：每一組新的盲測題找到一類新的失敗，修好之後，下一組題又冒出另一類（分數 94.7 → 90.9 → 83.8 → 77.1）。這份 spec 把方向固定下來：

- 本 spec 內的設計，執行期間不換。某階段沒過門檻，只能在該階段的設計內修。
- 若真的需要換設計，先在第 11 節「變更紀錄」寫明理由，經使用者同意後才動手。

使用者 2026-10-15 提出的三個要求：

1. 新增「目標不明」狀態。
2. 能追問的事實不要寫死，可以交給一個 agent，再加程式規則把關。
3. 判斷盡量收斂到同一條路徑，不要分散混亂。

## 1. 目標與非目標

**目標**

- 每一輪由**同一個函式** `decide_core` 產生一個四態判斷 `CoreDecision`，寫進 `TaskDecision.core` 和 trace。回覆、執行、卡片都只能依據它，不能自己另做判斷。
- 新增 `CLARIFY`（目標不明）：讀不出使用者要什麼結果時，先釐清目標，不選 workflow。
- 追問的事實由「合約接地」的 fact agent 提出，程式規則把關，取代寫死的 11 種 `DIMENSIONS`。
- 驗收改成**程式計分**：直接比對 trace 裡的四態判斷和 gold，不再需要盲標子代理。

**非目標**

- 不修逐題失敗，不加字詞清單或正則來判斷意圖，也不靠改 prompt 措辭修正。
- 不改 workflow 能力，不改 YAML 已宣告的限制。
- 不動 run 的三道閘：`RunVerdict` 在路由、Plan Evaluator、executor 的檢查都保留，只改成讀 `CoreDecision`。
- 中文不進驗收門檻（2026-10-14 使用者決定）。

## 2. 現況（為什麼會分散）

- **分類階段**：`graph/router_invocation.invoke_router` 依序呼叫約 15 個步驟。其中語意讀取、discriminator、intent router、hypothesis matcher、condition recommender、concern matcher、能力檢查、第二意見、run check、checked_match 等，多數都會直接改寫 `action`、`should_execute` 或 `capability_match_status`。也就是說，判斷是一路被改寫出來的，沒有一個明確的終點。
- **回覆階段**：`graph/response._respond` 有約 23 個依序檢查的分支。每個 renderer 自己決定要不要接手、要說什麼。其中 `render_cobra_expression_boundary` 和 `render_unsupported_algorithm_boundary` 在任何讀取之前，就先用正則判斷然後直接回覆。
- **追問**：只走 `interpretation/needed_facts.py`。事實限定在 11 種 `DIMENSIONS`，而且只有使用者說「不知道」時才會問。m3 的 30 題追問只問對 4 題。今天的 15 題追問題裡，約一半的決定性事實不在這 11 種之內，例如 log 轉換、檔案是哪一版、特徵數上限、RBP 還是 TF。
- **目標不明**：沒有這個狀態。只有當語意讀取給出 `artifact_type == "unknown"` 時，才會走 `render_research_choices` 選單，而模型很少給 unknown。今天的 C01（「想更了解子宮內膜癌樣本的基因調控」）就被讀成調控網路，回覆寫「available from PANDA」。

## 3. 四態定義與界線

| kind | 意思 | 回覆要做到 | 不能做 |
|---|---|---|---|
| `CLARIFY` | 讀不出使用者要什麼結果 | 一句理解；依使用者已說的資料，列出可能得到的結果類型；**一個**關於目標的問題（資料不明時，再加問有什麼資料） | 選 workflow、說「X 可做／適合」、規劃 run |
| `ASK` | 目標明確，但一個未知前提會改變判定 | 問該事實（最多 2 個問題），附上使用者原話與使它重要的合約原文（2026-10-16 起不再列兩種答案各導向什麼，見變更紀錄） | 規劃 run；把判定說成已確定；未經驗證就說某個答案導向哪個 workflow |
| `DECLINE` | 照所問的做不到 | 說做不到與理由（引合約）；之後可提替代結果 | 把被拒的需求說成可做 |
| `DO` | 可以做 | 給 workflow（平手時可列選項）；run 請求進入既有的輸入與 run 閘 | — |

輔助狀態：

- `DO` 的子型 `partial`：多個需求中有的可做、有的不行。逐項列出，**絕不自動只跑可做的部分**（2026-10-14 使用者決定）。
- `UNCHECKED`：讀取或檢查失敗（例如服務錯誤、額度用完）。如實說無法判斷，永遠不當成 `DO`。

**優先序**：`UNCHECKED` → `CLARIFY` → `ASK` → `DECLINE` / `DO`。有需求被拒、同時有另一個需求待追問時，判為 `ASK`，回覆裡附上被拒的部分。

**兩條界線**（寫進程式規則與單元測試）：

1. **追問只問會改變判定結果的未知前提**。不能因為 YAML 有某個欄位，就把所有未知條件都問一遍。使用者沒有表示不確定的未陳述條件，交給 run 的輸入檢查或宣告欄位處理，不追問（延續 2026-10-14 決定）。
2. **釐清目標先於 workflow 選擇**。讀不出使用者要什麼結果時，不能先選一個 workflow，再給「可做」的判斷。

## 4. 架構

```
使用者訊息
  → 讀取與檢查（現有呼叫；全部只產生「證據」，不再改寫判定）
      語意讀取 · 能力檢查 / 第二意見 · goal 讀取（新） · fact agent（新） · 輸入檢查 · run check …
  → decide_core(evidence) → CoreDecision      ← 唯一做判斷的地方，純程式，可單元測試、可離線重放
      寫入 TaskDecision.core 與 trace 事件 core.decision
  → 執行閘：plan / Plan Evaluator / executor 只在 kind=DO、有 run 請求、RunVerdict 同意時放行
  → 回覆：_respond 第一步依 kind 分派到對應的 view，view 只拿 CoreDecision（加上 registry 說明文字）
```

### 4.1 `CoreDecision`（草案）

```python
class FactQuestion(BaseModel):
    question: str            # 要問使用者的話
    user_quote: str          # 請求中表示「不確定」的原文（逐字）
    workflow: str            # 這個前提屬於哪個候選 workflow
    contract_quote: str      # 該 workflow YAML 中使前提重要的條文（逐字）
    if_yes: str              # supported | not_supported | other_workflow:<NAME>
    if_no: str
    settled_by_input_check: bool = False   # 輸入檢查會查到 → 說明、不追問

class CoreDecision(BaseModel):
    kind: Literal["CLARIFY", "ASK", "DECLINE", "DO", "UNCHECKED"]
    partial: bool = False
    workflows: list[str] = []              # DO：可做的 workflow（平手時多個）
    declined: list[DeclinedPart] = []      # 被拒的需求、理由與合約引文
    facts: list[FactQuestion] = []         # ASK
    clarify: ClarifyNeed | None = None     # CLARIFY：缺什麼（result / data / both）與可能的結果類型
    run_allowed: bool = False              # 只有 DO 才可能為 True
    evidence: dict = {}                    # 各證據來源的摘要，用於 trace 與除錯
```

### 4.2 `decide_core` 規則

純函式，輸入是證據，輸出是 `CoreDecision`，沒有任何模型呼叫：

1. 讀取或檢查失敗，且無可用證據 → `UNCHECKED`。
2. goal 讀取結果不是 `result_named`，或沒有經逐字驗證的結果引文 → `CLARIFY`（第 5 節）。
3. 有通過第 6 節規則的 `FactQuestion` → `ASK`。
4. 每個結果需求依能力檢查與方法條件的狀態分類：`not_available` 為拒；`available` / `with_step` 為可做；`needs_fact` 已在第 3 步處理。全部被拒 → `DECLINE`；部分被拒 → `DO`（partial）；其餘 → `DO`。
5. `run_allowed` 等於 `kind == DO`、不是 partial、有 run 請求、且 `RunVerdict` 為核准的那幾種。

第 5 階段（第 13 節）修改第 1–3 步：已確認的目標不明，即使 routing 失敗也判 CLARIFY；結果沒定、也沒列出選項時判 CLARIFY；程式算出分支的數量事實判 ASK，排在 fact agent 的提問前面。

### 4.3 回覆分派

`_respond` 第一步依 `kind` 分派。現有分支歸到下列 kind，成為該 kind 的呈現細節，不再自己判斷要不要接手。第 3 階段會先盤點確認這份對照：

| kind | 現有分支（`graph/response.py`） |
|---|---|
| CLARIFY | `research_choices`（改由 CLARIFY view 呼叫） |
| ASK | needed-fact 回覆、`hypothesis_routes` 中的結果選擇 |
| DECLINE | `capability_gap`、`algorithm_boundary`、`cobra_boundary`、`handoff_boundary` |
| DO | `needs_input`、`input_confirmation`、`preference_confirmation`、`plan_rejected`（run 被閘擋下）、`verified_guidance`、`scientific_guidance`、`workflow_contract`、`handoff_script`、`outcome_clarification`（平手選項）、`composition`、`execution`、最後的模型自由回覆 |
| UNCHECKED | `unresolved` |
| （非判斷：工具） | `download_string`、`web_search`、`retrieval_failure`、`authority_report` |

規則：

- 兩個正則 boundary renderer 不再直接回覆，改成提供給 `decide_core` 的證據（拒絕理由或交接說明）。
- view 的函式簽章只接受 `CoreDecision`，拿不到其他判定欄位，所以結構上無法和判斷不一致。
- 最後的模型自由回覆只用於 `DO` 的說明，並收到 `CoreDecision` 作為不可違反的前提。

## 5. 目標不明（CLARIFY）

- **讀取**：在現有語意讀取的輸出加一個欄位 `goal: {status: result_named | purpose_only | none, quote}`。由模型判斷使用者是否「說出想要的結果」（一個網路、每個樣本的網路、群落、分型、TF 活性……），還是只說了目的或主題（「想了解基因調控」「做個網路分析」「看看有什麼發現」）。不用字詞清單。
- **程式規則**：
  - `quote` 必須逐字出現在請求中。
  - `result_named` 的 `quote` 必須與至少一個能力檢查的結果列重疊；否則視為 `purpose_only`。
  - 點名了 workflow 但沒有目標（「該用 BONOBO 還是 LIONESS？」）同樣是 `CLARIFY`：可以比較被點名的選項，但結尾必須問目標。
- **與「結果二選一」的界線**：使用者列出兩個以上的結果、只是不確定要哪個，屬於 `ASK`（沿用既有 `open_choices`）。連結果都沒說，才是 `CLARIFY`。
- **回覆**：結果類型清單由 registry 的 `output_capability` 產生，只說「可以得到什麼」，不說哪個適合。
- **下一輪**：使用者回答後，用「原請求 + 回答」重新走一次 `decide_core`（沿用 follow-up conditions 機制）。

## 6. 追問事實（ASK）：合約接地的 fact agent + 程式規則

- **呼叫時機**：目標已明（非 `CLARIFY`）且至少有一個候選 workflow 時，每輪最多一次。
- **輸入**：使用者請求，加上各候選 workflow 的合約條文（YAML 的 `description`、`conventions`、`controls`、`handoff_contract`）。合約本身就是事實的封閉範圍，不需要另外寫一份事實清單。
- **輸出**：0 到 3 個 `FactProposal`，欄位同 `FactQuestion`。模型可以自由提出任何事實，前提是有合約條文支撐。
- **程式規則**（不通過就丟棄並記錄 `core.fact_rejected` 與原因）：
  - R1：`user_quote` 逐字出現在請求中，而且是使用者表示不確定的話：說不知道、給了兩個互相矛盾的版本，或同一句話有兩種讀法。只是「沒提到」不算（界線 1）。
  - R2：`contract_quote` 逐字出現在該 workflow 的 YAML 中。
  - R3：`if_yes != if_no`，而且都屬於合法值。換句話說，兩種答案必須導向不同的判定。（R3 仍用來篩選提案；這兩個結果只記在 trace，不出現在回覆中，見變更紀錄 2026-10-16。）
  - R4：請求的已讀欄位（能力檢查的 typed attrs、設定、計數）已經陳述這個事實時，不追問。
  - R5：條文屬於該 workflow 在 YAML 新增的 `input_checks:` 清單（輸入檢查會驗的項目），而且請求是對具名檔案的 run 時，設 `settled_by_input_check`：回覆說明檢查會先確認這一點，不追問。現有程式內的 `FILE_CHECKED` 搬到 YAML。
  - R6：最多問 2 個，依請求中的出現順序。
- **取代**：`DIMENSIONS` 與 `UnknownAbout` 在第 2 階段改為 shadow 對照，通過門檻後移除。`decisive_outcomes` 的反事實比對引擎，可作為 R3 在有結構化欄位時的程式驗證。
- **模型**：第 2 階段第 1 步離線比較（只對請求文字呼叫 fact agent，不跑完整 session），在能力檢查用的模型與 gpt-4o-mini 之間選一個。輸出 schema 保持精簡，避開 nemotron 的截斷問題。

## 7. 收斂（單一路徑）

- `decide_core` 是唯一設定 `kind` 的地方。第 3 階段要盤點分類階段每個會改寫 `action`、`should_execute`、`capability_match_status` 的步驟，逐一改成「只寫證據欄位」。盤點表放進 research log。
- 執行閘只讀 `CoreDecision.run_allowed`，加上既有的 `RunVerdict`、計畫摘要比對。
- 回覆依第 4.3 節分派。完成後，每個 kind 只有一個入口 view。
- 結構指標：「某個 kind 卻由其他 kind 的 view 回覆」的次數必須為 0（從 trace 記錄的 kind 與實際使用的 view 程式計算）。

## 8. 驗收

**題庫**

- 固定題庫：`docs/research-log/core-judgment-2026-10-15/items.json` 去掉 C01、C02、C03、C05，剩 **56 題**：do 14、dont 13、ask 15、vague 14。
  - 這 56 題沒被任何修改用過，之後也不得用來調整 prompt 或規則。
  - 每題的 gold 包含四態類別、目標 workflow，以及 ask 題的決定性事實。
- 開發集：C01、C02、C03、C05，加上已看過的 m3、accept24、heldout15，只用於離線除錯。

**計分方式（程式計分，讀 trace 的 `core.decision`）**

| 項目 | 怎麼算 |
|---|---|
| 四態正確 | `kind` 對應 gold 類別（do → DO、dont → DECLINE、ask → ASK、vague → CLARIFY） |
| 目標 workflow | DO 的 `workflows` 必須是 gold workflows 的子集 |
| 待追問事實 | ASK 的 `facts` 與 gold 的決定性事實相符：程式先比對 workflow 與合約引文，再由我逐題確認 15 題 |
| 忠實呈現 | 每階段抽查：所有非 DO 的 session，加上 10 個 DO session，確認回覆文字與 `CoreDecision` 一致；目標 0 個矛盾。由我抽查，不用子代理 |

**最終門檻（第 3 階段後）**

- do：≥ 12/14 正確，誤拒 ≤ 1
- dont：誤承諾 ≤ 1/13，正確 ≥ 11/13
- ask：問對事實 ≥ 9/15
- vague：`CLARIFY` ≥ 10/14
- 四類加權成本分數 ≥ 80（沿用 `analyze.py` 的成本矩陣）

**每階段門檻**：該階段針對的類別要進步；其他類別最多退步 1 題。

**成本**：每次題庫實測 56 個 session、每題 1 次，約 56–170 次 nemotron 和約 US$0.10 的 gpt-4o-mini，跑之前先報備。每個階段最多跑 2 次（含一次修正後重跑）。只改程式的階段，優先用錄製的讀取離線重放。

## 9. 階段

| 階段 | 內容 | 行為改變 | 驗證 |
|---|---|---|---|
| 0 基線 | 新增 `CoreDecision`、`decide_core`（從現有訊號推出，shadow 模式），寫進 trace；記錄每輪實際用的 view | 無 | 單元測試；題庫跑 1 次，得到程式計分的基線分數 |
| 1 目標不明 | goal 欄位、第 5 節規則、CLARIFY view；`decide_core` 對 CLARIFY 生效 | vague 題改為先釐清 | 單元測試；題庫 1 次；vague ↑、do 的多餘釐清 ≤ 1 |
| 2 追問 | fact agent、R1–R6、YAML `input_checks:`；先離線比較模型，再讓 ASK 生效 | 追問來源改變 | 離線 fact agent 對 ask 和 do 的請求文字；題庫 1 次；ask ↑、do 的多餘追問 ≤ 1 |
| 3 收斂 | 盤點並改寫分類階段的判定改寫點；回覆依 kind 分派；boundary renderer 改成證據；執行閘讀 core；移除被取代的路徑 | 回覆路徑收斂 | 先離線重放錄製讀取，再跑題庫 1 次；最終門檻與 0 矛盾 |
| 4 合約限制（2026-10-16 加入，第 12 節） | 4a：`workflow_conditions` 的關係限制、YAML `input_checks` 的 `scope` 標記與完整性測試；4b：能力檢查讀取的 `ruled_out_inputs`，與路線上的必要輸入 | dont 的誤承諾減少 | 4a 用錄製資料離線重算；4b 跑題庫 1 次；第 12.4 節的門檻 |
| 5 目標與事實的邊界（2026-10-16 加入，第 13 節） | 5a：routing 失敗時，已確認的目標不明判 CLARIFY；5b：能力檢查讀取的 `count_alternatives`，由程式算出各候選值的判定；5c：`FactProposal` 的 `about`／`alternatives` 與 R7 | 太模糊類多釐清、ask 類問到數量事實 | 5a 離線重放；5b 單元測試與離線讀取；5c 離線 fact agent；三項通過後題庫跑 1 次；第 13.5 節的門檻 |

- 每個階段在獨立 worktree 分支上完成，全部測試通過才提交（主樹有其他 session 在改）。
- 推送前經使用者同意，push 到 `netzoo-agent` 遠端，fast-forward only。

## 10. 保留的既有決定

- 不自動只跑部分（partial）；中文不進門檻；不靠 prompt 措辭修正。
- 只追問使用者表示不確定的事實（2026-10-14）。
- `RunVerdict` 三道閘、approval 計畫摘要；精簡測試（先離線，實測要報備、有上限）。
- 單一標註改為程式計分加我的抽查。

## 11. 風險、未決與變更紀錄

**風險**

- goal 欄位由模型判斷，可能把有目標的請求判成不明。以 do 類的多餘釐清數監控，每階段門檻 ≤ 1。
- fact agent 每輪多一次呼叫；nemotron 有輸出截斷的前例。對策是 schema 精簡，並在第 2 階段第 1 步量測截斷率。
- 多需求請求的 kind 組合規則，在第 0 階段用 m3 的 MX 錄製資料離線驗證。

**未決**（不影響開工）

- fact agent 用哪個模型：第 2 階段離線比較後決定。
- 第 3 階段盤點後，哪些分類步驟可以整個刪除。

**變更紀錄**

- 2026-10-15 草案。
- 2026-10-15（第 1 階段實作位置，不是設計變更）：goal 欄位放在能力檢查讀取（`RequestConditions.goal`、`goal_quote`；與能力檢查同一次呼叫，不另外加呼叫），而不是路由的語意讀取。理由：第 0 階段的 9 題模糊請求被判「做不到」，就是因為能力檢查把沒說結果的句子讀成需求；由同一個讀取者判斷「有沒有說出結果」最一致。另外，語意讀取有多段重試／修補的 schema，欄位會在中途遺失。程式規則照第 5 節：引文須逐字驗證；`result_named` 的引文若沒有和任何 result／about_methods 需求重疊，就視為不明；讀取未確認（備援模型）時不判 CLARIFY。
- 2026-10-16（第 2 階段實作，R1 的驗證方式，不是設計變更）：R1 要求使用者「表示不確定」，但程式不能用字詞清單判斷。開發集 m3（54 題英文）離線結果：只靠 fact agent 自己標註時，「該做」的題目被多問 20/27（gpt-4o-mini）與 10/27（nemotron）。改為兩個讀取者都同意：能力檢查的 `unknown_facts` 加上 `other` 類別，記錄任何不確定之處的引文（`uncertain_quotes`；`other` 不進舊的 11 種 dimension），fact agent 的引文必須與其中一段重疊。結果多問降到 1/27 與 0/27，該追問題處理對 17/24 與 15/24。依此選 gpt-4o-mini 當 fact agent（`NETZOO_FACT_MODEL=router`，預設）。R5 的 `input_checks` 每條都必須逐字出現在該 workflow 的合約內，由 policy loader 驗證。
- 2026-10-16（第 3 階段實作方式，偏離第 7 節字面；**使用者 2026-10-16 已接受**）：沒有把分類階段約 25 個判定改寫點逐一改成「只寫證據欄位」，改為在兩個出口強制：回覆由 `core_views.core_view` 依 kind 分派（非 DO 的 kind 只有一個入口），執行閘 `run_approval_failures` 要求 `core.run_allowed`。上游改寫因此只能成為 `decide_core` 的輸入；`core.view` 事件的 `mismatch` 量測「回覆 renderer 不屬於該判定」（p2 錄製為 4，以第 3 階段程式重放為 0）。盤點表見 research log `INVENTORY-P3.md`。
- 2026-10-16（待決事項 1，**設計變更，使用者已同意**）：fact agent 的 ASK 回覆不再列出 if yes／if no 的結果，只保留問題、使用者原話與合約原文。理由：這兩個結果是模型寫的，程式通常無法驗證方向。實測中有錯誤的例子，例如 p2b C06「If no: PUMA does it instead」、C36「If no: no registered workflow」，p2 C31 連 yes 分支都寫反。R3 仍要求兩個結果不同且合法，用來篩掉不會改變判定的提案；結果記錄在 `FactQuestion.if_yes/if_no` 與 trace。舊的 11 種 dimension 的 needs_fact 回覆不受影響：它的各分支由程式依 sheet 反事實比對算出，是經過驗證的。

- 2026-10-16（**新增第 4 階段，設計變更，使用者已同意**）：合約限制在請求層一定被檢查，見第 12 節。4a 採精簡版：在 `workflow_conditions` 加數量關係限制，數值讀自輸入檢查器的共用函式；YAML `input_checks` 加 `scope`／`limit` 標記，並加完整性測試。4b 採 B1：能力檢查讀取加 `ruled_out_inputs`，再用 `route_available` 判斷路線上的必要輸入。讀取變異另案處理。
- 2026-10-16（p4b、p4c 兩輪都錯的題目，實作補充，**不是設計變更**；research log `RESULTS-BOTH-WRONG.md`）：
  - 第 5 節的程式規則：goal 引文點名幾個 workflow，由 registry 名稱計算（`method_names.workflows_in`，只認 registry 的拼法，不用字詞清單）。恰好點名一個 workflow 時，目標就是那個方法，不判 CLARIFY；點名兩個以上、讀取為 `method_named` 且沒有讀到任何結果列時，判 CLARIFY（第 5 節「該用 BONOBO 還是 LIONESS？」）。
  - 第 6 節的候選：goal 引文點名的 workflow 排在 fact agent 候選的最前面（它就是「可能回答請求的 workflow」）。
  - 第 4.1 節 DO 的 `workflows`：run 的判定只寫它要跑的 workflow，不再把路由的其他候選一起列入。
  - 合約欄位：enum 控制項可宣告 `value_names`（同一個允許值的其他稱呼，例如 BONOBO 的 `HDF5 → .h5`，取自該控制項說明的「.h5 or .hdf (HDF5)」）。registry 與 YAML 兩邊都要宣告，loader 要求每個稱呼都對到允許值；同時對到兩個值的說法仍視為無法確定。
  - 不在此項：routing 失敗時 UNCHECKED 先於 CLARIFY 的順序（C10、C37），以及 C24、C45 的兩個設計變更，等使用者決定。
- 2026-10-16（**新增第 5 階段，設計變更，使用者已同意**）：目標與事實的邊界，見第 13 節。
  - 5a：routing 失敗時，已確認的目標不明判 CLARIFY（修改第 4.2 節第 1 步）。
  - 5b：數量的候選值由程式算出各自的判定，先只做數量。由程式算出分支的數量事實，即使 fact agent 有跑也生效，第 6 節「取代」一段因此有例外。
  - 5c：`FactProposal` 加 `about`／`alternatives` 與 R7。結果沒定、也沒列出選項時判 CLARIFY（第 5 節的 ASK／CLARIFY 界線）。
  - 實作順序 5a → 5b → 5c。

## 12. 第 4 階段：合約限制在請求層一定被檢查（2026-10-16 加入，使用者已同意）

### 12.1 問題（錄製資料 p0–p3）

| 題目 | 四輪結果 | 原因 | 第 4 階段 |
|---|---|---|---|
| C57 COBRA 48 基因、600 樣本 | 4/4 誤承諾 | 讀取正確讀到 features=48、samples=600，但請求層沒有「基因數須多於樣本數」；這條只寫在輸入檢查器（`data/cobra.py`） | 4a |
| C18 只有表現量，要直接跑 CONDOR | 3/4 誤承諾 | 「使用者沒有 motif／PPI」在這類回合沒被型別化（data-facts 讀取只在平手時才跑），PANDA→CONDOR 路線因此仍被提出 | 4b |
| C30 SAMBAR kmax 8、5 樣本；C17 只固定一個 lambda | 2/4、2/4 | 規則已存在，是讀取有時漏掉設定 | 不處理（另案） |

YAML 23 條 `input_checks` 的盤點：

- 可由請求內容判斷的數量限制（最少樣本、LIONESS-DRAGON 上限、SAMBAR kmax、DRAGON 兩層、OTTER 樣本數、設定範圍），請求層的 `workflow_conditions` 都已經處理，且都讀自輸入檢查器或 executor 的常數。唯一缺的是 COBRA 的「基因多於樣本」。
- 其餘條目只能從檔案判斷（ID 是否對齊、header、矩陣是否對稱、值的型別），第 2 階段的 R5 已讓它們「說明、不追問」。

### 12.2 4a：數量關係限制、`scope` 標記、完整性測試

- **共用的檢查函式**：在 `data/cobra.py` 新增一個函式，供輸入檢查器（`load_cobra_inputs`）與請求層共用，判斷基因數是否多於樣本數（同 `sambar.kmax_sample_error` 的做法）。數值與規則只寫在這一個地方。
- **`workflow_conditions`**：
  - `WorkflowConditions` 加一種「兩個數量的關係」限制，內容讀自上述共用函式，模組本身仍不存任何數值。
  - `data_issue` 加上這種關係的判斷。只有在請求**逐字說出**樣本數，而且**只說出一個**特徵數（也就是基因數沒有歧義）時才判斷；數量沒被說出、或有多個資料型別的特徵數時不判斷，絕不推測。
  - 違反時，照 M1 既有的流程移除該 workflow 的可做判定，理由寫明合約與請求各自的數字。之後交給 `decide_core` 判 DECLINE 或 partial。
- **YAML `scope` 標記**：
  - `input_checks` 每一條改為 `{text, scope, limit}`。`scope` 是 `request`（請求內容可以判斷）或 `file`（只有檔案能判斷）；`limit` 只在 `scope: request` 時填，指向 `workflow_conditions` 的一條限制（例如 `min_samples`、`max_values`、`omics_layers`、`relation:features>samples`、`setting:kmax<=samples`）。
  - 純字串條目讀成 `scope: file`，與現有寫法相容，不升 `policy_version`。
  - policy loader 驗證三件事：`text` 逐字出現在該 workflow 的合約內（現有規則）、`scope` 的值合法、`limit` 的名稱合法。
- **完整性測試**：每條 `scope: request` 的條目，都必須對應到 `workflow_conditions` 中該 workflow 一條確實存在、且非空的限制，否則測試失敗。日後在合約加入新的請求層限制時，測試會逼著補上對應的程式限制。
- **一致性測試**：用邊界大小的合成表格去跑 COBRA 真正的輸入檢查器（例如 5 個基因 × 6 個樣本要被拒，7 × 6 要通過），確認與請求層的判斷一致。

### 12.3 4b：使用者說沒有的輸入（`ruled_out_inputs`）

- **讀取**：能力檢查的 `RequestConditions` 加一個欄位 `ruled_out_inputs: list[{kind, quote}]`。
  - `kind` 的值：`motif_prior`、`ppi`、`mirna_list`、`covariates`、`second_omics`、`mutations`、`network`、`expression`。
  - 欄位說明要寫清楚：只收使用者說自己「沒有、拿不到」的輸入；「還沒上傳、之後再給、在同事那裡」不算。
  - 引文必須逐字驗證，驗證通過的才存成 `CapabilityCheck.ruled_out`（kind → 引文）。
- **對照必要輸入**：直接用 registry 既有的 `required_inputs`，不另外寫進 YAML。對照表：`motif_file`→`motif_prior`、`ppi_file`→`ppi`、`mirna_file`→`mirna_list`、`design_file`→`covariates`、`omics_layer_2`→`second_omics`、`mutation_file`→`mutations`、`network_file`→`network`、`expression_file`→`expression`。
- **什麼算致命**：
  - 被排除的輸入若有已登錄的工具或 workflow 能產生，就不算致命：
    - `ppi` 可由 STRING 下載產生。
    - `network` 可由 PANDA、PUMA、OTTER 透過已登錄的交接產生，但這條路線的 workflow 本身也要能用使用者現有的輸入跑。
  - 沒有登錄來源的（例如 `motif_prior`）就是致命的。
- **共用判斷**：寫一個函式 `route_available(workflow, available, ruled_out)`，給兩個地方用：
  - 能力檢查的可做判定：一個 workflow 的必要輸入被致命排除時移除，理由引用使用者原話。
  - 兩步驟路線的回覆（`hypothesis_routes`、composition）：路線中任何一步不可行，就不提出這條路線。

  C18 的情況：CONDOR 需要網路，網路得先由 PANDA 或 OTTER 產生，而這兩者都需要 motif prior，使用者說沒有，因此不提出這條路線。
- **成本**：能力檢查的輸出會多一個小欄位。上限已調到 16k，但要繼續量測解碼失敗率。

### 12.4 驗收

- **4a（離線，不呼叫模型）**：
  - 用錄製的 p0–p3 能力檢查列（列中有 `method` 的 samples/features），對每個可做判定的 workflow 重算 `data_issue`。
  - 預期：C57 在四輪都被新規則移除可做判定；所有錄製的 do、ask 題目，新規則造成的移除為 0。
  - 另外跑單元測試、一致性測試、完整性測試。
- **4b（題庫實測 1 次，56 題，約 US$0.12，跑前報備）**：
  - G1：dont 的誤承諾（含部分承諾）比 p3 的 4 題少。
  - G2：do 的誤拒不增加（p3 為 1），而且沒有任何 do 題因 `ruled_out_inputs` 被移除。
  - G3：其他類別最多比 p3 少 1 題。
  - G4：判定與回覆路徑 0 不一致。
  - G5：能力檢查解碼失敗率不高於 p3（6/56），並記錄被預算擋下的呼叫數。
- **預期**：dont 誤承諾 4 → 約 2。spec 第 8 節要求 ≤ 1，可能仍差一點，剩下的是讀取變異（C30、C17），另案處理。

### 12.5 不在第 4 階段

- **讀取變異**（C30、C17：規則已存在，讀取漏掉設定）。可能的方向是對設定也用第二讀取者確認，另案提出。
- 把既有的最少樣本等常數改成由 YAML 宣告。現在的做法（讀自輸入檢查器的常數，再加完整性測試）已能避免規則出現兩份。

## 13. 第 5 階段：目標與事實的邊界（2026-10-16 加入，使用者已同意）

### 13.1 問題（錄製資料 p1–p4c；p4b、p4c 兩輪都錯）

| 題目 | 錄製結果 | 原因 | 第 5 階段 |
|---|---|---|---|
| C10「該用 COBRA 還是 CONDOR？」 | p2、p3、p4b、p4c 都是 UNCHECKED | 沒有任何呼叫失敗。研究假設讀取讀到 `question_mode: unclear_goal` 但沒有可用的假設，程式把 `match_basis` 設成 `unverified_evidence`，`router_invocation` 再標成 `research_choices_unavailable`，`decide_core` 因此判成 routing 失敗。能力檢查也已確認目標不明，但 UNCHECKED 排在 CLARIFY 前面 | 5a |
| C45「200 還是 2,000 個蛋白質」 | p2、p4b、p4c 問成「資料格式對不對」，只有 p3 問到「是不是 200-protein 那一組」 | 能力檢查只記到 300 個 miRNA。這個事實由程式就能判斷：500 個特徵沒超過限制，2,300 個特徵是 132,192,500 個值，超過 2,000 萬的上限。但讀取沒有型別化「一個數量的兩個候選值」，fact agent 也看不到數量 | 5b |
| C24「審稿人要網路分析，我不知道要哪種」 | p4b、p4c 都是 ASK | fact agent 把「使用者不知道要什麼結果」當成可追問的事實。其他被採用的結果類提問（C11、C31、C34、C36，金標都是 ASK）都在請求中逐字列出兩個選項，C24 沒有列。單靠 `uncertainty` 分不出來（p3 的 C34 也標成 `said_unknown`） | 5c |

p1–p4c 共 6 個「routing 失敗」回合：5 個是上述「讀到 unclear_goal、沒有呼叫失敗」（C10 ×4、C37 ×1，都是太模糊類），1 個是真的語意讀取失敗（C47）。

### 13.2 5a：routing 失敗時，已確認的目標不明先判 CLARIFY

- **規則**：`decide_core` 第一條（routing 失敗、沒有任何路由結果 → UNCHECKED）的例外，從一種擴大成兩種：
  - 能力檢查已確認完全缺口（現有）；
  - `goal_unclear(check)` 為真 → 判 CLARIFY，basis `goal_unclear`，回覆走 CLARIFY 的同一個 view。
- `goal_unclear` 本身已要求能力檢查是確認過的讀取（非備援），而且引文經過逐字驗證，所以未確認的讀取仍判 UNCHECKED（p3 C37）。
- **不做**：在源頭把「讀到 unclear_goal」改成另一個 reason code。這比較精確，但會改到路由輸出與 m3 的回覆，範圍大得多。
- **已知限制**：routing 沒讀到輸入時，`ClarifyNeed` 的 `inputs` 是空的，回覆會列出所有結果，並再問一次資料（C37 的使用者其實已經說了有哪些資料）。
- **評分上的性質**：在非太模糊類，CLARIFY 與 UNCHECKED 的成本相同（do、dont、ask 都是 1），所以這條規則在題庫上不會讓任何一類的成本增加。

### 13.3 5b：數量給了兩個以上的候選值時，由程式算出各自的判定

只處理數量（樣本數、特徵數），不處理設定值（見 13.6）。

- **讀取**：能力檢查的 `RequestConditions` 加一個欄位 `count_alternatives: list[{of, quote, values}]`。
  - `of` 是 `samples` 或 `features`。
  - `quote` 是請求中給出候選值的原文，`values` 是各個候選數字。
  - 欄位說明要寫清楚：只收使用者給了兩個以上候選值、自己無法確定是哪一個的數量（「200-protein targeted panel or the 2,000-protein discovery panel」「either 100 or 1000 features」）；範圍（「100–200 個樣本」）與已確定的數量不算。
- **程式驗證**（不通過就丟棄）：
  - `quote` 逐字出現在請求中；
  - `values` 的每個數字都在 `quote` 裡（`stated_numbers`）；
  - 至少兩個不同的值。

  通過的存成 `CapabilityCheck.count_alternatives`。
- **已記錄的數量**：列的 `method` 中，引文落在 `quote` 之內的樣本數或特徵數，其實沒有被確定，先移除。
- **反事實判斷**（共用 `method_fitting`，數值規則只在 `workflow_conditions` 一處）：
  - 對每個有可做判定的結果列（`available`、`with_step`、`partial`），依每個候選值重算：
    - `samples`：樣本數換成候選值；
    - `features`：候選值是另一個資料型別的特徵數，總特徵數 = 其他已記錄的特徵數 + 候選值，`feature_counts` 加 1。只有這一個特徵數時，第 4a 節的關係限制也會判斷（U06：COBRA，40 個樣本，「20 or 200 genes」）。
  - 各候選值留下的 workflow 不同 → 這列改為 `needs_fact`：
    - `depends_on` 為 `sample_count` 或 `feature_count`；
    - `unknown_quote` 為 `quote`；
    - `outcomes` 為「候選值 → 留下的 sheet keys」；
    - 各分支被移除的理由取自 `data_issue`；
    - 新欄位 `by_code = True`，表示分支由程式算出。
  - 所有候選值都留下同樣的 workflow → 不追問，這列不變。
  - 所有候選值都讓 workflow 被移除 → 這列改為 `not_available`，理由列出每個候選值的限制（之後由 `decide_core` 判 DECLINE 或 partial）。
- **與 fact agent 的關係**：
  - `by_code` 的列不是舊 dimension 的 shadow：`without_legacy_waits` 不解除它，fact agent 有跑也保留。
  - 第 6 節「取代」一段因此改為：舊的 11 種 dimension 是 shadow，但由程式算出分支的數量事實仍然生效。
- **`decide_core`**：
  - CLARIFY（目標不明）之後，有 `by_code` 的事實時判 ASK，basis `count_fact`。
  - 程式事實排在 fact agent 的提問前面。fact agent 提問的 `user_quote` 與程式事實的 `quote` 重疊時，保留程式的那一題。合計最多 2 題（R6）。
  - `with_core` 對 `count_fact` 的 ASK 和 fact agent 的 ASK 一樣保留這一輪：不選 workflow、不執行。
- **回覆**：
  - 問題由程式產生：引用使用者原話，問是哪一個候選值。
  - 列出程式算出的各分支，例如「200：LIONESS-DRAGON 可以做；2,000：LIONESS-DRAGON 最多寫 20,000,000 個值，2,300 個特徵與 50 個樣本會有 132,192,500 個」。
  - 待決事項 1（2026-10-16）只拿掉模型寫的分支；程式算出的分支經過驗證，照舊顯示。
- **成本**：能力檢查的輸出多一個小欄位，要量測解碼失敗率。

### 13.4 5c：結果沒定、也沒列出選項時判 CLARIFY

- **schema**：`FactProposal` 加兩個欄位（只加欄位說明，不改 `FACT_INSTRUCTIONS` 的既有句子）：
  - `about`：`user_data`（使用者的資料）或 `wanted_result`（想要的結果）。
  - `alternatives: list[str]`：事實是關於想要的結果時，請求中點名每個候選結果的原文；請求沒點名、或事實是關於資料時為空。
- **R7**（程式判斷，只用於 `about = wanted_result`）：
  - 驗證過的選項：逐字出現在請求中、不為空、彼此不包含。
  - 至少 2 個 → 照舊經過 R1–R6，可以成為 ASK（第 5 節：列出兩個以上的結果、只是不確定要哪個，屬於 ASK）。
  - 少於 2 個 → 不追問，記成「結果沒定」（`FactCheck.open_results`，存 `user_quote`）。這種提問仍須通過 R1（兩個讀取者都同意使用者不確定）、R2（合約引文逐字）與 R4（不在已陳述的引文內）；R3、R5、R6 不適用，因為它不會被問。
- **`decide_core`**：
  - 在 goal 的 CLARIFY 之後、任何 ASK 之前：fact agent 有跑而且 `open_results` 不為空 → 判 CLARIFY，basis `result_open`。`ClarifyNeed.goal_quote` 用該提問的 `user_quote`。
  - 同一輪的資料類提問（包括 5b 的程式事實）這一輪不問（第 3 節：釐清目標先於選 workflow）。
- **`user_data`** 的提問完全不變。

### 13.5 驗收

- **5a（離線，不呼叫模型）**：
  - 用錄製的 p1–p4c 與 m3 重放 `decide_core`。
  - 預期：只有 C10 的 4 個回合（p2、p3、p4b、p4c）由 UNCHECKED 改為 CLARIFY，其他判定 0 改變，m3 0 改變。
  - 單元測試三種情況：routing 失敗加已確認的目標不明 → CLARIFY；加備援讀取的目標不明 → UNCHECKED；加讀到具名結果 → UNCHECKED。
- **5b（單元測試加離線讀取）**：
  - **單元測試**：
    - C45 型：300 + {200, 2000} 個特徵、50 個樣本，判 ASK，分支由程式算出；
    - U06 型：單一特徵數 {20, 200}、40 個樣本，COBRA；
    - 所有候選值都超過限制，判 DECLINE；
    - 候選值不影響結果時，不追問；
    - 數字不在引文內時丟棄；
    - 引文內已記錄的數量被移除。
  - **離線讀取**：用能力檢查自己的模型（nemotron，免費額度）以新 schema 讀取 m3 的 U06、U12、U14 與 P 類 27 題英文。同一天也用現行 schema 讀同一批題目作為對照，共約 60 次。
    - B1：U06、U12 至少 1 題讀出正確的候選值。
    - B2：P 類 0 題有 `count_alternatives`。
    - B3：U14（設定值「0.3 or 3.0」）不被讀成數量。
    - B4：解碼失敗不多於對照組。
- **5c（離線 fact agent）**：
  - 用 gpt-4o-mini 以新 schema 對 m3 開發集英文 U（27）與 P（27）各呼叫一次，約 US$0.04。R1 的第二讀取者沿用第 2 階段 `live/f2w` 的錄製讀取，與第 2 階段同條件。
    - C1：U 類 0 題產生 `open_results`。
    - C2：U 類追問處理對 ≥ 17/24（第 2 階段的數字）。
    - C3：P 類「追問或結果沒定」合計 ≤ 1。
  - m3 沒有「太模糊」類的題目，所以 5c 對 C24 型的召回只能在題庫實測時看到。
- **題庫實測**（5a–5c 都通過離線門檻後，56 題跑 1 次，約 US$0.11，跑前報備）：
  - G1：各類正確題數不低於 p4b、p4c 兩輪中較差那一輪減 1（do ≥ 9、dont ≥ 10、ask ≥ 7、vague ≥ 9）。
  - G2：do 與 ask 類被判 `result_open` 的 CLARIFY ≤ 1。
  - G3：請求沒有給候選數量的題目，0 題出現 `count_fact`。
  - G4：判定與回覆路徑 0 不一致。
  - G5：能力檢查解碼失敗 ≤ 3/56。
  - 另外逐題報告 C10、C24、C45 的結果。同一份程式兩輪曾相差約 ±5 分，所以總分只作參考，不單憑一輪宣稱達到第 8 節的最終門檻。

### 13.6 不在第 5 階段

- 設定值的候選（U14「lam 0.3 or 3.0」用 `setting_issue` 判斷）：同樣的機制可以延伸，5b 通過後另案提出。
- 研究假設讀取把 `unclear_goal` 標成失敗的源頭標籤。
- 讀取變異：C17，以及 goal 讀取的誤判。
- C39：fact agent 問成「有沒有 miRNA ID 清單」，而不是「是 miRNA 還是 piRNA」。
- C52 在 p4c 被條件檢查判成 BONOBO 不符「log2-transformed and centered」。

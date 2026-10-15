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
| `ASK` | 目標明確，但一個未知前提會改變判定 | 說明是哪個前提、兩種答案各導向什麼；問該事實（最多 2 個問題） | 規劃 run；把判定說成已確定 |
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
  - R3：`if_yes != if_no`，而且都屬於合法值。換句話說，兩種答案必須導向不同的判定。
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

# Research Log｜SAMBAR 整合與 NetZoo Agent 語意路由

建立日期：2026-09-04  
研究狀態：進行中  
目前程式 checkpoint：`b36226d`  
紀錄性質：依對話、實際輸出、session／trace 與測試結果回溯整理；後續可逐輪追加。

> 本紀錄保存「當時看到什麼、如何解釋、做了什麼、結果是否支持原先判斷」，不是把所有修改整理成一條必然成功的故事。未確認的原因保留為假設，未通過的驗收不因為已有改善而改寫成成功。

## 研究問題與實驗設定

### 起點

最初想驗證新加入的 SAMBAR 是否能被 Agent 正確辨識與推薦。測試進行後，研究範圍逐漸擴大到：

**當使用者已清楚說明科學目的與資料類型時，Agent 為什麼仍可能理解錯誤？如何讓錯誤被發現、修復，並在無法修復時一致地與使用者互動？**

### 三個固定探針

| ID | 問題設計 | 欲觀察的能力 |
| --- | --- | --- |
| Q1｜機制辨識 | 癌症突變分群；要求基因長度與病患突變負荷校正，再聚合為途徑分數、計算距離 | 從科學需求辨識工作流程，區分中間產物與最終目標 |
| Q2｜稀疏性 | 200 位肺癌病患，突變矩陣 99% 為零，直接分群效果不佳 | 辨識目前資料模態，解釋為什麼考慮途徑聚合 |
| Q3｜錯誤方法引導 | 先提 RNA-Seq／PANDA 成功經驗，再詢問能否把 WES 突變矩陣交給 PANDA／LIONESS，最後做病患分群 | 區分歷史背景、目前輸入、提議方法、方法適用性問題與最終科學目的 |

原始語料與預期欄位保存於 [routing_scenarios.json](../../tests/routing_scenarios.json)。

### 證據與判讀原則

- **觀察**：畫面、保存欄位、trace 事件、測試結果直接顯示的事實。
- **假設**：用來解釋觀察、尚需驗證的原因。
- **已確認機制**：有程式路徑或可重現測試支持的因果關係。
- **限制**：資料未保存、尚未實測，或無法由目前結果推論的部分。

本研究不把「答案出現 SAMBAR」「系統顯示 exact」「完整語意正確」視為同一個成功指標；也不把測試腳本提供的正確回覆，當成真實模型的理解能力。

## Log 01｜初次測試：問題看似在 SAMBAR，實際跨越多個層次

時間：初始測試階段，精確執行日期未保留於此紀錄。  
狀態：已觀察問題；初始根因尚不能只由畫面確定。

### 觀察

- Q1：顯示路由器不可用與 `ValueError`，要求使用者重新描述。
- Q2：已明確要求突變病患分群，系統卻表示結果類型不清楚。
- Q3：被 PANDA／LIONESS 名稱引導，選擇 PANDA，並轉而要求表現量資料。

### 當時的假設

1. 新套件的能力可能沒有完整暴露給路由器。
2. 語意分類過度依賴工具名稱，而不是資料與目的。
3. 技術失敗可能被錯誤呈現為「使用者沒有說清楚」。

`ValueError` 本身不能證明是 provider 停機、網路問題或特定 schema 問題；需要後續紀錄才能區分。

### 決策與介入

不只增加「SAMBAR」關鍵字，而是把工作範圍擴大到科學能力路由、輸入界線與失敗處理。後續依序進行 P0 路由修正、P1 語意與驗證強化，以及 P2 測試策略工作。

相關實作 checkpoint：

- `b91a8d6`：scientific capability routing and mutation input boundaries。
- `ef9ff2b`：semantic input contracts and evidence validation。

### 反思

「新增套件測試失敗」只是入口。真正要驗證的是使用者問題經過多個元件之後，是否仍保存同一個科學意圖。

下一輪需要同時觀察工作流程選擇與最終回答，而不是只看路由器選了誰。

## Log 02｜推薦到了 SAMBAR，但回答仍先肯定錯誤方法

時間：前期路由修正後；依保留的輸出回溯。  
狀態：工具推薦改善，回答一致性未通過。

### 觀察

三題開始能推薦 SAMBAR，但 Q3 曾在開頭認可把 WES 突變矩陣交給 LIONESS 是有效做法，後文又說目前 PANDA／LIONESS 工作流程不接受該輸入。

同一回答內出現「先肯定、再否定、最後推薦其他工具」。另外，也出現將途徑分數矩陣與分群結果混在一起描述的情況。

### 更新後的假設

路由結果與回答生成之間缺少足夠的約束。即使推薦工具正確，回答層仍可能接受使用者的錯誤前提，或改寫產物意義。

### 介入

- 補上產物類型、實體、粒度的跨欄位一致性檢查。
- 區分精確匹配與備援推薦，不共用相同成功訊號。
- 將不相容方法與拒絕原因以結構化資訊傳給回答層。
- 對已選定能力的推薦與拒絕，使用程式控制的契約與呈現方式。
- 將驗收延伸至最終回答，檢查方法立場及產物區分。

相關 checkpoint：`0454eff` — semantic and final guidance consistency。

### 結果與反思

後續輸出能分開描述基因分數、途徑分數、樣本距離與分群標籤，且曾正確呈現 PANDA／LIONESS-PANDA 對目前突變輸入的拒絕說明。

這支持了「回答層需要接收明確的限制與產物契約」，而不只是被選中的工具名稱。

但不能把拒絕寫成對整個方法家族的泛化判斷。判斷應限定於目前註冊工作流程與輸入，不能因歷史段落提過 PANDA，就說之前的 RNA-Seq 分析也是錯的。

## Log 03｜嚴格驗證後三題全是 fallback：安全性改善，不代表任務完成

時間：2026-09-03 後續測試批次。  
狀態：失敗被攔截，但語意匹配仍未成功。

### 觀察

三題都推薦 SAMBAR，但全部顯示 fallback，而不是精確匹配。回答與進度曾要求確認或澄清，Next step 卻又引導使用者提供輸入開始流程。

### 假設

嚴格驗證已開始阻止錯誤結果通過，但修復能力與互動狀態還沒有配合。系統將「無法驗證語意」混同為「使用者問題不清楚」。

### 介入

1. 分開保存使用者目標與備援候選，不用候選工具的預設產物補寫目標。
2. 統一回答、進度與 Next step 的互動規則。
3. fallback 不自動觸發澄清，也不提供未驗證的執行捷徑。
4. 三題分別解釋校正需求、稀疏性、方法與輸入界線。
5. 測試從回答擴大到「進度＋回答＋下一步」。

相關 checkpoint：`933f4ea` — semantic repair and fallback guidance。

### 結果與反思

失敗互動變得一致：不再要求使用者為系統的理解失敗負責，也不再同時宣稱未確認與可開始。

但三題仍是 fallback。這一輪的成功是**改善失敗時的行為**，不是成功理解問題。若只看安全措辭與工具名稱，會高估進度。

## Log 04｜舊錯誤消失，卻發現三題都更早卡在必要欄位

觀察時間：2026-09-04 約 16:53–16:54。  
狀態：真實語意失敗仍可重現。  
Session：Q1 `8e4da569`、Q2 `fa58aea4`、Q3 `cd43df8c`。

### 觀察

| 問題 | 初始回覆的驗證失敗 | reviewer 最後的失敗 |
| --- | --- | --- |
| Q1 | 缺少 `operation` | 仍缺少 `operation` |
| Q2 | 缺少 `operation`、`granularity` | 仍缺少 `operation` |
| Q3 | 兩個 hypothesis 都缺少 `operation` | 仍缺少 `operation` |

這一批精確匹配與完整修復都是 0/3。不能因為之前的角色／粒度錯誤不再顯示，就宣稱那些問題已經被修正：新的結果可能根本還沒有走到後面的檢查。

### 要驗證的假設

- H1：SDK 轉換過程可能遺失必要欄位。
- H2：模型看到的產物條件分支不夠完整，容易只填局部欄位。
- H3：reviewer 沒有收到足夠具體的缺欄位修復資訊。

### 查證結果

- 實際攔截受測 SDK 的 HTTP 請求後，根層級的 `required` 與 `operation` 仍存在。**受測版本的結果不支持 H1。**
- 當時的產物條件分支只包含局部限制，沒有重列所有必要欄位。這是已確認的 schema 結構；但不能僅憑此證明模型漏欄位的唯一原因，H2 仍需用實測效果評估。
- 修復訊息沒有針對缺少欄位提供完整的欄位要求，且 schema 錯誤位置的 hypothesis 索引處理有缺口。H3 獲得程式檢查支持。

### 下一步決策

修生成與修復資訊，保留嚴格驗證。不透過自動補上 `operation=analyze`、更換成工具預設產物，或放寬必要欄位來取得成功狀態。

## Log 05｜必要欄位修復與實際終端驗收

實作時間：2026-09-04。  
封存 checkpoint：`b36226d`，17:20:22（UTC+08:00）。  
狀態：離線契約與終端修正已驗證；模型成效須另看下一輪真實輸出。

### 介入 A：schema 與 reviewer

- 在每個產物條件分支重列必要欄位與型別。
- 明確說明 `operation` 與 `granularity` 的語意及不可省略要求。
- 修復回饋指出 hypothesis 索引、缺少欄位、合法值及證據更新要求。
- 要求完整替換的 review 結果，而非複製不完整提案或只回傳局部補丁。
- 保留舊的跨欄位錯誤回放，新增 `missing-required` 批次。

### 介入 B：Next step 截斷

使用者畫面在 `inpu` 附近截斷，但字串本身完整。

可重現原因：顯示提示的 `Window` 沒有啟用換行。下方可編輯輸入區域已能換行，不代表上方提示也能換行。

修正為 `wrap_lines=True`，並使用 PTY 與 ANSI 畫面模擬驗證，而不是再增加一個字串包含測試。

### 驗證紀錄

- 測試先重現必要欄位分支／修復定位的缺口，以及 40／60／90 欄的提示截斷。
- 修正後，相關驗收 51 項通過、零跳過。
- HTTP 測試使用真正的 SDK 轉換及攔截請求，但模型回覆由測試腳本提供；不涉及付費模型呼叫。
- 三題均測試「完整修復」與「reviewer 再次漏欄位」。後者仍被判定失敗，沒有因重試次數耗盡而被接受。
- PTY 測試包含縮至 32 欄與提交 `exit`，確認畫面及基本互動均正常。

### 完整測試的限制

| 版本／環境 | 通過 | 失敗 |
| --- | --- | --- |
| 修改前 `933f4ea`，相同完整依賴環境 | 825 | 16 |
| 本輪修改，排除獨立 opt-in Docker 科學測試 | 842 | 16 |

兩次是相同的 16 個失敗項目，涉及圖流程／回答預期與 BONOBO 測試。本輪比較沒有新增失敗，但也沒有達到完整測試全綠。Ruff 與 diff 格式檢查通過。

### 反思

離線測試證明「系統能正確處理指定的有效或無效回覆」，不能證明「真實模型現在會穩定產生有效回覆」。下一輪必須保留這個差別。

## Log 06｜最新實測：畫面 exact 達 2/3，但完整語意仍有缺口

觀察時間：2026-09-04 約 17:15–17:16。  
狀態：部分改善；完整語意驗收未通過。  
Session：Q1 `9fb95ec7`、Q2 `6d9e8665`、Q3 `ee60e54a`。

> 測試發生於實作完成、checkpoint 提交之前。Commit 時間是封存時間，不代表測試當時 checkout 已有該 commit。

### 畫面觀察

- Q1／Q2 顯示 `Workflow — SAMBAR`，不再是 fallback。
- Q3 仍是 fallback，但沒有再認可把目前突變矩陣交給 PANDA／LIONESS 的做法。
- 三題 Next step 都完整換行，不再截斷；單字跨行屬於折行，而非字元遺失。
- Q3 先前明確的 PANDA／LIONESS-PANDA 拒絕說明消失。

### 核對 session 後的觀察

| 欄位 | Q1 | Q2 | Q3 |
| --- | --- | --- | --- |
| 匹配狀態 | `exact` | `exact` | `fallback` |
| 匹配依據 | `semantic` | `semantic` | `registry_features` |
| `operation` | `analyze` | `analyze` | `infer` |
| `artifact_type` | `sample_distance_matrix` | `sample_cluster_assignment` | `multi_omic_network` |
| `granularity` | `aggregate` | `aggregate` | `sample_specific` |
| `input_artifacts` | `[]` | `[]` | `[]` |
| `rejected_methods` | `[]` | `[]` | `[]` |

本批未再出現必要欄位缺失。Q2 初始回覆仍有角色／證據錯誤，reviewer 修正後通過內部驗證。Q1／Q3 也完成 review，但不能都算成「原本驗證失敗後的修復成功」。

### 對結果的判讀

1. **工具匹配訊號改善。** 從上一批的 0/3 exact 提升至 2/3。
2. **輸入資訊仍被漏掉。** 三題明確描述突變資料，結構化輸入卻全為空。
3. **Q1 未完整保存最終目標。** 距離是使用者提出的中間產物之一；依既有語料標準，主要目標是病患分群標籤。
4. **Q3 仍混淆目的與手段。** 保存成單一病患多體學網路，沒有充分辨識最後的亞型分群目的與方法適用性問題。

依目前語料要求的完整欄位，三題仍是 0/3 完整符合。這與「畫面 exact 有 2/3」不矛盾：兩者衡量的對象不同。

### 已確認的警告消失路徑

`模型漏記目前輸入 → 不相容檢查拿到空輸入 → rejected_methods 回傳空陣列 → 回答沒有明確拒絕說明`

這不是只需在回答模板加一句警告。上游輸入資訊不完整，讓下游檢查失去依據。

### 更新後的研究判斷

目前驗證較擅長檢查「已填資訊是否一致」，不擅長檢查「使用者明明說了，模型卻整個漏掉」。輸入清單為空時，就不會產生對應輸入項目的證據要求。

因此，下一輪的重點應從必要欄位的格式修復，轉向**語意資訊的完整性與目的／手段的辨識**。

## 目前假設帳本

| ID | 假設／問題 | 目前證據 | 狀態 |
| --- | --- | --- | --- |
| H1 | SDK 丟失必要欄位導致模型漏填 | 受測 SDK 的 HTTP body 仍保留 root required | 受測環境不支持；不推論所有版本 |
| H2 | 局部產物分支與不明確修復回饋增加漏填風險 | 程式結構確認；修正後這批不再出現必要欄位錯誤 | 部分支持，非單一變因因果證明 |
| H3 | 顯示提示未換行造成 Next step 截斷 | PTY 修正前失敗、修正後通過；真實輸出也完整 | 已確認並修正 |
| H4 | 輸入抽取缺漏造成方法拒絕資訊消失 | 空輸入、空拒絕清單與程式路徑一致 | 機制已確認，尚未修正 |
| H5 | 只驗證已填欄位會放過重要資訊缺漏 | 三題輸入為空仍通過；證據要求由已填欄位產生 | 已確認存在缺口 |
| H6 | 模型仍將提議方法／中間產物當作主要目標 | Q1 保存距離；Q3 保存多體學網路 | 已觀察，泛化程度待測 |

## 下一輪實驗計畫

以下是待執行計畫，不是已完成修改。

### E1｜明確輸入的完整性

**問題：** 能否讓模型保留目前資料，同時不把歷史資料錯當目前輸入？

**候選介入：** 在生成與 review 中要求區分目前輸入、歷史背景、提議中間產物與未提及輸入。對原文已明確描述、結構化結果卻缺漏的資訊，產生可追溯的修復要求。

**對照：** 原始三題、歷史突變／目前表現量的反向問題、完全未提輸入的一般工具詢問。

**通過條件：** 原始三題保存 `mutation_matrix`；反向與未提供資料案例不被硬填突變輸入。不能一律禁止空輸入來製造成功。

### E2｜最終目標與提議手段

**問題：** 能否區分「算距離來分群」「只要距離矩陣」及「確實要網路」？

**候選介入：** 明確表示主要目標與提議手段，讓 reviewer 對照原始問題核對；若使用者需要多個產物，保留其關係，不用工具預設值替換。

**通過條件：** Q1／Q3 的主要目標符合既有分群標準；「只要距離、不分群」與真正網路需求仍保留其原始目標。

### E3｜方法相容性與資訊缺漏

**問題：** 輸入抽取不完整時，能否避免靜默失去相容性檢查？

**候選介入：** 依可追溯的目前輸入事實修復抽取；未完成檢查時明確表示未完成，不將空白等同相容。拒絕仍限定於目前工作流程契約，不泛化否定整個方法。

**通過條件：** Q3 同時保有適當推薦、明確的 PANDA／LIONESS-PANDA 輸入界線、正確產物與一致的 Next step；不能只檢查是否提到 SAMBAR。

### E4｜穩定性與跨工作流程

**問題：** 改善能否超出這三個固定問題，而不是只適合 SAMBAR？

**對照：** 中英文改寫、重複執行、稀疏表現量、反向歷史背景、多產物、真正不確定及不支援的科學目標，並擴及其他已登錄工作流程。

**通過條件：** 分別回報輸入／目標正確率、匹配、修復、拒絕與互動一致性；預先訂出接受門檻。三個單次成功不能視為穩定性證明。

付費模型實驗需明確選擇案例與呼叫上限。完整環境既有 16 個失敗與 Docker 科學整合驗收，亦需另行追蹤，不能因這批改善而視為已完成。

## 累積方法論筆記

- 推薦正確工具，不代表完整理解問題。
- 內部驗證通過，不代表原文的重要資訊都有被保存。
- 舊錯誤不再出現，可能是更早的錯誤阻止了後續檢查。
- reviewer 修正被指出的錯誤，不代表修復後已完整符合科學需求。
- 字串完整，不代表實際終端畫面完整。
- 回覆、進度與 Next step 必須在同一組狀態規則下驗收。
- 成功案例與失敗案例都要留下；後續發現應追加，不應把當時的失敗改寫成成功。

## 證據索引

### 程式 checkpoint

以下時間來自 Git commit，均為 UTC+08:00；是封存時間，不等於實驗開始或結束時間。

| Commit | 封存時間 | 主題 |
| --- | --- | --- |
| `b91a8d6` | 2026-09-03 14:11:37 | 科學能力路由與突變輸入界線 |
| `ef9ff2b` | 2026-09-03 14:58:17 | 語意輸入契約與證據驗證 |
| `0454eff` | 2026-09-03 16:54:48 | 語意與最終回答一致性 |
| `933f4ea` | 2026-09-04 16:57:12 | 語意修復與 fallback 互動 |
| `b36226d` | 2026-09-04 17:20:22 | 必要欄位修復與終端換行 |

### 最新實測對應紀錄

| 問題 | Session | Run |
| --- | --- | --- |
| Q1 | `9fb95ec7` | `b7135949-8e4b-4aec-b4e7-960faca64dfe` |
| Q2 | `6d9e8665` | `07cd6408-a7c5-4ab5-bfe1-8be254226bc7` |
| Q3 | `ee60e54a` | `c94e92ef-9833-4aa2-b04c-56caba3a6b89` |

Session／trace 為本機紀錄，未將完整內容嵌入本文件。早期未保存完整原始提案的案例，回放資料是依錯誤類型重建，不是原始模型輸出的逐字副本。

- [測試策略與執行指令](../routing-test-strategy.md)
- [實際 SDK／HTTP 契約測試](../../tests/test_semantic_provider_wire.py)
- [必要欄位修復測試](../../tests/test_missing_required_repair.py)
- [互動終端驗收](../../tests/test_terminal_pty.py)
- [錯誤回放](../../scripts/routing_repair_replay.py)

## 後續追加模板

```markdown
## Log NN｜本輪研究問題

日期／時區：
程式版本或工作樹狀態：
環境／模型／重要參數：
案例與資料來源：
狀態：待驗證／未通過／部分改善／通過本輪門檻

### 觀察
原始輸出、保存欄位或 trace 顯示了什麼？

### 假設與預測
目前認為的原因是什麼？若假設成立，應看到什麼變化？

### 介入與對照
這次改了什麼？哪些保持不變？是否有其他同時變動的因素？

### 結果與證據
列出案例數、指標分母、失敗、跳過、檔案／session／run。
區分測試腳本、真實模型與科學執行結果。

### 解釋與限制
結果支持或反駁什麼？還有哪些替代解釋？哪些尚未測量？

### 決策與下一步
保留、修改或放棄哪個方向？下一個最小驗證實驗是什麼？
```

## Log 07｜E1 原文輸入完整性與失敗路徑的一致性

日期／時區：2026-09-05，Asia/Taipei。  
程式版本：從 `b36226d` 工作樹開始；本輪尚未 commit。  
環境：`/private/tmp/netzoo-schema-qa.AW2MQ5/venv/bin/python`，沿用既有完整依賴環境。  
案例：固定 Q1–Q3、反向歷史、未提輸入、假設資料、否定資料、距離限定、真正網路需求。  
狀態：通過本輪有界離線契約驗收；真實模型語意成效尚未重測，研究目標未宣稱全面完成。

### 初始狀態與根因證據

- 第一個操作為 `git status --short`：既有未追蹤的 `docs/research-log/` 與
  `routing/request_signals.py`。後者未修改、未接入 production；本輪追加研究紀錄。
- Graph generation 為 `2026-09-04T09:13:09Z`。Coverage 對部分檔案回報
  `metadata_changed`／`not_tracked`，所以對相關程式直接讀 source；沒有把舊圖當成完整證據。
- `outcome_validation._required_evidence()` 只列出 outcome 已填輸入；清空輸入及
  其 evidence 就沒有任何輸入證據要求。`rejected_methods_for()` 對空輸入直接回傳空清單。
- 首個 regression 經 production routing 重現：Q1/Q2 空輸入為 exact；Q3
  為 fallback，但仍保存空輸入 outcome。三項期望安全拒絕的測試全部失敗。
- 後續檢查又發現 fallback 的 `explicit_input_artifacts()` 使用無時態區分的
  另一套模式；历史／假設突變資料仍會被存成 guidance inputs。兩項新增測試先失敗。

### 紅燈 → 修正

1. 先重現三題反覆漏輸入，再在現有 evidence validator 加上原文完整性檢查。
2. 先重現缺少具體 repair feedback、歷史輸入混用及輸出被誤當輸入，才補上
   current/historical/uncertain/negated/proposed-output 區分與原文片段回饋。
3. 先重現 Q1 距離／Q3 網路取代病患分群，以及空輸入相容性狀態未明示，
   才加入有界的 terminal-goal conflict 與 `not_assessed` 回答。
4. 對照測試抓出假設方法詢問、只有 WES raw reads、逗號後歷史範圍的誤判；
   收窄輸入證據與延續逗號時態範圍。WES 名稱本身不能證明已持有突變矩陣。
5. fallback 改用同一套 current-input witnesses，避免驗證失敗後重新帶回歷史資料。

### 最小介入與不變的權限邊界

- 新增 `interpretation/request_integrity.py`：只產生遺漏／衝突 diagnostic，
  不填 outcome、不選工具、不從工具名稱推導資料。詞彙涵蓋 mutation/expression，
  並非 SAMBAR 專屬分支；未識別的模態仍由原有語意與證據契約處理。
- 原有兩次 semantic 嘗試都驗證；reviewer 收到具體欄位修復要求與原文片段。
  修復成功才保存 reviewed outcome；再失敗就沿用安全 fallback，outcome 為空，
  continuation 關閉。沒有放寬 schema，也沒有增加模型呼叫次數。
- 對已明說的病患分群，距離／網路不能取代 terminal artifact。
  只要距離、不分群及真正網路需求的對照仍保持原目標。
- 空输入不是相容性確認；一般未提供資料的工具詢問仍可保留空输入，回答明示未評估。

### 結果與證據

- 新 E1 檔案 33 項通過；包含三題空輸入拒絕、完整 reviewer 修復、Q1/Q3
  錯誤主要產物的拒絕及修復、歷史／目前資料、未提／假設／否定、fallback 與
  回答／進度／Next step 一致性。
- Q1/Q2/Q3 scripted 修復都保存 `mutation_matrix` 與 `sample_cluster_assignment`；
  Q1 回答分開列出距離等相关產物；Q3 保存 PANDA、LIONESS-PANDA 的
  `incompatible_input` 拒絕與 `mutation_matrix`，回答有相同的有界拒絕。
- 真 SDK + MockTransport 新增六項 E1 HTTP case（三題 × 完整／再次漏輸入）；
  原有 required schema/wire 測試與 PTY 測試保留。
- 擴充 gate：**139 passed、0 failed、0 skipped**。最後追加的 Q3 結構化拒絕斷言
  單獨重跑 E1 檔案：33 passed。Ruff 與 `git diff --check` 通過。
- 完整套件，排除獨立 opt-in Docker 科學測試：本輪 **881 passed、16 failed、0 skipped**；
  同環境 `git archive b36226d` 基線 **842 passed、16 failed、0 skipped**。
  程式比較確認失敗 ID 完全一致，見 [驗證比較 JSON](e1-offline-validation.json)。
- 三個舊 fixture 按新契約調整，未刪測試：翻譯錯誤測試補正已明說的 expression input；
  distance drift 改斷言不得 exact；validator success 與 gold correctness 的區別改用
  unresolved granularity，仍要求兩種指標分開。
- **付費模型呼叫 0 次；Docker 科學執行未跑。** 本輪不是自然語言準確率實驗。

### 解釋、限制與下一步

此介入支持「只驗已填欄位會漏掉原文資訊」及「fallback 的另一套抽取會重新混用歷史」
兩條機制；不支持任何真實模型修復率提升的結論。最新 live 完整語意仍維持上輪 0/3。

文字 witnesses 是有界的英／中文模式，不是完整語言解析器。任意代詞回指、跨句時態、
複雜否定、未涵蓋模態及多個同等主要目標仍有漏判／誤判風險；不得將本輪測試泛化。
E2 的完整多產物關係亦未增加新的持久欄位，目前依 primary outcome、assumptions 與
既有 artifact guidance 表達。16 個既有失敗與 Docker gate 仍未解決。

建議可將本輪作為有界 validator／review／fallback checkpoint 提交；不應命名成
「真實 routing accuracy 已修復」。後續先擴充語境對照，再由使用者另行授權 live
探針與呼叫上限。未自行呼叫付費模型，也未建立 commit。

## Log 08｜P0 惡意／畸形 provider payload：本地 TypeError 被誤報為 provider 不可用

日期／時區：2026-09-05，Asia/Taipei。  
程式版本：從 `b36226d` 的 E1 工作樹開始；本輪尚未 commit。  
環境：`/private/tmp/netzoo-schema-qa.AW2MQ5/venv/bin/python`，沿用既有完整依賴環境。  
案例：17 種畸形原始欄位形狀 × interpretation／review，加上 production routing 與
真 SDK + `httpx.MockTransport`。  
狀態：通過本輪有界離線契約驗收；未呼叫付費模型，live 完整語意仍維持 0/3。

> 本輪不修 routing accuracy。上一輪已撤回的 alias 實驗在第二次 semantic attempt 造成
> `TypeError`，因此先建立「任何 provider 形狀都只能是可診斷 schema failure」的安全底座。

### 觀察與根因證據

先寫 red 測試，直接對 production contract 與 routing seam 送出 provider 可以合法輸出的
JSON 形狀。17 種形狀中有 6 種在 **strict validation 之前** 就拋出 `TypeError`：

| 形狀 | 位置 | 原因 |
| --- | --- | --- |
| `selection_tags` 內含 dict／list | `OutcomeHypothesis._normalize_registry_tag_evidence` | `set(...)` 對 unhashable item |
| `selection_tags` 為數字 | 同上 | `set(5)` 不可疊代 |
| `evidence[i].dimension` 為 dict／list | 同上 | `dimension in selection_tags` 對 unhashable 值 |
| `evidence` 為數字 | 同上 | 直接疊代非序列 |

這段 normalizer 位於 `contracts/outcomes.py`，**E1 工作樹並未修改它；`b36226d` 也有相同缺陷**。
因此這不是上一輪 alias 實驗獨有的問題，而是既有、live 可達的路徑。

失敗後果經 production routing 重現，而不只是單元推論：

```text
TypeError（本地 normalizer）
→ _validation_issue_types() 取不到 Pydantic errors，回傳 []
→ attempt 0 不會進入 schema_validation 重試，reviewer 完全不被呼叫
→ recover_registry_guidance() 只接受 ValidationError/ValueError，回傳 None
→ deterministic_router_fallback() 標記 match_basis=provider_unavailable
→ 使用者看到「router 不可用」，capability_match_status 為 None
```

也就是說：一個可修復的 schema 問題被降級成「provider 停機」，同時失去唯一一次 reviewer
修復機會。這與使用者在已撤回實驗中看到的 `error_type=TypeError`、`validation_issues=[]`
是同一個失敗形狀，但根因在既有程式，不需要 alias 查表就能觸發。

### 介入（最小、不改語意規則）

1. `contracts/outcomes.py`：normalizer 先做型別檢查。非 Mapping 的 outcome、非
   list/tuple 的 evidence、非 list/tuple 的 `selection_tags`、非 str 的 `dimension`
   一律 **原樣保留**，交給 strict Pydantic validation 報出精確 path 與 type。
   缺少或 null 的 evidence 仍與先前一致視為空清單，沒有放寬或收緊既有可接受形狀。
2. `interpretation/semantic_repair.py`：`semantic_payload()` 在索引前檢查 tool call
   entry 是否為 Mapping，畸形 entry 仍是既有的可回報 decode 失敗。
3. `graph/router_invocation.py`：`_validation_issue_types()` 追加 `input_type`
   （僅型別名稱，例如 `dict`），讓 trace 保存「provider 實際送了什麼形狀」。
   **不保存原始值**，測試明確斷言值內容不得出現在 issue 摘要中。

未新增 alias 轉換、未放寬 schema、未吞掉 Pydantic error、未變更 reviewer prompt 內容、
未增加模型呼叫次數。

### 結果與證據

- 新檔 `tests/test_malformed_payload_contract.py`：**93 項通過**。涵蓋 17 種形狀 ×
  兩個 contract 的定位斷言、`semantic_payload()` 原樣傳遞、malformed 首輪仍能進入
  reviewer 並修復、兩輪皆 malformed 時為 fallback 且 `match_basis` 不得為
  `provider_unavailable`、trace 形狀摘要不含原始值，以及 3 個真 SDK +
  `httpx.MockTransport` 的 `parsed=None` 案例。
- 修正前 red：34 項失敗（含 2 個真 SDK 案例）；`input-artifact-dict-item` 這類
  原本就正確的 literal error 作為對照持續通過。
- 擴充 focused gate：**232 passed、0 failed、0 skipped**（先前 139，加上本檔 93）。
- 完整套件，排除 opt-in Docker：**974 passed、16 failed、0 skipped**；
  失敗 ID 與 `b36226d`／E1 的同一組 16 項完全相同，見
  [P0 驗證比較 JSON](p0-malformed-payload-validation.json)。
- Ruff 與 `git diff --check` 通過。
- **付費模型呼叫 0 次；Docker 科學執行未跑；live Q1–Q3 未重測。**

### 解釋、限制與下一步

本輪支持一條已確認機制：**strict validation 之前的任何未檢型別操作，都會把可診斷、
可修復的 schema 失敗升級成不可修復的 router 失敗，並產生錯誤的 provider 歸因。**

不支持任何語意正確率結論。這些形狀是人為列舉，不是實際捕捉到的 provider payload；
Q1／Q2 先前的 `literal_error` 究竟是不是 `somatic_mutation` 仍未知，因為原始 arguments
沒有被保存。新增的 `input_type` 只會在下一次真實失敗時才開始累積證據，
**不能用來回溯解釋既有 trace**。

下一步仍依交接文件順序：P1 把 data mentions 變成明確語意契約，再考慮是否需要任何
canonical 名稱對映；若要對映，必須先看到真實 payload，而不是因 registry 有兩套名稱
就自動轉換。

## Log 09｜從 trace 回收證據、封閉本體詞彙、型別化 executor 參數與基線清理

日期／時區：2026-09-05，Asia/Taipei。  
程式版本：`b36226d` 工作樹（E1 + P0 之上）；本輪尚未 commit。  
環境：`/private/tmp/netzoo-schema-qa.AW2MQ5/venv/bin/python`。  
狀態：離線通過；**未呼叫付費模型，live Q1–Q3 未重測，完整語意仍為 0/3。**

### 觀察一：本機 trace 可回收部分「無法回溯」的證據

`.netzoo/traces` 與 `.netzoo/sessions` 在本機存在。查閱後可確認：

- 已撤回 alias 實驗（run `8a855968…`）第二輪 `llm.completed` 的
  `provider_request_id=null`、`output_tokens=0`，代表 `raw` 從未被指派。
  由於 `payload, raw = semantic_payload(structured)` 是同一行賦值，例外必定發生在
  `semantic_payload()` 之內，且當時已進入 `parsed is None` 的 raw-arguments 分支。
  因此「至少一個 `input_artifacts` item 不是字串」由 trace 支持，不再只是讀程式推論。
- **E1 的 validator 在真實模型上完全正確觸發**：Q1 與 Q3 第一輪即回報
  `missing_current_input:mutation_matrix` 與 `terminal_goal_conflict:sample_cluster_assignment`，
  Q2 回報 `missing_current_input` 與 `artifact_roles`。這是先前紀錄未強調的正面證據。
- 剩下的 live 阻塞點因此非常窄：**reviewer 在唯一一次修復機會中，對
  `input_artifacts.0` 回覆了不在 enum 內的字面值**（`literal_error`）。
- Session 檔只保存最終 decision，**不含原始 provider arguments**。該值仍然未知，
  沒有任何回溯方法可以取得；下一次 live 失敗才會由新的診斷欄位回答。

### 假設與介入

H7：模型收到的是**沒有定義的 artifact 名稱清單**，因此必須自行把使用者的用語映射到
canonical 字面值。修復訊息雖然已經指名 `mutation_matrix`，但整份 prompt 從未說明它是什麼。

介入（全部由 registry／ontology 導出，沒有任何 SAMBAR 分支）：

1. semantic prompt 以 `ARTIFACT_SEMANTICS` 渲染**封閉詞彙表**（名稱＋定義），
   取代原本的裸名稱列舉，並明說「只能使用其中之一，寧可用 unknown 也不要近似名稱」。
   新的 artifact type 會自動出現，測試逐項檢查每個 literal 都有定義。
2. `RequestedOutcome.input_artifacts` 的 schema description 指向同一份封閉詞彙。
   `SCHEMA_DIGESTS` 依既有的刻意變更程序更新。
3. reviewer 修復訊息追加 `input_artifact_definition` 與 `permitted_input_artifacts`，
   並明說「這已經是 canonical 值，不要改寫、翻譯或替換近似詞」。
4. `_validation_issue_types()` 在型別名稱之外，追加**只限識別字形狀**的
   `input_value`（`[A-Za-z][A-Za-z0-9_.-]{0,63}`）。含空白、非 ASCII 或過長的值一律不保存，
   測試明確涵蓋中文原句、含 email 的自由文字與過長字串。

### 觀察二：畸形形狀的覆蓋不該靠手寫列舉

新增由 contract 自動導出的矩陣：走訪 `OutcomeHypothesis`／`RequestedOutcome`／
`OutcomeEvidence` 的每個欄位 × 五種畸形形狀，要求任何組合都不得產生 `TypeError`，
且若拋出 ValidationError 必須定位到該欄位。新欄位會自動被涵蓋，不需新增手寫案例。

### 觀察三：`executor_arguments` 對非文字選填參數的型別錯誤（真實缺陷）

`executor_arguments()` 把所有未填的選填輸入轉成空字串。對 `delta`、`log_transformed`、
`centered`（`X | None`）而言，其 tool schema 直接拒絕 `""`，因此 BONOBO 的真實執行路徑
必然失敗。原本的處理方式是為 DRAGON 的 `lambda1/lambda2` 加一個 workflow 專屬分支。

改為**通用規則**：依 `TaskDecision` 已宣告的型別判斷。文字輸入維持 `""`（適配器用它表示
「未提供」），非文字選填則整個省略，讓適配器自己的預設語意生效（例如 DRAGON 估計
未提供的 penalty 參數）。workflow 專屬分支因此被刪除。

新增 `tests/test_executor_argument_types.py`：對**每一個**可執行 action 檢查
（1）沒有任何選填參數被跨型別強制轉換，（2）registry 產生的 payload 能通過該工具自己的
args schema。

### 觀察四：既有 16 個失敗多數是刻意變更後未更新的期望

逐項查證後修正 13 項，全部依「目前刻意契約」重寫，而不是調數字：

- BONOBO 6 項：由上述真實缺陷造成，程式修好後即通過。
- `build_graph` 2 項：測試未指定 `router_model_name`，落回預設模型而不在 allowlist。
- 共用 fixture 的 explicit evidence 未逐字引用原文（「explicit 必須引用原文」是後來加入的
  規則），改為 inferred 並附推導理由。
- 一個 fixture 的 `operation` evidence 值是 `explain`、outcome 卻是 `infer`；改為一致。
- 三項期望 response model 改寫已驗證推薦：現行契約是 code-owned 呈現，改為斷言
  **response model 不被呼叫**且答案含註冊推薦，這比原斷言更嚴格。
- 一項期望 provider 失敗時要求使用者重述：Log 03 已刻意移除，改為斷言不得出現
  `restate`，且答案明說這不是使用者問題不清楚。
- `include_raw` 契約：改為逐 schema 斷言（semantic 兩個為 True 以保留無效 arguments 供
  一次 review，intent 為 False），比原本只看 `calls[0]` 更精確。

**仍未處理 3 項**，因為它們需要產品判斷而非測試修補：

1. `test_graph_records_ordered_plan_tool_and_evaluation_events`
2. `test_graph_runs_plan_execute_evaluate_loop`
   兩者都因 demo autofill 現在停在 `needs_confirmation` 而沒有 `plan.approved`／
   `tool.*`／`evaluation.recorded`。若只改成斷言 `needs_confirmation`，就會失去執行路徑的
   事件順序覆蓋；正確做法是補一條「確認後執行」的路徑，需另行決定。
3. `test_explicit_sample_specific_guidance_reaches_response_llm`
   其 `AmbiguousSemanticInterpreter` 產生的 outcome 現在被 registry 判為 `exact`。
   究竟是匹配變好、還是該案例本來就該保持 ambiguous，屬於語意判斷。

### 結果與證據

- Focused gate（原 9 檔 + 本輪 3 個新檔）：**371 passed、0 failed、0 skipped**。
- 完整套件排除 opt-in Docker：**1126 passed、3 failed、0 skipped**
  （E1+P0 時為 1119 passed、10 failed；`b36226d` 為 842 passed、16 failed）。
- Ruff 與 `git diff --check` 通過。
- **付費模型呼叫 0 次；Docker 科學執行未跑；live Q1–Q3 未重測。**

### 解釋與限制

詞彙介入針對的是一條有 trace 支持的窄失敗（reviewer 產生非法 literal），但
**沒有任何離線測試能證明真實模型會因此改用正確字面值**。這個假設只能由 live 重測判定；
在那之前 live 完整語意仍應記為 0/3。

`input_value` 只會在**未來**失敗中累積證據。畸形形狀矩陣涵蓋 contract 的每個欄位，
但不涵蓋「provider 回傳合法卻錯誤的科學內容」，那屬於語意問題不是型別問題。
P1（typed data-mention inventory）尚未進行，因此跨模態、任意時態與回指的泛化風險不變；
在看到 live 結果之前不宜再改模型面向的契約，以免重演一次撤回。

## Log 10｜第一次 live 重測：安全性與回答明確改善，語意接受仍為 0/3

日期／時區：2026-09-05，Asia/Taipei。  
程式版本：`b36226d` 工作樹（E1 + P0 + Log 09 詞彙介入）。  
模型：`openai/gpt-4o-mini`，temperature 0。  
**實際付費呼叫：6 次**（三題各 2 次；intent router 從未被呼叫，低於 9 次上限）。  
完整報告：[live-q1-q3-2026-09-05.json](live-q1-q3-2026-09-05.json)。  
狀態：**未通過**。`semantic_pass_rate = 0.0`，三題皆 fallback。

### 觀察

| 指標 | 結果 |
| --- | --- |
| `pass_rate` / `route_pass_rate` / `semantic_pass_rate` | 0.0 / 0.0 / 0.0 |
| `fallback_count` / `registry_recovery_count` | 3 / 3 |
| `review_repair_validation_rate` | 0.0（3 次嘗試皆失敗） |
| `answer_failure_count` | **0** |
| `interaction_failure_count` | **0** |
| `unsafe_execution_count` | **0** |
| diagnostics | Q1/Q2：`evidence_validation` + `schema_validation`；Q3：僅 `evidence_validation` |
| `call_roles` | 三題皆 `[semantic_interpreter, semantic_reviewer]`，兩次都 `failed` |

三題 `outcome` 皆為空、`request_mode` 為 `unknown`，全部走 `semantic_validation_recovery`
回到 SAMBAR 建議。

### 與 2026-09-04 那批 live 的差異

這一批**不是**只是「同樣 0/3」。兩者失敗的方式不同：

| | 2026-09-04（`b36226d`） | 本批 |
| --- | --- | --- |
| Q1／Q2 顯示狀態 | `exact` | `fallback` |
| Q1 保存產物 | `sample_distance_matrix`（錯誤目標） | 空，未保存錯誤結果 |
| Q3 保存產物 | `multi_omic_network`（錯誤目標） | 空 |
| Q3 方法拒絕 | `rejected_methods=[]`（警告消失） | **PANDA 與 LIONESS-PANDA 皆以 `incompatible_input` + `mutation_matrix` 呈現** |
| 回答斷言 | 未於同一格式測量 | `answer_failure_count=0` |

也就是說：**先前是把錯誤結果當成精確匹配呈現，現在是明確地失敗並拒絕捏造結果**，
且 Q3 遺失的輸入相容性警告已回復。這是安全性與回答層的可測量改善，
**但完全不是語意理解的成功**；`semantic_pass_rate` 仍為 0，不得混為一談。

### 尚未回答的問題與本輪介入

報告只保存粗分類（`evidence_validation`／`schema_validation`），而 evaluator 使用記憶體
recorder，不寫 `.netzoo/traces`。因此**這次仍然沒有拿到「哪個欄位、什麼值」**。

修正：`_diagnostic_details()` 將既有的結構化 issue 代碼與 Pydantic 定位（含 Log 09 的
`input_type`／識別字形狀 `input_value`）放入每個 result row；並讓
`routing.semantic_interpretation_rejected` 在第一次嘗試就一併保存 `shapes`——
第一次嘗試正是原始值最容易遺失的地方。這些是 harness 自己的本體代碼，不是 provider
原文訊息。

Log 09 的詞彙介入**沒有**讓這批通過。它是否對 `input_artifacts` 的字面值有任何影響，
必須等下一次帶 `diagnostic_details` 的 live 重測才能判定；在此之前不應宣稱它有效或無效。

## Log 11｜根因確定：模型在 `input_artifacts[0]` 回傳物件，不是錯誤的名稱

日期／時區：2026-09-05，Asia/Taipei。  
模型：`openai/gpt-4o-mini`。**付費呼叫 6 次。**  
報告：[live-q1-q3-2026-09-05-detailed.json](live-q1-q3-2026-09-05-detailed.json)。  
狀態：**語意仍 0/3**，但長期未知的根因已由觀察確定。

### 決定性觀察

新的 `diagnostic_details` 在 Q2、Q3 的第二次嘗試同時給出：

```text
schema_validation:outcome_hypothesis.outcome.input_artifacts.0:literal_error
shapes: [{location: [...input_artifacts, 0], type: literal_error, input_type: "dict"}]
```

**`input_type` 是 `dict`。** 因此：

- 自 Log 06 起反覆出現的 `input_artifacts.0` `literal_error` **不是模型發明了 enum 名稱**，
  而是回傳了一個**物件**。
- Log 08 從 trace 推得的「至少一個 item 不是字串」由此直接證實。
- **已撤回的 alias 查表方案本來就不可能成功**：它對每個 item 做 `dict.get(item, item)`，
  遇到 unhashable dict 必然 `TypeError`——當時看到的崩潰正是這個值造成的。
- **Log 09 的封閉詞彙介入針對錯誤的假設**（模型並沒有在猜名稱）。它沒有害處，
  對其他欄位仍有價值，但不應被記為此問題的修正。

### 三題各自的實際失敗點

| 題 | 第一次嘗試 | 第二次嘗試 |
| --- | --- | --- |
| Q1 | `missing_current_input` + `terminal_goal_conflict`（兩個 hypothesis 都是） | **只差一項**：`missing_evidence:input_artifact=mutation_matrix`——reviewer 已正確填回輸入，卻沒有補上對應證據 |
| Q2 | `missing_current_input`、`artifact_roles`、四項 `ungrounded_evidence`、`missing_evidence:target_type` | `input_artifacts.0` 為 dict |
| Q3 | 兩個 hypothesis 的 `missing_current_input`、`terminal_goal_conflict`、`conflicting_evidence`、`missing_evidence` | `input_artifacts.0` 為 dict |

Q1 特別值得記錄：它已經走到只差一個證據項目。這不是理解失敗，是**修復指示不夠具體**。

### 介入（皆通用，皆先寫失敗測試）

1. `_validation_issue_types()` 對物件值追加 `input_keys`：只保留識別字形狀的鍵、上限 8 個。
   鍵是模型自選的 schema 詞彙，不是使用者內容；中文鍵、含空白鍵、過長鍵一律排除，
   測試明確涵蓋。下一次即可知道它究竟造出什麼形狀的物件。
2. `input_artifacts` 的 schema description 明說**是一組純字串**，
   「絕不可把項目包成物件；證據、角色與理由屬於 evidence 清單」。`SCHEMA_DIGESTS` 依既有
   刻意變更程序更新。
3. `repair_feedback()` 對 `missing_current_input` 追加 `required_evidence`：
   dimension／value／source 與**使用者原文的 text_span**（由發出該 issue 的同一組
   witnesses 定位，因此不是捏造），rationale 仍由 reviewer 自行撰寫。
   `noncurrent_input`（要求移除輸入）不附此欄位。原文沒有可用片段時也不附。

### 結果與限制

離線：完整套件 **1138 passed、3 failed（既有待決策項）、0 skipped**；ruff 與
`git diff --check` 通過。

三項介入分別對應三個已觀察到的失敗點，但**沒有任何離線測試能證明真實模型會照做**。
特別是第 2 項：schema description 只是描述，function calling 不保證遵守；若下一次
`input_keys` 顯示它仍回傳物件，就必須改為結構性解法（例如在 provider 層面重新表達該欄位），
而不是再加一句敘述。在下一次 live 重測之前，完整語意仍記為 0/3。

## Log 12｜物件的鍵確認為本契約自身的欄位名；描述文字無效，改為傳輸形狀正規化

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`。**付費呼叫 6 次。**  
報告：[live-q1-q3-round3.json](live-q1-q3-round3.json)。狀態：**語意仍 0/3。**

### 觀察

新的 `input_keys` 給出物件形狀：

| 題 | `input_artifacts[0]` 的鍵 |
| --- | --- |
| Q1 | `["artifact_type"]` |
| Q2 | `["artifact_type", "granularity"]` |

模型把應為字面值的項目，包成**以 `RequestedOutcome` 自身欄位名為鍵的物件**。

**Log 11 介入 2（schema description 明說「絕不可包成物件」）完全無效**——Q1、Q2 在加入該
描述後仍然回傳物件。這證實了當時就寫下的預期：function calling 不保證遵守描述文字，
描述不是結構性解法。此處必須據實記錄為一次無效介入，不得因後續改善而淡化。

Q3 這一輪沒有出現 dict，改為第二次嘗試的四項證據問題
（`missing_current_input`、`artifact_granularity`、`conflicting_evidence:input_artifact`、
`missing_evidence:entity_type`）。同一題在不同輪次以不同方式失敗，顯示 reviewer 只有一次
機會時，任何單一失誤都是致命的；也顯示三題失敗並非單一原因。

### 介入：只正規化「無歧義」的傳輸形狀

`RequestedOutcome` 新增 `mode="before"` 的欄位驗證器，套用於**封閉詞彙清單**
（`input_artifacts`、`entity_types`、`regulator_types`、`target_types`）：

- 項目是 Mapping、**恰好一個鍵**、鍵屬於一組固定的包裝鍵
  （`artifact_type`／`artifact`／`type`／`name`／`value`／`input_artifact`）、值是 `str`
  → 取出該字串。
- 其餘一律**原樣保留**，交給既有的嚴格 enum 驗證定位報錯。

理由與界線：

- 單鍵包裝所攜帶的資訊就是那個字面值，取出不丟失任何東西；取出後**仍然**面對同一個
  封閉 enum。測試明確斷言 `{"artifact_type": "somatic_mutation"}` 仍然失敗且
  `errors()[0]["input"] == "somatic_mutation"`——**沒有任何名稱被映射到另一個名稱**。
- 多一個鍵（如 Q2 的 `granularity`）就必須決定丟棄什麼，那是語意判斷，因此維持錯誤。
- 自由文字清單（`display_entities`、`selection_tags`、`unresolved_dimensions`）排除在外，
  那裡出現物件是真正的錯誤而非包裝。
- 同檔案已有先例：`OutcomeHypothesis._nest_flattened_outcome` 正是「等價傳輸形狀在嚴格
  驗證前正規化」。本次沿用同一原則，不是放寬 schema。

P0 套件中原本以 `{"type": ...}` 當作畸形案例的三處已改為多鍵物件，並加註說明單鍵包裝
現由新檔涵蓋；**沒有刪除任何測試**。

### 結果與限制

離線：完整套件 **1158 passed、3 failed（既有待決策項）、0 skipped**；新檔 20 項；
ruff 與 `git diff --check` 通過。

此介入**只**解決 Q1／Q2 觀察到的單鍵包裝。它不能解決 Q2 的多鍵物件、Q3 的證據問題，
也不改變「reviewer 只有一次機會」這個結構限制。

另需記錄一項尚未測試的變因：`.env` 的 `NETZOO_ROUTER_MODEL_ALLOWLIST` 與
`OPENROUTER_SEMANTIC_MODEL` 都只有 `openai/gpt-4o-mini`。三輪 live 的失敗型態
（包物件、證據不接地、同題不同輪不同失敗）與模型能力不足一致。在為單一弱模型繼續增加
補償機制之前，應先用較強模型測一次，以判定**這組契約本身是否可達成**。這是變因控制，
不是換模型當作修正。

## Log 13｜變因控制：gpt-4o 同樣 0/3，且暴露修復訊息自相矛盾

日期／時區：2026-09-05，Asia/Taipei。模型 **`openai/gpt-4o`**（`--model` 明確指定，
allowlist 以環境變數暫時擴充）。**付費呼叫 6 次。**  
報告：[live-q1-q3-gpt4o.json](live-q1-q3-gpt4o.json)。狀態：**0/3。**

### 觀察

| | gpt-4o-mini（Log 12） | gpt-4o |
| --- | --- | --- |
| `semantic_pass_rate` | 0.0 | 0.0 |
| diagnostics | 含 `schema_validation`（回傳物件） | **只有 `evidence_validation`，完全沒有 schema 錯誤** |
| 兩次嘗試的 issue | 不同 | **三題皆逐字相同** |

gpt-4o 三題兩次嘗試的 issue 完全一致：

```text
missing_current_input:mutation_matrix
terminal_goal_conflict:sample_cluster_assignment
inconsistent_not_applicable_outcome
conflicting_evidence:input_artifact=mutation_matrix
```

即：它把 `artifact_type` 設為 `unknown`、`granularity` 設為 `not_applicable`，
但**同時提供了 `input_artifact=mutation_matrix` 的證據**——它讀懂了資料，卻拒絕承諾
一個具型別的科學產物；而且 reviewer 那一輪**什麼都沒有改**。

### 兩項由此暴露的程式缺陷

1. **`inconsistent_not_applicable_outcome` 沒有任何修復分支。**
   `repair_feedback()` 對它只產生 `{"field_constraints": ...}`，沒有 action、沒有指示。
2. **`field_constraints` 是由「已被否決的」`artifact_type` 算出來的。**
   因為提案的 artifact 是 `unknown`，`artifact_field_constraints("unknown")` 回傳
   `{"artifact_type": {"const": "unknown"}}`。於是同一則訊息裡：

   - `terminal_goal_conflict` 指示：把 artifact_type 改為 `sample_cluster_assignment`
   - `field_constraints` 硬性約束：`artifact_type` 必須是 `unknown`

   **修復訊息自相矛盾，其中一半還是硬性 `const`。** 這與 reviewer 原封不動回傳同一份
   內容的觀察一致。這不是模型能力問題，是我方訊息缺陷。

### 介入

- `field_constraints` 改為描述**應該返回的** outcome：先掃描 issue 集合建立
  「hypothesis index → 已修正 artifact」對照，該索引的**每一則** feedback 都採用修正後的
  artifact。修正只套用到自己的 hypothesis 索引。
- artifact 無法解析（`unknown` 且沒有修正目標）時，**完全不輸出 `field_constraints`**。
  沒有可約束的目標，好過要求模型保留正在被修的值。
- 新增 `inconsistent_not_applicable_outcome` 修復分支：`replace_not_applicable_outcome`，
  明說「要求 guidance、工具建議或計畫，仍然是在談一個科學結果」，
  canonical 空 outcome 只保留給完全沒有科學結果的請求。

離線：新檔 `tests/test_repair_feedback_coherence.py` 8 項；完整套件
**1166 passed、3 failed（既有待決策項）、0 skipped**；ruff 與 `git diff --check` 通過。

### 解釋與限制

變因控制的結論很明確：**問題主體不在模型能力。** 兩個能力相差一個量級的模型都是 0/3，
而且較強的模型反而暴露出修復訊息本身的矛盾——它嚴格遵守了我們給的 `const`。

同時必須誠實記錄：**Log 12 的傳輸形狀正規化對 gpt-4o 毫無作用**（它本來就不包物件），
它只對 mini 有效；而 Log 09 的詞彙介入至今仍未被任何 live 證據支持。

本輪修正對應的是**已觀察到的具體矛盾**，不是猜測。但同樣沒有任何離線測試能證明模型
會因此產出正確 outcome。在下一次 live 重測之前，完整語意仍記為 0/3。

另有一項尚未處理的結構限制：reviewer 只有一次機會，任何單一失誤即致命。三輪 live 中
每一題都至少有一次「只差一兩項」的嘗試。是否要放寬呼叫上限，屬於成本與契約決策。

## Log 14｜Q1 首次產出 gold outcome；失敗點移到 registry 匹配的 assumptions 耦合

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`。**付費呼叫 7 次。**  
報告：[live-q1-q3-round4.json](live-q1-q3-round4.json)。狀態：**語意驗收 0/3，但性質改變。**

### 觀察：三題全部前進，Q1 出現質變

| | Q1 | Q2 | Q3 |
| --- | --- | --- | --- |
| `review_repair_validated` | **true（首次）** | false | false |
| 走完管線 | **`semantic_registry_intent`** | fallback | fallback |
| 第二次嘗試剩餘問題 | 無 | 兩鍵物件 | **只剩 `artifact_granularity`** |

Q1 保存的 outcome **完全符合 gold**：

```json
{"operation":"analyze","input_artifacts":["mutation_matrix"],
 "artifact_type":"sample_cluster_assignment","entity_types":["sample"],
 "granularity":"aggregate","unresolved_dimensions":[]}
```

三次呼叫全部成功，reviewer 修復通過驗證。這是本研究中**語意層第一次產出正確的完整結果**。

但 `status` 是 `ambiguous`、`matched_actions` 為空，因此 `answer_evaluated=false`、
`answer_failure_count=1`——**使用者這一題反而完全沒有得到指引**，比先前的 fallback 建議更差。
必須記為一次使用者可見的退步，不能因語意改善而略過。

### 已直接重現的機制

`routing/outcome_matching.py:455`：

```python
if not hypothesis.assumptions and strict.status == "exact":
```

離線直接對照（`test_one_assumption_turns_the_gold_outcome_into_an_advisory_candidate`）：

| assumptions | 結果 |
| --- | --- |
| 0 個 | `exact`、`matched_actions=['run_sambar']` |
| 1 個 | `ambiguous`、`matched_actions=[]`、`hypothesis_actions=['run_sambar']` |

**任何一條 assumption 都會讓完全正確的 outcome 失去 exact 匹配。** 這是已重現的行為，
不是推論。

而 E1 加入的 `terminal_goal_conflict` 修復指示原文寫著：

> retain their relationship in **assumptions**, not as a replacement primary goal

**我們指示模型做的事，正好使它失去 exact 匹配。** 這與 Log 13 的 `const: unknown`
屬於同一類自傷：修復訊息與下游契約互相衝突。

### 介入

- `terminal_goal_conflict` 指示不再要求把中間產物關係寫進 `assumptions`，改為明說
  中間步驟不屬於此 outcome、相關 registry 產物由最終答案自行列出，並明確要求
  **不要為此新增 assumption**（assumption 代表對請求本身的未確認詮釋）。
- 報告新增 `assumption_count`，讓「正確 outcome 卻失去 exact」在下一次 live 直接可見。
  只記數量；assumption 文字是模型針對請求寫的散文，刻意不保存。

離線：`tests/test_repair_feedback_coherence.py` 11 項；完整套件
**1169 passed、3 failed（既有待決策項）、0 skipped**；ruff 與 `git diff --check` 通過。

### 尚未決定的兩個產品問題

1. **assumptions 守衛是否過於粗糙。** 它的原意是「帶有詮釋性猜測的 hypothesis 只能是
   建議」（既有測試以「network means regulatory network」這類詮釋為例）。但它無法區分
   詮釋性猜測與單純的關係註記。本輪只移除我方造成的衝突，**沒有改動守衛本身**；
   要不要讓它更細緻，屬於安全性取捨，需另行決定。
2. **`ambiguous` 且有 `hypothesis_actions` 時完全不給指引。** Q1 因此從「fallback 建議」
   退步為「沒有答案」。這是互動契約問題，與語意正確性無關。

三輪介入的效果評估仍需下一次 live：Log 09 詞彙至今無證據支持，Log 12 傳輸正規化只對
mini 有效，Log 13／14 對應的是已列印重現的矛盾。完整語意在重測前仍記為 0/3。

## Log 15｜預測失準與方法論修正：n=1 的逐輪比較不足以支持因果結論

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`。**付費呼叫 6 次。**  
報告：[live-q1-q3-round5.json](live-q1-q3-round5.json)。狀態：**0/3，且 Q1 相對上一輪退步。**

### 觀察：預測錯誤

Log 14 預測「Q1 有機會拿到 exact」。**結果相反**：Q1 回到 fallback，第二次嘗試失敗於
`missing_evidence:input_artifact=mutation_matrix`，`review_repair_validated=false`。
三題 `assumption_count` 皆為 0，與 assumptions 指示已移除一致，但**這一輪根本沒走到
匹配階段**，因此無法據此判定 Log 14 的介入有效或無效。

### Q1 在五輪之間的失敗方式

| 輪次 | 當時程式狀態 | Q1 第二次嘗試 |
| --- | --- | --- |
| 2 | E1 + P0 | `missing_evidence:input_artifact` |
| 3 | + 封閉詞彙、`required_evidence` | dict 包裝（`literal_error`） |
| 4 | + 傳輸正規化、修復訊息一致性 | **gold outcome**，因 assumptions 降為 ambiguous |
| 5 | + 移除 assumptions 指示 | `missing_evidence:input_artifact` |

**沒有單調趨勢，且失敗方式在同一題上來回擺盪。** temperature 為 0，但 provider 端仍非
決定性。因此：

> 每輪 n=1、且每輪之間都改動程式——這是被混淆的設計。前述數輪「介入 → 重測」的因果
> 歸因（Log 09、11、12、14）在統計上都不成立，不能宣稱任何一項已被 live 驗證。

這是本研究的方法論錯誤，據實記錄。已確認的部分僅限於**離線可重現**者：

- Log 13 的 `const: unknown` 矛盾：離線列印重現。
- Log 14 的 assumptions 耦合：離線對照重現（0 個 → exact；1 個 → ambiguous）。
- Log 12 的 dict 包裝：live 觀察到形狀，離線正規化有測試。

這些是**程式缺陷的證明**，不是**改善 live 準確率的證明**。兩者不可混為一談。

### 離線核對：`required_evidence` 確實有送達

為排除「介入未生效」，離線檢查三題的 witness 與修復訊息：

| 題 | `required_evidence.text_span` |
| --- | --- |
| Q1 | `DNA 突變資料` |
| Q2 | `體細胞突變` |
| Q3 | `體細胞突變` |

原文片段正確定位並送入 reviewer，Q1 仍然漏掉該證據項。**因此 Log 11 的
`required_evidence` 介入同樣未獲 live 支持。**

### 本輪不新增介入

依上述方法論結論，下一步應是**測量而非再猜**：以 `--repeat 3` 取得分布與
`unstable_cases`，再決定哪些差異值得歸因。評估器已支援每輪獨立試驗與不穩定案例列表。

```bash
python scripts/evaluate_routing.py --live --case original-q1 --case original-q2 \
  --case original-q3 --repeat 3 --max-calls 27 --json
```

呼叫上限由 `cases × repeat × 3` 計算，低於此值會在建立 provider 前被拒絕。

### 跨五輪穩定成立的事實

即使語意驗收仍為 0/3，以下在每一輪都成立：

- `unsafe_execution_count = 0`
- `interaction_failure_count = 0`
- 錯誤結果從未被呈現為 exact
- Q3 的 PANDA／LIONESS-PANDA 輸入相容性拒絕每輪都正確出現
- 本輪 `answer_failure_count = 0`：Log 14 記錄的 Q1「完全無指引」退步已消失

Q3 連續兩輪第二次嘗試只剩 `artifact_granularity:sample_cluster_assignment` 單一問題，
是目前最接近通過的案例；但依同一方法論，兩次觀察亦不足以宣稱趨勢。

## Log 16｜n=3 重複測量：dict 包裝佔 5/9，且其來源確認為我方修復訊息

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 19 次。** 報告：[live-q1-q3-repeat3.json](live-q1-q3-repeat3.json)。  
狀態：**9 次試驗 0 通過**，但首次取得可用的分布。

### 分布

| | 試驗 1 | 試驗 2 | 試驗 3 |
| --- | --- | --- | --- |
| Q1 | reviewer 通過、**gold outcome**、`assumption_count=2` → `ambiguous`、**使用者無答案** | dict `{artifact_type, granularity}` | dict 同上 |
| Q2 | dict 同上 | dict 同上 | **兩個** dict：`{artifact_type, entity_types, granularity, regulator_types, target_types}` |
| Q3 | 證據問題 ×4 | 證據問題 ×3 | 只剩 `artifact_granularity` |

`unstable_cases: ["original-q1"]`；`review_repair_validation_rate = 1/9`；
`schema_validation` 出現於 **9 次中的 5 次**。

### 根因確認：模型複製的是修復訊息裡的 `field_constraints`

試驗 Q2-T3 的物件鍵為
`{artifact_type, entity_types, granularity, regulator_types, target_types}`。
離線比對：

- `artifact_field_constraints('sample_cluster_assignment')` 的鍵集**完全相同**。
- 該鍵集**不含 `operation`**，而 schema 的 artifact `anyOf` 分支必然包含
  `operation`（它在 `required` 內）。

因此可排除 provider schema 分支，**來源是 `repair_feedback()` 送出的 `field_constraints`
物件本身**；`{artifact_type, granularity}` 是同一物件的子集。這是繼 Log 13 的
`const: unknown`、Log 14 的 assumptions 之後，**第三個由我方訊息造成的失敗**。

### 介入（單一介入，兩個面向，皆針對同一根因）

1. `field_constraints` 併附 `field_constraints_note`，明說這是 outcome 各欄位的
   JSON Schema 約束、**不是可貼入清單的值**，且 `input_artifacts` 只放純字面值。
2. 傳輸正規化擴充至**鏡像 outcome 形狀的物件**：物件中恰有一個包裝鍵帶字串值，
   且其餘鍵全部是 `RequestedOutcome` 的欄位名稱時，取出該字面值。
   理由：一個 `input_artifacts` 項目內沒有任何位置可以表示 granularity、entity_types
   等同層欄位，因此取出不會遺失**契約可儲存**的資訊；取出後仍面對同一封閉 enum，
   測試明確斷言 `{"artifact_type": "somatic_mutation", ...}` 仍然失敗。
   含非 outcome 欄位（例如 `source`）的物件維持錯誤，因為其意義未定。

一個原本斷言 `{artifact_type, granularity}` 應維持錯誤的測試，依本輪證據**改分類**並
加註說明；同時把 P0 套件中對應案例改為含非 outcome 欄位的物件。**沒有刪除任何測試。**

離線：完整套件 **1177 passed、3 failed（既有待決策項）、0 skipped**；
ruff 與 `git diff --check` 通過。

### 可否證的預測

若此歸因正確，下一次 `--repeat 3` 的 `schema_validation` 應由 5/9 明顯下降。
若未下降，則歸因錯誤，必須改為結構性處理（例如不再於修復訊息中傳遞任何物件形狀），
不得再以敘述文字重試。

### 升級為決策事項：assumptions 守衛是目前的約束瓶頸

9 次試驗中**唯一**產生 gold outcome 的 Q1-T1，因 `assumption_count=2` 被降為
`ambiguous`、`matched_actions=[]`，使用者因此**完全沒有得到指引**
（`answer_evaluated=false`）。Log 14 移除了修復訊息中要求寫入 assumptions 的指示，
模型仍自行寫入兩條。

因此 assumptions 守衛已不只是設計疑慮，而是**目前唯一一次語意成功的直接阻斷者**。
是否放寬屬於安全性取捨，本輪**未改動**，留待決定。與之相關但獨立的互動問題是：
`ambiguous` 且存在 `hypothesis_actions` 時目前完全不輸出指引，這使一次語意成功
反而變成比 fallback 更差的使用者結果。

## Log 17｜預測獲得驗證：schema 錯誤 5/9 → 0/9，並出現首次完整通過

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 20 次。** 報告：[live-q1-q3-repeat3-round2.json](live-q1-q3-repeat3-round2.json)。

### Log 16 的可否證預測與結果

> 預測：若歸因（reviewer 複製修復訊息的 `field_constraints` 物件）正確，
> 下一次 `--repeat 3` 的 `schema_validation` 應由 5/9 明顯下降。

| 指標 | Log 16 | 本輪 |
| --- | --- | --- |
| `diagnostics.schema_validation` | **5**（9 次中） | **0** |
| `semantic_pass_rate` | 0.000 | **0.111** |
| `review_repair_validation_rate` | 0.111 | 0.222 |
| `passed` | 0 / 9 | **1 / 9** |

**預測成立，且沒有任何一次試驗再出現 `input_artifacts` 的型別錯誤。** 這是本研究中
第一個事先寫下、事後獲得驗證的因果預測。歸因（Log 16）因此獲得支持：
問題來源是修復訊息傳遞的物件形狀，而非模型詞彙或 provider schema 分支。

### 首次完整通過

`original-q2` 試驗 1：`passed=true`、`status=exact`、`matched_actions=['run_sambar']`、
`request_mode=guidance`、outcome 完全符合 gold、`answer_passed=true`、
`interaction_passed=true`，進度顯示 `✓ Workflow — SAMBAR`，Next step 開放 continuation。

**這是研究開始以來第一次有試驗通過全部驗收條件。** 但 9 次中僅 1 次，
`unstable_cases` 為 `["original-q1", "original-q2"]`；**不得表述為 Q2 已修好**。

### 失敗結構已改變

本輪 `diagnostics` 只剩 `evidence_validation`。剩餘失敗集中於三群：

| 群 | 出現 | 修復分支狀態 |
| --- | --- | --- |
| `artifact_granularity:sample_cluster_assignment` | Q3 **3/3** | **原本沒有** |
| `artifact_roles:sample_cluster_assignment` | Q2 2/3 | 有（`roles`） |
| `missing_evidence:input_artifact=mutation_matrix` | Q1 2/3 | 有，但發生於最後一次嘗試 |

`artifact_granularity` 與 `artifact_entity` 送到 reviewer 時只有 `field_constraints`，
沒有 action 也沒有指示——與 Log 13 的 `inconsistent_not_applicable_outcome` 同一缺口。

### 本輪介入（單一介入）

新增 artifact 一致性修復分支：`align_with_artifact_ontology`，指出
「artifact_type 決定該欄位的可用值」，附上由 `ARTIFACT_SEMANTICS` 導出的
`allowed_values`（沿用 Log 13 的規則：以**修正後**的 artifact 為準），並要求同步更新
或移除該欄位的證據。未宣告限制的 artifact 不輸出 `allowed_values`。

離線：`tests/test_repair_feedback_coherence.py` 15 項；完整套件
**1181 passed、3 failed（既有待決策項）、0 skipped**；ruff 與 `git diff --check` 通過。

### 可否證的預測

Q3 第二次嘗試的 `artifact_granularity:sample_cluster_assignment` 應由 3/3 下降。
若未下降，則「缺少修復分支」不是主因，需改查該欄位在 prompt 中的 granularity 規則
（Q3 原文含 LIONESS 的 sample-specific 語境，模型可能是被原文帶走而非缺少指示）。

### 仍未決定

Q1 試驗 2 再次出現：gold outcome + `assumption_count=2` → `ambiguous` → **使用者無答案**。
Log 16 提出的 A／B／C 尚未選擇；在 9 次試驗中，assumptions 守衛已第二次成為
唯一一次語意成功的直接阻斷者。

## Log 18｜option C 生效、通過率 2/9；但 `artifact_granularity` 預測未成立

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 21 次。** 報告：[live-q1-q3-repeat3-round3.json](live-q1-q3-repeat3-round3.json)。  
本輪執行時工作樹已含 artifact 一致性修復分支與 option C 的第一版。

### 結果

| 指標 | 前一輪 | 本輪 |
| --- | --- | --- |
| `passed` | 1 / 9 | **2 / 9** |
| `semantic_pass_rate` | 0.111 | **0.222** |
| `review_repair_validation_rate` | 0.222 | **0.333** |
| `answer_evaluated_count` | 8 | **9** |
| `answer_failure_count` | 1 | **0** |
| `schema_validation` | 0 | 0（維持） |

Q2 三次試驗中兩次完整通過（`exact`、`run_sambar`、`request_mode=guidance`、gold outcome）。

### option C：確認生效，但第一版仍有殘留缺陷

Q1 試驗 1 出現 `match_basis: "assumed_outcome"`、`status: fallback`、
`assumption_count: 2`，**outcome 完整保存且使用者收到完整的 SAMBAR 指引**。
`answer_evaluated_count` 由 8 升至 9、`answer_failure_count` 歸零，
Log 14／16 記錄的「語意成功卻無指引」退步已消除。

但同一筆仍被評分器標記 `clarification: unnecessary question`：回答尾端附加了
「What supported NetZoo result do you want the agent to produce?」，Next step 也變成
`clarify_outcome`。追查後為 `assembly.py` 的規則：intent 判為 execute 且沒有 exact action
時就補一個問題。assumed_outcome 的 outcome 是完整的、候選也唯一，該問題沒有可收集的答案。

### 本輪修正（三項，均為前一版介入的缺口）

1. `match_outcome_hypotheses` 新增 `assumed_guidance` 參數，並要求
   **只有單一、完全確定的 hypothesis** 才能走 assumed_outcome 路徑；
   `request_mode == "execute"` 一律不適用。這修復了兩個既有安全性測試的回歸：
   執行請求不得從未確認的詮釋取得候選，兩個 hypothesis 仍須提出粒度選擇問題。
   **這兩個回歸是 option C 第一版造成的，記錄於此。**
2. `assembly.py`：`assumed_outcome` 不再補上「你想要什麼結果」的問題。
3. `MatchBasis` 新增 `assumed_outcome`；`SCHEMA_DIGESTS` 依刻意變更程序更新。

離線：完整套件 **1191 passed、3 failed（既有待決策項）、0 skipped**；
ruff 與 `git diff --check` 通過。

### 預測未成立

Log 17 預測：Q3 第二次嘗試的 `artifact_granularity:sample_cluster_assignment`
應由 3/3 下降。**本輪仍為 3/3。**

依當時預先訂下的判準：「缺少修復分支」**不是**主因。下一步應改查
granularity 規則本身——Q3 原文含 LIONESS 的 sample-specific 語境，模型可能是被原文
語境帶走，而非缺少修復指示。在取得該方向的證據前，不應再對修復訊息加碼。

`artifact 一致性修復分支`本身仍是正確的（它補上了一個確實存在的空缺），但**不能記為
Q3 的解法**。

### 累積狀態

| 輪次 | passed / 9 | schema 錯誤 | 備註 |
| --- | --- | --- | --- |
| repeat3 第一輪 | 0 | 5 | 首次取得分布 |
| 第二輪 | 1 | 0 | 傳輸形狀歸因獲驗證 |
| 第三輪 | **2** | 0 | option C 生效；granularity 預測失敗 |

`unstable_cases` 仍為 `["original-q1", "original-q2"]`。Q3 尚未有任何一次通過。
三輪合計 27 次試驗、3 次通過，全部集中於 Q2；**不得表述為「Q2 已修好」**。

## Log 19｜Q1 轉為穩定；剩餘阻礙收斂到 `request_mode`，且成因是 prompt 內部矛盾

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 23 次。** 報告：[live-q1-q3-repeat3-round4.json](live-q1-q3-repeat3-round4.json)。

### 結果

| 指標 | 第三輪 | 第四輪 |
| --- | --- | --- |
| `passed` | 2 / 9 | 2 / 9 |
| `review_repair_validation_rate` | 0.333 | **0.556** |
| `registry_recovery_count` | 6 | **4** |
| `answer_failure_count` | 0 | 0 |
| `unstable_cases` | Q1、Q2 | **只剩 Q2** |

### Q1：從不穩定變為穩定，且錯誤收斂到三項

三次試驗**全部**產生 gold outcome、`review_repair_validated=true`、
`match_basis="assumed_outcome"`，使用者都收到完整 SAMBAR 指引。錯誤只剩：

```text
status: expected exact, got fallback
request_mode: expected guidance, got unknown
pipeline: registry_guidance_fallback
```

Log 18 的 `clarification: unnecessary question` **已消失**，assembly 修正生效。

### 成因：semantic prompt 對同一分類自相矛盾

Q1 原文結尾是「**你有哪個內建工具可以一條龍處理…？**」，是明確的工具選擇問題。

- intent prompt 明列「tool/workflow selection questions」屬於 `answer`。
- semantic prompt 的 `guidance` 定義**沒有**列出工具選擇問題。
- semantic prompt 另一處寫著這類問題「**do not authorize execution**」，
  而 `unknown` 的定義正是「未確立是否要現在執行」。

模型選 `unknown` 是被我方文字帶去的，不是模型判斷失誤。這是**第四個**由我方訊息造成的
失敗，前三個為 `const: unknown`（Log 13）、assumptions 指示（Log 14）、
`field_constraints` 物件（Log 16）。

### 介入

semantic prompt 三處對齊：`guidance` 明列工具選擇問題；`unknown` 收窄為
「請求對是否執行沒有可辨識立場」並明說「不得僅因未授權執行就選 unknown」；
兩處「does not authorize execution」改為同時指明該類問題本身即 guidance。

離線：完整套件 **1193 passed、3 failed（既有待決策項）、0 skipped**；
ruff 與 `git diff --check` 通過。

### 可否證的預測

1. Q1 的 `request_mode` 應在多數試驗中變為 `guidance`。
2. 若成立，Q1 應進一步取得 `exact`：`request_mode == "guidance"` 會走
   guidance 完整性提升路徑，該路徑不受 assumptions 守衛影響
   （此邊界已由 `test_guidance_mode_completeness_promotion_is_left_unchanged` 記錄）。

若 request_mode 改變但仍未 exact，則 guidance 路徑另有阻礙，需重新檢查該路徑而非 prompt。
若 request_mode 未改變，則此 prompt 矛盾不是主因，**不得再以文字重試**。

### 未變更

Q3 的 `artifact_granularity` 仍為 3/3（第三輪已判定「缺修復分支」非主因）。
本輪未對其介入，避免同時改動多個變因。

## Log 20｜兩項預測皆成立，通過率 4/9；`request_mode` 成為唯一判別因子

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 22 次。** 報告：[live-q1-q3-repeat3-round5.json](live-q1-q3-repeat3-round5.json)。

### Log 19 的預測與結果

> 1. Q1 的 `request_mode` 應在多數試驗中變為 `guidance`。
> 2. 若成立，Q1 應進一步取得 `exact`（guidance 完整性提升路徑不受 assumptions 守衛影響）。

**兩項皆成立。**

| 指標 | 第四輪 | 第五輪 |
| --- | --- | --- |
| `passed` | 2 / 9 | **4 / 9** |
| `semantic_pass_rate` | 0.222 | **0.444** |
| `review_repair_rate` | 0.222 | **0.444** |

Q1 由 0/3 變為 **2/3 通過**；Q2 維持 2/3；Q3 仍 0/3。

### 跨 9 次試驗的完美相關

| `request_mode` | 試驗數 | 通過 |
| --- | --- | --- |
| `guidance` | 4 | **4** |
| `unknown` | 5 | **0** |

沒有例外。`request_mode` 目前是唯一的判別因子：分類為 `guidance` 的試驗全部走完
`semantic_registry_intent` 並取得 `exact`；分類為 `unknown` 的全部落入 fallback。

這也回頭證實 Log 19 的機制判讀正確：問題不在模型能力，而在 semantic prompt 對
`guidance` 與 `unknown` 的界線描述。

### 本輪介入：改列舉為通則

剩餘 `unknown` 的案例中，Q3 問的是「我該不該把這份矩陣丟進 PANDA 跟 LIONESS？」——
對**具名方法**的適用性提問，Log 19 的規則只涵蓋「哪個工具能產出結果」，未涵蓋此形。

繼續列舉題型會留下下一種未涵蓋的題型，因此改為通則：

- `guidance`：**任何描述或詢問科學結果／方法、而未指示現在執行的請求**。
  說明、比較、工作流程規劃、步驟列舉、假設性問答、哪個工具能產出結果、
  以及具名方法是否適合使用者的資料或目標，全部屬之。
- `unknown`：**收窄為「完全看不出科學請求」**，並明說不得僅因未授權執行、
  或因問題中沒有單一具名工具而選用。
- `execute` 維持不變：必須是明確要求現在執行。

安全性不受影響：`semantic_execution_missing` 判斷的是 `request_mode != "execute"`，
`guidance` 與 `unknown` 在執行閘門上完全等價。此變更只影響 guidance 完整性提升路徑。

離線：完整套件 **1195 passed、3 failed（既有待決策項）、0 skipped**；
ruff 與 `git diff --check` 通過。

### 可否證的預測

`request_mode == "guidance"` 的比例應由 4/9 上升；若 9/9 相關性維持，通過率應同步上升。
**Q3 即使轉為 guidance 也未必通過**：其第二次嘗試另有
`conflicting_evidence:granularity=sample_specific` 與 `missing_evidence:entity_type=sample`，
屬於獨立問題。若 request_mode 比例未上升，則「列舉不足」不是主因，不得再以文字重試。

### 累積

| 輪次 | passed / 9 | 主要變因 |
| --- | --- | --- |
| 1 | 0 | 取得分布基線 |
| 2 | 1 | 修復訊息不再傳遞物件形狀 |
| 3 | 2 | artifact 一致性分支、option C 第一版 |
| 4 | 2 | option C 修正；Q1 轉穩定 |
| 5 | **4** | `request_mode` 分類界線 |

五輪 45 次試驗共 9 次通過。Q3 仍未有任何一次通過，`unsafe_execution_count` 全程為 0。

## Log 21｜通則化預測失敗且造成退步；依預設判準退回實測較佳組態

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 20 次。** 報告：[live-q1-q3-repeat3-round6.json](live-q1-q3-repeat3-round6.json)。

### 預測與結果

Log 20 預測：`request_mode == "guidance"` 的比例應由 4/9 上升。

| 指標 | 第五輪（列舉版） | 第六輪（通則版） |
| --- | --- | --- |
| `request_mode == guidance` | 4 / 9 | **2 / 9** |
| `passed` | 4 / 9 | **2 / 9** |
| Q1 | 2 / 3 | **0 / 3** |
| Q2 | 2 / 3 | 2 / 3 |
| Q3 | 0 / 3 | 0 / 3 |

**預測失敗，且方向相反。** 把列舉改成通則使 `guidance` 分類變少，通過率同步下降，
Q1 由 2/3 退回 0/3。

`request_mode` 與通過與否的完美相關**依然成立**（2 個 guidance 全通過，7 個 unknown 全失敗），
因此判別機制的判讀不變；改變的只是分類本身變差。

### 依預設判準處理

Log 20 已預先寫下：「若 request_mode 比例未上升，則『列舉不足』不是主因，
**不得再以文字重試**。」

因此本輪**退回 Log 19 的列舉版措辭**——那是目前唯一有實測支持的組態（4/9）。
測試同步改為斷言列舉版措辭存在、且通則版措辭不得出現，並在測試說明中記錄
兩輪的實測數字與退回理由。

**必須誠實標註統計限制**：n=9，4/9 對 2/9 的差異不具統計顯著性，
本輪**不能證明列舉版較佳**；只能說通則版沒有任何支持證據，而列舉版有一次較好的實測，
因此退回較好的已測狀態。若日後要再動這段文字，必須先有機制層級的證據，
不能只憑一次分數。

### 附帶新觀察（僅記錄，未介入）

Q2 試驗 2 出現新的失敗形狀：
`schema_validation:outcome_hypothesis.evidence.1.rationale:missing`，
`input_keys` 顯示該 evidence 物件只有 `dimension/source/text_span/value`，缺 `rationale`。
9 次中僅 1 次，樣本不足以歸因，不予介入。

### 離線

完整套件 **1195 passed、3 failed（既有待決策項）、0 skipped**；
ruff 與 `git diff --check` 通過。

### 六輪累積

| 輪次 | passed / 9 | 主要變因 |
| --- | --- | --- |
| 1 | 0 | 取得分布基線 |
| 2 | 1 | 修復訊息不再傳遞物件形狀 |
| 3 | 2 | artifact 一致性分支、option C 第一版 |
| 4 | 2 | option C 修正；Q1 轉穩定 |
| 5 | **4** | `request_mode` 分類界線（列舉版） |
| 6 | 2 | 通則版 → **已退回** |

目前程式狀態等同第五輪。54 次試驗共 11 次通過，Q3 全程 0 次。
`unsafe_execution_count` 六輪全部為 0。

## Log 22｜Q3 的失敗是結構性的：修正 artifact_type 會產生無法再修的相依欄位違規

日期／時區：2026-09-05，Asia/Taipei。**離線分析，付費呼叫 0 次。**  
資料來源：六輪 `--repeat 3` 報告，Q3 共 **18 次試驗**。

### 先排除「資訊不足」

離線列印 Q3 attempt 1 的修復訊息（重建 live 觀察到的 regulatory_network +
sample_specific 提案）：

```text
terminal_goal_conflict -> action: restore_terminal_goal
                          granularity constraint: {"enum": ["aggregate", "unknown"]}
                          entity constraint     : {"items": {"enum": ["sample", "unknown"]}}
```

Log 13 的修正確實生效——約束描述的是**修正後**的 artifact，允許值正確。
**reviewer 拿得到正確資訊，仍回傳 `sample_specific`。** 因此不是訊息內容缺漏。

### 決定性統計

| 情況 | 試驗數 | 最終仍有 granularity 問題 |
| --- | --- | --- |
| granularity 於 **attempt 1** 即被標記（有修復機會） | 4 | 2 |
| granularity **只在 attempt 2 出現**（無修復機會） | 14 | **14** |

有修復機會時修好率 2/4；沒有修復機會時 0/14——後者是定義使然，不是模型能力。

### 機制

Q3 原文以 PANDA／LIONESS 的 sample-specific 網路框架陳述，第一次嘗試多半提出
`regulatory_network` + `sample_specific`。此時 `sample_specific` 對
`regulatory_network` **是合法的**，因此不會產生 `artifact_granularity` 問題。

attempt 2 依指示把 artifact_type 修正為 `sample_cluster_assignment`——這是正確的修復——
但繼承下來的 `sample_specific` 在新 artifact 下才變成違規。**這個違規是由修正本身產生的，
而攻擊它的唯一機會已經用完。**

這正是 Log 13 記錄過的限制（「reviewer 只有一次機會，任何單一失誤即致命」），
現在有 18 次試驗的量化證據，並且指出它會**系統性地**打擊「需要更換 artifact_type」的案例——
Q3 每一輪都需要換，Q1／Q2 多半不需要。這也解釋了為何 Q3 是唯一零通過的案例。

### 不採取的做法

- **再加修復訊息文字**：已證明資訊已存在，且 Log 21 已確立不得再以文字重試。
- **由程式依 ontology 自動改正相依欄位**：那是替模型填寫 outcome，
  違反既有禁令（「不要一律把 input 填成…」同一原則）。

### 待決策

唯一對得上此機制的做法是**放寬語意嘗試上限**：允許有界的第三次嘗試，
且僅在前一次確實有進展（issue 集合縮小或改變）時才啟用，避免無限重試。
代價是這些案例多一次呼叫，且既有文件記載的「三次呼叫上限」需改為四次。
屬於成本與契約決策，**本輪未實作**。

若不放寬，Q3 這類「需要更換 artifact_type」的請求預期將持續失敗，
但仍會得到正確的 fallback 指引與 PANDA／LIONESS 輸入相容性拒絕——
六輪 18 次試驗中，Q3 的回答斷言全部通過。

## Log 23｜實作有界第三次嘗試；token 預算是同一個決定的必要部分

日期／時區：2026-09-05，Asia/Taipei。**離線實作，付費呼叫 0 次。**  
依據：使用者授權放寬嘗試上限（Log 22 的待決策事項）。

### 介入

`_invoke_semantic_interpreter` 的上限由 2 次提高為 3 次（`MAX_SEMANTIC_ATTEMPTS`），
第三次**僅在前一次有可測量進展時**授予：

```python
def _made_progress(previous, current):
    return set(current) != set(previous) and len(current) <= len(previous)
```

重複相同 issue 或情況變糟，一律維持原本的兩次語意呼叫即結束——
無法收斂的模型不會多花任何成本。

### 未預期的發現：原本的 token 預算會讓這個放寬失效

實作後測試仍只有 2 次語意呼叫。追查發現不是新邏輯的問題，而是
`DEFAULT_TASK_TOKEN_BUDGET = 20_000` 在第三次嘗試被請求前就先擋掉了。

實測（Q3 fixture，逐步提高預算）：

| 預算 | 語意呼叫 | 結果 | 診斷 |
| --- | --- | --- | --- |
| 20_000（原值） | 2 | fallback | `budget` |
| 22_000 | 2 | fallback | `budget` |
| 24_000 | 3 | exact | `budget`、`intent`（intent router 被擋） |
| 26_000 | 3 | **exact** | 無預算警告 |
| 28_000 | 3 | exact | 無預算警告 |

四次呼叫的實測成本約 **21_300** tokens。選定 **28_000**：26_000 是最小可用值，
但 live prompt 長度有變異（觀察到單次試驗達 13.7k），保留餘裕。

**必須明確記錄的代價**：這是**每個請求**的上限，不只是重試的請求。
提高後，單一任務的 token 天花板由 20k 升至 28k；實際花費仍由各請求自身決定，
但失控任務的封頂變寬了。

### 連帶變更

- 評估器 `--max-calls` 由 `cases × repeat × 3` 改為 `× 4`。
- `_score` 的 call-limit 安全檢查由 `> 3` 改為 `> 4`。
- `docs/routing-test-strategy.md` 的「three-call bound」全部更新為四次，並新增本節說明。
- `test_repeated_semantic_drift_invalidates_exact_even_when_candidate_stays_correct`
  的 fixture 由「每隔一次 review 漂移」改為「該 trial 的每一次 review 都漂移」。
  原設計在新契約下代表「漂移後被修正」，已不符其命名意圖；改為持續漂移後，
  第三次嘗試因無進展而不啟用，測試意圖（持續漂移永不成為 exact）得以保留。

### 離線

新檔 `tests/test_bounded_third_attempt.py` 8 項；完整套件
**1203 passed、3 failed（既有待決策項）、0 skipped**；ruff 與 `git diff --check` 通過。

### 尚未驗證

**Q3 是否因此通過，只能由 live 重測判定。** 離線 fixture 顯示「進展→第三次→收斂」
可以取得 exact，但那是腳本化回覆，不是模型行為。預期：Q3 的
`artifact_granularity` 於最終嘗試出現的比例應下降；Q1／Q2 的呼叫數多數不變
（它們第二次即通過或第二次即失敗且無進展）。

## Log 24｜第三次嘗試預測失敗：兩次啟用皆使情況變糟；Q1 首次 3/3

日期／時區：2026-09-05，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 24 次。** 報告：[live-q1-q3-repeat3-round7.json](live-q1-q3-repeat3-round7.json)。  
本輪含 Log 23 的第三次嘗試與 28_000 token 預算。

### 預測與結果

Log 23 預測：Q3 的 `artifact_granularity` 於最終嘗試出現的比例應下降。**未成立。**
三次試驗最終嘗試全部仍有該問題。

第三次嘗試在 9 次試驗中啟用 **2 次**（皆為 Q3），兩次都**使情況變糟**：

| 試驗 | attempt 2 | attempt 3 |
| --- | --- | --- |
| Q3 t1 | 2 項（`artifact_granularity`、`missing_evidence:entity_type`） | **4 項** |
| Q3 t3 | 2 項（同上） | **4 項** |

兩次的 attempt 3 都新增了 `missing_current_input:mutation_matrix` 與兩項
`ungrounded_evidence`——**模型在第三次把原本已填對的 input 弄丟了**，granularity 也沒修好。

因此「多給一次機會就會收斂」的假設**被推翻**。Log 22 對機制的判讀（granularity 違規由
修正本身產生、且出現在無後繼的嘗試）仍然成立，但**補救方式錯了**。

### 本輪其他觀察

| 案例 | 通過 | 備註 |
| --- | --- | --- |
| Q1 | **3 / 3** | 研究以來首次有案例全數通過；三次皆只用 3 次呼叫，**未觸發第三次嘗試** |
| Q2 | 1 / 3 | 由 2/3 下降 |
| Q3 | 0 / 3 | 不變 |

總計 `passed 4/9`，與第五輪（無第三次嘗試）相同。**第三次嘗試沒有換到任何通過。**

Q1 的 3/3 不能歸因於第三次嘗試——它一次都沒用到。與第五輪（同樣措辭、20k 預算）的
2/3 相比，差異在 n=3 下不具意義。

### 一項先前未察覺的限制

第三次嘗試**只適用於證據驗證失敗**。attempt ≥ 1 的 **schema** 失敗會立即返回，
不進入進展判斷。Q2 本輪兩次失敗正是 schema 失敗
（`outcome_hypothesis.evidence.N.rationale:missing`），因此第三次嘗試對它完全無效。

該失敗形狀已在第六、七輪重複出現：`input_keys` 顯示 evidence 物件只有
`dimension/source/text_span/value`，**缺 `rationale`**。三次觀察，尚未介入。

### 待決策：是否撤回第三次嘗試

證據：啟用 2 次、2 次變糟、0 次帶來通過；總通過率與未啟用時相同（4/9）。
依本研究一貫判準（無支持證據即退回較好的已測狀態），應**撤回**第三次嘗試
與隨之提高的 token 預算（28_000 → 20_000）。

但此放寬是使用者在知情下的決定，故本輪**未自行撤回**，僅提出證據與建議。
若保留，代價是 Q3 這類案例每次多一次呼叫且無收益；若撤回，Q3 回到兩次嘗試，
結果不變（仍為 0/3），但省下該次呼叫並回復較低的 token 天花板。

## Log 25｜分析錯誤更正：`request_mode` 的相關性是報告產物，不是因果

日期／時區：2026-09-06，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 20 次。** 報告：[live-q1-q3-repeat3-round8.json](live-q1-q3-repeat3-round8.json)。  
結果：`passed 1/9`（前一輪 4/9）。

### 我的分析錯了

第八輪新增的 `request_mode` 驗證器**在 9 次試驗中觸發 0 次**。也就是說模型每一次
都回報 `guidance`，從來沒有回報過 `unknown`。

原因：`_semantic_failure()` 呼叫 `outcome_routing_state(decision)`，
而該函式的 `request_mode` 預設值就是 `"unknown"`。**任何語意失敗的 run，
報告裡的 `request_mode` 一律是 `unknown`，與模型的實際輸出無關。**

跨全部輪次核對：

| pipeline 走完 | 報告的 request_mode | 次數 |
| --- | --- | --- |
| 否 | unknown | **53** |
| 否 | guidance | 1 |
| 是 | guidance | 16 |
| 是 | unknown | 2 |

所以 Log 20 記錄的「通過 ⟺ guidance，零例外」**是一個恆真式**：
失敗 → fallback → 欄位填 unknown。而我據此推出的「48 次失敗中有 42 次卡在
request_mode」**完全錯誤**——它量的是報告預設值，不是模型行為。

Log 19／20 的 prompt 修改與 Log 24 的 request_mode 驗證器，都建立在這個誤讀上。
第五輪 2/9→4/9、第六輪 4/9→2/9 的變化，在 n=9 下無法與雜訊區分。

**處置**：`request_mode` 驗證器已 `git revert`（`baaae06`）。它在測量集上完全不觸發，
且帶有 live 無法覆蓋的風險方向（把真正的工作指令說成 guidance）。
無支持證據即退回，與本研究一貫判準一致。

### 更正後的真實阻礙

改用 `diagnostic_details`（非恆真式）統計最後一次嘗試的 issue，全部輪次：

| issue | 次數 |
| --- | --- |
| **`missing_evidence`** | **29** |
| `artifact_granularity` | 18 |
| `schema_validation` | 14 |
| `conflicting_evidence` | 13 |
| `missing_current_input` | 9 |

`missing_evidence` 再細分：**`entity_type` 21 次**、`input_artifact` 8 次。

也就是說：**outcome 多半是對的，缺的是「證明」。** 系統要求每個已填維度都有
對應且接地的證據，而模型反覆漏掉其中一項。這正是使用者問的
「為什麼會沒能自己驗證問題的理解」的答案。

### 介入：不要求 ontology 已唯一決定的維度提供證據

`sample_cluster_assignment` 的 ontology 宣告 `entities = {sample}`、
`granularities = {aggregate}`——**都只有一個合法值**，且
`outcome_consistency_issues()` 已經會拒絕任何其他值。因此為它們另外要求一則證據
不帶任何資訊：真正需要被證明的是「為什麼選這個 artifact_type」。

這延伸的是驗證器**既有**的規則——被列為 regulator/target 的實體本來就不需要
第二則 entity 證據。現在同樣排除 artifact 唯一決定的 entity 與 granularity。
允許多個值的 artifact（如 `pathway_mutation_matrix` 的 {pathway, sample}、
`regulatory_network` 的兩種 granularity）**不受影響**，因為那裡的值是真正的選擇。

一致性檢查完全未動：測試明確斷言 artifact 禁止的 entity 或 granularity
仍然被 `artifact_entity` / `artifact_granularity` 拒絕。

離線：新檔 `tests/test_entailed_evidence.py` 8 項；完整套件
**1210 passed、3 failed（既有待決策項）、0 skipped**；ruff 與 `git diff --check` 通過。

### 可否證的預測

`missing_evidence:entity_type` 應由 21 次大幅下降或消失。
若未下降，則此歸因錯誤，需重新檢查 `_required_evidence` 的實際觸發條件。

## Log 26｜預測成立：`entity_type` 證據需求歸零，通過 1/9 → 3/9

日期／時區：2026-09-06，Asia/Taipei。模型 `openai/gpt-4o-mini`，`--repeat 3`。  
**付費呼叫 21 次。** 報告：[live-q1-q3-repeat3-round9.json](live-q1-q3-repeat3-round9.json)。

### Log 25 的預測與結果

> 預測：`missing_evidence:entity_type` 應由 21 次大幅下降或消失。

| 指標 | 第八輪 | 第九輪 |
| --- | --- | --- |
| `missing_evidence:entity_type` | 8 | **0** |
| `passed` | 1 / 9 | **3 / 9** |
| `review_repair_validation_rate` | 0.222 | 0.333 |

**預測成立。** 「不要求 ontology 已唯一決定的維度提供證據」使該類阻礙完全消失。
Q1 由 0/3 變 2/3，Q2 1/3，Q3 仍 0/3。

### 阻礙移轉

`entity_type` 消失後，下一層浮現：

| 第九輪最終阻礙 | 次數 |
| --- | --- |
| `missing_evidence:input_artifact=mutation_matrix` | **3** |
| `schema_validation:evidence.N.rationale:missing` | 1 |
| `missing_current_input:mutation_matrix` | 1 |
| `conflicting_evidence:input_artifact=mutation_matrix` | 1 |
| `conflicting_evidence:granularity=sample_specific` | 1 |

`missing_evidence:input_artifact` 由 2 升至 6 次——它先前被 `entity_type` 遮住。

### 介入：同一原則延伸一格，並在該處停住

request witnesses **本來就會**在原文中定位目前輸入——那正是
`missing_current_input` 的來源。當 outcome 列出的輸入，正是這些 witnesses
獨立確認為 current 的那一個時，接地已由程式對照原文完成，再要求模型自己證明一次
不增加任何資訊。

**界線嚴格**：witnesses 看不到的輸入仍然必須有模型證據——那裡模型的證據是唯一的接地。
歷史／否定／假設的輸入不算確認（測試明確涵蓋，且 `noncurrent_input` 照常觸發）。
完整性需求完全未動：漏掉已確認的輸入仍然是 `missing_current_input`。

這是繼「role 成員不需第二則 entity 證據」（既有）與 Log 25「ontology 唯一決定的維度」
之後，同一原則的第三次應用，且到此為止：artifact_type、operation
與模型自行主張的輸入仍然必須被證明。

### 更新的既有測試

`test_current_input_artifact_requires_its_own_consistent_evidence` 的第一段斷言
在新規則下過時（其 task 原文本就含「somatic mutation matrix」）。**未刪除**：
改為使用未提及輸入的 task 以保留「未確認輸入仍需證據」的意圖，並加註指向
`tests/test_entailed_evidence.py`，該檔同時釘住兩個方向。

離線：`tests/test_entailed_evidence.py` 12 項；完整套件
**1214 passed、3 failed（既有待決策項）、0 skipped**；ruff 與 `git diff --check` 通過。

### 可否證的預測

`missing_evidence:input_artifact` 應由 6 次大幅下降。
若未下降，則此歸因錯誤，需檢查 witnesses 在該題實際回報的 status。
Q3 仍可能因 `conflicting_evidence:granularity` 與 `artifact_granularity` 失敗——
那是 Log 22 記錄的獨立結構問題，本輪未動。
